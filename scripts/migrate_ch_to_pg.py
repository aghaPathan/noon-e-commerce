#!/usr/bin/env python3
"""
Phase 2: ClickHouse to PostgreSQL Migration Script

Migrates product master data from ClickHouse to PostgreSQL.
Price history stays in ClickHouse (time-series optimized).

Usage:
    python migrate_ch_to_pg.py [--dry-run]
"""
import argparse
import sys
from datetime import datetime
from clickhouse_driver import Client as CHClient
import psycopg2
from psycopg2.extras import execute_values
import hashlib

# ============================================
# Configuration
# ============================================

CLICKHOUSE = {
    'host': 'localhost',
    'user': 'default',
    'password': 'Changeme_123',
    'database': 'noon_intelligence'
}

POSTGRES = {
    'host': 'localhost',
    'port': 5432,
    'user': 'noon_user',
    'password': 'NoonApp_2026!',
    'database': 'noon_app'
}

DEFAULT_ADMIN = {
    'email': 'admin@noon-intel.local',
    'password': 'Admin123!',  # Will be hashed
    'full_name': 'System Administrator',
    'role': 'admin'
}


# ============================================
# Helpers
# ============================================

def hash_password(password: str) -> str:
    """Simple password hash (use passlib in production)."""
    # Using SHA256 for migration; Phase 3 will use passlib/bcrypt
    return hashlib.sha256(password.encode()).hexdigest()


def get_ch_client():
    """Get ClickHouse client."""
    return CHClient(
        host=CLICKHOUSE['host'],
        user=CLICKHOUSE['user'],
        password=CLICKHOUSE['password'],
        database=CLICKHOUSE['database']
    )


def get_pg_conn():
    """Get PostgreSQL connection."""
    return psycopg2.connect(
        host=POSTGRES['host'],
        port=POSTGRES['port'],
        user=POSTGRES['user'],
        password=POSTGRES['password'],
        database=POSTGRES['database']
    )


# ============================================
# Migration Functions
# ============================================

def create_admin_user(pg_conn, dry_run=False):
    """Create default admin user if not exists."""
    print("\n[1/4] Creating default admin user...")
    
    cursor = pg_conn.cursor()
    
    # Check if admin exists
    cursor.execute(
        "SELECT id, email FROM users WHERE email = %s",
        (DEFAULT_ADMIN['email'],)
    )
    existing = cursor.fetchone()
    
    if existing:
        print(f"  ✓ Admin already exists: {existing[1]} (id={existing[0]})")
        return existing[0]
    
    if dry_run:
        print(f"  [DRY-RUN] Would create admin: {DEFAULT_ADMIN['email']}")
        return None
    
    # Create admin
    password_hash = hash_password(DEFAULT_ADMIN['password'])
    cursor.execute("""
        INSERT INTO users (email, password_hash, full_name, role, is_active, email_verified)
        VALUES (%s, %s, %s, %s, true, true)
        RETURNING id
    """, (
        DEFAULT_ADMIN['email'],
        password_hash,
        DEFAULT_ADMIN['full_name'],
        DEFAULT_ADMIN['role']
    ))
    
    admin_id = cursor.fetchone()[0]
    pg_conn.commit()
    
    print(f"  ✓ Created admin: {DEFAULT_ADMIN['email']} (id={admin_id})")
    print(f"    Password: {DEFAULT_ADMIN['password']}")
    return admin_id


def fetch_ch_products(ch_client):
    """Fetch all products from ClickHouse."""
    print("\n[2/4] Fetching products from ClickHouse...")
    
    products = ch_client.execute("""
        SELECT 
            sku,
            name,
            category,
            brand,
            url,
            active,
            created_at,
            updated_at
        FROM products
    """)
    
    print(f"  ✓ Found {len(products)} products in ClickHouse")
    return products


def migrate_products(pg_conn, products, dry_run=False):
    """Migrate products to PostgreSQL."""
    print("\n[3/4] Migrating products to PostgreSQL...")
    
    if not products:
        print("  ⚠ No products to migrate")
        return 0
    
    cursor = pg_conn.cursor()
    
    # Check existing products
    cursor.execute("SELECT sku FROM products")
    existing_skus = {row[0] for row in cursor.fetchall()}
    
    # Filter new products
    new_products = [p for p in products if p[0] not in existing_skus]
    skipped = len(products) - len(new_products)
    
    if skipped > 0:
        print(f"  ⚠ Skipping {skipped} existing products")
    
    if not new_products:
        print("  ✓ All products already migrated")
        return 0
    
    if dry_run:
        print(f"  [DRY-RUN] Would insert {len(new_products)} products")
        for p in new_products[:3]:
            print(f"    - {p[0]}: {p[1][:50]}...")
        if len(new_products) > 3:
            print(f"    ... and {len(new_products) - 3} more")
        return len(new_products)
    
    # Insert products
    insert_query = """
        INSERT INTO products (sku, name, category, brand, url, active, created_at, updated_at)
        VALUES %s
        ON CONFLICT (sku) DO UPDATE SET
            name = EXCLUDED.name,
            category = EXCLUDED.category,
            brand = EXCLUDED.brand,
            url = EXCLUDED.url,
            active = EXCLUDED.active,
            updated_at = EXCLUDED.updated_at
    """
    
    # Convert ClickHouse data to PostgreSQL format
    pg_products = [
        (
            p[0],  # sku
            p[1],  # name
            p[2],  # category
            p[3],  # brand
            p[4] if p[4] else None,  # url
            bool(p[5]),  # active
            p[6],  # created_at
            p[7]   # updated_at
        )
        for p in new_products
    ]
    
    execute_values(cursor, insert_query, pg_products)
    pg_conn.commit()
    
    print(f"  ✓ Migrated {len(new_products)} products")
    return len(new_products)


def validate_migration(ch_client, pg_conn):
    """Validate data integrity after migration."""
    print("\n[4/4] Validating migration...")
    
    # Count in ClickHouse
    ch_count = ch_client.execute("SELECT count() FROM products")[0][0]
    
    # Count in PostgreSQL
    cursor = pg_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    pg_count = cursor.fetchone()[0]
    
    # Sample check - get random SKU and compare
    ch_sample = ch_client.execute("SELECT sku, name FROM products LIMIT 1")
    if ch_sample:
        sku, ch_name = ch_sample[0]
        cursor.execute("SELECT name FROM products WHERE sku = %s", (sku,))
        pg_result = cursor.fetchone()
        pg_name = pg_result[0] if pg_result else None
        
        if pg_name == ch_name:
            print(f"  ✓ Sample validation passed: {sku}")
        else:
            print(f"  ⚠ Sample mismatch for {sku}: CH='{ch_name}' vs PG='{pg_name}'")
    
    # Final counts
    print(f"\n  Summary:")
    print(f"    ClickHouse products: {ch_count}")
    print(f"    PostgreSQL products: {pg_count}")
    
    if ch_count == pg_count:
        print(f"  ✓ Counts match!")
        return True
    else:
        print(f"  ⚠ Count mismatch (CH: {ch_count}, PG: {pg_count})")
        return False


# ============================================
# Main
# ============================================

def main():
    parser = argparse.ArgumentParser(description='Migrate ClickHouse data to PostgreSQL')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    args = parser.parse_args()
    
    print("=" * 60)
    print("SKU Price Tracker - Phase 2: Data Migration")
    print("=" * 60)
    
    if args.dry_run:
        print("\n*** DRY RUN MODE - No changes will be made ***\n")
    
    try:
        # Connect to databases
        print("Connecting to databases...")
        ch_client = get_ch_client()
        pg_conn = get_pg_conn()
        print("  ✓ Connected to ClickHouse")
        print("  ✓ Connected to PostgreSQL")
        
        # Step 1: Create admin user
        admin_id = create_admin_user(pg_conn, args.dry_run)
        
        # Step 2: Fetch products from ClickHouse
        products = fetch_ch_products(ch_client)
        
        # Step 3: Migrate products to PostgreSQL
        migrated = migrate_products(pg_conn, products, args.dry_run)
        
        # Step 4: Validate migration
        if not args.dry_run:
            valid = validate_migration(ch_client, pg_conn)
        else:
            print("\n[4/4] Skipping validation (dry-run)")
            valid = True
        
        # Cleanup
        pg_conn.close()
        
        print("\n" + "=" * 60)
        if args.dry_run:
            print("DRY RUN COMPLETE - No changes made")
        elif valid:
            print("MIGRATION COMPLETE ✓")
        else:
            print("MIGRATION COMPLETE (with warnings)")
        print("=" * 60)
        
        return 0 if valid else 1
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
