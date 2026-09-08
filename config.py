"""
Global configuration for Customer Retention Analytics Pipeline.
All constants, paths, and parameters are defined here for consistency.
"""

import os
from datetime import datetime

# ─── Paths ───────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_RAW = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_PROCESSED = os.path.join(PROJECT_ROOT, "data", "processed")
OUTPUT_FIGURES = os.path.join(PROJECT_ROOT, "outputs", "figures")
OUTPUT_MODELS = os.path.join(PROJECT_ROOT, "outputs", "models")
OUTPUT_POWERBI = os.path.join(PROJECT_ROOT, "outputs", "powerbi")

# Create directories
for d in [DATA_RAW, DATA_PROCESSED, OUTPUT_FIGURES, OUTPUT_MODELS, OUTPUT_POWERBI]:
    os.makedirs(d, exist_ok=True)

# ─── Random Seed ─────────────────────────────────────────────────────────
RANDOM_SEED = 42

# ─── Currency ────────────────────────────────────────────────────────────
CURRENCY_SYMBOL = "₹"

# ─── Date Configuration ─────────────────────────────────────────────────
# 18-month transaction window
TRANSACTION_START = datetime(2024, 1, 1)
TRANSACTION_END = datetime(2025, 6, 30)

# Analysis date: the "today" for computing recency, features, etc.
ANALYSIS_DATE = datetime(2025, 7, 1)

# Churn prediction: observation/prediction split
CHURN_WINDOW_DAYS = 90
CHURN_SPLIT_DATE = datetime(2025, 4, 1)  # ANALYSIS_DATE - 90 days

# ─── Dataset Scale ───────────────────────────────────────────────────────
NUM_CUSTOMERS = 5000
AVG_TRANSACTIONS_PER_CUSTOMER = 16  # ~80K total transactions

# ─── Product Categories & Margins ───────────────────────────────────────
PRODUCT_CATEGORIES = {
    # category: (avg_unit_price, price_std, cogs_pct, return_rate)
    "Electronics":  (2500, 1500, 0.60, 0.12),
    "Apparel":      (1200, 800,  0.45, 0.18),
    "Home":         (1800, 1000, 0.50, 0.08),
    "Food":         (300,  200,  0.65, 0.03),
    "Beauty":       (600,  400,  0.40, 0.10),
    "Sports":       (1500, 900,  0.55, 0.07),
    "Books":        (350,  200,  0.70, 0.02),
}

# ─── Acquisition Channels & Costs ───────────────────────────────────────
ACQUISITION_CHANNELS = {
    # channel: (probability, acquisition_cost)
    "Organic":     (0.30, 0),
    "Paid Search": (0.25, 500),
    "Social":      (0.20, 350),
    "Referral":    (0.15, 200),
    "Email":       (0.10, 150),
}

# ─── Regions ─────────────────────────────────────────────────────────────
REGIONS = ["North", "South", "East", "West", "Central"]

# ─── Intervention Costs (Phase 7) ───────────────────────────────────────
INTERVENTION_COSTS = {
    "High Value":   500,   # Personal outreach + premium offer
    "Medium Value": 200,   # Targeted email campaign + discount
    "Low Value":    50,    # Automated email sequence
}

# ─── Retention Success Probabilities (Phase 7) ──────────────────────────
RETENTION_SUCCESS_PROB = {
    "Champions":           0.70,
    "Loyal Customers":     0.65,
    "Potential Loyalists":  0.60,
    "At Risk":             0.50,
    "High Value At Risk":  0.45,
    "Needs Attention":     0.40,
    "Dormant":             0.20,
}

# ─── Retention Priority Weights (Phase 7) ───────────────────────────────
PRIORITY_WEIGHTS = {
    "value":       0.40,
    "churn_risk":  0.35,
    "net_benefit": 0.25,
}

# ─── Profitability Constants (Phase 5) ──────────────────────────────────
RETURN_PROCESSING_COST = 50     # ₹ per return
SERVICE_COST_PER_TICKET = 100   # ₹ per support ticket

# ─── Feature Engineering Windows ─────────────────────────────────────────
TREND_WINDOW_DAYS = 90  # For spending/frequency trend calculation

# ─── Engagement Score Weights ────────────────────────────────────────────
ENGAGEMENT_WEIGHTS = {
    "emails_opened_30d":     0.20,
    "website_visits_30d":    0.30,
    "campaign_clicks_30d":   0.25,
    "app_sessions_30d":      0.25,
}

# ─── ML Configuration ───────────────────────────────────────────────────
TEST_SIZE = 0.20
K_MEANS_RANGE = range(3, 9)  # Test k=3..8 for clustering
