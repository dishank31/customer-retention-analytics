# Power BI Dashboard Guide — Customer Retention Analytics

This guide provides the complete blueprint for building a 4-page Power BI dashboard
from the exported CSV files.

---

## Data Import

Import these files into Power BI via **Get Data → Text/CSV**:

| File | Description | Primary Key |
|------|-------------|-------------|
| `customer_master.csv` | One row per customer — all features, scores, segments | `customer_id` |
| `transactions_summary.csv` | Monthly aggregates per customer | `customer_id` + `year_month` |
| `retention_decisions.csv` | Top 100 retention targets with economics | `customer_id` |
| `segment_summary.csv` | Aggregate metrics per segment | `rfm_segment` |

### Relationships
- `customer_master[customer_id]` → `transactions_summary[customer_id]` (1:Many)
- `customer_master[customer_id]` → `retention_decisions[customer_id]` (1:1)
- `customer_master[rfm_segment]` → `segment_summary[rfm_segment]` (Many:1)

### Date Table
Create a calendar table for time intelligence:
```dax
DateTable = 
ADDCOLUMNS(
    CALENDAR(DATE(2024,1,1), DATE(2025,6,30)),
    "Year", YEAR([Date]),
    "Month", MONTH([Date]),
    "MonthName", FORMAT([Date], "MMM YYYY"),
    "Quarter", "Q" & FORMAT([Date], "Q YYYY")
)
```

---

## Page 1 — Executive Overview

### KPI Cards (Top Row)

```dax
Total Customers = COUNTROWS(customer_master)

Active Customers = 
CALCULATE(
    COUNTROWS(customer_master),
    customer_master[churn_predicted] = 0
)

At-Risk Customers = 
CALCULATE(
    COUNTROWS(customer_master),
    customer_master[churn_prob] >= 0.5
)

Total Revenue = SUM(customer_master[gross_revenue])

Total Profit = SUM(customer_master[customer_profit])

Profit At Risk = 
CALCULATE(
    SUM(customer_master[expected_retention_value]),
    customer_master[churn_prob] >= 0.5
)
```

### Visuals

| Visual | Type | Fields |
|--------|------|--------|
| Customer Value Distribution | Donut Chart | Legend: `value_tier`, Values: Count of `customer_id` |
| Churn Risk by Segment | Clustered Bar | Axis: `rfm_segment`, Values: Avg of `churn_prob` |
| Revenue by Segment | Treemap | Group: `rfm_segment`, Values: Sum of `gross_revenue` |
| Top 10 Retention Opportunities | Table | `customer_id`, `customer_profit`, `churn_prob`, `retention_priority_score`, `recommended_action` — Filter: Top N by `retention_priority_score` |

### Color Scheme
- Primary: #2C3E50 (dark blue-gray)
- Accent: #E74C3C (red for risk), #2ECC71 (green for positive)
- Background: #F8F9FA (light gray)

---

## Page 2 — Customer Segmentation

### Visuals

| Visual | Type | Fields |
|--------|------|--------|
| Customer Count by Segment | Stacked Bar | Axis: `rfm_segment`, Values: Count |
| Revenue vs Profit by Segment | Clustered Bar | Axis: `rfm_segment`, Values: Avg `gross_revenue`, Avg `customer_profit` |
| Recency vs Frequency Scatter | Scatter | X: `recency_days`, Y: `frequency`, Legend: `rfm_segment`, Size: `monetary` |
| Segment Profile Table | Matrix | Rows: `rfm_segment`, Values: Avg `recency_days`, `frequency`, `monetary`, `engagement_score`, `profit_margin` |

### DAX Measures

```dax
Avg Recency = AVERAGE(customer_master[recency_days])

Avg Frequency = AVERAGE(customer_master[frequency])

Avg Monetary = AVERAGE(customer_master[monetary])

Avg AOV = AVERAGE(customer_master[avg_order_value])

Segment % = 
DIVIDE(
    COUNTROWS(customer_master),
    CALCULATE(COUNTROWS(customer_master), ALL(customer_master[rfm_segment]))
) * 100
```

### Slicers
- Region
- Acquisition Channel
- Value Tier
- Loyalty Program (Yes/No)

---

## Page 3 — Churn Analytics

### KPI Cards

```dax
Overall Churn Rate = 
DIVIDE(
    CALCULATE(COUNTROWS(customer_master), customer_master[churn_predicted] = 1),
    COUNTROWS(customer_master)
) * 100

Highest Risk Segment = 
TOPN(1,
    SUMMARIZE(customer_master, customer_master[rfm_segment],
        "AvgChurn", AVERAGE(customer_master[churn_prob])),
    [AvgChurn], DESC
)
```

### Visuals

| Visual | Type | Fields |
|--------|------|--------|
| Churn Probability Distribution | Histogram | Values: `churn_prob` (bins = 20) |
| Churn Rate by Segment | Bar | Axis: `rfm_segment`, Values: Avg `churn_prob` |
| Churn vs Recency | Line | X: `recency_days` (binned), Y: Avg `churn_prob` |
| Churn vs Engagement | Scatter | X: `engagement_score`, Y: `churn_prob` |
| Churn vs Spending Trend | Line | X: `spending_trend` (binned), Y: Avg `churn_prob` |
| Feature Importance | Bar (static image) | Embed `feature_importance.png` or `shap_summary.png` |

### Churn Driver Cards
Create card visuals showing correlations:
```dax
Recency-Churn Correlation = 
// Use Python visual or pre-computed value from model output
// Higher recency → Higher churn probability

Engagement-Churn Correlation =
// Lower engagement → Higher churn probability
```

---

## Page 4 — Retention Decision Dashboard 🔥

**This is the money page.**

### KPI Cards

```dax
Total Expected Retention Value = 
SUM(customer_master[expected_retention_value])

Retention Budget Needed = 
CALCULATE(
    SUM(customer_master[intervention_cost]),
    customer_master[expected_net_benefit] > 0
)

Expected ROI = 
DIVIDE(
    CALCULATE(SUM(customer_master[expected_net_benefit]), 
              customer_master[expected_net_benefit] > 0),
    CALCULATE(SUM(customer_master[intervention_cost]),
              customer_master[expected_net_benefit] > 0)
) * 100

Positive ROI Customers = 
CALCULATE(
    COUNTROWS(customer_master),
    customer_master[expected_net_benefit] > 0
)
```

### Main Visuals

| Visual | Type | Fields |
|--------|------|--------|
| Profit vs Churn Risk (Bubble) | Scatter | X: `churn_prob`, Y: `customer_profit`, Size: `retention_priority_score`, Color: `value_tier` |
| Decision Matrix Heatmap | Matrix | Rows: `value_tier`, Columns: `risk_tier`, Values: Count, Conditional formatting by `avg_priority` |
| Top Retention Targets | Table from `retention_decisions.csv` | `priority_rank`, `customer_id`, `customer_profit`, `churn_prob`, `expected_retention_value`, `intervention_cost`, `expected_net_benefit`, `retention_priority_score`, `recommended_action` |
| Actions Distribution | Donut | Legend: `recommended_action`, Values: Count |

### Conditional Formatting
- `retention_priority_score`: Color scale Red (high) → Yellow → Green (low)
- `churn_prob`: Color scale Green (low) → Red (high)
- `expected_net_benefit`: Red for negative, Green for positive
- `priority_rank`: Data bars

### Slicers
- Value Tier (High/Medium/Low)
- Risk Tier (High/Medium/Low)
- RFM Segment
- Recommended Action
- Priority Score range slider

---

## General Design Guidelines

1. **Theme**: Use a dark or semi-dark theme for professional appearance
2. **Font**: Segoe UI or DIN (Power BI defaults)
3. **Grid**: Use a 12-column grid layout
4. **KPI Cards**: Place at the top of each page
5. **Tooltips**: Add custom tooltips showing customer detail on hover
6. **Bookmarks**: Create bookmarks for "High Risk Only" and "Top 50 Targets" views
7. **Drill-through**: Enable drill-through from any segment to individual customer detail

---

## Quick Setup Checklist

- [ ] Import 4 CSV files
- [ ] Create relationships
- [ ] Create Date Table
- [ ] Create DAX measures
- [ ] Build Page 1 (Executive Overview)
- [ ] Build Page 2 (Segmentation)
- [ ] Build Page 3 (Churn Analytics)
- [ ] Build Page 4 (Retention Decisions)
- [ ] Apply conditional formatting
- [ ] Add slicers and filters
- [ ] Apply theme and formatting
- [ ] Test interactions and drill-through
