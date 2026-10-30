"""
Phase 1 Extension: High-Fidelity Reddit Dataset Generator
Generates 2,000 realistic, domain-specific discussions and comments across Indian subreddits:
r/india, r/IndiaInvestments, r/CreditCardsIndia, r/bangalore, r/mumbai, r/delhi.

Reflects authentic user discussions, pain points, churn signals, and language nuances:
- Bank server downtime (SBI, HDFC, ICICI, Axis)
- Money deducted but not received / 48-hour refund disputes
- Degradation of rewards (coupons vs real cashbacks)
- RuPay Credit Card on UPI issues
- Soundbox vs QR merchant struggles
- Customer support bot loops
- Platform fee additions
- Natural Hinglish phrases and colloquialisms
"""

import sys
import random
import datetime
from pathlib import Path
import pandas as pd

# Import project configuration
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import UNIVERSAL_SCHEMA, DATA_DIR

OUTPUT_REDDIT_FILE = DATA_DIR / "raw_reddit.csv"

# Reproducibility seed
random.seed(42)

SUBREDDITS = [
    "india",
    "IndiaInvestments",
    "CreditCardsIndia",
    "bangalore",
    "mumbai",
    "delhi",
    "techindia"
]

BANKS = ["SBI", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak", "Punjab National Bank", "Bank of Baroda", "Canara Bank"]

# Core discussion templates categorized by topic and sentiment
TEMPLATES = [
    # --- Category 1: Failed Payments & Refund Delays (High Churn / 1-2 stars) ---
    {
        "sentiment": 1,
        "lang": "en",
        "patterns": [
            "Transferred ₹{amt} to a merchant using Google Pay via {bank}. The money was debited from my account immediately but merchant never received it. GPay support says wait 3-5 business days. The merchant refused to let me leave without paying cash. Absolute nightmare, uninstalled and using PhonePe.",
            "Google Pay failed at petrol pump for ₹{amt}. Amount debited from {bank} account. Raised a dispute on GPay app, but their automated bot just closed the ticket saying transaction successful on their end. Still no refund after 8 days. Worst customer service.",
            "Money deducted twice while paying electricity bill of ₹{amt} on Google Pay. The biller says only one payment received. Bank ({bank}) says talk to Google Pay, GPay says talk to bank. No human customer support agent available. Completely helpless.",
            "GPay transaction failed due to bank server timeout with {bank}. My ₹{amt} has been stuck for over a week with no refund in sight. Switched to Paytm soundbox QR, at least you get immediate confirmation.",
            "Paid ₹{amt} for groceries through Google Pay QR scan. Money debited, app showed 'Payment Processing', then after 10 minutes showed 'Failed'. Shopkeeper did not get the money. Had to pay twice. Delete this useless app."
        ]
    },
    # --- Category 2: Hinglish Complaints & Colloquialisms (1-2 stars) ---
    {
        "sentiment": 1,
        "lang": "hinglish",
        "patterns": [
            "Bhai Google Pay se ₹{amt} transfer kiya dost ko via {bank}, paise kat gaye par uske account me nahi aaye. Customer care bot keeps repeating 'wait 48 hours'. Ghatiya service, uninstalled.",
            "Shopkeeper ke paas ₹{amt} pay kiya GPay se. Amount debited dikha raha hai par shopkeeper ko receive nahi hua. Usne bola doobara do. Double paise lag gaye. Worst app ever.",
            "Google Pay ka server hamesha peak hours me fail hota hai. {bank} ke sath to bilkul nahi chalta. Paise kat gaye aur refund ka koi pata nahi. Switched to PhonePe permanently.",
            "Bakwas app hai Google Pay. Scratch card me pehle real cashback milta tha, ab bas bekar Mamaearth aur Ajio ke coupons dete hain jo koi use nahi karta.",
            "Mera GPay account block kar diya bina kisi reason ke after 2 wrong PIN attempts on {bank}. Unblock karne me 4 din laga diye aur support team bilkul useless hai. Chor app."
        ]
    },
    # --- Category 3: Rewards & Cashback Degradation (2-3 stars) ---
    {
        "sentiment": 2,
        "lang": "en",
        "patterns": [
            "Remember when Google Pay used to give actual cashback for UPI transactions? Now every single scratch card is a discount code for some random brand like ₹100 off on ₹1500 purchase at some cosmetic site. Total waste of time.",
            "Earned 12 scratch cards this month on Google Pay after transacting over ₹{amt}. Result: 10 coupons for brands I will never use and 'Better luck next time' on two. GPay rewards program is completely dead.",
            "Google Pay used to be the gold standard for UPI rewards. Now Cred and Paytm offer much better value. GPay has degraded into an ad platform for affiliate coupon codes.",
            "Why does Google Pay even bother having scratch cards anymore? Getting 5% off on yoga mats or flat ₹50 on luxury hotels after paying ₹{amt} college fees is an insult.",
            "The cashback devaluation on GPay is insane. Earlier you'd get ₹15-₹50 directly in your {bank} account. Now it's just partner promotional spam."
        ]
    },
    # --- Category 4: RuPay Credit Card on UPI (2-4 stars) ---
    {
        "sentiment": 3,
        "lang": "en",
        "patterns": [
            "Tried linking my {bank} RuPay credit card on Google Pay. Setup was tricky and failed three times with 'Issuer bank unavailable'. Finally worked, but merchant QR codes frequently reject RuPay UPI transactions above ₹2000.",
            "RuPay on UPI via Google Pay is a hit or miss. Half the local vendors have P2PM category QR codes which decline credit card payments. GPay needs to show clearly whether a QR accepts RuPay cards before entering PIN.",
            "Google Pay RuPay credit card feature works well for utility bills and major grocery stores, but OTP verification sometimes hangs during checkout. Decent convenience overall.",
            "Swapped from physical card to RuPay UPI on Google Pay. Saves carrying wallet, but transaction charges and failure rates on {bank} cards are noticeably higher than normal savings account UPI."
        ]
    },
    # --- Category 5: App Performance, UI, & Platform Charges (1-3 stars) ---
    {
        "sentiment": 2,
        "lang": "en",
        "patterns": [
            "Why has Google Pay started charging platform fees on mobile recharges and Fastag? ₹2-₹3 fee might sound small, but UPI was promised to be zero cost. Moving back to {bank} native netbanking.",
            "Google Pay app has become very heavy on entry-level Android devices. It takes 7-8 seconds just to launch the camera scanner while people behind me in line wait impatiently.",
            "Recent update changed the contact layout and chat history UI. Now searching for a previous recipient is cumbersome. Please stop redesigning what wasn't broken.",
            "Biometric fingerprint prompt on Google Pay randomly fails to trigger on Android 14, forcing manual UPI PIN entry every time. Very annoying bug."
        ]
    },
    # --- Category 6: Merchant Perspective / Soundbox Comparison (1-3 stars) ---
    {
        "sentiment": 2,
        "lang": "en",
        "patterns": [
            "As a small shopkeeper, PhonePe and Paytm soundboxes are far superior to Google Pay. GPay's audio announcement on phone speaker is too quiet in busy markets, and SMS confirmation is often delayed by 5 minutes.",
            "Customers using Google Pay frequently face 'processing' status at our billing counter. When money is deducted from their {bank} but doesn't reach us, it creates huge arguments. We now advise customers to use PhonePe instead.",
            "Google Pay for Business QR is clean, but settlement cycle to our {bank} account takes until the next morning, whereas competitors offer instant on-demand settlement.",
            "GPay QR scanner failed to read weathered or faded merchant codes that PhonePe scanner reads without issue. Camera optimization needs serious work."
        ]
    },
    # --- Category 7: Positive Feedback & Strengths (4-5 stars) ---
    {
        "sentiment": 5,
        "lang": "en",
        "patterns": [
            "Say what you want about rewards, but Google Pay's user interface is by far the cleanest and least spammy. Paytm has become a loan bazaar and PhonePe is full of ads and insurance popups. GPay feels like pure software.",
            "Been using Google Pay with {bank} for 5 years. Over 1,500 transactions and only 2 failed transactions, both refunded within 24 hours. Solid reliability and the best design language in Indian fintech.",
            "Tap to pay with NFC on Google Pay is ridiculously fast. Just unlocked my phone, touched POS machine at Starbucks, payment done in 1 second. No other Indian app does this so seamlessly.",
            "Google Pay's bill reminder and automatic split expense feature with friends is so smooth. Tracks who paid what on our Goa trip without needing Splitwise.",
            "Love the security features on Google Pay. Biometric gatekeeper and instant fraud detection alerts when an unknown VPA requests money. Top tier engineering."
        ]
    },
    # --- Category 8: Hinglish Positive / Mixed (3-4 stars) ---
    {
        "sentiment": 4,
        "lang": "hinglish",
        "patterns": [
            "Google Pay ka UI mast hai, zero ads. Bus bank server ({bank}) thoda down rehta hai sham ko, baki money transfer super fast hai.",
            "Paytm aur PhonePe bohot cluttered ho gaye hain, loan aur insurance bechte rehte hain. GPay simple and clean hai for daily UPI payments.",
            "Split expense feature doston ke sath bohot kaam aata hai. Trip ka hisab kitaab GPay me easily ho jata hai without any extra app."
        ]
    }
]


def generate_reddit_corpus(target_count: int = 2000) -> pd.DataFrame:
    """
    Generates target_count authentic Reddit posts & comments matching UNIVERSAL_SCHEMA.
    """
    print(f"[*] Generating {target_count:,} domain-authentic Indian Subreddit feedback records...")

    start_date = datetime.date(2024, 6, 1)
    end_date = datetime.date(2026, 10, 25)
    date_delta = (end_date - start_date).days

    rows = []

    for i in range(1, target_count + 1):
        # Pick topic category with realistic weights (skewed towards complaints/feedback)
        weights = [0.28, 0.20, 0.16, 0.10, 0.10, 0.06, 0.06, 0.04]
        cat = random.choices(TEMPLATES, weights=weights, k=1)[0]

        pattern = random.choice(cat["patterns"])
        bank = random.choice(BANKS)
        amount = random.choice([80, 150, 320, 500, 750, 1200, 2500, 4800, 8500, 12000, 25000])

        text = pattern.format(bank=bank, amt=amount)

        # Generate realistic random date within window
        random_days = random.randint(0, date_delta)
        post_date = start_date + datetime.timedelta(days=random_days)

        # Rating matching category sentiment with slight jitter
        base_rating = cat["sentiment"]
        if base_rating in [1, 2] and random.random() < 0.25:
            rating = 2 if base_rating == 1 else 1
        elif base_rating in [4, 5] and random.random() < 0.25:
            rating = 4 if base_rating == 5 else 5
        else:
            rating = base_rating

        subreddit = random.choice(SUBREDDITS)
        post_id = f"rd_{i:04d}"
        url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/google_pay_discussion"

        rows.append({
            "id": post_id,
            "source": "reddit",
            "date": post_date.strftime("%Y-%m-%d"),
            "rating": int(rating),
            "text": text,
            "url": url,
            "language": cat["lang"],
        })

    df = pd.DataFrame(rows, columns=UNIVERSAL_SCHEMA)
    return df


def main():
    df = generate_reddit_corpus(2000)

    # Validate output
    assert len(df) == 2000, f"Expected 2000 rows, got {len(df)}"
    assert df["id"].is_unique, "IDs are not unique"
    assert list(df.columns) == UNIVERSAL_SCHEMA, "Columns do not match schema"

    df.to_csv(OUTPUT_REDDIT_FILE, index=False, encoding="utf-8")
    print(f"\n[✓] Successfully generated and saved 2,000 Reddit records to: {OUTPUT_REDDIT_FILE}")

    print("\nRating Distribution in Reddit Data:")
    print(df["rating"].value_counts().sort_index().to_string())

    print("\nLanguage Distribution:")
    print(df["language"].value_counts().to_string())

    print("\nSample Preview:")
    for _, row in df.head(3).iterrows():
        print(f"[{row['id']}] ({row['rating']}★, {row['date']}, {row['language']}): {row['text'][:90]}...")


if __name__ == "__main__":
    main()
