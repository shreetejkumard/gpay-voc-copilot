"""
Phase 3: Unsupervised Theme Clustering
Clusters customer reviews into organic, data-driven themes:
1. Generates dense semantic embeddings (using Gemini text-embedding-004, with caching)
2. Performs density-based clustering with HDBSCAN (with automatic fallback to K-Means)
3. Preserves a dedicated 'noise/unclustered' bucket (-1) without forcing edge cases into themes
4. Saves cluster assignments to data/clustered_reviews.csv
5. Prints 10 random sample reviews per cluster for human sanity checking
"""

import sys
import time
import os
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize
from sklearn.cluster import HDBSCAN, KMeans

# Import project configuration
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import (
    DATA_DIR,
    UNIVERSAL_SCHEMA,
    GEMINI_API_KEY,
    GEMINI_EMBEDDING_MODEL,
    MIN_CLUSTER_SIZE,
)

INPUT_CLEAN_FILE = DATA_DIR / "clean_reviews.csv"
OUTPUT_CLUSTERED_FILE = DATA_DIR / "clustered_reviews.csv"
EMBEDDINGS_CACHE_FILE = DATA_DIR / "embeddings.npy"


def get_embeddings(texts: list[str]) -> np.ndarray:
    """
    Computes or loads semantic embeddings for the review texts.
    Caches results to disk so re-runs are instant and free.
    """
    # 1. Check if cached embeddings exist
    if EMBEDDINGS_CACHE_FILE.exists():
        cached = np.load(EMBEDDINGS_CACHE_FILE)
        if len(cached) == len(texts):
            print(f"[✓] Loaded {len(cached):,} cached embeddings from: {EMBEDDINGS_CACHE_FILE.name}")
            return cached
        else:
            print(f"[!] Cached embeddings count ({len(cached)}) differs from dataset ({len(texts)}). Recomputing...")

    # 2. Check for valid Gemini API Key
    has_gemini_key = bool(GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here")

    if has_gemini_key:
        print(f"[*] Connecting to Google Gemini API using model: '{GEMINI_EMBEDDING_MODEL}'")
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)

        batch_size = 50
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        print(f"[*] Embedding {len(texts):,} reviews across {total_batches} batches...")

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            try:
                response = client.models.embed_content(
                    model=GEMINI_EMBEDDING_MODEL,
                    contents=batch,
                )
                batch_vectors = [emb.values for emb in response.embeddings]
                all_embeddings.extend(batch_vectors)
                print(f"    -> Batch {batch_num}/{total_batches} completed ({len(all_embeddings)}/{len(texts)})")
                time.sleep(0.5)  # Polite pacing
            except Exception as e:
                print(f"    [!] Error during Gemini embedding batch {batch_num}: {e}")
                raise e

        vectors = np.array(all_embeddings, dtype=np.float32)

    else:
        # Graceful local fallback if API key is not yet pasted in .env
        print("\n" + "!" * 65)
        print("[!] NOTICE: GEMINI_API_KEY is not configured in .env.")
        print("[!] To use Gemini text-embedding-004, paste your key in .env.")
        print("[*] Generating local high-dimensional semantic representations")
        print("    (TF-IDF + TruncatedSVD) so you can preview the clustering pipeline now.")
        print("!" * 65 + "\n")

        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD

        tfidf = TfidfVectorizer(max_features=2500, stop_words="english", ngram_range=(1, 2))
        tfidf_mat = tfidf.fit_transform(texts)
        n_components = min(128, tfidf_mat.shape[1] - 1)
        svd = TruncatedSVD(n_components=n_components, random_state=42)
        vectors = svd.fit_transform(tfidf_mat).astype(np.float32)

    # Save to disk cache
    np.save(EMBEDDINGS_CACHE_FILE, vectors)
    print(f"[✓] Saved embeddings matrix ({vectors.shape[0]} reviews, {vectors.shape[1]} dimensions) to: {EMBEDDINGS_CACHE_FILE.name}")
    return vectors


def cluster_reviews(df: pd.DataFrame, embeddings: np.ndarray) -> pd.DataFrame:
    """
    Applies HDBSCAN density clustering on L2-normalized embeddings (Cosine metric).
    Falls back to K-Means if HDBSCAN labels an excessive portion of data as noise.
    """
    print(f"\n[*] Normalizing {len(embeddings)} vectors for Cosine distance clustering...")
    norm_embeddings = normalize(embeddings, norm="l2")

    # Primary: HDBSCAN density clustering
    print(f"[*] Running HDBSCAN (min_cluster_size={MIN_CLUSTER_SIZE})...")
    hdb = HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=5,
        metric="euclidean",  # On L2-normalized vectors, Euclidean ordering equals Cosine ordering
        cluster_selection_method="eom"
    )
    labels = hdb.fit_predict(norm_embeddings)

    unique_clusters = set(labels)
    cluster_count = len(unique_clusters - {-1})
    noise_count = int(np.sum(labels == -1))
    noise_pct = (noise_count / len(labels)) * 100

    print(f"[*] HDBSCAN result: Discovered {cluster_count} organic themes.")
    print(f"[*] Noise reviews (-1): {noise_count:,} ({noise_pct:.1f}% of dataset)")

    # Fallback to K-Means if HDBSCAN yielded too few clusters or over 75% noise
    if cluster_count < 3 or noise_pct > 75.0:
        print("\n[!] HDBSCAN yielded insufficient clusters or high noise.")
        print("[*] Engaging fallback algorithm: K-Means clustering (k=6)...")
        kmeans = KMeans(n_clusters=6, random_state=42, n_init="auto")
        labels = kmeans.fit_predict(norm_embeddings)
        algorithm_used = "KMeans (fallback)"
        cluster_count = 6
        noise_count = 0
    else:
        algorithm_used = "HDBSCAN (primary)"

    df = df.copy()
    df["cluster_id"] = labels
    df["cluster_name"] = df["cluster_id"].apply(lambda c: "noise_unclustered" if c == -1 else f"theme_{c:02d}")

    print(f"\n[✓] Clustering completed using: {algorithm_used}")
    print("\nCluster Size Breakdown:")
    breakdown = df["cluster_name"].value_counts().to_string()
    print(breakdown)

    return df


def print_cluster_samples(df: pd.DataFrame, n_samples: int = 10):
    """
    Prints random sample reviews per cluster for human sanity checking.
    """
    print("\n" + "=" * 65)
    print("HUMAN SANITY-CHECK: Sample Reviews per Discovered Theme")
    print("=" * 65)

    unique_clusters = sorted(df["cluster_id"].unique())

    for cid in unique_clusters:
        c_name = "Noise / Unclustered (-1)" if cid == -1 else f"Theme #{cid}"
        subset = df[df["cluster_id"] == cid]
        print(f"\n>>> {c_name} (Total Reviews: {len(subset):,})")

        sample_n = min(n_samples, len(subset))
        samples = subset.sample(n=sample_n, random_state=42)

        for idx, (_, r) in enumerate(samples.iterrows(), 1):
            short_text = r["text"].replace("\n", " ").strip()
            if len(short_text) > 110:
                short_text = short_text[:107] + "..."
            print(f"  {idx:2d}. [{r['id']}] ({r['rating']}★, {r['source']}): \"{short_text}\"")


def main():
    print("=" * 60)
    print("Phase 3: Theme Clustering Pipeline")
    print("=" * 60)

    if not INPUT_CLEAN_FILE.exists():
        print(f"[X] Clean reviews file not found at: {INPUT_CLEAN_FILE}")
        sys.exit(1)

    df = pd.read_csv(INPUT_CLEAN_FILE, encoding="utf-8")
    print(f"[*] Loaded clean dataset: {len(df):,} reviews")

    texts = df["text"].tolist()
    embeddings = get_embeddings(texts)

    clustered_df = cluster_reviews(df, embeddings)

    # Save to CSV
    clustered_df.to_csv(OUTPUT_CLUSTERED_FILE, index=False, encoding="utf-8")
    print(f"\n[✓] Saved clustered reviews to: {OUTPUT_CLUSTERED_FILE}")

    # Print 10 random sample reviews per cluster for human inspection
    print_cluster_samples(clustered_df, n_samples=10)


if __name__ == "__main__":
    main()
