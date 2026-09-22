# Research Atlas V3 product contract

This branch implements the first V3 foundation slice described in the V3 architecture research report.

## Product definition

Research Atlas V3 is a financial-first guided company research workbench.

The default mental model is:

Company / Ticker
→ 60-second Company View
→ What changed?
→ Questions worth investigating
→ Why / Evidence / Compare / Add to Research
→ Analysis
→ Scenario when the question requires it
→ Report / Revision

It is not an automatic investment recommendation engine.

## Four-page information architecture

1. Research — What is this company and what is worth investigating?
2. Evidence — Where did the facts come from and what is still unverified?
3. Analysis — What happened, why, how does it compare, and what happens under a scenario?
4. Report — What does the researcher currently believe and how did that view change?

Data Integrity remains available, but it is intentionally subordinate to Financial Diagnostics.

## Interaction contract

Every deterministic finding should expose the same four actions:

- WHY — reveal the relationship, priority components and possible mechanisms.
- EVIDENCE — show the point-in-time observation and source lineage.
- COMPARE — carry the same question into a peer-comparability gate.
- ADD TO RESEARCH — save a research-question object; this does not save a final conclusion.

## Deterministic vs judgement boundary

Code may create:

- calculated metrics
- accounting/data-integrity checks
- anomaly relationships
- suggested research questions
- scenario calculations

The system must not silently turn those into a final judgement.

Candidate != verified.
Calculated != disclosed.
Comparable != identical.
Data Integrity != Financial Quality.
LLM interpretation != fact.

## Implemented in this foundation branch

- V3 four-page shell as the default local root.
- V2 remains available at /v2.
- 60-second Company View from the existing point-in-time state.
- Native, dependency-free financial trend visualizations.
- deterministic V3 diagnostics in atlas/v3.py.
- transparent diagnostic priority components.
- source coverage and Data Integrity summary.
- WHY / EVIDENCE / COMPARE / ADD TO RESEARCH interaction grammar.
- question-first Scenario entry.
- Comparative Reasoning UI over the existing metric-level comparability backend.
- Research Memory view using immutable existing records.
- question-save route so a question can be persisted before a conclusion exists.
- V3 Semantic Contract: Company / Metric / Observation / Document / Segment / Product / Driver / ResearchQuestion / Claim / Revision.
- Opt-in direct SEC EDGAR SourceAdapter and Automatic Starter Research Pack for new U.S. tickers.
- V3-6 deterministic latest-10-K Item 1 parser with source-linked Business excerpt and pending-review Segment/Product candidates.

## Not implemented yet

The foundation branch does not pretend that the later V3 roadmap is complete.

- Direct SEC EDGAR SourceAdapter is implemented as an opt-in local feature; EdgarTools remains a reference/possible alternative adapter.
- No Docling PDF parser yet.
- No external LLM/RAG.
- V3 Semantic Contract is implemented as typed objects + validated projections over the V2 relational store; dedicated-table migration is intentionally deferred.
- No complete industry-module registry.
- No graph database.
- No cloud/multi-user authentication.
- No ECharts dependency yet; P0 uses accessible native SVG/CSS charts to avoid adding a build/dependency step before the interaction model is validated.

## Next engineering slices

1. Stabilize the Semantic Contract under real SEC Starter Pack imports; then decide dedicated-table migration.
2. Extend filing-text coverage beyond Item 1 into note-level segment disclosures and richer HTML/Docling parsing while preserving provenance.
3. ECharts visualization layer and chart-data contract.
4. Semiconductor / SaaS / Consumer / Automotive / Bank industry modules.
5. Optional LLM-assisted research planning on top of deterministic evidence contracts.

The V3 rule remains: simple surface, deep logic.


## V3-7 Company / Product Map

Implemented in `atlas/company_map.py`.

The user-facing path is:

```
Company
→ Segment / Product
→ Context
→ Operating Driver
→ Financial Outcome
```

Edges preserve state. An evidence-backed Segment/Product is not rendered as equivalent to an industry-template Driver. Product-to-Segment relationships are only shown as evidence-linked when `segment_id` is known; otherwise the Product stays attached to Company with an explicit `unlinked_segment` status.

## V3-8 Industry Driver Modules

Implemented in `atlas/industries.py` with deterministic module selection and five domain modules:

- Semiconductor / Hardware
- SaaS / Subscription
- Consumer / Retail
- Automotive
- Bank / Financial Institution

A General fallback remains available.

Every driver declares its research question, linked financial metrics, operating KPIs to seek, source requirements and comparability policy. Module selection exposes the reason (mode / SIC / keyword), and all module drivers are marked `template` / `is_company_fact=False`.

This layer tells the researcher **what to investigate**; it does not fabricate operating KPIs or automatically assert causality.
