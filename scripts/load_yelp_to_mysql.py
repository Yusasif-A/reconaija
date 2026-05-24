"""
Load Yelp JSON files into MySQL database for BCT Hackathon
Creates Nigerian-themed demo users for authentic local context

Usage:
    python scripts/load_yelp_to_mysql.py
"""

import json
import pymysql
from tqdm import tqdm
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USERNAME'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4',
    'connect_timeout': 60,
    'read_timeout': 60,
    'write_timeout': 60,
    'autocommit': False
}

# File paths
REVIEWS_PATH = "yelp_academic_dataset_review.json"
BUSINESS_PATH = "yelp_academic_dataset_business.json"
USER_PATH = "yelp_academic_dataset_user.json"

# Subset sizes
MAX_REVIEWS = 20_000
MAX_BUSINESSES = 20_000
MAX_USERS = 20_000

def get_connection():
    """Create MySQL connection"""
    return pymysql.connect(**DB_CONFIG)

def setup_database():
    """Create database and tables"""
    print("🔧 Setting up database...")

    # First connect without database to create it
    conn_config = DB_CONFIG.copy()
    db_name = conn_config.pop('database')
    conn = pymysql.connect(**conn_config)
    cursor = conn.cursor()

    # Create database if not exists
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    print(f"✅ Database '{db_name}' ready")
    conn.close()

    # Connect to the database
    conn = get_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255),
            review_count INT,
            average_stars DECIMAL(3,2),
            display_name VARCHAR(255),
            INDEX idx_display_name (display_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Create businesses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            business_id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255),
            categories TEXT,
            city VARCHAR(255),
            state VARCHAR(100),
            stars DECIMAL(3,2),
            review_count INT,
            image_url TEXT,
            INDEX idx_name (name),
            INDEX idx_city (city),
            INDEX idx_stars (stars)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Create reviews table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            review_id VARCHAR(255) PRIMARY KEY,
            user_id VARCHAR(255),
            business_id VARCHAR(255),
            stars INT,
            text TEXT,
            date VARCHAR(50),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (business_id) REFERENCES businesses(business_id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_business_id (business_id),
            INDEX idx_stars (stars)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    conn.commit()
    print("✅ Tables created")
    return conn

def load_businesses(conn):
    """Load businesses from JSON into MySQL"""
    print(f"\n📦 Loading businesses (max {MAX_BUSINESSES:,})...")

    cursor = conn.cursor()
    businesses = []
    batch = []
    batch_size = 500
    count = 0

    with open(BUSINESS_PATH, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc="Reading businesses", unit=" businesses"):
            if count >= MAX_BUSINESSES:
                break

            try:
                b = json.loads(line)
                categories = b.get("categories") or ""

                # Extract image URL (Yelp data may have 'image_url' or 'photos' array)
                image_url = b.get("image_url", "")
                if not image_url and b.get("photos"):
                    # If photos array exists, take the first one
                    image_url = b["photos"][0] if isinstance(b["photos"], list) and len(b["photos"]) > 0 else ""

                batch.append((
                    b["business_id"],
                    b["name"],
                    categories,
                    b.get("city", ""),
                    b.get("state", ""),
                    b.get("stars", 0),
                    b.get("review_count", 0),
                    image_url
                ))

                businesses.append({
                    "business_id": b["business_id"],
                    "name": b["name"],
                    "categories": categories,
                    "city": b.get("city", ""),
                    "stars": b.get("stars", 0)
                })

                count += 1

                # Insert batch when it reaches batch_size
                if len(batch) >= batch_size:
                    cursor.executemany(
                        "INSERT IGNORE INTO businesses VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                        batch
                    )
                    conn.commit()
                    batch = []

            except Exception as e:
                print(f"Error loading business: {e}")
                continue

        # Insert remaining batch
        if batch:
            cursor.executemany(
                "INSERT IGNORE INTO businesses VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                batch
            )
            conn.commit()

    print(f"✅ Loaded {count:,} businesses")
    return businesses

def load_users(conn):
    """Load users from JSON into MySQL"""
    print(f"\n👥 Loading users (max {MAX_USERS:,})...")

    cursor = conn.cursor()
    batch = []
    batch_size = 500
    count = 0

    with open(USER_PATH, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc="Reading users", unit=" users"):
            if count >= MAX_USERS:
                break

            try:
                u = json.loads(line)

                batch.append((
                    u["user_id"],
                    u.get("name", "Anonymous"),
                    u.get("review_count", 0),
                    u.get("average_stars", 0),
                    u.get("name", "Anonymous")  # display_name same as name initially
                ))

                count += 1

                # Insert batch when it reaches batch_size
                if len(batch) >= batch_size:
                    try:
                        conn.ping(reconnect=True)
                    except:
                        conn = get_connection()
                        cursor = conn.cursor()
                    
                    cursor.executemany(
                        "INSERT IGNORE INTO users VALUES (%s,%s,%s,%s,%s)",
                        batch
                    )
                    conn.commit()
                    batch = []

            except Exception as e:
                # Skip errors silently if it's just connection issues
                if "InterfaceError" not in str(e) and str(e) != "(0, '')":
                    print(f"Error loading user: {e}")
                continue

        # Insert remaining batch
        if batch:
            cursor.executemany(
                "INSERT IGNORE INTO users VALUES (%s,%s,%s,%s,%s)",
                batch
            )
            conn.commit()

    print(f"✅ Loaded {count:,} users")
    return conn

def load_reviews(conn):
    """Load reviews from JSON into MySQL"""
    print(f"\n⭐ Loading reviews (max {MAX_REVIEWS:,})...")

    cursor = conn.cursor()
    batch = []
    batch_size = 500
    count = 0

    with open(REVIEWS_PATH, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc="Reading reviews", unit=" reviews"):
            if count >= MAX_REVIEWS:
                break

            try:
                r = json.loads(line)

                batch.append((
                    r["review_id"],
                    r["user_id"],
                    r["business_id"],
                    int(r["stars"]),
                    r["text"],
                    r["date"]
                ))

                count += 1

                # Insert batch when it reaches batch_size
                if len(batch) >= batch_size:
                    try:
                        conn.ping(reconnect=True)
                    except:
                        conn = get_connection()
                        cursor = conn.cursor()
                    
                    cursor.executemany(
                        "INSERT IGNORE INTO reviews VALUES (%s,%s,%s,%s,%s,%s)",
                        batch
                    )
                    conn.commit()
                    batch = []

            except Exception as e:
                if "InterfaceError" not in str(e) and str(e) != "(0, '')":
                    print(f"Error loading review: {e}")
                continue

        # Insert remaining batch
        if batch:
            cursor.executemany(
                "INSERT IGNORE INTO reviews VALUES (%s,%s,%s,%s,%s,%s)",
                batch
            )
            conn.commit()

    print(f"✅ Loaded {count:,} reviews")
    return conn

def create_nigerian_demo_users(conn):
    """Create curated Nigerian-themed demo users"""
    print("\n🇳🇬 Creating Nigerian-themed demo users...")
    print("   Selecting users who have ACTUAL reviews in the database...")

    cursor = conn.cursor()
    demo_users = []

    # 1. The Lagos Foodie (high ratings, detailed reviews, mentions upscale places)
    cursor.execute("""
        SELECT u.user_id, u.name, u.average_stars, COUNT(r.review_id) as actual_reviews
        FROM users u
        INNER JOIN reviews r ON u.user_id = r.user_id
        WHERE u.average_stars > 4.0
        GROUP BY u.user_id, u.name, u.average_stars
        HAVING actual_reviews >= 5
        ORDER BY u.average_stars DESC, actual_reviews DESC
        LIMIT 1
    """)
    lagos_foodie = cursor.fetchone()
    if lagos_foodie:
        print(f"   Found Lagos Foodie with {lagos_foodie[3]} reviews")
        demo_users.append((lagos_foodie[0], "The Lagos Foodie", "Loves upscale dining, detailed reviews"))

    # 2. The Budget King (mentions value, price-conscious)
    cursor.execute("""
        SELECT u.user_id, u.name, u.average_stars, COUNT(r.review_id) as actual_reviews
        FROM users u
        INNER JOIN reviews r ON u.user_id = r.user_id
        WHERE u.average_stars BETWEEN 3.0 AND 4.0
        GROUP BY u.user_id, u.name, u.average_stars
        HAVING actual_reviews >= 5
        ORDER BY actual_reviews DESC
        LIMIT 1
    """)
    budget_king = cursor.fetchone()
    if budget_king:
        print(f"   Found Budget King with {budget_king[3]} reviews")
        demo_users.append((budget_king[0], "The Budget King", "Value-conscious, mentions prices"))

    # 3. The Harsh Critic (low ratings, blunt)
    cursor.execute("""
        SELECT u.user_id, u.name, u.average_stars, COUNT(r.review_id) as actual_reviews
        FROM users u
        INNER JOIN reviews r ON u.user_id = r.user_id
        WHERE u.average_stars < 2.5
        GROUP BY u.user_id, u.name, u.average_stars
        HAVING actual_reviews >= 5
        ORDER BY u.average_stars ASC
        LIMIT 1
    """)
    harsh_critic = cursor.fetchone()
    if harsh_critic:
        print(f"   Found Harsh Critic with {harsh_critic[3]} reviews")
        demo_users.append((harsh_critic[0], "The Harsh Critic", "Low ratings, brutally honest"))

    # 4. The Hype Man (high ratings, enthusiastic)
    cursor.execute("""
        SELECT u.user_id, u.name, u.average_stars, COUNT(r.review_id) as actual_reviews
        FROM users u
        INNER JOIN reviews r ON u.user_id = r.user_id
        WHERE u.average_stars > 4.5
        GROUP BY u.user_id, u.name, u.average_stars
        HAVING actual_reviews >= 5
        ORDER BY u.average_stars DESC
        LIMIT 1 OFFSET 1
    """)
    hype_man = cursor.fetchone()
    if hype_man:
        print(f"   Found Hype Man with {hype_man[3]} reviews")
        demo_users.append((hype_man[0], "The Hype Man", "Loves everything, always positive"))

    # 5. The Pidgin Pro (will write in Pidgin - simulated based on casual style)
    cursor.execute("""
        SELECT u.user_id, u.name, u.average_stars, COUNT(r.review_id) as actual_reviews
        FROM users u
        INNER JOIN reviews r ON u.user_id = r.user_id
        GROUP BY u.user_id, u.name, u.average_stars
        HAVING actual_reviews >= 5
        ORDER BY RAND()
        LIMIT 1
    """)
    pidgin_pro = cursor.fetchone()
    if pidgin_pro:
        print(f"   Found Pidgin Pro with {pidgin_pro[3]} reviews")
        demo_users.append((pidgin_pro[0], "The Pidgin Pro", "Writes in Nigerian Pidgin English"))

    # 6. The Quick Reviewer (short reviews)
    cursor.execute("""
        SELECT u.user_id, u.name, u.average_stars, COUNT(r.review_id) as actual_reviews
        FROM users u
        INNER JOIN reviews r ON u.user_id = r.user_id
        GROUP BY u.user_id, u.name, u.average_stars
        HAVING actual_reviews >= 5
        ORDER BY RAND()
        LIMIT 1
    """)
    quick_reviewer = cursor.fetchone()
    if quick_reviewer:
        print(f"   Found Quick Reviewer with {quick_reviewer[3]} reviews")
        demo_users.append((quick_reviewer[0], "The Quick Reviewer", "Short, casual reviews"))

    # 7. The Service Checker (focuses on staff & service)
    cursor.execute("""
        SELECT u.user_id, u.name, u.average_stars, COUNT(r.review_id) as actual_reviews
        FROM users u
        INNER JOIN reviews r ON u.user_id = r.user_id
        GROUP BY u.user_id, u.name, u.average_stars
        HAVING actual_reviews >= 5
        ORDER BY RAND()
        LIMIT 1
    """)
    service_checker = cursor.fetchone()
    if service_checker:
        print(f"   Found Service Checker with {service_checker[3]} reviews")
        demo_users.append((service_checker[0], "The Service Checker", "Focuses on staff and speed"))

    # 8. The Jollof Judge (rates based on food quality)
    cursor.execute("""
        SELECT u.user_id, u.name, u.average_stars, COUNT(r.review_id) as actual_reviews
        FROM users u
        INNER JOIN reviews r ON u.user_id = r.user_id
        WHERE u.average_stars BETWEEN 3.5 AND 4.5
        GROUP BY u.user_id, u.name, u.average_stars
        HAVING actual_reviews >= 5
        ORDER BY RAND()
        LIMIT 1
    """)
    jollof_judge = cursor.fetchone()
    if jollof_judge:
        print(f"   Found Jollof Judge with {jollof_judge[3]} reviews")
        demo_users.append((jollof_judge[0], "The Jollof Judge", "Rates based on Nigerian food quality"))

    # Nigerian names to assign
    nigerian_names = [
        "Chioma Okafor",      # Lagos Foodie
        "Emeka Nwosu",        # Budget King
        "Ngozi Adeyemi",      # Harsh Critic
        "Tunde Balogun",      # Hype Man
        "Amaka Eze",          # Pidgin Pro
        "Yemi Oladipo",       # Quick Reviewer
        "Funke Ajayi",        # Service Checker
        "Chinedu Okoro"       # Jollof Judge
    ]

    # Update display names and Nigerian names in database
    for idx, (user_id, display_name, description) in enumerate(demo_users):
        nigerian_name = nigerian_names[idx] if idx < len(nigerian_names) else "Nigerian User"

        cursor.execute(
            "UPDATE users SET display_name = %s, name = %s WHERE user_id = %s",
            (display_name, nigerian_name, user_id)
        )
        print(f"  ✅ {display_name} ({nigerian_name}): {description}")

    conn.commit()
    print(f"\n✅ Created {len(demo_users)} Nigerian-themed demo users with Nigerian names")

def main():
    print("🚀 Setting up Yelp dataset for BCT Hackathon (Nigerian Edition)...\n")

    try:
        # Setup database
        conn = setup_database()

        # Load data
        businesses = load_businesses(conn)
        load_users(conn)
        load_reviews(conn)
        create_nigerian_demo_users(conn)

        conn.close()

        print("\n" + "="*60)
        print("✅ Setup complete!")
        print("="*60)
        print(f"\nDatabase: {DB_CONFIG['database']} on {DB_CONFIG['host']}")
        print("\nNext steps:")
        print("1. Build FAISS index: python scripts/build_faiss_index.py")
        print("2. Start backend: cd backend && uvicorn main:app --reload")
        print("3. Start frontend: cd frontend && npm run dev")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()
