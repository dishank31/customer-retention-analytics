"""
Phase 7 — Power BI Export
==========================
Produces clean, Power BI-optimized CSV exports including:
- Customer master table
- Transaction summary (monthly aggregates)
- Retention decisions (top targets)
- Segment summary
- Date dimension table
- Geographic summary
- Product category performance
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def export_customer_master(df):
    """Export the primary customer master table for Power BI."""

    # Select and rename columns for Power BI friendliness
    cols = [
        "customer_id", "age", "gender", "region", "acquisition_channel",
        "customer_tenure_days",
        # RFM
        "recency_days", "frequency", "monetary",
        "r_score", "f_score", "m_score", "rfm_score",
        # Behavior
        "avg_order_value", "median_order_value", "categories_purchased",
        "category_concentration", "discount_usage_rate", "avg_discount_pct",
        "return_rate", "interpurchase_time_avg",
        # Trends
        "spending_trend", "frequency_trend", "aov_trend",
        # Engagement
        "engagement_score", "emails_opened_30d", "website_visits_30d",
        "campaign_clicks_30d", "app_sessions_30d", "support_tickets",
        "loyalty_program",
        # Review data (if available)
        "avg_review_score", "review_count",
        # Segmentation
        "rfm_segment", "kmeans_segment", "cluster",
        # Profitability
        "gross_revenue", "net_revenue", "customer_profit", "profit_margin",
        "profit_quartile", "value_tier",
        # Churn
        "churn_prob", "churn_predicted", "churn_actual",
        # Retention
        "intervention_cost", "success_prob",
        "expected_retention_value", "expected_net_benefit",
        "retention_priority_score", "priority_rank",
        "recommended_action", "risk_tier",
    ]

    # Only keep columns that exist
    available = [c for c in cols if c in df.columns]
    export = df[available].copy()

    # Round numeric columns for cleaner Power BI display
    float_cols = export.select_dtypes(include=[np.floating]).columns
    export[float_cols] = export[float_cols].round(2)

    path = os.path.join(config.OUTPUT_POWERBI, "customer_master.csv")
    export.to_csv(path, index=False)
    print(f"  ✓ Customer Master: {len(export):,} rows, {len(available)} cols → {path}")

    return export


def export_transactions_summary(transactions):
    """Export monthly transaction aggregates per customer for time trends."""
    txn = transactions.copy()
    txn["order_date"] = pd.to_datetime(txn["order_date"])
    txn["year_month"] = txn["order_date"].dt.to_period("M").astype(str)

    monthly = txn.groupby(["customer_id", "year_month"]).agg(
        order_count=("transaction_id", "nunique"),
        total_revenue=("revenue", "sum"),
        total_quantity=("quantity", "sum"),
        avg_order_value=("revenue", "mean"),
        return_count=("is_return", "sum"),
    ).reset_index()

    monthly = monthly.round(2)

    path = os.path.join(config.OUTPUT_POWERBI, "transactions_summary.csv")
    monthly.to_csv(path, index=False)
    print(f"  ✓ Transactions Summary: {len(monthly):,} rows → {path}")

    return monthly


def export_retention_decisions(df, top_n=100):
    """Export top retention targets with full economic breakdown."""
    top = df.nsmallest(top_n, "priority_rank").copy()

    cols = [
        "priority_rank", "customer_id", "rfm_segment", "value_tier",
        "customer_profit", "churn_prob", "success_prob",
        "expected_retention_value", "intervention_cost",
        "expected_net_benefit", "retention_priority_score",
        "recommended_action",
        # Context
        "recency_days", "frequency", "monetary", "engagement_score",
        "spending_trend", "profit_margin",
    ]

    available = [c for c in cols if c in top.columns]
    export = top[available].copy()
    export = export.round(2)

    path = os.path.join(config.OUTPUT_POWERBI, "retention_decisions.csv")
    export.to_csv(path, index=False)
    print(f"  ✓ Retention Decisions: {len(export)} rows → {path}")

    return export


def export_segment_summary(df):
    """Export aggregate metrics per segment for dashboard cards."""
    summary = df.groupby("rfm_segment").agg(
        customer_count=("customer_id", "count"),
        pct_of_total=("customer_id", lambda x: len(x) / len(df) * 100),
        avg_revenue=("gross_revenue", "mean"),
        total_revenue=("gross_revenue", "sum"),
        avg_profit=("customer_profit", "mean"),
        total_profit=("customer_profit", "sum"),
        avg_profit_margin=("profit_margin", "mean"),
        avg_churn_prob=("churn_prob", "mean"),
        churn_count=("churn_predicted", "sum"),
        avg_engagement=("engagement_score", "mean"),
        avg_recency=("recency_days", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_aov=("avg_order_value", "mean"),
        total_erv=("expected_retention_value", "sum"),
        avg_priority=("retention_priority_score", "mean"),
    ).reset_index()

    summary = summary.round(2)

    path = os.path.join(config.OUTPUT_POWERBI, "segment_summary.csv")
    summary.to_csv(path, index=False)
    print(f"  ✓ Segment Summary: {len(summary)} segments → {path}")

    return summary


def export_date_dimension():
    """
    Export a date dimension table for proper time intelligence in Power BI.
    Covers the full Olist dataset time range.
    """
    start = config.TRANSACTION_START
    end = config.ANALYSIS_DATE

    dates = pd.date_range(start=start, end=end, freq="D")
    date_dim = pd.DataFrame({
        "date": dates,
        "year": dates.year,
        "month": dates.month,
        "month_name": dates.strftime("%B"),
        "quarter": dates.quarter,
        "quarter_name": dates.strftime("Q%q").str.replace("q", ""),
        "day_of_week": dates.dayofweek,
        "day_name": dates.strftime("%A"),
        "year_month": dates.strftime("%Y-%m"),
        "is_weekend": dates.dayofweek.isin([5, 6]).astype(int),
    })

    # Fix quarter_name
    date_dim["quarter_name"] = "Q" + date_dim["quarter"].astype(str)

    path = os.path.join(config.OUTPUT_POWERBI, "date_dimension.csv")
    date_dim.to_csv(path, index=False)
    print(f"  ✓ Date Dimension: {len(date_dim):,} rows → {path}")

    return date_dim


def export_geographic_summary(df):
    """Export geographic summary for map visuals in Power BI."""

    geo_cols = ["customer_id", "region"]
    if "customer_state" in df.columns:
        geo_cols.append("customer_state")

    # Group by available geographic columns
    group_col = "customer_state" if "customer_state" in df.columns else "region"

    geo_summary = df.groupby(group_col).agg(
        customer_count=("customer_id", "count"),
        total_revenue=("gross_revenue", "sum"),
        avg_profit=("customer_profit", "mean"),
        avg_churn_prob=("churn_prob", "mean"),
    ).reset_index()

    geo_summary = geo_summary.round(2)

    # Add region mapping if grouping by state
    if group_col == "customer_state":
        geo_summary["region"] = geo_summary["customer_state"].map(
            config.BRAZILIAN_REGIONS
        )

    path = os.path.join(config.OUTPUT_POWERBI, "geographic_summary.csv")
    geo_summary.to_csv(path, index=False)
    print(f"  ✓ Geographic Summary: {len(geo_summary)} locations → {path}")

    return geo_summary


def export_category_performance(transactions):
    """Export product category performance metrics."""
    txn = transactions.copy()
    txn["order_date"] = pd.to_datetime(txn["order_date"])

    # Use super_category if available, else product_category
    cat_col = (
        "product_super_category"
        if "product_super_category" in txn.columns
        else "product_category"
    )

    cat_perf = txn.groupby(cat_col).agg(
        total_orders=("transaction_id", "nunique"),
        total_items=("quantity", "sum"),
        total_revenue=("revenue", "sum"),
        avg_price=("unit_price", "mean"),
        return_rate=("is_return", "mean"),
        unique_customers=("customer_id", "nunique"),
    ).reset_index()

    cat_perf = cat_perf.round(2)
    cat_perf = cat_perf.sort_values("total_revenue", ascending=False)

    path = os.path.join(config.OUTPUT_POWERBI, "category_performance.csv")
    cat_perf.to_csv(path, index=False)
    print(f"  ✓ Category Performance: {len(cat_perf)} categories → {path}")

    return cat_perf


def run(final_data=None, transactions=None):
    """Run Power BI export pipeline."""
    print("\n" + "=" * 60)
    print("PHASE 7: Power BI Export")
    print("=" * 60)

    if final_data is None:
        final_data = pd.read_csv(
            os.path.join(config.DATA_PROCESSED, "customer_retention_final.csv")
        )
    if transactions is None:
        transactions = pd.read_csv(os.path.join(config.DATA_RAW, "transactions.csv"))

    print("\n  Exporting Power BI datasets...")
    export_customer_master(final_data)
    export_transactions_summary(transactions)
    export_retention_decisions(final_data)
    export_segment_summary(final_data)
    export_date_dimension()
    export_geographic_summary(final_data)
    export_category_performance(transactions)

    print(f"\n  ✓ All exports saved to: {config.OUTPUT_POWERBI}")

    return True


if __name__ == "__main__":
    run()
