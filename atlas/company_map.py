"""V3-7 Company / Product Map projection.

The map is a navigational research graph, not a claim that every edge is verified.
Evidence-backed semantic nodes and template driver nodes are visually/status separated.
"""

def _node(ident,kind,label,status="unknown",source_ids=None,meta=None):
    return {
        "id":ident,"kind":kind,"label":label,"status":status,
        "source_ids":list(source_ids or []),"meta":meta or {},
    }

def _edge(source,relation,target,status="structural",source_ids=None,note=None):
    return {
        "source":source,"relation":relation,"target":target,"status":status,
        "source_ids":list(source_ids or []),"note":note,
    }

def build_company_map(semantic,industry_view):
    company=semantic["company"];cid="company:"+company["id"]
    nodes=[_node(cid,"company",company["name"],company.get("business_review_state","unavailable"),company.get("business_source_ids",[]),{
        "ticker":company["ticker"],"industry":company["industry"],"summary":company.get("business_summary"),
    })]
    edges=[]

    segment_ids=set()
    for s in semantic.get("segments",[]):
        sid="segment:"+s["id"];segment_ids.add(s["id"])
        nodes.append(_node(sid,"segment",s["name"],s.get("review_state","pending_review"),s.get("source_ids",[]),{
            "locator":s.get("locator"),"excerpt":s.get("excerpt"),"business_model":s.get("business_model"),
        }))
        edges.append(_edge(cid,"HAS_SEGMENT",sid,"evidence_linked",s.get("source_ids",[])))

    product_nodes=[]
    for p in semantic.get("products",[]):
        pid="product:"+p["id"];product_nodes.append(pid)
        nodes.append(_node(pid,"product",p["name"],p.get("review_state","pending_review"),p.get("source_ids",[]),{
            "category":p.get("category"),"locator":p.get("locator"),"excerpt":p.get("excerpt"),
        }))
        if p.get("segment_id") in segment_ids:
            edges.append(_edge("segment:"+p["segment_id"],"OFFERS",pid,"evidence_linked",p.get("source_ids",[])))
        else:
            edges.append(_edge(cid,"OFFERS",pid,"unlinked_segment",p.get("source_ids",[]),"Product is not yet mapped to a verified segment."))

    context_ids=set()
    for entity in semantic.get("context_entities",[]):
        eid="context:"+entity["id"];context_ids.add(entity["id"])
        nodes.append(_node(eid,entity["entity_type"],entity["name"],entity.get("review_state","pending_review"),entity.get("source_ids",[]),{
            "locator":entity.get("locator"),"excerpt":entity.get("excerpt"),
        }))
        edges.append(_edge(cid,"HAS_CONTEXT",eid,"evidence_linked",entity.get("source_ids",[])))

    metric_ids={m["id"] for m in semantic.get("metrics",[])}
    used_metrics=[]
    for driver in industry_view.get("drivers",[]):
        did="driver-template:"+driver["id"]
        nodes.append(_node(did,"driver",driver["label"],"template",[],{
            "category":driver["category"],"question":driver["question"],
            "evidence_status":driver["evidence_status"],"operating_kpis":driver["operating_kpis"],
            "comparison":driver["comparison"],
        }))
        edges.append(_edge(cid,"RESEARCH_WITH",did,"template",[],industry_view["label"]))
        for metric in driver.get("linked_metrics",[]):
            if metric not in metric_ids:continue
            mid="metric:"+metric
            if metric not in used_metrics:
                metric_def=next(m for m in semantic["metrics"] if m["id"]==metric)
                nodes.append(_node(mid,"metric",metric_def["label"],"canonical_metric",[],{
                    "statement":metric_def["statement"],"comparison_policy":metric_def["comparison_policy"],
                }))
                used_metrics.append(metric)
            edges.append(_edge(did,"AFFECTS",mid,"template",[],"Mechanism to investigate; not established causality."))

    # Existing company-specific driver hypotheses remain distinct from industry templates.
    for d in semantic.get("drivers",[]):
        did="driver:"+d["id"]
        nodes.append(_node(did,"driver",d["name"],d.get("status","hypothesis"),d.get("source_ids",[]),{
            "driver_type":d.get("driver_type"),"model_parameter":d.get("model_parameter"),**d.get("metadata",{}),
        }))
        edges.append(_edge(cid,"HAS_DRIVER_HYPOTHESIS",did,"research_hypothesis",d.get("source_ids",[])))
        for metric in d.get("linked_metric_ids",[]):
            if metric in metric_ids:
                mid="metric:"+metric
                if metric not in used_metrics:
                    metric_def=next(m for m in semantic["metrics"] if m["id"]==metric)
                    nodes.append(_node(mid,"metric",metric_def["label"],"canonical_metric",[],{
                        "statement":metric_def["statement"],"comparison_policy":metric_def["comparison_policy"],
                    }))
                    used_metrics.append(metric)
                edges.append(_edge(did,"AFFECTS",mid,"hypothesis",d.get("source_ids",[])))

    layers=[
        {"id":"company","label":"Company","node_ids":[n["id"] for n in nodes if n["kind"]=="company"]},
        {"id":"business","label":"Segments / Products","node_ids":[n["id"] for n in nodes if n["kind"] in ["segment","product"]]},
        {"id":"context","label":"Context","node_ids":[n["id"] for n in nodes if n["kind"] in ["customer","competitor","geography","channel","risk"]]},
        {"id":"drivers","label":"Operating Drivers","node_ids":[n["id"] for n in nodes if n["kind"]=="driver"]},
        {"id":"financials","label":"Financial Outcomes","node_ids":[n["id"] for n in nodes if n["kind"]=="metric"]},
    ]
    return {
        "nodes":nodes,"edges":edges,"layers":layers,
        "counts":{layer["id"]:len(layer["node_ids"]) for layer in layers},
        "industry_module":industry_view["module_id"],
        "boundary":"Evidence-backed nodes, research hypotheses and industry templates are different states; the map does not collapse them into one truth layer.",
    }
