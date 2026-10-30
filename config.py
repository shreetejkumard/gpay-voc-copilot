"""
Configuration settings for Voice of Customer Copilot for Google Pay (India).
Centralizes file paths, model configurations, data schemas, and churn detection heuristics.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base project paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SCRIPTS_DIR = BASE_DIR / "scripts"
EVALS_DIR = BASE_DIR / "evals"
APP_DIR = BASE_DIR / "app"

# Ensure essential directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Google Gemini API configuration
# Read from environment variables with sensible defaults
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-3.5-flash-lite")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

# Google Play Store scraping parameters
PLAYSTORE_APP_ID = "com.google.android.apps.nbu.paisa.user"  # Google Pay India app package
PLAYSTORE_LANG = "en"
PLAYSTORE_COUNTRY = "in"
TARGET_PLAYSTORE_REVIEWS = 4000  # Scaled up for higher volume (800 per star rating)

# Universal Data Schema
# Every data source must strictly adhere to these exact 7 columns
UNIVERSAL_SCHEMA = ["id", "source", "date", "rating", "text", "url", "language"]

# Clustering & Quality thresholds
MIN_CLUSTER_SIZE = 15           # Minimum cluster size for HDBSCAN
LOW_CONFIDENCE_THRESHOLD = 35   # Clusters with fewer reviews receive a "Low Confidence" badge
MIN_REVIEW_WORDS = 5            # Filter out low-effort reviews (e.g. "good", "nice app")

# Churn indicator keywords (English & Hinglish)
# Configurable list representing user frustration and churn intent
CHURN_KEYWORDS = [
    "uninstalled",
    "uninstall",
    "switching",
    "switched to phonepe",
    "switched to paytm",
    "switch to paytm",
    "switch to phonepe",
    "phonepe",
    "paytm",
    "money deducted",
    "amount deducted",
    "no refund",
    "refund not received",
    "account blocked",
    "blocked my account",
    "delete",
    "deleted",
    "worst app",
    "useless app",
    "fraud app",
    "cheated",
    "scam",
    # Hinglish & Hindi colloquial expressions
    "paise kat gaye",
    "paise kat gye",
    "paisa phas gaya",
    "paisa fas gaya",
    "bakwas app",
    "ghatiya",
    "chor app",
    "refund nahi aaya",
    "refund nahi mila",
    "kaam nahi kar raha",
]
