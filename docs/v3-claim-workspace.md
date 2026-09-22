# Claim Workspace / Browser E2E / Unified Provenance

This slice turns the hardened Semantic Contract into a user-visible research workflow.

## Claim Workspace

The Report page now treats Claim as a first-class object instead of a timeline-only artifact.

Workflow:

```
ResearchQuestion
→ select supporting evidence
→ select counter-evidence
→ write current claim
→ write alternative explanation
→ define falsification / next-evidence trigger
→ choose status
→ save immutable Claim revision
```

Rules:

- a question-linked Claim must reference at least one Observation
- the same Observation cannot be both support and counter-evidence
- source IDs must cover every selected Observation
- the Claim text must match the linked ResearchQuestion
- revisions never overwrite prior Claims

The UI reads/writes the same `research-save` contract used by the backend; there is no parallel browser-only model.

## Unified provenance

Semantic Contract 3.5 projects a common `provenance` envelope for Observation, Segment, Product, ContextEntity, Driver and Claim objects.

The Evidence Drawer reads this envelope directly. Manual extraction review lineage is preserved through `parent_source_id`, literal quote and `extraction_review_id`; SEC data preserves source type, accession, disclosure date and XBRL source tag where available.

Missing provenance fields remain missing. The UI must not manufacture a citation, locator or extraction method.

## Browser E2E

Playwright exercises the real local server, SQLite store, browser UI and API boundary.

Current E2E coverage verifies:

1. a Research finding can become a saved ResearchQuestion
2. the question opens in Claim Workspace
3. support and counter-evidence can be selected
4. an initial Claim can be saved
5. a second save creates an immutable revision rather than overwriting the first
6. the Evidence Drawer renders the semantic provenance envelope
7. the four primary research stages remain navigable

Run locally:

```bash
npm install
npx playwright install chromium
python -B serve_atlas.py --db .runtime/e2e.sqlite3
npm run test:e2e
```

GitHub Actions starts the local server and runs the same browser flow after the existing deterministic/unit suites pass.
