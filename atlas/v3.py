"""V3 presentation contract: deterministic diagnostics, source coverage and guided research questions.

This module does not call an LLM and does not mark evidence as verified.
It converts existing point-in-time state into user-facing research signals.
"""
from .engine import ratio, rounded

def _growth(current, previous, key):
    if key not in current or key not in previous or previous.get(key) in (None, 0):
        return None
    return round((current[key] / previous[key] - 1) * 100, 2)

def _evidence_ids(observations, metrics, periods):
    wanted=set(metrics); periods=set(periods)
    return [o["id"] for o in observations if o.get("metric") in wanted and o.get("period") in periods]

def _priority(materiality=1, divergence=1, industry=1, evidence=1, gap=0):
    parts={
        "materiality":materiality,
        "divergence":divergence,
        "industry_relevance":industry,
        "evidence_quality":evidence,
        "data_gap_penalty":gap,
    }
    parts["total"]=materiality+divergence+industry+evidence-gap
    return parts

def _level(score):
    if score >= 8:
        return "high"
    if score >= 5:
        return "watch"
    return "info"

def build_findings(profile, diagnostics, observations):
    years=diagnostics.get("years",[])
    if not years:
        return []
    current=diagnostics.get("current",{})
    previous=diagnostics.get("previous",{})
    current_year=years[-1]
    previous_year=years[-2] if len(years)>1 else None
    periods=[p for p in [current_year,previous_year] if p]
    reviewed=sum(bool(o.get("reviewed")) for o in observations if o.get("period") in periods)
    relevant=sum(1 for o in observations if o.get("period") in periods)
    evidence_quality=2 if relevant and reviewed==relevant else 1
    findings=[]

    def add(ident,category,title,statement,why,metrics,question,mechanisms,priority):
        ids=_evidence_ids(observations,metrics,periods)
        findings.append({
            "id":ident,
            "category":category,
            "title":title,
            "statement":statement,
            "why":why,
            "metrics":metrics,
            "question":question,
            "possible_mechanisms":mechanisms,
            "evidence_ids":ids,
            "priority":priority,
            "severity":_level(priority["total"]),
            "basis":"Deterministic diagnostic; not a final research conclusion.",
        })

    rev_g=_growth(current,previous,"revenue")
    cfo_g=_growth(current,previous,"cfo")
    ar_g=_growth(current,previous,"receivables")
    inv_g=_growth(current,previous,"inventory")
    cost_g=_growth(current,previous,"cost")

    if rev_g is not None and cfo_g is not None and rev_g-cfo_g >= 10:
        gap=round(rev_g-cfo_g,1)
        p=_priority(2,3 if gap>=20 else 2,2,evidence_quality,0)
        add(
            "cash-conversion-divergence","Cash conversion","利润与现金的增长出现分化",
            "收入同比约 +%.1f%%，经营现金流同比约 +%.1f%%，两者相差 %.1f 个百分点。" % (rev_g,cfo_g,gap),
            "增长没有以相同速度转化为经营现金流，值得继续检查营运资金和业务结构，而不是直接判断现金流质量恶化。",
            ["revenue","cfo","receivables","inventory","payables"],
            "为什么收入增长没有同步转化为经营现金流？",
            ["客户付款条件或客户结构变化","存货提前备货或产品切换","应付节奏变化","一次性现金流时点差异"],
            p,
        )

    if rev_g is not None and ar_g is not None and ar_g-rev_g >= 10:
        gap=round(ar_g-rev_g,1)
        p=_priority(2,3 if gap>=20 else 2,2,evidence_quality,0)
        add(
            "receivables-vs-revenue","Working capital","应收账款增速快于收入",
            "应收账款同比约 +%.1f%%，比收入增速高 %.1f 个百分点。" % (ar_g,gap),
            "这可能反映回款节奏、客户组合或收入确认时点变化，需要查看披露和同行趋势。",
            ["receivables","revenue","cfo"],
            "应收账款为什么比收入增长更快？",
            ["付款条件变化","客户集中度或客户结构变化","季末收入节奏","业务增长带来的正常资金占用"],
            p,
        )

    baseline=cost_g if cost_g is not None else rev_g
    if baseline is not None and inv_g is not None and inv_g-baseline >= 10:
        gap=round(inv_g-baseline,1)
        p=_priority(2,3 if gap>=20 else 2,2,evidence_quality,0)
        add(
            "inventory-divergence","Working capital","存货增速高于业务基准",
            "存货同比约 +%.1f%%，比%s增速高 %.1f 个百分点。" % (inv_g,"营业成本" if cost_g is not None else "收入",gap),
            "存货变化既可能是需求准备，也可能来自产品切换、交付节奏或渠道变化，不能只凭余额做风险结论。",
            ["inventory","cost","revenue","cfo"],
            "存货增长是在为未来需求准备，还是反映周转变化？",
            ["提前备货","产品生命周期切换","供应链策略","需求或渠道节奏变化"],
            p,
        )

    if previous.get("revenue") and previous.get("gross_profit") is not None and current.get("revenue") and current.get("gross_profit") is not None:
        old=ratio(previous["gross_profit"],previous["revenue"])
        new=ratio(current["gross_profit"],current["revenue"])
        if old is not None and new is not None and abs(new-old)>=2:
            delta=round(new-old,1)
            p=_priority(2,2,2,evidence_quality,0)
            add(
                "gross-margin-shift","Profitability","毛利率发生明显变化",
                "毛利率从 %.1f%% 变为 %.1f%%，变化 %+.1f 个百分点。" % (old,new,delta),
                "毛利率变化通常需要结合价格、产品组合、成本、规模和会计分类解释。",
                ["revenue","gross_profit","cost"],
                "什么因素解释了毛利率的变化？",
                ["产品组合与价格","投入成本","规模或利用率","业务/地区组合","会计分类变化"],
                p,
            )

    cash_conversion=diagnostics.get("ratios",{}).get("cash_conversion")
    if cash_conversion is not None and current.get("net_income",0)>0 and cash_conversion<80:
        p=_priority(2,2,1,evidence_quality,0)
        add(
            "earnings-cash-conversion","Earnings quality","净利润向经营现金流的转化偏弱",
            "经营现金流 / 净利润约为 %.1f%%。" % cash_conversion,
            "单期现金转化偏低不等于利润失真；应先检查营运资金、非现金项目和时点因素。",
            ["net_income","cfo","receivables","inventory","payables"],
            "净利润和经营现金流为什么存在差异？",
            ["营运资金变化","非现金费用","税费与付款时点","业务组合变化"],
            p,
        )

    segments=profile.get("segments",[])
    revenue=current.get("revenue")
    if revenue and segments:
        largest=max((s.get("value",0) for s in segments),default=0)
        share=largest/revenue*100 if revenue else 0
        if share>=60:
            top=max(segments,key=lambda s:s.get("value",0))
            p=_priority(2,1,2,evidence_quality,0)
            add(
                "segment-concentration","Segment economics","收入集中在主要业务板块",
                "%s 约占当前收入 %.1f%%。" % (top.get("name","主要业务"),share),
                "高集中度并非好坏判断，但会让该业务的需求、价格和竞争变化更重要。",
                ["revenue"],
                "主要业务板块的增长驱动是否可持续？",
                ["终端需求","价格与产品组合","客户集中度","竞争与替代方案"],
                p,
            )

    findings.sort(key=lambda x:(x["priority"]["total"],len(x["evidence_ids"])),reverse=True)
    return findings[:5]

def build_v3_view(profile,diagnostics,periods,observations,documents,relations):
    findings=build_findings(profile,diagnostics,observations)
    questions=[]
    for item in findings:
        if item["question"] not in questions:
            questions.append(item["question"])
    if profile.get("question") and profile["question"] not in questions:
        questions.append(profile["question"])
    questions=questions[:5]

    trajectory=[]
    for year in diagnostics.get("years",[]):
        row=periods.get(year,{})
        trajectory.append({
            "period":year,
            "revenue":row.get("revenue"),
            "gross_margin":ratio(row.get("gross_profit"),row.get("revenue")),
            "operating_margin":ratio(row.get("operating_income"),row.get("revenue")),
            "cfo":row.get("cfo"),
            "inventory":row.get("inventory"),
            "receivables":row.get("receivables"),
        })

    checks=relations.get("checks",[])
    coverage={k:sum(c.get("status")==k for c in checks) for k in ["pass","fail","missing"]}
    integrity_status="attention" if coverage["fail"] else "partial" if coverage["missing"] else "ok"
    reviewed=sum(bool(o.get("reviewed")) for o in observations)
    source_coverage={
        "documents":len(documents),
        "latest_disclosed_at":max((d.get("disclosed_at","") for d in documents),default=None),
        "observations":len(observations),
        "reviewed":reviewed,
        "pending_review":len(observations)-reviewed,
    }
    business_models=profile.get("business_models",[])
    summary=("当前档案将 %s 归类为 %s；主要商业模式：%s。" %
             (profile.get("name",profile.get("ticker","公司")),profile.get("industry","待分类"),
              "、".join(business_models) if business_models else "待补充"))
    return {
        "summary":summary,
        "business_map":{
            "industry":profile.get("industry"),
            "business_models":business_models,
            "segments":profile.get("segments",[]),
            "unknowns":profile.get("unknowns",[]),
        },
        "trajectory":trajectory,
        "findings":findings,
        "questions":questions,
        "source_coverage":source_coverage,
        "data_integrity":{
            "status":integrity_status,
            "coverage":coverage,
            "definition":"用于发现提取、映射、单位、期间或口径问题；通过勾稽不等于公司财务质量良好。",
        },
        "interaction_contract":["WHY","EVIDENCE","COMPARE","ADD_TO_RESEARCH"],
        "boundary":"System proposes; human decides. Calculated is not disclosed; candidate is not verified.",
    }
