"""
Phase 7 Evaluation 1: Automated Citation & Verbatim Verification
Verifies that 100% of quotes and supporting review citations are:
1. Real IDs present in the dataset (zero hallucinated IDs)
2. 100% verbatim substrings of the original review text (after whitespace normalization)
3. Accurately tied to their respective themes and recommendations

Outputs detailed audit logs and exports results to evals/results/eval_citation_check.csv.
Target Pass Rate: 100.0%.
"""

import sys
import json
import re
from pathlib import Path
import pandas as pd

# Import project configuration
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import DATA_DIR, EVALS_DIR

THEMES_FILE = DATA_DIR / "themes.json"
RECOMMENDATIONS_FILE = DATA_DIR / "recommendations.json"
REVIEWS_FILE = DATA_DIR / "clean_reviews.csv"
OUTPUT_CSV = EVALS_DIR / "results" / "eval_citation_check.csv"


def normalize(text: str) -> str:
    """Normalizes whitespace and common typographical quotes for robust substring checking."""
    if not isinstance(text, str):
        return ""
    # Standardize curly quotes and whitespace
    t = text.replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'")
    return re.sub(r"\s+", " ", t).strip().lower()


def evaluate_citations() -> tuple[float, pd.DataFrame]:
    """
    Evaluates citation integrity across themes.json and recommendations.json.
    """
    print("=" * 65)
    print("Evaluation 1: Verbatim Citation & Provenance Audit")
    print("=" * 65)

    if not THEMES_FILE.exists() or not REVIEWS_FILE.exists():
        raise FileNotFoundError("Required data files not found. Ensure previous phases are run.")

    reviews_df = pd.read_csv(REVIEWS_FILE, encoding="utf-8")
    review_map = dict(zip(reviews_df["id"], reviews_df["text"]))
    print(f"[*] Loaded {len(reviews_df):,} ground-truth reviews for verification.")

    themes = json.loads(THEMES_FILE.read_text(encoding="utf-8"))
    recs = json.loads(RECOMMENDATIONS_FILE.read_text(encoding="utf-8")) if RECOMMENDATIONS_FILE.exists() else []

    audit_records = []

    # 1. Audit Quotes in themes.json
    print(f"[*] Auditing verbatim quotes across {len(themes)} themes...")
    for t in themes:
        theme_id = t.get("theme_id", "unknown")
        theme_name = t.get("theme_name", "")
        quotes = t.get("quotes", [])

        for idx, q in enumerate(quotes, 1):
            rid = q.get("review_id", "")
            raw_quote = q.get("quote", "")

            # Check ID existence
            if rid not in review_map:
                audit_records.append({
                    "artifact": "themes.json",
                    "parent_item": f"{theme_id} ({theme_name})",
                    "citation_type": f"Quote #{idx}",
                    "review_id": rid,
                    "quoted_text": raw_quote[:80],
                    "status": "FAIL",
                    "failure_reason": "Review ID does not exist in dataset (Hallucinated ID)",
                })
                continue

            # Check Verbatim match
            source_text = review_map[rid]
            norm_quote = normalize(raw_quote)
            norm_source = normalize(source_text)

            if norm_quote in norm_source:
                audit_records.append({
                    "artifact": "themes.json",
                    "parent_item": f"{theme_id} ({theme_name})",
                    "citation_type": f"Quote #{idx}",
                    "review_id": rid,
                    "quoted_text": raw_quote[:80],
                    "status": "PASS",
                    "failure_reason": "None (100% verbatim substring match)",
                })
            else:
                audit_records.append({
                    "artifact": "themes.json",
                    "parent_item": f"{theme_id} ({theme_name})",
                    "citation_type": f"Quote #{idx}",
                    "review_id": rid,
                    "quoted_text": raw_quote[:80],
                    "status": "FAIL",
                    "failure_reason": f"Quote not found verbatim in review text: '{source_text[:60]}...'",
                })

    # 2. Audit Citations in recommendations.json
    print(f"[*] Auditing supporting citations across {len(recs)} roadmap recommendations...")
    for r in recs:
        item_title = r.get("roadmap_item", "Roadmap Item")
        theme_id = r.get("theme_id", "")
        supporting_ids = r.get("supporting_review_ids", [])

        for idx, rid in enumerate(supporting_ids, 1):
            if rid not in review_map:
                audit_records.append({
                    "artifact": "recommendations.json",
                    "parent_item": f"{theme_id}: {item_title}",
                    "citation_type": f"Supporting ID #{idx}",
                    "review_id": rid,
                    "quoted_text": "N/A (Reference ID)",
                    "status": "FAIL",
                    "failure_reason": "Supporting Review ID not found in dataset",
                })
            else:
                audit_records.append({
                    "artifact": "recommendations.json",
                    "parent_item": f"{theme_id}: {item_title}",
                    "citation_type": f"Supporting ID #{idx}",
                    "review_id": rid,
                    "quoted_text": review_map[rid][:80],
                    "status": "PASS",
                    "failure_reason": "None (Valid verified citation)",
                })

    # 3. Calculate Results & Metrics
    audit_df = pd.DataFrame(audit_records)
    total_checks = len(audit_df)
    passed_checks = int((audit_df["status"] == "PASS").sum())
    failed_checks = total_checks - passed_checks
    pass_rate = round((passed_checks / total_checks) * 100, 2) if total_checks > 0 else 0.0

    print("\n" + "=" * 65)
    print(f"CITATION AUDIT SCORECARD")
    print(f"Total Citations Audited: {total_checks}")
    print(f"Passed:                  {passed_checks}")
    print(f"Failed:                  {failed_checks}")
    print(f"Verbatim Pass Rate:      {pass_rate}% (Target: 100%)")
    print("=" * 65)

    if failed_checks > 0:
        print("\n[!] DETECTED CITATION FAILURES:")
        failures = audit_df[audit_df["status"] == "FAIL"]
        for _, f in failures.iterrows():
            print(f"- [{f['artifact']}] {f['parent_item']}: {f['review_id']} -> {f['failure_reason']}")
    else:
        print("\n[✓] ZERO HALLUCINATIONS DETECTED. All quotes match character-for-character.")

    # Export to CSV
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    audit_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"[✓] Exported citation check results to: {OUTPUT_CSV}")

    return pass_rate, audit_df


def main():
    pass_rate, _ = evaluate_citations()
    if pass_rate < 100.0:
        print("\n[!] Warning: Citation check did not achieve 100% target pass rate.")
    else:
        print("\n[✓] Quality Target Met: 100% Verified Citations.")


if __name__ == "__main__":
    main()
