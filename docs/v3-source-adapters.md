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

## Starter Pack scope

P0 maps a conservative core of US-GAAP Company Facts into canonical V3 metrics. Every Observation retains accession, filed date, source XBRL tag, fiscal period, basis, scope, currency, unit, version count and selection policy.

Multiple candidate 10-K facts are not silently collapsed without trace: the imported observation records how many versions were seen and whether it is a restatement candidate.

## Deliberate limitations

Company Facts is not a full Company Map. This adapter does not infer products, customers, competitors, marketing strategy, ESG conclusions or segment definitions from filing prose.

Those need a later filing-text parser (HTML/Docling), industry modules and/or human review.

## EdgarTools

EdgarTools remains a strong reference and possible alternate SourceAdapter. This branch first implements the adapter boundary against official SEC endpoints so the semantic model is not coupled to one third-party library before the contract is stable.
