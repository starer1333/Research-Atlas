"""Research records and human decisions. Sources never receive execution privileges."""
import json,uuid
from .engine import ValidationError,valid_date
from . import drivers,extraction

ROUTES={'driver-defaults','driver-calculate','driver-save','driver-diff','comparison-save','business-note','research-save','extraction-draft','extraction-review','extraction-import'}

def required(p,keys):
    for k in keys:
        if not isinstance(p.get(k),str) or not p[k].strip() or len(p[k])>12000:raise ValidationError('请填写 '+k+'，且不超过 12000 字符')

def sources(state,ids):
    if not isinstance(ids,list) or not ids or not set(ids)<={d['id'] for d in state['documents']}:raise ValidationError('选择当前公司、当前研究时点可用的来源')

def record(state,ident,kind):
    result=next((r for r in state['records'] if r['id']==ident and r['kind']==kind),None)
    if not result:raise ValidationError('该公司不存在指定研究版本')
    if result['content'].get('asof',state['asof'])>state['asof']:raise ValidationError('该记录的研究时点晚于当前日期')
    return result

def handle(store,route,p):
    company=p['company'];s=store.state(company,p['asof'])
    if route=='driver-defaults':return {'suggested':drivers.suggested(s)}
    if route in ['driver-calculate','driver-save']:
        required(p,['reason','counter','trigger']);sources(s,p.get('source_ids'))
        result=drivers.calculate(s,p['template'],p['params'])
        result.update({k:p[k] for k in ['reason','counter','trigger','source_ids']})
        result['parent_id']=p.get('parent_id')
        if result['parent_id']:
            parent=record(s,result['parent_id'],'driver')['content']
            result['change']=drivers.compare_snapshots(parent,result)
        if route=='driver-save':return {'id':store.save_record(company,'driver',result),'result':result}
        return result
    if route=='driver-diff':
        old=record(s,p['before'],'driver')['content'];new=record(s,p['after'],'driver')['content']
        return drivers.compare_snapshots(old,new)
    if route=='comparison-save':
        required(p,['reason']);result=store.compare(company,p.get('peers',[]),p['asof'],p.get('nearby',False))
        result.update(reason=p['reason'],company_ids=[r['ticker'] for r in result['rows']])
        return {'id':store.save_record(company,'comparison',result)}
    if route=='business-note':
        required(p,['subject','dimension','observation','mechanism','alternative','trigger'])
        if p.get('level') not in ['company','segment','product']:raise ValidationError('选择公司、业务或产品层级')
        peer=p.get('peer');peer_state=store.state(peer,p['asof']);sources(s,p.get('source_ids'));sources(peer_state,p.get('peer_source_ids'))
        result={k:p[k] for k in ['subject','dimension','observation','mechanism','alternative','trigger','level','peer','source_ids','peer_source_ids','asof']}
        result.update(company_ids=[company,peer],kind='Research interpretation',documents=s['documents']+peer_state['documents'])
        return {'id':store.save_record(company,'business-note',result)}
    if route=='research-save':
        required(p,['question','conclusion','alternative','next_evidence','change_reason']);sources(s,p.get('source_ids'))
        if p.get('status') not in ['open','supported','challenged','withdrawn']:raise ValidationError('选择研究判断状态')
        parent=p.get('parent_id')
        if parent:record(s,parent,'research')
        model_id=p.get('model_id')
        if model_id:record(s,model_id,'driver')
        result={k:p.get(k) for k in ['question','conclusion','alternative','next_evidence','change_reason','source_ids','status','parent_id','model_id','asof']}
        result['documents']=[d for d in s['documents'] if d['id'] in p['source_ids']]
        return {'id':store.save_record(company,'research',result)}
    if route=='extraction-draft':
        sources(s,[p.get('source_id')]);valid_date(p.get('period_start'));valid_date(p.get('period_end'))
        if p['period_start']>p['period_end']:raise ValidationError('期间结束不能早于开始')
        doc=next(d for d in s['documents'] if d['id']==p['source_id'])
        if p['period_end']>doc['disclosed_at']:raise ValidationError('资料披露早于录入的期间结束')
        result=extraction.extract(p.get('text'),p.get('period'),p.get('unit'),p.get('provider','local-rules'),p.get('external'))
        result.update({k:p[k] for k in ['source_id','text','period','period_start','period_end','unit','asof']})
        return {'id':store.save_record(company,'extraction',result),'result':result}
    if route=='extraction-review':
        draft=record(s,p['id'],'extraction')['content'];reviewed=extraction.review(draft,p.get('decisions'))
        result={'draft_id':p['id'],'asof':p['asof'],'review':reviewed,'evaluation':extraction.score_review(reviewed)}
        return {'id':store.save_record(company,'extraction-review',result),'result':result}
    if route=='extraction-import':
        reviewed=record(s,p['id'],'extraction-review')['content'];draft=record(s,reviewed['draft_id'],'extraction')['content']
        sources(s,[draft['source_id']]);original=next(d for d in s['documents'] if d['id']==draft['source_id'])
        ident='reviewed-'+p['id'];profile=s['company'];observations=[]
        for index,r in enumerate(reviewed['review']):
            if not r['accepted']:continue
            a=r['accepted'];observations.append({'id':ident+'-'+str(index),'company':company,'period':a['period'],'period_type':'quarterly' if 'Q' in a['period'] else 'annual','period_start':draft['period_start'],'period_end':draft['period_end'],'metric':a['metric'],'value':a['value'],'unit':a['unit'],'kind':'Disclosed','currency':profile['currency'],'scope':profile['scope'],'basis':profile['basis'],'quote':a['quote'],'extraction_review_id':p['id']})
        if not observations:raise ValidationError('全部候选已拒绝，没有可导入数据')
        result=store.import_document({'id':ident,'company':company,'title':original['title']+' / 人工审核候选','url':original['url'],'disclosed_at':original['disclosed_at'],'locator':original['locator'],'parent_source_id':original['id'],'observations':observations})
        # Import remains pending financial review: candidate acceptance is not audit confirmation.
        return {**result,'note':'候选审核记录保留；正式指标仍需在证据面板确认财务核验。'}

def metric_comparability(rows,states,nearby):
    amount_keys=['revenue','gross_profit','operating_income','net_income','cfo','receivables','inventory','sbc']
    dependencies={'gross_margin':['revenue','gross_profit'],'op_margin':['revenue','operating_income'],'cash_conversion':['net_income','cfo'],'sbc_ratio':['revenue','sbc']}
    rule_inputs={'gross':{'revenue','cost','gross_profit'},'operating':{'gross_profit','opex','operating_income','other_operating_income'},'balance':{'assets','liabilities','equity'},'cfo':{'cfo','net_income','noncash_adjustments','operating_wc_cash'}}
    for row,s in zip(rows,states):
        cells={}
        for key in amount_keys+list(dependencies):
            ratio=key in dependencies;needs=dependencies.get(key,[key]);reasons=[]
            # Retain period, reporting and industry constraints; choose currency policy per metric.
            for reason in row['reasons']:
                if reason=='币种不一致或未分类' and ratio:continue
                if reason=='存在未解决的报表勾稽差异':continue
                if any(word in reason for word in ['不一致或未分类','缺少财政','不是严格同期','严格比较需要','年度时长','无年度数据']):reasons.append(reason)
            if any(row['values'].get(k) is None for k in needs):reasons.append('缺少本指标输入')
            if ratio and row['values'].get(needs[0],0)<=0:reasons.append('分母非正，不解释为普通质量比率')
            # Anchor must be equally valid; rows cannot compare against missing or broken inputs.
            anchor=rows[0]
            if any(anchor['values'].get(k) is None for k in needs):reasons.append('基准公司缺少本指标输入')
            if ratio and anchor['values'].get(needs[0],0)<=0:reasons.append('基准分母非正')
            for subject in [s,states[0]]:
                for check in subject['relations']['checks']:
                    if subject['diagnostics']['years'] and check['period']==subject['diagnostics']['years'][-1]:
                        if check['status']=='fail' and set(needs)&rule_inputs.get(check['id'],set(check['inputs'])):reasons.append('本指标依赖的勾稽存在差额')
            notes=['未自动调节业务组合；仅作研究参考']
            if row['currency']!=anchor['currency'] and ratio:notes.append('比例不需机械换汇，但汇率和业务结构仍影响经济解释')
            if row['review_pending']:notes.append('部分来源待人工核验')
            if nearby:notes.append('允许相邻财年；请查看起止日期差异')
            cells[key]={'status':'blocked' if reasons else 'qualified','reasons':list(dict.fromkeys(reasons)),'notes':notes,'value':(row['ratios'].get(key) if ratio else row['values'].get(key)) if not reasons else None}
        row['metric_checks']=cells
