"""Intel historical earnings-release fixture, pending user verification."""
URL='https://www.intc.com/news-events/press-releases/detail/1726/intel-reports-fourth-quarter-and-full-year-2024-financial'
DOC={'id':'intc-fy24','company':'INTC','title':'Intel FY2024 earnings release (unaudited tables)','url':URL,'disclosed_at':'2025-01-30','locator':'Consolidated Statements of Income / Balance Sheets / Cash Flows / Supplemental Operating Segment Results','note':'USD million；净利润为包含少数股东的合并净利润；分部含内部交易，不能直接相加。'}
PROFILE={'name':'Intel','industry':'semiconductors','business_models':['芯片设计','制造与代工'],'mode':'hardware','currency':'USD','basis':'GAAP','scope':'consolidated','operating_identity':'gp_less_opex','tolerance':.01,'subtitle':'半导体 / 设计与制造','question':'产品业务与制造投入怎样共同影响利润和现金？','segments':[],'market':[],'unknowns':['重组费用与资本性支出影响年度比较，不能把合并利润率差异完全归因于产品。','分部交易需抵销；未提供独立产品市场份额。'],'periods':{'FY2024':{'start':'2023-12-31','end':'2024-12-28'},'FY2023':{'start':'2023-01-01','end':'2023-12-30'}}}
DATA={'FY2024':{'revenue':53101,'cost':35756,'gross_profit':17345,'opex':29023,'operating_income':-11678,'net_income':-19233,'cfo':8288,'capex':23944,'capex_principal':1178,'sbc':3410,'receivables':3478,'inventory':12198,'payables':12556,'assets':196485,'equity':105032,'cash_balance':8249,'cfi':-18256,'cff':11138,'cash_open':7079,'cash_change':1170,'cash_close':8249},'FY2023':{'revenue':54228,'cost':32517,'gross_profit':21711,'opex':21618,'operating_income':93,'net_income':1675,'cfo':11471,'capex':25750,'capex_principal':0,'sbc':3229,'receivables':3402,'inventory':11127,'payables':8578,'assets':191572,'equity':109965,'cash_balance':7079,'cfi':-24041,'cff':8505,'cash_open':11144,'cash_change':-4065,'cash_close':7079}}

def seed(store,db,encode,labels):
    db.execute('INSERT OR IGNORE INTO companies VALUES(?,?)',('INTC',encode(PROFILE)))
    if db.execute('SELECT 1 FROM documents WHERE id=?',(DOC['id'],)).fetchone():return
    store._document(db,DOC)
    for period,values in DATA.items():
        for metric,value in values.items():
            window=PROFILE['periods'][period]
            o={'id':f'INTC-{period}-{metric}','company':'INTC','period':period,'period_type':'annual','period_start':window['start'],'period_end':window['end'],'metric':metric,'label':labels[metric],'value':value,'kind':'Disclosed','currency':'USD','unit':'million','basis':'GAAP','scope':'consolidated','source_id':DOC['id']}
            db.execute('INSERT INTO observations(id,source_id,company,period,metric,content) VALUES(?,?,?,?,?,?)',(o['id'],DOC['id'],'INTC',period,metric,encode(o)))
    store._audit(db,'seed_peer','INTC','新增第三家半导体历史案例；保留未审计公告标记，全部待人工核验')
