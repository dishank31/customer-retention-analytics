"""
Phase 2 — Synthetic Dataset Generation
=======================================
Generates three relational tables (customers, transactions, engagement)
with realistic distributions and correlated behavior profiles.
"""

import os
import sys
import numpy as np
import pandas as pd
from faker import Faker
from datetime import timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

fake = Faker("en_IN")  # Indian locale for names/addresses
Faker.seed(config.RANDOM_SEED)
np.random.seed(config.RANDOM_SEED)


# ─── Behavior Profiles ──────────────────────────────────────────────────
# Each customer is assigned a profile that drives correlated behavior
PROFILES = {
    # profile: (prob, avg_orders, spend_mult, engage_mult, churn_tendency)
    "power_user":     (0.10, 30, 1.8, 1.5, 0.05),
    "regular":        (0.35, 16, 1.0, 1.0, 0.15),
    "occasional":     (0.30, 8,  0.7, 0.6, 0.30),
    "declining":      (0.15, 12, 0.9, 0.4, 0.60),
    "one_time":       (0.10, 2,  0.5, 0.2, 0.80),
}


def generate_customers(n=config.NUM_CUSTOMERS):
    """Generate customer demographics table."""
    print(f"  Generating {n} customers...")

    profiles = np.random.choice(
        list(PROFILES.keys()),
        size=n,
        p=[v[0] for v in PROFILES.values()]
    )

    regions = np.random.choice(config.REGIONS, size=n)
    channels = np.random.choice(
        list(config.ACQUISITION_CHANNELS.keys()),
        size=n,
        p=[v[0] for v in config.ACQUISITION_CHANNELS.values()]
    )

    # Signup dates: spread over 2022-01 to 2025-03
    signup_start = pd.Timestamp("2022-01-01")
    signup_end = pd.Timestamp("2025-03-31")
    signup_range_days = (signup_end - signup_start).days
    signup_dates = [
        signup_start + timedelta(days=int(np.random.uniform(0, signup_range_days)))
        for _ in range(n)
    ]

    # Age: normal distribution centered at 35
    ages = np.clip(np.random.normal(35, 10, n).astype(int), 18, 70)

    genders = np.random.choice(["M", "F", "Other"], size=n, p=[0.48, 0.48, 0.04])

    customers = pd.DataFrame({
        "customer_id": [f"C{str(i+1).zfill(4)}" for i in range(n)],
        "age": ages,
        "gender": genders,
        "region": regions,
        "signup_date": signup_dates,
        "acquisition_channel": channels,
        "behavior_profile": profiles,  # kept for internal use, can be dropped for export
    })

    return customers


def generate_transactions(customers):
    """Generate transaction-level data with realistic patterns."""
    print(f"  Generating transactions...")

    all_transactions = []
    txn_id_counter = 10001
    categories = list(config.PRODUCT_CATEGORIES.keys())

    for _, cust in customers.iterrows():
        cid = cust["customer_id"]
        profile = cust["behavior_profile"]
        signup = pd.Timestamp(cust["signup_date"])
        profile_params = PROFILES[profile]

        avg_orders = profile_params[1]
        spend_mult = profile_params[2]
        churn_tendency = profile_params[4]

        # Number of orders: Poisson-distributed around profile avg
        n_orders = max(1, np.random.poisson(avg_orders))

        # Eligible purchase window: signup to transaction end
        eligible_start = max(signup, pd.Timestamp(config.TRANSACTION_START))
        eligible_end = pd.Timestamp(config.TRANSACTION_END)
        if eligible_start >= eligible_end:
            eligible_start = eligible_end - timedelta(days=30)

        window_days = (eligible_end - eligible_start).days
        if window_days <= 0:
            window_days = 30

        # For declining customers, concentrate purchases early
        if profile == "declining":
            order_offsets = np.sort(np.random.beta(1.5, 4, n_orders) * window_days).astype(int)
        elif profile == "one_time":
            order_offsets = np.random.uniform(0, window_days * 0.3, n_orders).astype(int)
        else:
            order_offsets = np.sort(np.random.uniform(0, window_days, n_orders)).astype(int)

        # Category preference: each customer has a primary category
        primary_cat = np.random.choice(categories)
        cat_weights = [0.1] * len(categories)
        cat_weights[categories.index(primary_cat)] = 0.4
        cat_weights = np.array(cat_weights) / sum(cat_weights)

        for offset in order_offsets:
            order_date = eligible_start + timedelta(days=int(offset))

            # 1-3 items per order
            n_items = np.random.choice([1, 2, 3], p=[0.60, 0.30, 0.10])

            for _ in range(n_items):
                cat = np.random.choice(categories, p=cat_weights)
                cat_params = config.PRODUCT_CATEGORIES[cat]
                avg_price, price_std, cogs_pct, return_rate = cat_params

                # Log-normal price distribution
                unit_price = max(50, np.random.lognormal(
                    np.log(avg_price * spend_mult),
                    0.4
                ))
                unit_price = round(unit_price, 2)

                quantity = np.random.choice(
                    [1, 2, 3, 4, 5],
                    p=[0.50, 0.25, 0.13, 0.07, 0.05]
                )

                revenue = round(unit_price * quantity, 2)

                # Discount: 70% no discount, rest 5-40%
                if np.random.random() < 0.30:
                    discount_pct = round(np.random.uniform(5, 40), 1)
                else:
                    discount_pct = 0.0

                # Returns
                is_return = 1 if np.random.random() < return_rate else 0

                # COGS
                cost_of_goods = round(revenue * np.random.uniform(
                    cogs_pct - 0.05, cogs_pct + 0.05
                ), 2)

                product_id = f"P{np.random.randint(1, 50):03d}_{cat[:3].upper()}"

                all_transactions.append({
                    "transaction_id": f"T{txn_id_counter}",
                    "customer_id": cid,
                    "order_date": order_date.strftime("%Y-%m-%d"),
                    "product_category": cat,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "revenue": revenue,
                    "discount_pct": discount_pct,
                    "is_return": is_return,
                    "cost_of_goods": cost_of_goods,
                })
                txn_id_counter += 1

    transactions = pd.DataFrame(all_transactions)
    print(f"  Generated {len(transactions)} transaction rows.")
    return transactions


def generate_engagement(customers):
    """Generate engagement metrics table correlated with behavior profiles."""
    print(f"  Generating engagement data...")

    engagement_rows = []

    for _, cust in customers.iterrows():
        profile = cust["behavior_profile"]
        engage_mult = PROFILES[profile][3]

        # Base engagement scaled by profile multiplier
        emails = max(0, int(np.random.poisson(8 * engage_mult)))
        website = max(0, int(np.random.poisson(20 * engage_mult)))
        clicks = max(0, int(np.random.poisson(5 * engage_mult)))
        app = max(0, int(np.random.poisson(15 * engage_mult)))
        tickets = max(0, int(np.random.poisson(1)))
        loyalty = 1 if np.random.random() < (0.3 + 0.4 * engage_mult) else 0

        engagement_rows.append({
            "customer_id": cust["customer_id"],
            "emails_opened_30d": min(emails, 25),
            "website_visits_30d": min(website, 60),
            "campaign_clicks_30d": min(clicks, 20),
            "app_sessions_30d": min(app, 50),
            "support_tickets": min(tickets, 8),
            "loyalty_program": loyalty,
        })

    return pd.DataFrame(engagement_rows)


def run():
    """Generate and save all datasets."""
    print("\n" + "="*60)
    print("PHASE 2: Dataset Generation")
    print("="*60)

    customers = generate_customers()
    transactions = generate_transactions(customers)
    engagement = generate_engagement(customers)

    # Save to CSV
    cust_path = os.path.join(config.DATA_RAW, "customers.csv")
    txn_path = os.path.join(config.DATA_RAW, "transactions.csv")
    eng_path = os.path.join(config.DATA_RAW, "engagement.csv")

    customers.to_csv(cust_path, index=False)
    transactions.to_csv(txn_path, index=False)
    engagement.to_csv(eng_path, index=False)

    print(f"\n  ✓ Customers:    {len(customers):>6} rows → {cust_path}")
    print(f"  ✓ Transactions: {len(transactions):>6} rows → {txn_path}")
    print(f"  ✓ Engagement:   {len(engagement):>6} rows → {eng_path}")

    return customers, transactions, engagement


if __name__ == "__main__":
    run()
