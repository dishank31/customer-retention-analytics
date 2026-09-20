"""
Phase 1 — Olist E-Commerce Dataset Loader
==========================================
Loads and transforms the real-world Olist Brazilian e-commerce dataset
into the pipeline's expected schema (customers, transactions, engagement).

Dataset Source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Required Files (place in data/raw/olist/):
- olist_customers_dataset.csv
- olist_orders_dataset.csv
- olist_order_items_dataset.csv
- olist_order_payments_dataset.csv
- olist_products_dataset.csv
- olist_product_category_name_translation.csv

Optional Files:
- olist_order_reviews_dataset.csv  (for review-based satisfaction)
- olist_sellers_dataset.csv        (for seller analysis)
- olist_geolocation_dataset.csv    (for geo analysis)
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def load_olist_data(raw_dir=None):
    """
    Load all Olist CSV files and return merged DataFrames.

    Parameters
    ----------
    raw_dir : str
        Path to directory containing Olist CSV files.
        If None, uses config.DATA_OLIST_RAW

    Returns
    -------
    dict : Dictionary containing all loaded DataFrames
    """
    if raw_dir is None:
        raw_dir = config.DATA_OLIST_RAW

    print(f"  Loading Olist datasets from: {raw_dir}")

    dataframes = {}

    # Load required files
    for key in config.OLIST_REQUIRED_FILES:
        filename = config.OLIST_FILES[key]
        filepath = os.path.join(raw_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(
                f"Missing required file: {filepath}\n"
                f"Download from: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce\n"
                f"Place all CSV files in: {raw_dir}"
            )
        dataframes[key] = pd.read_csv(filepath, encoding="utf-8")
        print(f"    ✓ {key}: {len(dataframes[key]):,} rows")

    # Load optional files
    for key in config.OLIST_OPTIONAL_FILES:
        filename = config.OLIST_FILES[key]
        filepath = os.path.join(raw_dir, filename)
        if os.path.exists(filepath):
            dataframes[key] = pd.read_csv(filepath, encoding="utf-8")
            print(f"    ✓ {key}: {len(dataframes[key]):,} rows (optional)")
        else:
            print(f"    ○ {key}: not found (optional, skipped)")

    return dataframes


def _log_data_quality(df, name):
    """Print data quality summary for a DataFrame."""
    nulls = df.isnull().sum()
    null_cols = nulls[nulls > 0]
    if len(null_cols) > 0:
        print(f"    ⚠ {name} null values: {dict(null_cols)}")


def transform_customers(df_customers, df_orders):
    """
    Transform Olist customers into pipeline's customer schema.

    Creates synthetic demographics (age, gender) since Olist only has
    customer_id and geolocation. Preserves real customer IDs.
    """
    print("  Transforming customers...")

    # Get unique customers who have placed orders
    customer_ids = df_orders["customer_id"].unique()

    # Merge with customer geolocation data
    customers = df_customers[df_customers["customer_id"].isin(customer_ids)].copy()

    # Map order-specific customer_id to real customer_unique_id
    if "customer_unique_id" in customers.columns:
        customers["real_customer_id"] = customers["customer_unique_id"]
        customers = customers.drop_duplicates(subset=["real_customer_id"], keep="first")
        customers["customer_id"] = customers["real_customer_id"]

    # Map state to region
    customers["region"] = (
        customers["customer_state"]
        .map(config.BRAZILIAN_REGIONS)
        .fillna("Other")
    )

    # Generate synthetic age (normal distribution, 18-70)
    np.random.seed(config.RANDOM_SEED)
    n_customers = len(customers)
    customers["age"] = np.clip(
        np.random.normal(35, 10, n_customers).astype(int), 18, 70
    )

    # Generate synthetic gender (balanced distribution)
    genders = np.random.choice(
        ["M", "F", "Other"], size=n_customers, p=[0.48, 0.48, 0.04]
    )
    customers["gender"] = genders

    # Generate synthetic signup_date based on first purchase
    df_orders["order_purchase_timestamp"] = pd.to_datetime(
        df_orders["order_purchase_timestamp"]
    )
    first_order = (
        df_orders.groupby("customer_id")["order_purchase_timestamp"]
        .min()
        .reset_index()
    )
    first_order.columns = ["customer_id", "signup_date"]
    customers = customers.merge(first_order, on="customer_id", how="left")

    # Fill missing signup dates with earliest order date
    customers["signup_date"] = pd.to_datetime(customers["signup_date"])
    customers["signup_date"] = customers["signup_date"].fillna(
        df_orders["order_purchase_timestamp"].min()
    )

    # Generate synthetic acquisition_channel
    channels = np.random.choice(
        list(config.ACQUISITION_CHANNELS.keys()),
        size=n_customers,
        p=[v[0] for v in config.ACQUISITION_CHANNELS.values()],
    )
    customers["acquisition_channel"] = channels

    # Select final columns
    customers_final = customers[
        [
            "customer_id",
            "age",
            "gender",
            "region",
            "signup_date",
            "acquisition_channel",
            "customer_city",
            "customer_state",
        ]
    ].copy()

    _log_data_quality(customers_final, "customers")
    print(f"    → {len(customers_final):,} customers")
    return customers_final


def transform_transactions(
    df_orders, df_items, df_payments, df_products, df_translation, df_customers
):
    """
    Transform Olist orders/items into pipeline's transaction schema.
    """
    print("  Transforming transactions...")

    # Map order-specific customer_id to real customer_unique_id
    df_orders = df_orders.merge(df_customers[["customer_id", "customer_unique_id"]], on="customer_id", how="left")
    df_orders["customer_id"] = df_orders["customer_unique_id"]

    # Filter to delivered orders only (exclude cancelled etc.)
    delivered_orders = df_orders[
        df_orders["order_status"].isin(["delivered", "shipped", "invoiced"])
    ].copy()
    print(f"    Filtering to delivered/shipped/invoiced: {len(delivered_orders):,} orders")

    # Merge orders with items
    orders = delivered_orders.merge(df_items, on="order_id", how="inner")

    # Merge product category names (translate Portuguese to English)
    products_translated = df_products.merge(
        df_translation, on="product_category_name", how="left"
    )
    orders = orders.merge(
        products_translated[["product_id", "product_category_name_english"]],
        on="product_id",
        how="left",
    )

    # Fill missing categories
    orders["product_category_name_english"] = orders[
        "product_category_name_english"
    ].fillna("other")

    # Map to super-categories
    orders["product_super_category"] = (
        orders["product_category_name_english"]
        .str.lower()
        .str.strip()
        .map(config.PRODUCT_SUPER_CATEGORIES)
        .fillna(config.DEFAULT_SUPER_CATEGORY)
    )

    # Convert timestamps
    for col in [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_customer_date",
    ]:
        if col in orders.columns:
            orders[col] = pd.to_datetime(orders[col], errors="coerce")

    # Calculate payment value per order
    order_payments = (
        df_payments.groupby("order_id")
        .agg(
            total_payment=("payment_value", "sum"),
            payment_installments=("payment_installments", "mean"),
            payment_type=(
                "payment_type",
                lambda x: x.mode()[0] if len(x) > 0 else "unknown",
            ),
        )
        .reset_index()
    )

    orders = orders.merge(order_payments, on="order_id", how="left")

    # Revenue = item price; cost = estimated COGS
    orders["revenue"] = orders["price"]
    orders["cost_of_goods"] = orders["price"] * config.DEFAULT_COGS_PERCENT

    # Estimate discount (if payment < sum of prices)
    order_item_sum = df_items.groupby("order_id")["price"].sum().reset_index()
    order_item_sum.columns = ["order_id", "total_price"]
    order_payments_calc = (
        df_payments.groupby("order_id")["payment_value"].sum().reset_index()
    )
    order_payments_calc.columns = ["order_id", "total_payment"]

    discount_info = order_item_sum.merge(
        order_payments_calc, on="order_id", how="left"
    )
    discount_info["discount_pct"] = np.where(
        discount_info["total_price"] > discount_info["total_payment"],
        (
            (discount_info["total_price"] - discount_info["total_payment"])
            / discount_info["total_price"]
            * 100
        ).clip(0, 40),
        0,
    )

    orders = orders.merge(
        discount_info[["order_id", "discount_pct"]], on="order_id", how="left"
    )
    orders["discount_pct"] = orders["discount_pct"].fillna(0)

    # Create synthetic is_return flag (based on realistic return rates)
    category_return_rates = {
        "electronics": 0.12,
        "home": 0.08,
        "fashion": 0.18,
        "food": 0.03,
        "beauty": 0.10,
        "health": 0.08,
        "sports": 0.07,
        "books": 0.02,
        "toys": 0.09,
        "baby": 0.06,
    }

    def get_return_rate(category):
        if pd.isna(category):
            return 0.05
        cat_lower = str(category).lower()
        for cat, rate in category_return_rates.items():
            if cat in cat_lower:
                return rate
        return 0.05

    np.random.seed(config.RANDOM_SEED + 1)
    orders["is_return"] = orders["product_category_name_english"].apply(
        lambda x: 1 if np.random.random() < get_return_rate(x) else 0
    )

    # Set quantity to 1 per item row (Olist has one row per item)
    orders["quantity"] = 1

    # Create product_id with prefix
    orders["product_id"] = "P_" + orders["product_id"].astype(str)

    # Rename and select columns to match pipeline schema
    transactions = orders.rename(
        columns={
            "order_id": "transaction_id",
            "customer_id": "customer_id",
            "order_purchase_timestamp": "order_date",
            "product_category_name_english": "product_category",
            "price": "unit_price",
        }
    )[
        [
            "transaction_id",
            "customer_id",
            "order_date",
            "product_category",
            "product_super_category",
            "product_id",
            "quantity",
            "unit_price",
            "revenue",
            "discount_pct",
            "is_return",
            "cost_of_goods",
            "freight_value",
        ]
    ].copy()

    # Format order_date as string
    transactions["order_date"] = transactions["order_date"].dt.strftime("%Y-%m-%d")

    # Drop rows with null order_date
    before = len(transactions)
    transactions = transactions.dropna(subset=["order_date"])
    if before > len(transactions):
        print(f"    ⚠ Dropped {before - len(transactions)} rows with null dates")

    _log_data_quality(transactions, "transactions")
    print(f"    → {len(transactions):,} transaction rows")
    return transactions


def create_engagement_proxy(customers, transactions, analysis_date):
    """
    Create synthetic engagement metrics since Olist doesn't have this data.

    Uses transaction patterns to create realistic proxy engagement scores.
    """
    print("  Creating engagement proxies...")

    analysis_ts = pd.Timestamp(analysis_date)
    txn = transactions.copy()
    txn["order_date"] = pd.to_datetime(txn["order_date"])

    # Calculate recency for each customer
    last_purchase = txn.groupby("customer_id")["order_date"].max().reset_index()
    last_purchase.columns = ["customer_id", "last_purchase"]

    # Get recent transactions (last 30 days relative to analysis date)
    recent_start = analysis_ts - pd.Timedelta(days=30)
    recent_txn = txn[txn["order_date"] >= recent_start]

    # Calculate engagement proxies based on purchase behavior
    engagement_metrics = (
        recent_txn.groupby("customer_id")
        .agg(
            recent_orders=("transaction_id", "nunique"),
            recent_revenue=("revenue", "sum"),
            recent_items=("quantity", "sum"),
        )
        .reset_index()
    )

    # Merge with all customers
    engagement = customers[["customer_id"]].merge(
        engagement_metrics, on="customer_id", how="left"
    )
    engagement = engagement.fillna(0)

    # Create proxy engagement metrics correlated with purchase activity
    np.random.seed(config.RANDOM_SEED)
    n = len(engagement)

    # Emails opened: correlated with order frequency
    engagement["emails_opened_30d"] = (
        (engagement["recent_orders"] * 2 + np.random.poisson(3, n))
        .clip(0, 25)
        .astype(int)
    )

    # Website visits: higher correlation with browsing before purchase
    engagement["website_visits_30d"] = (
        (engagement["recent_orders"] * 5 + np.random.poisson(10, n))
        .clip(0, 60)
        .astype(int)
    )

    # Campaign clicks: correlated with purchases
    engagement["campaign_clicks_30d"] = (
        (engagement["recent_orders"] * 1.5 + np.random.poisson(2, n))
        .clip(0, 20)
        .astype(int)
    )

    # App sessions: random but correlated with active users
    engagement["app_sessions_30d"] = (
        (engagement["recent_orders"] * 3 + np.random.poisson(8, n))
        .clip(0, 50)
        .astype(int)
    )

    # Support tickets: low probability per order
    engagement["support_tickets"] = (
        np.random.poisson(engagement["recent_orders"] * 0.1, n)
        .clip(0, 8)
        .astype(int)
    )

    # Loyalty program: more likely for frequent buyers
    loyalty_prob = np.clip(engagement["recent_orders"] / 10, 0, 0.8)
    engagement["loyalty_program"] = (
        (np.random.random(n) < loyalty_prob).astype(int)
    )

    # Drop helper columns
    engagement = engagement.drop(
        columns=["recent_orders", "recent_revenue", "recent_items"],
        errors="ignore",
    )

    print(f"    → Engagement data for {len(engagement):,} customers")
    return engagement


def enrich_with_reviews(engagement, df_reviews, df_orders):
    """
    Enrich engagement data with review scores if reviews data is available.
    """
    if df_reviews is None:
        return engagement

    print("  Enriching with review data...")

    # Merge reviews with orders to get customer_id
    reviews_with_customer = df_reviews.merge(
        df_orders[["order_id", "customer_id"]], on="order_id", how="inner"
    )

    # Aggregate review scores per customer
    review_agg = (
        reviews_with_customer.groupby("customer_id")
        .agg(
            avg_review_score=("review_score", "mean"),
            review_count=("review_id", "count"),
        )
        .reset_index()
    )
    review_agg["avg_review_score"] = review_agg["avg_review_score"].round(2)

    # Merge with engagement
    engagement = engagement.merge(review_agg, on="customer_id", how="left")
    engagement["avg_review_score"] = engagement["avg_review_score"].fillna(0)
    engagement["review_count"] = engagement["review_count"].fillna(0).astype(int)

    print(f"    → Added review scores for {(engagement['review_count'] > 0).sum():,} customers")
    return engagement


def run(save_to_csv=True):
    """
    Main function to load Olist data and transform to pipeline format.

    Parameters
    ----------
    save_to_csv : bool
        Whether to save transformed data to CSV files

    Returns
    -------
    tuple : (customers, transactions, engagement) DataFrames
    """
    print("\n" + "=" * 60)
    print("PHASE 1: Olist Dataset Loading & Transformation")
    print("=" * 60)

    # Step 1: Load raw Olist data
    print("\n  Step 1: Loading raw Olist datasets...")
    raw_data = load_olist_data()

    # Step 2: Transform customers
    print("\n  Step 2: Transforming customer data...")
    customers = transform_customers(raw_data["customers"], raw_data["orders"])

    # Step 3: Transform transactions
    print("\n  Step 3: Transforming transaction data...")
    transactions = transform_transactions(
        raw_data["orders"],
        raw_data["order_items"],
        raw_data["payments"],
        raw_data["products"],
        raw_data["category_translation"],
        raw_data["customers"],
    )

    # Step 4: Create engagement proxies
    print("\n  Step 4: Creating engagement proxy metrics...")
    engagement = create_engagement_proxy(
        customers, transactions, config.ANALYSIS_DATE
    )

    # Step 4b: Enrich with reviews if available
    if "reviews" in raw_data:
        engagement = enrich_with_reviews(
            engagement, raw_data["reviews"], raw_data["orders"]
        )

    # Step 5: Save to CSV
    if save_to_csv:
        print("\n  Step 5: Saving transformed data...")

        cust_path = os.path.join(config.DATA_RAW, "customers.csv")
        txn_path = os.path.join(config.DATA_RAW, "transactions.csv")
        eng_path = os.path.join(config.DATA_RAW, "engagement.csv")

        customers.to_csv(cust_path, index=False)
        transactions.to_csv(txn_path, index=False)
        engagement.to_csv(eng_path, index=False)

        print(f"\n  ✓ Customers:    {len(customers):>6,} rows → {cust_path}")
        print(f"  ✓ Transactions: {len(transactions):>6,} rows → {txn_path}")
        print(f"  ✓ Engagement:   {len(engagement):>6,} rows → {eng_path}")

    print("\n" + "=" * 60)
    print("  OLIST DATA LOADING COMPLETE")
    print("=" * 60)

    # Print summary statistics
    print("\n  Dataset Summary:")
    print(f"    Time Period: {transactions['order_date'].min()} to {transactions['order_date'].max()}")
    print(f"    Unique Customers: {customers['customer_id'].nunique():,}")
    print(f"    Unique Products: {transactions['product_id'].nunique():,}")
    print(f"    Product Categories: {transactions['product_category'].nunique()}")
    print(f"    Super Categories: {transactions['product_super_category'].nunique()}")
    print(f"    Total Revenue: {config.CURRENCY_SYMBOL} {transactions['revenue'].sum():,.2f}")

    return customers, transactions, engagement


if __name__ == "__main__":
    run()
