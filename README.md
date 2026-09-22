# Research Atlas V3

**Evidence before conviction.**  
A financial-first company research workbench that connects source evidence, business structure, financial diagnostics, peer comparability, operating drivers, research questions and revision history.

**Repository:** https://github.com/starer1333/Research-Atlas  
**Public V3 preview:** https://starer1333.github.io/Research-Atlas/v3/  
**Business / Company Map preview:** https://starer1333.github.io/Research-Atlas/v3/?view=business

## Product flow

```
Ticker / Company
↓
SourceAdapter
↓
SEC EDGAR + optional user evidence
↓
Semantic Contract
↓
Company / Product Map
↓
Industry Driver Module
↓
Financial Diagnostics
↓
Research Question
↓
Evidence / Compare / Scenario
↓
Claim / Revision
```

The user-facing information architecture stays small:

**Research / Evidence / Analysis / Report**

## Current implementation

### V3-1 → V3-6

- 60-second Company View
- deterministic Financial Diagnostics
- point-in-time Evidence Drawer
- metric-level Comparative Reasoning gate
- question-first Scenario entry
- Research Memory / Revision Trail
- V3 Semantic Contract with Company, Metric, Observation, Document, Segment, Product, Driver, ResearchQuestion, Claim and Revision
- opt-in official SEC EDGAR SourceAdapter
- Automatic Starter Research Pack for new U.S. tickers
- deterministic latest-10-K Item 1 Business extraction
- source-linked Segment / Product / Platform / Service candidates, all `pending_review`

### V3-7 — Company / Product Map

Implemented in `atlas/company_map.py`.

```
Company
→ Segment / Product
→ Context
→ Operating Driver
→ Financial Outcome
```

The map distinguishes evidence-backed objects, research hypotheses and industry templates. Products without a verified Segment mapping stay explicitly `unlinked_segment`; the system does not guess.

Semantic Contract 3.3 also adds `ContextEntity` for Customer, Competitor, Geography, Channel and Risk evidence.

### V3-8 — Industry Driver Modules

Implemented in `atlas/industries.py`.

Current modules:

- Semiconductor / Hardware
- SaaS / Subscription
- Consumer / Retail
- Automotive
- Bank / Financial Institution
- General fallback

Each module defines operating drivers, linked financial metrics, operating KPIs to seek, source requirements, research questions and comparability boundaries. Selection is deterministic and exposes the reason (mode / SIC / keyword).

**Industry drivers are research templates, not company facts.**

## Research integrity

Research Atlas keeps these distinctions explicit:

- `Disclosed` vs `Calculated`
- `candidate` vs `reviewed`
- Data Integrity vs Financial Quality
- company evidence vs industry template
- comparable vs qualified vs not directly comparable
- ResearchQuestion vs Claim
- current view vs Revision

The system does not treat a balanced accounting equation as evidence of business quality and does not turn an anomaly into an investment conclusion.

## Local start

Python 3.10+.

```powershell
python -B serve_atlas.py
```

Open:

```
http://127.0.0.1:8766
```

Previous V2 UI:

```
http://127.0.0.1:8766/v2
```

### Enable official SEC ingestion

SEC network access is **off by default**.

```powershell
$env:ATLAS_SEC_USER_AGENT="ResearchAtlas your-email@example.com"
python -B serve_atlas.py --enable-sec
```

The adapter only uses fixed official SEC domains. Imported observations and filing-text semantic candidates remain pending review.

## Code map

| Path | Responsibility |
|---|---|
| `atlas/semantic.py` | Semantic Contract 3.3 |
| `atlas/sources/` | SourceAdapter, SEC Company Facts and 10-K intake |
| `atlas/company_map.py` | V3-7 Company / Product Map |
| `atlas/industries.py` | V3-8 Industry Driver Modules |
| `atlas/v3.py` | guided view + deterministic findings |
| `atlas/relations.py` | accounting relationships and comparability |
| `atlas/drivers.py` | deterministic hardware/software scenario mechanics |
| `atlas/store.py` | SQLite persistence and point-in-time state |
| `workbench/v3-index.html` | V3 shell |
| `workbench/v3.js` | Research / Evidence / Analysis / Report interactions |
| `workbench/v3.css` | V3 visual system |

## Validation

GitHub Actions runs syntax checks plus:

```
python -B tests/test_semantic.py
python -B tests/test_sec_starter.py
python -B tests/test_filing_text.py
python -B tests/test_v3.py
python -B tests/test_company_map.py
python -B tests/test_industries.py
python -B tests/test_research.py
python -B tests/test_workbench.py
node --test tests/model.test.cjs
```

## Not claimed yet

- complete Customer / Competitor / pricing / strategy extraction
- note-level segment-table parsing across all issuers
- Docling/PDF intake
- external LLM/RAG
- full three-statement forecasting for every industry
- bank-specific valuation engine
- production ECharts visualization layer
- multi-user cloud authentication
- automatic investment recommendations or company scores

## Architecture references

Research Atlas studies architecture and interaction ideas from FinRobot, OpenBB, WrenAI, Dexter, EdgarTools, FinanceToolkit, Docling and GPT Researcher. It is not a reproduction of those systems. Reused code, where applicable, should retain source/license attribution.

## Documentation

- [V3 Product Contract](docs/v3-product-contract.md)
- [V3 Semantic Contract](docs/v3-semantic-contract.md)
- [V3 SourceAdapter / SEC](docs/v3-source-adapters.md)
- [V3-7 Company / Product Map](docs/v3-company-map.md)
- [V3-8 Industry Driver Modules](docs/v3-industry-modules.md)
- [Security boundary](docs/security.md)
- [V2.2 historical release notes](docs/v22-release.md)

## Legacy

V0.1 and V2 remain in the repository for design history and regression compatibility. V3 is the current product direction.
