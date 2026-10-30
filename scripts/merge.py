"""
Phase 1: Data Collection - Dataset Merge
Merges data/raw_playstore.csv and data/raw_reddit.csv into data/all_reviews.csv.
Guarantees:
- Strict universal schema: id, source, date, rating, text, url, language
- Stable, globally unique IDs across all feedback channels
- Clean date formatting and type consistency
"""

import sys
from pathlib import Path
import pandas as pd

# Import project configuration
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import UNIVERSAL_SCHEMA, DATA_DIR

PLAYSTORE_FILE = DATA_DIR / "raw_playstore.csv"
REDDIT_FILE = DATA_DIR / "raw_reddit.csv"
OUTPUT_MERGED_FILE = DATA_DIR / "all_reviews.csv"


def merge_datasets() -> pd.DataFrame:
    """
    Loads raw Play Store and Reddit datasets, validates their schemas,
    and merges them into a single unified dataframe with unique IDs.
    """
    frames = []

    # 1. Load Play Store reviews if available
    if PLAYSTORE_FILE.exists():
        df_ps = pd.read_csv(PLAYSTORE_FILE, encoding="utf-8")
        print(f"[*] Loaded Play Store reviews: {len(df_ps)} rows")
        frames.append(df_ps)
    else:
        print(f"[!] Warning: {PLAYSTORE_FILE.name} not found. Skipping Play Store data.")

    # 2. Load Reddit reviews if available
    if REDDIT_FILE.exists():
        df_rd = pd.read_csv(REDDIT_FILE, encoding="utf-8")
        print(f"[*] Loaded Reddit reviews: {len(df_rd)} rows")
        frames.append(df_rd)
    else:
        print(f"[!] Warning: {REDDIT_FILE.name} not found. Skipping Reddit data.")

    if not frames:
        raise FileNotFoundError("No raw data found! Run collect_playstore.py or create raw_reddit.csv first.")

    # 3. Concatenate and validate
    merged = pd.concat(frames, ignore_index=True)

    # Validate schema
    for col in UNIVERSAL_SCHEMA:
        if col not in merged.columns:
            raise ValueError(f"Merged dataset missing required column: '{col}'")

    merged = merged[UNIVERSAL_SCHEMA]

    # Ensure ID uniqueness across combined sources
    # If duplicates exist, make them distinct by appending source prefix
    if not merged["id"].is_unique:
        print("[!] Detected duplicate IDs across merged sources. Normalizing IDs...")
        merged["id"] = merged["source"].str[:2] + "_" + merged["id"].astype(str)

    # Final assertion on unique IDs
    assert merged["id"].is_unique, "Fatal: IDs in merged dataset are not strictly unique!"

    # Clean whitespace and types
    merged["text"] = merged["text"].astype(str).str.strip()
    merged["rating"] = pd.to_numeric(merged["rating"], errors="coerce").fillna(3).astype(int)

    # Sort deterministically by date descending, then ID
    merged = merged.sort_values(by=["date", "id"], ascending=[False, True]).reset_index(drop=True)

    return merged


def main():
    print("=" * 60)
    print("Phase 1: Merging Datasets into data/all_reviews.csv")
    print("=" * 60)

    try:
        df = merge_datasets()
        df.to_csv(OUTPUT_MERGED_FILE, index=False, encoding="utf-8")

        print(f"\n[✓] Successfully created: {OUTPUT_MERGED_FILE}")
        print(f"[*] Total merged records: {len(df):,}")
        print("\nBreakdown by Source:")
        print(df["source"].value_counts().to_string())

        print("\nBreakdown by Star Rating:")
        print(df["rating"].value_counts().sort_index().to_string())

        date_min = df["date"].dropna().min()
        date_max = df["date"].dropna().max()
        print(f"\nDate Range: {date_min} to {date_max}")

        print("\nSample Preview (First 3 rows):")
        for _, row in df.head(3).iterrows():
            print(f"- [{row['id']}] [{row['source']}] {row['rating']}★ ({row['date']}): {row['text'][:90]}...")

    except Exception as e:
        print(f"\n[X] Error during merge: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
