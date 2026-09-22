"""Deterministic SEC 10-K text extraction for V3-6.

This module intentionally produces candidates, not verified business semantics.
It uses only Python stdlib so Research Atlas keeps a zero-install local path.
"""
import hashlib,re
from html.parser import HTMLParser

BLOCK_TAGS={"p","div","br","tr","td","th","li","ul","ol","table","section","article","h1","h2","h3","h4","h5","h6"}
SKIP_TAGS={"script","style","noscript","svg","ix:header","ix:hidden","xbrli:context","xbrli:unit"}
GENERIC={
    "products","product","services","service","solutions","solution","offerings","offering",
    "business","businesses","segment","segments","platform","platforms","customers","customer",
    "hardware","software","technology","technologies","other","others","operations",
}
ITEM1=re.compile(r"(?im)(?:^|\n)\s*item\s+1\s*[\.\:\-–—]?\s*business\b[^\n]*")
ITEM1A=re.compile(r"(?im)(?:^|\n)\s*item\s+1a\s*[\.\:\-–—]?\s*risk\s+factors\b[^\n]*")

class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        tag=tag.lower()
        if tag in SKIP_TAGS:self.skip+=1
        elif not self.skip and tag in BLOCK_TAGS:self.parts.append("\n")
    def handle_endtag(self,tag):
        tag=tag.lower()
        if tag in SKIP_TAGS and self.skip:self.skip-=1
        elif not self.skip and tag in BLOCK_TAGS:self.parts.append("\n")
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)

def html_to_text(html):
    parser=_TextParser();parser.feed(str(html or ""))
    text="".join(parser.parts).replace("\xa0"," ")
    lines=[]
    for line in text.splitlines():
        line=re.sub(r"[ \t\r\f\v]+"," ",line).strip()
        if line:lines.append(line)
    return "\n".join(lines)

def _section_candidates(text):
    starts=list(ITEM1.finditer(text));out=[]
    for start in starts:
        nxt=ITEM1A.search(text,start.end())
        if not nxt:continue
        section=text[start.end():nxt.start()].strip()
        if 300<=len(section)<=350000:out.append(section)
    return out

def extract_item1_business(text):
    candidates=_section_candidates(text)
    if candidates:return max(candidates,key=len)
    loose=re.compile(r"(?is)\bitem\s+1\s*[\.\:\-–—]?\s*business\b")
    loose_next=re.compile(r"(?is)\bitem\s+1a\s*[\.\:\-–—]?\s*risk\s+factors\b")
    out=[]
    for start in loose.finditer(text):
        nxt=loose_next.search(text,start.end())
        if nxt:
            section=text[start.end():nxt.start()].strip()
            if 300<=len(section)<=350000:out.append(section)
    return max(out,key=len) if out else ""

def _paragraphs(section):
    rows=[]
    for raw in section.split("\n"):
        line=re.sub(r"\s+"," ",raw).strip(" •·\t")
        if len(line)<70:continue
        if re.match(r"(?i)^item\s+\d",line):continue
        if re.search(r"(?i)table of contents",line):continue
        rows.append(line)
    if len(rows)>=2:return rows
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+(?=[A-Z])",re.sub(r"\s+"," ",section)) if len(x.strip())>=70]

def business_excerpt(section,max_chars=2600):
    chosen=[];size=0
    for p in _paragraphs(section):
        if size+len(p)>max_chars and chosen:break
        chosen.append(p);size+=len(p)+2
        if len(chosen)>=4:break
    return "\n\n".join(chosen)[:max_chars].strip()

def _sentences(section):
    flat=re.sub(r"\s+"," ",section)
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])",flat) if 35<=len(x.strip())<=1200]

def _clean_name(value):
    value=re.sub(r"^[\s:;,.\-–—]+|[\s:;,.\-–—]+$","",value)
    value=re.sub(r"(?i)^(?:and|or|the|our|its|a|an|following|three|four|five|six|two)\s+","",value)
    value=re.sub(r"(?i)\s+(?:reportable|operating|business)?\s*segments?$","",value)
    return re.sub(r"\s+"," ",value).strip()

def _split_names(fragment,kind):
    fragment=re.split(r"(?i)\b(?:which|where|that|whose|because|while)\b",fragment,1)[0]
    fragment=fragment.strip(" :;.-")
    parts=re.split(r"\s*;\s*|\s*,\s*|\s+and\s+(?=(?:[A-Z0-9]|the\s+[A-Z]))",fragment)
    out=[]
    for part in parts:
        name=_clean_name(part);words=name.split()
        if not (2<=len(name)<=90 and 1<=len(words)<=10):continue
        low=re.sub(r"[^a-z]+"," ",name.lower()).strip()
        if low in GENERIC or low.startswith("following "):continue
        if not re.search(r"[A-Za-z]",name):continue
        if re.search(r"(?i)\b(?:fiscal year|year ended|million|billion|revenue|percentage)\b",name):continue
        if kind=="product" and low in {"hardware","software","cloud services","professional services"}:continue
        out.append(name)
    seen=[];keys=set()
    for name in out:
        key=re.sub(r"\W+","",name.lower())
        if key and key not in keys:keys.add(key);seen.append(name)
    return seen[:10]

SEGMENT_PATTERNS=[
    re.compile(r"(?i)\b(?:our\s+)?(?:reportable|operating|business)\s+segments?\s+(?:are|include|consist\s+of|comprise)\s*[:\-]?\s*(.+)"),
    re.compile(r"(?i)\bwe\s+(?:operate|manage|report)\s+(?:our\s+business\s+)?(?:through|in)\s+(?:the\s+following\s+)?(?:reportable\s+|operating\s+)?segments?\s*[:\-]\s*(.+)"),
]
PRODUCT_PATTERNS=[
    re.compile(r"(?i)\b(?:our\s+)?(?:products|platforms|services|offerings|solutions)\s+(?:include|are|consist\s+of|comprise)\s*[:\-]?\s*(.+)"),
    re.compile(r"(?i)\bwe\s+offer\s+(?:the\s+following\s+)?(?:products|platforms|services|offerings|solutions)\s*[:\-]?\s*(.+)"),
]

def _extract_explicit(section,patterns,kind,source_id,locator):
    rows=[];seen=set()
    for sentence in _sentences(section):
        for pattern in patterns:
            match=pattern.search(sentence)
            if not match:continue
            names=_split_names(match.group(1),kind)
            if not (1<=len(names)<=8):continue
            for name in names:
                key=re.sub(r"\W+","",name.lower())
                if not key or key in seen:continue
                seen.add(key)
                rows.append({
                    "name":name,"source":source_id,"source_ids":[source_id],"locator":locator,
                    "excerpt":sentence[:700],"review_state":"pending_review",
                    "extraction_method":"10-k-item1-explicit-list","confidence":"candidate",
                })
    return rows[:12]

def analyze_10k_html(html,source_id,source_url=None):
    text=html_to_text(html);section=extract_item1_business(text)
    locator="Form 10-K · Item 1. Business"
    if not section:
        return {
            "source_id":source_id,"source_url":source_url,"item1_found":False,
            "business_summary":None,"segments":[],"products":[],
            "content_sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "section_chars":0,"warnings":["Could not isolate Item 1. Business with deterministic heading rules."],
        }
    return {
        "source_id":source_id,"source_url":source_url,"item1_found":True,
        "business_summary":business_excerpt(section),
        "business_locator":locator,"business_review_state":"pending_review",
        "business_extraction_method":"10-k-item1-leading-paragraphs",
        "segments":_extract_explicit(section,SEGMENT_PATTERNS,"segment",source_id,locator),
        "products":_extract_explicit(section,PRODUCT_PATTERNS,"product",source_id,locator),
        "content_sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "section_sha256":hashlib.sha256(section.encode("utf-8")).hexdigest(),
        "section_chars":len(section),
        "warnings":[
            "Business text is a deterministic filing excerpt, not an LLM summary.",
            "Segment/Product rows are lexical candidates and remain pending_review until a researcher confirms them.",
        ],
    }
