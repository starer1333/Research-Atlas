"""Named financial identities; missing inputs never become zero.
Amounts are normalized to millions in the company's presentation currency.
Rules compare amounts, not economic causality. No automatic period/FX matching.
"""
from .engine import rounded,number,ratio
from .seed import LABELS

METRICS={**LABELS,
 'other_operating_income':'其他经营收益（收益为正）',
 'noncash_adjustments':'非现金调整合计', 'operating_wc_cash':'经营资产负债变动现金影响',
 'cfi':'投资活动现金净额','cff':'筹资活动现金净额','fx_cash':'汇率对现金影响',
 'cash_change':'现金流表现金净变动','cash_open':'现金流表期初现金','cash_close':'现金流表期末现金',
 'cash_balance':'资产负债表现金及等价物','restricted_cash':'受限现金',
 'current_assets':'流动资产','current_liabilities':'流动负债',
 'retained_open':'期初留存收益','retained_close':'期末留存收益','dividends':'留存收益分配',
 'retained_other':'留存收益其他变动（增加为正）',
 'interest_income':'利息收入','interest_expense':'利息支出（支出为正）','net_interest_income':'净利息收入'}

RULES=[
 ('gross','损益表','收入 − 成本 = 毛利',{'revenue':1,'cost':-1},'gross_profit','total',None),
 ('operating','损益表','毛利 − 经营费用 + 其他经营收益 = 经营利润',{'gross_profit':1,'opex':-1,'other_operating_income':1},'operating_income','total',None),
 ('balance','资产负债表','资产 = 负债 + 权益',{'liabilities':1,'equity':1},'assets','total',None),
 ('cfo','跨表现金流','净利润 + 非现金调整 + 经营资产负债变动现金影响 = CFO',{'net_income':1,'noncash_adjustments':1,'operating_wc_cash':1},'cfo','total',None),
 ('cash_movement','现金流量表','经营 + 投资 + 筹资 + 汇率影响 = 现金净变动',{'cfo':1,'cfi':1,'cff':1,'fx_cash':1},'cash_change','total',None),
 ('cash_roll','现金流量表','期初现金 + 净变动 = 期末现金（现金流表口径）',{'cash_open':1,'cash_change':1},'cash_close','total',None),
 ('cash_scope','跨表口径','现金及等价物 + 受限现金 = 现金流表期末现金',{'cash_balance':1,'restricted_cash':1},'cash_close','total',None),
 ('retained','权益变动','期初留存收益 + 净利润 − 分配 + 其他变动 = 期末留存收益',{'retained_open':1,'net_income':1,'dividends':-1,'retained_other':1},'retained_close','total',None),
 ('interest','金融业务','利息收入 − 利息支出 = 净利息收入',{'interest_income':1,'interest_expense':-1},'net_interest_income','financial',None)
]

def reconcile(metrics,profile,period):
    checks=[]
    for ident,group,formula,weights,target,template,_ in RULES:
        if template=='financial' and profile.get('mode')!='financial':continue
        if profile.get('mode')=='financial' and ident in ('gross','operating'):continue
        terms=dict(weights);assumptions=[]
        # Explicit presentation policy, never inferred from a missing number.
        if ident=='operating' and profile.get('operating_identity')=='gp_less_opex':
            terms.pop('other_operating_income');formula='毛利 − 经营费用 = 经营利润'
        keys=list(terms)+[target];missing=[k for k in keys if metrics.get(k) is None]
        expected=None;delta=None;status='missing'
        if not missing:
            expected=sum(number(metrics[k])*v for k,v in terms.items());delta=number(metrics[target])-expected
            status='pass' if abs(delta)<=number(profile.get('tolerance',.01)) else 'fail'
        checks.append({'id':ident,'period':period,'group':group,'formula':formula,'target':target,'inputs':keys,'missing':missing,'expected':rounded(expected) if expected is not None else None,'actual':metrics.get(target),'difference':rounded(delta) if delta is not None else None,'status':status,'assumptions':assumptions})
    return checks

def dashboard(periods,profile):
    years=sorted(periods);all_checks=[];common=[]
    for year in years:
        m=periods[year];all_checks+=reconcile(m,profile,year)
        common.append({'period':year,'revenue':m.get('revenue'),'gross_margin':ratio(m.get('gross_profit'),m.get('revenue')),'operating_margin':ratio(m.get('operating_income'),m.get('revenue')),'net_margin':ratio(m.get('net_income'),m.get('revenue')),'cfo_margin':ratio(m.get('cfo'),m.get('revenue')),'debt_ratio':ratio(m.get('liabilities'),m.get('assets'))})
    return {'checks':all_checks,'common_size':common,'coverage':{s:sum(c['status']==s for c in all_checks) for s in ['pass','fail','missing']},'definition':'差额 = 披露右侧值 − 左侧计算值；0 只在已披露或明确口径下使用。','tolerance':profile.get('tolerance',.01)}
