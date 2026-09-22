# V3 Semantic Contract

Research Atlas V3 uses one shared vocabulary across ingestion, finance logic, UI and later AI tools.

```
Company
├─ Document
│  └─ Observation ──> Metric
├─ Segment
│  └─ Product
│     └─ Driver ──> Metric
└─ ResearchQuestion
   └─ Claim
      └─ Revision
```

The executable contract is in `atlas/semantic.py`. It is deliberately implemented as typed Python dataclasses plus relational references rather than a graph database.

## Objects

| Object | Meaning | Primary relationships |
|---|---|---|
| Company | reporting/research entity | owns all company-scoped objects |
| Metric | canonical financial or operating concept | referenced by Observation and Driver |
| Document | source with disclosure date | source of Observation/Driver/Claim evidence |
| Observation | point-in-time value or fact | Company + Metric + Document + Period + Scope |
| Segment | disclosed/research business unit | belongs to Company |
| Product | product/platform/service | belongs to Company, optionally Segment |
| Driver | mechanism/hypothesis linked to metrics | may link Segment/Product/Document |
| ResearchQuestion | question to investigate | references Evidence |
| Claim | researcher conclusion; not auto-created from a metric | references support/counter-evidence |
| Revision | immutable reasoned change | links research history |

## Non-negotiable rules

Observation requires period, value, currency, unit, accounting basis, scope, document, disclosed date, value kind and review state.

ResearchQuestion and Claim remain separate. Saving a question never implies a conclusion.

- `Disclosed` does not mean Research Atlas independently audited the value.
- `Calculated` retains formula/dependencies and cannot masquerade as disclosed.
- `pending_review` is distinct from extraction acceptance.
- Data Integrity is a data contract, not a company-quality judgement.
- Point-in-time filtering follows disclosure availability.

## Migration strategy

V2 SQLite tables remain the persistence substrate. `build_semantic_snapshot(state)` projects them into V3 objects and validates references. This avoids a destructive database migration before the contracts are stable.

Dedicated relational tables for Segment/Product/Driver/ResearchQuestion/Claim/Revision can follow after the contract survives real UI and SEC-ingestion usage.
