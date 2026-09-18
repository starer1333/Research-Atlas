"""Read-only check of the pinned sample. Does not establish a generation root cause."""
from pathlib import Path
import json
root = Path(__file__).resolve().parents[1]
report = root / 'upstream/FinRobot/finrobot_equity/core/output/NVDA_Equity_Research_Report.html'
lines = report.read_text(encoding='utf-8').splitlines()
actual = [i for i,s in enumerate(lines,1) if 'Revenue (2026A)' in s]
forecast = [i for i,s in enumerate(lines,1) if 'consensus estimates' in s and 'FY2026' in s]
result = {'file': str(report.relative_to(root)), 'actual_label_lines':actual,'forecast_narrative_lines':forecast,'conflict_detected':bool(actual and forecast),'root_cause':'not established'}
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(0 if result['conflict_detected'] else 1)
