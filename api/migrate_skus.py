#!/usr/bin/env python3
"""
Migration script: Move SKUs from file to PostgreSQL
Creates admin user and imports existing SKUs
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models_db import User, SKU, Base, get_engine
from db_session import get_db_context, engine
from auth import hash_password

# Configuration
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@noon-ecommerce.local')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin123!')
SKU_FILE_PATH = os.environ.get('SKU_FILE_PATH', '/home/sysadmin/ai-dev-team/workspace/Noon-E-Commerce/skus.txt')


def migrate():
    """Run migration"""
    print("=" * 60)
    print("Noon-E-Commerce Migration: File → PostgreSQL")
    print("=" * 60)
    
    with get_db_context() as db:
        # 1. Create admin user if not exists
        print(f"\n[1/3] Creating admin user: {ADMIN_EMAIL}")
        admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        
        if admin:
            print(f"  ⏭️  Admin user already exists (ID: {admin.id})")
        else:
            admin = User(
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
                is_admin=True,
                is_active=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print(f"  ✅ Created admin user (ID: {admin.id})")
            print(f"  📧 Email: {ADMIN_EMAIL}")
            print(f"  🔑 Password: {ADMIN_PASSWORD}")
        
        # 2. Read SKUs from file
        print(f"\n[2/3] Reading SKUs from: {SKU_FILE_PATH}")
        
        if not os.path.exists(SKU_FILE_PATH):
            print(f"  ⚠️  File not found: {SKU_FILE_PATH}")
            sku_codes = []
        else:
            with open(SKU_FILE_PATH, 'r') as f:
                sku_codes = [line.strip().upper() for line in f if line.strip()]
            print(f"  📄 Found {len(sku_codes)} SKUs in file")
        
        # 3. Import SKUs
        print(f"\n[3/3] Importing SKUs to PostgreSQL")
        
        created = 0
        skipped = 0
        errors = []
        
        for sku_code in sku_codes:
            try:
                # Check if exists
                existing = db.query(SKU).filter(
                    SKU.user_id == admin.id,
                    SKU.sku_code == sku_code
                ).first()
                
                if existing:
                    skipped += 1
                    continue
                
                # Create SKU
                sku = SKU(
                    user_id=admin.id,
                    sku_code=sku_code,
                    product_url=f'https://www.noon.com/saudi-en/{sku_code}/p/',
                    is_active=True
                )
                db.add(sku)
                created += 1
                
            except Exception as e:
                errors.append(f"{sku_code}: {str(e)}")
        
        db.commit()
        
        print(f"  ✅ Created: {created}")
        print(f"  ⏭️  Skipped (duplicates): {skipped}")
        
        if errors:
            print(f"  ❌ Errors: {len(errors)}")
            for err in errors[:5]:
                print(f"     - {err}")
        
        # Summary
        total_skus = db.query(SKU).filter(SKU.user_id == admin.id).count()
        print(f"\n{'=' * 60}")
        print(f"Migration complete!")
        print(f"Admin user: {ADMIN_EMAIL}")
        print(f"Total SKUs: {total_skus}")
        print(f"{'=' * 60}")


if __name__ == '__main__':
    migrate()
