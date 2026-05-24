import requests
import gzip
import json
import os
import pandas as pd
from tqdm import tqdm
import random
import time

# ==================== CONFIG ====================
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

def validate_gzip(gz_path):
    """Check if gzip file is valid by attempting to read it"""
    try:
        with gzip.open(gz_path, 'rb') as f:
            f.read(1024)  # Try to read first chunk
        return True
    except Exception:
        return False

def download_file(url, dest_path, retries=6):
    """Download with validation and retries"""

    # Check if file exists and is valid
    if os.path.exists(dest_path):
        if validate_gzip(dest_path):
            print(f"   ✓ Valid file already exists, skipping download")
            return True
        else:
            print(f"   ⚠ Corrupted file detected, deleting and re-downloading...")
            os.remove(dest_path)

    for attempt in range(retries):
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                total = int(r.headers.get('content-length', 0))

                with open(dest_path, 'wb') as f, tqdm(
                    total=total, initial=0, unit='B', unit_scale=True,
                    desc=os.path.basename(dest_path)
                ) as pbar:

                    for chunk in r.iter_content(chunk_size=1024*1024):  # 1MB
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))

            # Validate after download
            if validate_gzip(dest_path):
                return True
            else:
                print(f"   ⚠ Downloaded file is corrupted, retrying...")
                os.remove(dest_path)

        except Exception as e:
            print(f"   Attempt {attempt+1} failed: {e}")
            if os.path.exists(dest_path):
                os.remove(dest_path)
            time.sleep(5 * (attempt + 1))

    print(f"   ❌ Failed after {retries} attempts")
    return False


def process_category(cat):
    print(f"\n🔄 Processing: {cat}")
    
    # === Reviews ===
    review_url = f"{BASE_URL}/review_categories/{cat}.jsonl.gz"
    review_gz = f"amazon_samples/{cat}_reviews.jsonl.gz"
    review_final = f"amazon_samples/{cat}_reviews_5k.json"
    
    if not os.path.exists(review_gz) or os.path.getsize(review_gz) < 100_000:
        print("   ⬇️ Downloading Reviews...")
        download_file(review_url, review_gz)
    
    # Extract + Sample Reviews
    if not os.path.exists(review_final):
        print("   📦 Extracting & Sampling Reviews...")
        try:
            reviews = []
            with gzip.open(review_gz, 'rt', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= SAMPLE_SIZE * 5:
                        break
                    if line.strip():
                        reviews.append(json.loads(line.strip()))

            random.seed(42)
            sampled = random.sample(reviews, min(SAMPLE_SIZE, len(reviews)))
            pd.DataFrame(sampled).to_json(review_final, orient="records", indent=2)
            print(f"   ✅ Reviews saved: {len(sampled)}")
        except EOFError as e:
            print(f"   ❌ Extraction failed: {e}")
            print(f"   Deleting corrupted file, please re-run the script")
            if os.path.exists(review_gz):
                os.remove(review_gz)
            return
    
    # === METADATA (Only for products in our reviews) ===
    meta_url = f"{BASE_URL}/meta_categories/meta_{cat}.jsonl.gz"
    meta_gz = f"amazon_samples/meta_{cat}.jsonl.gz"
    meta_final = f"amazon_samples/{cat}_meta.json"

    if not os.path.exists(meta_final):
        # Get product IDs from our sampled reviews
        review_df = pd.read_json(review_final)
        needed_asins = set(review_df['parent_asin'].dropna().unique())
        print(f"   🔍 Need metadata for {len(needed_asins)} unique products")

        # Download metadata file if needed
        if not os.path.exists(meta_gz) or os.path.getsize(meta_gz) < 10_000:
            print("   ⬇️ Downloading Metadata...")
            download_file(meta_url, meta_gz)

        # Extract ONLY matching products
        print("   📦 Extracting matching metadata...")
        try:
            meta_items = []
            found_count = 0
            with gzip.open(meta_gz, 'rt', encoding='utf-8') as f:
                for line in tqdm(f, desc="Scanning metadata"):
                    if line.strip():
                        item = json.loads(line.strip())
                        # Only keep if this product was reviewed
                        if item.get('parent_asin') in needed_asins:
                            meta_items.append(item)
                            found_count += 1
                            # Stop once we found all needed products
                            if found_count >= len(needed_asins):
                                break

            pd.DataFrame(meta_items).to_json(meta_final, orient="records", indent=2)
            print(f"   ✅ Metadata saved: {len(meta_items)} products (matched from reviews)")
        except EOFError as e:
            print(f"   ❌ Metadata extraction failed: {e}")
            print(f"   Deleting corrupted file, please re-run the script")
            if os.path.exists(meta_gz):
                os.remove(meta_gz)
            return

# ==================== RUN ====================
print("🚀 Starting Download (Reviews + Metadata)...\n")

for cat in categories:
    process_category(cat)

print("\n🎉 DONE! You now have both Reviews and Metadata.")