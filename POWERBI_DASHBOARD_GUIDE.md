# 🎨 Power BI Dashboard Design Guide
## Customer Retention Analytics with Olist E-Commerce Data

---

## 📊 Dashboard Architecture Overview

### **Four-Page Dashboard Structure**

```
┌─────────────────────────────────────────────────────────────┐
│  PAGE 1: Executive Overview          │  PAGE 2: Segmentation │
│  • KPI Cards                         │  • RFM Matrix         │
│  • Revenue Trends                    │  • Cluster Analysis   │
│  • Churn Alerts                      │  • Customer Profiles  │
│  • Geographic Heatmap                │  • Segment Comparison │
├─────────────────────────────────────────────────────────────┤
│  PAGE 3: Profitability Analysis      │  PAGE 4: Action Center│
│  • Profit Distribution               │  • Retention Queue    │
│  • Cost Breakdown                    │  • Intervention ROI   │
│  • Customer Lifetime Value           │  • Campaign Tracker   │
│  • Margin Analysis                   │  • Priority Rankings  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Data Model Setup

### **Step 1: Import CSV Files**

Load these four tables from `outputs/powerbi/`:

1. **customer_master** (Primary table, ~97K rows)
   - Key: `customer_id`
   - Contains: Demographics, RFM, Engagement, Profitability, Churn scores

2. **transactions_summary** (Time-series data)
   - Key: `customer_id` + `year_month`
   - Relationship: Many-to-One with customer_master

3. **retention_decisions** (Top 100 priority customers)
   - Key: `customer_id`
   - Relationship: One-to-One with customer_master

4. **segment_summary** (Aggregated by segment)
   - Key: `rfm_segment`
   - Relationship: One-to-Many with customer_master

### **Step 2: Create Relationships**

```
customer_master (customer_id) ──< transactions_summary (customer_id)
customer_master (customer_id) ── retention_decisions (customer_id)
customer_master (rfm_segment) >── segment_summary (rfm_segment)
```

---

## 🎯 PAGE 1: Executive Overview

### **Layout Wireframe**

```
┌──────────────────────────────────────────────────────────────────┐
│  [Logo] CUSTOMER RETENTION DASHBOARD              [Date Slicer]  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ TOTAL    │  │ ACTIVE   │  │ CHURN    │  │ AVG      │        │
│  │ REVENUE  │  │ CUSTOMERS│  │ RISK     │  │ PROFIT   │        │
│  │ R$ 12.5M │  │ 84,392   │  │ 23.4%    │  │ R$ 145   │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                  │
│  ┌─────────────────────────────┐  ┌──────────────────────────┐  │
│  │                             │  │  CHURN RISK BY SEGMENT   │  │
│  │   MONTHLY REVENUE TREND     │  │  [Horizontal Bar Chart]  │  │
│  │   [Line + Column Chart]     │  │                          │  │
│  │                             │  │  Champions       ████ 5% │  │
│  │                             │  │  Loyal         █████ 8%  │  │
│  │                             │  │  At Risk     ████████ 35%│  │
│  │                             │  │  Dormant     █████████ 45%│ │
│  │                             │  │                          │  │
│  └─────────────────────────────┘  └──────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────┐  ┌──────────────────────────┐  │
│  │                             │  │                          │  │
│  │   GEOGRAPHIC HEATMAP        │  │   TOP ALERTS             │  │
│  │   [Brazil Map Visual]       │  │   [Table]                │  │
│  │                             │  │   Customer | Risk | Value│  │
│  │   Color: Churn Rate %       │  │   C1234    | HIGH | High│  │
│  │                             │  │   C5678    | HIGH | High│  │
│  │                             │  │   ...                    │  │
│  └─────────────────────────────┘  └──────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### **DAX Measures for KPI Cards**

```dax
// Total Revenue
Total Revenue = SUM(customer_master[gross_revenue])

// Active Customers (purchased in last 90 days)
Active Customers = 
CALCULATE(
    DISTINCTCOUNT(customer_master[customer_id]),
    customer_master[recency_days] <= 90
)

// Churn Risk (% with probability > 0.5)
Churn Risk % = 
DIVIDE(
    CALCULATE(
        COUNTROWS(customer_master),
        customer_master[churn_prob] > 0.5
    ),
    COUNTROWS(customer_master),
    0
)

// Average Customer Profit
Avg Customer Profit = AVERAGE(customer_master[customer_profit])

// Total Profit
Total Profit = SUM(customer_master[customer_profit])

// Profit Margin %
Profit Margin % = 
DIVIDE(
    [Total Profit],
    [Total Revenue],
    0
)
```

### **Visual Configurations**

| Visual | Type | Fields | Formatting |
|--------|------|--------|------------|
| KPI Cards | Card | Measures above | Data labels: R$ format, 1 decimal |
| Revenue Trend | Line & Column | year_month, total_revenue, order_count | Dual axis, line for orders |
| Churn by Segment | Bar Chart | rfm_segment, avg_churn_prob | Sort descending, red gradient |
| Geographic Map | Filled Map | customer_state, churn_prob | Color scale: Green-Yellow-Red |
| Top Alerts | Table | customer_id, churn_prob, customer_profit | Conditional formatting on prob |

---

## 🎯 PAGE 2: Customer Segmentation

### **Layout Wireframe**

```
┌──────────────────────────────────────────────────────────────────┐
│  [Back] SEGMENTATION ANALYSIS                     [Segment Slicer]│
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────┐  ┌──────────────────────────┐  │
│  │                             │  │                          │  │
│  │   RFM MATRIX                │  │   SEGMENT METRICS        │  │
│  │   [Scatter Plot]            │  │   [Multi-row Card]       │  │
│  │                             │  │                          │  │
│  │   Y: Frequency              │  │   Count:     12,453      │  │
│  │   X: Recency                │  │   Avg Rev:   R$ 1,234    │  │
│  │   Size: Monetary            │  │   Avg Margin: 18.5%      │  │
│  │   Color: Segment            │  │   Churn Rate: 23%        │  │
│  │                             │  │   Engagement: 45.2       │  │
│  │                             │  │                          │  │
│  └─────────────────────────────┘  └──────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │   SEGMENT COMPARISON (Radar Chart)                        │  │
│  │                                                           │  │
│  │        Revenue                                            │  │
│  │           ╱│╲                                             │  │
│  │      Loyalty ╱ │ ╲ Frequency                              │  │
│  │         ╱   ╱  │  ╲   ╲                                   │  │
│  │        ╱   ╱   │   ╲   ╲                                  │  │
│  │   Engagement────┼──── Recency                              │  │
│  │        ╲   ╲   │   ╱   ╱                                  │  │
│  │         ╲   ╲  │  ╱   ╱                                   │  │
│  │      Margin ╲  │ ╱ Profit                                 │  │
│  │           ╲  │ ╱                                           │  │
│  │              ╲│                                            │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────┐  ┌──────────────────────────┐  │
│  │   CLUSTER DISTRIBUTION      │  │   SEGMENT TRENDS         │  │
│  │   [Donut Chart]             │  │   [Line Chart]           │  │
│  │                             │  │                          │  │
│  │   Champions     12%         │  │   Revenue by month       │  │
│  │   Loyal         23%         │  │   per segment            │  │
│  │   At Risk       28%         │  │                          │  │
│  │   Dormant       18%         │  │                          │  │
│  │   Others        19%         │  │                          │  │
│  │                             │  │                          │  │
│  └─────────────────────────────┘  └──────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### **DAX Measures for Segmentation**

```dax
// Segment Count
Segment Customer Count = DISTINCTCOUNT(customer_master[customer_id])

// Average Revenue by Segment
Avg Revenue by Segment = AVERAGE(customer_master[gross_revenue])

// Average Frequency
Avg Frequency = AVERAGE(customer_master[frequency])

// Average Recency (lower is better)
Avg Recency = AVERAGE(customer_master[recency_days])

// Engagement Score Average
Avg Engagement = AVERAGE(customer_master[engagement_score])

// Segment Profitability
Segment Profit Margin = AVERAGE(customer_master[profit_margin])

// High Value Customers in Segment
High Value Count = 
CALCULATE(
    COUNTROWS(customer_master),
    customer_master[value_tier] = "High Value"
)
```

### **RFM Matrix Scatter Plot Setup**

- **X-Axis**: `recency_days` (invert so lower = right side)
- **Y-Axis**: `frequency`
- **Size**: `monetary`
- **Legend**: `rfm_segment`
- **Tooltips**: customer_id, customer_profit, churn_prob, engagement_score

**Pro Tip**: Create calculated columns for RFM quadrants:
```dax
RFM Quadrant = 
SWITCH(
    TRUE(),
    customer_master[recency_days] <= 30 && customer_master[frequency] >= 10, "Stars",
    customer_master[recency_days] <= 30 && customer_master[frequency] < 10, "Potential",
    customer_master[recency_days] > 90 && customer_master[frequency] >= 5, "At Risk",
    "Dormant"
)
```

---

## 🎯 PAGE 3: Profitability Analysis

### **Layout Wireframe**

```
┌──────────────────────────────────────────────────────────────────┐
│  [Back] PROFITABILITY DASHBOARD                  [Value Tier Filter]│
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ TOTAL    │  │ TOTAL    │  │ AVG      │  │ UNPROFIT-│        │
│  │ PROFIT   │  │ MARGIN   │  │ CLV      │  │ ABLE     │        │
│  │ R$ 2.1M  │  │ 16.8%    │  │ R$ 892   │  │ 18.3%    │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                  │
│  ┌─────────────────────────────┐  ┌──────────────────────────┐  │
│  │                             │  │                          │  │
│  │   PROFIT DISTRIBUTION       │  │   COST BREAKDOWN         │  │
│  │   [Histogram]               │  │   [Waterfall Chart]      │  │
│  │                             │  │                          │  │
│  │   Count                     │  │   Revenue                │  │
│  │     │                       │  │      ↓                   │  │
│  │   40█                       │  │   - COGS                 │  │
│  │   30█                       │  │      ↓                   │  │
│  │   20█   ██                  │  │   - Discounts            │  │
│  │   10█   ████   ██           │  │      ↓                   │  │
│  │    0██████████████████      │  │   - Returns              │  │
│  │     -500  0   500  1000     │  │      ↓                   │  │
│  │        Customer Profit      │  │   - Service Costs        │  │
│  │                             │  │      ↓                   │  │
│  │                             │  │   = NET PROFIT           │  │
│  │                             │  │                          │  │
│  └─────────────────────────────┘  └──────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │   REVENUE vs PROFIT SCATTER                               │  │
│  │   [Scatter Plot]                                          │  │
│  │                                                           │  │
│  │   Y: Profit                                               │  │
│  │   │                                                       │  │
│  │   │    ● ●                                                │  │
│  │   │   ●  ●  ●                                             │  │
│  │   │  ●   ●   ●    ●                                       │  │
│  │   │ ●    ●    ●  ●                                        │  │
│  │   │●     ●     ●●                                         │  │
│  │   └───────────────────────────                            │  │
│  │          X: Revenue                                        │  │
│  │                                                           │  │
│  │   Color: Profit Margin % (Red-Yellow-Green)               │  │
│  │   Size: Customer Tenure                                   │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────┐  ┌──────────────────────────┐  │
│  │   PROFIT BY SEGMENT         │  │   VALUE TIER ANALYSIS    │  │
│  │   [Clustered Column]        │  │   [Pie + Table]          │  │
│  │                             │  │                          │  │
│  │   Champions  ████████       │  │   High Value   45% ████  │  │
│  │   Loyal      ██████         │  │   Medium       35% ███   │  │
│  │   At Risk    ████           │  │   Low          20% ██    │  │
│  │   Dormant    ██             │  │                          │  │
│  │                             │  │   Avg Profit by Tier     │  │
│  │                             │  │   [Mini bar chart]       │  │
│  └─────────────────────────────┘  └──────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### **DAX Measures for Profitability**

```dax
// Total Profit
Total Profit = SUM(customer_master[customer_profit])

// Profit Margin %
Profit Margin % = 
DIVIDE(
    [Total Profit],
    SUM(customer_master[gross_revenue]),
    0
)

// Unprofitable Customer Count
Unprofitable Customers = 
CALCULATE(
    COUNTROWS(customer_master),
    customer_master[customer_profit] < 0
)

// Unprofitable %
Unprofitable % = 
DIVIDE(
    [Unprofitable Customers],
    COUNTROWS(customer_master),
    0
)

// Average Customer Lifetime Value (CLV)
Avg CLV = 
AVERAGE(customer_master[customer_profit]) * 
AVERAGE(customer_master[frequency]) * 
(365 / AVERAGE(customer_master[interpurchase_time_avg]))

// Cost Components
Total COGS = SUM(customer_master[total_cogs])
Total Discount Cost = SUM(customer_master[total_discount_cost])
Total Return Cost = SUM(customer_master[return_cost])
Total Service Cost = SUM(customer_master[service_cost])

// Profit Quartile Analysis
Q4 Profit (Top 25%) = 
CALCULATE(
    SUM(customer_master[customer_profit]),
    customer_master[profit_quartile] = 4
)
```

---

## 🎯 PAGE 4: Retention Action Center

### **Layout Wireframe**

```
┌──────────────────────────────────────────────────────────────────┐
│  [Back] RETENTION ACTION CENTER          [Priority Tier Filter] │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ HIGH     │  │ EXPECTED │  │ TOTAL    │  │ CAMPAIGN │        │
│  │ PRIORITY │  │ RETENTION│  │ INTERVEN-│  │ BUDGET   │        │
│  │ CUSTOMERS│  │ VALUE    │  │ TION COST│  │ NEEDED   │        │
│  │ 2,847    │  │ R$ 456K  │  │ R$ 89K   │  │ R$ 125K  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │   TOP 100 RETENTION TARGETS                               │  │
│  │   [Detailed Table with Conditional Formatting]            │  │
│  │                                                           │  │
│  │   Rank | Customer  | Segment    | Profit | Churn | Action│  │
│  │   ─────────────────────────────────────────────────────   │  │
│  │   1    | C12345    | At Risk    | R$2.3K | 87%   | Call  │  │
│  │   2    | C67890    | High Value | R$5.1K | 82%   | Offer │  │
│  │   3    | C11111    | Loyal      | R$1.8K | 79%   | Email │  │
│  │   ...                                                     │  │
│  │                                                           │  │
│  │   [Export to CSV Button]                                  │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────┐  ┌──────────────────────────┐  │
│  │                             │  │                          │  │
│  │   INTERVENTION ROI          │  │   RECOMMENDED ACTIONS    │  │
│  │   [Scatter Plot]            │  │   [Donut + Bar]          │  │
│  │                             │  │                          │  │
│  │   Y: Expected Value         │  │   Personal Call   15%    │  │
│  │   │                         │  │   Special Offer   35%    │  │
│  │   │    ●  ●                 │  │   Email Campaign  40%    │  │
│  │   │   ●    ●                │  │   Automated     10%      │  │
│  │   │  ●      ●               │  │                          │  │
│  │   │ ●        ●              │  │   By Segment:            │  │
│  │   │──────────●────           │  │   Champions → Loyalty   │  │
│  │   └────────────────────      │  │   At Risk → Winback     │  │
│  │      Low    Med   High       │  │   Dormant → Reactivate  │  │
│  │         Success Probability  │  │                          │  │
│  │                             │  │                          │  │
│  └─────────────────────────────┘  └──────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │   PRIORITY SCORE DISTRIBUTION                             │  │
│  │   [Histogram with Reference Lines]                        │  │
│  │                                                           │  │
│  │   Count                                                   │  │
│  │     │                                                     │  │
│  │   50█                                                     │  │
│  │   40█                                                     │  │
│  │   30█   ██                                                │  │
│  │   20█   ████   ██                                         │  │
│  │   10█   █████ ██████                                      │  │
│  │    0██████████████████████                                │  │
│  │     0   20   40   60   80   100                           │  │
│  │        Priority Score                                     │  │
│  │                                                           │  │
│  │   Red Line: High Priority (>75)                           │  │
│  │   Yellow Line: Medium (50-75)                             │  │
│  │   Green Line: Low (<50)                                   │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### **DAX Measures for Retention**

```dax
// High Priority Customers
High Priority Count = 
CALCULATE(
    COUNTROWS(customer_master),
    customer_master[retention_priority_score] >= 75
)

// Total Expected Retention Value
Total ERV = SUM(customer_master[expected_retention_value])

// Total Intervention Cost
Total Intervention Cost = SUM(customer_master[intervention_cost])

// Net Expected Benefit
Net Expected Benefit = 
SUM(customer_master[expected_net_benefit])

// ROI on Retention
Retention ROI % = 
DIVIDE(
    [Net Expected Benefit],
    [Total Intervention Cost],
    0
)

// Success Probability Weighted
Weighted Success Prob = 
AVERAGE(customer_master[success_prob])

// Customers by Recommended Action
Action Personal Call = 
CALCULATE(
    COUNTROWS(customer_master),
    customer_master[recommended_action] = "Personal Outreach"
)

Action Special Offer = 
CALCULATE(
    COUNTROWS(customer_master),
    customer_master[recommended_action] = "Special Offer"
)

// Campaign Budget Needed
Campaign Budget = 
SUM(customer_master[intervention_cost]) * 1.2  // 20% buffer
```

### **Retention Targets Table Configuration**

**Fields to Display:**
1. `priority_rank` (Sort ascending)
2. `customer_id`
3. `rfm_segment`
4. `value_tier`
5. `customer_profit` (Format: R$ #,##0)
6. `churn_prob` (Format: %, Conditional: Red if >70%, Yellow 50-70%, Green <50%)
7. `success_prob` (Format: %)
8. `expected_retention_value` (Format: R$ #,##0)
9. `intervention_cost` (Format: R$ #,##0)
10. `expected_net_benefit` (Format: R$ #,##0, Conditional formatting)
11. `recommended_action` (Icon based on value)

**Conditional Formatting Rules:**

```dax
// Churn Probability Color
Churn Color = 
SWITCH(
    TRUE(),
    customer_master[churn_prob] >= 0.7, "#E74C3C",  // Red
    customer_master[churn_prob] >= 0.5, "#F39C12",  // Orange
    "#2ECC71"  // Green
)

// Priority Rank Icon
Priority Icon = 
SWITCH(
    TRUE(),
    customer_master[priority_rank] <= 20, "🔴",
    customer_master[priority_rank] <= 50, "🟡",
    "🟢"
)
```

---

## 🎨 Design System & Best Practices

### **Color Palette**

```
Primary Brand:     #2C3E50 (Dark Blue-Grey)
Accent:            #3498DB (Bright Blue)

Segment Colors:
- Champions:       #2ECC71 (Emerald Green)
- Loyal:           #3498DB (Blue)
- Potential:       #9B59B6 (Purple)
- At Risk:         #F39C12 (Orange)
- Dormant:         #E74C3C (Red)

Profitability:
- Profitable:      #27AE60 (Green)
- Break-even:      #F1C40F (Yellow)
- Unprofitable:    #C0392B (Red)

Churn Risk:
- Low Risk:        #2ECC71 (Green)
- Medium Risk:     #F39C12 (Orange)
- High Risk:       #E74C3C (Red)
```

### **Typography**

- **Headers**: Segoe UI Semibold, 14-16pt
- **KPI Values**: Segoe UI Bold, 24-28pt
- **Body Text**: Segoe UI Regular, 10-11pt
- **Data Labels**: Segoe UI Regular, 9pt

### **Interactive Elements**

1. **Slicers** (Right sidebar):
   - Date Range (Relative: Last 12 months)
   - Segment (Multi-select)
   - Region (Multi-select)
   - Value Tier (Single select)
   - Churn Risk Level (Single select)

2. **Drill-through Pages**:
   - From any customer ID → Customer Detail Page
   - From segment → Segment Deep Dive
   - From geographic region → Regional Analysis

3. **Tooltips**:
   - Custom tooltip page showing:
     - Customer profile summary
     - Purchase history sparkline
     - Engagement trends
     - Recommended actions

### **Performance Optimization**

```dax
// Use variables for complex calculations
Customer Profit Calc = 
VAR GrossRev = SUM(customer_master[gross_revenue])
VAR COGS = SUM(customer_master[total_cogs])
VAR Discounts = SUM(customer_master[total_discount_cost])
VAR Returns = SUM(customer_master[return_cost])
VAR Service = SUM(customer_master[service_cost])
VAR Acquisition = SUM(customer_master[acquisition_cost])
RETURN
    GrossRev - COGS - Discounts - Returns - Service - Acquisition

// Avoid CALCULATE in row context
// Use summarized tables for large datasets
```

---

## 📋 Implementation Checklist

### **Phase 1: Data Setup** ✓
- [ ] Import 4 CSV files from `outputs/powerbi/`
- [ ] Create relationships between tables
- [ ] Verify data types (dates, currency, decimals)
- [ ] Hide unnecessary columns

### **Phase 2: DAX Measures** ⏳
- [ ] Create all KPI measures (15-20 measures)
- [ ] Build time intelligence measures (MoM, YoY)
- [ ] Create dynamic segmentation logic
- [ ] Test measures with different filters

### **Phase 3: Visual Development** ⏳
- [ ] Build Page 1: Executive Overview
- [ ] Build Page 2: Segmentation Analysis
- [ ] Build Page 3: Profitability Dashboard
- [ ] Build Page 4: Retention Action Center
- [ ] Add custom tooltips
- [ ] Implement drill-through pages

### **Phase 4: Polish & Deploy** ⏳
- [ ] Apply consistent color scheme
- [ ] Add company logo and branding
- [ ] Set up mobile layout
- [ ] Configure row-level security (if needed)
- [ ] Publish to Power BI Service
- [ ] Set up automatic data refresh
- [ ] Share with stakeholders

---

## 🚀 Advanced Features (Optional)

### **1. What-If Parameters**

Create parameters for scenario analysis:
- Intervention budget slider
- Target churn reduction %
- Customer lifetime multiplier

```dax
// Example: Budget Impact Analysis
Projected Retentions = 
[High Priority Count] * 
'What-If'[Success Rate Slider] * 
'What-If'[Budget Multiplier]
```

### **2. AI Insights**

Enable Power BI AI features:
- **Key Influencers**: What drives churn?
- **Decomposition Tree**: Profit margin breakdown
- **Anomaly Detection**: Unusual purchase patterns
- **Forecasting**: Future revenue projections

### **3. Automated Narratives**

Use Power BI's smart narratives to auto-generate insights:
- "Churn risk increased by X% this month"
- "Top segment contributing to revenue: Champions"
- "Recommended action mix shifted toward email campaigns"

### **4. Integration with Marketing Tools**

Export retention lists to:
- Email marketing platforms (Mailchimp, SendGrid)
- CRM systems (Salesforce, HubSpot)
- Ad platforms (Facebook Custom Audiences, Google Ads)

---

## 📞 Support & Resources

- **Dataset Documentation**: See `README.md` in project root
- **Column Definitions**: Refer to data dictionary in outputs
- **DAX Guide**: https://dax.guide
- **Power BI Community**: https://community.powerbi.com

---

**Created for**: Customer Retention Analytics Pipeline  
**Dataset**: Olist Brazilian E-Commerce (Real-world data)  
**Last Updated**: 2025  
