"""Research Atlas V3 semantic contract.

Typed, serializable objects shared by ingestion, finance logic, UI and later AI tools.
The contract intentionally stays relational; a graph database is not required.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional

SCHEMA_VERSION="3.3"

@dataclass(frozen=True)
class Company:
    id:str
    ticker:str
    name:str
    industry:str
    business_models:list
    currency:str
    accounting_basis:str
    scope:str
    cik:Optional[str]=None
    business_summary:Optional[str]=None
    business_source_ids:list=field(default_factory=list)
    business_review_state:str="unavailable"
    business_locator:Optional[str]=None
    metadata:dict=field(default_factory=dict)

@dataclass(frozen=True)
class Metric:
    id:str
    label:str
    statement:str
    unit_family:str
    comparison_policy:str
    aliases:list=field(default_factory=list)

@dataclass(frozen=True)
class Document:
    id:str
    company_id:str
    title:str
    url:str
    disclosed_at:str
    source_type:str
    form:Optional[str]=None
    accession:Optional[str]=None
    locator:Optional[str]=None
    metadata:dict=field(default_factory=dict)

@dataclass(frozen=True)
class Observation:
    id:str
    company_id:str
    metric_id:str
    document_id:str
    period:str
    period_type:str
    value:float
    currency:str
    unit:str
    accounting_basis:str
    scope:str
    value_kind:str
    review_state:str
    disclosed_at:str
    period_start:Optional[str]=None
    period_end:Optional[str]=None
    source_tag:Optional[str]=None
    formula:Optional[str]=None
    metadata:dict=field(default_factory=dict)

@dataclass(frozen=True)
class Segment:
    id:str
    company_id:str
    name:str
    business_model:Optional[str]=None
    parent_segment_id:Optional[str]=None
    source_ids:list=field(default_factory=list)
    review_state:str="pending_review"
    locator:Optional[str]=None
    excerpt:Optional[str]=None
    extraction_method:Optional[str]=None
    metadata:dict=field(default_factory=dict)

@dataclass(frozen=True)
class Product:
    id:str
    company_id:str
    name:str
    segment_id:Optional[str]=None
    category:Optional[str]=None
    source_ids:list=field(default_factory=list)
    review_state:str="pending_review"
    locator:Optional[str]=None
    excerpt:Optional[str]=None
    extraction_method:Optional[str]=None
    metadata:dict=field(default_factory=dict)

@dataclass(frozen=True)
class ContextEntity:
    id:str
    company_id:str
    entity_type:str
    name:str
    source_ids:list=field(default_factory=list)
    review_state:str="pending_review"
    locator:Optional[str]=None
    excerpt:Optional[str]=None
    metadata:dict=field(default_factory=dict)

@dataclass(frozen=True)
class Driver:
    id:str
    company_id:str
    name:str
    driver_type:str
    linked_metric_ids:list
    source_ids:list
    segment_id:Optional[str]=None
    product_id:Optional[str]=None
    model_parameter:Optional[str]=None
    status:str="hypothesis"
    metadata:dict=field(default_factory=dict)

@dataclass(frozen=True)
class ResearchQuestion:
    id:str
    company_id:str
    question:str
    status:str
    evidence_ids:list
    source_ids:list
    created_at:str
    reason:Optional[str]=None
    parent_id:Optional[str]=None
    metadata:dict=field(default_factory=dict)

@dataclass(frozen=True)
class Claim:
    id:str
    company_id:str
    conclusion:str
    status:str
    supporting_evidence_ids:list
    counter_evidence_ids:list
    source_ids:list
    created_at:str
    question_id:Optional[str]=None
    alternative:Optional[str]=None
    change_trigger:Optional[str]=None
    metadata:dict=field(default_factory=dict)

@dataclass(frozen=True)
class Revision:
    id:str
    company_id:str
    object_kind:str
    object_id:str
    created_at:str
    change_reason:str
    parent_revision_id:Optional[str]=None
    source_ids:list=field(default_factory=list)
    metadata:dict=field(default_factory=dict)

STATEMENTS={
    "revenue":"income","cost":"income","gross_profit":"income","opex":"income",
    "operating_income":"income","net_income":"income","non_gaap_op":"non_gaap",
    "cfo":"cash_flow","capex":"cash_flow","capex_principal":"cash_flow","da":"cash_flow",
    "sbc":"cash_flow","receivables":"balance_sheet","inventory":"balance_sheet",
    "payables":"balance_sheet","assets":"balance_sheet","liabilities":"balance_sheet",
    "equity":"balance_sheet","cash_securities":"balance_sheet","debt":"balance_sheet",
}
RATIO_METRICS={"gross_margin","op_margin","net_margin","cash_conversion","sbc_ratio"}

def metric_definition(metric_id,label):
    return Metric(
        id=metric_id,label=label,statement=STATEMENTS.get(metric_id,"derived_or_other"),
        unit_family="ratio" if metric_id in RATIO_METRICS else "currency_amount",
        comparison_policy="qualified" if metric_id in RATIO_METRICS else "requires_currency_period_scope_alignment",
    )

def _slug(value):
    return "".join(c.lower() if c.isalnum() else "-" for c in str(value)).strip("-") or "item"

def build_semantic_snapshot(state):
    profile=state["company"];ticker=profile["ticker"]
    company=Company(
        id=ticker,ticker=ticker,name=profile["name"],industry=profile.get("industry","unclassified"),
        business_models=list(profile.get("business_models",[])),currency=profile.get("currency","USD"),
        accounting_basis=profile.get("basis","GAAP"),scope=profile.get("scope","consolidated"),
        cik=profile.get("cik"),business_summary=profile.get("business_summary"),
        business_source_ids=list(profile.get("business_source_ids",[])),
        business_review_state=profile.get("business_review_state","unavailable"),
        business_locator=profile.get("business_locator"),
        metadata={"mode":profile.get("mode"),"subtitle":profile.get("subtitle"),"business_extraction_method":profile.get("business_extraction_method")},
    )
    metrics=[metric_definition(k,v) for k,v in state.get("metric_dictionary",{}).items()]
    metric_ids={m.id for m in metrics}
    documents=[
        Document(
            id=d["id"],company_id=ticker,title=d["title"],url=d["url"],disclosed_at=d["disclosed_at"],
            source_type=d.get("source_type","curated"),form=d.get("form"),accession=d.get("accession"),
            locator=d.get("locator"),metadata={k:d[k] for k in ["note","parent_source_id","filing_text_sha256","item1_section_sha256","item1_section_chars","business_extraction_state"] if d.get(k) is not None},
        ) for d in state.get("documents",[])
    ]
    document_ids={d.id for d in documents}
    observations=[]
    for o in state.get("observations",[]):
        if o.get("metric") not in metric_ids:
            continue
        observations.append(Observation(
            id=o["id"],company_id=ticker,metric_id=o["metric"],document_id=o["source_id"],
            period=o["period"],period_type=o.get("period_type","annual"),value=float(o["value"]),
            currency=o.get("currency",profile.get("currency","USD")),unit=o.get("unit","million"),
            accounting_basis=o.get("basis",profile.get("basis","GAAP")),scope=o.get("scope",profile.get("scope","consolidated")),
            value_kind=o.get("kind","Unknown"),review_state="reviewed" if o.get("reviewed") else "pending_review",
            disclosed_at=o.get("disclosed_at",""),period_start=o.get("period_start"),period_end=o.get("period_end"),
            source_tag=o.get("source_tag"),formula=o.get("formula"),
            metadata={k:o[k] for k in ["source_accession","version_count","restatement_candidate","selection_policy"] if o.get(k) is not None},
        ))
    observation_ids={o.id for o in observations}
    segments=[]
    segment_rows=profile.get("business_segments") or [s for s in profile.get("segments",[]) if s.get("semantic_role")!="consolidated_total"]
    for i,s in enumerate(segment_rows):
        sid=s.get("id") or f"{ticker}:segment:{_slug(s.get('key') or s.get('name') or i)}"
        src=[x for x in (s.get("source_ids") or ([s.get("source")] if s.get("source") else [])) if x in document_ids]
        segments.append(Segment(
            id=sid,company_id=ticker,name=s.get("name",sid),business_model=s.get("business_model"),
            source_ids=src,review_state=s.get("review_state","pending_review"),
            locator=s.get("locator"),excerpt=s.get("excerpt"),extraction_method=s.get("extraction_method"),
            metadata={k:s[k] for k in ["value","period","kind","formula","confidence","semantic_role"] if s.get(k) is not None},
        ))
    segment_ids={s.id for s in segments}
    products=[]
    for i,p in enumerate(profile.get("products",[])):
        pid=p.get("id") or f"{ticker}:product:{_slug(p.get('name') or i)}"
        products.append(Product(
            id=pid,company_id=ticker,name=p.get("name",pid),
            segment_id=p.get("segment_id") if p.get("segment_id") in segment_ids else None,
            category=p.get("category"),source_ids=[x for x in (p.get("source_ids") or ([p.get("source")] if p.get("source") else [])) if x in document_ids],
            review_state=p.get("review_state","pending_review"),locator=p.get("locator"),excerpt=p.get("excerpt"),
            extraction_method=p.get("extraction_method"),metadata={**p.get("metadata",{}),**{k:p[k] for k in ["confidence"] if p.get(k) is not None}},
        ))
    context_entities=[]
    allowed_context={"customer","competitor","geography","channel","risk"}
    for i,e in enumerate(profile.get("context_entities",[])):
        etype=str(e.get("entity_type","")).lower()
        if etype not in allowed_context:
            continue
        eid=e.get("id") or f"{ticker}:context:{etype}:{_slug(e.get('name') or i)}"
        context_entities.append(ContextEntity(
            id=eid,company_id=ticker,entity_type=etype,name=e.get("name",eid),
            source_ids=[x for x in (e.get("source_ids") or ([e.get("source")] if e.get("source") else [])) if x in document_ids],
            review_state=e.get("review_state","pending_review"),locator=e.get("locator"),excerpt=e.get("excerpt"),
            metadata={k:e[k] for k in ["confidence","relationship","scope"] if e.get(k) is not None},
        ))
    drivers=[]
    for i,d in enumerate(profile.get("market",[])):
        drivers.append(Driver(
            id=f"{ticker}:driver:{i+1}",company_id=ticker,name=d.get("title",f"Driver {i+1}"),
            driver_type=d.get("kind","research_hypothesis"),
            linked_metric_ids=[x for x in d.get("metric_ids",[]) if x in metric_ids],
            source_ids=[d["source"]] if d.get("source") in document_ids else [],
            model_parameter=d.get("driver"),status="hypothesis",metadata={"description":d.get("body","")},
        ))
    questions=[];claims=[];revisions=[]
    for r in state.get("records",[]):
        c=r.get("content",{});kind=r.get("kind");rid=r["id"];created=r.get("created_at","")
        if kind=="question":
            questions.append(ResearchQuestion(
                id=rid,company_id=ticker,question=c.get("question",""),status=c.get("status","open"),
                evidence_ids=[x for x in c.get("evidence_ids",[]) if x in observation_ids],
                source_ids=[x for x in c.get("source_ids",[]) if x in document_ids],created_at=created,
                reason=c.get("reason"),parent_id=c.get("parent_id"),metadata={"finding_id":c.get("finding_id")},
            ))
        elif kind in ("research","thesis"):
            claims.append(Claim(
                id=rid,company_id=ticker,conclusion=c.get("conclusion") or c.get("title") or "",
                status=c.get("status","open"),
                supporting_evidence_ids=[x for x in c.get("evidence_ids",[]) if x in observation_ids],
                counter_evidence_ids=[],source_ids=[x for x in c.get("source_ids",[]) if x in document_ids],
                created_at=created,question_id=c.get("question_id"),alternative=c.get("alternative") or c.get("counter"),
                change_trigger=c.get("next_evidence") or c.get("trigger"),metadata={"legacy_kind":kind},
            ))
        parent=c.get("parent_id");change=c.get("change_reason") or c.get("reason")
        if parent or change:
            revisions.append(Revision(
                id=f"revision:{rid}",company_id=ticker,object_kind=kind or "record",object_id=rid,
                created_at=created,change_reason=str(change or "New version"),parent_revision_id=parent,
                source_ids=[x for x in c.get("source_ids",[]) if x in document_ids],
            ))
    snapshot={
        "schema_version":SCHEMA_VERSION,"company":asdict(company),
        "metrics":[asdict(x) for x in metrics],"documents":[asdict(x) for x in documents],
        "observations":[asdict(x) for x in observations],"segments":[asdict(x) for x in segments],
        "products":[asdict(x) for x in products],"context_entities":[asdict(x) for x in context_entities],"drivers":[asdict(x) for x in drivers],
        "research_questions":[asdict(x) for x in questions],"claims":[asdict(x) for x in claims],
        "revisions":[asdict(x) for x in revisions],
    }
    snapshot["validation"]=validate_snapshot(snapshot)
    return snapshot

def validate_snapshot(snapshot):
    issues=[];company_id=snapshot["company"]["id"]
    metrics={x["id"] for x in snapshot["metrics"]};docs={x["id"] for x in snapshot["documents"]}
    observations={x["id"] for x in snapshot["observations"]};segments={x["id"] for x in snapshot["segments"]}
    for o in snapshot["observations"]:
        if o["company_id"]!=company_id:issues.append(f"Observation {o['id']} company mismatch")
        if o["metric_id"] not in metrics:issues.append(f"Observation {o['id']} missing Metric")
        if o["document_id"] not in docs:issues.append(f"Observation {o['id']} missing Document")
    if set(snapshot["company"].get("business_source_ids",[]))-docs:issues.append("Company business_summary missing Document refs")
    for s in snapshot["segments"]:
        if s["company_id"]!=company_id:issues.append(f"Segment {s['id']} company mismatch")
        if set(s.get("source_ids",[]))-docs:issues.append(f"Segment {s['id']} missing Document refs")
    for p in snapshot["products"]:
        if p["company_id"]!=company_id:issues.append(f"Product {p['id']} company mismatch")
        if p["segment_id"] and p["segment_id"] not in segments:issues.append(f"Product {p['id']} missing Segment")
        if set(p.get("source_ids",[]))-docs:issues.append(f"Product {p['id']} missing Document refs")
    for e in snapshot.get("context_entities",[]):
        if e["company_id"]!=company_id:issues.append(f"ContextEntity {e['id']} company mismatch")
        if set(e.get("source_ids",[]))-docs:issues.append(f"ContextEntity {e['id']} missing Document refs")
    for q in snapshot["research_questions"]:
        if set(q["evidence_ids"])-observations:issues.append(f"ResearchQuestion {q['id']} missing Observation refs")
        if set(q["source_ids"])-docs:issues.append(f"ResearchQuestion {q['id']} missing Document refs")
    return {
        "ok":not issues,"issues":issues,
        "object_counts":{k:len(snapshot[k]) for k in ["metrics","documents","observations","segments","products","context_entities","drivers","research_questions","claims","revisions"]},
    }
