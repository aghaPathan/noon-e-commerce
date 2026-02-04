#!/usr/bin/env python3
"""
Noon.com Product Scraper using ScraperAPI
Project: Noon-E-Commerce
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from scraperapi_sdk import ScraperAPIClient
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('noon_scraper')

# Configuration
SCRAPERAPI_KEY = os.environ.get('SCRAPERAPI_KEY')
MAX_RETRIES = 3
RETRY_DELAYS = [5, 10, 20]  # Exponential backoff in seconds


@dataclass
class ProductData:
    """Data structure for scraped product information"""
    sku: str
    product_name: str
    seller: str
    price: float
    original_price: Optional[float]
    discount_pct: Optional[float]
    currency: str
    in_stock: bool
    url: str
    scraped_at: datetime
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['scraped_at'] = self.scraped_at.isoformat()
        return d


class NoonScraper:
    """Scraper for Noon.com product pages using ScraperAPI"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or SCRAPERAPI_KEY
        if not self.api_key:
            raise ValueError("SCRAPERAPI_KEY environment variable not set")
        self.client = ScraperAPIClient(self.api_key)
        logger.info("NoonScraper initialized")
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch page HTML with retry logic"""
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1}/{MAX_RETRIES})")
                response = self.client.get(
                    url=url,
                    params={
                        'render': True,  # Enable JS rendering
                        'country_code': 'sa',  # Saudi Arabia
                    }
                )
                return response
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {error_msg}")
                
                # Check for rate limiting
                if '429' in error_msg or 'rate' in error_msg.lower():
                    delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                    logger.info(f"Rate limited. Waiting {delay}s before retry...")
                    time.sleep(delay)
                elif attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAYS[attempt])
                else:
                    logger.error(f"Failed to fetch {url} after {MAX_RETRIES} attempts")
                    return None
        return None
    
    def _parse_product(self, html: str, url: str, sku: str) -> Optional[ProductData]:
        """Parse product data from HTML"""
        import re
        import json
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Product name
            name_elem = soup.select_one('h1[data-qa="pdp-name"]') or \
                       soup.select_one('h1.productTitle') or \
                       soup.select_one('h1')
            product_name = name_elem.get_text(strip=True) if name_elem else "Unknown"
            
            # Try to extract price from JSON data embedded in page (most reliable)
            price = 0.0
            original_price = None
            seller = "noon"
            
            # Look for sale_price in JSON
            sale_price_match = re.search(r'"sale_price"\s*:\s*([\d.]+)', html)
            if sale_price_match:
                price = float(sale_price_match.group(1))
            
            # Look for original price
            original_match = re.search(r'"price"\s*:\s*([\d.]+)', html)
            if original_match:
                orig = float(original_match.group(1))
                if orig > price:
                    original_price = orig
            
            # Fallback: look for price pattern in elements with Price classes
            if price == 0.0:
                price_elems = soup.select('[class*="Price"]')
                for elem in price_elems:
                    text = elem.get_text(strip=True)
                    # Extract first number that looks like a price (e.g., 4649.00)
                    match = re.match(r'([\d,]+\.?\d*)', text)
                    if match:
                        price = self._parse_price(match.group(1))
                        if price > 0:
                            break
            
            # Extract seller from JSON
            seller_match = re.search(r'"store_name"\s*:\s*"([^"]+)"', html)
            if seller_match:
                seller = seller_match.group(1)
            else:
                seller_elem = soup.select_one('a[data-qa="pdp-seller-name"]') or \
                             soup.select_one('.sellerName') or \
                             soup.select_one('[class*="seller"]')
                seller = seller_elem.get_text(strip=True) if seller_elem else "noon"
            
            # Calculate discount
            discount_pct = None
            if original_price and original_price > price:
                discount_pct = round((1 - price / original_price) * 100, 1)
            
            # Stock status
            out_of_stock = soup.select_one('[data-qa="pdp-out-of-stock"]') or \
                          soup.find(string=lambda t: t and 'out of stock' in t.lower())
            in_stock = out_of_stock is None
            
            return ProductData(
                sku=sku,
                product_name=product_name,
                seller=seller,
                price=price,
                original_price=original_price,
                discount_pct=discount_pct,
                currency='SAR',
                in_stock=in_stock,
                url=url,
                scraped_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error parsing product {sku}: {e}")
            return None
    
    def _parse_price(self, price_text: str) -> float:
        """Extract numeric price from text"""
        import re
        # Remove currency symbols and whitespace
        cleaned = re.sub(r'[^\d.,]', '', price_text)
        # Handle comma as thousands separator
        cleaned = cleaned.replace(',', '')
        try:
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0
    
    def scrape_product(self, sku: str) -> Optional[ProductData]:
        """Scrape a single product by SKU"""
        url = f"https://www.noon.com/saudi-en/{sku}/p/"
        
        html = self._fetch_page(url)
        if not html:
            logger.error(f"Failed to fetch product {sku}")
            return None
        
        product = self._parse_product(html, url, sku)
        if product:
            logger.info(f"Scraped {sku}: {product.product_name} - {product.price} SAR")
        return product
    
    def scrape_products(self, skus: List[str]) -> Dict[str, ProductData]:
        """Scrape multiple products, continue on failures"""
        results = {}
        failed = []
        
        for i, sku in enumerate(skus, 1):
            logger.info(f"Processing {i}/{len(skus)}: {sku}")
            
            product = self.scrape_product(sku)
            if product:
                results[sku] = product
            else:
                failed.append(sku)
            
            # Rate limiting between requests
            if i < len(skus):
                time.sleep(2)
        
        logger.info(f"Completed: {len(results)} success, {len(failed)} failed")
        if failed:
            logger.warning(f"Failed SKUs: {failed}")
        
        return results


def main():
    """CLI entry point for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Noon.com Product Scraper')
    parser.add_argument('skus', nargs='+', help='Product SKUs to scrape')
    parser.add_argument('--output', '-o', help='Output JSON file')
    args = parser.parse_args()
    
    scraper = NoonScraper()
    results = scraper.scrape_products(args.skus)
    
    output = {sku: p.to_dict() for sku, p in results.items()}
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
