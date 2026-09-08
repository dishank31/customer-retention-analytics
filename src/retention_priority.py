"""
Phase 7 — Retention Prioritization
====================================
The centerpiece: combines customer value, churn risk, and intervention
economics into a transparent Retention Priority Score with sensitivity
analysis and a decision matrix.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def assign_intervention_costs(df):
    """Assign intervention costs based on value tier."""
    cost_map = config.INTERVENTION_COSTS
    df["intervention_cost"] = df["value_tier"].map(cost_map).fillna(
        cost_map["Low Value"]
    )
    return df


def assign_success_probability(df):
    """Assign retention success probability based on segment."""
    prob_map = config.RETENTION_SUCCESS_PROB
    df["success_prob"] = df["rfm_segment"].map(prob_map).fillna(0.35)
    return df


def compute_retention_economics(df):
    """Compute expected retention value, net benefit, and priority score."""

    # ── Expected Retention Value ───────────────────────────────────
    # What's the expected value of successfully retaining this customer?
    df["expected_retention_value"] = (
        df["customer_profit"] * df["churn_prob"] * df["success_prob"]
    )

    # ── Expected Net Benefit ───────────────────────────────────────
    df["expected_net_benefit"] = (
        df["expected_retention_value"] - df["intervention_cost"]
    )

    # ── Retention Priority Score (0-100) ───────────────────────────
    # Normalize components to 0-1
    def min_max_normalize(series):
        s_min, s_max = series.min(), series.max()
        if s_max == s_min:
            return pd.Series(0.5, index=series.index)
        return (series - s_min) / (s_max - s_min)

    norm_profit = min_max_normalize(df["customer_profit"])
    norm_churn = min_max_normalize(df["churn_prob"])
    norm_benefit = min_max_normalize(df["expected_net_benefit"])

    weights = config.PRIORITY_WEIGHTS
    df["retention_priority_score"] = (
        weights["value"] * norm_profit +
        weights["churn_risk"] * norm_churn +
        weights["net_benefit"] * norm_benefit
    ) * 100

    df["retention_priority_score"] = df["retention_priority_score"].round(1)

    # ── Priority Rank ──────────────────────────────────────────────
    df["priority_rank"] = df["retention_priority_score"].rank(
        ascending=False, method="min"
    ).astype(int)

    # ── Recommended Action ─────────────────────────────────────────
    df["recommended_action"] = df.apply(_recommend_action, axis=1)

    return df


def _recommend_action(row):
    """Determine recommended action based on value + risk combination."""
    value_tier = row["value_tier"]
    churn_prob = row["churn_prob"]
    net_benefit = row["expected_net_benefit"]

    if net_benefit <= 0:
        if value_tier == "Low Value":
            return "Let Go — Negative ROI"
        else:
            return "Monitor — Marginal ROI"

    if value_tier == "High Value" and churn_prob >= 0.6:
        return "Immediate Retention — Personal Outreach"
    elif value_tier == "High Value" and churn_prob >= 0.3:
        return "Proactive Retention — Premium Offer"
    elif value_tier == "High Value":
        return "Maintain — Loyalty Rewards"
    elif value_tier == "Medium Value" and churn_prob >= 0.5:
        return "Targeted Campaign — Email + Discount"
    elif value_tier == "Medium Value":
        return "Nurture — Cross-sell Campaign"
    elif value_tier == "Low Value" and churn_prob >= 0.5:
        return "Low-Cost — Automated Email Sequence"
    else:
        return "Standard — No Specific Action"


def sensitivity_analysis(df):
    """Test different weight configurations and compare top-20 lists."""
    print("\n  Sensitivity Analysis:")

    weight_configs = {
        "Default (40/35/25)": {"value": 0.40, "churn_risk": 0.35, "net_benefit": 0.25},
        "Value-Heavy (50/25/25)": {"value": 0.50, "churn_risk": 0.25, "net_benefit": 0.25},
        "Risk-Heavy (30/40/30)": {"value": 0.30, "churn_risk": 0.40, "net_benefit": 0.30},
        "Balanced (33/33/33)": {"value": 0.33, "churn_risk": 0.34, "net_benefit": 0.33},
    }

    def min_max_normalize(series):
        s_min, s_max = series.min(), series.max()
        if s_max == s_min:
            return pd.Series(0.5, index=series.index)
        return (series - s_min) / (s_max - s_min)

    norm_profit = min_max_normalize(df["customer_profit"])
    norm_churn = min_max_normalize(df["churn_prob"])
    norm_benefit = min_max_normalize(df["expected_net_benefit"])

    top_20_sets = {}

    for config_name, weights in weight_configs.items():
        score = (
            weights["value"] * norm_profit +
            weights["churn_risk"] * norm_churn +
            weights["net_benefit"] * norm_benefit
        ) * 100

        top_20 = df.loc[score.nlargest(20).index, "customer_id"].tolist()
        top_20_sets[config_name] = set(top_20)

        avg_score = score.mean()
        print(f"    {config_name}: avg score = {avg_score:.1f}")

    # Overlap analysis
    default_top = top_20_sets["Default (40/35/25)"]
    print(f"\n  Top-20 overlap with default weights:")
    for name, top_set in top_20_sets.items():
        if name == "Default (40/35/25)":
            continue
        overlap = len(default_top & top_set)
        print(f"    {name}: {overlap}/20 overlap ({overlap/20:.0%})")

    return weight_configs


def create_decision_matrix(df):
    """Create the segment × risk decision matrix summary."""

    # Create risk tiers
    df["risk_tier"] = pd.cut(
        df["churn_prob"],
        bins=[0, 0.3, 0.6, 1.0],
        labels=["Low Risk", "Medium Risk", "High Risk"],
        include_lowest=True
    )

    matrix = df.groupby(["value_tier", "risk_tier"]).agg(
        customer_count=("customer_id", "count"),
        avg_profit=("customer_profit", "mean"),
        avg_churn_prob=("churn_prob", "mean"),
        total_profit_at_risk=("expected_retention_value", "sum"),
        avg_priority=("retention_priority_score", "mean"),
    ).reset_index()

    matrix["avg_profit"] = matrix["avg_profit"].round(0)
    matrix["avg_churn_prob"] = matrix["avg_churn_prob"].round(2)
    matrix["total_profit_at_risk"] = matrix["total_profit_at_risk"].round(0)
    matrix["avg_priority"] = matrix["avg_priority"].round(1)

    print(f"\n  Decision Matrix:")
    print(matrix.to_string(index=False))

    return matrix


def plot_retention_analysis(df):
    """Generate retention prioritization visualizations."""
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))

    # 1. Priority score distribution
    axes[0, 0].hist(df["retention_priority_score"], bins=50, color="#e74c3c",
                     edgecolor="white", alpha=0.8)
    axes[0, 0].set_title("Retention Priority Score Distribution")
    axes[0, 0].set_xlabel("Priority Score")
    axes[0, 0].set_ylabel("Count")

    # 2. Profit vs Churn (bubble = priority)
    scatter = axes[0, 1].scatter(
        df["churn_prob"], df["customer_profit"],
        s=df["retention_priority_score"] * 0.5,
        c=df["retention_priority_score"],
        cmap="RdYlGn_r", alpha=0.5, edgecolors="none"
    )
    axes[0, 1].set_title("Customer Profit vs Churn Probability")
    axes[0, 1].set_xlabel("Churn Probability")
    axes[0, 1].set_ylabel(f"Customer Profit ({config.CURRENCY_SYMBOL})")
    plt.colorbar(scatter, ax=axes[0, 1], label="Priority Score")

    # 3. Expected net benefit by segment
    seg_benefit = df.groupby("rfm_segment")["expected_net_benefit"].mean().sort_values()
    colors = ["#e74c3c" if v < 0 else "#2ecc71" for v in seg_benefit.values]
    axes[1, 0].barh(seg_benefit.index, seg_benefit.values, color=colors)
    axes[1, 0].set_title("Avg Expected Net Benefit by Segment")
    axes[1, 0].set_xlabel(f"Expected Net Benefit ({config.CURRENCY_SYMBOL})")
    axes[1, 0].axvline(0, color="black", linestyle="--", alpha=0.5)

    # 4. Recommended action distribution
    action_counts = df["recommended_action"].value_counts()
    action_counts.plot(kind="barh", ax=axes[1, 1],
                        color=sns.color_palette("viridis", len(action_counts)))
    axes[1, 1].set_title("Recommended Actions Distribution")
    axes[1, 1].set_xlabel("Customer Count")

    plt.tight_layout()
    plt.savefig(os.path.join(config.OUTPUT_FIGURES, "retention_prioritization.png"),
                dpi=150, bbox_inches="tight")
    plt.close()


def generate_top_targets_report(df, top_n=20):
    """Generate a report of top retention targets."""
    top = df.nsmallest(top_n, "priority_rank").copy()

    report_cols = [
        "priority_rank", "customer_id", "customer_profit", "churn_prob",
        "expected_retention_value", "intervention_cost", "expected_net_benefit",
        "retention_priority_score", "rfm_segment", "value_tier", "recommended_action"
    ]

    report = top[report_cols].copy()
    report["customer_profit"] = report["customer_profit"].round(0)
    report["expected_retention_value"] = report["expected_retention_value"].round(0)
    report["expected_net_benefit"] = report["expected_net_benefit"].round(0)
    report["churn_prob"] = report["churn_prob"].round(2)

    print(f"\n  Top {top_n} Retention Targets:")
    print(report.to_string(index=False))

    return report


def run(customer_data=None):
    """Run retention prioritization pipeline."""
    print("\n" + "="*60)
    print("PHASE 7: Retention Prioritization")
    print("="*60)

    if customer_data is None:
        customer_data = pd.read_csv(
            os.path.join(config.DATA_PROCESSED, "customer_churn.csv")
        )

    df = customer_data.copy()

    # 1. Assign intervention costs
    print("\n  Assigning intervention costs...")
    df = assign_intervention_costs(df)

    # 2. Assign success probabilities
    print("  Assigning retention success probabilities...")
    df = assign_success_probability(df)

    # 3. Compute retention economics
    print("  Computing retention economics...")
    df = compute_retention_economics(df)

    # 4. Summary statistics
    total_erv = df["expected_retention_value"].sum()
    total_cost = df[df["expected_net_benefit"] > 0]["intervention_cost"].sum()
    total_benefit = df[df["expected_net_benefit"] > 0]["expected_net_benefit"].sum()
    positive_roi = (df["expected_net_benefit"] > 0).sum()

    print(f"\n  Retention Economics Summary:")
    print(f"    Total Expected Retention Value: {config.CURRENCY_SYMBOL}{total_erv:>12,.0f}")
    print(f"    Total Intervention Budget:      {config.CURRENCY_SYMBOL}{total_cost:>12,.0f}")
    print(f"    Total Expected Net Benefit:     {config.CURRENCY_SYMBOL}{total_benefit:>12,.0f}")
    print(f"    Positive ROI customers:         {positive_roi:>6} ({positive_roi/len(df):.1%})")

    # 5. Top targets
    top_report = generate_top_targets_report(df)

    # 6. Decision matrix
    decision_matrix = create_decision_matrix(df)

    # 7. Sensitivity analysis
    sensitivity_analysis(df)

    # 8. Visualizations
    print("\n  Generating retention charts...")
    plot_retention_analysis(df)

    # 9. Save
    out_path = os.path.join(config.DATA_PROCESSED, "customer_retention_final.csv")
    df.to_csv(out_path, index=False)
    print(f"\n  ✓ Retention prioritization → {out_path}")

    # Save decision matrix
    dm_path = os.path.join(config.DATA_PROCESSED, "decision_matrix.csv")
    decision_matrix.to_csv(dm_path, index=False)

    return df


if __name__ == "__main__":
    run()
