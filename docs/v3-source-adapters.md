# V3 SourceAdapter and SEC Starter Pack

```
Ticker / Company name
        ↓
SourceAdapter.resolve_company
        ↓
SourceAdapter.discover_documents
        ↓
SourceAdapter.company_facts
        ↓
SourceAdapter.filing_text (latest 10-K primary HTML)
        ↓
Item 1 Business parser
        ↓
Starter Research Pack
        ↓
Store.import_starter_pack
        ↓
V3 Semantic Contract
        ↓
60-second Company View
```

## Implemented adapter

`atlas.sources.sec.SecEdgarAdapter` uses official SEC EDGAR endpoints for company resolution, submissions metadata and XBRL Company Facts.

Network use is opt-in:

```powershell
$env:ATLAS_SEC_USER_AGENT="ResearchAtlas your-email@example.com"
python -B serve_atlas.py --enable-sec
```

Typing an unknown U.S. ticker into the V3 company box then builds and imports a Starter Research Pack.

## V3-6: 10-K Business / Segment / Product semantics

When SEC network access is enabled, the adapter also downloads the **latest 10-K primary HTML document** from the SEC archive and runs a deterministic stdlib parser.

The parser:

- isolates the longest valid `Item 1. Business → Item 1A. Risk Factors` span, avoiding the short table-of-contents occurrence;
- stores a leading Business excerpt with document/source lineage;
- extracts only **explicit lexical lists** such as “reportable segments are …” and “our products include …”;
- produces Segment/Product rows as `pending_review` candidates with source ID, locator, excerpt and extraction method;
- stores content/section SHA-256 fingerprints instead of persisting the full filing HTML.

It does **not** use an LLM and does not claim that a lexical candidate is a verified company ontology.

## Starter Pack scope

P0 maps a conservative core of US-GAAP Company Facts into canonical V3 metrics. Every Observation retains accession, filed date, source XBRL tag, fiscal period, basis, scope, currency, unit, version count and selection policy.

Multiple candidate 10-K facts are not silently collapsed without trace: the imported observation records how many versions were seen and whether it is a restatement candidate.

## Deliberate limitations

Company Facts plus Item 1 parsing is still not a full Company Map. V3-6 does not infer customers, competitors, pricing, marketing strategy, ESG conclusions, or complete note-level segment definitions. Product/Segment candidates are intentionally conservative and require human review.

A later filing-note parser (HTML/Docling), industry modules and/or optional LLM review can expand coverage without changing the Semantic Contract.

## EdgarTools

EdgarTools remains a strong reference and possible alternate SourceAdapter. This branch first implements the adapter boundary against official SEC endpoints so the semantic model is not coupled to one third-party library before the contract is stable.
