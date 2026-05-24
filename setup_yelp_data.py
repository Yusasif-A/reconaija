"""
Load Yelp JSON files into SQLite database for the hackathon.
This creates a subset of the data (500k reviews, 150k businesses, 100k users).

Usage:
    python setup_yelp_data.py
"""

import json
import sqlite3
from tqdm import tqdm
import os

# Paths
DB_PATH = "data/yelp_reviews.db"
REVIEWS_PATH = "yelp_academic_dataset_review.json"
BUSINESS_PATH = "yelp_academic_dataset_business.json"
USER_PATH = "yelp_academic_dataset_user.json"

# Subset sizes
MAX_REVIEWS = 500_000
MAX_BUSINESSES = 150_000
MAX_USERS = 100_000

def setup_database():
    """Create SQLite database and tables"""
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            review_count INTEGER,
            average_stars REAL,
            display_name TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            business_id TEXT PRIMARY KEY,
            name TEXT,
            categories TEXT,
            city TEXT,
            state TEXT,
            stars REAL,
            review_count INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            review_id TEXT PRIMARY KEY,
            user_id TEXT,
            business_id TEXT,
            stars INTEGER,
            text TEXT,
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (business_id) REFERENCES businesses(business_id)
        )
    """)

    conn.commit()
    return conn

def load_businesses(conn):
    """Load businesses from JSON into SQLite"""
    print(f"\n📦 Loading businesses (max {MAX_BUSINESSES:,})...")

    cursor = conn.cursor()
    businesses = []
    count = 0

    with open(BUSINESS_PATH, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc="Reading businesses", unit=" businesses"):
            if count >= MAX_BUSINESSES:
                break

            try:
                b = json.loads(line)
                categories = b.get("categories") or ""

                cursor.execute(
                    "INSERT OR IGNORE INTO businesses VALUES (?,?,?,?,?,?,?)",
                    (
                        b["business_id"],
                        b["name"],
                        categories,
                        b.get("city", ""),
                        b.get("state", ""),
                        b.get("stars", 0),
                        b.get("review_count", 0)
                    )
                )

                businesses.append({
                    "business_id": b["business_id"],
                    "name": b["name"],
                    "categories": categories,
                    "city": b.get("city", ""),
                    "stars": b.get("stars", 0)
                })

                count += 1
            except Exception as e:
                print(f"Error loading business: {e}")
                continue

    conn.commit()
    print(f"✅ Loaded {count:,} businesses")
    return businesses

def load_users(conn):
    """Load users from JSON into SQLite"""
    print(f"\n👥 Loading users (max {MAX_USERS:,})...")

    cursor = conn.cursor()
    count = 0

    with open(USER_PATH, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc="Reading users", unit=" users"):
            if count >= MAX_USERS:
                break

            try:
                u = json.loads(line)

                cursor.execute(
                    "INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)",
                    (
                        u["user_id"],
                        u.get("name", "Anonymous"),
                        u.get("review_count", 0),
                        u.get("average_stars", 0),
                        u.get("name", "Anonymous")  # display_name same as name initially
                    )
                )

                count += 1
            except Exception as e:
                print(f"Error loading user: {e}")
                continue

    conn.commit()
    print(f"✅ Loaded {count:,} users")

def load_reviews(conn):
    """Load reviews from JSON into SQLite"""
    print(f"\n⭐ Loading reviews (max {MAX_REVIEWS:,})...")

    cursor = conn.cursor()
    count = 0

    with open(REVIEWS_PATH, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc="Reading reviews", unit=" reviews"):
            if count >= MAX_REVIEWS:
                break

            try:
                r = json.loads(line)

                cursor.execute(
                    "INSERT OR IGNORE INTO reviews VALUES (?,?,?,?,?,?)",
                    (
                        r["review_id"],
                        r["user_id"],
                        r["business_id"],
                        int(r["stars"]),
                        r["text"],
                        r["date"]
                    )
                )

                count += 1

                # Commit every 10k rows for performance
                if count % 10000 == 0:
                    conn.commit()

            except Exception as e:
                print(f"Error loading review: {e}")
                continue

    conn.commit()
    print(f"✅ Loaded {count:,} reviews")

def create_demo_users(conn):
    """Create curated demo users for the dropdown"""
    print("\n🎭 Finding interesting demo users...")

    cursor = conn.cursor()

    # Find users with different characteristics
    demo_users = []

    # The Harsh Critic (low average stars)
    cursor.execute("""
        SELECT user_id, name, average_stars, review_count
        FROM users
        WHERE average_stars < 2.5 AND review_count > 20
        ORDER BY average_stars ASC
        LIMIT 1
    """)
    harsh = cursor.fetchone()
    if harsh:
        demo_users.append((harsh[0], "The Harsh Critic", f"{harsh[1]} - Avg {harsh[2]:.1f}★, {harsh[3]} reviews"))

    # The Hype Person (high average stars)
    cursor.execute("""
        SELECT user_id, name, average_stars, review_count
        FROM users
        WHERE average_stars > 4.5 AND review_count > 20
        ORDER BY average_stars DESC
        LIMIT 1
    """)
    hype = cursor.fetchone()
    if hype:
        demo_users.append((hype[0], "The Hype Person", f"{hype[1]} - Avg {hype[2]:.1f}★, {hype[3]} reviews"))

    # The Prolific Reviewer (many reviews)
    cursor.execute("""
        SELECT user_id, name, average_stars, review_count
        FROM users
        WHERE review_count > 100
        ORDER BY review_count DESC
        LIMIT 1
    """)
    prolific = cursor.fetchone()
    if prolific:
        demo_users.append((prolific[0], "The Prolific Reviewer", f"{prolific[1]} - {prolific[3]} reviews"))

    # Update display names
    for user_id, display_name, description in demo_users:
        cursor.execute(
            "UPDATE users SET display_name = ? WHERE user_id = ?",
            (display_name, user_id)
        )
        print(f"  ✅ {display_name}: {description}")

    conn.commit()
    print(f"\n✅ Created {len(demo_users)} demo users")

def main():
    print("🚀 Setting up Yelp dataset for BCT Hackathon...\n")

    # Create database
    conn = setup_database()

    # Load data
    businesses = load_businesses(conn)
    load_users(conn)
    load_reviews(conn)
    create_demo_users(conn)

    conn.close()

    print("\n" + "="*50)
    print("✅ Setup complete!")
    print("="*50)
    print(f"\nDatabase created at: {DB_PATH}")
    print("\nNext steps:")
    print("1. Build FAISS index: python build_faiss_index.py")
    print("2. Start backend: cd backend && uvicorn main:app --reload")
    print("3. Start frontend: cd frontend && npm start")

if __name__ == "__main__":
    main()