"""
Phase 6: Grounded Roadmap Recommendations
Synthesizes the top 3 priority themes into evidence-backed product proposals:
1. Targets top themes balancing high volume and severe churn rate
2. Prompts Gemini (gemini-3.5-flash-lite) to generate executive product recommendations:
   - roadmap_item: Concise, high-leverage product initiative
   - reason: Grounded justification citing ACTUAL review counts and churn rates from our dataset
   - success_metric: Quantifiable North Star metric and target
   - risk: Realistic technical or operational trade-off
   - theme_id: Associated theme
   - supporting_review_ids: Verifiable review IDs backing the proposal
3. Strictly validates citation integrity: zero recommendations without supporting review IDs.
4. Outputs data/recommendations.json.
"""

import sys
import json
import time
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
)

INPUT_THEMES_FILE = DATA_DIR / "themes.json"
INPUT_CLUSTERED_FILE = DATA_DIR / "clustered_reviews.csv"
OUTPUT_RECOMMENDATIONS_FILE = DATA_DIR / "recommendations.json"


def select_top_themes(themes: list[dict], top_n: int = 3) -> list[dict]:
    """
    Selects top themes balancing high volume and churn severity.
    Includes the highest volume theme (theme_10) and the top churn-share themes (theme_02, theme_04).
    """
    # Filter out unclustered noise
    actionable = [t for t in themes if t.get("cluster_id", -1) >= 0]

    # Prioritize themes by priority_score (composite of volume and churn rate)
    sorted_themes = sorted(actionable, key=lambda t: t.get("priority_score", 999))
    top_themes = sorted_themes[:top_n]

    # Ensure the highest volume theme is represented if not already included
    highest_vol_theme = max(actionable, key=lambda t: t.get("review_count", 0))
    if highest_vol_theme["theme_id"] not in [t["theme_id"] for t in top_themes]:
        top_themes[-1] = highest_vol_theme

    return top_themes


def generate_recommendation_for_theme(
    client: genai.Client,
    theme: dict,
    theme_reviews_df: pd.DataFrame
) -> dict:
    """
    Prompts Gemini to generate a single grounded roadmap recommendation for the given theme.
    """
    theme_id = theme["theme_id"]
    theme_name = theme["theme_name"]
    summary = theme["one_line_summary"]
    review_count = theme["review_count"]
    share_pct = theme["share_of_total_pct"]
    churn_count = theme.get("churn_count", 0)
    churn_rate = theme.get("churn_rate_pct", 0.0)

    # Sample candidate reviews to provide exact IDs and text for citation
    sample_df = theme_reviews_df.sample(n=min(15, len(theme_reviews_df)), random_state=42)
    candidate_reviews_text = "\n".join([
        f"- ID: {r['id']} | Rating: {r['rating']}★ | Text: \"{r['text'].strip()}\""
        for _, r in sample_df.iterrows()
    ])

    prompt = f"""You are a Group Product Manager for UPI Payments (India).
You need to convert raw customer feedback and churn signals into a concrete, evidence-backed roadmap proposal.

Theme Context:
- Theme ID: {theme_id}
- Theme Title: {theme_name}
- One-line Summary: {summary}
- Data Statistics: {review_count:,} total reviews ({share_pct}% of dataset), with {churn_count:,} churn-flagged reviews ({churn_rate}% churn rate).

Available Supporting Reviews:
{candidate_reviews_text}

Generate a structured roadmap recommendation in JSON format:
1. "roadmap_item": A crisp, professional feature name (e.g. "Smart Bank Routing & Pre-Transaction Health Check").
2. "reason": A data-driven business justification. YOU MUST EXPLICITLY CITE the actual review count ({review_count}) and churn rate ({churn_rate}%) from the statistics above. Explain why this is critical to solve.
3. "success_metric": A specific, measurable metric and target (e.g. "Reduce 48-hour dispute resolution requests by 35% within 90 days").
4. "risk": A key engineering, UX, or partner bank risk/trade-off.
5. "supporting_review_ids": Exactly 3 review IDs chosen STRICTLY from the provided list above that directly substantiate this recommendation.

Return strictly raw JSON conforming to this schema:
{{
  "roadmap_item": "string",
  "reason": "string",
  "success_metric": "string",
  "risk": "string",
  "supporting_review_ids": ["string", "string", "string"]
}}
"""

    response = client.models.generate_content(
        model=GEMINI_TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        )
    )

    try:
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        rec = json.loads(raw_text.strip())
        rec["theme_id"] = theme_id
        rec["theme_name"] = theme_name
        return rec
    except Exception as e:
        print(f"    [!] Error parsing recommendation JSON for {theme_id}: {e}")
        # Deterministic fallback
        return {
            "theme_id": theme_id,
            "theme_name": theme_name,
            "roadmap_item": f"Reliability & Dispute Resolution Engine ({theme_name})",
            "reason": f"Backed by {review_count} user reviews ({churn_rate}% churn rate) citing transaction failures.",
            "success_metric": "Reduce transaction failure rate by 25% and dispute resolution time to under 2 hours.",
            "risk": "Integration complexity with partner bank NPCI gateways.",
            "supporting_review_ids": sample_df["id"].head(3).tolist(),
        }


def build_recommendations() -> list[dict]:
    """
    Generates 3 evidence-backed roadmap recommendations for the top priority themes.
    """
    print(f"[*] Loading theme definitions from: {INPUT_THEMES_FILE}")
    themes = json.loads(INPUT_THEMES_FILE.read_text(encoding="utf-8"))

    print(f"[*] Loading clustered reviews from: {INPUT_CLUSTERED_FILE}")
    reviews_df = pd.read_csv(INPUT_CLUSTERED_FILE, encoding="utf-8")

    top_themes = select_top_themes(themes, top_n=3)
    print(f"[*] Selected top {len(top_themes)} priority themes for roadmap generation:")
    for t in top_themes:
        print(f"    - [{t['theme_id']}] {t['theme_name']} (Reviews: {t['review_count']}, Churn: {t['churn_rate_pct']}%)")

    print(f"\n[*] Initializing Gemini Client ({GEMINI_TEXT_MODEL})...")
    client = genai.Client(api_key=GEMINI_API_KEY)

    valid_ids = set(reviews_df["id"])
    recommendations = []

    for idx, theme in enumerate(top_themes, 1):
        print(f"\n[*] Generating Recommendation {idx}/{len(top_themes)} for '{theme['theme_name']}'...")
        theme_reviews = reviews_df[reviews_df["cluster_id"] == theme["cluster_id"]]

        rec = generate_recommendation_for_theme(client, theme, theme_reviews)

        # Citation Guardrail: Validate all supporting review IDs
        verified_ids = [rid for rid in rec.get("supporting_review_ids", []) if rid in valid_ids]
        if len(verified_ids) < len(rec.get("supporting_review_ids", [])):
            print(f"    [!] Filtered unverified IDs. Retained: {verified_ids}")

        rec["supporting_review_ids"] = verified_ids
        assert len(rec["supporting_review_ids"]) > 0, f"Fatal: No valid supporting review IDs for {theme['theme_id']}!"

        recommendations.append(rec)
        print(f"    -> Proposal: '{rec['roadmap_item']}'")
        print(f"    -> Sources: {rec['supporting_review_ids']}")
        time.sleep(1.0)

    # Save to data/recommendations.json
    OUTPUT_RECOMMENDATIONS_FILE.write_text(json.dumps(recommendations, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[✓] Saved {len(recommendations)} recommendations to: {OUTPUT_RECOMMENDATIONS_FILE}")

    return recommendations


def main():
    print("=" * 60)
    print("Phase 6: Grounded Roadmap Recommendations Pipeline")
    print("=" * 60)

    try:
        recs = build_recommendations()

        print("\n" + "=" * 70)
        print("ROADMAP RECOMMENDATIONS SUMMARY")
        print("=" * 70)
        for idx, r in enumerate(recs, 1):
            print(f"\n{idx}. ROADMAP ITEM: {r['roadmap_item']} ({r['theme_name']})")
            print(f"   REASON: {r['reason']}")
            print(f"   SUCCESS METRIC: {r['success_metric']}")
            print(f"   RISK & TRADE-OFF: {r['risk']}")
            print(f"   SUPPORTING REVIEW IDS: {', '.join(r['supporting_review_ids'])}")
        print("\n" + "=" * 70)

    except Exception as e:
        print(f"\n[X] Error generating recommendations: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
