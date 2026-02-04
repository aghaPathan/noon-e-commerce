#!/usr/bin/env python3
"""
API Integration Tests for Noon-E-Commerce
Phase 9: Automated endpoint validation

Run: python3 test_api.py [--base-url http://localhost:8096]
"""

import sys
import json
import argparse
import requests
from typing import Optional, Dict, Any

class APITester:
    def __init__(self, base_url: str = "http://localhost:8096"):
        self.base_url = base_url.rstrip('/')
        self.token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.results = {"passed": 0, "failed": 0, "tests": []}
    
    def log(self, test: str, passed: bool, detail: str = ""):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test}" + (f" - {detail}" if detail else ""))
        self.results["tests"].append({"test": test, "passed": passed, "detail": detail})
        if passed:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
    
    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.pop("headers", {})
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return requests.request(method, url, headers=headers, **kwargs)
    
    # ========== Health ==========
    def test_health(self):
        print("\n🏥 Health Check")
        resp = self.request("GET", "/health")
        self.log("GET /health", resp.status_code == 200, f"status={resp.status_code}")
    
    # ========== Auth ==========
    def test_auth(self):
        print("\n🔐 Authentication")
        
        # Register
        email = f"test_{int(__import__('time').time())}@test.com"
        resp = self.request("POST", "/api/auth/register", json={
            "email": email,
            "password": "TestPass123!",
            "full_name": "Test User"
        })
        self.log("POST /api/auth/register", resp.status_code == 201, f"email={email}")
        if resp.status_code == 201:
            self.user_id = resp.json().get("id")
        
        # Login
        resp = self.request("POST", "/api/auth/login", json={
            "email": email,
            "password": "TestPass123!"
        })
        self.log("POST /api/auth/login", resp.status_code == 200)
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
        
        # Get me
        resp = self.request("GET", "/api/auth/me")
        self.log("GET /api/auth/me", resp.status_code == 200 and resp.json().get("email") == email)
        
        # Refresh token
        resp = self.request("POST", "/api/auth/refresh", json={
            "refresh_token": self.refresh_token
        })
        self.log("POST /api/auth/refresh", resp.status_code == 200)
        if resp.status_code == 200:
            self.token = resp.json().get("access_token")
    
    # ========== SKUs ==========
    def test_skus(self):
        print("\n📦 SKU Management")
        
        # Create SKU
        resp = self.request("POST", "/api/skus", json={
            "sku_code": "N12345TEST"
        })
        self.log("POST /api/skus", resp.status_code == 201)
        sku_id = resp.json().get("id") if resp.status_code == 201 else None
        
        # List SKUs
        resp = self.request("GET", "/api/skus")
        self.log("GET /api/skus", resp.status_code == 200 and "items" in resp.json())
        
        if sku_id:
            # Get SKU
            resp = self.request("GET", f"/api/skus/{sku_id}")
            self.log(f"GET /api/skus/{sku_id}", resp.status_code == 200)
            
            # Update SKU
            resp = self.request("PUT", f"/api/skus/{sku_id}", json={
                "target_price": 99.99
            })
            self.log(f"PUT /api/skus/{sku_id}", resp.status_code == 200)
            
            # Get price history
            resp = self.request("GET", f"/api/skus/{sku_id}/price-history")
            self.log(f"GET /api/skus/{sku_id}/price-history", resp.status_code == 200)
            
            # Delete SKU
            resp = self.request("DELETE", f"/api/skus/{sku_id}")
            self.log(f"DELETE /api/skus/{sku_id}", resp.status_code == 204)
        
        # Bulk import
        resp = self.request("POST", "/api/skus/bulk", json={
            "sku_codes": ["N11111111A", "N22222222B"]
        })
        self.log("POST /api/skus/bulk", resp.status_code == 200)
    
    # ========== Alerts ==========
    def test_alerts(self):
        print("\n🔔 Alerts")
        
        # List alerts
        resp = self.request("GET", "/api/alerts")
        self.log("GET /api/alerts", resp.status_code == 200 and "items" in resp.json())
        
        # Unread count
        resp = self.request("GET", "/api/alerts/unread-count")
        self.log("GET /api/alerts/unread-count", resp.status_code == 200)
        
        # Mark all read
        resp = self.request("POST", "/api/alerts/mark-all-read")
        self.log("POST /api/alerts/mark-all-read", resp.status_code == 200)
    
    # ========== Admin ==========
    def test_admin(self):
        print("\n👑 Admin (may fail for non-admin)")
        
        resp = self.request("GET", "/api/admin/stats")
        # 403 is expected for non-admin
        self.log("GET /api/admin/stats", resp.status_code in [200, 403], 
                 f"status={resp.status_code}")
    
    def run_all(self):
        print(f"🧪 Testing API at {self.base_url}")
        print("=" * 50)
        
        self.test_health()
        self.test_auth()
        self.test_skus()
        self.test_alerts()
        self.test_admin()
        
        print("\n" + "=" * 50)
        print(f"📊 Results: {self.results['passed']} passed, {self.results['failed']} failed")
        return self.results["failed"] == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Noon-E-Commerce API")
    parser.add_argument("--base-url", default="http://localhost:8096", help="API base URL")
    args = parser.parse_args()
    
    tester = APITester(args.base_url)
    success = tester.run_all()
    sys.exit(0 if success else 1)
