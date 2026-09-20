"""
Global configuration for Customer Retention Analytics Pipeline.
All constants, paths, and parameters are defined here for consistency.

Dataset: Olist Brazilian E-Commerce (Kaggle)
Period:  September 2016 – August 2018
"""

import os
from datetime import datetime

# ─── Paths ───────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_RAW = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_OLIST_RAW = os.path.join(DATA_RAW, "olist")
DATA_PROCESSED = os.path.join(PROJECT_ROOT, "data", "processed")
OUTPUT_FIGURES = os.path.join(PROJECT_ROOT, "outputs", "figures")
OUTPUT_MODELS = os.path.join(PROJECT_ROOT, "outputs", "models")
OUTPUT_POWERBI = os.path.join(PROJECT_ROOT, "outputs", "powerbi")
NOTEBOOKS_DIR = os.path.join(PROJECT_ROOT, "notebooks")

# Create directories
for d in [DATA_RAW, DATA_OLIST_RAW, DATA_PROCESSED,
          OUTPUT_FIGURES, OUTPUT_MODELS, OUTPUT_POWERBI, NOTEBOOKS_DIR]:
    os.makedirs(d, exist_ok=True)

# ─── Random Seed ─────────────────────────────────────────────────────────
RANDOM_SEED = 42

# ─── Currency ────────────────────────────────────────────────────────────
CURRENCY_SYMBOL = "R$"
CURRENCY_NAME = "Brazilian Real"

# ─── Date Configuration ─────────────────────────────────────────────────
# Olist dataset spans: September 2016 – August 2018
TRANSACTION_START = datetime(2016, 9, 1)
TRANSACTION_END = datetime(2018, 8, 31)

# Analysis date: the "today" for computing recency, features, etc.
ANALYSIS_DATE = datetime(2018, 9, 1)

# Churn prediction: observation/prediction split
CHURN_WINDOW_DAYS = 90
CHURN_SPLIT_DATE = datetime(2018, 6, 1)  # ANALYSIS_DATE - 90 days

# ─── Olist Files ─────────────────────────────────────────────────────────
OLIST_FILES = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "products": "olist_products_dataset.csv",
    "category_translation": "olist_product_category_name_translation.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
}

# Files that are required (pipeline cannot run without them)
OLIST_REQUIRED_FILES = [
    "customers", "orders", "order_items", "payments",
    "products", "category_translation",
]

# Files that are optional (enhance analysis but not mandatory)
OLIST_OPTIONAL_FILES = ["reviews", "sellers", "geolocation"]

# ─── Product Super-Categories ───────────────────────────────────────────
# Maps Olist's 70+ categories to ~12 business-friendly super-categories
PRODUCT_SUPER_CATEGORIES = {
    # Electronics & Tech
    "computers_accessories": "Electronics",
    "computers": "Electronics",
    "electronics": "Electronics",
    "tablets_printing_image": "Electronics",
    "telephony": "Electronics",
    "fixed_telephony": "Electronics",
    "consoles_games": "Electronics",
    "audio": "Electronics",
    "signaling_and_security": "Electronics",
    "security_and_services": "Electronics",
    "pc_gamer": "Electronics",
    "small_appliances": "Electronics",
    "small_appliances_home_oven_and_coffee": "Electronics",
    "portable_kitchen_food_processors": "Electronics",
    "air_conditioning": "Electronics",

    # Fashion & Apparel
    "fashion_bags_accessories": "Fashion",
    "fashion_shoes": "Fashion",
    "fashion_male_clothing": "Fashion",
    "fashion_underwear_beach": "Fashion",
    "fashion_sport": "Fashion",
    "fashio_female_clothing": "Fashion",
    "fashion_childrens_clothes": "Fashion",
    "luggage_accessories": "Fashion",
    "watches_gifts": "Fashion",
    "cool_stuff": "Fashion",

    # Home & Furniture
    "furniture_decor": "Home & Living",
    "furniture_living_room": "Home & Living",
    "furniture_bedroom": "Home & Living",
    "furniture_mattress_and_upholstery": "Home & Living",
    "home_confort": "Home & Living",
    "home_comfort_2": "Home & Living",
    "home_construction": "Home & Living",
    "garden_tools": "Home & Living",
    "housewares": "Home & Living",
    "kitchen_dining_laundry_garden_furniture": "Home & Living",
    "costruction_tools_garden": "Home & Living",
    "construction_tools_construction": "Home & Living",
    "construction_tools_lights": "Home & Living",
    "construction_tools_safety": "Home & Living",
    "costruction_tools_tools": "Home & Living",
    "la_cuisine": "Home & Living",
    "flowers": "Home & Living",

    # Health & Beauty
    "health_beauty": "Health & Beauty",
    "perfumery": "Health & Beauty",
    "diapers_and_hygiene": "Health & Beauty",

    # Sports & Leisure
    "sports_leisure": "Sports & Leisure",

    # Baby & Kids
    "baby": "Baby & Kids",
    "toys": "Baby & Kids",
    "christmas_supplies": "Baby & Kids",

    # Books & Media
    "books_general_interest": "Books & Media",
    "books_technical": "Books & Media",
    "books_imported": "Books & Media",
    "dvds_blu_ray": "Books & Media",
    "cds_dvds_musicals": "Books & Media",
    "cine_photo": "Books & Media",
    "music": "Books & Media",
    "musical_instruments": "Books & Media",
    "arts_and_craftmanship": "Books & Media",
    "art": "Books & Media",

    # Food & Drink
    "food_drink": "Food & Drink",
    "food": "Food & Drink",
    "drinks": "Food & Drink",

    # Auto & Industry
    "auto": "Auto & Industry",
    "industry_commerce_and_business": "Auto & Industry",
    "construction_tools_tools": "Auto & Industry",

    # Office & Stationery
    "office_furniture": "Office & Stationery",
    "stationery": "Office & Stationery",

    # Pet
    "pet_shop": "Pet Shop",

    # Bed, Bath & Table
    "bed_bath_table": "Bed, Bath & Table",
    "market_place": "Bed, Bath & Table",
}

# Default super-category for unmapped categories
DEFAULT_SUPER_CATEGORY = "Other"

# ─── Brazilian Regions ───────────────────────────────────────────────────
BRAZILIAN_REGIONS = {
    "SP": "Southeast", "RJ": "Southeast", "MG": "Southeast", "ES": "Southeast",
    "PR": "South", "SC": "South", "RS": "South",
    "BA": "Northeast", "PE": "Northeast", "CE": "Northeast",
    "MA": "Northeast", "AL": "Northeast", "RN": "Northeast",
    "PB": "Northeast", "SE": "Northeast", "PI": "Northeast",
    "PA": "North", "AM": "North", "RO": "North",
    "TO": "North", "AC": "North", "AP": "North", "RR": "North",
    "GO": "Central-West", "DF": "Central-West",
    "MT": "Central-West", "MS": "Central-West",
}

REGIONS = ["Southeast", "South", "Northeast", "North", "Central-West"]

# ─── Acquisition Channels (synthetic proxy) ─────────────────────────────
ACQUISITION_CHANNELS = {
    # channel: (probability, acquisition_cost_BRL)
    "Organic":     (0.30, 0),
    "Paid Search": (0.25, 50),
    "Social":      (0.20, 35),
    "Referral":    (0.15, 20),
    "Email":       (0.10, 15),
}

# ─── Intervention Costs (Phase 7) ───────────────────────────────────────
INTERVENTION_COSTS = {
    "High Value":   50,    # Personal outreach + premium offer (BRL)
    "Medium Value": 20,    # Targeted email campaign + discount
    "Low Value":    5,     # Automated email sequence
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
DEFAULT_COGS_PERCENT = 0.55       # Default cost of goods sold (55%)
RETURN_PROCESSING_COST = 5        # BRL per return
SERVICE_COST_PER_TICKET = 10      # BRL per support ticket

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
