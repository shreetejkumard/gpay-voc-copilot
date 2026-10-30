"""
Phase 7 Evaluation Exporter: Google Sheets Ready CSV Export
Exports all evaluation and pipeline audit results into 5 formatted CSV files
specifically tailored to be copied/pasted into Google Sheets tabs:

Tab 1: Data cleaning      (Pipeline Funnel, Filtering breakdown, Language stats)
Tab 2: Citation check     (Verbatim string match audit, Zero hallucination scorecard)
Tab 3: Theme accuracy     (Human benchmark vs Model cluster agreement)
Tab 4: Failure modes      (Sarcasm, Hinglish, Bot Spam, Tiny Cluster tests)
Tab 5: Fixes and Roadmap  (Evidence-backed recommendations, Metrics, Risks, Citations)
"""

import sys
import json
import shutil
from pathlib import Path
import pandas as pd

# Import project configuration
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import DATA_DIR, EVALS_DIR

CLEANING_LOG_FILE = DATA_DIR / "cleaning_log.json"
CITATION_CHECK_CSV = EVALS_DIR / "results" / "eval_citation_check.csv"
THEME_ACCURACY_CSV = EVALS_DIR / "results" / "eval_theme_accuracy.csv"
FAILURE_MODES_CSV = EVALS_DIR / "results" / "eval_failure_modes.csv"
RECOMMENDATIONS_FILE = DATA_DIR / "recommendations.json"

SHEETS_EXPORT_DIR = EVALS_DIR / "results" / "google_sheets_export"


def export_google_sheets_tabs():
    """
    Creates and populates the 5 Google Sheets tab CSVs.
    """
    SHEETS_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 65)
    print("Exporting All Evaluation Results for Google Sheets")
    print(f"Target Directory: {SHEETS_EXPORT_DIR}")
    print("=" * 65)

    # --- TAB 1: Data Cleaning Funnel ---
    print("[*] Generating Tab 1: Data Cleaning...")
    if CLEANING_LOG_FILE.exists():
        log = json.loads(CLEANING_LOG_FILE.read_text(encoding="utf-8"))
        tab1_rows = [
            {"Metric": "Starting Merged Reviews", "Value": log.get("rows_before", 0), "Notes": "Raw merged data from Play Store and Reddit"},
            {"Metric": "Exact Duplicates Removed", "Value": log.get("duplicates_removed", 0), "Notes": "Identical review text dropped"},
            {"Metric": "Near-Duplicates Removed", "Value": log.get("near_duplicates_removed", 0), "Notes": "Punctuation/whitespace/casing variations dropped"},
            {"Metric": "Short Reviews Dropped (< 5 words)", "Value": log.get("short_rows_removed", 0), "Notes": "Low-signal praise/complaints ('good', 'nice app')"},
            {"Metric": "Clean High-Signal Reviews Retained", "Value": log.get("rows_after", 0), "Notes": "Information-dense corpus passed to clustering"},
            {"Metric": "Corpus Retention Rate", "Value": f"{log.get('retained_percentage', 0)}%", "Notes": "Quality-to-noise ratio"},
            {"Metric": "Language: English (en)", "Value": log.get("language_distribution", {}).get("en", 0), "Notes": "Standard English reviews"},
            {"Metric": "Language: Hinglish", "Value": log.get("language_distribution", {}).get("hinglish", 0), "Notes": "Romanized Hindi colloquial reviews"},
            {"Metric": "Language: Hindi (hi)", "Value": log.get("language_distribution", {}).get("hi", 0), "Notes": "Devanagari script reviews"},
        ]
        pd.DataFrame(tab1_rows).to_csv(SHEETS_EXPORT_DIR / "tab1_data_cleaning.csv", index=False)
        print("    [✓] Created tab1_data_cleaning.csv")

    # --- TAB 2: Citation Check ---
    print("[*] Generating Tab 2: Citation Check...")
    if CITATION_CHECK_CSV.exists():
        shutil.copy(CITATION_CHECK_CSV, SHEETS_EXPORT_DIR / "tab2_citation_check.csv")
        print("    [✓] Created tab2_citation_check.csv")

    # --- TAB 3: Theme Accuracy ---
    print("[*] Generating Tab 3: Theme Accuracy...")
    if THEME_ACCURACY_CSV.exists():
        shutil.copy(THEME_ACCURACY_CSV, SHEETS_EXPORT_DIR / "tab3_theme_accuracy.csv")
        print("    [✓] Created tab3_theme_accuracy.csv")

    # --- TAB 4: Failure Modes ---
    print("[*] Generating Tab 4: Failure Modes...")
    if FAILURE_MODES_CSV.exists():
        shutil.copy(FAILURE_MODES_CSV, SHEETS_EXPORT_DIR / "tab4_failure_modes.csv")
        print("    [✓] Created tab4_failure_modes.csv")

    # --- TAB 5: Fixes and Roadmap ---
    print("[*] Generating Tab 5: Fixes & Roadmap...")
    if RECOMMENDATIONS_FILE.exists():
        recs = json.loads(RECOMMENDATIONS_FILE.read_text(encoding="utf-8"))
        tab5_rows = []
        for idx, r in enumerate(recs, 1):
            tab5_rows.append({
                "Priority": f"P{idx-1}",
                "Roadmap Initiative": r.get("roadmap_item", ""),
                "Theme Target": r.get("theme_name", ""),
                "Data Justification": r.get("reason", ""),
                "North Star Metric": r.get("success_metric", ""),
                "Risk & Trade-off": r.get("risk", ""),
                "Supporting Review IDs": ", ".join(r.get("supporting_review_ids", [])),
            })
        pd.DataFrame(tab5_rows).to_csv(SHEETS_EXPORT_DIR / "tab5_fixes_and_roadmap.csv", index=False)
        print("    [✓] Created tab5_fixes_and_roadmap.csv")

    print("\n[✓] All 5 Google Sheets tabs exported successfully!")
    print(f"Files are located in: {SHEETS_EXPORT_DIR.resolve()}")


if __name__ == "__main__":
    export_google_sheets_tabs()
