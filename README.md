# Customer Retention Analytics Pipeline

An end-to-end analytics pipeline that transforms raw transactional data into actionable retention decisions, combining customer segmentation, profitability analysis, churn prediction, and economically-grounded retention prioritization.

## Business Problem

An e-commerce company wants to identify customers who are both **economically valuable** and at **meaningful risk of churn**, with limited resources for retention campaigns.

This requires three dimensions:
- **Customer Value** — Who generates the most profit?
- **Churn Risk** — Who is likely to leave?
- **Intervention Cost** — Is it worth the investment?

## Pipeline Phases

| Phase | Module | Description |
|-------|--------|-------------|
| 1 | — | Business Problem Definition |
| 2 | `data_generation.py` | Synthetic dataset (5K customers, ~80K transactions) |
| 3 | `feature_engineering.py` | 25+ customer features (RFM + behavioral + trends) |
| 4 | `segmentation.py` | Rule-based RFM + K-Means clustering comparison |
| 5 | `profitability.py` | Customer profit = Revenue − COGS − Discounts − Returns − Service |
| 6 | `churn_model.py` | 4 ML models + SHAP explainability |
| 7 | `retention_priority.py` | Priority scoring + sensitivity analysis + decision matrix |
| 8 | `export_powerbi.py` | Power BI-ready CSV exports + dashboard guide |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline
python main.py

# Or run from a specific phase
python main.py --phase 6  # Re-run from churn prediction onwards
```

## Output Structure

```
data/
├── raw/                    # Generated synthetic CSVs
│   ├── customers.csv
│   ├── transactions.csv
│   └── engagement.csv
└── processed/              # Feature-engineered outputs
    ├── customer_features.csv
    ├── customer_segmented.csv
    ├── customer_profitable.csv
    ├── customer_churn.csv
    └── customer_retention_final.csv

outputs/
├── figures/                # Charts & visualizations
├── models/                 # Trained ML model + scaler
└── powerbi/                # Power BI-ready exports
    ├── customer_master.csv
    ├── transactions_summary.csv
    ├── retention_decisions.csv
    ├── segment_summary.csv
    └── powerbi_guide.md
```

## Key Features

- **Behavior Profiles**: Synthetic data uses correlated behavior profiles (power_user, regular, occasional, declining, one_time) for realistic patterns
- **Temporal Churn Definition**: Churn defined by 90-day no-purchase window with proper observation/prediction split
- **Dual Segmentation**: Compare rule-based RFM vs K-Means clustering with Adjusted Rand Index
- **Profitability, Not Revenue**: Customer Profit = Revenue − COGS − Discounts − Returns − Service − Acquisition
- **SHAP Explainability**: Understand why individual customers are flagged as high-risk
- **Retention Priority Score**: Transparent formula combining value (40%) + risk (35%) + net benefit (25%)
- **Sensitivity Analysis**: Tests 4 weight configurations and measures top-20 overlap

## Power BI Dashboard

The pipeline exports 4 CSVs optimized for a 4-page Power BI dashboard. See `outputs/powerbi/powerbi_guide.md` for:
- Complete DAX measures
- Visual specifications per page
- Relationship setup
- Conditional formatting rules

## Configuration

All parameters are centralized in `config.py`:
- Date ranges, churn window
- Product categories & margins
- Intervention costs
- Priority score weights
- ML hyperparameters
