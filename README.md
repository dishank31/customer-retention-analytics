# Customer Retention Analytics Pipeline

An end-to-end analytics pipeline that transforms the **Olist Brazilian E-Commerce** dataset into actionable retention decisions, combining customer segmentation, profitability analysis, churn prediction, and economically-grounded retention prioritization — with Power BI-ready exports.

## Business Problem

An e-commerce company wants to identify customers who are both **economically valuable** and at **meaningful risk of churn**, with limited resources for retention campaigns.

This requires three dimensions:
- **Customer Value** — Who generates the most profit?
- **Churn Risk** — Who is likely to leave?
- **Intervention ROI** — Is it worth the investment?

## Dataset

**[Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)** — Real-world transactional data from a Brazilian marketplace.

| Metric | Value |
|--------|-------|
| **Customers** | ~97,000 |
| **Orders** | ~100,000 |
| **Time Period** | Sep 2016 – Aug 2018 |
| **Product Categories** | 70+ (mapped to 12 super-categories) |
| **Currency** | R$ (Brazilian Real) |

## Pipeline Phases

| Phase | Module | Description |
|-------|--------|-------------|
| 1 | `load_olist_data.py` | Olist dataset loading & transformation |
| 2 | `feature_engineering.py` | 25+ customer features (RFM + behavioral + trends) |
| 3 | `segmentation.py` | Rule-based RFM + K-Means clustering comparison |
| 4 | `profitability.py` | Customer profit = Revenue − COGS − Discounts − Returns − Service |
| 5 | `churn_model.py` | 4 ML models + SHAP explainability |
| 6 | `retention_priority.py` | Priority scoring + sensitivity analysis + decision matrix |
| 7 | `export_powerbi.py` | 7 Power BI-ready CSV exports |

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Download Olist Dataset
Download from [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and extract CSV files to:
```
data/raw/olist/
├── olist_customers_dataset.csv
├── olist_orders_dataset.csv
├── olist_order_items_dataset.csv
├── olist_order_payments_dataset.csv
├── olist_products_dataset.csv
├── olist_product_category_name_translation.csv
├── olist_order_reviews_dataset.csv        (optional)
├── olist_sellers_dataset.csv              (optional)
└── olist_geolocation_dataset.csv          (optional)
```

### 3. Run the Pipeline
```bash
python main.py              # Run all phases
python main.py --phase 3    # Re-run from phase 3 onwards
```

### 4. Or Use Notebooks (Recommended)
```bash
jupyter notebook notebooks/
```
Run notebooks `01` through `07` in order for interactive analysis with visualizations.

## Project Structure

```
├── config.py                          # Global configuration
├── main.py                            # Pipeline runner
├── requirements.txt                   # Dependencies
│
├── notebooks/                         # Interactive analysis
│   ├── 01_data_loading_eda.ipynb      # Load + EDA
│   ├── 02_feature_engineering.ipynb   # Feature creation
│   ├── 03_segmentation.ipynb          # RFM + K-Means
│   ├── 04_profitability.ipynb         # Profit analysis
│   ├── 05_churn_prediction.ipynb      # ML models + SHAP
│   ├── 06_retention_priority.ipynb    # Priority scoring
│   └── 07_powerbi_export.ipynb        # Export + validation
│
├── src/                               # Core modules
│   ├── load_olist_data.py
│   ├── feature_engineering.py
│   ├── segmentation.py
│   ├── profitability.py
│   ├── churn_model.py
│   ├── retention_priority.py
│   └── export_powerbi.py
│
├── data/
│   ├── raw/olist/                     # Olist CSVs (user downloads)
│   └── processed/                     # Pipeline outputs
│
├── outputs/
│   ├── figures/                       # Charts & visualizations
│   ├── models/                        # Trained ML models
│   └── powerbi/                       # Power BI exports
│
└── docs/
    ├── POWERBI_DASHBOARD_GUIDE.md     # Dashboard design guide
    └── OLIST_INTEGRATION.md           # Integration notes
```

## Power BI Dashboard

The pipeline exports 7 CSVs to `outputs/powerbi/`:

| Table | Description |
|-------|-------------|
| `customer_master.csv` | Primary table — demographics, RFM, engagement, profitability, churn |
| `transactions_summary.csv` | Monthly aggregates per customer |
| `retention_decisions.csv` | Top 100 priority targets with economics |
| `segment_summary.csv` | Aggregate metrics per segment |
| `date_dimension.csv` | Date table for time intelligence |
| `geographic_summary.csv` | State/region level metrics |
| `category_performance.csv` | Product category performance |

See `docs/POWERBI_DASHBOARD_GUIDE.md` for complete dashboard design, DAX measures, and visual specifications.

## Key Features

- **Real-World Data**: Uses the Olist Brazilian E-Commerce dataset (100K+ orders)
- **Temporal Churn Definition**: 90-day no-purchase window with observation/prediction split
- **Dual Segmentation**: Rule-based RFM vs K-Means clustering with Adjusted Rand Index
- **Profitability, Not Revenue**: Customer Profit = Revenue − COGS − Discounts − Returns − Service − Acquisition
- **SHAP Explainability**: Understand why individual customers are flagged as high-risk
- **Retention Priority Score**: Transparent formula: Value (40%) + Risk (35%) + Net Benefit (25%)
- **Sensitivity Analysis**: Tests 4 weight configurations and measures top-20 overlap
- **Power BI Ready**: 7 optimized export tables with date dimension for time intelligence

## Configuration

All parameters are centralized in `config.py`:
- Date ranges (Olist period: 2016–2018)
- Currency (R$ — Brazilian Real)
- Product super-category mappings
- Brazilian state → region mappings
- Intervention costs and priority weights
- ML hyperparameters
