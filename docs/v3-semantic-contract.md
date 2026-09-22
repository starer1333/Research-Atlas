# V3 Semantic Contract 3.3

Research Atlas V3 uses one shared vocabulary across ingestion, finance logic, UI and later AI tools.

```
Company
├─ Document
│  └─ Observation ──> Metric
├─ Segment
│  └─ Product
├─ ContextEntity (Customer / Competitor / Geography / Channel / Risk)
├─ Driver ──> Metric
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


## V3-7 Company / Product Map

`atlas/company_map.py` projects the semantic snapshot into a navigational research graph. It intentionally separates three states:

1. **Evidence-linked semantic objects** — Company, Segment, Product and ContextEntity with source/review metadata.
2. **Company-specific research hypotheses** — existing Driver records linked to evidence where available.
3. **Industry templates** — operating Driver nodes from V3-8; these are explicitly `template`, not company facts.

The map uses relational/JSON objects rather than a graph database. This keeps the MVP inspectable while preserving a future migration path if graph traversal becomes a real product requirement.

`ContextEntity` supports `customer / competitor / geography / channel / risk`. V3-7 defines the contract and map behavior; automatic extraction of those entities remains incomplete.
