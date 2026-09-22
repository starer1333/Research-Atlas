import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from atlas.industries import select_module,build_industry_view

def test_industry_module_selection():
    cases=[
        ({"mode":"hardware","industry":"semiconductors"},"semiconductor_hardware"),
        ({"mode":"software","industry":"software"},"saas_subscription"),
        ({"mode":"general","industry":"consumer retail"},"consumer_retail"),
        ({"mode":"automotive","industry":"automotive","sic":"3711"},"automotive"),
        ({"mode":"financial","industry":"bank"},"bank"),
    ]
    for profile,expected in cases:
        module,reason=select_module(profile)
        assert module==expected,(profile,module,reason)

def test_driver_contract_is_transparent():
    view=build_industry_view(
        {"mode":"hardware","industry":"semiconductors"},
        {"current":{"revenue":100,"gross_profit":60,"inventory":20}},
        [],
    )
    assert view["module_id"]=="semiconductor_hardware"
    assert len(view["drivers"])>=5
    for driver in view["drivers"]:
        assert driver["question"]
        assert driver["comparison"] in ["qualified","not_directly_comparable"]
        assert driver["status"]=="template"
        assert driver["is_company_fact"] is False
    inventory=next(d for d in view["drivers"] if d["id"]=="inventory_cycle")
    assert inventory["evidence_status"]=="financial_signal_available"

if __name__=="__main__":
    test_industry_module_selection()
    test_driver_contract_is_transparent()
    print("industry driver module tests passed")
