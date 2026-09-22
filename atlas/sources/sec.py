"""Direct SEC EDGAR SourceAdapter.

Network access is opt-in. Only fixed sec.gov endpoints are allowed.
"""
import gzip,json
from urllib.request import Request,urlopen
from urllib.parse import urlparse
from .base import SourceAdapter,SourceAdapterError
from .starter import build_starter_pack

ALLOWED_HOSTS={"www.sec.gov","data.sec.gov"}

class SecEdgarAdapter(SourceAdapter):
    adapter_id="sec-edgar-direct"
    def __init__(self,user_agent,timeout=20):
        user_agent=str(user_agent or "").strip()
        if len(user_agent)<8:
            raise SourceAdapterError("SEC adapter requires a descriptive User-Agent, e.g. 'ResearchAtlas contact@example.com'")
        self.user_agent=user_agent;self.timeout=timeout;self._ticker_cache=None
    def _json(self,url):
        parsed=urlparse(url)
        if parsed.scheme!="https" or parsed.hostname not in ALLOWED_HOSTS:
            raise SourceAdapterError("SEC adapter rejected a non-SEC endpoint")
        req=Request(url,headers={"User-Agent":self.user_agent,"Accept":"application/json","Accept-Encoding":"gzip"})
        try:
            with urlopen(req,timeout=self.timeout) as response:
                raw=response.read()
                if response.headers.get("Content-Encoding")=="gzip":raw=gzip.decompress(raw)
                return json.loads(raw.decode("utf-8"))
        except Exception as e:
            raise SourceAdapterError("SEC EDGAR request failed: "+str(e))
    def _tickers(self):
        if self._ticker_cache is None:
            payload=self._json("https://www.sec.gov/files/company_tickers.json")
            self._ticker_cache=list(payload.values()) if isinstance(payload,dict) else payload
        return self._ticker_cache
    def resolve_company(self,query):
        q=str(query or "").strip()
        if not q:raise SourceAdapterError("Enter a ticker or company name")
        rows=self._tickers();upper=q.upper()
        exact=[x for x in rows if str(x.get("ticker","")).upper()==upper]
        if not exact:exact=[x for x in rows if str(x.get("title","")).strip().lower()==q.lower()]
        if not exact:
            partial=[x for x in rows if q.lower() in str(x.get("title","")).lower()]
            if len(partial)==1:exact=partial
        if not exact:raise SourceAdapterError("SEC company resolver found no unique match")
        row=exact[0]
        return {"ticker":str(row["ticker"]).upper(),"name":row.get("title"),"cik":str(row["cik_str"]).zfill(10)}
    def discover_documents(self,company):
        cik=str(company["cik"]).zfill(10)
        return self._json(f"https://data.sec.gov/submissions/CIK{cik}.json")
    def company_facts(self,company):
        cik=str(company["cik"]).zfill(10)
        return self._json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
    def starter_pack(self,query):
        company=self.resolve_company(query)
        return build_starter_pack(company,self.discover_documents(company),self.company_facts(company))
