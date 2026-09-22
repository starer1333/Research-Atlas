"""Build an isolated, reproducible historical exercise. Never touches the user database."""
import sys,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from atlas.store import Store
from atlas.drivers import suggested

def main():
    folder=ROOT/'.runtime'/'research-case'/datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f');folder.mkdir(parents=True)
    store=Store(folder/'case.sqlite3')
    def act(route,**p):return store.action(route,{'company':'AMD','asof':'2025-03-01',**p})
    peer=act('comparison-save',peers=['NVDA','INTC'],nearby=True,reason='比较设计型与设计制造一体公司的利润、资本投入和数据口径；不生成竞争力排名。')
    base={**suggested(store.state('AMD','2025-03-01')),'source_ids':['amd-fy24'],'reason':'AI 起草的历史研究练习：销量指数每年 +10%、价格不变；仅作模型基准，年报不能证明这一销量预测。','counter':'产品组合、客户采购、供给与费用变化都可能解释收入和利润，现有资料不能区分实际量价。','trigger':'同口径实际收入偏离基准，或出现回款、存货、毛利率恶化时重新检验。'}
    first=act('driver-save',**base)
    stress={**base,'params':{**base['params'],'price_growth':-5},'parent_id':first['id'],'reason':'新增压力情景：价格指数每年 -5%，检验在销量增长下利润与现金是否仍稳健；不是事实性降价预测。'}
    second=act('driver-save',**stress)
    thesis={'question':'增长是否足以抵消价格与资金占用压力？','conclusion':'基准模型有正现金流，但需要对价格压力与回款作敏感性分析；当前不能确认竞争优势能持续。','alternative':'收入增长可能来自产品组合，量价指数不是实际经营披露。','next_evidence':'后续分部收入、毛利、应收与存货资料；关注合并范围变化。','change_reason':'建立练习判断','status':'open','source_ids':['amd-fy24'],'model_id':first['id']}
    initial=act('research-save',**thesis)
    guidance_url='https://ir.amd.com/financial-information/sec-filings/content/0000002488-25-000009/q42024991.htm'
    # The forecast is management guidance, not an independent historical prediction.
    forecast=act('forecast',period='FY2025Q1',low=6800,predicted=7100,high=7400,reason='历史管理层收入指引复盘，不是本人独立预测。来源：'+guidance_url)
    update={'id':'amd-q125-case','company':'AMD','title':'AMD Q1 2025 earnings release','url':'https://ir.amd.com/financial-information/sec-filings/content/0000002488-25-000045/q12025991.htm','disclosed_at':'2025-05-06','locator':'GAAP Quarterly Financial Results / Net revenue','observations':[{'id':'amd-q125-case-revenue','company':'AMD','period':'FY2025Q1','period_type':'quarterly','period_start':'2024-12-29','period_end':'2025-03-29','metric':'revenue','value':7438,'currency':'USD','unit':'million','scope':'consolidated','basis':'GAAP','kind':'Disclosed'}]}
    act('import',document=update)
    assert not any(o['period']=='FY2025Q1' for o in store.state('AMD','2025-03-01')['observations'])
    evaluation=act('evaluate',id=forecast['id'],asof='2025-06-01')['result']
    revised=act('research-save',**{**thesis,'asof':'2025-06-01','parent_id':initial['id'],'source_ids':['amd-fy24','amd-q125-case'],'model_id':second['id'],'conclusion':'已接入 Q1 收入高于管理层原指引上界，但收入单项不足以确认盈利质量或量价机制。保持待验证，不自动提高全年增长假设。','change_reason':'加入后续已披露收入；区分季度指引误差、全年经营压力情景与尚未解决的资金占用问题。'})
    software=store.state('ADBE','2025-03-01');soft=store.action('driver-save',{'company':'ADBE','asof':'2025-03-01',**suggested(software),'source_ids':['ad-fy24'],'reason':'第二商业模式验证：留存、扩张与新增客户为练习假设，基期收入暂作经常性运行率。','counter':'缺客户队列、合同期限与确认时点，不能宣称真实 NRR 或 ARR。','trigger':'补充客户及合同资料后重估确认节奏。'})
    manifest={'database':str(folder/'case.sqlite3'),'comparison_id':peer['id'],'driver_versions':[first['id'],second['id']],'research_versions':[initial['id'],revised['id']],'evaluation':evaluation,'software_version':soft['id'],'first_year_base':first['result']['rows'][0],'first_year_stress':second['result']['rows'][0],'change':second['result']['change'],'notice':'AI authored historical exercise. No user review claimed; no external model calls.'}
    (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (folder/'AMD-research.md').write_text(store.export('AMD','2025-06-01'),encoding='utf-8')
    (folder/'Adobe-model.md').write_text(store.export('ADBE','2025-03-01'),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
