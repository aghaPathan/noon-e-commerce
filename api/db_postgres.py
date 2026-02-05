"""
PostgreSQL Database Connection for Noon-E-Commerce
Matches postgres_schema.sql: users, products, watchlist, price_alerts
"""

import os
from contextlib import contextmanager
from typing import Optional, List, Dict, Tuple
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration - noon_app database
DB_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
DB_PORT = int(os.environ.get('POSTGRES_PORT', '5432'))
DB_USER = os.environ.get('POSTGRES_USER', 'noon_user')
DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
if not DB_PASSWORD:
    raise RuntimeError("POSTGRES_PASSWORD environment variable is required")
DB_NAME = os.environ.get('POSTGRES_DB', 'noon_app')


@contextmanager
def get_db():
    """Get database connection context manager"""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursor_factory=RealDictCursor
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class UserDB:
    """User database operations"""
    
    @staticmethod
    def create(email: str, password_hash: str, full_name: str = None, role: str = 'user') -> Dict:
        """Create new user"""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (email, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s)
                RETURNING id, email, full_name, role, is_active, created_at, updated_at
            """, (email, password_hash, full_name, role))
            return dict(cur.fetchone())
    
    @staticmethod
    def get_by_email(email: str) -> Optional[Dict]:
        """Get user by email"""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, email, password_hash, full_name, role, is_active, created_at, updated_at
                FROM users WHERE email = %s
            """, (email,))
            row = cur.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, email, full_name, role, is_active, created_at, updated_at
                FROM users WHERE id = %s
            """, (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def list_all(page: int = 1, page_size: int = 50) -> Tuple[List[Dict], int]:
        """List all users (admin)"""
        offset = (page - 1) * page_size
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as count FROM users")
            total = cur.fetchone()['count']
            
            cur.execute("""
                SELECT id, email, full_name, role, is_active, created_at, updated_at
                FROM users
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (page_size, offset))
            users = [dict(row) for row in cur.fetchall()]
            return users, total
    
    @staticmethod
    def update(user_id: int, **kwargs) -> Optional[Dict]:
        """Update user"""
        allowed = {'role', 'is_active', 'full_name'}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return UserDB.get_by_id(user_id)
        
        set_clause = ', '.join(f"{k} = %s" for k in updates.keys())
        values = list(updates.values()) + [user_id]
        
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(f"""
                UPDATE users SET {set_clause}, updated_at = NOW()
                WHERE id = %s
                RETURNING id, email, full_name, role, is_active, created_at, updated_at
            """, values)
            row = cur.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def delete(user_id: int) -> bool:
        """Delete user"""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            return cur.rowcount > 0


class ProductDB:
    """Product (master data) database operations"""
    
    @staticmethod
    def get_by_sku(sku: str) -> Optional[Dict]:
        """Get product by SKU"""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM products WHERE sku = %s", (sku,))
            row = cur.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_by_id(product_id: int) -> Optional[Dict]:
        """Get product by ID"""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def create_or_update(sku: str, name: str = None, category: str = None,
                         brand: str = None, url: str = None, image_url: str = None) -> Dict:
        """Create or update product"""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO products (sku, name, category, brand, url, image_url)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (sku) DO UPDATE SET
                    name = COALESCE(EXCLUDED.name, products.name),
                    category = COALESCE(EXCLUDED.category, products.category),
                    brand = COALESCE(EXCLUDED.brand, products.brand),
                    url = COALESCE(EXCLUDED.url, products.url),
                    image_url = COALESCE(EXCLUDED.image_url, products.image_url),
                    updated_at = NOW()
                RETURNING *
            """, (sku, name or f'Product {sku}', category, brand, url, image_url))
            return dict(cur.fetchone())
    
    @staticmethod
    def list_all(page: int = 1, page_size: int = 50) -> Tuple[List[Dict], int]:
        """List all products"""
        offset = (page - 1) * page_size
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as count FROM products WHERE active = true")
            total = cur.fetchone()['count']
            
            cur.execute("""
                SELECT * FROM products WHERE active = true
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (page_size, offset))
            return [dict(row) for row in cur.fetchall()], total


class WatchlistDB:
    """Watchlist (user-scoped SKU tracking) database operations"""
    
    @staticmethod
    def add(user_id: int, sku: str, target_price: float = None) -> Dict:
        """Add SKU to user's watchlist"""
        # Ensure product exists
        product = ProductDB.get_by_sku(sku)
        if not product:
            ProductDB.create_or_update(sku, name=f'Product {sku}')
        
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO watchlist (user_id, sku, target_price)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, sku) DO UPDATE SET
                    target_price = COALESCE(EXCLUDED.target_price, watchlist.target_price)
                RETURNING *
            """, (user_id, sku, target_price))
            return dict(cur.fetchone())
    
    @staticmethod
    def get_by_id(watchlist_id: int, user_id: int = None) -> Optional[Dict]:
        """Get watchlist item by ID"""
        with get_db() as conn:
            cur = conn.cursor()
            if user_id:
                cur.execute("""
                    SELECT w.*, p.name as product_name, p.brand, p.category, p.url, p.image_url
                    FROM watchlist w
                    LEFT JOIN products p ON w.sku = p.sku
                    WHERE w.id = %s AND w.user_id = %s
                """, (watchlist_id, user_id))
            else:
                cur.execute("""
                    SELECT w.*, p.name as product_name, p.brand, p.category, p.url, p.image_url
                    FROM watchlist w
                    LEFT JOIN products p ON w.sku = p.sku
                    WHERE w.id = %s
                """, (watchlist_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_by_sku(user_id: int, sku: str) -> Optional[Dict]:
        """Get watchlist item by user and SKU"""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT w.*, p.name as product_name, p.brand, p.category, p.url, p.image_url
                FROM watchlist w
                LEFT JOIN products p ON w.sku = p.sku
                WHERE w.user_id = %s AND w.sku = %s
            """, (user_id, sku))
            row = cur.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def list_by_user(user_id: int, page: int = 1, page_size: int = 50,
                     search: str = None, sort_by: str = 'created_at',
                     sort_order: str = 'desc') -> Tuple[List[Dict], int]:
        """List user's watchlist with pagination and search"""
        offset = (page - 1) * page_size
        
        # Validate sort
        allowed_sorts = {'created_at', 'target_price', 'sku'}
        sort_by = sort_by if sort_by in allowed_sorts else 'created_at'
        sort_order = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
        
        with get_db() as conn:
            cur = conn.cursor()
            
            where = "w.user_id = %s"
            params = [user_id]
            
            if search:
                where += " AND (w.sku ILIKE %s OR p.name ILIKE %s)"
                params.extend([f'%{search}%', f'%{search}%'])
            
            # Count
            cur.execute(f"""
                SELECT COUNT(*) as count FROM watchlist w
                LEFT JOIN products p ON w.sku = p.sku
                WHERE {where}
            """, params)
            total = cur.fetchone()['count']
            
            # Map sort_by for joined query
            sort_col = f"w.{sort_by}" if sort_by != 'product_name' else "p.name"
            
            # Fetch
            cur.execute(f"""
                SELECT w.*, p.name as product_name, p.brand, p.category, p.url, p.image_url
                FROM watchlist w
                LEFT JOIN products p ON w.sku = p.sku
                WHERE {where}
                ORDER BY {sort_col} {sort_order}
                LIMIT %s OFFSET %s
            """, params + [page_size, offset])
            items = [dict(row) for row in cur.fetchall()]
            return items, total
    
    @staticmethod
    def list_all(page: int = 1, page_size: int = 50) -> Tuple[List[Dict], int]:
        """List all watchlist items (admin)"""
        offset = (page - 1) * page_size
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as count FROM watchlist")
            total = cur.fetchone()['count']
            
            cur.execute("""
                SELECT w.*, p.name as product_name, u.email as user_email
                FROM watchlist w
                LEFT JOIN products p ON w.sku = p.sku
                JOIN users u ON w.user_id = u.id
                ORDER BY w.created_at DESC
                LIMIT %s OFFSET %s
            """, (page_size, offset))
            return [dict(row) for row in cur.fetchall()], total
    
    @staticmethod
    def update(watchlist_id: int, user_id: int, **kwargs) -> Optional[Dict]:
        """Update watchlist item"""
        allowed = {'target_price', 'notify_on_drop'}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return WatchlistDB.get_by_id(watchlist_id, user_id)
        
        set_clause = ', '.join(f"{k} = %s" for k in updates.keys())
        values = list(updates.values()) + [watchlist_id, user_id]
        
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(f"""
                UPDATE watchlist SET {set_clause}
                WHERE id = %s AND user_id = %s
                RETURNING *
            """, values)
            row = cur.fetchone()
            if row:
                return WatchlistDB.get_by_id(row['id'], user_id)
            return None
    
    @staticmethod
    def delete(watchlist_id: int, user_id: int) -> bool:
        """Remove item from watchlist"""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                DELETE FROM watchlist WHERE id = %s AND user_id = %s
            """, (watchlist_id, user_id))
            return cur.rowcount > 0
    
    @staticmethod
    def bulk_add(user_id: int, sku_codes: List[str]) -> List[Dict]:
        """Bulk add SKUs to watchlist"""
        created = []
        for sku in sku_codes:
            try:
                item = WatchlistDB.add(user_id, sku)
                created.append(item)
            except Exception:
                continue  # Skip duplicates or errors
        return created
    
    @staticmethod
    def get_all_skus() -> List[str]:
        """Get all unique SKUs being tracked"""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT sku FROM watchlist")
            return [row['sku'] for row in cur.fetchall()]


class PriceAlertDB:
    """Price alert database operations"""
    
    @staticmethod
    def create(user_id: int, sku: str, old_price: float, new_price: float,
               alert_type: str = 'price_drop') -> Dict:
        """Create price alert"""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO price_alerts (user_id, sku, old_price, new_price, alert_type)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
            """, (user_id, sku, old_price, new_price, alert_type))
            return dict(cur.fetchone())
    
    @staticmethod
    def list_by_user(user_id: int, page: int = 1, page_size: int = 50,
                     unread_only: bool = False) -> Tuple[List[Dict], int]:
        """List alerts for user"""
        offset = (page - 1) * page_size
        with get_db() as conn:
            cur = conn.cursor()
            
            where = "user_id = %s"
            params = [user_id]
            if unread_only:
                where += " AND read_at IS NULL"
            
            cur.execute(f"SELECT COUNT(*) as count FROM price_alerts WHERE {where}", params)
            total = cur.fetchone()['count']
            
            cur.execute(f"""
                SELECT * FROM price_alerts
                WHERE {where}
                ORDER BY sent_at DESC
                LIMIT %s OFFSET %s
            """, params + [page_size, offset])
            return [dict(row) for row in cur.fetchall()], total
    
    @staticmethod
    def mark_read(alert_id: int, user_id: int) -> bool:
        """Mark alert as read"""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE price_alerts SET read_at = NOW()
                WHERE id = %s AND user_id = %s
            """, (alert_id, user_id))
            return cur.rowcount > 0


def get_stats() -> Dict:
    """Get admin statistics"""
    with get_db() as conn:
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) as count FROM users WHERE is_active = TRUE")
        total_users = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM products WHERE active = TRUE")
        total_products = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM watchlist")
        total_watchlist = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM price_alerts")
        total_alerts = cur.fetchone()['count']
        
        cur.execute("""
            SELECT COUNT(*) as count FROM users 
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)
        new_users_week = cur.fetchone()['count']
        
        return {
            'total_users': total_users,
            'total_products': total_products,
            'total_watchlist_items': total_watchlist,
            'total_alerts': total_alerts,
            'new_users_this_week': new_users_week
        }
