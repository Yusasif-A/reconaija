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

def stream_download_and_sample(url, category, sample_size):
    """Stream download and stop after collecting enough samples"""
    print(f"\n🔄 Processing: {category}")
    print(f"   📥 Streaming reviews (will stop after ~{sample_size * 3} lines)...")

    reviews = []
    try:
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()

            # Decompress on-the-fly
            decompressor = gzip.GzipFile(fileobj=response.raw)

            line_count = 0
            target_lines = sample_size * 3  # Read 3x to have variety

            with tqdm(total=target_lines, desc="Reading lines", unit="lines") as pbar:
                buffer = b""
                while line_count < target_lines:
                    chunk = decompressor.read(1024 * 64)  # 64KB chunks
                    if not chunk:
                        break

                    buffer += chunk
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        if line.strip():
                            try:
                                reviews.append(json.loads(line.decode('utf-8')))
                                line_count += 1
                                pbar.update(1)

                                if line_count >= target_lines:
                                    break
                            except json.JSONDecodeError:
                                continue

                print(f"   ✅ Collected {len(reviews)} reviews")

        # Sample randomly
        random.seed(42)
        sampled = random.sample(reviews, min(sample_size, len(reviews)))

        # Save reviews
        review_file = f"amazon_samples/{category}_reviews_stream.json"
        pd.DataFrame(sampled).to_json(review_file, orient="records", indent=2)
        print(f"   💾 Saved {len(sampled)} reviews to {review_file}")

        # Get metadata for these products
        get_metadata_for_reviews(category, sampled)

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def get_metadata_for_reviews(category, reviews):
    """Download and extract metadata only for reviewed products"""
    print(f"   🔍 Fetching metadata for reviewed products...")

    # Get unique product IDs
    product_ids = set()
    for review in reviews:
        if 'parent_asin' in review:
            product_ids.add(review['parent_asin'])

    print(f"   📦 Need metadata for {len(product_ids)} unique products")

    meta_url = f"{BASE_URL}/meta_categories/meta_{category}.jsonl.gz"
    meta_items = []
    found_count = 0

    try:
        with requests.get(meta_url, stream=True, timeout=60) as response:
            response.raise_for_status()

            decompressor = gzip.GzipFile(fileobj=response.raw)

            with tqdm(total=len(product_ids), desc="Finding metadata", unit="products") as pbar:
                buffer = b""
                while found_count < len(product_ids):
                    chunk = decompressor.read(1024 * 64)
                    if not chunk:
                        break

                    buffer += chunk
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        if line.strip():
                            try:
                                item = json.loads(line.decode('utf-8'))
                                if item.get('parent_asin') in product_ids:
                                    meta_items.append(item)
                                    found_count += 1
                                    pbar.update(1)

                                    if found_count >= len(product_ids):
                                        break
                            except json.JSONDecodeError:
                                continue

        # Merge reviews with metadata into ONE combined JSON
        print(f"   🔀 Merging reviews with product info...")

        reviews_df = pd.DataFrame(reviews)
        meta_df = pd.DataFrame(meta_items)

        # Merge on parent_asin
        merged_df = reviews_df.merge(
            meta_df,
            on='parent_asin',
            how='left',
            suffixes=('_review', '_product')
        )

        # Save combined JSON
        combined_file = f"amazon_samples/{category}_combined.json"
        merged_df.to_json(combined_file, orient="records", indent=2)

        matched = merged_df['title_product'].notna().sum()
        print(f"   💾 Saved {len(merged_df)} records to: {combined_file}")
        print(f"   ✅ Match rate: {matched}/{len(merged_df)} reviews have product info ({matched/len(merged_df)*100:.1f}%)")

    except Exception as e:
        print(f"   ⚠️  Metadata fetch failed: {e}")


# ==================== RUN ====================
print("🚀 Starting STREAMING Download (No full file download!)...\n")

for cat in categories:
    stream_download_and_sample(
        f"{BASE_URL}/review_categories/{cat}.jsonl.gz",
        cat,
        SAMPLE_SIZE
    )

print("\n🎉 DONE! Check 'amazon_samples' folder for *_stream.json files")