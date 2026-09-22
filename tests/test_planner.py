import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from atlas.planner import PlannerConfig, PlannerError, ResearchPlanner, build_grounded_context


def fixture_state():
    return {
        "company":{"ticker":"TEST","name":"Test Co","industry":"Software"},
        "asof":"2026-09-01",
        "documents":[{"id":"doc-1","title":"FY2025 annual report","disclosed_at":"2026-02-01","locator":"MD&A"}],
        "v3":{
            "summary":"Test summary",
            "business_map":{"business_summary":"Subscription software."},
            "findings":[{
                "id":"cash",
                "title":"Cash divergence",
                "statement":"Revenue grew faster than CFO.",
                "question":"Why did CFO lag revenue growth?",
                "evidence_ids":["obs-1"],
                "possible_mechanisms":["working capital"],
            }],
            "questions":["Why did CFO lag revenue growth?"],
            "industry_module":{"label":"SaaS / Subscription","drivers":[{"label":"Retention","question":"Is retention changing?","linked_metrics":["revenue"],"evidence_status":"template"}],"boundary":"Template is not fact."},
            "source_coverage":{"documents":1,"observations":1},
        },
    }


def test_grounded_context_is_compact_and_source_scoped():
    ctx=build_grounded_context(fixture_state(),"cash conversion")
    assert ctx["available_evidence_ids"]==["obs-1"]
    assert ctx["available_source_ids"]==["doc-1"]
    assert "raw_text" not in json.dumps(ctx)


def test_planner_validates_and_drops_unknown_references():
    def fake(url,headers,body,timeout):
        content={
            "summary":"Investigate cash conversion first.",
            "items":[{
                "question":"Why did CFO lag revenue growth?",
                "why_now":"A deterministic finding flagged divergence.",
                "evidence_to_check":["working-capital footnote"],
                "counter_evidence":["normal billing seasonality"],
                "suggested_actions":["open evidence","compare peer definitions"],
                "evidence_ids":["obs-1","hallucinated-observation"],
                "source_ids":["doc-1","fake-doc"],
            }]
        }
        return {"choices":[{"message":{"content":json.dumps(content)}}]}
    config=PlannerConfig.validate("https://example.ai/v1","secret","test-model")
    result=ResearchPlanner(config,transport=fake).plan(fixture_state())
    assert result["status"]=="ai_suggested"
    item=result["items"][0]
    assert item["evidence_ids"]==["obs-1"]
    assert item["source_ids"]==["doc-1"]
    assert item["fact_status"]=="not_verified"
    assert "reference_warning" in item


def test_planner_rejects_unsafe_base_url():
    try:
        PlannerConfig.validate("http://127.0.0.1:8000/v1","secret","model")
    except PlannerError:
        pass
    else:
        raise AssertionError("unsafe AI endpoint should be rejected")


if __name__=="__main__":
    test_grounded_context_is_compact_and_source_scoped()
    test_planner_validates_and_drops_unknown_references()
    test_planner_rejects_unsafe_base_url()
    print("Planner tests passed")
