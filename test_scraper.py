#!/usr/bin/env python3
"""
Unit Tests for Noon Scraper
Project: Noon-E-Commerce
"""

import unittest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime
import json

# Import after setting up mock for scraperapi_sdk
with patch.dict('sys.modules', {'scraperapi_sdk': MagicMock()}):
    from noon_scraper import NoonScraper, ProductData, RETRY_DELAYS


class TestProductData(unittest.TestCase):
    """Tests for ProductData dataclass"""
    
    def test_product_data_creation(self):
        """Test creating a ProductData instance"""
        product = ProductData(
            sku='N12345678',
            product_name='Test Product',
            seller='Test Seller',
            price=99.99,
            original_price=149.99,
            discount_pct=33.3,
            currency='SAR',
            in_stock=True,
            url='https://noon.com/test',
            scraped_at=datetime(2026, 2, 2, 10, 0, 0)
        )
        
        self.assertEqual(product.sku, 'N12345678')
        self.assertEqual(product.price, 99.99)
        self.assertTrue(product.in_stock)
    
    def test_product_data_to_dict(self):
        """Test converting ProductData to dictionary"""
        dt = datetime(2026, 2, 2, 10, 0, 0)
        product = ProductData(
            sku='N12345678',
            product_name='Test Product',
            seller='noon',
            price=50.0,
            original_price=None,
            discount_pct=None,
            currency='SAR',
            in_stock=True,
            url='https://noon.com/test',
            scraped_at=dt
        )
        
        d = product.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d['sku'], 'N12345678')
        self.assertEqual(d['scraped_at'], '2026-02-02T10:00:00')


class TestNoonScraper(unittest.TestCase):
    """Tests for NoonScraper class"""
    
    @patch.dict('os.environ', {'SCRAPERAPI_KEY': 'test_api_key'})
    def test_scraper_initialization(self):
        """Test scraper initializes with API key"""
        with patch('noon_scraper.ScraperAPIClient'):
            scraper = NoonScraper()
            self.assertEqual(scraper.api_key, 'test_api_key')
    
    @patch.dict('os.environ', {}, clear=True)
    def test_scraper_no_api_key_raises(self):
        """Test scraper raises error without API key"""
        with patch('noon_scraper.ScraperAPIClient'):
            with self.assertRaises(ValueError) as ctx:
                NoonScraper()
            self.assertIn('SCRAPERAPI_KEY', str(ctx.exception))
    
    def test_parse_price_simple(self):
        """Test parsing simple price strings"""
        with patch.dict('os.environ', {'SCRAPERAPI_KEY': 'test'}):
            with patch('noon_scraper.ScraperAPIClient'):
                scraper = NoonScraper()
        
        self.assertEqual(scraper._parse_price('99.99'), 99.99)
        self.assertEqual(scraper._parse_price('SAR 99.99'), 99.99)
        self.assertEqual(scraper._parse_price('1,299.00'), 1299.0)
        self.assertEqual(scraper._parse_price(''), 0.0)
    
    def test_parse_price_with_currency(self):
        """Test parsing price with currency symbols"""
        with patch.dict('os.environ', {'SCRAPERAPI_KEY': 'test'}):
            with patch('noon_scraper.ScraperAPIClient'):
                scraper = NoonScraper()
        
        self.assertEqual(scraper._parse_price('SAR 1,500.00'), 1500.0)
        self.assertEqual(scraper._parse_price('ر.س 250'), 250.0)


class TestParseProduct(unittest.TestCase):
    """Tests for HTML parsing"""
    
    def setUp(self):
        with patch.dict('os.environ', {'SCRAPERAPI_KEY': 'test'}):
            with patch('noon_scraper.ScraperAPIClient'):
                self.scraper = NoonScraper()
    
    def test_parse_product_basic_html(self):
        """Test parsing basic product HTML"""
        html = '''
        <html>
            <h1 data-qa="pdp-name">Test Product Name</h1>
            <span data-qa="pdp-price-final">SAR 99.99</span>
            <a data-qa="pdp-seller-name">Test Seller</a>
        </html>
        '''
        
        product = self.scraper._parse_product(html, 'https://noon.com/test', 'N123')
        
        self.assertIsNotNone(product)
        self.assertEqual(product.sku, 'N123')
        self.assertEqual(product.product_name, 'Test Product Name')
        self.assertEqual(product.price, 99.99)
        self.assertEqual(product.seller, 'Test Seller')
        self.assertTrue(product.in_stock)
    
    def test_parse_product_with_discount(self):
        """Test parsing product with discount"""
        html = '''
        <html>
            <h1 data-qa="pdp-name">Discounted Item</h1>
            <span data-qa="pdp-price-final">SAR 75.00</span>
            <span data-qa="pdp-price-was">SAR 100.00</span>
            <a data-qa="pdp-seller-name">noon</a>
        </html>
        '''
        
        product = self.scraper._parse_product(html, 'https://noon.com/test', 'N456')
        
        self.assertIsNotNone(product)
        self.assertEqual(product.price, 75.0)
        self.assertEqual(product.original_price, 100.0)
        self.assertEqual(product.discount_pct, 25.0)
    
    def test_parse_product_out_of_stock(self):
        """Test parsing out of stock product"""
        html = '''
        <html>
            <h1 data-qa="pdp-name">Out of Stock Item</h1>
            <span data-qa="pdp-price-final">SAR 50.00</span>
            <div data-qa="pdp-out-of-stock">Out of Stock</div>
        </html>
        '''
        
        product = self.scraper._parse_product(html, 'https://noon.com/test', 'N789')
        
        self.assertIsNotNone(product)
        self.assertFalse(product.in_stock)


class TestRetryLogic(unittest.TestCase):
    """Tests for retry and error handling"""
    
    def test_retry_delays_configured(self):
        """Test retry delays are properly configured"""
        self.assertEqual(len(RETRY_DELAYS), 3)
        self.assertEqual(RETRY_DELAYS, [5, 10, 20])


if __name__ == '__main__':
    unittest.main()
