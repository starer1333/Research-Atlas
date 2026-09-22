"""Transform SEC EDGAR payloads into a conservative V3 Starter Research Pack."""
from datetime import datetime,timezone

SCHEMA_VERSION="3.4"
CORE_TAGS={
 "revenue":["RevenueFromContractWithCustomerExcludingAssessedTax","Revenues","SalesRevenueNet"],
 "cost":["CostOfRevenue","CostOfGoodsAndServicesSold","CostOfGoodsSold"],
 "gross_profit":["GrossProfit"],
 "operating_income":["OperatingIncomeLoss"],
 "net_income":["NetIncomeLoss","ProfitLoss"],
 "cfo":["NetCashProvidedByUsedInOperatingActivities"],
 "capex":["PaymentsToAcquirePropertyPlantAndEquipment","PaymentsToAcquireProductiveAssets"],
 "da":["DepreciationDepletionAndAmortization","DepreciationDepletionAndAmortizationPropertyPlantAndEquipment"],
 "sbc":["ShareBasedCompensation"],
 "receivables":["AccountsReceivableNetCurrent","AccountsNotesAndLoansReceivableNetCurrent"],
 "inventory":["InventoryNet"],
 "payables":["AccountsPayableCurrent"],
 "assets":["Assets"],
 "liabilities":["Liabilities"],
 "equity":["StockholdersEquity","StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
 "cash_securities":["CashAndCashEquivalentsAtCarryingValue","CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
}
DURATION={"revenue","cost","gross_profit","operating_income","net_income","cfo","capex","da","sbc"}

def _recent_filings(submissions):
    recent=submissions.get("filings",{}).get("recent",{})
    keys=["accessionNumber","filingDate","reportDate","form","primaryDocument","primaryDocDescription"]
    size=len(recent.get("accessionNumber",[]));rows=[]
    for i in range(size):
        row={k:(recent.get(k,[None]*size)[i] if i<len(recent.get(k,[])) else None) for k in keys}
        if row["accessionNumber"]:rows.append(row)
    return rows

def _filing_url(cik,accession,primary_document=None):
    cik_num=str(int(str(cik)));compact=accession.replace("-","")
    if primary_document:
        return f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{compact}/{primary_document}"
    return f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{compact}/{accession}-index.htm"

def latest_10k(company,submissions):
    rows=[r for r in _recent_filings(submissions) if r.get("form")=="10-K" and r.get("primaryDocument")]
    if not rows:return None
    row=max(rows,key=lambda x:x.get("filingDate") or "")
    accn=row["accessionNumber"]
    return {"id":"sec:"+accn,"accession":accn,"form":"10-K","filing_date":row.get("filingDate"),"report_date":row.get("reportDate"),"primary_document":row.get("primaryDocument"),"url":_filing_url(company["cik"],accn,row.get("primaryDocument"))}

def _slug(value):
    return "".join(c.lower() if c.isalnum() else "-" for c in str(value)).strip("-") or "item"

def build_starter_pack(company,submissions,facts,max_years=3,filing_analysis=None,filing_error=None):
    ticker=company["ticker"].upper();cik=str(company["cik"]).zfill(10)
    filings=_recent_filings(submissions);accepted_forms={"10-K","10-Q","8-K","DEF 14A"}
    documents=[]
    for r in filings:
        if r.get("form") not in accepted_forms:continue
        accn=r["accessionNumber"]
        documents.append({
            "id":"sec:"+accn,"company":ticker,"title":f"{ticker} {r.get('form')} · {r.get('filingDate')}",
            "url":_filing_url(cik,accn,r.get("primaryDocument")),"disclosed_at":r.get("filingDate"),
            "locator":f"SEC EDGAR accession {accn}","source_type":"sec-edgar","form":r.get("form"),
            "accession":accn,"report_date":r.get("reportDate"),
            "note":"Official SEC filing metadata; document text is not yet parsed by V3.",
        })
    document_ids={d["id"] for d in documents};usgaap=facts.get("facts",{}).get("us-gaap",{})
    candidates={};version_counts={}
    for metric,tags in CORE_TAGS.items():
        for priority,tag in enumerate(tags):
            for unit,rows in usgaap.get(tag,{}).get("units",{}).items():
                if unit!="USD":continue
                for row in rows:
                    if row.get("form")!="10-K" or row.get("fp")!="FY" or not row.get("fy") or not row.get("accn"):continue
                    if "sec:"+row["accn"] not in document_ids or row.get("val") is None or row.get("end") is None:continue
                    key=(int(row["fy"]),metric);version_counts[key]=version_counts.get(key,0)+1
                    score=(str(row.get("filed","")),-priority);existing=candidates.get(key)
                    if existing is None or score>existing[0]:candidates[key]=(score,tag,row)
    fiscal_years=sorted({fy for fy,_ in candidates})[-max_years:];windows={}
    for fy in fiscal_years:
        duration=[]
        for metric in DURATION:
            item=candidates.get((fy,metric))
            if item and item[2].get("start") and item[2].get("end"):duration.append(item[2])
        if duration:
            preferred=None
            for metric in ["revenue","net_income","cfo"]:
                item=candidates.get((fy,metric))
                if item and item[2].get("start"):preferred=item[2];break
            preferred=preferred or duration[0];windows[fy]={"start":preferred.get("start"),"end":preferred.get("end")}
        else:
            instant=[item[2] for (year,_),item in candidates.items() if year==fy]
            if instant:windows[fy]={"start":None,"end":instant[0].get("end")}
    observations=[]
    for fy in fiscal_years:
        for metric in CORE_TAGS:
            item=candidates.get((fy,metric))
            if not item:continue
            _,tag,row=item;accn=row["accn"];window=windows.get(fy,{})
            observations.append({
                "id":f"SEC-{ticker}-FY{fy}-{metric}-{accn}","company":ticker,"period":f"FY{fy}","period_type":"annual",
                "metric":metric,"value":float(row["val"])/1_000_000,"raw_value":row["val"],"raw_unit":"USD",
                "currency":"USD","unit":"million","scope":"consolidated","basis":"GAAP","kind":"Disclosed",
                "source_id":"sec:"+accn,"period_start":window.get("start"),"period_end":window.get("end") or row.get("end"),
                "source_tag":"us-gaap:"+tag,"source_accession":accn,"source_filed_at":row.get("filed"),
                "version_count":version_counts.get((fy,metric),1),"restatement_candidate":version_counts.get((fy,metric),1)>1,
                "selection_policy":"latest filed 10-K fact for fiscal year; canonical tag priority breaks same-file ties",
            })
        vals={o["metric"]:o for o in observations if o["period"]==f"FY{fy}"}
        if "gross_profit" in vals and "operating_income" in vals and "opex" not in vals:
            gp=vals["gross_profit"];op=vals["operating_income"]
            observations.append({
                "id":f"SEC-{ticker}-FY{fy}-opex-derived","company":ticker,"period":f"FY{fy}","period_type":"annual",
                "metric":"opex","value":gp["value"]-op["value"],"currency":"USD","unit":"million","scope":"consolidated","basis":"GAAP",
                "kind":"Calculated","source_id":gp["source_id"],"period_start":gp.get("period_start"),"period_end":gp.get("period_end"),
                "formula":"gross_profit - operating_income","depends_on":[gp["id"],op["id"]],"source_tag":"derived",
                "selection_policy":"calculated from selected SEC facts; not independently disclosed",
            })
    periods={f"FY{fy}":{"start":w.get("start"),"end":w.get("end")} for fy,w in windows.items()}
    docs_sorted=sorted(documents,key=lambda d:d["disclosed_at"] or "",reverse=True)
    asof=max([d["disclosed_at"] for d in docs_sorted if d.get("disclosed_at")] or [datetime.now(timezone.utc).date().isoformat()])
    sic=str(submissions.get("sic") or "");sic_num=int(sic) if sic.isdigit() else None
    mode="financial" if sic_num and 6000<=sic_num<6800 else "general"
    industry="financial" if mode=="financial" else ("SEC SIC "+sic if sic else "unclassified")
    business_segments=[];products=[];business_summary=None;business_source_ids=[]
    business_locator=None;business_review_state="unavailable";business_extraction_method=None
    if filing_analysis and filing_analysis.get("item1_found"):
        business_summary=filing_analysis.get("business_summary")
        business_source_ids=[filing_analysis["source_id"]]
        business_locator=filing_analysis.get("business_locator")
        business_review_state=filing_analysis.get("business_review_state","pending_review")
        business_extraction_method=filing_analysis.get("business_extraction_method")
        for row in filing_analysis.get("segments",[]):
            name=row["name"];business_segments.append({**row,"id":f"{ticker}:segment:{_slug(name)}","semantic_role":"business_segment"})
        for row in filing_analysis.get("products",[]):
            name=row["name"];products.append({**row,"id":f"{ticker}:product:{_slug(name)}","segment_id":None,"category":"10-K Item 1 candidate"})
    profile={
        "name":submissions.get("name") or company.get("name") or ticker,"ticker":ticker,"cik":cik,
        "currency":"USD","basis":"GAAP","scope":"consolidated","industry":industry,"mode":mode,
        "business_models":["待研究者根据 10-K 与行业语境确认"],
        "business_summary":business_summary,"business_source_ids":business_source_ids,
        "business_locator":business_locator,"business_review_state":business_review_state,
        "business_extraction_method":business_extraction_method,
        "subtitle":(submissions.get("sicDescription") or industry)+" / SEC EDGAR Starter Pack",
        "question":"增长、盈利和现金流是否相互支持？","segments":[],"business_segments":business_segments,"products":products,"context_entities":[],"market":[],
        "unknowns":[
            "Starter Pack 自动映射 SEC Company Facts 中可识别的核心财务指标。",
            "10-K Item 1 Business 采用确定性文本规则；Business/Segment/Product 候选仍需人工核验。",
            "客户、竞争、定价与完整分部注释尚未自动结构化。",
            "scope 暂按 consolidated 建模；使用前仍需在原始 filing 核对 XBRL context、重述和公司特定口径。",
        ],
        "operating_identity":"gp_less_opex","periods":periods,"tolerance":0.01,
        "source_adapter":"sec-edgar-direct","sic":sic,"sic_description":submissions.get("sicDescription"),
        "exchanges":submissions.get("exchanges",[]),
    }
    if filing_analysis:
        for d in documents:
            if d["id"]==filing_analysis.get("source_id"):
                d["filing_text_sha256"]=filing_analysis.get("content_sha256");d["item1_section_sha256"]=filing_analysis.get("section_sha256");d["item1_section_chars"]=filing_analysis.get("section_chars",0);d["business_extraction_state"]="candidate" if filing_analysis.get("item1_found") else "not_found"
                d["note"]="Official SEC filing metadata; Item 1 text parsed with deterministic V3-6 rules; semantic candidates require review."
    return {
        "schema_version":SCHEMA_VERSION,"adapter":"sec-edgar-direct","generated_at":datetime.now(timezone.utc).isoformat(),
        "asof":asof,"company":profile,"documents":docs_sorted,"observations":observations,
        "coverage":{
            "forms":{form:sum(d.get("form")==form for d in documents) for form in sorted(accepted_forms)},
            "mapped_metrics":sorted({o["metric"] for o in observations}),"fiscal_years":[f"FY{x}" for x in fiscal_years],
            "observation_documents":sorted({o["source_id"] for o in observations}),
            "filing_text":{"attempted":bool(filing_analysis or filing_error),"item1_found":bool(filing_analysis and filing_analysis.get("item1_found")),"source_id":filing_analysis.get("source_id") if filing_analysis else None,"section_chars":filing_analysis.get("section_chars",0) if filing_analysis else 0,"segment_candidates":len(business_segments),"product_candidates":len(products),"error":filing_error},
            "warnings":[
                "SEC Company Facts can contain multiple contexts/taxonomy tags; V3 keeps provenance and flags multiple candidate versions.",
                "Starter Pack is a research starting point, not audited normalization by Research Atlas.",
                "Item 1 Business/Segment/Product extraction is deterministic and candidate-only; human review remains required.",
            ],
        },
    }
