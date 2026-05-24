import pandas as pd
import json

# Merge the existing stream files into combined JSONs

categories_to_merge = [
    "Grocery_and_Gourmet_Food",
    "Movies_and_TV"  # Only partial metadata, but let's merge what we have
]

for category in categories_to_merge:
    print(f"\n🔀 Merging: {category}")

    try:
        # Load files
        reviews_df = pd.read_json(f"amazon_samples/{category}_reviews_stream.json")
        meta_df = pd.read_json(f"amazon_samples/{category}_meta_stream.json")

        print(f"   📊 Reviews: {len(reviews_df)}")
        print(f"   📦 Metadata: {len(meta_df)}")

        # Merge on parent_asin
        merged_df = reviews_df.merge(
            meta_df,
            on='parent_asin',
            how='left',
            suffixes=('_review', '_product')
        )

        # Check match rate
        matched = merged_df['title_product'].notna().sum()
        print(f"   ✅ Matched: {matched}/{len(merged_df)} reviews ({matched/len(merged_df)*100:.1f}%)")

        # Save combined
        output_file = f"amazon_samples/{category}_combined.json"
        merged_df.to_json(output_file, orient="records", indent=2)
        print(f"   💾 Saved to: {output_file}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n✅ Done merging existing files!")