"""
Phase 8 — Power BI Export
==========================
Produces clean, Power BI-optimized CSV exports and a comprehensive
dashboard design guide with DAX measures.
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
    print(f"  ✓ Customer Master: {len(export)} rows, {len(available)} cols → {path}")

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
    print(f"  ✓ Transactions Summary: {len(monthly)} rows → {path}")

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


def run(final_data=None, transactions=None):
    """Run Power BI export pipeline."""
    print("\n" + "="*60)
    print("PHASE 8: Power BI Export")
    print("="*60)

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

    print(f"\n  ✓ All exports saved to: {config.OUTPUT_POWERBI}")

    return True


if __name__ == "__main__":
    run()
