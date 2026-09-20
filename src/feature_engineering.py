"""
Phase 2 — Customer Feature Engineering
========================================
Transforms transaction-level data into one row per customer
with RFM, behavioral, trend, and engagement features (~25 features).
Designed to work with Olist real-world data.
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def compute_rfm(transactions, analysis_date=config.ANALYSIS_DATE):
    """Compute core RFM metrics per customer."""
    txn = transactions.copy()
    txn["order_date"] = pd.to_datetime(txn["order_date"])

    # Exclude returns for monetary
    txn_valid = txn[txn["is_return"] == 0].copy()

    rfm = txn_valid.groupby("customer_id").agg(
        last_purchase_date=("order_date", "max"),
        frequency=("transaction_id", "nunique"),
        monetary=("revenue", "sum"),
    ).reset_index()

    rfm["recency_days"] = (
        pd.Timestamp(analysis_date) - rfm["last_purchase_date"]
    ).dt.days
    rfm.drop(columns=["last_purchase_date"], inplace=True)

    return rfm


def compute_purchase_behavior(transactions):
    """Compute purchase behavior features beyond RFM."""
    txn = transactions.copy()
    txn["order_date"] = pd.to_datetime(txn["order_date"])
    txn_valid = txn[txn["is_return"] == 0].copy()

    # Per-order aggregates
    order_agg = txn_valid.groupby(["customer_id", "transaction_id"]).agg(
        order_value=("revenue", "sum"),
        order_quantity=("quantity", "sum"),
        order_date=("order_date", "first"),
    ).reset_index()

    # Customer-level from orders
    cust_orders = order_agg.groupby("customer_id").agg(
        avg_order_value=("order_value", "mean"),
        median_order_value=("order_value", "median"),
        purchase_std=("order_value", "std"),
        avg_quantity=("order_quantity", "mean"),
    ).reset_index()
    cust_orders["purchase_std"] = cust_orders["purchase_std"].fillna(0)

    # Category diversity (use product_category)
    cat_col = "product_category"
    cat_diversity = txn_valid.groupby("customer_id").agg(
        categories_purchased=(cat_col, "nunique"),
    ).reset_index()

    # Super-category diversity (if available)
    if "product_super_category" in txn_valid.columns:
        super_diversity = txn_valid.groupby("customer_id").agg(
            super_categories_purchased=("product_super_category", "nunique"),
        ).reset_index()
    else:
        super_diversity = None

    # Category concentration (Herfindahl index)
    cat_spend = txn_valid.groupby(["customer_id", cat_col])["revenue"].sum().reset_index()
    cat_total = cat_spend.groupby("customer_id")["revenue"].sum().reset_index()
    cat_total.columns = ["customer_id", "total_rev"]
    cat_spend = cat_spend.merge(cat_total, on="customer_id")
    cat_spend["share"] = cat_spend["revenue"] / cat_spend["total_rev"]
    cat_spend["share_sq"] = cat_spend["share"] ** 2
    hhi = cat_spend.groupby("customer_id")["share_sq"].sum().reset_index()
    hhi.columns = ["customer_id", "category_concentration"]

    # Discount usage
    discount_usage = txn_valid.groupby("customer_id").agg(
        discount_usage_rate=("discount_pct", lambda x: (x > 0).mean()),
        avg_discount_pct=("discount_pct", "mean"),
    ).reset_index()

    # Return rate (from all transactions including returns)
    txn_all = transactions.copy()
    return_rate = txn_all.groupby("customer_id").agg(
        total_txns=("transaction_id", "count"),
        total_returns=("is_return", "sum"),
    ).reset_index()
    return_rate["return_rate"] = return_rate["total_returns"] / return_rate["total_txns"]
    return_rate = return_rate[["customer_id", "return_rate"]]

    # Interpurchase time
    order_dates = order_agg.sort_values(["customer_id", "order_date"])
    order_dates["prev_date"] = order_dates.groupby("customer_id")["order_date"].shift(1)
    order_dates["gap_days"] = (order_dates["order_date"] - order_dates["prev_date"]).dt.days
    ipt = order_dates.groupby("customer_id").agg(
        interpurchase_time_avg=("gap_days", "mean"),
        interpurchase_time_std=("gap_days", "std"),
    ).reset_index()
    ipt["interpurchase_time_avg"] = ipt["interpurchase_time_avg"].fillna(0)
    ipt["interpurchase_time_std"] = ipt["interpurchase_time_std"].fillna(0)

    # Merge all
    behavior = cust_orders
    for df in [cat_diversity, hhi, discount_usage, return_rate, ipt]:
        behavior = behavior.merge(df, on="customer_id", how="left")

    if super_diversity is not None:
        behavior = behavior.merge(super_diversity, on="customer_id", how="left")

    return behavior


def compute_trend_features(transactions, analysis_date=config.ANALYSIS_DATE):
    """Compute spending and frequency trends (recent vs previous 90-day windows)."""
    txn = transactions.copy()
    txn["order_date"] = pd.to_datetime(txn["order_date"])
    txn_valid = txn[txn["is_return"] == 0].copy()

    window = config.TREND_WINDOW_DAYS
    recent_start = pd.Timestamp(analysis_date) - pd.Timedelta(days=window)
    prev_start = recent_start - pd.Timedelta(days=window)

    recent = txn_valid[txn_valid["order_date"] >= recent_start]
    previous = txn_valid[
        (txn_valid["order_date"] >= prev_start)
        & (txn_valid["order_date"] < recent_start)
    ]

    # Recent window aggregates
    recent_agg = recent.groupby("customer_id").agg(
        recent_spend=("revenue", "sum"),
        recent_orders=("transaction_id", "nunique"),
        recent_aov=("revenue", "mean"),
    ).reset_index()

    # Previous window aggregates
    prev_agg = previous.groupby("customer_id").agg(
        prev_spend=("revenue", "sum"),
        prev_orders=("transaction_id", "nunique"),
        prev_aov=("revenue", "mean"),
    ).reset_index()

    # Get all customers
    all_custs = pd.DataFrame({"customer_id": txn_valid["customer_id"].unique()})
    trends = all_custs.merge(recent_agg, on="customer_id", how="left")
    trends = trends.merge(prev_agg, on="customer_id", how="left")
    trends = trends.fillna(0)

    # Trend calculations (avoid division by zero)
    def safe_trend(recent_col, prev_col):
        return np.where(
            trends[prev_col] > 0,
            (trends[recent_col] - trends[prev_col]) / trends[prev_col],
            np.where(trends[recent_col] > 0, 1.0, 0.0),
        )

    trends["spending_trend"] = safe_trend("recent_spend", "prev_spend")
    trends["frequency_trend"] = safe_trend("recent_orders", "prev_orders")
    trends["aov_trend"] = safe_trend("recent_aov", "prev_aov")

    # Clip extreme trends
    for col in ["spending_trend", "frequency_trend", "aov_trend"]:
        trends[col] = np.clip(trends[col], -1.0, 5.0)

    return trends[["customer_id", "spending_trend", "frequency_trend", "aov_trend"]]


def compute_engagement_score(engagement):
    """Compute composite engagement score from engagement metrics."""
    eng = engagement.copy()

    # Normalize each metric to 0-1 range
    for col, weight in config.ENGAGEMENT_WEIGHTS.items():
        if col in eng.columns:
            col_max = eng[col].max()
            if col_max > 0:
                eng[f"{col}_norm"] = eng[col] / col_max
            else:
                eng[f"{col}_norm"] = 0

    # Weighted composite score (0-100)
    eng["engagement_score"] = sum(
        eng.get(f"{col}_norm", 0) * weight * 100
        for col, weight in config.ENGAGEMENT_WEIGHTS.items()
    )
    eng["engagement_score"] = eng["engagement_score"].round(2)

    return eng[["customer_id", "engagement_score"]]


def run(customers=None, transactions=None, engagement=None):
    """Run full feature engineering pipeline."""
    print("\n" + "=" * 60)
    print("PHASE 2: Feature Engineering")
    print("=" * 60)

    # Load data if not passed
    if customers is None:
        customers = pd.read_csv(os.path.join(config.DATA_RAW, "customers.csv"))
    if transactions is None:
        transactions = pd.read_csv(os.path.join(config.DATA_RAW, "transactions.csv"))
    if engagement is None:
        engagement = pd.read_csv(os.path.join(config.DATA_RAW, "engagement.csv"))

    # Compute features
    print("  Computing RFM features...")
    rfm = compute_rfm(transactions)

    print("  Computing purchase behavior features...")
    behavior = compute_purchase_behavior(transactions)

    print("  Computing trend features...")
    trends = compute_trend_features(transactions)

    print("  Computing engagement score...")
    eng_score = compute_engagement_score(engagement)

    # Merge everything into customer master
    print("  Assembling customer feature matrix...")
    customer_features = customers[
        ["customer_id", "age", "gender", "region", "signup_date", "acquisition_channel"]
    ].copy()

    # Customer tenure
    customer_features["signup_date"] = pd.to_datetime(customer_features["signup_date"])
    customer_features["customer_tenure_days"] = (
        pd.Timestamp(config.ANALYSIS_DATE) - customer_features["signup_date"]
    ).dt.days

    # Merge all feature sets
    for df in [rfm, behavior, trends, eng_score]:
        customer_features = customer_features.merge(df, on="customer_id", how="left")

    # Merge engagement raw + loyalty
    eng_cols = [
        "customer_id",
        "emails_opened_30d",
        "website_visits_30d",
        "campaign_clicks_30d",
        "app_sessions_30d",
        "support_tickets",
        "loyalty_program",
    ]
    available_eng_cols = [c for c in eng_cols if c in engagement.columns]
    customer_features = customer_features.merge(
        engagement[available_eng_cols], on="customer_id", how="left"
    )

    # Merge review data if available
    if "avg_review_score" in engagement.columns:
        customer_features = customer_features.merge(
            engagement[["customer_id", "avg_review_score", "review_count"]],
            on="customer_id",
            how="left",
        )

    # Fill NaN for customers with no transactions in certain windows
    numeric_cols = customer_features.select_dtypes(include=[np.number]).columns
    customer_features[numeric_cols] = customer_features[numeric_cols].fillna(0)

    # Save
    out_path = os.path.join(config.DATA_PROCESSED, "customer_features.csv")
    customer_features.to_csv(out_path, index=False)
    print(
        f"\n  ✓ Customer features: {len(customer_features):,} rows, "
        f"{len(customer_features.columns)} columns → {out_path}"
    )

    return customer_features


if __name__ == "__main__":
    run()
