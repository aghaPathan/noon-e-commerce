"""
Airflow DAG: Noon Price Scraper
Project: Noon-E-Commerce

Schedule: Daily at 6 AM KSA (3 AM UTC)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.models import Variable
import logging

logger = logging.getLogger(__name__)

# DAG Configuration
DAG_ID = 'noon_price_scraper'
SCHEDULE = '0 3 * * *'  # 3 AM UTC = 6 AM KSA

default_args = {
    'owner': 'noon-ecommerce',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30),
    'execution_timeout': timedelta(hours=2),
}


def load_skus(**context):
    """Load SKU list from Variable or file"""
    import json
    
    try:
        # Try loading from Airflow Variable
        skus_json = Variable.get('noon_skus', default_var=None)
        if skus_json:
            skus = json.loads(skus_json)
            logger.info(f"Loaded {len(skus)} SKUs from Airflow Variable")
            return skus
    except Exception as e:
        logger.warning(f"Could not load from Variable: {e}")
    
    # Fallback to file
    sku_file = '/home/sysadmin/workspace/noon-e-commerce/skus.txt'
    try:
        with open(sku_file, 'r') as f:
            skus = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(skus)} SKUs from file")
        return skus
    except FileNotFoundError:
        logger.warning(f"SKU file not found: {sku_file}")
        # Return sample SKUs for testing
        return ['N12345678', 'N87654321']


def scrape_noon(**context):
    """Scrape Noon.com products using ScraperAPI"""
    import sys
    sys.path.insert(0, '/home/sysadmin/workspace/noon-e-commerce')
    
    from noon_scraper import NoonScraper
    
    # Get SKUs from previous task
    ti = context['ti']
    skus = ti.xcom_pull(task_ids='load_skus')
    
    if not skus:
        logger.error("No SKUs to scrape")
        raise ValueError("No SKUs provided")
    
    logger.info(f"Scraping {len(skus)} products")
    
    scraper = NoonScraper()
    results = scraper.scrape_products(skus)
    
    # Push results to XCom
    serialized = {sku: p.to_dict() for sku, p in results.items()}
    ti.xcom_push(key='scraped_data', value=serialized)
    
    logger.info(f"Scraped {len(results)}/{len(skus)} products successfully")
    return len(results)


def validate_data(**context):
    """Validate scraped data quality"""
    ti = context['ti']
    data = ti.xcom_pull(task_ids='scrape_noon', key='scraped_data')
    
    if not data:
        raise ValueError("No data to validate")
    
    valid_count = 0
    invalid_skus = []
    
    for sku, product in data.items():
        # Validation rules
        errors = []
        
        if not product.get('product_name') or product['product_name'] == 'Unknown':
            errors.append('missing_name')
        
        price = product.get('price', 0)
        if price <= 0 or price > 999999:
            errors.append(f'invalid_price:{price}')
        
        if errors:
            invalid_skus.append({'sku': sku, 'errors': errors})
            logger.warning(f"Validation failed for {sku}: {errors}")
        else:
            valid_count += 1
    
    # Allow up to 10% invalid
    invalid_pct = len(invalid_skus) / len(data) * 100 if data else 0
    
    if invalid_pct > 10:
        logger.error(f"Validation failed: {invalid_pct:.1f}% invalid (threshold: 10%)")
        raise ValueError(f"Too many invalid records: {invalid_pct:.1f}%")
    
    logger.info(f"Validation passed: {valid_count}/{len(data)} valid ({100-invalid_pct:.1f}%)")
    ti.xcom_push(key='valid_data', value=data)
    return valid_count


def load_to_clickhouse(**context):
    """Load validated data to ClickHouse"""
    from clickhouse_driver import Client
    import os
    
    ti = context['ti']
    data = ti.xcom_pull(task_ids='validate_data', key='valid_data')
    execution_date = context['ds']
    
    if not data:
        raise ValueError("No data to load")
    
    # ClickHouse connection
    client = Client(
        host=os.environ.get('CLICKHOUSE_HOST', 'localhost'),
        port=int(os.environ.get('CLICKHOUSE_PORT', 9000)),
        user=os.environ.get('CLICKHOUSE_USER', 'default'),
        password=os.environ.get('CLICKHOUSE_PASSWORD'),
        database='noon_intelligence'
    )
    
    # Prepare records
    records = []
    for sku, product in data.items():
        records.append({
            'sku': sku,
            'seller_id': product.get('seller', 'noon'),
            'price': product.get('price', 0),
            'original_price': product.get('original_price'),
            'discount_pct': product.get('discount_pct'),
            'currency': product.get('currency', 'SAR'),
            'in_stock': 1 if product.get('in_stock') else 0,
            'scraped_at': product.get('scraped_at'),
        })
    
    # Insert with ReplacingMergeTree handling duplicates
    client.execute(
        '''
        INSERT INTO price_history 
        (sku, seller_id, price, original_price, discount_pct, currency, in_stock, scraped_at)
        VALUES
        ''',
        records
    )
    
    logger.info(f"Loaded {len(records)} records to ClickHouse for {execution_date}")
    return len(records)


def cleanup(**context):
    """Cleanup XCom data to prevent bloat"""
    from airflow.models import XCom
    
    ti = context['ti']
    dag_id = context['dag'].dag_id
    execution_date = context['execution_date']
    
    # Clear XCom for this DAG run
    XCom.clear(
        dag_id=dag_id,
        execution_date=execution_date,
    )
    logger.info("XCom cleanup completed")


# DAG Definition
with DAG(
    dag_id=DAG_ID,
    default_args=default_args,
    description='Daily Noon.com price scraper for market intelligence',
    schedule_interval=SCHEDULE,
    start_date=datetime(2026, 2, 1),
    catchup=False,
    tags=['noon', 'scraping', 'market-intelligence'],
    max_active_runs=1,
) as dag:
    
    start = EmptyOperator(task_id='start')
    
    load_skus_task = PythonOperator(
        task_id='load_skus',
        python_callable=load_skus,
    )
    
    scrape_task = PythonOperator(
        task_id='scrape_noon',
        python_callable=scrape_noon,
    )
    
    validate_task = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data,
    )
    
    load_task = PythonOperator(
        task_id='load_clickhouse',
        python_callable=load_to_clickhouse,
    )
    
    cleanup_task = PythonOperator(
        task_id='cleanup',
        python_callable=cleanup,
        trigger_rule='all_done',  # Run even if upstream fails
    )
    
    end = EmptyOperator(task_id='end')
    
    # Task dependencies
    start >> load_skus_task >> scrape_task >> validate_task >> load_task >> cleanup_task >> end
