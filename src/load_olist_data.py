"""
Phase 2 — Olist E-Commerce Dataset Loader
==========================================
Loads and transforms the real-world Olist Brazilian e-commerce dataset
into the pipeline's expected schema (customers, transactions, engagement).

Dataset Source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Required Files (place in data/raw/olist_raw/):
- olist_customers_dataset.csv
- olist_orders_dataset.csv
- olist_order_items_dataset.csv
- olist_order_payments_dataset.csv
- olist_products_dataset.csv
- olist_product_category_name_translation.csv
- olist_geolocation_dataset.csv (optional for geo analysis)
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
    
    Parameters:
    -----------
    raw_dir : str
        Path to directory containing Olist CSV files.
        If None, uses config.DATA_RAW + "/olist_raw"
    
    Returns:
    --------
    dict : Dictionary containing all loaded DataFrames
    """
    if raw_dir is None:
        raw_dir = os.path.join(config.DATA_RAW, "olist_raw")
    
    print(f"Loading Olist datasets from: {raw_dir}")
    
    # Load all required files
    files = {
        "customers": "olist_customers_dataset.csv",
        "orders": "olist_orders_dataset.csv",
        "order_items": "olist_order_items_dataset.csv",
        "payments": "olist_order_payments_dataset.csv",
        "products": "olist_products_dataset.csv",
        "category_translation": "olist_product_category_name_translation.csv",
    }
    
    dataframes = {}
    for key, filename in files.items():
        filepath = os.path.join(raw_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Missing required file: {filepath}")
        dataframes[key] = pd.read_csv(filepath, encoding='utf-8')
        print(f"  ✓ Loaded {key}: {len(dataframes[key])} rows")
    
    return dataframes


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
    
    # Map state to region (Brazilian states → simplified regions)
    state_to_region = {
        "SP": "Southeast", "RJ": "Southeast", "MG": "Southeast", "ES": "Southeast",
        "PR": "South", "SC": "South", "RS": "South",
        "BA": "Northeast", "PE": "Northeast", "CE": "Northeast", "PA": "North",
        "AM": "North", "MA": "Northeast", "GO": "Central-West", "DF": "Central-West",
        "MT": "Central-West", "MS": "Central-West", "RO": "North",
        "AL": "Northeast", "RN": "Northeast", "PB": "Northeast", "SE": "Northeast",
        "PI": "Northeast", "TO": "North", "AC": "North", "AP": "North", "RR": "North",
    }
    
    customers["region"] = customers["customer_state"].map(state_to_region).fillna("Other")
    
    # Generate synthetic age (normal distribution, 18-70)
    np.random.seed(config.RANDOM_SEED)
    n_customers = len(customers)
    customers["age"] = np.clip(np.random.normal(35, 10, n_customers).astype(int), 18, 70)
    
    # Generate synthetic gender (balanced distribution)
    genders = np.random.choice(["M", "F", "Other"], size=n_customers, p=[0.48, 0.48, 0.04])
    customers["gender"] = genders
    
    # Generate synthetic signup_date based on first purchase
    first_order = df_orders.groupby("customer_id")["order_purchase_timestamp"].min().reset_index()
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
        p=[v[0] for v in config.ACQUISITION_CHANNELS.values()]
    )
    customers["acquisition_channel"] = channels
    
    # Select final columns
    customers_final = customers[[
        "customer_id", "age", "gender", "region", "signup_date",
        "acquisition_channel", "customer_city", "customer_state"
    ]].copy()
    
    print(f"    Created {len(customers_final)} customers")
    return customers_final


def transform_transactions(df_orders, df_items, df_payments, df_products, df_translation):
    """
    Transform Olist orders/items into pipeline's transaction schema.
    """
    print("  Transforming transactions...")
    
    # Merge orders with items
    orders = df_orders.merge(df_items, on="order_id", how="inner")
    
    # Merge product category names (translate Portuguese to English)
    products_translated = df_products.merge(
        df_translation, 
        on="product_category_name", 
        how="left"
    )
    orders = orders.merge(
        products_translated[["product_id", "product_category_name_english"]],
        on="product_id",
        how="left"
    )
    
    # Fill missing categories
    orders["product_category_name_english"] = orders["product_category_name_english"].fillna("Other")
    
    # Convert timestamps
    orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])
    orders["order_approved_at"] = pd.to_datetime(orders["order_approved_at"])
    orders["order_delivered_customer_date"] = pd.to_datetime(orders["order_delivered_customer_date"])
    
    # Calculate payment value per item (distribute payment across items)
    # First, get total payment per order
    order_payments = df_payments.groupby("order_id").agg(
        total_payment=("payment_value", "sum"),
        payment_installments=("payment_installments", "mean"),
        payment_type=("payment_type", lambda x: x.mode()[0] if len(x) > 0 else "unknown")
    ).reset_index()
    
    orders = orders.merge(order_payments, on="order_id", how="left")
    
    # Calculate revenue per item (proportional to price)
    orders["revenue"] = orders["price"]
    orders["cost_of_goods"] = orders["price"] * 0.55  # Average 55% COGS
    
    # Estimate discount (if payment < sum of prices)
    order_item_sum = df_items.groupby("order_id")["price"].sum().reset_index()
    order_item_sum.columns = ["order_id", "total_price"]
    order_payments_calc = df_payments.groupby("order_id")["payment_value"].sum().reset_index()
    order_payments_calc.columns = ["order_id", "total_payment"]
    
    discount_info = order_item_sum.merge(order_payments_calc, on="order_id", how="left")
    discount_info["discount_pct"] = np.where(
        discount_info["total_price"] > discount_info["total_payment"],
        ((discount_info["total_price"] - discount_info["total_payment"]) / discount_info["total_price"] * 100).clip(0, 40),
        0
    )
    
    orders = orders.merge(discount_info[["order_id", "discount_pct"]], on="order_id", how="left")
    orders["discount_pct"] = orders["discount_pct"].fillna(0)
    
    # Create synthetic is_return flag (based on realistic return rates by category)
    category_return_rates = {
        "electronics": 0.12, "home_furniture": 0.08, "fashion_clothing": 0.18,
        "food_drink": 0.03, "beauty": 0.10, "sports": 0.07, "books": 0.02,
        "toys": 0.09, "baby": 0.06, "health": 0.08
    }
    
    def get_return_rate(category):
        if pd.isna(category):
            return 0.05
        category_lower = str(category).lower()
        for cat, rate in category_return_rates.items():
            if cat in category_lower:
                return rate
        return 0.05
    
    orders["is_return"] = orders["product_category_name_english"].apply(
        lambda x: 1 if np.random.random() < get_return_rate(x) else 0
    )
    
    # Create product_id
    orders["product_id"] = "P_" + orders["product_id"].astype(str)
    
    # Rename and select columns to match pipeline schema
    transactions = orders.rename(columns={
        "order_id": "transaction_id",
        "customer_id": "customer_id",
        "order_purchase_timestamp": "order_date",
        "product_category_name_english": "product_category",
        "quantity": "quantity",
        "price": "unit_price",
        "revenue": "revenue",
        "cost_of_goods": "cost_of_goods",
        "discount_pct": "discount_pct",
        "is_return": "is_return",
    })[[
        "transaction_id", "customer_id", "order_date", "product_category",
        "product_id", "quantity", "unit_price", "revenue", "discount_pct",
        "is_return", "cost_of_goods"
    ]].copy()
    
    # Format order_date as string
    transactions["order_date"] = transactions["order_date"].dt.strftime("%Y-%m-%d")
    
    print(f"    Created {len(transactions)} transaction rows")
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
    
    # Get recent transactions (last 30 days)
    recent_start = analysis_ts - pd.Timedelta(days=30)
    recent_txn = txn[txn["order_date"] >= recent_start]
    
    # Calculate engagement proxies based on purchase behavior
    engagement_metrics = recent_txn.groupby("customer_id").agg(
        recent_orders=("transaction_id", "nunique"),
        recent_revenue=("revenue", "sum"),
        recent_items=("quantity", "sum"),
    ).reset_index()
    
    # Merge with all customers
    engagement = customers[["customer_id"]].merge(
        engagement_metrics, 
        on="customer_id", 
        how="left"
    )
    engagement = engagement.fillna(0)
    
    # Create proxy engagement metrics correlated with purchase activity
    np.random.seed(config.RANDOM_SEED)
    
    # Emails opened: correlated with order frequency
    engagement["emails_opened_30d"] = (
        (engagement["recent_orders"] * 2 + np.random.poisson(3, len(engagement))).clip(0, 25).astype(int)
    )
    
    # Website visits: higher correlation with browsing before purchase
    engagement["website_visits_30d"] = (
        (engagement["recent_orders"] * 5 + np.random.poisson(10, len(engagement))).clip(0, 60).astype(int)
    )
    
    # Campaign clicks: correlated with purchases
    engagement["campaign_clicks_30d"] = (
        (engagement["recent_orders"] * 1.5 + np.random.poisson(2, len(engagement))).clip(0, 20).astype(int)
    )
    
    # App sessions: random but correlated with active users
    engagement["app_sessions_30d"] = (
        (engagement["recent_orders"] * 3 + np.random.poisson(8, len(engagement))).clip(0, 50).astype(int)
    )
    
    # Support tickets: low probability per order
    engagement["support_tickets"] = (
        np.random.poisson(engagement["recent_orders"] * 0.1, len(engagement)).clip(0, 8).astype(int)
    )
    
    # Loyalty program: more likely for frequent buyers
    loyalty_prob = np.clip(engagement["recent_orders"] / 10, 0, 0.8)
    engagement["loyalty_program"] = (
        (np.random.random(len(engagement)) < loyalty_prob).astype(int)
    )
    
    print(f"    Created engagement data for {len(engagement)} customers")
    return engagement


def run(save_to_csv=True):
    """
    Main function to load Olist data and transform to pipeline format.
    
    Parameters:
    -----------
    save_to_csv : bool
        Whether to save transformed data to CSV files
    
    Returns:
    --------
    tuple : (customers, transactions, engagement) DataFrames
    """
    print("\n" + "="*60)
    print("PHASE 2: Olist Dataset Loading & Transformation")
    print("="*60)
    
    # Step 1: Load raw Olist data
    print("\n  Step 1: Loading raw Olist datasets...")
    raw_data = load_olist_data()
    
    # Step 2: Transform customers
    print("\n  Step 2: Transforming customer data...")
    customers = transform_customers(
        raw_data["customers"], 
        raw_data["orders"]
    )
    
    # Step 3: Transform transactions
    print("\n  Step 3: Transforming transaction data...")
    transactions = transform_transactions(
        raw_data["orders"],
        raw_data["order_items"],
        raw_data["payments"],
        raw_data["products"],
        raw_data["category_translation"]
    )
    
    # Step 4: Create engagement proxies
    print("\n  Step 4: Creating engagement proxy metrics...")
    engagement = create_engagement_proxy(
        customers, 
        transactions, 
        config.ANALYSIS_DATE
    )
    
    # Step 5: Save to CSV (matching synthetic data format)
    if save_to_csv:
        print("\n  Step 5: Saving transformed data...")
        
        # Create backup of any existing synthetic data
        if os.path.exists(os.path.join(config.DATA_RAW, "customers.csv")):
            backup_dir = os.path.join(config.DATA_RAW, "synthetic_backup")
            os.makedirs(backup_dir, exist_ok=True)
            for fname in ["customers.csv", "transactions.csv", "engagement.csv"]:
                src = os.path.join(config.DATA_RAW, fname)
                dst = os.path.join(backup_dir, fname)
                if os.path.exists(src):
                    os.rename(src, dst)
            print(f"    Backed up synthetic data to: {backup_dir}")
        
        # Save Olist-transformed data
        cust_path = os.path.join(config.DATA_RAW, "customers.csv")
        txn_path = os.path.join(config.DATA_RAW, "transactions.csv")
        eng_path = os.path.join(config.DATA_RAW, "engagement.csv")
        
        customers.to_csv(cust_path, index=False)
        transactions.to_csv(txn_path, index=False)
        engagement.to_csv(eng_path, index=False)
        
        print(f"\n  ✓ Customers:    {len(customers):>6} rows → {cust_path}")
        print(f"  ✓ Transactions: {len(transactions):>6} rows → {txn_path}")
        print(f"  ✓ Engagement:   {len(engagement):>6} rows → {eng_path}")
    
    print("\n" + "="*60)
    print("  OLIST DATA LOADING COMPLETE")
    print("="*60)
    
    # Print summary statistics
    print("\n  Dataset Summary:")
    print(f"    Time Period: {transactions['order_date'].min()} to {transactions['order_date'].max()}")
    print(f"    Unique Customers: {customers['customer_id'].nunique()}")
    print(f"    Unique Products: {transactions['product_id'].nunique()}")
    print(f"    Product Categories: {transactions['product_category'].nunique()}")
    print(f"    Total Revenue: R$ {transactions['revenue'].sum():,.2f}")
    
    return customers, transactions, engagement


if __name__ == "__main__":
    run()
