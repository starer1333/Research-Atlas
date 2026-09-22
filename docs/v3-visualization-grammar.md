# V3-9 — Visualization Grammar / Apache ECharts

V3-9 replaces hand-built decorative charts with a small, explicit visualization grammar.

## Principle

A chart must answer a research question. It does not create evidence, verification status, company scores or investment conclusions.

The backend publishes a chart contract through state.v3.visualization_grammar. The browser renders the supported charts with Apache ECharts 6.1.

Current chart families:

- Revenue × Operating Margin: dual-axis bar + line
- CFO / Receivables / Inventory: multi-line working-capital relationship view
- Segment mix: donut, only when numeric segment values exist
- Operating-profit bridge: waterfall-style accounting decomposition
- Peer comparison: comparability gate remains visible before any visual comparison
- Scenario output: calculated forecast trajectories remain explicitly labelled Calculated

## Grammar rules

1. Missing values remain missing; never silently coerce them to zero.
2. Calculated values are visually and textually distinct from disclosed values.
3. Candidate / pending-review business objects do not become numeric charts unless a value exists.
4. Peer visualization is downstream of the comparability gate.
5. Tooltips preserve period, units and the analytical boundary.
6. Motion is restrained and disabled under prefers-reduced-motion.
7. Charts use interaction for inspection, not gamified scoring.

The V3 workbench loads a pinned ECharts build from jsDelivr. If it is unavailable, the page remains usable and shows a chart-unavailable state rather than changing the research data.
