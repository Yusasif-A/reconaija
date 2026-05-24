"""
Database layer for MySQL operations
Handles all SQL queries for users, businesses, and reviews
"""

import pymysql
from contextlib import contextmanager

try:
    from config import DB_CONFIG
except ModuleNotFoundError:
    from backend.config import DB_CONFIG

@contextmanager
def get_db():
    """Context manager for MySQL connection"""
    conn = pymysql.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()

def get_user_reviews(user_id: str, limit: int = 15) -> list[dict]:
    """Fetch the most recent reviews for a user"""
    with get_db() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT r.stars, r.text, r.date, b.name as business_name, b.categories
            FROM reviews r
            JOIN businesses b ON r.business_id = b.business_id
            WHERE r.user_id = %s
            ORDER BY r.date DESC
            LIMIT %s
        """, (user_id, limit))
        return cursor.fetchall()

def get_user_profile(user_id: str) -> dict:
    """Get user's aggregate stats"""
    with get_db() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT u.*,
                   AVG(r.stars) as computed_avg,
                   COUNT(r.review_id) as total_reviews
            FROM users u
            LEFT JOIN reviews r ON u.user_id = r.user_id
            WHERE u.user_id = %s
            GROUP BY u.user_id
        """, (user_id,))
        result = cursor.fetchone()
        return result if result else {}

def get_business_info(business_name: str) -> dict:
    """Find a business by name (fuzzy search)"""
    with get_db() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT * FROM businesses
            WHERE name LIKE %s
            LIMIT 1
        """, (f"%{business_name}%",))
        result = cursor.fetchone()
        return result if result else {}

def get_businesses_not_reviewed_by_user(user_id: str, category: str = None, limit: int = 50) -> list[dict]:
    """Get businesses the user has NOT reviewed yet — for Task B candidates"""
    with get_db() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        query = """
            SELECT b.* FROM businesses b
            WHERE b.business_id NOT IN (
                SELECT business_id FROM reviews WHERE user_id = %s
            )
        """
        params = [user_id]

        if category:
            query += " AND b.categories LIKE %s"
            params.append(f"%{category}%")

        query += " ORDER BY b.stars DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Fallback: if user has reviewed everything, just return top-rated businesses
        if not results:
            print(f"[Database] User {user_id} has reviewed all businesses, returning top-rated instead")

            # Try with category filter first
            if category:
                query = "SELECT * FROM businesses WHERE categories LIKE %s ORDER BY stars DESC, review_count DESC LIMIT %s"
                cursor.execute(query, (f"%{category}%", limit))
                results = cursor.fetchall()

            # If still empty, ignore category and just return top businesses
            if not results:
                print(f"[Database] No businesses found for category '{category}', returning all top-rated")
                query = "SELECT * FROM businesses ORDER BY stars DESC, review_count DESC LIMIT %s"
                cursor.execute(query, (limit,))
                results = cursor.fetchall()

        print(f"[Database] Returning {len(results)} candidate businesses")
        return results

def get_demo_users() -> list[dict]:
    """Get curated demo users for the dropdown"""
    with get_db() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT user_id, name, display_name, average_stars, review_count
            FROM users
            WHERE display_name != name AND display_name IS NOT NULL
            ORDER BY display_name
        """)
        return cursor.fetchall()

def get_all_businesses(limit: int = 1000) -> list[dict]:
    """Get all businesses for ChromaDB index building"""
    with get_db() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT business_id, name, categories, city, state, stars
            FROM businesses
            LIMIT %s
        """, (limit,))
        return cursor.fetchall()

def get_user_reviewed_businesses(user_id: str) -> list[str]:
    """Get list of business names the user has already reviewed"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.name
            FROM reviews r
            JOIN businesses b ON r.business_id = b.business_id
            WHERE r.user_id = %s
        """, (user_id,))
        results = cursor.fetchall()
        return [row[0] for row in results]

def get_user_primary_category(user_id: str) -> str:
    """Get the category the user reviews most frequently"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.categories, COUNT(*) as count
            FROM reviews r
            JOIN businesses b ON r.business_id = b.business_id
            WHERE r.user_id = %s AND b.categories IS NOT NULL
            GROUP BY b.categories
            ORDER BY count DESC
            LIMIT 1
        """, (user_id,))
        result = cursor.fetchone()
        if result and result[0]:
            # Extract first category from comma-separated list
            categories = result[0].split(',')
            return categories[0].strip() if categories else "Restaurants"
        return "Restaurants"
