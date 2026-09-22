import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tempfile
from atlas.store import Store

def test_semantic_snapshot_contract():
    with tempfile.TemporaryDirectory() as d:
        state=Store(Path(d)/"research.sqlite3").state("NVDA","2025-03-01")
        sem=state["semantic"]
        assert sem["schema_version"].startswith("3.")
        assert sem["company"]["ticker"]=="NVDA"
        assert sem["validation"]["ok"], sem["validation"]["issues"]
        assert sem["metrics"] and sem["documents"] and sem["observations"]
        doc_ids={x["id"] for x in sem["documents"]}
        metric_ids={x["id"] for x in sem["metrics"]}
        for o in sem["observations"]:
            assert o["document_id"] in doc_ids
            assert o["metric_id"] in metric_ids
            assert o["review_state"] in ["reviewed","pending_review"]
        assert "business_summary" in sem["company"]
        assert all(set(s["source_ids"])<=doc_ids for s in sem["segments"])
        assert all(set(p["source_ids"])<=doc_ids for p in sem["products"])

if __name__=="__main__":
    test_semantic_snapshot_contract()
    print("semantic contract test passed")
