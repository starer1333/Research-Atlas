import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from atlas.company_map import build_company_map
from atlas.industries import build_industry_view
from atlas.store import Store

def test_store_exposes_v3_7_map_and_v3_8_module():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        state=Store(Path(d)/"research.sqlite3").state("NVDA","2025-03-01")
        assert state["v3"]["industry_module"]["module_id"]=="semiconductor_hardware"
        cmap=state["v3"]["company_map"]
        assert cmap["industry_module"]=="semiconductor_hardware"
        assert cmap["counts"]["company"]==1
        assert cmap["counts"]["drivers"]>=5
        assert any(e["relation"]=="AFFECTS" for e in cmap["edges"])
        # Consolidated fallback rows must not masquerade as semantic segments.
        assert all("合并或主体总收入" not in n["label"] for n in cmap["nodes"] if n["kind"]=="segment")

def test_product_segment_context_edges():
    semantic={
      "company":{"id":"TEST","ticker":"TEST","name":"Test Co","industry":"software","business_summary":"x","business_source_ids":["doc1"],"business_review_state":"pending_review"},
      "metrics":[{"id":"revenue","label":"Revenue","statement":"income","comparison_policy":"qualified"}],
      "segments":[{"id":"TEST:segment:cloud","name":"Cloud","source_ids":["doc1"],"review_state":"pending_review"}],
      "products":[{"id":"TEST:product:atlas","name":"Atlas","segment_id":"TEST:segment:cloud","source_ids":["doc1"],"review_state":"pending_review","category":"SaaS"}],
      "context_entities":[{"id":"TEST:context:competitor:peer","entity_type":"competitor","name":"Peer","source_ids":["doc1"],"review_state":"pending_review"}],
      "drivers":[],
    }
    industry=build_industry_view({"mode":"software","industry":"software"},{"current":{"revenue":10}},[])
    cmap=build_company_map(semantic,industry)
    assert any(e["relation"]=="OFFERS" and e["source"].startswith("segment:") for e in cmap["edges"])
    assert any(n["kind"]=="competitor" for n in cmap["nodes"])
    assert cmap["counts"]["business"]==2

if __name__=="__main__":
    test_store_exposes_v3_7_map_and_v3_8_module()
    test_product_segment_context_edges()
    print("company map tests passed")
