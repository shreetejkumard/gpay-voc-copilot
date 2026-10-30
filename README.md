# Voice of Customer Copilot (VoC) 💳⚡

> **"This is the most Product Manager project on this list, because this is a real workflow that you do on day 1 of your product manager job."**  
> *Turning messy, unstructured feedback from Play Store reviews, support tickets, and community forums into ranked pain points, verifiable customer quotes, churn signals, and 3 evidence-backed roadmap recommendations.*

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Gemini 3.5 Flash](https://img.shields.io/badge/LLM-Gemini%203.5%20Flash-4285F4.svg)](https://ai.google.dev/)
[![Citation Pass Rate](https://img.shields.io/badge/Citations-100%25%20Verbatim-34A853.svg)](#1-verbatim-citation-audit)
[![Daily Cron](https://img.shields.io/badge/Pipeline-Daily%20Cron%20Sync-blueviolet.svg)](#-the-stronger-version-automated-daily-cron-pipeline)
[![Deployed on Vercel](https://img.shields.io/badge/Deployed-Vercel-black.svg)](https://vercel.com)

---

## 📌 The Day-1 PM Manifesto: Why This Exists

In a real product management job, customer feedback doesn't arrive in clean spreadsheets:
- It pours in from **Play Store reviews, customer support tickets, sales calls, user interviews, and WhatsApp screenshots from founders**.
- The Product Manager's core responsibility is to **turn messy, qualitative chaos into prioritized product decisions**.

Most AI portfolio projects build basic "summarizers". A generic summarizer says:
> *"Users are unhappy with payments."*

**A real Product Manager asks:**
> *"Based on what? How many users? What exact words did they use? What is the churn rate? What is the risk and North Star metric?"*

This **Voice of Customer Copilot** is built to answer those exact questions with mathematical rigor.

---

## ⚖️ The APM Standard: Bad Output vs. Good Output

| Dimension | The Naive "Bad" Output ❌ | The Grounded "Good" Output (Our Copilot) ✅ |
| :--- | :--- | :--- |
| **Headline** | *"Users are unhappy with payments and server timeouts."* | **Theme #2**: *"Bank Timeouts & Delayed Refunds Driving Active Churn to Competitor Soundbox"* |
| **Quantification** | *"Many users complained about failed payments."* (Subjective, unquantified) | **68 reviews (3.31% of dataset)**, with a **100.0% active churn rate** (68/68 users cite uninstalling or switching to competitor QR). |
| **Root Cause** | *"Payment gateway issues."* | Specific systemic failure: **SBI and HDFC peak-hour server timeouts** where money is debited but takes $>7$ business days to refund, causing public embarrassment at checkout. |
| **Verbatim Citations** | None (or hallucinated paraphrases). | **100% Verbatim & Traceable**: <br>• `[rd_1108]`: *"UPI app transaction failed due to bank server timeout with SBI. My ₹1200 has been stuck for over a week with no refund in sight. Switched to Paytm soundbox QR, at least you get immediate confirmation."* |
| **Roadmap Proposal** | *"Make payments more reliable."* | **Roadmap Item**: *"Smart Bank Routing & Automated Real-Time Refund Tracking"* |
| **North Star KPI** | *"Improve user satisfaction (CSAT)."* (Unmeasurable) | **Measurable Metric**: Reduce bank-timeout failure rates by **30%** and automate **80% of stuck refunds to clear within T+1 day** over 90 days. |
| **Risk & Trade-off** | Unstated ("Just fix it"). | **Explicit Trade-off**: Heavy reliance on partner bank API uptime and webhook responsiveness; automated provisional refunds introduce short-term financial ledger risk. |

---

## 🖥️ The 3-Screen SaaS Workflow: Upload → Analyze → Executive Dashboard

Built with a focused, utility-first user experience (inspired by *iLovePDF* and modern SaaS apps):

1. **Screen 1: Minimal Upload & Ingestion Landing Page**
   - **Feedback Upload Dropzone:** Drag & drop customer feedback files (`.csv`, `.xlsx`, `.pdf`, `.docx`, `.txt`) or paste raw unstructured feedback text.
   - **Live Review Detection:** Real-time feedback parser estimating review counts and validating formatting.
   - **Trial Dataset & 1-Click Demo:** Downloadable `sample_customer_reviews.csv` and instant 1-click evaluation button for interviewers and reviewers who don't have messy feedback files on hand.

2. **Screen 2: Real-Time Processing Pipeline Animation**
   - Step 1: Data Normalization & Bot Spam Deduplication
   - Step 2: Language & Nuance Classification (English, Hindi, Hinglish)
   - Step 3: Unsupervised Theme Clustering (HDBSCAN text embeddings)
   - Step 4: Verbatim Quote & Churn Signal Extraction
   - Step 5: Roadmap Synthesis & Verification Assertions

3. **Screen 3: Executive Product Manager Dashboard**
   - **Executive KPI Bar:** Feedback volume analyzed, clustered pain points, active churn risk %, and 100% verbatim citation pass rate.
   - **Ranked Themes & Quotes:** 12 organic pain point clusters with volume, churn risk, and expandable 100% verbatim customer quotes.
   - **What to Put on the Roadmap:** 3 evidence-backed proposals with real counts, North Star KPIs, and engineering risk mitigations.
   - **Bad vs. Good Output Case Study:** Side-by-side comparison illustrating why naive LLM summarizers fail executive product reviews.
   - **AI Safety & Evals Suite:** 100% verbatim citation audit, 4/4 edge case stress tests, and 5 downloadable Google Sheets tabs.

---

## 🔄 The Stronger Version: Automated Daily Cron Pipeline

Rather than being a one-off analysis, this repository features an **automated daily ingestion and synthesis pipeline** orchestrated by **GitHub Actions** ([`.github/workflows/daily_sync.yml`](file:///.github/workflows/daily_sync.yml)):

```
┌─────────────────────────────────────────────────────────────┐
│             DAILY CRON TRIGGER (00:00 UTC / 05:30 IST)      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. PULL: Ingest latest Play Store & community reviews       │
│ 2. CLEAN: Deduplicate, strip noise, tag Hinglish/Hindi      │
│ 3. CLUSTER: Run HDBSCAN density clustering                  │
│ 4. SYNTHESIZE: Gemini 3.5 Flash names themes & extracts quotes │
│ 5. CHURN: Score attrition intensity & compute dual rankings │
│ 6. EVALUATE: Assert 100% verbatim citation pass rate         │
│ 7. DEPLOY: Auto-commit fresh data bundle back to main repo   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔬 Evaluation Results & Safety Guardrails (`evals/`)

### 1. Verbatim Citation Audit (`evals/citation_check.py`)
- **Metric:** Verbatim Substring Matching against ground-truth raw review texts.
- **Pass Rate:** **100.0%** (47 out of 47 quotes and citations verified with 0 failures).
- **Target:** 100% (Guarantees zero hallucinated quotes presented to product leadership).

### 2. Failure Mode & Edge Case Stress Tests (`evals/failure_mode_tests.py`)
| Test ID | Edge Case | Observed System Behavior | Verdict |
| :--- | :--- | :--- | :--- |
| **`FM_01`** | **Sarcasm Handling** (*"Great, another failed payment! Thanks..."*) | Caught customer friction despite positive surface words ("Great", "Thanks"). | **`PASS`** |
| **`FM_02`** | **Hinglish Processing** (*"Bhai paise kat gaye dost ko nahi mile..."*) | Correctly tagged as `hinglish` and extracted churn triggers (`paise kat gaye`, `uninstalled`). | **`PASS`** |
| **`FM_03`** | **Duplicate Bot Spam** | Normalized hashing purged 100% of duplicate promotional bot clones. | **`PASS`** |
| **`FM_04`** | **Tiny Cluster Guardrail** | Automatically attached `Low Confidence (< 35 reviews)` badge to avoid over-indexing. | **`PASS`** |

### 3. Google Sheets Export Portfolio Tabs (`evals/export_all_sheets.py`)
Pre-formatted CSVs located in `evals/results/google_sheets_export/` ready to paste into your portfolio Google Sheet:
- `tab1_data_cleaning.csv` (Funnel metrics)
- `tab2_citation_check.csv` (100% citation audit)
- `tab3_theme_accuracy.csv` (Human benchmark comparison)
- `tab4_failure_modes.csv` (Edge case test scorecard)
- `tab5_fixes_and_roadmap.csv` (Roadmap proposals with metrics and trade-offs)

---

## 🎯 3 Evidence-Backed Roadmap Recommendations

### 1. Smart Bank Routing & Automated Real-Time Refund Tracking (Priority: P0)
- **Target Theme:** `theme_02` (Bank Timeouts & Delayed Refunds)
- **Data Justification:** Directly addresses 68 user reviews representing a **100.0% churn rate**, where users permanently switch to competitor soundboxes due to locked funds exceeding 7 days during SBI/HDFC server downtime.
- **North Star Metric:** Reduce bank-timeout failure rates by **30%** and automate **80% of stuck refunds to clear within T+1 day** over 90 days.
- **Engineering Risk & Trade-off:** Heavy reliance on partner bank API uptime and webhook responsiveness for real-time reconciliation.
- **Verified Review Citations:** `rd_1108`, `rd_0975`, `rd_0758`

### 2. Real-Time Payment Failure Fallback & Instant Provisional Reversal (Priority: P0)
- **Target Theme:** `theme_04` (Merchant POS Payment Failures)
- **Data Justification:** Accounts for 41 reviews with a **100.0% active churn rate** where users immediately uninstalled after facing public embarrassment at grocery counters when money was debited but showed "Processing".
- **North Star Metric:** Reduce merchant payment failure dispute escalations by **50%** and decrease delayed-refund churn from 100% to under 15% within 90 days.
- **Engineering Risk & Trade-off:** Automated provisional refunds introduce short-term financial ledger reconciliation and fraud risk.
- **Verified Review Citations:** `rd_0672`, `rd_1539`, `rd_1645`

### 3. Intelligent Gateway Routing & Automated UPI Lite Health Recovery (Priority: P1)
- **Target Theme:** `theme_10` (Persistent UPI Payment and Server Errors)
- **Data Justification:** Largest operational bottleneck representing **1,146 reviews (55.8% of feedback)** and 83 churn flags, citing repetitive "Issuer bank unavailable" errors and failed UPI Lite transactions.
- **North Star Metric:** Reduce transaction failure support tickets by **40%** and achieve automatic reversal within 1 hour for **95% of cases**.
- **Engineering Risk & Trade-off:** Multi-bank health telemetry may introduce slight handshake latency (~100ms) during peak evening traffic.
- **Verified Review Citations:** `gp_880f2583...`, `gp_bdc9e4fd...`, `gp_b581f92f...`

---

## 🚀 How to Run Locally

```bash
# 1. Clone & install
git clone https://github.com/shreetejkumard/voc-copilot.git
cd voc-copilot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Add your Gemini API key in .env
cp .env.example .env

# 3. Run the complete pipeline
python3 scripts/collect_playstore.py
python3 scripts/clean.py
python3 scripts/cluster.py
python3 scripts/name_themes.py
python3 scripts/churn.py
python3 scripts/recommend.py
python3 evals/citation_check.py

# 4. View the dashboard locally
python3 -m http.server 8080
# Open http://localhost:8080 in your browser
```

---

## ☁️ Deploying on Vercel (1-Click)

1. Push your repository to GitHub:
   ```bash
   git add .
   git commit -m "feat: complete Day-1 PM Voice of Customer Copilot"
   git push origin main
   ```
2. Log into [vercel.com](https://vercel.com) using your GitHub account.
3. Click **Add New...** → **Project** → select your repo.
4. Click **Deploy** (zero build configuration needed).
5. Vercel delivers a live HTTPS link in 15 seconds to include in your resume and portfolio!
