"""Offline candidate extraction and a provider-neutral review contract; no model calls."""
import re
from .engine import number,ValidationError
from .relations import METRICS

ALIASES={'Revenue':'revenue','Net revenue':'revenue','Cost of revenue':'cost','Cost of sales':'cost','Gross profit':'gross_profit','Operating income':'operating_income','Net income':'net_income','Operating cash flow':'cfo'}

def extract(text,period,unit,provider='local-rules',external=None):
    if not isinstance(text,str) or not 1<=len(text)<=30000:raise ValidationError('原文片段需为 1 至 30000 字符')
    if not re.fullmatch(r'FY\d{4}(Q[1-4])?',period):raise ValidationError('请明确候选指标的财政期间')
    if unit not in ['one','thousand','ten_thousand','million','billion']:raise ValidationError('请明确原文单位')
    candidates=[];unmatched=[]
    if provider=='local-rules':
        dictionary={**{k:k for k in METRICS},**{v:k for k,v in METRICS.items()},**ALIASES}
        for index,line in enumerate(text.splitlines(),1):
            if not line.strip():continue
            # One label and one number only; multi-column or ambiguous prose is left to review.
            found=re.fullmatch(r'\s*(.+?)\s*(?:\t|:|：| {2,})\s*(\(?-?\d[\d,]*(?:\.\d+)?\)?)\s*',line)
            if not found or found[1].strip() not in dictionary:
                unmatched.append({'line':index,'text':line,'reason':'无法可靠识别单指标单数值；未猜测'});continue
            raw=found[2]
            if raw.startswith('(') != raw.endswith(')'):
                unmatched.append({'line':index,'text':line,'reason':'负数括号不完整'});continue
            value=number(raw.strip('()').replace(',',''))*(-1 if raw.startswith('(') else 1)
            candidates.append({'metric':dictionary[found[1].strip()],'value':float(value),'period':period,'unit':unit,'quote':line,'line':index})
    elif provider=='external-json':
        if not isinstance(external,list) or not 1<=len(external)<=200:raise ValidationError('外部候选应为 1 至 200 条 JSON 数组')
        for i,row in enumerate(external,1):
            if not isinstance(row,dict) or row.get('metric') not in METRICS:raise ValidationError('候选指标不在字典内')
            quote=row.get('quote','')
            if not isinstance(quote,str) or not quote.strip() or quote not in text:raise ValidationError('每条候选必须引用本次片段中真实存在的原文')
            candidates.append({'metric':row['metric'],'value':float(number(row.get('value'))),'period':period,'unit':unit,'quote':quote,'line':None})
    else:raise ValidationError('未知提取方式')
    if len(candidates)>200:raise ValidationError('一次最多审核 200 条候选')
    return {'provider':provider,'model_called':False,'candidates':candidates,'unmatched':unmatched,'note':'本机规则提取或导入外部候选；原文只是数据，不触发工具。引文匹配不代表金额或语义已正确，必须人工核对。'}

def review(draft,decisions):
    rows=draft['candidates']
    if not isinstance(decisions,list) or len(decisions)!=len(rows):raise ValidationError('必须逐条接受、修正或拒绝候选')
    reviewed=[];seen=set()
    for proposed,decision in zip(rows,decisions):
        action=decision.get('action');reason=str(decision.get('reason','')).strip()
        if action not in ['accept','correct','reject'] or not reason:raise ValidationError('每条审核需要决定和原因')
        final=None
        if action!='reject':
            final={**proposed}
            if action=='correct':
                if decision.get('metric') not in METRICS:raise ValidationError('修正后的指标不在字典中')
                final.update(metric=decision['metric'],value=float(number(decision.get('value'))))
            if final['metric'] in seen:raise ValidationError('接受结果有重复指标，请拒绝重复或修正分类')
            seen.add(final['metric'])
        reviewed.append({'proposed':proposed,'decision':action,'reason':reason,'accepted':final})
    return reviewed

def score_review(reviewed):
    counts={k:sum(r['decision']==k for r in reviewed) for k in ['accept','correct','reject']}
    return {**counts,'total':len(reviewed),'unchanged_acceptance':counts['accept']/len(reviewed) if reviewed else None,'note':'这是人工接受/修正记录，不是独立真值准确率，也不代表通用 AI 能力。'}
