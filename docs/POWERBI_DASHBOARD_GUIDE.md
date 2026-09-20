# 🎨 Power BI Dashboard Design Guide
## Customer Retention Analytics — Olist E-Commerce

---

## 📊 Dashboard Architecture: 6 Pages

```
┌─────────────────────────────────────────────────────────────┐
│  PAGE 1: Executive Overview          │  PAGE 2: Segmentation │
│  • KPI Cards (4)                     │  • RFM Matrix         │
│  • Revenue Trend (line)              │  • Cluster PCA        │
│  • Churn Alert (bar)                 │  • Segment Profiles   │
│  • Geographic Map                    │  • Revenue Share      │
├─────────────────────────────────────────────────────────────┤
│  PAGE 3: Profitability               │  PAGE 4: Churn Intel  │
│  • Profit Waterfall                  │  • Risk Distribution  │
│  • Pareto Analysis                   │  • Model Performance  │
│  • Cost Breakdown                    │  • SHAP Features      │
│  • Margin by Segment                 │  • Risk by Segment    │
├─────────────────────────────────────────────────────────────┤
│  PAGE 5: Retention Action Center     │  PAGE 6: Geo & Product│
│  • Priority Queue (table)            │  • Brazil State Map   │
│  • Intervention ROI                  │  • Category Revenue   │
│  • Decision Matrix (heatmap)         │  • State Comparison   │
│  • Campaign Budget                   │  • Super Category Mix │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Design System

### Color Palette (Dark Premium Theme)

| Role | Color | Hex |
|------|-------|-----|
| Background (Primary) | Dark Navy | `#0f0f23` |
| Background (Cards) | Deep Blue | `#1a1a3e` |
| Accent 1 (Revenue/Positive) | Emerald | `#2ecc71` |
| Accent 2 (Risk/Negative) | Coral Red | `#e94560` |
| Accent 3 (Engagement) | Royal Blue | `#3498db` |
| Accent 4 (Warning) | Amber | `#f39c12` |
| Accent 5 (Neutral) | Purple | `#9b59b6` |
| Text (Primary) | White | `#ffffff` |
| Text (Secondary) | Light Gray | `#b0b0c8` |
| Borders | Subtle Gray | `#2a2a4a` |

### Typography
- **Headers**: Segoe UI Semibold, 16-20pt
- **KPI Values**: Segoe UI Bold, 28-36pt
- **Body**: Segoe UI, 10-12pt
- **Labels**: Segoe UI Light, 9pt

### Card Styling
- Border radius: 8px
- Shadow: 0 2px 8px rgba(0,0,0,0.3)
- Padding: 16px
- Background: `#1a1a3e` with subtle gradient

---

## 📁 Data Model Setup

### Step 1: Import Tables

Load from `outputs/powerbi/`:
1. **customer_master** — Primary fact table (~97K rows)
2. **transactions_summary** — Time-series monthly data
3. **retention_decisions** — Top 100 priority targets
4. **segment_summary** — Segment-level aggregates
5. **date_dimension** — Calendar table for time intelligence
6. **geographic_summary** — State/region metrics
7. **category_performance** — Product category stats

### Step 2: Create Relationships

```
date_dimension[year_month]  ─── transactions_summary[year_month]  (1:M)
customer_master[customer_id] ──< transactions_summary[customer_id] (1:M)
customer_master[customer_id] ─── retention_decisions[customer_id]  (1:1)
customer_master[rfm_segment] >── segment_summary[rfm_segment]     (M:1)
```

### Step 3: Set Data Types

| Column | Type |
|--------|------|
| customer_id | Text |
| order_date, signup_date | Date |
| revenue, profit, cost fields | Decimal Number |
| churn_prob, profit_margin | Decimal (0-1) |
| frequency, age, recency_days | Whole Number |
| rfm_segment, value_tier, region | Text |

---

## 📐 PAGE 1: Executive Overview

### Layout
```
┌──────────────────────────────────────────────────────────────────┐
│  🏢 CUSTOMER RETENTION DASHBOARD              [Date Slicer ▼]   │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │ TOTAL REV  │ │ ACTIVE     │ │ CHURN RISK │ │ AVG PROFIT │   │
│  │ R$ 15.4M   │ │ 84,392     │ │ 23.4%      │ │ R$ 45.20   │   │
│  │ ▲ +12% MoM │ │ ▼ -3% MoM │ │ ▲ +2.1pp   │ │ ▲ +5% MoM  │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│                                                                  │
│  ┌──────────────────────────────┐  ┌───────────────────────────┐ │
│  │  MONTHLY REVENUE TREND       │  │ CHURN RISK BY SEGMENT     │ │
│  │  [Area Chart + Line]         │  │ [Horizontal Bar]          │ │
│  │  X: year_month               │  │                           │ │
│  │  Y: total_revenue            │  │ Champions      ████ 5%    │ │
│  │  Line: order_count           │  │ Loyal        █████ 8%     │ │
│  │                              │  │ At Risk    ████████ 35%   │ │
│  └──────────────────────────────┘  └───────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────┐  ┌───────────────────────────┐ │
│  │  TOP 10 ALERTS               │  │ ACQUISITION CHANNEL MIX   │ │
│  │  [Table — conditional fmt]   │  │ [Donut Chart]             │ │
│  │  Priority | ID | Risk | Act  │  │                           │ │
│  └──────────────────────────────┘  └───────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### DAX Measures

```dax
// ── KPI Cards ──────────────────────────────────────────

Total Revenue =
    SUM(customer_master[gross_revenue])

Active Customers =
    COUNTROWS(FILTER(customer_master, customer_master[churn_predicted] = 0))

Overall Churn Rate =
    DIVIDE(
        COUNTROWS(FILTER(customer_master, customer_master[churn_predicted] = 1)),
        COUNTROWS(customer_master),
        0
    )

Avg Customer Profit =
    AVERAGE(customer_master[customer_profit])

Total Customers =
    COUNTROWS(customer_master)

// ── Revenue Formatting ─────────────────────────────────

Revenue Formatted =
    VAR rev = [Total Revenue]
    RETURN IF(rev >= 1000000, FORMAT(rev / 1000000, "R$ #,##0.0M"),
           IF(rev >= 1000, FORMAT(rev / 1000, "R$ #,##0.0K"),
           FORMAT(rev, "R$ #,##0")))

// ── Churn Rate Formatted ───────────────────────────────

Churn Rate % =
    FORMAT([Overall Churn Rate], "0.0%")
```

---

## 📐 PAGE 2: Customer Segmentation

### Layout
```
┌──────────────────────────────────────────────────────────────────┐
│  📊 SEGMENTATION ANALYSIS                    [Segment Slicer ▼]  │
├──────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────┐  ┌───────────────────────────┐ │
│  │  RFM SEGMENT DISTRIBUTION    │  │ SEGMENT PROFILE RADAR     │ │
│  │  [Stacked Bar — horizontal]  │  │ [Radar/Spider Chart]      │ │
│  │  Y: rfm_segment              │  │ Axes: Recency, Frequency  │ │
│  │  X: customer_count           │  │   Monetary, Engagement    │ │
│  │  Color: value_tier           │  │   Profit                  │ │
│  └──────────────────────────────┘  └───────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────┐  ┌───────────────────────────┐ │
│  │  REVENUE vs FREQUENCY        │  │ SEGMENT METRICS TABLE     │ │
│  │  [Scatter Plot]              │  │ [Matrix — conditional fmt]│ │
│  │  X: frequency                │  │ Segment | Count | Rev |   │ │
│  │  Y: monetary                 │  │         Profit | Churn    │ │
│  │  Size: engagement_score      │  │                           │ │
│  │  Color: rfm_segment          │  │                           │ │
│  └──────────────────────────────┘  └───────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### DAX Measures

```dax
// ── Segment Metrics ────────────────────────────────────

Segment Revenue Share =
    DIVIDE(
        SUM(customer_master[gross_revenue]),
        CALCULATE(SUM(customer_master[gross_revenue]), ALL(customer_master[rfm_segment])),
        0
    )

Segment Avg Engagement =
    AVERAGE(customer_master[engagement_score])

Segment Customer Count =
    COUNTROWS(customer_master)

Segment Pct =
    DIVIDE([Segment Customer Count],
           CALCULATE(COUNTROWS(customer_master), ALL(customer_master[rfm_segment])),
           0)
```

---

## 📐 PAGE 3: Profitability Deep Dive

### Layout
```
┌──────────────────────────────────────────────────────────────────┐
│  💰 PROFITABILITY ANALYSIS                   [Value Tier ▼]      │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │ TOTAL      │ │ AVG MARGIN │ │ UNPROFITABLE│ │ TOP 20%    │   │
│  │ PROFIT     │ │            │ │ CUSTOMERS   │ │ SHARE      │   │
│  │ R$ 2.1M    │ │ 14.2%      │ │ 12,340      │ │ 78%        │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│                                                                  │
│  ┌──────────────────────────────┐  ┌───────────────────────────┐ │
│  │  PROFIT DISTRIBUTION          │  │ COST BREAKDOWN            │ │
│  │  [Histogram]                  │  │ [Waterfall Chart]         │ │
│  │  X: customer_profit bins      │  │ Revenue → COGS →          │ │
│  │  Y: count                     │  │ Discounts → Returns →     │ │
│  │  Ref line: break-even (0)     │  │ Service → Acquisition →   │ │
│  │                               │  │ = Profit                  │ │
│  └──────────────────────────────┘  └───────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  PROFIT BY SEGMENT × VALUE TIER                              │ │
│  │  [Clustered Bar Chart]                                       │ │
│  │  X: rfm_segment    Color: value_tier                         │ │
│  │  Y: avg_profit                                               │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### DAX Measures

```dax
Total Profit =
    SUM(customer_master[customer_profit])

Avg Profit Margin =
    AVERAGE(customer_master[profit_margin])

Unprofitable Count =
    COUNTROWS(FILTER(customer_master, customer_master[customer_profit] < 0))

Unprofitable Pct =
    DIVIDE([Unprofitable Count], [Total Customers], 0)

// ── Cost Components ────────────────────────────────────

Total COGS = SUM(customer_master[total_cogs])
Total Discount Cost = SUM(customer_master[total_discount_cost])
Total Return Cost = SUM(customer_master[return_cost])
Total Service Cost = SUM(customer_master[service_cost])
Total Acquisition Cost = SUM(customer_master[acquisition_cost])
```

---

## 📐 PAGE 4: Churn Intelligence

### Layout
```
┌──────────────────────────────────────────────────────────────────┐
│  🤖 CHURN INTELLIGENCE                      [Risk Tier ▼]       │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │ PREDICTED  │ │ HIGH RISK  │ │ AT-RISK    │ │ BEST MODEL │   │
│  │ CHURNERS   │ │ COUNT      │ │ REVENUE    │ │ AUC-ROC    │   │
│  │ 22,450     │ │ 8,120      │ │ R$ 4.2M    │ │ 0.847      │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│                                                                  │
│  ┌──────────────────────────────┐  ┌───────────────────────────┐ │
│  │  CHURN PROBABILITY DIST      │  │ CHURN RATE BY SEGMENT     │ │
│  │  [Histogram]                  │  │ [Bar Chart — conditional] │ │
│  │  X: churn_prob (bins)         │  │ Color: red>50%, amber>30% │ │
│  │  Ref: 0.5 threshold          │  │        green<30%          │ │
│  └──────────────────────────────┘  └───────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────┐  ┌───────────────────────────┐ │
│  │  CHURN DRIVERS (SHAP)         │  │ HIGH VALUE AT RISK LIST   │ │
│  │  [Image: shap_summary.png]    │  │ [Table — top 20]          │ │
│  │  Or: feature importance bars  │  │ ID | Profit | Risk | Act  │ │
│  └──────────────────────────────┘  └───────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### DAX Measures

```dax
Predicted Churners =
    COUNTROWS(FILTER(customer_master, customer_master[churn_predicted] = 1))

High Risk Count =
    COUNTROWS(FILTER(customer_master, customer_master[churn_prob] >= 0.6))

At Risk Revenue =
    CALCULATE(
        SUM(customer_master[gross_revenue]),
        customer_master[churn_prob] >= 0.5
    )

Revenue at Risk % =
    DIVIDE([At Risk Revenue], [Total Revenue], 0)
```

---

## 📐 PAGE 5: Retention Action Center

### Layout
```
┌──────────────────────────────────────────────────────────────────┐
│  🎯 RETENTION ACTION CENTER                 [Action Slicer ▼]   │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │ POSITIVE   │ │ TOTAL      │ │ EXPECTED   │ │ CAMPAIGN   │   │
│  │ ROI CUSTS  │ │ BUDGET     │ │ RETURN     │ │ ROI        │   │
│  │ 34,200     │ │ R$ 450K    │ │ R$ 1.2M    │ │ 267%       │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  RETENTION PRIORITY QUEUE                                    │ │
│  │  [Table — sortable, filterable]                              │ │
│  │  Rank | Customer | Profit | Risk | Net Benefit | Action      │ │
│  │  Conditional formatting: gradient on priority_score          │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────┐  ┌───────────────────────────┐ │
│  │  DECISION MATRIX (HEATMAP)    │  │ ACTION DISTRIBUTION       │ │
│  │  [Matrix — conditional fmt]   │  │ [Pie/Donut Chart]         │ │
│  │  Rows: value_tier             │  │ Segments: recommended_    │ │
│  │  Cols: risk_tier              │  │           action          │ │
│  │  Values: customer_count       │  │                           │ │
│  └──────────────────────────────┘  └───────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### DAX Measures

```dax
Positive ROI Customers =
    COUNTROWS(FILTER(customer_master, customer_master[expected_net_benefit] > 0))

Total Intervention Budget =
    CALCULATE(
        SUM(customer_master[intervention_cost]),
        customer_master[expected_net_benefit] > 0
    )

Expected Return =
    CALCULATE(
        SUM(customer_master[expected_retention_value]),
        customer_master[expected_net_benefit] > 0
    )

Campaign ROI =
    DIVIDE([Expected Return] - [Total Intervention Budget],
           [Total Intervention Budget], 0)

Campaign ROI % =
    FORMAT([Campaign ROI], "0%")

Total ERV =
    SUM(customer_master[expected_retention_value])
```

---

## 📐 PAGE 6: Geographic & Product Analysis

### Layout
```
┌──────────────────────────────────────────────────────────────────┐
│  🌎 GEOGRAPHIC & PRODUCT ANALYSIS           [Region Slicer ▼]   │
├──────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  BRAZIL STATE MAP                                            │ │
│  │  [Filled Map / Shape Map]                                    │ │
│  │  Location: customer_state                                    │ │
│  │  Color saturation: total_revenue  (or avg_churn_prob)        │ │
│  │  Tooltip: customer_count, total_revenue, avg_profit          │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────┐  ┌───────────────────────────┐ │
│  │  REVENUE BY SUPER CATEGORY    │  │ TOP STATES TABLE          │ │
│  │  [Treemap or Stacked Bar]     │  │ [Table — conditional fmt] │ │
│  │  Category: super_category     │  │ State | Customers | Rev | │ │
│  │  Value: total_revenue         │  │        Profit | Churn     │ │
│  │  Color: return_rate           │  │                           │ │
│  └──────────────────────────────┘  └───────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### DAX Measures

```dax
State Revenue =
    SUM(geographic_summary[total_revenue])

State Customer Count =
    SUM(geographic_summary[customer_count])

Category Return Rate =
    AVERAGE(category_performance[return_rate])
```

---

## 🎨 Conditional Formatting Rules

### Churn Probability
| Range | Color | Icon |
|-------|-------|------|
| 0 – 0.3 | `#2ecc71` (Green) | ✅ |
| 0.3 – 0.6 | `#f39c12` (Amber) | ⚠️ |
| 0.6 – 1.0 | `#e94560` (Red) | 🔴 |

### Profit Margin
| Range | Color |
|-------|-------|
| < 0% | `#e94560` (Red) |
| 0% – 15% | `#f39c12` (Amber) |
| > 15% | `#2ecc71` (Green) |

### Priority Score
| Range | Color |
|-------|-------|
| 0 – 33 | Light Gray |
| 33 – 66 | Amber gradient |
| 66 – 100 | Red gradient (urgent) |

---

## ✅ Implementation Checklist

### Setup (15 min)
- [ ] Import all 7 CSV files from `outputs/powerbi/`
- [ ] Set correct data types for each column
- [ ] Create relationships between tables
- [ ] Mark `date_dimension` as the date table

### Page 1: Executive Overview (30 min)
- [ ] Create 4 KPI cards with DAX measures
- [ ] Build monthly revenue trend (area + line combo)
- [ ] Build churn risk by segment (bar chart)
- [ ] Add top 10 alerts table
- [ ] Add date slicer

### Page 2: Segmentation (30 min)
- [ ] Build RFM segment distribution (stacked bar)
- [ ] Build revenue vs frequency scatter
- [ ] Build segment metrics matrix with conditional formatting
- [ ] Add segment slicer

### Page 3: Profitability (30 min)
- [ ] Create 4 profit KPI cards
- [ ] Build profit distribution histogram
- [ ] Build cost breakdown waterfall
- [ ] Build profit by segment × value tier

### Page 4: Churn Intelligence (20 min)
- [ ] Create churn KPI cards
- [ ] Build churn probability histogram
- [ ] Build churn rate by segment (conditional colors)
- [ ] Add SHAP image or feature importance bars
- [ ] Build high-value at-risk table

### Page 5: Retention Action Center (30 min)
- [ ] Create ROI KPI cards
- [ ] Build priority queue table (sortable)
- [ ] Build decision matrix heatmap
- [ ] Build action distribution donut

### Page 6: Geo & Product (20 min)
- [ ] Add Brazil state map visual
- [ ] Build category treemap
- [ ] Build state comparison table
- [ ] Add region slicer

### Polish (15 min)
- [ ] Apply dark theme and color palette
- [ ] Add conditional formatting to all tables
- [ ] Configure tooltips on all visuals
- [ ] Add page navigation buttons
- [ ] Test all slicers and cross-filtering

---

## 💡 Pro Tips for Stunning Dashboards

1. **Use a dark background** (`#0f0f23`) — makes data pop and looks premium
2. **Limit each page to 6-8 visuals** — avoid clutter
3. **Use consistent colors** across all pages for segments/tiers
4. **Add subtle borders** (`#2a2a4a`) around cards instead of harsh lines
5. **Use icons in KPI cards** (▲ for increase, ▼ for decrease)
6. **Apply gradient backgrounds** to cards for depth
7. **Add page-level tooltips** for detailed customer drill-through
8. **Use bookmarks** for toggle views (e.g., switch between RFM and K-Means)
9. **Create a mobile layout** for each page
10. **Add a "Last Refreshed" timestamp** in the footer
