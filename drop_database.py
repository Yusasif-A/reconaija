"""
Drop and recreate the RecoNaija database
Run this before load_yelp_to_mysql.py if you need a fresh start
"""

import pymysql
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
    'charset': 'utf8mb4'
}

DB_NAME = os.getenv('DB_NAME')

def drop_and_recreate():
    """Drop the database if it exists and recreate it"""
    print(f"🗑️  Dropping database '{DB_NAME}' if it exists...")
    
    try:
        # Connect without specifying database
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Drop database
        cursor.execute(f"DROP DATABASE IF EXISTS `{DB_NAME}`")
        print(f"✅ Database '{DB_NAME}' dropped")
        
        # Recreate database
        cursor.execute(f"CREATE DATABASE `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✅ Database '{DB_NAME}' recreated")
        
        conn.close()
        
        print("\n" + "="*60)
        print("✅ Database reset complete!")
        print("="*60)
        print("\nNext step:")
        print("python scripts/load_yelp_to_mysql.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    drop_and_recreate()
