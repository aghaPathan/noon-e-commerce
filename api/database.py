"""
ClickHouse Database Handler for Noon-E-Commerce API
With retry logic for resilience
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from contextlib import contextmanager

from clickhouse_driver import Client
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# Configuration from environment
CLICKHOUSE_HOST = os.environ.get('CLICKHOUSE_HOST', 'localhost')
CLICKHOUSE_PORT = int(os.environ.get('CLICKHOUSE_PORT', 9000))
CLICKHOUSE_USER = os.environ.get('CLICKHOUSE_USER', 'default')
CLICKHOUSE_PASSWORD = os.environ.get('CLICKHOUSE_PASSWORD')
if not CLICKHOUSE_PASSWORD:
    raise RuntimeError("CLICKHOUSE_PASSWORD environment variable is required. Set it before starting the application.")
CLICKHOUSE_DB = os.environ.get('CLICKHOUSE_DB', 'noon_intelligence')


class ClickHouseDB:
    """ClickHouse database connection handler"""
    
    def __init__(self):
        self._client = None
    
    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = Client(
                host=CLICKHOUSE_HOST,
                port=CLICKHOUSE_PORT,
                user=CLICKHOUSE_USER,
                password=CLICKHOUSE_PASSWORD,
                database=CLICKHOUSE_DB,
            )
        return self._client
    
    # Slow query threshold in milliseconds
    SLOW_QUERY_THRESHOLD_MS = int(os.environ.get('SLOW_QUERY_THRESHOLD_MS', 100))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, OSError)),
        before_sleep=lambda retry_state: logger.warning(
            f"DB query retry attempt {retry_state.attempt_number} after error: {retry_state.outcome.exception()}"
        )
    )
    def execute(self, query: str, params: Dict = None) -> List[tuple]:
        """Execute a query and return results with retry logic and timing"""
        import time
        start_time = time.time()
        
        try:
            result = self.client.execute(query, params or {})
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log slow queries
            if duration_ms > self.SLOW_QUERY_THRESHOLD_MS:
                # Truncate query for logging (first 200 chars)
                query_preview = query[:200].replace('\n', ' ')
                logger.warning(f"SLOW QUERY ({duration_ms:.2f}ms): {query_preview}...")
            else:
                logger.debug(f"Query executed in {duration_ms:.2f}ms")
            
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Query failed after {duration_ms:.2f}ms: {e}")
            # Reset client on connection errors to force reconnect
            if "connection" in str(e).lower() or "network" in str(e).lower():
                self._client = None
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((ConnectionError, OSError))
    )
    def health_check(self) -> bool:
        """Check database connectivity with retry"""
        try:
            result = self.client.execute("SELECT 1")
            return result == [(1,)]
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self._client = None  # Reset client for reconnect
            return False
    
    # Product queries
    def get_products(self, page: int = 1, page_size: int = 50, active_only: bool = True) -> tuple:
        """Get paginated list of products"""
        offset = (page - 1) * page_size
        
        where_clause = "WHERE active = 1" if active_only else ""
        
        # Get total count
        count_query = f"SELECT count() FROM products {where_clause}"
        total = self.execute(count_query)[0][0]
        
        # Get products
        query = f"""
            SELECT sku, name, category, brand, active, created_at
            FROM products
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """
        rows = self.execute(query, {'limit': page_size, 'offset': offset})
        
        products = [
            {
                'sku': r[0],
                'name': r[1],
                'category': r[2],
                'brand': r[3],
                'active': bool(r[4]),
                'created_at': r[5],
            }
            for r in rows
        ]
        
        return products, total
    
    def get_price_history(self, sku: str, days: int = 30) -> Dict[str, Any]:
        """Get price history for a SKU"""
        start_date = date.today() - timedelta(days=days)
        
        query = """
            SELECT 
                toDate(scraped_at) as date,
                price,
                original_price,
                discount_pct,
                seller_id,
                in_stock
            FROM price_history
            WHERE sku = %(sku)s AND date >= %(start_date)s
            ORDER BY date DESC, scraped_at DESC
        """
        rows = self.execute(query, {'sku': sku, 'start_date': start_date})
        
        if not rows:
            return None
        
        history = [
            {
                'date': r[0],
                'price': float(r[1]),
                'original_price': float(r[2]) if r[2] else None,
                'discount_pct': float(r[3]) if r[3] else None,
                'seller_id': r[4],
                'in_stock': bool(r[5]),
            }
            for r in rows
        ]
        
        prices = [h['price'] for h in history]
        
        # Calculate price change
        price_change_pct = None
        if len(history) >= 2:
            oldest = history[-1]['price']
            newest = history[0]['price']
            if oldest > 0:
                price_change_pct = round((newest - oldest) / oldest * 100, 2)
        
        # Get product name
        product_query = "SELECT name FROM products WHERE sku = %(sku)s LIMIT 1"
        product_result = self.execute(product_query, {'sku': sku})
        product_name = product_result[0][0] if product_result else None
        
        return {
            'sku': sku,
            'product_name': product_name,
            'currency': 'SAR',
            'history': history,
            'min_price': min(prices),
            'max_price': max(prices),
            'avg_price': round(sum(prices) / len(prices), 2),
            'price_change_pct': price_change_pct,
        }
    
    def get_competitors(self, sku: str) -> Dict[str, Any]:
        """Get competitor prices for a SKU"""
        query = """
            SELECT 
                ph.seller_id,
                c.seller_name,
                ph.price,
                ph.original_price,
                ph.discount_pct,
                ph.in_stock,
                ph.scraped_at
            FROM mv_latest_prices ph
            LEFT JOIN competitors c ON ph.seller_id = c.seller_id
            WHERE ph.sku = %(sku)s
            ORDER BY ph.price ASC
        """
        rows = self.execute(query, {'sku': sku})
        
        if not rows:
            return None
        
        competitors = [
            {
                'seller_id': r[0],
                'seller_name': r[1],
                'price': float(r[2]),
                'original_price': float(r[3]) if r[3] else None,
                'discount_pct': float(r[4]) if r[4] else None,
                'in_stock': bool(r[5]),
                'last_updated': r[6],
            }
            for r in rows
        ]
        
        prices = [c['price'] for c in competitors]
        
        # Get product name
        product_query = "SELECT name FROM products WHERE sku = %(sku)s LIMIT 1"
        product_result = self.execute(product_query, {'sku': sku})
        product_name = product_result[0][0] if product_result else None
        
        return {
            'sku': sku,
            'product_name': product_name,
            'competitors': competitors,
            'lowest_price': min(prices),
            'highest_price': max(prices),
            'seller_count': len(competitors),
        }
    
    def get_latest_prices(self) -> List[Dict[str, Any]]:
        """Get latest prices for all tracked products (for frontend dashboard)"""
        query = """
            SELECT 
                ph.sku,
                p.name as product_name,
                c.seller_name as seller,
                ph.price,
                ph.original_price,
                ph.discount_pct,
                ph.in_stock,
                ph.scraped_at
            FROM mv_latest_prices ph
            LEFT JOIN products p ON ph.sku = p.sku
            LEFT JOIN competitors c ON ph.seller_id = c.seller_id
            WHERE p.active = 1
            ORDER BY ph.scraped_at DESC
            LIMIT 100
        """
        try:
            rows = self.execute(query)
            return [
                {
                    'sku': r[0],
                    'product_name': r[1] or r[0],
                    'seller': r[2] or 'Unknown',
                    'price': float(r[3]) if r[3] else 0,
                    'original_price': float(r[4]) if r[4] else None,
                    'discount_pct': float(r[5]) if r[5] else None,
                    'in_stock': bool(r[6]) if r[6] is not None else True,
                    'scraped_at': r[7].isoformat() if r[7] else datetime.utcnow().isoformat(),
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Error getting latest prices: {e}")
            # Return empty list if table doesn't exist or other errors
            return []

    def get_daily_price_alerts(self, threshold_pct: float = 5.0) -> Dict[str, Any]:
        """Get products with significant price changes"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        query = """
            SELECT 
                t.sku,
                p.name,
                y.price as prev_price,
                t.price as curr_price,
                t.price - y.price as change_amount,
                round((t.price - y.price) / y.price * 100, 2) as change_pct,
                t.seller_id,
                t.scraped_at
            FROM mv_latest_prices t
            JOIN (
                SELECT sku, seller_id, price
                FROM price_history
                WHERE toDate(scraped_at) = %(yesterday)s
            ) y ON t.sku = y.sku AND t.seller_id = y.seller_id
            LEFT JOIN products p ON t.sku = p.sku
            WHERE abs((t.price - y.price) / y.price * 100) >= %(threshold)s
            ORDER BY abs(change_pct) DESC
            LIMIT 100
        """
        rows = self.execute(query, {'yesterday': yesterday, 'threshold': threshold_pct})
        
        alerts = []
        drops = 0
        increases = 0
        
        for r in rows:
            change_pct = float(r[5])
            alert_type = 'price_drop' if change_pct < 0 else 'price_increase'
            
            if change_pct < 0:
                drops += 1
            else:
                increases += 1
            
            alerts.append({
                'sku': r[0],
                'product_name': r[1],
                'previous_price': float(r[2]),
                'current_price': float(r[3]),
                'change_amount': float(r[4]),
                'change_pct': change_pct,
                'seller_id': r[6],
                'alert_type': alert_type,
                'detected_at': r[7],
            })
        
        return {
            'date': today,
            'alerts': alerts,
            'total_drops': drops,
            'total_increases': increases,
        }


# Singleton instance
db = ClickHouseDB()
