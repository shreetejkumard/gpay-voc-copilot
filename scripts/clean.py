"""
Phase 2: Data Cleaning & Preprocessing
Cleans merged user reviews from data/all_reviews.csv:
1. Removes exact duplicates (identical raw text)
2. Removes near-duplicates (identical after normalization: lowercasing, punctuation stripping, whitespace collapsing)
3. Drops uninformative short reviews (< 5 words: e.g. "good", "nice", "ok", "worst")
4. Tags language accurately as English ('en'), Hindi Devanagari ('hi'), or Hinglish ('hinglish')
5. Produces an audit trail at data/cleaning_log.json
6. Saves the refined dataset to data/clean_reviews.csv
"""

import sys
import re
import json
import string
import datetime
from pathlib import Path
import pandas as pd

# Import project configuration
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import UNIVERSAL_SCHEMA, DATA_DIR, MIN_REVIEW_WORDS

INPUT_FILE = DATA_DIR / "all_reviews.csv"
OUTPUT_CLEAN_FILE = DATA_DIR / "clean_reviews.csv"
CLEANING_LOG_FILE = DATA_DIR / "cleaning_log.json"

# Devanagari Unicode range for Hindi script detection
DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F]")

# High-frequency Hinglish vocabulary markers (Romanized Hindi)
HINGLISH_MARKERS = {
    "kya", "hai", "hain", "bhai", "nahi", "nhi", "karo", "kat", "gaye", "gye",
    "hona", "hoga", "mera", "meri", "mere", "kuch", "paise", "paisa", "rupaye",
    "dekh", "raha", "rahi", "rahe", "karna", "karta", "karti", "wali", "wala",
    "wale", "chahiye", "lekin", "kyun", "kyu", "kaise", "sab", "aata", "aati",
    "aaya", "aaye", "bohot", "bahut", "kharab", "bakwas", "ghatiya", "chor",
    "chal", "baad", "phir", "tak", "tha", "thi", "the", "diya", "diye", "mila",
    "mile", "fas", "phas", "hote", "hoti", "kr", "rahega", "karega", "rakha"
}


def normalize_text_for_dedup(text: str) -> str:
    """
    Normalizes text to detect near-duplicates:
    - Lowercase
    - Remove punctuation
    - Collapse extra whitespace
    """
    if not isinstance(text, str):
        return ""
    # Lowercase
    text = text.lower()
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def detect_language(text: str) -> str:
    """
    Detects whether text is Hindi (Devanagari), Hinglish (Roman script Hindi), or English.
    - If Devanagari characters are present -> 'hi'
    - If Roman script contains 2+ common Hinglish vocabulary markers -> 'hinglish'
    - Otherwise -> 'en'
    """
    if not isinstance(text, str) or not text.strip():
        return "en"

    # 1. Hindi Devanagari check
    if DEVANAGARI_REGEX.search(text):
        return "hi"

    # 2. Hinglish vocabulary check
    # Tokenize words in lowercase alphanumeric
    tokens = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
    hinglish_match_count = len(tokens.intersection(HINGLISH_MARKERS))

    if hinglish_match_count >= 2:
        return "hinglish"

    # 3. Default to English
    return "en"


def clean_dataset() -> pd.DataFrame:
    """
    Executes the multi-stage cleaning pipeline with an audit log.
    """
    print(f"[*] Loading raw merged reviews from: {INPUT_FILE}")
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}. Run Phase 1 merge first.")

    df = pd.read_csv(INPUT_FILE, encoding="utf-8")
    rows_before = len(df)
    print(f"[*] Starting row count: {rows_before:,}")

    # --- Step 1: Remove Exact Duplicates ---
    # Rows with identical raw text
    is_exact_dup = df.duplicated(subset=["text"], keep="first")
    exact_duplicates_count = int(is_exact_dup.sum())
    df = df[~is_exact_dup].copy()
    print(f"[-] Removed exact duplicates: {exact_duplicates_count:,}")

    # --- Step 2: Remove Near-Duplicates ---
    # Rows that are identical after punctuation/casing/whitespace normalization
    normalized_series = df["text"].apply(normalize_text_for_dedup)
    is_near_dup = normalized_series.duplicated(keep="first")
    near_duplicates_count = int(is_near_dup.sum())
    df = df[~is_near_dup].copy()
    print(f"[-] Removed near-duplicates:  {near_duplicates_count:,}")

    # --- Step 3: Remove Short Reviews (< MIN_REVIEW_WORDS words) ---
    # e.g., "good", "nice app", "super", "ok" offer zero actionable product signal
    word_counts = df["text"].astype(str).apply(lambda t: len(t.strip().split()))
    is_too_short = word_counts < MIN_REVIEW_WORDS
    short_rows_count = int(is_too_short.sum())
    df = df[~is_too_short].copy()
    print(f"[-] Removed short reviews (< {MIN_REVIEW_WORDS} words): {short_rows_count:,}")

    rows_after = len(df)
    print(f"[*] Final retained row count: {rows_after:,}")

    # --- Step 4: Tag Language ('en', 'hi', 'hinglish') ---
    print("[*] Tagging languages (English, Hindi, Hinglish)...")
    df["language"] = df["text"].apply(detect_language)
    lang_dist = df["language"].value_counts().to_dict()
    print(f"[✓] Language breakdown: {lang_dist}")

    # --- Step 5: Generate Audit Log ---
    cleaning_log = {
        "timestamp": datetime.datetime.now().isoformat(),
        "rows_before": rows_before,
        "duplicates_removed": exact_duplicates_count,
        "near_duplicates_removed": near_duplicates_count,
        "short_rows_removed": short_rows_count,
        "rows_after": rows_after,
        "retained_percentage": round((rows_after / rows_before) * 100, 2),
        "language_distribution": lang_dist,
        "source_distribution": df["source"].value_counts().to_dict(),
        "rating_distribution": df["rating"].value_counts().sort_index().to_dict(),
    }

    CLEANING_LOG_FILE.write_text(json.dumps(cleaning_log, indent=2), encoding="utf-8")
    print(f"[✓] Saved cleaning audit log to: {CLEANING_LOG_FILE}")

    # Save clean dataset
    df = df[UNIVERSAL_SCHEMA]
    df.to_csv(OUTPUT_CLEAN_FILE, index=False, encoding="utf-8")
    print(f"[✓] Saved clean reviews to: {OUTPUT_CLEAN_FILE}")

    return df


def main():
    print("=" * 60)
    print("Phase 2: Data Cleaning & Preprocessing Pipeline")
    print("=" * 60)

    try:
        df = clean_dataset()
        print("\nClean Dataset Sample Preview:")
        for _, row in df.head(3).iterrows():
            print(f"- [{row['id']}] [{row['source']}] [{row['language']}] {row['rating']}★: {row['text'][:90]}...")
    except Exception as e:
        print(f"\n[X] Error during data cleaning: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
