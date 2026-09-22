"""Curated historical disclosures, checked against linked primary sources on 2026-09-18.
Machine-transcribed and pending user review; no claim of current investment coverage.
"""
NV_URL = 'https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-fourth-quarter-and-fiscal-2025'
AD_URL = 'https://www.adobe.com/cc-shared/assets/investor-relations/pdfs/11214202/bi645trh3w45e.pdf'
Q1_URL = 'https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-first-quarter-fiscal-2026'

COMPANIES = {
 'NVDA': {'name':'NVIDIA','subtitle':'加速计算 / 硬件与平台','mode':'hardware','asof':'2025-03-01','question':'高速增长能否穿越产品切换，并保持现金创造能力？','segments':[{'key':'data_center','name':'数据中心','value':115200,'previous':None,'source':'nv-fy25','precision':'公告舍入至 0.1 十亿美元'},{'key':'other','name':'其他业务（含舍入差额）','value':15297,'previous':None,'source':'nv-fy25','kind':'Calculated','formula':'130497 - 115200'}], 'unknowns':['未接入 GPU 实际销量与成交均价，不能做精确量价分解。','没有独立第三方市场规模和竞争份额证据，不能把收入占比当市场份额。','数据中心为市场平台收入分类，不等同于财报经营分部。'], 'market':[{'title':'需求侧','body':'云基础设施采购与计算需求 → 数据中心收入。需求持续性是待验证机制，不能仅凭管理层表态确认。','source':'nv-fy25','kind':'研究假说','driver':'growth_0'},{'title':'产品与供给','body':'产品切换、产能与交付结构 → 实现收入与毛利率。缺少量价数据时使用披露收入分组。','source':'nv-fy25','kind':'研究假说','driver':'gross_margin'},{'title':'经营约束','body':'应收及库存增加会占用资金。需要同时核对销售增长、采购与回款期间。','source':'nv-fy25','kind':'可计算关系','driver':'nwc_ratio'}]},
 'ADBE': {'name':'Adobe','subtitle':'数字创作 / 企业体验软件','mode':'software','asof':'2025-03-01','question':'经常性业务增长，能否转化为可持续的 GAAP 利润？','segments':[{'key':'digital_media','name':'Digital Media','value':15864,'previous':14216,'source':'ad-fy24'},{'key':'digital_experience','name':'Digital Experience','value':5366,'previous':4893,'source':'ad-fy24'},{'key':'publishing','name':'Publishing & Advertising','value':275,'previous':300,'source':'ad-fy24'}], 'unknowns':['没有客户级留存和扩张明细，不编造 NRR 或客户流失率。','ARR 使用固定汇率计量，年度之间须对齐重估基准，不能直接当作收入。','当前案例未接入资产负债表及全年现金流量表，相关诊断留空。'], 'market':[{'title':'创作与文档','body':'产品使用价值、付费意愿和替代工具 → 数字媒体收入；AI 变现对价格和留存的影响待验证。','source':'ad-fy24','kind':'研究假说','driver':'growth_0'},{'title':'企业采购','body':'企业数字体验需求与合同履约 → 数字体验收入；RPO 与 ARR 不直接等于本期收入。','source':'ad-fy24','kind':'研究假说','driver':'growth_1'},{'title':'利润质量','body':'GAAP 与 Non-GAAP 经营利润存在调整差异，需要识别股权激励与收购相关费用。','source':'ad-fy24','kind':'披露线索','driver':'opex_ratio'}]}
}

DOCUMENTS = [
 {'id':'nv-fy25','company':'NVDA','title':'NVIDIA FY2025 业绩公告','url':NV_URL,'disclosed_at':'2025-02-26','locator':'年度损益表、资产负债表、现金流量表；Data Center 小节','excerpt':'Revenue; Gross profit; Net cash provided by operating activities.','note':'网页表格无页码；金额 USD million；GAAP、合并；比较数的可用日期按本次来源披露日保守处理。'},
 {'id':'ad-fy24','company':'ADBE','title':'Adobe FY2024 Investor Relations Data Sheet','url':AD_URL,'disclosed_at':'2024-12-11','locator':'第 2 页：分部收入；第 3 页：GAAP / Non-GAAP 勾稽','excerpt':'Total Revenue; Digital Media; Operating income.','note':'PDF 表格金额 USD million；年度列 FY2024 / FY2023；GAAP、合并。未使用不同汇率基准 ARR 做增长计算。'}
]

LABELS = {'revenue':'营业收入','cost':'营业成本','gross_profit':'毛利润','opex':'经营费用','operating_income':'经营利润','net_income':'净利润','cfo':'经营活动现金流','capex':'购建固定及无形资产支出','capex_principal':'相关资产本金支付','da':'折旧摊销','sbc':'股权激励费用','receivables':'应收账款','inventory':'存货','payables':'应付账款','cash_securities':'现金及可交易证券','debt':'有息债务','assets':'总资产','liabilities':'总负债','equity':'股东权益','non_gaap_op':'Non-GAAP 经营利润','acquisition_adjustment':'收购相关经营费用调整'}

DATA = {
 'NVDA':{'FY2024':{'revenue':60922,'cost':16621,'gross_profit':44301,'opex':11329,'operating_income':32972,'net_income':29760,'cfo':28090,'capex':1069,'capex_principal':74,'da':1508,'sbc':3549,'receivables':9999,'inventory':5282,'payables':2699,'cash_securities':25984,'debt':9709,'assets':65728,'liabilities':22750,'equity':42978},'FY2025':{'revenue':130497,'cost':32639,'gross_profit':97858,'opex':16405,'operating_income':81453,'net_income':72880,'cfo':64089,'capex':3236,'capex_principal':129,'da':1864,'sbc':4737,'receivables':23065,'inventory':10080,'payables':6310,'cash_securities':43210,'debt':8463,'assets':111601,'liabilities':32274,'equity':79327}},
 'ADBE':{'FY2023':{'revenue':19409,'cost':2354,'gross_profit':17055,'opex':10405,'operating_income':6650,'net_income':5428,'sbc':1735,'non_gaap_op':8918,'acquisition_adjustment':116},'FY2024':{'revenue':21505,'cost':2358,'gross_profit':19147,'opex':12406,'operating_income':6741,'net_income':5560,'sbc':1881,'non_gaap_op':10019,'acquisition_adjustment':1007}}
}

def observations():
    rows=[]
    for company,periods in DATA.items():
        for period,metrics in periods.items():
            for metric,value in metrics.items():
                rows.append({'id':f'{company}-{period}-{metric}','company':company,'period':period,'period_type':'annual','metric':metric,'label':LABELS[metric],'value':value,'currency':'USD','unit':'million','scope':'consolidated','basis':'non-GAAP' if metric=='non_gaap_op' else 'GAAP','kind':'Calculated' if company=='NVDA' and metric=='debt' else 'Disclosed','source_id':'nv-fy25' if company=='NVDA' else 'ad-fy24','formula':'short-term debt + long-term debt' if company=='NVDA' and metric=='debt' else None})
    return rows

DEMO_UPDATE = {'id':'nv-q1-26','company':'NVDA','title':'NVIDIA Q1 FY2026 业绩公告（后续证据）','url':Q1_URL,'disclosed_at':'2025-05-28','locator':'GAAP 季度摘要：Revenue','excerpt':'Revenue','note':'后续材料；不能用于 2025-03-01 的研究输入。','observations':[{'id':'NVDA-FY2026Q1-revenue','company':'NVDA','period':'FY2026Q1','period_type':'quarterly','metric':'revenue','label':'营业收入','value':44062,'currency':'USD','unit':'million','scope':'consolidated','basis':'GAAP','kind':'Disclosed'}]}
