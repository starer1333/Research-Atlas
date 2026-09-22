"""Export only fresh public fixtures. Never open the user's research database."""
import json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from atlas.store import Store
from atlas.drivers import suggested, calculate
from atlas.peer_seed import DIFFERENTIATION

def build():
    runtime = ROOT / '.runtime' / 'pages-build'
    runtime.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=runtime) as directory:
        store = Store(Path(directory) / 'seed.sqlite3')
        states = {}
        for ticker in ['NVDA', 'AMD', 'INTC', 'ADBE']:
            state = store.state(ticker, '2025-03-01')
            item = {k: state[k] for k in ['company', 'asof', 'documents', 'observations', 'periods', 'diagnostics', 'relations', 'metric_dictionary']}
            item['driver'] = suggested(state)
            item['reference_model'] = calculate(state, **{'template': item['driver']['template'], 'params': item['driver']['params']})['rows']
            item['differentiation'] = DIFFERENTIATION[ticker]
            states[ticker] = item
    destination = ROOT / 'pages' / 'data.json'
    destination.write_text(json.dumps(states, ensure_ascii=False, allow_nan=False, separators=(',', ':')), encoding='utf-8')
    (ROOT / 'pages' / '.nojekyll').touch()
    print('Exported four public historical fixtures; no user database accessed.')

if __name__ == '__main__': build()
