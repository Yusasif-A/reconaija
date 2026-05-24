"""
Recreate Demo Users with Actual Reviews
Fixes the issue where demo users have 0 reviews
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

def recreate_demo_users():
    """Recreate demo users, ensuring they have actual reviews"""
    print("🔧 Recreating demo users with actual reviews...")

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # First, clear existing demo users
    print("\n   Clearing old demo users...")
    cursor.execute("UPDATE users SET display_name = NULL WHERE display_name IS NOT NULL")
    conn.commit()

    demo_users = []
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

    print("\n   Selecting users who have ACTUAL reviews in the database...\n")

    # 1. The Lagos Foodie
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
    result = cursor.fetchone()
    if result:
        print(f"   ✅ Lagos Foodie: {result[3]} reviews, {result[2]:.1f} avg stars")
        demo_users.append((result[0], "The Lagos Foodie", "Loves upscale dining"))

    # 2. The Budget King
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
    result = cursor.fetchone()
    if result:
        print(f"   ✅ Budget King: {result[3]} reviews, {result[2]:.1f} avg stars")
        demo_users.append((result[0], "The Budget King", "Value-conscious"))

    # 3. The Harsh Critic
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
    result = cursor.fetchone()
    if result:
        print(f"   ✅ Harsh Critic: {result[3]} reviews, {result[2]:.1f} avg stars")
        demo_users.append((result[0], "The Harsh Critic", "Low ratings"))

    # 4. The Hype Man
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
    result = cursor.fetchone()
    if result:
        print(f"   ✅ Hype Man: {result[3]} reviews, {result[2]:.1f} avg stars")
        demo_users.append((result[0], "The Hype Man", "Always positive"))

    # 5. The Pidgin Pro
    cursor.execute("""
        SELECT u.user_id, u.name, u.average_stars, COUNT(r.review_id) as actual_reviews
        FROM users u
        INNER JOIN reviews r ON u.user_id = r.user_id
        GROUP BY u.user_id, u.name, u.average_stars
        HAVING actual_reviews >= 5
        ORDER BY RAND()
        LIMIT 1
    """)
    result = cursor.fetchone()
    if result:
        print(f"   ✅ Pidgin Pro: {result[3]} reviews, {result[2]:.1f} avg stars")
        demo_users.append((result[0], "The Pidgin Pro", "Nigerian Pidgin"))

    # 6. The Quick Reviewer
    cursor.execute("""
        SELECT u.user_id, u.name, u.average_stars, COUNT(r.review_id) as actual_reviews
        FROM users u
        INNER JOIN reviews r ON u.user_id = r.user_id
        GROUP BY u.user_id, u.name, u.average_stars
        HAVING actual_reviews >= 5
        ORDER BY RAND()
        LIMIT 1
    """)
    result = cursor.fetchone()
    if result:
        print(f"   ✅ Quick Reviewer: {result[3]} reviews, {result[2]:.1f} avg stars")
        demo_users.append((result[0], "The Quick Reviewer", "Short reviews"))

    # 7. The Service Checker
    cursor.execute("""
        SELECT u.user_id, u.name, u.average_stars, COUNT(r.review_id) as actual_reviews
        FROM users u
        INNER JOIN reviews r ON u.user_id = r.user_id
        GROUP BY u.user_id, u.name, u.average_stars
        HAVING actual_reviews >= 5
        ORDER BY RAND()
        LIMIT 1
    """)
    result = cursor.fetchone()
    if result:
        print(f"   ✅ Service Checker: {result[3]} reviews, {result[2]:.1f} avg stars")
        demo_users.append((result[0], "The Service Checker", "Focuses on service"))

    # 8. The Jollof Judge
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
    result = cursor.fetchone()
    if result:
        print(f"   ✅ Jollof Judge: {result[3]} reviews, {result[2]:.1f} avg stars")
        demo_users.append((result[0], "The Jollof Judge", "Food quality focus"))

    # Update display names and Nigerian names
    print("\n   Updating database with Nigerian names...\n")
    for idx, (user_id, display_name, description) in enumerate(demo_users):
        nigerian_name = nigerian_names[idx] if idx < len(nigerian_names) else "Nigerian User"

        cursor.execute(
            "UPDATE users SET display_name = %s, name = %s WHERE user_id = %s",
            (display_name, nigerian_name, user_id)
        )
        print(f"   ✅ {display_name} → {nigerian_name}")

    conn.commit()
    conn.close()

    print(f"\n✅ Successfully created {len(demo_users)} demo users with actual reviews!")
    print("\n   Refresh your frontend and try again.")

if __name__ == "__main__":
    recreate_demo_users()
