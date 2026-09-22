# V3-7 Company / Product Map

Research Atlas V3-7 turns the semantic contract into a navigational research graph without introducing a graph database.

## Map layers

```
Company
  ↓
Segments / Products
  ↓
Context: customer / competitor / geography / channel / risk
  ↓
Operating Drivers
  ↓
Financial Outcomes
```

## State model

- `evidence_linked`: backed by semantic objects with source lineage.
- `pending_review`: extracted candidate waiting for researcher confirmation.
- `research_hypothesis`: company-specific mechanism, not a disclosed fact.
- `template`: industry research lens from V3-8.
- `unlinked_segment`: Product exists but has no verified Segment mapping.

The UI must preserve these distinctions.

## Why no graph database yet?

Current requirements are bounded traversal and visualization over a single company research workspace. Relational/JSON objects are simpler to validate, export and debug. A graph database should only be introduced if cross-company graph queries or multi-hop traversal become a demonstrated requirement.
