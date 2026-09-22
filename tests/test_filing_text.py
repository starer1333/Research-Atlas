import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from atlas.sources.filing_text import analyze_10k_html

HTML="""
<html><body>
<div>TABLE OF CONTENTS</div>
<div>Item 1. Business</div><div>Item 1A. Risk Factors</div>
<h2>ITEM 1. BUSINESS</h2>
<p>Example Corp designs accelerated computing systems for enterprise and consumer markets. We sell hardware platforms and related software subscriptions through direct and channel relationships.</p>
<p>Our reportable segments are Compute Platforms and Cloud Software.</p>
<p>Our products include Atlas GPU, Nova Accelerator, and Orbit Studio.</p>
<p>We invest in a common software stack that supports these offerings across markets.</p>
<p>Our strategy is to connect product design, software, and distribution into a common platform that can support multiple workloads over time.</p>
<h2>ITEM 1A. RISK FACTORS</h2>
<p>Risks begin here.</p>
</body></html>
"""

def test_item1_business_and_candidates():
    out=analyze_10k_html(HTML,"sec:0001","https://www.sec.gov/example.htm")
    assert out["item1_found"]
    assert "accelerated computing systems" in out["business_summary"]
    segments={x["name"] for x in out["segments"]}
    products={x["name"] for x in out["products"]}
    assert {"Compute Platforms","Cloud Software"}<=segments
    assert {"Atlas GPU","Nova Accelerator","Orbit Studio"}<=products
    assert all(x["review_state"]=="pending_review" for x in out["segments"]+out["products"])
    assert out["section_chars"]>300

if __name__=="__main__":
    test_item1_business_and_candidates()
    print("10-K filing-text semantic extraction test passed")
