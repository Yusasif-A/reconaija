import requests
import gzip
import json
import pandas as pd
from tqdm import tqdm
import random

# ==================== CONFIG ====================
import os
os.makedirs("amazon_samples", exist_ok=True)

BASE_URL = "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw"

categories = [
    "Grocery_and_Gourmet_Food",
    "Movies_and_TV",
    "Books",
    "Home_and_Kitchen"
]

SAMPLE_SIZE = 2000
# ===============================================

def download_metadata_first(category, sample_size):
    """
    METADATA FIRST approach - guarantees every review has product info
    1. Download metadata first (sample ~3000 products)
    2. Get their product IDs
    3. Download reviews ONLY for those products
    """
    print(f"\n🔄 Processing: {category}")

    # === STEP 1: Get Metadata First ===
    print(f"   📦 Downloading metadata (will collect ~{sample_size * 2} products)...")
    meta_url = f"{BASE_URL}/meta_categories/meta_{category}.jsonl.gz"

    meta_items = []
    target_meta = sample_size * 2  # Get 2x products to ensure enough reviews

    try:
        with requests.get(meta_url, stream=True, timeout=60) as response:
            response.raise_for_status()
            decompressor = gzip.GzipFile(fileobj=response.raw)

            with tqdm(total=target_meta, desc="Reading metadata", unit="products") as pbar:
                buffer = b""
                while len(meta_items) < target_meta:
                    chunk = decompressor.read(1024 * 64)
                    if not chunk:
                        break

                    buffer += chunk
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        if line.strip():
                            try:
                                item = json.loads(line.decode('utf-8'))
                                # Only keep items with essential fields
                                if item.get('parent_asin') and item.get('title'):
                                    meta_items.append(item)
                                    pbar.update(1)

                                    if len(meta_items) >= target_meta:
                                        break
                            except json.JSONDecodeError:
                                continue

        print(f"   ✅ Collected {len(meta_items)} product metadata")

        # Get product IDs
        product_ids = set(item['parent_asin'] for item in meta_items)
        print(f"   📋 Have {len(product_ids)} unique product IDs")

    except Exception as e:
        print(f"   ❌ Metadata download failed: {e}")
        return False

    # === STEP 2: Get Reviews for These Products ===
    print(f"   📥 Downloading reviews for these products...")
    review_url = f"{BASE_URL}/review_categories/{category}.jsonl.gz"

    reviews = []
    target_reviews = sample_size * 50  # Read MANY more reviews to find matches (100,000 lines)

    try:
        with requests.get(review_url, stream=True, timeout=60) as response:
            response.raise_for_status()
            decompressor = gzip.GzipFile(fileobj=response.raw)

            with tqdm(total=target_reviews, desc="Reading reviews", unit="reviews") as pbar:
                buffer = b""
                lines_read = 0
                should_stop = False

                while lines_read < target_reviews and not should_stop:
                    chunk = decompressor.read(1024 * 64)
                    if not chunk:
                        break

                    buffer += chunk
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        if line.strip():
                            try:
                                review = json.loads(line.decode('utf-8'))
                                # ONLY keep reviews for products we have metadata for
                                if review.get('parent_asin') in product_ids:
                                    reviews.append(review)

                                    # Stop early if we already have enough reviews
                                    if len(reviews) >= sample_size:
                                        print(f"\n   🎯 Got {len(reviews)} reviews, stopping...")
                                        should_stop = True
                                        break

                                lines_read += 1
                                pbar.update(1)

                                if lines_read >= target_reviews:
                                    break
                            except json.JSONDecodeError:
                                continue

                        if should_stop:
                            break

        print(f"   ✅ Found {len(reviews)} matching reviews")

        # Sample if we have more than needed
        if len(reviews) > sample_size:
            random.seed(42)
            reviews = random.sample(reviews, sample_size)
            print(f"   🎲 Sampled down to {len(reviews)} reviews")

    except Exception as e:
        print(f"   ❌ Review download failed: {e}")
        return False

    # === STEP 3: Filter metadata to only reviewed products ===
    reviewed_product_ids = set(r['parent_asin'] for r in reviews)
    meta_items = [m for m in meta_items if m['parent_asin'] in reviewed_product_ids]

    print(f"   🔗 Final match: {len(reviews)} reviews + {len(meta_items)} products")

    # === STEP 4: Merge into ONE JSON per category ===
    print(f"   🔀 Merging reviews with product info...")

    # Convert to DataFrames
    reviews_df = pd.DataFrame(reviews)
    meta_df = pd.DataFrame(meta_items)

    # Merge on parent_asin - each review gets its product info attached
    merged_df = reviews_df.merge(
        meta_df,
        on='parent_asin',
        how='left',
        suffixes=('_review', '_product')
    )

    # Save as ONE combined JSON per category
    output_file = f"amazon_samples/{category}_combined.json"
    merged_df.to_json(output_file, orient="records", indent=2)

    print(f"   💾 Saved {len(merged_df)} records to: {output_file}")
    print(f"   ✅ Each record has: review + product info in ONE JSON!\n")

    return True


# ==================== RUN ====================
print("🚀 METADATA-FIRST Download (Guaranteed matches!)...\n")

for cat in categories:
    download_metadata_first(cat, SAMPLE_SIZE)

print("\n🎉 DONE! All reviews have matching product info.")
print("Run 'python merge_data.py' to combine them.")