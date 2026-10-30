"""
Phase 5: Churn Signals & Theme Prioritization
Detects churn indicators and severe friction signals across all reviews:
1. Scans review text against configurable churn keywords (English & Hinglish) from config.py
2. Flags churn intent: app uninstalls, switching to competitors (PhonePe, Paytm),
   unresolved deductions, blocked accounts, and scam complaints.
3. Computes theme-level churn volume, churn rate (percentage of theme exhibiting churn intent),
   and most frequent churn triggers.
4. Produces dual rankings:
   - Rank by Volume (widespread friction)
   - Rank by Churn Rate (high-severity attrition risk)
5. Enriches data/themes.json with churn metrics and exports data/churn_ranked_themes.csv.
"""

import sys
import json
import re
from pathlib import Path
from collections import Counter
import pandas as pd

# Import project configuration
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import DATA_DIR, CHURN_KEYWORDS

INPUT_CLUSTERED_FILE = DATA_DIR / "clustered_reviews.csv"
INPUT_THEMES_FILE = DATA_DIR / "themes.json"
OUTPUT_THEMES_FILE = DATA_DIR / "themes.json"
OUTPUT_CHURN_CSV = DATA_DIR / "churn_ranked_themes.csv"


def detect_churn_signals(text: str) -> list[str]:
    """
    Checks if a review contains any churn keywords or phrases.
    Returns the list of matching keywords found.
    """
    if not isinstance(text, str):
        return []

    text_lower = text.lower()
    matches = []

    for kw in CHURN_KEYWORDS:
        # Use regex boundary matching where appropriate or substring search
        pattern = r"\b" + re.escape(kw.lower()) + r"\b"
        if re.search(pattern, text_lower):
            matches.append(kw)
        elif kw.lower() in text_lower:
            # Fallback for multi-word phrases or colloquial strings
            matches.append(kw)

    # Return unique matches
    return sorted(list(set(matches)))


def analyze_churn() -> tuple[list[dict], pd.DataFrame]:
    """
    Runs churn signal analysis across clustered reviews, updates themes.json,
    and returns enriched themes and a summary dataframe.
    """
    print(f"[*] Loading clustered reviews from: {INPUT_CLUSTERED_FILE}")
    if not INPUT_CLUSTERED_FILE.exists():
        raise FileNotFoundError(f"{INPUT_CLUSTERED_FILE.name} not found. Run Phase 3 first.")

    df = pd.read_csv(INPUT_CLUSTERED_FILE, encoding="utf-8")
    print(f"[*] Total reviews to analyze: {len(df):,}")

    print(f"[*] Loading theme definitions from: {INPUT_THEMES_FILE}")
    if not INPUT_THEMES_FILE.exists():
        raise FileNotFoundError(f"{INPUT_THEMES_FILE.name} not found. Run Phase 4 first.")

    themes_data = json.loads(INPUT_THEMES_FILE.read_text(encoding="utf-8"))

    # 1. Flag churn on every review
    print(f"[*] Scanning reviews against {len(CHURN_KEYWORDS)} English & Hinglish churn markers...")
    df["churn_triggers"] = df["text"].apply(detect_churn_signals)
    df["is_churn"] = df["churn_triggers"].apply(lambda t: len(t) > 0)

    total_churn_reviews = int(df["is_churn"].sum())
    total_churn_pct = round((total_churn_reviews / len(df)) * 100, 2)
    print(f"[✓] Churn signals detected in {total_churn_reviews:,} of {len(df):,} reviews ({total_churn_pct}%)")

    # 2. Aggregate churn metrics per theme
    theme_churn_stats = {}
    for cid in df["cluster_id"].unique():
        theme_reviews = df[df["cluster_id"] == cid]
        count = len(theme_reviews)
        churn_count = int(theme_reviews["is_churn"].sum())
        churn_rate = round((churn_count / count) * 100, 2) if count > 0 else 0.0

        # Collect all triggered keywords in this cluster
        all_triggers = [kw for sublist in theme_reviews["churn_triggers"] for kw in sublist]
        trigger_counts = Counter(all_triggers).most_common(3)
        top_triggers = [f"{kw} ({cnt})" for kw, cnt in trigger_counts]

        theme_churn_stats[cid] = {
            "churn_count": churn_count,
            "churn_rate_pct": churn_rate,
            "top_churn_triggers": top_triggers,
        }

    # 3. Enrich themes_data
    for theme in themes_data:
        cid = theme.get("cluster_id", -1)
        stats = theme_churn_stats.get(cid, {"churn_count": 0, "churn_rate_pct": 0.0, "top_churn_triggers": []})
        theme["churn_count"] = stats["churn_count"]
        theme["churn_rate_pct"] = stats["churn_rate_pct"]
        theme["top_churn_triggers"] = stats["top_churn_triggers"]

    # 4. Compute Dual Rankings (Excluding noise bucket for actionable ranking)
    actionable_themes = [t for t in themes_data if t["cluster_id"] >= 0]
    noise_themes = [t for t in themes_data if t["cluster_id"] == -1]

    # Rank by Volume (1 = highest volume)
    actionable_themes.sort(key=lambda t: t["review_count"], reverse=True)
    for rank, t in enumerate(actionable_themes, 1):
        t["rank_by_volume"] = rank

    # Rank by Churn Share (1 = highest churn percentage)
    actionable_themes.sort(key=lambda t: (t["churn_rate_pct"], t["churn_count"]), reverse=True)
    for rank, t in enumerate(actionable_themes, 1):
        t["rank_by_churn_share"] = rank

    # Set noise rank to null/N/A
    for t in noise_themes:
        t["rank_by_volume"] = None
        t["rank_by_churn_share"] = None

    # Re-sort themes by combined urgency: weighted score of volume + churn rate
    # Combined Urgency Score = (Volume Rank * 0.4) + (Churn Rank * 0.6) -> lowest score is highest priority
    for t in actionable_themes:
        t["priority_score"] = round((t["rank_by_volume"] * 0.4) + (t["rank_by_churn_share"] * 0.6), 2)
    actionable_themes.sort(key=lambda t: t["priority_score"])

    # Combine back with noise at the end
    final_themes = actionable_themes + noise_themes

    # 5. Save updated themes.json
    OUTPUT_THEMES_FILE.write_text(json.dumps(final_themes, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[✓] Enriched and saved: {OUTPUT_THEMES_FILE}")

    # 6. Export tabular summary to CSV
    summary_rows = []
    for t in actionable_themes:
        summary_rows.append({
            "theme_id": t["theme_id"],
            "theme_name": t["theme_name"],
            "review_count": t["review_count"],
            "share_of_total_pct": t["share_of_total_pct"],
            "rank_by_volume": t["rank_by_volume"],
            "churn_count": t["churn_count"],
            "churn_rate_pct": t["churn_rate_pct"],
            "rank_by_churn_share": t["rank_by_churn_share"],
            "priority_score": t["priority_score"],
            "top_triggers": ", ".join(t["top_churn_triggers"]),
            "low_confidence": t.get("low_confidence", False),
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(OUTPUT_CHURN_CSV, index=False, encoding="utf-8")
    print(f"[✓] Saved churn rankings CSV to: {OUTPUT_CHURN_CSV}")

    return final_themes, summary_df


def main():
    print("=" * 60)
    print("Phase 5: Churn Signals & Dual Theme Prioritization")
    print("=" * 60)

    try:
        themes, summary_df = analyze_churn()

        print("\n" + "=" * 75)
        print(f"{'Theme ID':<10} | {'Theme Name':<32} | {'Vol (Rank)':<11} | {'Churn Rate (Rank)':<18}")
        print("=" * 75)
        for _, r in summary_df.iterrows():
            vol_str = f"{r['review_count']} (#{r['rank_by_volume']})"
            churn_str = f"{r['churn_rate_pct']}% (#{r['rank_by_churn_share']})"
            print(f"{r['theme_id']:<10} | {r['theme_name'][:32]:<32} | {vol_str:<11} | {churn_str:<18}")
        print("=" * 75)

        print("\nTop 3 Themes by Churn Share (Highest Attrition Risk):")
        top_churn = summary_df.sort_values(by="churn_rate_pct", ascending=False).head(3)
        for _, r in top_churn.iterrows():
            print(f"- {r['theme_name']}: {r['churn_rate_pct']}% of users flagged for churn (Triggers: {r['top_triggers']})")

    except Exception as e:
        print(f"\n[X] Error during churn analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
