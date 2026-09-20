"""
Phase 4 — Customer Profitability
=================================
Estimates customer profit by deducting COGS, discounts, returns,
shipping, service costs, and acquisition costs from gross revenue.
Adapted for Olist dataset with freight values.
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


def compute_profitability(transactions, customers, engagement):
    """Compute customer-level profitability metrics."""

    txn = transactions.copy()
    txn["order_date"] = pd.to_datetime(txn["order_date"])

    # ── Revenue components ─────────────────────────────────────────
    agg_dict = {
        "gross_revenue": ("revenue", "sum"),
        "total_cogs": ("cost_of_goods", "sum"),
        "total_returns": ("is_return", "sum"),
    }

    # Include freight if available
    if "freight_value" in txn.columns:
        agg_dict["total_freight"] = ("freight_value", "sum")

    cust_revenue = txn.groupby("customer_id").agg(**agg_dict).reset_index()

    if "total_freight" not in cust_revenue.columns:
        cust_revenue["total_freight"] = 0

    # Net revenue: gross minus returned items' revenue
    returns_revenue = (
        txn[txn["is_return"] == 1]
        .groupby("customer_id")["revenue"]
        .sum()
        .reset_index()
    )
    returns_revenue.columns = ["customer_id", "returned_revenue"]
    cust_revenue = cust_revenue.merge(returns_revenue, on="customer_id", how="left")
    cust_revenue["returned_revenue"] = cust_revenue["returned_revenue"].fillna(0)
    cust_revenue["net_revenue"] = (
        cust_revenue["gross_revenue"] - cust_revenue["returned_revenue"]
    )

    # ── Discount costs ─────────────────────────────────────────────
    txn["discount_cost"] = txn["revenue"] * txn["discount_pct"] / 100
    discount_costs = (
        txn.groupby("customer_id")["discount_cost"].sum().reset_index()
    )
    discount_costs.columns = ["customer_id", "total_discount_cost"]
    cust_revenue = cust_revenue.merge(discount_costs, on="customer_id", how="left")
    cust_revenue["total_discount_cost"] = cust_revenue["total_discount_cost"].fillna(0)

    # ── Return processing costs ────────────────────────────────────
    cust_revenue["return_cost"] = (
        cust_revenue["total_returns"] * config.RETURN_PROCESSING_COST
    )

    # ── Service costs (from engagement/support tickets) ────────────
    eng = engagement[["customer_id", "support_tickets"]].copy()
    cust_revenue = cust_revenue.merge(eng, on="customer_id", how="left")
    cust_revenue["support_tickets"] = cust_revenue["support_tickets"].fillna(0)
    cust_revenue["service_cost"] = (
        cust_revenue["support_tickets"] * config.SERVICE_COST_PER_TICKET
    )

    # ── Acquisition costs ──────────────────────────────────────────
    cust_info = customers[["customer_id", "acquisition_channel"]].copy()
    acq_cost_map = {ch: v[1] for ch, v in config.ACQUISITION_CHANNELS.items()}
    cust_info["acquisition_cost"] = cust_info["acquisition_channel"].map(acq_cost_map)
    cust_revenue = cust_revenue.merge(
        cust_info[["customer_id", "acquisition_cost"]], on="customer_id", how="left"
    )
    cust_revenue["acquisition_cost"] = cust_revenue["acquisition_cost"].fillna(0)

    # ── Customer Profit ────────────────────────────────────────────
    cust_revenue["customer_profit"] = (
        cust_revenue["net_revenue"]
        - cust_revenue["total_cogs"]
        - cust_revenue["total_discount_cost"]
        - cust_revenue["return_cost"]
        - cust_revenue["service_cost"]
        - cust_revenue["acquisition_cost"]
    )

    # ── Profit Margin ──────────────────────────────────────────────
    cust_revenue["profit_margin"] = np.where(
        cust_revenue["net_revenue"] > 0,
        cust_revenue["customer_profit"] / cust_revenue["net_revenue"],
        0,
    )

    # ── Profit Quartile ────────────────────────────────────────────
    cust_revenue["profit_quartile"] = pd.qcut(
        cust_revenue["customer_profit"].rank(method="first"),
        q=4,
        labels=[1, 2, 3, 4],
    ).astype(int)

    # ── Value tier (for intervention costs) ────────────────────────
    profit_66 = cust_revenue["customer_profit"].quantile(0.66)
    profit_33 = cust_revenue["customer_profit"].quantile(0.33)

    cust_revenue["value_tier"] = np.where(
        cust_revenue["customer_profit"] >= profit_66,
        "High Value",
        np.where(
            cust_revenue["customer_profit"] >= profit_33,
            "Medium Value",
            "Low Value",
        ),
    )

    return cust_revenue


def plot_profitability(profit_df):
    """Generate profitability visualizations."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Profit distribution
    axes[0, 0].hist(
        profit_df["customer_profit"], bins=50, color="#2ecc71",
        edgecolor="white", alpha=0.8,
    )
    axes[0, 0].axvline(0, color="red", linestyle="--", linewidth=1.5, label="Break-even")
    axes[0, 0].set_title("Customer Profit Distribution")
    axes[0, 0].set_xlabel(f"Profit ({config.CURRENCY_SYMBOL})")
    axes[0, 0].set_ylabel("Count")
    axes[0, 0].legend()

    # Revenue vs Profit scatter (subsample for performance)
    sample_size = min(5000, len(profit_df))
    sample = profit_df.sample(sample_size, random_state=config.RANDOM_SEED)
    axes[0, 1].scatter(
        sample["gross_revenue"], sample["customer_profit"],
        alpha=0.3, s=8, c=sample["profit_margin"],
        cmap="RdYlGn", vmin=-0.5, vmax=0.5,
    )
    axes[0, 1].set_title("Revenue vs Profit")
    axes[0, 1].set_xlabel(f"Gross Revenue ({config.CURRENCY_SYMBOL})")
    axes[0, 1].set_ylabel(f"Customer Profit ({config.CURRENCY_SYMBOL})")
    axes[0, 1].axhline(0, color="red", linestyle="--", alpha=0.5)

    # Profit margin distribution
    axes[1, 0].hist(
        profit_df["profit_margin"].clip(-1, 1), bins=50,
        color="#3498db", edgecolor="white", alpha=0.8,
    )
    axes[1, 0].set_title("Profit Margin Distribution")
    axes[1, 0].set_xlabel("Profit Margin")
    axes[1, 0].set_ylabel("Count")
    axes[1, 0].axvline(0, color="red", linestyle="--", linewidth=1.5)

    # Cost breakdown (aggregated)
    cost_cols = {
        "COGS": profit_df["total_cogs"].sum(),
        "Discounts": profit_df["total_discount_cost"].sum(),
        "Returns": profit_df["return_cost"].sum(),
        "Service": profit_df["service_cost"].sum(),
        "Acquisition": profit_df["acquisition_cost"].sum(),
    }
    if "total_freight" in profit_df.columns:
        cost_cols["Freight"] = profit_df["total_freight"].sum()

    colors_bar = ["#e74c3c", "#e67e22", "#f39c12", "#9b59b6", "#1abc9c", "#3498db"]
    axes[1, 1].bar(
        list(cost_cols.keys()),
        list(cost_cols.values()),
        color=colors_bar[: len(cost_cols)],
    )
    axes[1, 1].set_title("Aggregate Cost Breakdown")
    axes[1, 1].set_ylabel(f"Total Cost ({config.CURRENCY_SYMBOL})")
    axes[1, 1].tick_params(axis="x", rotation=15)

    plt.tight_layout()
    plt.savefig(
        os.path.join(config.OUTPUT_FIGURES, "profitability_analysis.png"),
        dpi=150, bbox_inches="tight",
    )
    plt.close()


def run(segmented_customers=None, transactions=None, customers=None, engagement=None):
    """Run profitability analysis."""
    print("\n" + "=" * 60)
    print("PHASE 4: Customer Profitability")
    print("=" * 60)

    if transactions is None:
        transactions = pd.read_csv(os.path.join(config.DATA_RAW, "transactions.csv"))
    if customers is None:
        customers = pd.read_csv(os.path.join(config.DATA_RAW, "customers.csv"))
    if engagement is None:
        engagement = pd.read_csv(os.path.join(config.DATA_RAW, "engagement.csv"))
    if segmented_customers is None:
        segmented_customers = pd.read_csv(
            os.path.join(config.DATA_PROCESSED, "customer_segmented.csv")
        )

    print("  Computing customer profitability...")
    profit_df = compute_profitability(transactions, customers, engagement)

    # Merge profit into segmented data
    profit_cols = [
        "customer_id", "gross_revenue", "net_revenue", "total_cogs",
        "total_discount_cost", "return_cost", "service_cost",
        "acquisition_cost", "customer_profit", "profit_margin",
        "profit_quartile", "value_tier", "total_freight",
    ]
    available_cols = [c for c in profit_cols if c in profit_df.columns]
    df = segmented_customers.merge(profit_df[available_cols], on="customer_id", how="left")

    # Summary stats
    print(f"\n  Profitability Summary:")
    print(f"    Total Revenue:     {config.CURRENCY_SYMBOL} {df['gross_revenue'].sum():>12,.0f}")
    print(f"    Total Profit:      {config.CURRENCY_SYMBOL} {df['customer_profit'].sum():>12,.0f}")
    print(f"    Avg Profit Margin: {df['profit_margin'].mean():>11.1%}")
    print(
        f"    Unprofitable:      {(df['customer_profit'] < 0).sum():>6,} customers "
        f"({(df['customer_profit'] < 0).mean():.1%})"
    )

    # Insights: high revenue but low profit
    high_rev_low_profit = df[
        (df["gross_revenue"] > df["gross_revenue"].quantile(0.75))
        & (df["profit_margin"] < df["profit_margin"].quantile(0.25))
    ]
    print(f"\n  ⚠ High revenue, low margin: {len(high_rev_low_profit):,} customers")

    # Visualize
    print("  Generating profitability charts...")
    plot_profitability(profit_df)

    # Profit by segment
    seg_profit = df.groupby("rfm_segment").agg(
        avg_profit=("customer_profit", "mean"),
        avg_margin=("profit_margin", "mean"),
        count=("customer_id", "count"),
    ).reset_index()
    print(f"\n  Profit by RFM Segment:")
    print(seg_profit.to_string(index=False))

    # Save
    out_path = os.path.join(config.DATA_PROCESSED, "customer_profitable.csv")
    df.to_csv(out_path, index=False)
    print(f"\n  ✓ Profitability data → {out_path}")

    return df


if __name__ == "__main__":
    run()
