import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from atlas.sources.starter import build_starter_pack

def fixture():
    company={"ticker":"TEST","name":"Test Corp","cik":"0000001234"}
    submissions={
      "name":"Test Corp","sic":"3674","sicDescription":"Semiconductors","exchanges":["Nasdaq"],
      "filings":{"recent":{
        "accessionNumber":["0000001234-25-000001","0000001234-24-000001"],
        "filingDate":["2025-02-20","2024-02-20"],"reportDate":["2024-12-31","2023-12-31"],
        "form":["10-K","10-K"],"primaryDocument":["test-20241231.htm","test-20231231.htm"],
        "primaryDocDescription":["Annual report","Annual report"]
      }}
    }
    def rows(v24,v23,instant=False):
        a={"fy":2024,"fp":"FY","form":"10-K","filed":"2025-02-20","end":"2024-12-31","val":v24,"accn":"0000001234-25-000001"}
        b={"fy":2023,"fp":"FY","form":"10-K","filed":"2024-02-20","end":"2023-12-31","val":v23,"accn":"0000001234-24-000001"}
        if not instant:a.update(start="2024-01-01");b.update(start="2023-01-01")
        return [a,b]
    facts={"facts":{"us-gaap":{
      "RevenueFromContractWithCustomerExcludingAssessedTax":{"units":{"USD":rows(120_000_000,100_000_000)}},
      "GrossProfit":{"units":{"USD":rows(72_000_000,60_000_000)}},
      "OperatingIncomeLoss":{"units":{"USD":rows(30_000_000,25_000_000)}},
      "NetIncomeLoss":{"units":{"USD":rows(24_000_000,20_000_000)}},
      "NetCashProvidedByUsedInOperatingActivities":{"units":{"USD":rows(26_000_000,21_000_000)}},
      "Assets":{"units":{"USD":rows(300_000_000,250_000_000,True)}},
      "Liabilities":{"units":{"USD":rows(120_000_000,110_000_000,True)}},
      "StockholdersEquity":{"units":{"USD":rows(180_000_000,140_000_000,True)}}
    }}}
    return company,submissions,facts

def test_build_starter_pack():
    company,submissions,facts=fixture()
    analysis={
      "source_id":"sec:0000001234-25-000001","item1_found":True,
      "business_summary":"Test Corp designs semiconductor systems and software.",
      "business_locator":"Form 10-K · Item 1. Business","business_review_state":"pending_review",
      "business_extraction_method":"10-k-item1-leading-paragraphs","section_chars":1200,
      "content_sha256":"a"*64,"section_sha256":"b"*64,
      "segments":[{"name":"Compute","source":"sec:0000001234-25-000001","source_ids":["sec:0000001234-25-000001"],"locator":"Form 10-K · Item 1. Business","excerpt":"Our reportable segments are Compute and Software.","review_state":"pending_review","extraction_method":"10-k-item1-explicit-list","confidence":"candidate"}],
      "products":[{"name":"Atlas GPU","source":"sec:0000001234-25-000001","source_ids":["sec:0000001234-25-000001"],"locator":"Form 10-K · Item 1. Business","excerpt":"Our products include Atlas GPU.","review_state":"pending_review","extraction_method":"10-k-item1-explicit-list","confidence":"candidate"}],
    }
    pack=build_starter_pack(company,submissions,facts,filing_analysis=analysis)
    assert pack["schema_version"]=="3.4"
    assert pack["company"]["ticker"]=="TEST"
    assert pack["adapter"]=="sec-edgar-direct"
    assert pack["coverage"]["fiscal_years"]==["FY2023","FY2024"]
    metrics={o["metric"] for o in pack["observations"]}
    assert {"revenue","gross_profit","operating_income","opex","assets","liabilities","equity"}<=metrics
    assert all(o["source_id"].startswith("sec:") for o in pack["observations"])
    assert all(o["unit"]=="million" for o in pack["observations"])
    assert pack["company"]["business_summary"].startswith("Test Corp")
    assert pack["company"]["business_segments"][0]["id"].startswith("TEST:segment:")
    assert pack["company"]["products"][0]["name"]=="Atlas GPU"
    assert pack["coverage"]["filing_text"]["item1_found"]

if __name__=="__main__":
    test_build_starter_pack()
    print("SEC starter-pack transform test passed")
