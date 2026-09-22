import copy
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from atlas.store import Store
from atlas import drivers
from atlas.semantic import validate_snapshot


def test_semantic_snapshot_contract():
    with tempfile.TemporaryDirectory() as d:
        state=Store(Path(d)/"research.sqlite3").state("NVDA","2025-03-01")
        sem=state["semantic"]
        assert sem["schema_version"]=="3.5"
        assert sem["company"]["ticker"]=="NVDA"
        assert sem["validation"]["ok"], sem["validation"]["issues"]
        assert sem["metrics"] and sem["documents"] and sem["observations"]
        doc_ids={x["id"] for x in sem["documents"]}
        metric_ids={x["id"] for x in sem["metrics"]}
        obs_ids={x["id"] for x in sem["observations"]}
        for o in sem["observations"]:
            assert o["document_id"] in doc_ids
            assert o["metric_id"] in metric_ids
            assert o["review_state"] in ["reviewed","pending_review"]
            assert o["provenance"]["primary_source_id"]==o["document_id"]
            assert o["document_id"] in o["provenance"]["source_ids"]
            assert set(o["depends_on"])<=obs_ids
        assert "business_summary" in sem["company"]
        assert all(set(s["source_ids"])<=doc_ids for s in sem["segments"])
        assert all(set(p["source_ids"])<=doc_ids for p in sem["products"])
        assert all(set(s["provenance"]["source_ids"])==set(s["source_ids"]) for s in sem["segments"])
        assert all(set(p["provenance"]["source_ids"])==set(p["source_ids"]) for p in sem["products"])


def test_claim_driver_and_revision_lineage_survive_projection():
    with tempfile.TemporaryDirectory() as d:
        store=Store(Path(d)/"research.sqlite3")
        state=store.state("NVDA","2025-03-01")
        support,counter=state["observations"][0],state["observations"][1]
        source_ids=list(dict.fromkeys([support["source_id"],counter["source_id"]]))
        question=store.action("question-save",{
            "company":"NVDA","asof":"2025-03-01","question":"What explains the change?",
            "reason":"Need an evidence-linked research thread","finding_id":None,
            "evidence_ids":[support["id"]],"source_ids":[support["source_id"]],"status":"open",
        })["id"]
        first=store.action("research-save",{
            "company":"NVDA","asof":"2025-03-01","question":"What explains the change?",
            "question_id":question,"conclusion":"Initial explanation","alternative":"Alternative mechanism",
            "next_evidence":"Check the next filing","change_reason":"Start claim","status":"supported",
            "supporting_evidence_ids":[support["id"]],"counter_evidence_ids":[counter["id"]],
            "source_ids":source_ids,
        })["id"]
        second=store.action("research-save",{
            "company":"NVDA","asof":"2025-03-01","question":"What explains the change?",
            "question_id":question,"conclusion":"Revised explanation","alternative":"Alternative mechanism",
            "next_evidence":"Check the next filing","change_reason":"New evidence changed weighting",
            "status":"challenged","parent_id":first,
            "supporting_evidence_ids":[support["id"]],"counter_evidence_ids":[counter["id"]],
            "source_ids":source_ids,
        })["id"]

        model=drivers.suggested(state)
        saved_driver=store.action("driver-save",{
            "company":"NVDA","asof":"2025-03-01",**model,
            "reason":"Demand and pricing operating hypothesis",
            "counter":"Competitors may absorb demand","trigger":"Actual results miss the model",
            "source_ids":["nv-fy25"],
        })["id"]

        sem=store.state("NVDA","2025-03-01")["semantic"]
        claim=next(x for x in sem["claims"] if x["id"]==second)
        assert claim["question_id"]==question
        assert claim["supporting_evidence_ids"]==[support["id"]]
        assert claim["counter_evidence_ids"]==[counter["id"]]

        driver=next(x for x in sem["drivers"] if x["id"]==saved_driver)
        assert driver["metadata"]["origin"]=="saved_driver_record"
        assert driver["status"]=="hypothesis"
        assert "revenue" in driver["linked_metric_ids"]

        revision=next(x for x in sem["revisions"] if x["id"]=="revision:"+second)
        assert revision["parent_revision_id"]=="revision:"+first
        assert sem["validation"]["ok"], sem["validation"]["issues"]

        broken=copy.deepcopy(sem)
        broken_driver=next(x for x in broken["drivers"] if x["id"]==saved_driver)
        broken_driver["linked_metric_ids"].append("missing_metric")
        assert not validate_snapshot(broken)["ok"]


def test_calculated_observation_dependency_lineage_is_machine_resolvable():
    with tempfile.TemporaryDirectory() as d:
        sem=Store(Path(d)/"research.sqlite3").state("AMD","2025-03-01")["semantic"]
        row=next(x for x in sem["observations"] if x["metric_id"]=="liabilities" and x["period"]=="FY2024")
        assert len(row["depends_on"])==2
        obs_ids={x["id"] for x in sem["observations"]}
        assert set(row["depends_on"])<=obs_ids
        assert sem["validation"]["ok"], sem["validation"]["issues"]


def test_manual_extraction_provenance_survives_to_semantic_contract():
    with tempfile.TemporaryDirectory() as d:
        store=Store(Path(d)/"research.sqlite3")
        draft=store.action("extraction-draft",{
            "company":"NVDA","asof":"2025-03-01","source_id":"nv-fy25",
            "period":"FY2025","period_start":"2024-01-29","period_end":"2025-01-26",
            "unit":"million","text":"营业收入：130497"
        })["id"]
        review=store.action("extraction-review",{
            "company":"NVDA","asof":"2025-03-01","id":draft,
            "decisions":[{"action":"accept","reason":"Matched source text"}]
        })["id"]
        store.action("extraction-import",{"company":"NVDA","asof":"2025-03-01","id":review})
        sem=store.state("NVDA","2025-03-01")["semantic"]
        row=next(x for x in sem["observations"] if x["provenance"].get("extraction_review_id")==review)
        assert row["provenance"]["quote"]
        assert row["provenance"]["parent_source_id"]=="nv-fy25"
        assert row["provenance"]["review_state"]=="pending_review"


if __name__=="__main__":
    test_semantic_snapshot_contract()
    test_claim_driver_and_revision_lineage_survive_projection()
    test_calculated_observation_dependency_lineage_is_machine_resolvable()
    test_manual_extraction_provenance_survives_to_semantic_contract()
    print("semantic contract tests passed")
