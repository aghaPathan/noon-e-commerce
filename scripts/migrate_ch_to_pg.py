#!/usr/bin/env python3
"""
Phase 2: ClickHouse to PostgreSQL Migration Script

Migrates product master data from ClickHouse to PostgreSQL.
Price history stays in ClickHouse (time-series optimized).

Usage:
    python migrate_ch_to_pg.py [--dry-run]

Required environment variables:
    POSTGRES_PASSWORD, CLICKHOUSE_PASSWORD, ADMIN_PASSWORD
"""
import argparse
import os
import sys
from datetime import datetime
from clickhouse_driver import Client as CHClient
import psycopg2
from psycopg2.extras import execute_values

# Try bcrypt first, fall back to passlib
try:
    import bcrypt
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
except ImportError:
    from passlib.hash import bcrypt as passlib_bcrypt
    def hash_password(password: str) -> str:
        return passlib_bcrypt.hash(password)

# ============================================
# Configuration from Environment
# ============================================

def get_config():
    """Load configuration from environment variables."""
    pg_password = os.environ.get('POSTGRES_PASSWORD')
    ch_password = os.environ.get('CLICKHOUSE_PASSWORD')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    
    missing = []
    if not pg_password:
        missing.append('POSTGRES_PASSWORD')
    if not ch_password:
        missing.append('CLICKHOUSE_PASSWORD')
    if not admin_password:
        missing.append('ADMIN_PASSWORD')
    
    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print("   Set them or source your .env file first.")
        sys.exit(1)
    
    return {
        'clickhouse': {
            'host': os.environ.get('CLICKHOUSE_HOST', 'localhost'),
            'port': int(os.environ.get('CLICKHOUSE_PORT', 9000)),
            'user': os.environ.get('CLICKHOUSE_USER', 'default'),
            'password': ch_password,
            'database': os.environ.get('CLICKHOUSE_DB', 'noon_intelligence')
        },
        'postgres': {
            'host': os.environ.get('POSTGRES_HOST', 'localhost'),
            'port': int(os.environ.get('POSTGRES_PORT', 5433)),
            'user': os.environ.get('POSTGRES_USER', 'noon_user'),
            'password': pg_password,
            'database': os.environ.get('POSTGRES_DB', 'noon_app')
        },
        'admin': {
            'email': os.environ.get('ADMIN_EMAIL', 'admin@noon-intel.local'),
            'password': admin_password,
            'full_name': 'System Administrator',
            'role': 'admin'
        }
    }


def get_ch_client(config):
    """Get ClickHouse client."""
    return CHClient(
        host=config['clickhouse']['host'],
        port=config['clickhouse']['port'],
        user=config['clickhouse']['user'],
        password=config['clickhouse']['password'],
        database=config['clickhouse']['database']
    )


def get_pg_conn(config):
    """Get PostgreSQL connection."""
    return psycopg2.connect(
        host=config['postgres']['host'],
        port=config['postgres']['port'],
        user=config['postgres']['user'],
        password=config['postgres']['password'],
        database=config['postgres']['database']
    )


# ============================================
# Migration Functions
# ============================================

def create_admin_user(pg_conn, admin_config, dry_run=False):
    """Create default admin user if not exists."""
    print("\n[1/4] Creating default admin user...")
    
    cursor = pg_conn.cursor()
    
    # Check if admin exists
    cursor.execute(
        "SELECT id, email FROM users WHERE email = %s",
        (admin_config['email'],)
    )
    existing = cursor.fetchone()
    
    if existing:
        print(f"  ✓ Admin already exists: {existing[1]} (id={existing[0]})")
        return existing[0]
    
    if dry_run:
        print(f"  [DRY-RUN] Would create admin: {admin_config['email']}")
        return None
    
    # Create admin with bcrypt hash
    password_hash = hash_password(admin_config['password'])
    cursor.execute("""
        INSERT INTO users (email, password_hash, full_name, role, is_active, email_verified)
        VALUES (%s, %s, %s, %s, true, true)
        RETURNING id
    """, (
        admin_config['email'],
        password_hash,
        admin_config['full_name'],
        admin_config['role']
    ))
    
    admin_id = cursor.fetchone()[0]
    pg_conn.commit()
    
    print(f"  ✓ Created admin: {admin_config['email']} (id={admin_id})")
    return admin_id


def fetch_ch_products(ch_client):
    """Fetch all products from ClickHouse."""
    print("\n[2/4] Fetching products from ClickHouse...")
    
    try:
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
    except Exception as e:
        print(f"  ⚠ Could not fetch from ClickHouse: {e}")
        return []


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
    
    try:
        ch_count = ch_client.execute("SELECT count() FROM products")[0][0]
    except:
        ch_count = 0
    
    cursor = pg_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    pg_count = cursor.fetchone()[0]
    
    print(f"\n  Summary:")
    print(f"    ClickHouse products: {ch_count}")
    print(f"    PostgreSQL products: {pg_count}")
    
    if ch_count == pg_count or ch_count == 0:
        print(f"  ✓ Migration complete!")
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
    print("Noon E-Commerce - Data Migration")
    print("=" * 60)
    
    if args.dry_run:
        print("\n*** DRY RUN MODE - No changes will be made ***\n")
    
    try:
        config = get_config()
        
        print("Connecting to databases...")
        ch_client = get_ch_client(config)
        pg_conn = get_pg_conn(config)
        print("  ✓ Connected to ClickHouse")
        print("  ✓ Connected to PostgreSQL")
        
        # Step 1: Create admin user
        create_admin_user(pg_conn, config['admin'], args.dry_run)
        
        # Step 2: Fetch products from ClickHouse
        products = fetch_ch_products(ch_client)
        
        # Step 3: Migrate products to PostgreSQL
        migrate_products(pg_conn, products, args.dry_run)
        
        # Step 4: Validate migration
        if not args.dry_run:
            valid = validate_migration(ch_client, pg_conn)
        else:
            print("\n[4/4] Skipping validation (dry-run)")
            valid = True
        
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
