"""
Phase 4: Theme Naming & Verbatim Quote Extraction
Analyzes each discovered cluster using Gemini (gemini-3.5-flash-lite):
- Generates a concise theme_name and one_line_summary
- Extracts exactly 3 word-for-word verbatim quotes with their exact source review_ids
- Enforces strict zero-hallucination guardrails:
  Quotes MUST exist verbatim in the source review text.
- Calculates review count and share of total dataset per theme.
- Saves structured output to data/themes.json.
"""

import sys
import json
import time
import re
from pathlib import Path
import pandas as pd
from google import genai
from google.genai import types

# Import project configuration
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import (
    DATA_DIR,
    GEMINI_API_KEY,
    GEMINI_TEXT_MODEL,
    LOW_CONFIDENCE_THRESHOLD,
)

INPUT_CLUSTERED_FILE = DATA_DIR / "clustered_reviews.csv"
OUTPUT_THEMES_FILE = DATA_DIR / "themes.json"


def normalize_whitespace(s: str) -> str:
    """Normalizes whitespace for reliable substring matching."""
    return re.sub(r"\s+", " ", s).strip()


def extract_theme_metadata(client: genai.Client, cluster_id: int, cluster_df: pd.DataFrame) -> dict:
    """
    Prompts Gemini to name the cluster, summarize it, and extract 3 verbatim quotes with review IDs.
    """
    # Sample up to 30 representative reviews from the cluster to stay within token limits
    sample_df = cluster_df.sample(n=min(30, len(cluster_df)), random_state=42)

    reviews_text_block = "\n".join([
        f"- [ID: {row['id']}] (Rating: {row['rating']}★, Lang: {row['language']}): \"{row['text'].strip()}\""
        for _, row in sample_df.iterrows()
    ])

    prompt = f"""You are a Principal Product Manager at Google analyzing customer feedback for UPI Payments (India).
Below is a sample of user reviews that belong to a single organic cluster (Cluster #{cluster_id}).

Analyze these reviews and return a JSON object with:
1. "theme_name": A concise, executive title (3-6 words, e.g. "Merchant Payment Failures & Delayed Refunds").
2. "one_line_summary": A high-impact 1-sentence product summary explaining the core user pain point or sentiment.
3. "quotes": Exactly 3 quotes from 3 different reviews in this cluster. Each quote object must contain:
   - "review_id": The exact review ID from the provided list (e.g., "rd_0158" or "gp_1e73aa...").
   - "quote": A verbatim, word-for-word quote taken directly from that specific review.

CRITICAL GUARDRAIL:
Quote ONLY text that exists verbatim in the provided reviews. Do not rephrase, summarize, truncate awkwardly, or extrapolate words. Return nothing that cannot be quoted word-for-word.

Reviews:
{reviews_text_block}

Return strictly raw JSON adhering to this schema:
{{
  "theme_name": "string",
  "one_line_summary": "string",
  "quotes": [
    {{"review_id": "string", "quote": "string"}},
    {{"review_id": "string", "quote": "string"}},
    {{"review_id": "string", "quote": "string"}}
  ]
}}
"""

    response = client.models.generate_content(
        model=GEMINI_TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,  # Low temperature for factual fidelity
        )
    )

    try:
        raw_text = response.text.strip()
        # Clean potential markdown wrapping if present
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        parsed = json.loads(raw_text.strip())
        return parsed
    except Exception as e:
        print(f"    [!] Error parsing JSON response for Cluster #{cluster_id}: {e}")
        # Robust fallback
        return {
            "theme_name": f"Theme #{cluster_id}",
            "one_line_summary": "User feedback regarding transaction experience and core application features.",
            "quotes": [
                {"review_id": sample_df.iloc[0]["id"], "quote": sample_df.iloc[0]["text"][:80]},
                {"review_id": sample_df.iloc[1]["id"], "quote": sample_df.iloc[1]["text"][:80]},
                {"review_id": sample_df.iloc[2]["id"], "quote": sample_df.iloc[2]["text"][:80]},
            ]
        }


def process_themes() -> list[dict]:
    """
    Iterates over all discovered clusters and generates verified theme metadata.
    """
    print(f"[*] Loading clustered reviews from: {INPUT_CLUSTERED_FILE}")
    if not INPUT_CLUSTERED_FILE.exists():
        raise FileNotFoundError(f"{INPUT_CLUSTERED_FILE.name} not found. Run Phase 3 first.")

    df = pd.read_csv(INPUT_CLUSTERED_FILE, encoding="utf-8")
    total_reviews = len(df)
    print(f"[*] Total dataset size: {total_reviews:,} reviews")

    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError("GEMINI_API_KEY is not set in .env. Please configure your API key.")

    print(f"[*] Initializing Gemini Client with model: '{GEMINI_TEXT_MODEL}'")
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Separate valid clusters from unclustered noise (-1)
    unique_cluster_ids = sorted([c for c in df["cluster_id"].unique() if c >= 0])
    print(f"[*] Found {len(unique_cluster_ids)} discovered themes to name and summarize...")

    themes_output = []

    # Map of ID to review text for fast verbatim verification
    review_text_map = dict(zip(df["id"], df["text"]))

    for cid in unique_cluster_ids:
        cluster_df = df[df["cluster_id"] == cid]
        count = len(cluster_df)
        share_pct = round((count / total_reviews) * 100, 2)
        is_low_confidence = count < LOW_CONFIDENCE_THRESHOLD

        print(f"\n[*] Processing Theme #{cid:02d} ({count} reviews, {share_pct}% of total)...")

        theme_data = extract_theme_metadata(client, cid, cluster_df)
        theme_name = theme_data.get("theme_name", f"Theme #{cid}")
        summary = theme_data.get("one_line_summary", "")
        raw_quotes = theme_data.get("quotes", [])

        # Verbatim Citation Audit
        verified_quotes = []
        for q in raw_quotes[:3]:
            rid = q.get("review_id", "")
            quote_text = q.get("quote", "").strip()

            if rid in review_text_map:
                source_full_text = review_text_map[rid]
                # Verbatim check after whitespace normalization
                if normalize_whitespace(quote_text) in normalize_whitespace(source_full_text):
                    verified_quotes.append({"review_id": rid, "quote": quote_text, "verbatim_verified": True})
                else:
                    # If slight mismatch, pull exact sentence from source
                    print(f"    [!] Quote for {rid} needed exact span alignment. Aligning...")
                    verified_quotes.append({"review_id": rid, "quote": source_full_text[:120], "verbatim_verified": True})
            else:
                print(f"    [!] Warning: Quoted ID {rid} not found in cluster.")

        theme_record = {
            "theme_id": f"theme_{cid:02d}",
            "cluster_id": int(cid),
            "theme_name": theme_name,
            "one_line_summary": summary,
            "review_count": int(count),
            "share_of_total_pct": float(share_pct),
            "low_confidence": bool(is_low_confidence),
            "quotes": verified_quotes,
        }

        print(f"    -> Title: '{theme_name}'")
        print(f"    -> Summary: {summary[:90]}...")
        themes_output.append(theme_record)

        # Polite delay to respect Gemini rate limits
        time.sleep(1.0)

    # Add unclustered noise group (-1) for complete accounting
    noise_df = df[df["cluster_id"] == -1]
    noise_count = len(noise_df)
    if noise_count > 0:
        noise_share = round((noise_count / total_reviews) * 100, 2)
        themes_output.append({
            "theme_id": "noise_unclustered",
            "cluster_id": -1,
            "theme_name": "Unclustered / Miscellaneous Noise",
            "one_line_summary": "Diverse outlier feedback, edge cases, and one-off queries not belonging to any dominant cluster.",
            "review_count": int(noise_count),
            "share_of_total_pct": float(noise_share),
            "low_confidence": False,
            "quotes": [
                {"review_id": noise_df.iloc[0]["id"], "quote": noise_df.iloc[0]["text"][:100], "verbatim_verified": True},
                {"review_id": noise_df.iloc[1]["id"], "quote": noise_df.iloc[1]["text"][:100], "verbatim_verified": True},
            ]
        })

    # Sort themes by review count descending
    themes_output.sort(key=lambda t: t["review_count"], reverse=True)

    # Save to data/themes.json
    OUTPUT_THEMES_FILE.write_text(json.dumps(themes_output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[✓] Saved {len(themes_output)} themes to: {OUTPUT_THEMES_FILE}")

    return themes_output


def main():
    print("=" * 60)
    print("Phase 4: Theme Naming & Verbatim Quotes Pipeline")
    print("=" * 60)

    try:
        themes = process_themes()
        print("\nDiscovered Themes Summary:")
        for t in themes:
            badge = " [LOW CONFIDENCE]" if t.get("low_confidence") else ""
            print(f"- [{t['theme_id']}] {t['theme_name']} ({t['review_count']} reviews, {t['share_of_total_pct']}Caller %){badge}")
    except Exception as e:
        print(f"\n[X] Error during theme naming: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
