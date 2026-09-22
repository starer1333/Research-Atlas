import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tempfile
from atlas.store import Store

def test_v3_view_and_findings():
    with tempfile.TemporaryDirectory() as d:
        store=Store(Path(d)/"research.sqlite3")
        state=store.state("NVDA","2025-03-01")
        assert "v3" in state
        view=state["v3"]
        assert set(["summary","trajectory","findings","questions","source_coverage","data_integrity"]) <= set(view)
        visible={o["id"] for o in state["observations"]}
        for finding in view["findings"]:
            assert set(finding["evidence_ids"]) <= visible
            assert finding["priority"]["total"] >= 0
            assert finding["basis"].startswith("Deterministic")

def test_question_can_be_saved_before_conclusion():
    with tempfile.TemporaryDirectory() as d:
        store=Store(Path(d)/"research.sqlite3")
        state=store.state("NVDA","2025-03-01")
        finding=state["v3"]["findings"][0]
        source_ids=list(dict.fromkeys(
            o["source_id"] for o in state["observations"] if o["id"] in finding["evidence_ids"]
        ))
        result=store.action("question-save",{
            "company":"NVDA",
            "asof":"2025-03-01",
            "question":finding["question"],
            "reason":finding["statement"],
            "finding_id":finding["id"],
            "evidence_ids":finding["evidence_ids"],
            "source_ids":source_ids,
            "status":"open",
        })
        assert result["id"]
        refreshed=store.state("NVDA","2025-03-01")
        saved=[r for r in refreshed["records"] if r["kind"]=="question"]
        assert saved and saved[0]["content"]["question"]==finding["question"]

if __name__=="__main__":
    test_v3_view_and_findings()
    test_question_can_be_saved_before_conclusion()
    print("V3 tests passed")
