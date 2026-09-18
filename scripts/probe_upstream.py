"""Execute two pinned upstream modules on synthetic fixtures; never calls an API.
No upstream code is copied into the Research Atlas production engine.
"""
import sys,json,importlib.util
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'upstream/FinRobot/finrobot_equity/core/src/modules'
def module(name):
    spec=importlib.util.spec_from_file_location(name,BASE/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
p=module('financial_data_processor');v=module('valuation_engine')
frame=pd.DataFrame([{'date':'2025-01-31','year':2025,'revenue':100,'costOfRevenue':50,'grossProfit':50,'operatingExpenses':30,'sellingGeneralAndAdministrativeExpenses':10,'ebitda':20,'eps':0}])
result=p.extract_historical_metrics_from_api_data({'income_statement':frame});eps=result.loc[result.metrics=='EPS','2025A'].iloc[0]
data={'free_cash_flow':0,'ebitda':100,'shares_outstanding':10}
zero=v.ValuationEngine(data).calculate_dcf_valuation();sixty=v.ValuationEngine({**data,'free_cash_flow':60}).calculate_dcf_valuation()
base=v.ValuationEngine({**data,'free_cash_flow':60}).calculate_dcf_valuation();higher=v.ValuationEngine({**data,'free_cash_flow':60}).calculate_dcf_valuation({'wacc':.11})
out={'commit':'6d6ccd32c1b8b1904dc656cf06897438aba3daec','mode':'unmodified upstream modules, synthetic local fixtures; no API or report generation','zero_eps_became_missing':bool(pd.isna(eps)),'zero_fcf_price':zero.target_price,'explicit_60_fcf_price':sixty.target_price,'zero_fcf_replaced_by_fallback':zero.target_price==sixty.target_price,'reported_low_at_wacc_plus_1pp':base.low_estimate,'full_recalculation_at_wacc_plus_1pp':higher.target_price,'reported_range_matches_full_recalculation':abs(base.low_estimate-higher.target_price)<1e-8}
print(json.dumps(out,ensure_ascii=False,indent=2))
