"""
Phase 1: Data Collection - Reddit Loader & Validator
Loads manually collected Reddit posts/comments from data/raw_reddit.csv.
Validates adherence to the universal schema:
id, source, date, rating, text, url, language
Does NOT scrape Reddit (respects platform policies and avoids unauthenticated bot bans).
"""

import sys
from pathlib import Path
import pandas as pd

# Import project configuration
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import UNIVERSAL_SCHEMA, DATA_DIR

REDDIT_INPUT_FILE = DATA_DIR / "raw_reddit.csv"


def validate_and_load_reddit(file_path: Path = REDDIT_INPUT_FILE) -> pd.DataFrame:
    """
    Validates that the user's manual Reddit data conforms strictly to the project schema.
    """
    print(f"[*] Validating Reddit dataset at: {file_path}")

    if not file_path.exists():
        raise FileNotFoundError(
            f"Reddit data file not found at {file_path}. "
            "Please create it or use the provided starter template."
        )

    df = pd.read_csv(file_path, encoding="utf-8")

    # 1. Check exact columns
    missing_cols = [col for col in UNIVERSAL_SCHEMA if col not in df.columns]
    extra_cols = [col for col in df.columns if col not in UNIVERSAL_SCHEMA]

    if missing_cols:
        raise ValueError(f"Schema Error: Missing columns in {file_path.name}: {missing_cols}")
    if extra_cols:
        print(f"    [!] Warning: Extra columns found and will be dropped: {extra_cols}")
        df = df[UNIVERSAL_SCHEMA]

    # Reorder columns to guarantee identical structure
    df = df[UNIVERSAL_SCHEMA]

    # 2. Check for empty rows
    initial_count = len(df)
    df = df.dropna(subset=["id", "text"])
    if len(df) < initial_count:
        print(f"    [!] Dropped {initial_count - len(df)} rows with missing 'id' or 'text'")

    # 3. Check ID uniqueness
    if not df["id"].is_unique:
        duplicates = df[df["id"].duplicated()]["id"].tolist()
        raise ValueError(f"Integrity Error: Found duplicate IDs in {file_path.name}: {duplicates[:5]}")

    # 4. Standardize types
    df["source"] = df["source"].astype(str).str.lower()
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(3).astype(int)
    # Ensure rating is bounded 1 to 5
    df["rating"] = df["rating"].clip(1, 5)
    df["text"] = df["text"].astype(str).str.strip()
    df["language"] = df["language"].astype(str).str.lower().fillna("en")

    print(f"[✓] Validation successful: {len(df)} Reddit entries verified.")
    print(f"    - Unique sources: {df['source'].unique().tolist()}")
    print(f"    - Rating range: {df['rating'].min()} to {df['rating'].max()} (Mean: {df['rating'].mean():.2f})")
    print(f"    - Languages detected in input: {df['language'].value_counts().to_dict()}")

    return df


def main():
    try:
        df = validate_and_load_reddit(REDDIT_INPUT_FILE)
        print("\nSample Preview:")
        for _, row in df.head(3).iterrows():
            print(f"[{row['id']}] ({row['rating']}★, {row['date']}): {row['text'][:80]}...")
    except Exception as e:
        print(f"\n[X] Reddit validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
