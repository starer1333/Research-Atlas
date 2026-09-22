# V3-8 Industry Driver Modules

The industry layer sits **between company semantics and financial diagnostics**.

```
Company / Segment / Product evidence
        ↓
Industry Driver Module
        ↓
Operating questions + KPI requests
        ↓
Financial metrics / anomalies
        ↓
Research Question
```

## Implemented modules

| Module | Example operating drivers |
|---|---|
| Semiconductor / Hardware | volume, ASP, mix, unit cost/yield, inventory transition, capacity/CapEx |
| SaaS / Subscription | recurring base, retention, expansion, new customers, pricing/packaging, SBC/opex |
| Consumer / Retail | footprint, same-store sales, traffic/conversion, AOV, promotion, inventory turns |
| Automotive | deliveries, ASP/model mix, materials, utilization, warranty, CapEx |
| Bank | loan growth, NIM, deposit mix, credit cost/NPL, fee income, capital adequacy |

A General module is the fallback.

## Selection logic

Selection is deterministic and visible. It considers explicit mode, SEC SIC prefix, industry/subtitle/business-model keywords, then falls back to General. The selected module returns `selection_reason` to the UI.

## Comparability

Driver modules do not turn unlike KPIs into comparable numbers. Each driver is tagged `qualified` or `not_directly_comparable`, and every module includes comparability notes.

Examples:
- ARR/RPO definitions are not interchangeable with revenue.
- Semiconductor gross margin needs fabless vs integrated-manufacturing context.
- Automotive delivery definitions vary.
- Bank NIM/CET1 require bank-specific definitions.

## Boundary

Driver templates are not company disclosures, forecasts, probabilities or scores. They are a structured checklist for what evidence to seek next.
