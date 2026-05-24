"""
Quick script to check database state
"""
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USERNAME'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
}

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

print("=" * 60)
print("DATABASE STATE CHECK")
print("=" * 60)

# Check total counts
cursor.execute("SELECT COUNT(*) FROM users")
user_count = cursor.fetchone()[0]
print(f"\nTotal users: {user_count:,}")

cursor.execute("SELECT COUNT(*) FROM businesses")
business_count = cursor.fetchone()[0]
print(f"Total businesses: {business_count:,}")

cursor.execute("SELECT COUNT(*) FROM reviews")
review_count = cursor.fetchone()[0]
print(f"Total reviews: {review_count:,}")

# Check demo users
print("\n" + "=" * 60)
print("DEMO USERS")
print("=" * 60)

cursor.execute("""
    SELECT user_id, name, display_name, review_count, average_stars
    FROM users
    WHERE display_name IS NOT NULL AND display_name != name
    ORDER BY display_name
""")

demo_users = cursor.fetchall()
print(f"\nFound {len(demo_users)} demo users:\n")

for user in demo_users:
    user_id, name, display_name, review_count, avg_stars = user

    # Check actual reviews in database
    cursor.execute("SELECT COUNT(*) FROM reviews WHERE user_id = %s", (user_id,))
    actual_reviews = cursor.fetchone()[0]

    print(f"{display_name}")
    print(f"  User ID: {user_id}")
    print(f"  Original name: {name}")
    print(f"  Review count (in user table): {review_count}")
    print(f"  Actual reviews (in reviews table): {actual_reviews}")
    print(f"  Average stars: {avg_stars}")
    print()

conn.close()
