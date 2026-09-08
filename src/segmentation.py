"""
Phase 4 — Customer Segmentation
================================
Dual approach: Rule-based RFM segmentation (Approach A)
and K-Means clustering (Approach B), with comparison analysis.
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.decomposition import PCA
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


# ─── Approach A: Rule-Based RFM ─────────────────────────────────────────

def rfm_score(customer_features):
    """Assign RFM scores (1-5) using quintiles and map to segments."""
    df = customer_features.copy()

    # Recency: lower is better → invert scoring
    df["r_score"] = pd.qcut(df["recency_days"], q=5, labels=[5, 4, 3, 2, 1]).astype(int)

    # Frequency: higher is better
    df["f_score"] = pd.qcut(df["frequency"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)

    # Monetary: higher is better
    df["m_score"] = pd.qcut(df["monetary"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)

    # Combined RFM score
    df["rfm_score"] = df["r_score"] + df["f_score"] + df["m_score"]

    # Segment mapping
    df["rfm_segment"] = df.apply(_map_segment, axis=1)

    return df


def _map_segment(row):
    """Map RFM scores to named business segments."""
    r, f, m = row["r_score"], row["f_score"], row["m_score"]

    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    elif r >= 3 and f >= 3 and m >= 3:
        return "Loyal Customers"
    elif r >= 4 and f <= 3 and m <= 3:
        return "Potential Loyalists"
    elif r <= 2 and f >= 4 and m >= 4:
        return "High Value At Risk"
    elif r <= 2 and f >= 3 and m >= 3:
        return "At Risk"
    elif r >= 2 and r <= 3 and f <= 3 and m <= 3:
        return "Needs Attention"
    elif r <= 1 and f <= 2 and m <= 2:
        return "Dormant"
    else:
        return "Needs Attention"


# ─── Approach B: K-Means Clustering ─────────────────────────────────────

def kmeans_segmentation(customer_features):
    """Perform K-Means clustering with elbow/silhouette analysis."""
    df = customer_features.copy()

    # Features for clustering
    cluster_features = ["recency_days", "frequency", "monetary",
                        "engagement_score", "avg_order_value"]
    X = df[cluster_features].copy()
    X = X.fillna(0)

    # Standardize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Elbow method + silhouette scores
    inertias = []
    silhouettes = []
    k_range = list(config.K_MEANS_RANGE)

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=config.RANDOM_SEED, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(X_scaled, labels))

    # Plot elbow and silhouette
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(k_range, inertias, "bo-", linewidth=2)
    ax1.set_xlabel("Number of Clusters (k)")
    ax1.set_ylabel("Inertia")
    ax1.set_title("Elbow Method")
    ax1.grid(True, alpha=0.3)

    ax2.plot(k_range, silhouettes, "rs-", linewidth=2)
    ax2.set_xlabel("Number of Clusters (k)")
    ax2.set_ylabel("Silhouette Score")
    ax2.set_title("Silhouette Analysis")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(config.OUTPUT_FIGURES, "clustering_evaluation.png"),
                dpi=150, bbox_inches="tight")
    plt.close()

    # Select optimal k (best silhouette)
    optimal_k = k_range[np.argmax(silhouettes)]
    print(f"  Optimal k = {optimal_k} (silhouette = {max(silhouettes):.3f})")

    # Final clustering
    km_final = KMeans(n_clusters=optimal_k, random_state=config.RANDOM_SEED, n_init=10)
    df["cluster"] = km_final.fit_predict(X_scaled)

    # Profile clusters and assign business-friendly names
    cluster_profiles = df.groupby("cluster")[cluster_features].mean()
    print("\n  Cluster profiles:")
    print(cluster_profiles.round(1).to_string(index=True))

    # Assign names based on profiles
    df["kmeans_segment"] = df["cluster"].map(
        _name_clusters(cluster_profiles)
    )

    # PCA visualization
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    df["pca_1"] = X_pca[:, 0]
    df["pca_2"] = X_pca[:, 1]

    fig, ax = plt.subplots(figsize=(10, 7))
    scatter = ax.scatter(df["pca_1"], df["pca_2"],
                         c=df["cluster"], cmap="viridis",
                         alpha=0.5, s=10)
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)")
    ax.set_title("Customer Clusters (PCA Projection)")
    plt.colorbar(scatter, label="Cluster")
    plt.tight_layout()
    plt.savefig(os.path.join(config.OUTPUT_FIGURES, "cluster_pca.png"),
                dpi=150, bbox_inches="tight")
    plt.close()

    return df, optimal_k


def _name_clusters(profiles):
    """Assign business-friendly names to clusters based on their profiles."""
    names = {}
    n_clusters = len(profiles)

    # Rank clusters by monetary value
    monetary_ranks = profiles["monetary"].rank(ascending=False)
    recency_ranks = profiles["recency_days"].rank(ascending=True)  # lower recency = better

    for cluster_id in profiles.index:
        m_rank = monetary_ranks[cluster_id]
        r_rank = recency_ranks[cluster_id]

        if m_rank <= n_clusters * 0.25 and r_rank <= n_clusters * 0.5:
            names[cluster_id] = "High Value Active"
        elif m_rank <= n_clusters * 0.25 and r_rank > n_clusters * 0.5:
            names[cluster_id] = "High Value At Risk"
        elif m_rank <= n_clusters * 0.5 and r_rank <= n_clusters * 0.5:
            names[cluster_id] = "Medium Value Active"
        elif m_rank <= n_clusters * 0.5 and r_rank > n_clusters * 0.5:
            names[cluster_id] = "Medium Value Declining"
        elif r_rank <= n_clusters * 0.5:
            names[cluster_id] = "Low Value Active"
        else:
            names[cluster_id] = "Low Value Dormant"

    # De-duplicate names
    seen = {}
    for k, v in names.items():
        if v in seen.values():
            names[k] = v + f" ({k})"
        seen[k] = v

    return names


# ─── Comparison Analysis ────────────────────────────────────────────────

def compare_approaches(df):
    """Compare RFM rule-based segments with K-Means clusters."""
    print("\n  Comparing RFM vs K-Means segmentation...")

    # Cross-tabulation
    cross_tab = pd.crosstab(df["rfm_segment"], df["kmeans_segment"],
                            margins=True, margins_name="Total")

    # Adjusted Rand Index
    ari = adjusted_rand_score(df["rfm_segment"], df["kmeans_segment"])
    print(f"  Adjusted Rand Index: {ari:.3f}")

    # Segment size comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    rfm_counts = df["rfm_segment"].value_counts()
    rfm_counts.plot(kind="barh", ax=ax1, color=sns.color_palette("viridis", len(rfm_counts)))
    ax1.set_title("RFM Segments (Rule-Based)")
    ax1.set_xlabel("Customer Count")

    km_counts = df["kmeans_segment"].value_counts()
    km_counts.plot(kind="barh", ax=ax2, color=sns.color_palette("magma", len(km_counts)))
    ax2.set_title("K-Means Segments")
    ax2.set_xlabel("Customer Count")

    plt.tight_layout()
    plt.savefig(os.path.join(config.OUTPUT_FIGURES, "segmentation_comparison.png"),
                dpi=150, bbox_inches="tight")
    plt.close()

    return cross_tab, ari


# ─── Segment Profile Visualization ──────────────────────────────────────

def plot_segment_profiles(df):
    """Create radar charts and summary plots for segments."""

    # Revenue by RFM segment
    seg_summary = df.groupby("rfm_segment").agg(
        count=("customer_id", "count"),
        avg_recency=("recency_days", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        avg_engagement=("engagement_score", "mean"),
        avg_aov=("avg_order_value", "mean"),
    ).reset_index()

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Customer count by segment
    seg_order = seg_summary.sort_values("count", ascending=True)
    colors = sns.color_palette("viridis", len(seg_order))
    axes[0, 0].barh(seg_order["rfm_segment"], seg_order["count"], color=colors)
    axes[0, 0].set_title("Customer Count by Segment")
    axes[0, 0].set_xlabel("Count")

    # Revenue by segment
    seg_order = seg_summary.sort_values("avg_monetary", ascending=True)
    axes[0, 1].barh(seg_order["rfm_segment"], seg_order["avg_monetary"], color=colors)
    axes[0, 1].set_title("Average Revenue by Segment")
    axes[0, 1].set_xlabel(f"Revenue ({config.CURRENCY_SYMBOL})")

    # Recency by segment
    seg_order = seg_summary.sort_values("avg_recency", ascending=False)
    axes[1, 0].barh(seg_order["rfm_segment"], seg_order["avg_recency"], color=colors)
    axes[1, 0].set_title("Average Recency by Segment (days)")
    axes[1, 0].set_xlabel("Days")

    # Engagement by segment
    seg_order = seg_summary.sort_values("avg_engagement", ascending=True)
    axes[1, 1].barh(seg_order["rfm_segment"], seg_order["avg_engagement"], color=colors)
    axes[1, 1].set_title("Average Engagement Score by Segment")
    axes[1, 1].set_xlabel("Engagement Score")

    plt.tight_layout()
    plt.savefig(os.path.join(config.OUTPUT_FIGURES, "segment_profiles.png"),
                dpi=150, bbox_inches="tight")
    plt.close()

    return seg_summary


def run(customer_features=None):
    """Run full segmentation pipeline."""
    print("\n" + "="*60)
    print("PHASE 4: Customer Segmentation")
    print("="*60)

    if customer_features is None:
        customer_features = pd.read_csv(
            os.path.join(config.DATA_PROCESSED, "customer_features.csv")
        )

    # Approach A: Rule-based RFM
    print("\n  Approach A: Rule-Based RFM Segmentation")
    df = rfm_score(customer_features)
    print(f"  RFM segment distribution:")
    print(df["rfm_segment"].value_counts().to_string())

    # Approach B: K-Means
    print("\n  Approach B: K-Means Clustering")
    df, optimal_k = kmeans_segmentation(df)

    # Comparison
    cross_tab, ari = compare_approaches(df)

    # Profiles
    seg_summary = plot_segment_profiles(df)

    # Save
    out_path = os.path.join(config.DATA_PROCESSED, "customer_segmented.csv")
    # Drop PCA columns for cleaner output
    save_cols = [c for c in df.columns if c not in ["pca_1", "pca_2"]]
    df[save_cols].to_csv(out_path, index=False)
    print(f"\n  ✓ Segmented customers → {out_path}")

    return df


if __name__ == "__main__":
    run()
