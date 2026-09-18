"""Deterministic, explicit-assumption operating model. All monetary values USD million."""
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
import math

VERSION='atlas-operating-2.0'
class ValidationError(ValueError): pass

def number(value):
    if isinstance(value,bool): raise ValidationError('布尔值不是金额或参数')
    try: v=Decimal(str(value))
    except Exception: raise ValidationError('请输入有效数字')
    if not v.is_finite(): raise ValidationError('数字必须有限')
    return v

def rounded(value): return float(number(value).quantize(Decimal('.01'),rounding=ROUND_HALF_UP))
def valid_date(value):
    try: return date.fromisoformat(value).isoformat()
    except (ValueError,TypeError): raise ValidationError('日期必须为有效 YYYY-MM-DD')

def ratio(a,b): return None if a is None or b in (None,0) else round(a/b*100,2)

def diagnose(periods):
    years=sorted(periods)
    if not years:return {'years':[],'ratios':{},'checks':[],'bridges':[]}
    current=periods[years[-1]];previous=periods[years[-2]] if len(years)>1 else {}
    checks=[]
    for label,keys,func in [('收入减成本等于毛利',['revenue','cost','gross_profit'],lambda x:x['revenue']-x['cost']-x['gross_profit']),('毛利减费用等于经营利润',['gross_profit','opex','operating_income'],lambda x:x['gross_profit']-x['opex']-x['operating_income']),('资产等于负债加权益',['assets','liabilities','equity'],lambda x:x['assets']-x['liabilities']-x['equity'])]:
        available=all(k in current for k in keys);delta=func(current) if available else None
        checks.append({'label':label,'status':'pass' if available and abs(delta)<.01 else 'fail' if available else 'missing','difference':delta,'inputs':keys})
    ratios={'gross_margin':ratio(current.get('gross_profit'),current.get('revenue')),'op_margin':ratio(current.get('operating_income'),current.get('revenue')),'net_margin':ratio(current.get('net_income'),current.get('revenue')),'cash_conversion':ratio(current.get('cfo'),current.get('net_income')),'sbc_ratio':ratio(current.get('sbc'),current.get('revenue')),'revenue_growth':ratio(current.get('revenue',0)-previous['revenue'],previous['revenue']) if 'revenue' in previous else None}
    fcf=None
    if all(k in current for k in ['cfo','capex','capex_principal']): fcf=current['cfo']-current['capex']-current['capex_principal']
    # Ending-balance proxies are named explicitly; no false average-balance turnover ratios.
    ratios['ending_ar_days_proxy']=rounded(number(current['receivables'])/number(current['revenue'])*365) if all(k in current for k in ['receivables','revenue']) and current['revenue'] else None
    ratios['ending_inventory_days_proxy']=rounded(number(current['inventory'])/number(current['cost'])*365) if all(k in current for k in ['inventory','cost']) and current['cost'] else None
    bridges=[]
    if all(k in current and k in previous for k in ['revenue','gross_profit','opex']) and current['revenue'] and previous['revenue']:
        r0=number(previous['revenue']);r1=number(current['revenue']);m0=number(previous['gross_profit'])/r0;m1=number(current['gross_profit'])/r1
        bridges=[{'name':'收入规模效应','value':rounded((r1-r0)*m0),'formula':'(本期收入 - 上期收入) × 上期毛利率'},{'name':'毛利率效应','value':rounded(r1*(m1-m0)),'formula':'本期收入 × (本期毛利率 - 上期毛利率)'},{'name':'费用变化','value':rounded(number(previous['opex'])-number(current['opex'])),'formula':'上期费用 - 本期费用'}]
    return {'years':years,'ratios':ratios,'checks':checks,'bridges':bridges,'fcf':fcf,'current':current,'previous':previous}

def defaults(company,metrics,segments):
    rev=metrics['revenue'];hw=company=='NVDA'
    params={f'growth_{i}':25 if hw and i==0 else 8 if hw else [10,9,-5][i] for i in range(len(segments))}
    params.update({'terminal_revenue_growth':5,'gross_margin':ratio(metrics['gross_profit'],rev),'opex_ratio':ratio(metrics['opex'],rev),'tax_rate':17 if hw else 20,'da_ratio':ratio(metrics['da'],rev) if 'da' in metrics else 3,'capex_ratio':ratio(metrics['capex'],rev) if 'capex' in metrics else 2,'nwc_ratio':ratio(metrics['receivables']+metrics['inventory']-metrics['payables'],rev) if hw else 5,'opening_nwc_ratio':ratio(metrics['receivables']+metrics['inventory']-metrics['payables'],rev) if hw else 5,'wacc':10,'terminal_growth':2.5})
    return params

def validate(params,n):
    keys={f'growth_{i}' for i in range(n)}|{'terminal_revenue_growth','gross_margin','opex_ratio','tax_rate','da_ratio','capex_ratio','nwc_ratio','opening_nwc_ratio','wacc','terminal_growth'}
    if set(params)!=keys:raise ValidationError('模型参数缺失或包含未知参数')
    p={k:number(v)/100 for k,v in params.items()}
    for k,v in p.items():
        lo,hi=((-0.8,2) if k.startswith('growth_') else (-.5,.5) if k=='terminal_revenue_growth' else (-.5,1) if 'nwc' in k else (.01,.5) if k=='wacc' else (-.05,.10) if k=='terminal_growth' else (0,1))
        if not number(lo)<=v<=number(hi):raise ValidationError(f'{k} 超出允许范围')
    if p['terminal_growth']>=p['wacc']:raise ValidationError('WACC 必须大于永续增长率')
    return p

def project(company,metrics,segments,params,base_year):
    p=validate(params,len(segments));segment_values=[number(s['value']) for s in segments]
    revenue=number(metrics['revenue']);nwc=revenue*p['opening_nwc_ratio'];rows=[];pv=Decimal(0)
    for t in range(1,6):
        # Growth fades linearly to an explicitly assumed year-five revenue growth.
        growths=[p[f'growth_{i}']+(p['terminal_revenue_growth']-p[f'growth_{i}'])*number(t-1)/4 for i in range(len(segments))]
        segment_values=[v*(1+g) for v,g in zip(segment_values,growths)];revenue=sum(segment_values);gp=revenue*p['gross_margin'];opex=revenue*p['opex_ratio'];ebit=gp-opex;tax=max(ebit,Decimal(0))*p['tax_rate'];da=revenue*p['da_ratio'];capex=revenue*p['capex_ratio'];new_nwc=revenue*p['nwc_ratio'];delta_nwc=new_nwc-nwc;nwc=new_nwc;fcff=ebit-tax+da-capex-delta_nwc;discounted=fcff/(1+p['wacc'])**t;pv+=discounted
        rows.append({'year':f'FY{base_year+t}E','revenue':rounded(revenue),'segments':[rounded(v) for v in segment_values],'gross_profit':rounded(gp),'opex':rounded(opex),'ebit':rounded(ebit),'cash_tax':rounded(tax),'da':rounded(da),'capex':rounded(capex),'delta_nwc':rounded(delta_nwc),'fcff':rounded(fcff),'pv':rounded(discounted)})
    terminal=fcff*(1+p['terminal_growth'])/(p['wacc']-p['terminal_growth']);terminal_pv=terminal/(1+p['wacc'])**5;ev=pv+terminal_pv
    equity=None
    if 'cash_securities' in metrics and 'debt' in metrics:equity=ev+number(metrics['cash_securities'])-number(metrics['debt'])
    return {'rows':rows,'enterprise_value':rounded(ev),'equity_value':rounded(equity) if equity is not None else None,'pv_cashflows':rounded(pv),'pv_terminal':rounded(terminal_pv),'terminal_share':rounded(terminal_pv/ev*100) if ev else None,'model_version':VERSION,'basis':'Assumed + Calculated','warnings':['研究假设，不是管理层指引或统计置信区间。','FCFF 为简化经营模型：营运资金使用比例，未完成三表联动；不计算每股目标价。','期初营运资金比例对 Adobe 为显式假设；税务亏损结转未建模。' if company=='ADBE' else '营运资金只覆盖应收、存货与应付；其他项目未建模。']}

def scenario_set(company,metrics,segments,params,year):
    validate(params,len(segments));params={k:float(number(v)) for k,v in params.items()};out={}
    for label,delta in [('bear',-5),('base',0),('bull',5)]:
        p=dict(params)
        for i in range(len(segments)):p[f'growth_{i}']=max(-80,min(200,p[f'growth_{i}']+delta))
        p['gross_margin']=max(0,min(100,p['gross_margin']+delta*.4));out[label]=project(company,metrics,segments,p,year)
    sensitivity=[]
    for dw in [-2,-1,0,1,2]:
        row=[]
        for dg in [-1,0,1]:
            p={**params,'wacc':params['wacc']+dw,'terminal_growth':params['terminal_growth']+dg}
            try:v=project(company,metrics,segments,p,year)['enterprise_value']
            except ValidationError:v=None
            row.append({'wacc':p['wacc'],'g':p['terminal_growth'],'value':v})
        sensitivity.append(row)
    drivers=[]
    for key in params:
        adjusted={**params,key:params[key]+1}
        try:
            changed=project(company,metrics,segments,adjusted,year)
            drivers.append({'parameter':key,'change_pp':1,'delta_ev':rounded(number(changed['enterprise_value'])-number(out['base']['enterprise_value'])),'delta_year1_fcff':rounded(number(changed['rows'][0]['fcff'])-number(out['base']['rows'][0]['fcff']))})
        except ValidationError:pass
    drivers.sort(key=lambda x:abs(x['delta_ev']),reverse=True)
    return {'scenarios':out,'sensitivity':sensitivity,'drivers':drivers,'params':params,'scenario_definition':'悲观/乐观：首年各收入组增长 ±5pp，毛利率 ±2pp；其余参数不变。不是概率区间。'}

def evaluate_forecast(predicted,low,high,actual):
    p,l,h,a=map(number,[predicted,low,high,actual])
    if l>p or p>h:raise ValidationError('预测需满足下界 ≤ 点估计 ≤ 上界')
    return {'error':rounded(p-a),'absolute_error':rounded(abs(p-a)),'ape':rounded(abs(p-a)/abs(a)*100) if a else None,'covered':bool(l<=a<=h),'note':'单条误差与覆盖结果不是长期预测能力或置信度的证明。'}
