"""V3-8 industry driver modules.

These modules are research templates, not company facts or forecasts. Selection is
rule-based and transparent; missing operating KPIs stay missing.
"""
from copy import deepcopy

UNIVERSAL_DIMENSIONS=[
    {"id":"growth","label":"Growth","metrics":["revenue"],"question":"增长来自数量、价格、组合还是并购/汇率？"},
    {"id":"profitability","label":"Profitability","metrics":["gross_profit","operating_income"],"question":"毛利率与经营利润率变化由什么机制驱动？"},
    {"id":"cash","label":"Cash conversion","metrics":["cfo","net_income"],"question":"利润是否转化为现金？"},
    {"id":"working_capital","label":"Working capital","metrics":["receivables","inventory","payables"],"question":"营运资金是在支持增长还是吸收现金？"},
    {"id":"capital","label":"Capital intensity","metrics":["capex","da","assets"],"question":"增长需要多少资本投入？"},
    {"id":"earnings_quality","label":"Earnings quality","metrics":["net_income","cfo","sbc"],"question":"非现金项目、股权激励和一次性事项如何影响利润质量？"},
]

def D(id,label,category,linked_metrics,question,kpis=(),comparison="qualified",source_requirements=(),model_parameter=None):
    return {
        "id":id,"label":label,"category":category,"linked_metrics":list(linked_metrics),
        "operating_kpis":list(kpis),"question":question,"comparison":comparison,
        "source_requirements":list(source_requirements),"model_parameter":model_parameter,
    }

MODULES={
 "semiconductor_hardware":{
   "label":"Semiconductor / Hardware","description":"量、价、产品组合、供应/制造与库存共同解释收入、毛利与现金。",
   "match":{"modes":["hardware"],"keywords":["semiconductor","chip","accelerated computing","hardware"],"sic_prefixes":["367"]},
   "drivers":[
      D("volume","Volume / demand","Growth",["revenue"],"出货量或计算需求变化如何影响收入？",["shipments","units","compute demand"],"qualified",["10-K business","earnings commentary"],"volume_growth"),
      D("asp","ASP / pricing","Growth",["revenue","gross_profit"],"价格、配置与折扣如何改变收入和毛利？",["ASP","price/mix"],"qualified",["product disclosures","management commentary"],"price_growth"),
      D("mix","Product mix","Profitability",["revenue","gross_profit"],"高/低毛利产品与终端组合如何改变毛利率？",["segment mix","product mix"],"qualified",["segment/product revenue"]),
      D("unit_cost","Unit cost / yield","Profitability",["cost","gross_profit"],"晶圆、封装、良率或制造利用率如何改变单位成本？",["wafer cost","yield","utilization"],"not_directly_comparable",["supply/manufacturing disclosures"],"unit_cost_growth"),
      D("inventory_cycle","Inventory / transition","Cash",["inventory","cfo","cost"],"库存是在为需求准备、产品切换，还是周转放缓？",["DIO","inventory write-downs"],"qualified",["inventory notes","product transition commentary"]),
      D("capex_supply","Capacity / CapEx","Capital",["capex","assets","cfo"],"扩产与供应承诺对资本强度和现金有何影响？",["capacity commitments","capex"],"qualified",["cash flow","PP&E/supply notes"]),
   ],
   "comparability":[
      "Revenue growth is comparable only after checking product/market scope.",
      "Gross margin is qualified by fabless vs integrated manufacturing model.",
      "Segment revenue is not market share and segment definitions may differ.",
   ],
 },
 "saas_subscription":{
   "label":"SaaS / Subscription","description":"经常性收入基础、留存、扩张、新客、价格与股权激励共同解释增长和利润。",
   "match":{"modes":["software"],"keywords":["software","saas","subscription","digital media"],"sic_prefixes":["737"]},
   "drivers":[
      D("recurring_base","Recurring revenue base","Growth",["revenue"],"经常性收入基础在扩大还是减弱？",["ARR","RPO","subscription revenue"],"not_directly_comparable",["10-K revenue disaggregation"]),
      D("retention","Retention / churn","Growth",["revenue"],"存量客户留存如何影响下一期收入基础？",["gross retention","logo retention"],"not_directly_comparable",["KPI disclosure"],"retention"),
      D("expansion","Expansion / NRR","Growth",["revenue"],"存量客户扩张和席位/用量增长贡献多少？",["NRR","DBNRR","seats","usage"],"not_directly_comparable",["KPI disclosure"],"expansion"),
      D("new_customers","New customers","Growth",["revenue","receivables"],"新客增长、合同长度和确认节奏如何转化为收入？",["new customers","bookings"],"not_directly_comparable",["customer/KPI disclosure"],"new_customer_rate"),
      D("pricing_packaging","Pricing / packaging","Profitability",["revenue","gross_profit"],"提价、套餐和 AI 增值如何影响 ARPU 与毛利？",["ARPU","price uplift"],"qualified",["product/pricing disclosures"]),
      D("sbc_opex","SBC / opex discipline","Earnings quality",["sbc","operating_income","cfo"],"股权激励和研发销售投入如何影响 GAAP 利润与现金？",["SBC/revenue","R&D/revenue","S&M/revenue"],"qualified",["cash flow","expense notes"]),
   ],
   "comparability":[
      "ARR/RPO definitions vary and must not be treated as identical to revenue.",
      "NRR/retention definitions and customer cohorts differ across issuers.",
      "GAAP margin comparisons need SBC and acquisition-accounting context.",
   ],
 },
 "consumer_retail":{
   "label":"Consumer / Retail","description":"门店/渠道、流量、转化、客单价、促销与库存共同解释销售和现金。",
   "match":{"modes":["consumer"],"keywords":["retail","consumer","store","restaurant","apparel"],"sic_prefixes":["53","54","56","58"]},
   "drivers":[
      D("footprint","Store / channel footprint","Growth",["revenue","assets"],"门店、渠道和可售面积变化贡献多少增长？",["store count","selling area","channel mix"],"qualified",["10-K properties/business"]),
      D("same_store","Same-store sales","Growth",["revenue"],"可比店增长来自流量还是客单价？",["same-store sales","comparable sales"],"not_directly_comparable",["KPI disclosure"]),
      D("traffic_conversion","Traffic / conversion","Growth",["revenue"],"流量和转化率如何变化？",["traffic","conversion"],"not_directly_comparable",["operating KPI"]),
      D("aov","AOV / price / mix","Growth",["revenue","gross_profit"],"客单价、提价与品类组合如何影响销售和毛利？",["AOV","basket size","price/mix"],"qualified",["KPI/product disclosures"]),
      D("promo_marketing","Promotion / marketing","Profitability",["gross_profit","operating_income"],"促销和获客投入是在换增长还是压缩利润？",["markdown rate","marketing spend"],"qualified",["expense/marketing disclosures"]),
      D("inventory_turn","Inventory turns","Cash",["inventory","cost","cfo"],"库存与销售增速是否匹配，清货压力是否上升？",["inventory turns","DIO"],"qualified",["inventory notes"]),
   ],
   "comparability":[
      "Same-store sales definitions, fiscal calendars and store cohorts differ.",
      "Gross margin comparisons require channel and private-label mix context.",
      "Inventory intensity varies materially by category and seasonality.",
   ],
 },
 "automotive":{
   "label":"Automotive","description":"销量、ASP/车型组合、材料与制造利用率、保修和资本开支共同解释盈利与现金。",
   "match":{"modes":["automotive"],"keywords":["automotive","vehicle","automobile","motor"],"sic_prefixes":["371"]},
   "drivers":[
      D("deliveries","Deliveries / volume","Growth",["revenue"],"交付量变化如何影响汽车业务收入？",["deliveries","wholesale units"],"qualified",["delivery/volume disclosure"]),
      D("vehicle_asp","ASP / model mix","Growth",["revenue","gross_profit"],"车型、地区和价格组合如何改变单车收入与毛利？",["ASP","model mix"],"qualified",["segment/product disclosures"]),
      D("materials","Battery / material cost","Profitability",["cost","gross_profit"],"电池、原材料和采购成本如何影响单位成本？",["battery cost","material cost"],"not_directly_comparable",["supply/cost commentary"]),
      D("utilization","Plant utilization","Profitability",["gross_profit","assets"],"产能利用率和爬坡如何影响制造吸收与毛利？",["capacity","utilization"],"not_directly_comparable",["manufacturing disclosures"]),
      D("warranty","Warranty / quality","Earnings quality",["cost","operating_income"],"保修与召回准备如何影响盈利质量？",["warranty reserve","recall cost"],"qualified",["warranty notes"]),
      D("auto_capex","CapEx / capacity","Capital",["capex","assets","cfo"],"新工厂和平台投资对资本强度与 FCF 有何影响？",["capex","installed capacity"],"qualified",["cash flow","PP&E notes"]),
   ],
   "comparability":[
      "Delivery definitions can differ between wholesale, retail and production.",
      "Automotive gross margin may include credits/services differently.",
      "Capital intensity depends on manufacturing ownership and vertical integration.",
   ],
 },
 "bank":{
   "label":"Bank / Financial Institution","description":"资产负债表驱动业务：贷款、存款、息差、信用成本、资本与费用效率是核心。",
   "match":{"modes":["financial"],"keywords":["bank","financial institution","lender"],"sic_prefixes":["60","61","62"]},
   "drivers":[
      D("loan_growth","Loan growth","Growth",["assets"],"贷款余额增长来自哪些资产类别与风险偏好？",["loans","average earning assets"],"qualified",["balance sheet/loan notes"]),
      D("nim","Net interest margin","Profitability",[],"资产收益率、存款成本和资金结构如何改变 NIM？",["NIM","asset yield","deposit cost"],"not_directly_comparable",["bank KPI disclosure"]),
      D("deposit_mix","Deposit mix / funding","Profitability",["liabilities"],"低成本存款占比和批发融资如何影响资金成本？",["deposits","deposit beta","funding mix"],"qualified",["deposit/funding notes"]),
      D("credit_cost","Credit losses / NPL","Risk",[],"不良、逾期和拨备变化是否反映信用周期转弱？",["NPL","NCO","provision","allowance"],"qualified",["credit quality notes"]),
      D("fees","Fee income","Growth",["revenue"],"非息收入的结构与周期敏感度如何变化？",["fee income mix"],"qualified",["income statement/segment notes"]),
      D("capital","Capital adequacy","Capital",["equity"],"资本充足率和风险加权资产如何约束增长与分红？",["CET1","RWA","capital ratios"],"not_directly_comparable",["regulatory capital disclosures"]),
   ],
   "comparability":[
      "General-enterprise gross margin/FCFF logic is disabled for banks.",
      "NIM, credit metrics and capital ratios require bank-specific definitions.",
      "Cross-bank comparisons need portfolio mix, geography and regulatory context.",
   ],
 },
 "general":{
   "label":"General company","description":"使用通用财务核心；行业 operating KPI 需要研究者补充。",
   "match":{"modes":["general"],"keywords":[],"sic_prefixes":[]},
   "drivers":[
      D("revenue_mechanism","Revenue mechanism","Growth",["revenue"],"增长由数量、价格、组合还是并购/汇率驱动？",["volume","price","mix"],"qualified",["business/segment disclosure"]),
      D("margin_mechanism","Margin mechanism","Profitability",["gross_profit","operating_income"],"毛利与经营利润变化来自哪些成本和经营机制？",["gross margin drivers"],"qualified",["MD&A/cost disclosures"]),
      D("cash_mechanism","Cash conversion","Cash",["cfo","receivables","inventory","payables"],"利润与现金流之间的差异由什么解释？",["working capital"],"qualified",["cash flow/working capital notes"]),
      D("capital_mechanism","Capital intensity","Capital",["capex","assets"],"增长需要多少资本投入？",["capex intensity"],"qualified",["cash flow/PP&E notes"]),
   ],
   "comparability":["Use metric-level comparability gates before peer interpretation."],
 },
}

def _text(profile):
    values=[
        profile.get("industry",""),profile.get("subtitle",""),profile.get("sic_description",""),
        " ".join(profile.get("business_models",[])),
    ]
    return " ".join(str(x).lower() for x in values if x)

def select_module(profile):
    text=_text(profile);mode=str(profile.get("mode","general")).lower();sic=str(profile.get("sic",""))
    if mode=="financial":return "bank","mode=financial"
    scored=[]
    for module_id,module in MODULES.items():
        if module_id=="general":continue
        score=0;reasons=[]
        if mode in module["match"].get("modes",[]):score+=6;reasons.append("mode="+mode)
        for prefix in module["match"].get("sic_prefixes",[]):
            if sic.startswith(prefix):score+=5;reasons.append("SIC "+sic)
        for keyword in module["match"].get("keywords",[]):
            if keyword in text:score+=2;reasons.append("keyword="+keyword)
        scored.append((score,module_id,reasons))
    score,module_id,reasons=max(scored,key=lambda x:x[0])
    if score<=0:return "general","no deterministic industry match"
    return module_id,", ".join(reasons[:3])

def build_industry_view(profile,diagnostics,observations):
    module_id,reason=select_module(profile);module=deepcopy(MODULES[module_id])
    available=set(diagnostics.get("current",{}))
    for o in observations:available.add(o.get("metric"))
    for driver in module["drivers"]:
        observed=[m for m in driver["linked_metrics"] if m in available]
        driver["observed_metrics"]=observed
        driver["evidence_status"]="financial_signal_available" if observed else "needs_operating_evidence"
        driver["is_company_fact"]=False
        driver["status"]="template"
    return {
        "module_id":module_id,"label":module["label"],"description":module["description"],
        "selection_reason":reason,"universal_dimensions":deepcopy(UNIVERSAL_DIMENSIONS),
        "drivers":module["drivers"],"comparability":module["comparability"],
        "boundary":"Industry drivers are research templates, not disclosed company facts.",
    }
