"""Operating mechanisms with explicit assumptions, not fabricated operating disclosures."""
from decimal import Decimal
from .engine import number, rounded, ValidationError

COMMON = {'opex_growth':(-80,200),'tax_rate':(0,60),'da_ratio':(0,50),
          'capex_ratio':(0,100),'dso':(0,730),'dio':(0,730),'dpo':(0,730),
          'opening_nwc':(-1e12,1e12)}
SPECIFIC = {'hardware':{'volume_growth':(-80,200),'price_growth':(-80,100),'unit_cost_growth':(-80,100)},
            'software':{'retention':(0,100),'expansion':(-80,100),'new_customer_rate':(0,200),'new_customer_timing':(0,1),'service_cost_growth':(-80,100)}}

def suggested(state):
    m=state['diagnostics'].get('current',{})
    if state['company']['mode']=='financial' or not all(k in m for k in ['revenue','cost','gross_profit','operating_income']):return None
    rev=m['revenue'];cost=m['cost']
    if rev<=0 or cost<=0:return None
    template='software' if state['company']['mode']=='software' else 'hardware'
    p={'opex_growth':5,'tax_rate':20,'da_ratio':3,'capex_ratio':3,
       'dso':rounded(number(m.get('receivables',rev*30/365))/number(rev)*365),
       'dio':rounded(number(m.get('inventory',0))/number(cost)*365),
       'dpo':rounded(number(m.get('payables',cost*30/365))/number(cost)*365),
       'opening_nwc':m.get('receivables',0)+m.get('inventory',0)-m.get('payables',0)}
    p.update({'volume_growth':10,'price_growth':0,'unit_cost_growth':0} if template=='hardware' else {'retention':95,'expansion':5,'new_customer_rate':10,'new_customer_timing':.5,'service_cost_growth':5})
    return {'template':template,'params':p,'kind':'Assumed','note':'全部是可修改练习假设。周转天数若有历史余额则以期末余额估算；不是平均余额周转率。缺少余额时起始资金占用需自行论证。'}

def calculate(state,template,params):
    if state['company']['mode']=='financial':raise ValidationError('金融机构不适用这两个经营模型')
    if template not in SPECIFIC:raise ValidationError('请选择硬件或订阅经营模型')
    ranges={**COMMON,**SPECIFIC[template]}
    if set(params)!=set(ranges):raise ValidationError('经营参数缺失或含未知字段')
    p={k:number(v) for k,v in params.items()}
    for k,(lo,hi) in ranges.items():
        if not number(lo)<=p[k]<=number(hi):raise ValidationError(k+' 超出研究模型范围')
    d=state['diagnostics'];m=d.get('current',{})
    if not all(k in m for k in ['revenue','cost','gross_profit','operating_income']) or m['revenue']<=0 or m['cost']<=0:raise ValidationError('需要正收入、正成本、毛利及经营利润')
    period=d['years'][-1]
    if any(c['period']==period and c['id'] in ['gross','operating','balance'] and (c['status']=='fail' or c['id'] in ['gross','operating'] and c['status']!='pass') for c in state['relations']['checks']):raise ValidationError('先解决核心损益与资产负债勾稽问题')
    pct=lambda k:p[k]/100
    revenue=number(m['revenue']);cost=number(m['cost']);opex=number(m['gross_profit'])-number(m['operating_income'])
    nwc=p['opening_nwc'];runrate=revenue;volume_index=Decimal(100);rows=[]
    year=int(period[2:]);bridges=[]
    for t in range(1,6):
        prior_revenue=revenue
        if template=='hardware':
            volume_effect=prior_revenue*pct('volume_growth')
            price_effect=(prior_revenue+volume_effect)*pct('price_growth')
            revenue=prior_revenue+volume_effect+price_effect
            cost=cost*(1+pct('volume_growth'))*(1+pct('unit_cost_growth'))
            volume_index*=1+pct('volume_growth')
            bridge=[{'name':'量的假设效应','value':rounded(volume_effect)}, {'name':'价的假设效应（含交互）','value':rounded(price_effect)}]
            operations={'volume_index':rounded(volume_index),'price_index':rounded(100*(1+pct('price_growth'))**t)}
        else:
            # Opening recurring revenue equivalent is an assumption, not disclosed ARR.
            churn=runrate*(1-pct('retention'));expansion=(runrate-churn)*pct('expansion')
            new_runrate=runrate*pct('new_customer_rate')
            revenue=runrate-churn+expansion+new_runrate*p['new_customer_timing']
            bridge=[{'name':'期初运行率与上期确认收入差','value':rounded(runrate-prior_revenue)}, {'name':'流失影响','value':rounded(-churn)}, {'name':'留存客户扩张','value':rounded(expansion)}, {'name':'新增客户当年确认','value':rounded(new_runrate*p['new_customer_timing'])}]
            runrate=runrate-churn+expansion+new_runrate
            cost*=1+pct('service_cost_growth')
            operations={'assumed_exit_runrate':rounded(runrate),'new_customer_timing':float(p['new_customer_timing'])}
        opex*=1+pct('opex_growth');gross=revenue-cost;ebit=gross-opex;tax=max(ebit,Decimal(0))*pct('tax_rate')
        ar=revenue*p['dso']/365;inv=cost*p['dio']/365;ap=cost*p['dpo']/365;new_nwc=ar+inv-ap;change=new_nwc-nwc;nwc=new_nwc
        da=revenue*pct('da_ratio');capex=revenue*pct('capex_ratio');fcff=ebit-tax+da-capex-change
        row={'year':f'FY{year+t}E','revenue':revenue,'cost':cost,'gross_profit':gross,'net_opex':opex,'ebit':ebit,'cash_tax':tax,'receivables':ar,'inventory':inv,'payables':ap,'nwc':nwc,'delta_nwc':change,'da':da,'capex':capex,'fcff':fcff}
        rows.append({**{k:rounded(v) if k!='year' else v for k,v in row.items()},**operations})
        bridges.append({'year':row['year'],'opening_revenue':rounded(prior_revenue),'effects':bridge,'closing_revenue':rounded(revenue)})
    inputs=[o for o in state['observations'] if o['period']==period]
    return {'template':template,'model_version':'atlas-driver-1.0','period':period,'asof':state['asof'],'currency':state['company']['currency'],'params':{k:float(v) for k,v in p.items()},'rows':rows,'bridges':bridges,'inputs':inputs,'documents':state['documents'],'kind':'Assumed + Calculated','warnings':['经营指数不代表披露销量或客户数；收入桥解释模型假设，不证明历史因果关系。','订阅模型将基期收入视为期初经常性运行率，新增客户等客单价且按确认比例计入；未处理完整合同负债与收入确认。','FCFF 是税后经营利润加折旧、减资本开支及增量资金占用，不是披露的 CFO。未预测完整资产负债表、融资、税损结转或每股价值。','五年使用不变经营参数；所有假设需经研究者论证，不能代表统计置信区间。']}

def compare_snapshots(old,new):
    if old['template']!=new['template'] or old['period']!=new['period'] or old['currency']!=new['currency']:raise ValidationError('模型类型、基期与币种一致时才能对照版本')
    return {'params':[{'parameter':k,'before':old['params'][k],'after':v} for k,v in new['params'].items() if old['params'][k]!=v],
            'rows':[{'year':b['year'],**{k:rounded(number(b[k])-number(a[k])) for k in ['revenue','ebit','delta_nwc','fcff']}} for a,b in zip(old['rows'],new['rows'])]}
