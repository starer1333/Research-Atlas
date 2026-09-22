"""V3-9 visualization grammar.

The backend describes what a chart is allowed to communicate. Rendering remains a
frontend concern (Apache ECharts in the V3 workbench). This keeps visualization
semantics explicit and testable instead of letting chart choice silently change
the analytical meaning.
"""

GRAMMAR_VERSION = "3.9"

def build_visualization_grammar(profile, diagnostics):
    years = diagnostics.get("years", [])
    charts = []

    if years:
        charts.append({
            "id": "financial-trajectory",
            "family": "combo",
            "question": "How are scale and operating profitability moving together?",
            "x": "period",
            "series": [
                {"metric": "revenue", "mark": "bar", "axis": "amount", "role": "scale"},
                {"metric": "operating_margin", "mark": "line", "axis": "percent", "role": "profitability"},
            ],
            "interaction": ["axis-tooltip", "legend-focus"],
            "provenance": "Every point is derived from visible point-in-time observations.",
        })
        charts.append({
            "id": "cash-working-capital",
            "family": "multi-line",
            "question": "Is cash conversion diverging from working-capital balances?",
            "x": "period",
            "series": [
                {"metric": "cfo", "mark": "line", "axis": "amount"},
                {"metric": "receivables", "mark": "line", "axis": "amount"},
                {"metric": "inventory", "mark": "line", "axis": "amount"},
            ],
            "interaction": ["axis-tooltip", "legend-toggle"],
            "provenance": "Missing values stay missing; the chart never converts them to zero.",
        })

    if diagnostics.get("bridges"):
        charts.append({
            "id": "operating-profit-bridge",
            "family": "waterfall",
            "question": "Which accounting components explain the period-to-period operating-profit change?",
            "x": "bridge_component",
            "series": [{"metric": "bridge_delta", "mark": "waterfall", "axis": "amount"}],
            "interaction": ["item-tooltip"],
            "provenance": "Accounting decomposition only; it is not a causal business explanation.",
        })

    charts.append({
        "id": "segment-mix",
        "family": "donut",
        "question": "How concentrated is the disclosed business mix?",
        "x": "segment",
        "series": [{"metric": "segment_value", "mark": "arc", "axis": "share"}],
        "interaction": ["item-tooltip", "legend-focus"],
        "provenance": "Rendered only when numeric segment values exist; candidates without values remain textual evidence.",
    })

    return {
        "version": GRAMMAR_VERSION,
        "library": "Apache ECharts 6.1",
        "company_mode": profile.get("mode", "operating"),
        "principles": [
            "Question before decoration",
            "Missing is not zero",
            "Calculated is not disclosed",
            "Candidate is not verified",
            "Comparability gate before peer visualization",
            "Tooltip must preserve period, unit and analytical boundary",
            "Motion supports continuity; it must not imply certainty",
        ],
        "charts": charts,
        "boundary": "Charts are navigation and diagnosis aids. They do not create facts, verification status, scores or investment conclusions.",
    }
