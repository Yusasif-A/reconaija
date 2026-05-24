import pandas as pd
import json

# Example: How to merge reviews with product metadata

category = "Grocery_and_Gourmet_Food"

# Load reviews and metadata
reviews_df = pd.read_json(f"amazon_samples/{category}_reviews_stream.json")
meta_df = pd.read_json(f"amazon_samples/{category}_meta_stream.json")

print(f"📊 Loaded {len(reviews_df)} reviews")
print(f"📦 Loaded {len(meta_df)} product metadata")

# Merge on 'parent_asin' (product ID)
# This joins each review with its product information
merged_df = reviews_df.merge(
    meta_df,
    on='parent_asin',
    how='left',
    suffixes=('_review', '_product')
)

print(f"\n✅ Merged dataset: {len(merged_df)} rows")
print(f"\nColumns available:")
print(merged_df.columns.tolist())

# Save merged data
output_file = f"amazon_samples/{category}_merged.json"
merged_df.to_json(output_file, orient="records", indent=2)
print(f"\n💾 Saved to: {output_file}")

# Example: Show first review with product info
print("\n📝 Example merged record:")
sample = merged_df.iloc[0].to_dict()
print(f"Review: {sample.get('text', 'N/A')[:100]}...")
print(f"Product: {sample.get('title', 'N/A')}")
print(f"Rating: {sample.get('rating', 'N/A')}")
print(f"Price: {sample.get('price', 'N/A')}")