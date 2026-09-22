"""V3-10 optional AI research planner.

The planner is intentionally outside the deterministic finance/evidence core.
It can suggest research questions and evidence-gathering steps, but it cannot
write observations, mark evidence reviewed, calculate finance, or create final
claims. Nothing is persisted until the user explicitly saves a question.
"""
from dataclasses import dataclass
import ipaddress
import json
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class PlannerError(ValueError):
    pass


def _text(value, limit):
    value = str(value or "").strip()
    return value[:limit]


def _list(value, limit=6, item_limit=240):
    if not isinstance(value, list):
        return []
    out = []
    for item in value[:limit]:
        item = _text(item, item_limit)
        if item:
            out.append(item)
    return out


def _safe_base_url(value):
    value = str(value or "").strip().rstrip("/")
    parts = urlsplit(value)
    if parts.scheme != "https" or not parts.hostname:
        raise PlannerError("AI base URL must be an explicit https endpoint")
    host = parts.hostname.lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise PlannerError("AI base URL cannot target localhost/private development hosts")
    try:
        address = ipaddress.ip_address(host)
        if address.is_private or address.is_loopback or address.is_link_local:
            raise PlannerError("AI base URL cannot target a private IP")
    except ValueError:
        pass
    return value


@dataclass(frozen=True)
class PlannerConfig:
    base_url: str
    api_key: str
    model: str
    timeout: int = 25

    @classmethod
    def validate(cls, base_url, api_key, model, timeout=25):
        if not str(api_key or "").strip():
            raise PlannerError("AI Research Planner requires ATLAS_AI_API_KEY")
        if not str(model or "").strip():
            raise PlannerError("AI Research Planner requires ATLAS_AI_MODEL")
        return cls(_safe_base_url(base_url), str(api_key).strip(), str(model).strip(), int(timeout))


def build_grounded_context(state, focus=None):
    v3 = state.get("v3", {})
    findings = []
    for finding in v3.get("findings", [])[:5]:
        findings.append({
            "id": finding.get("id"),
            "title": _text(finding.get("title"), 180),
            "statement": _text(finding.get("statement"), 420),
            "question": _text(finding.get("question"), 320),
            "evidence_ids": list(finding.get("evidence_ids", []))[:20],
            "possible_mechanisms": _list(finding.get("possible_mechanisms", []), 6, 180),
        })
    documents = [{
        "id": d.get("id"),
        "title": _text(d.get("title"), 220),
        "disclosed_at": d.get("disclosed_at"),
        "locator": _text(d.get("locator"), 180),
    } for d in state.get("documents", [])[:16]]
    module = v3.get("industry_module", {})
    drivers = [{
        "label": _text(d.get("label"), 160),
        "question": _text(d.get("question"), 260),
        "linked_metrics": list(d.get("linked_metrics", []))[:8],
        "evidence_status": d.get("evidence_status"),
    } for d in module.get("drivers", [])[:8]]
    evidence_ids = sorted({eid for f in findings for eid in f.get("evidence_ids", []) if eid})
    source_ids = [d["id"] for d in documents if d.get("id")]
    return {
        "company": {
            "ticker": state.get("company", {}).get("ticker"),
            "name": state.get("company", {}).get("name"),
            "industry": state.get("company", {}).get("industry"),
        },
        "research_as_of": state.get("asof"),
        "focus": _text(focus, 360) if focus else None,
        "summary": _text(v3.get("summary"), 720),
        "business_summary": _text(v3.get("business_map", {}).get("business_summary"), 1200),
        "findings": findings,
        "current_questions": [_text(q, 320) for q in v3.get("questions", [])[:5]],
        "industry_module": {
            "label": module.get("label"),
            "drivers": drivers,
            "boundary": _text(module.get("boundary"), 420),
        },
        "source_coverage": v3.get("source_coverage", {}),
        "documents": documents,
        "available_evidence_ids": evidence_ids,
        "available_source_ids": source_ids,
    }


def _extract_json(content):
    content = str(content or "").strip()
    fence = chr(96) * 3
    if content.startswith(fence):
        content = content.strip(chr(96))
        if content.lower().startswith("json"):
            content = content[4:].lstrip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        raise PlannerError("AI planner returned non-JSON content")


def validate_plan(payload, context):
    if not isinstance(payload, dict):
        raise PlannerError("AI planner response must be a JSON object")
    raw_items = payload.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise PlannerError("AI planner response must include a non-empty items array")
    allowed_evidence = set(context.get("available_evidence_ids", []))
    allowed_sources = set(context.get("available_source_ids", []))
    items = []
    for raw in raw_items[:5]:
        if not isinstance(raw, dict):
            continue
        question = _text(raw.get("question"), 320)
        if len(question) < 8:
            continue
        raw_evidence = _list(raw.get("evidence_ids", []), 20, 120)
        raw_sources = _list(raw.get("source_ids", []), 20, 120)
        bad = [x for x in raw_evidence if x not in allowed_evidence] + [x for x in raw_sources if x not in allowed_sources]
        item = {
            "question": question,
            "why_now": _text(raw.get("why_now"), 520),
            "evidence_to_check": _list(raw.get("evidence_to_check", []), 6, 260),
            "counter_evidence": _list(raw.get("counter_evidence", []), 6, 260),
            "suggested_actions": _list(raw.get("suggested_actions", []), 6, 220),
            "evidence_ids": [x for x in raw_evidence if x in allowed_evidence],
            "source_ids": [x for x in raw_sources if x in allowed_sources],
            "status": "ai_suggested",
            "fact_status": "not_verified",
        }
        if bad:
            item["reference_warning"] = "Dropped unknown evidence/source IDs: " + ", ".join(bad[:8])
        items.append(item)
    if not items:
        raise PlannerError("AI planner did not return any usable research questions")
    return {
        "status": "ai_suggested",
        "summary": _text(payload.get("summary"), 700),
        "items": items,
        "boundary": "AI output is a research plan, not a fact, calculation, verification decision or final judgment.",
    }


class ResearchPlanner:
    def __init__(self, config, transport=None):
        self.config = config
        self.transport = transport or self._http_transport

    def capability(self):
        host = urlsplit(self.config.base_url).hostname
        return {
            "enabled": True,
            "provider": "openai-compatible",
            "model": self.config.model,
            "host": host,
            "writes_facts": False,
            "persists_automatically": False,
        }

    def _endpoint(self):
        if self.config.base_url.endswith("/chat/completions"):
            return self.config.base_url
        return self.config.base_url + "/chat/completions"

    def _http_transport(self, url, headers, body, timeout):
        request = Request(url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers=headers, method="POST")
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def plan(self, state, focus=None):
        context = build_grounded_context(state, focus)
        system = (
            "You are the optional Research Atlas research planner. Produce research questions and evidence-gathering steps only. "
            "Never invent facts, never calculate financial metrics, never mark evidence verified, never issue investment recommendations, "
            "and never claim that a mechanism is proven. Use only evidence/source IDs provided in the context. "
            "Return JSON only with keys summary and items. Each item must contain question, why_now, evidence_to_check, "
            "counter_evidence, suggested_actions, evidence_ids, source_ids. Return 3-5 items."
        )
        body = {
            "model": self.config.model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False, separators=(",", ":"))},
            ],
        }
        response = self.transport(
            self._endpoint(),
            {"Authorization": "Bearer " + self.config.api_key, "Content-Type": "application/json"},
            body,
            self.config.timeout,
        )
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise PlannerError("AI planner response does not match the OpenAI-compatible chat format")
        result = validate_plan(_extract_json(content), context)
        result.update({"provider": "openai-compatible", "model": self.config.model})
        return result
