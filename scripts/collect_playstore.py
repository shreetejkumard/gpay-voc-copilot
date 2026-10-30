"""
Phase 1: Data Collection - Google Play Store
Pulls recent Google Pay (India, English) reviews with mixed ratings (1 to 5 stars).
Saves output strictly adhering to universal schema:
id, source, date, rating, text, url, language
"""

import sys
import time
from pathlib import Path
import pandas as pd
from google_play_scraper import Sort, reviews

# Import project configuration
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import (
    PLAYSTORE_APP_ID,
    PLAYSTORE_LANG,
    PLAYSTORE_COUNTRY,
    TARGET_PLAYSTORE_REVIEWS,
    UNIVERSAL_SCHEMA,
    DATA_DIR,
)

OUTPUT_FILE = DATA_DIR / "raw_playstore.csv"


def fetch_playstore_reviews(target_count: int = TARGET_PLAYSTORE_REVIEWS) -> pd.DataFrame:
    """
    Fetches balanced reviews from Google Play Store across all 5 star ratings.
    This guarantees balanced representation of user sentiment rather than solely 1-star rants.
    """
    print(f"[*] Starting Play Store data collection for App ID: '{PLAYSTORE_APP_ID}'")
    print(f"[*] Target count: ~{target_count} reviews (balanced across 1-5 stars)")

    stars = [1, 2, 3, 4, 5]
    reviews_per_star = target_count // len(stars)
    all_collected = []
    seen_ids = set()

    for star in stars:
        print(f"[*] Fetching ~{reviews_per_star} reviews for rating {star}★...")
        try:
            # Fetch reviews for the specific star rating
            result, _ = reviews(
                PLAYSTORE_APP_ID,
                lang=PLAYSTORE_LANG,
                country=PLAYSTORE_COUNTRY,
                sort=Sort.NEWEST,
                count=reviews_per_star,
                filter_score_with=star,
            )

            count_for_star = 0
            for r in result:
                review_id = str(r.get("reviewId", "")).strip()
                if not review_id or review_id in seen_ids:
                    continue

                seen_ids.add(review_id)
                content = str(r.get("content", "")).strip()
                if not content:
                    continue

                # Format date to YYYY-MM-DD
                created_at = r.get("at")
                date_str = created_at.strftime("%Y-%m-%d") if created_at else ""

                # Construct direct permalink
                review_url = f"https://play.google.com/store/apps/details?id={PLAYSTORE_APP_ID}&reviewId={review_id}"

                row = {
                    "id": f"gp_{review_id}",
                    "source": "playstore",
                    "date": date_str,
                    "rating": int(r.get("score", star)),
                    "text": content,
                    "url": review_url,
                    "language": PLAYSTORE_LANG,
                }
                all_collected.append(row)
                count_for_star += 1

            print(f"    -> Successfully collected {count_for_star} reviews for {star}★")
            # Polite pause to respect Play Store rate limits
            time.sleep(1.0)

        except Exception as e:
            print(f"    [!] Error collecting reviews for {star}★: {e}")

    df = pd.DataFrame(all_collected, columns=UNIVERSAL_SCHEMA)
    return df


def main():
    df = fetch_playstore_reviews(TARGET_PLAYSTORE_REVIEWS)
    print(f"\n[*] Total Play Store reviews collected: {len(df)}")

    # Sanity checks
    assert list(df.columns) == UNIVERSAL_SCHEMA, f"Columns do not match {UNIVERSAL_SCHEMA}"
    assert df["id"].is_unique, "Review IDs are not unique!"

    # Save to CSV
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"[✓] Saved Play Store reviews to: {OUTPUT_FILE}")

    # Display breakdown
    print("\nRating Distribution:")
    print(df["rating"].value_counts().sort_index().to_string())
    print("\nSample Preview:")
    for _, row in df.head(3).iterrows():
        print(f"[{row['id']}] ({row['rating']}★, {row['date']}): {row['text'][:80]}...")


if __name__ == "__main__":
    main()
