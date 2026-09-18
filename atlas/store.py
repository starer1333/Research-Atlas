"""Local versioned research storage. No document execution and no cloud calls."""
import sqlite3,json,hashlib,uuid
from pathlib import Path
from datetime import datetime,timezone
from contextlib import contextmanager
from .seed import COMPANIES,DOCUMENTS,observations,DEMO_UPDATE
from .engine import diagnose,defaults,scenario_set,ValidationError,valid_date,number,evaluate_forecast

def now():return datetime.now(timezone.utc).isoformat()
def encode(x):return json.dumps(x,ensure_ascii=False,allow_nan=False)
def identity():return uuid.uuid4().hex

class Store:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY, company TEXT, disclosed_at TEXT, content TEXT, hash TEXT UNIQUE);
            CREATE TABLE IF NOT EXISTS observations(id TEXT PRIMARY KEY, source_id TEXT, company TEXT, period TEXT, metric TEXT, content TEXT, reviewed INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY, company TEXT, kind TEXT, created_at TEXT, content TEXT, stale INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, created_at TEXT, action TEXT, target TEXT, detail TEXT);
            ''')
            if not db.execute('SELECT 1 FROM documents LIMIT 1').fetchone():
                for d in DOCUMENTS:self._document(db,d)
                for o in observations():db.execute('INSERT INTO observations(id,source_id,company,period,metric,content) VALUES(?,?,?,?,?,?)',(o['id'],o['source_id'],o['company'],o['period'],o['metric'],encode(o)))
                self._audit(db,'seed','dataset','公开来源摘录初始化；全部等待用户审核')
    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=15);db.row_factory=sqlite3.Row
        try:
            with db:yield db
        finally:db.close()
    def _audit(self,db,action,target,detail):db.execute('INSERT INTO audit(created_at,action,target,detail) VALUES(?,?,?,?)',(now(),action,target,detail))
    def _document(self,db,d):
        digest=hashlib.sha256(encode(d).encode()).hexdigest()
        db.execute('INSERT INTO documents VALUES(?,?,?,?,?)',(d['id'],d['company'],d['disclosed_at'],encode(d),digest))
    def check_company(self,company):
        if company not in COMPANIES:raise ValidationError('未知公司')
    def state(self,company,asof):
        self.check_company(company);valid_date(asof)
        with self.connect() as db:
            docs=[json.loads(r['content']) for r in db.execute('SELECT * FROM documents WHERE company=? AND disclosed_at<=? ORDER BY disclosed_at,id',(company,asof))]
            rows=db.execute('SELECT o.*,d.disclosed_at FROM observations o JOIN documents d ON d.id=o.source_id WHERE o.company=? AND d.disclosed_at<=? ORDER BY d.disclosed_at,o.rowid',(company,asof)).fetchall()
            obs=[{**json.loads(r['content']),'reviewed':bool(r['reviewed']),'disclosed_at':r['disclosed_at']} for r in rows]
            # Latest disclosure wins for a metric-period; versions remain separately inspectable.
            latest={}
            for o in obs:latest[(o['period'],o['metric'],o['basis'])]=o
            periods={}
            for o in latest.values():
                if o['period_type']=='annual':periods.setdefault(o['period'],{})[o['metric']]=o['value']
            records=[{**dict(r),'content':json.loads(r['content'])} for r in db.execute('SELECT * FROM records WHERE company=? ORDER BY created_at DESC',(company,))]
            audit=[dict(r) for r in db.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 40')]
        visible_sources={d['id'] for d in docs}
        profile={**COMPANIES[company],'ticker':company};profile['segments']=[s for s in profile['segments'] if s['source'] in visible_sources];profile['market']=[m for m in profile['market'] if m['source'] in visible_sources];diagnostics=diagnose(periods)
        required={'revenue','gross_profit','opex'} | ({'receivables','inventory','payables'} if company=='NVDA' else set())
        if diagnostics['years'] and required <= set(diagnostics['current']) and diagnostics['current']['revenue'] and profile['segments']:
            params=defaults(company,diagnostics['current'],profile['segments'])
        else:params=None
        return {'company':profile,'asof':asof,'documents':docs,'observations':obs,'periods':periods,'diagnostics':diagnostics,'defaults':params,'records':records,'audit':audit,'ai':{'status':'not_connected','message':'未调用模型 API；预置研究问题由 AI 起草，尚未人工确认。'},'storage':'SQLite 本地持久化','review_pending':sum(not o['reviewed'] for o in obs)}
    def calculate(self,company,asof,params):
        s=self.state(company,asof)
        if not s['diagnostics']['years']:raise ValidationError('截至研究日期没有可用的年度输入')
        if s['defaults'] is None:raise ValidationError('年度输入不完整，不能启动预测模型')
        c=s['company'];metrics=s['diagnostics']['current'];year=int(s['diagnostics']['years'][-1][2:])
        # Revenue groups are sourced from a specific annual release; never silently rebase.
        expected='FY2025' if company=='NVDA' else 'FY2024'
        if s['diagnostics']['years'][-1]!=expected:raise ValidationError('新的年度资料需要先更新收入分组，不能沿用旧模型基期')
        if abs(sum(x['value'] for x in c['segments'])-metrics['revenue'])>.01:raise ValidationError('收入分组与最新合并收入不一致，请先审核与更新分组')
        result=scenario_set(company,metrics,c['segments'],params,year)
        chosen={}
        for o in s['observations']:
            if o['period']==expected:chosen[(o['metric'],o['basis'])]=o
        inputs=list(chosen.values())
        result.update({'asof':asof,'input_ids':[o['id'] for o in inputs],'inputs':inputs,'documents':s['documents'],'review_pending':sum(not o['reviewed'] for o in inputs),'period':expected,'segments':c['segments']})
        return result
    def save_record(self,company,kind,content):
        self.check_company(company);ident=identity()
        with self.connect() as db:
            db.execute('INSERT INTO records VALUES(?,?,?,?,?,0)',(ident,company,kind,now(),encode(content)));self._audit(db,'save_'+kind,ident,'用户保存研究记录')
        return ident
    def action(self,route,p):
        company=p.get('company');self.check_company(company)
        if route=='export-file':
            content=self.export(company,p['asof']);folder=self.path.parent/'exports';folder.mkdir(parents=True,exist_ok=True)
            destination=folder/(f'Research-Atlas-{company}-{valid_date(p["asof"])}-{identity()[:8]}.md')
            destination.write_text(content,encoding='utf-8')
            with self.connect() as db:self._audit(db,'export',destination.name,'研究包保存到项目资料库旁的 exports 目录')
            return {'path':str(destination.resolve()),'filename':destination.name,'content':content}
        if route=='calculate':return self.calculate(company,p['asof'],p['params'])
        if route=='snapshot':
            reason=str(p.get('reason','')).strip()
            if not reason:raise ValidationError('冻结模型必须填写理由')
            r=self.calculate(company,p['asof'],p['params']);r['reason']=reason;r['evidence_note']=p.get('evidence_note','')
            return {'id':self.save_record(company,'model',r),'message':'已冻结模型、假设与输入版本。'}
        if route=='review':
            ids=p.get('ids',[])
            if not ids or not isinstance(ids,list) or len(ids)>200:raise ValidationError('选择要审核的指标')
            with self.connect() as db:
                for ident in ids:
                    row=db.execute('SELECT company FROM observations WHERE id=?',(ident,)).fetchone()
                    if not row or row['company']!=company:raise ValidationError('审核对象不存在或公司不一致')
                    db.execute('UPDATE observations SET reviewed=1 WHERE id=?',(ident,));self._audit(db,'review',ident,'用户点击确认核验')
            return {'reviewed':len(ids)}
        if route=='thesis':
            required=['title','mechanism','support','counter','trigger','driver']
            if any(not str(p.get(k,'')).strip() for k in required):raise ValidationError('论点需要机制、支持、反证、推翻条件和关联参数')
            state=self.state(company,p['asof']);allowed={d['id'] for d in state['documents']}
            if not p.get('source_ids') or not set(p['source_ids'])<=allowed:raise ValidationError('论点须关联本研究时点可用的来源')
            if p['driver'] not in (state['defaults'] or {}):raise ValidationError('关联参数不属于当前模型')
            return {'id':self.save_record(company,'thesis',{k:p[k] for k in required+['source_ids','asof']})}
        if route=='memo':
            text=str(p.get('text',''));valid_date(p['asof'])
            if not text.strip():raise ValidationError('备忘录不能为空')
            return {'id':self.save_record(company,'memo',{'text':text,'asof':p['asof']})}
        if route=='forecast':
            valid_date(p['asof']);period=p.get('period','')
            import re
            if not re.fullmatch(r'FY\d{4}(Q[1-4])?',period):raise ValidationError('期间格式为 FY2026 或 FY2026Q1')
            vals={k:float(number(p[k])) for k in ['low','predicted','high']}
            if not 0<=vals['low']<=vals['predicted']<=vals['high']:raise ValidationError('收入预测需满足 0 ≤ 下界 ≤ 点估计 ≤ 上界')
            if not str(p.get('reason','')).strip():raise ValidationError('请写明预测依据')
            return {'id':self.save_record(company,'forecast',{**vals,'asof':p['asof'],'period':period,'metric':'revenue','unit':'million','currency':'USD','basis':'GAAP','scope':'consolidated','reason':p['reason'],'mode':'historical_exercise' if p['asof']<now()[:10] else 'prospective_unverified'})}
        if route=='evaluate':
            s=self.state(company,p['asof']);record=next((r for r in s['records'] if r['id']==p['id'] and r['kind']=='forecast'),None)
            if not record:raise ValidationError('预测不存在')
            f=record['content'];matches=[o for o in s['observations'] if o['metric']==f['metric'] and o['period']==f['period'] and o['basis']==f['basis'] and o['scope']==f['scope'] and o['unit']==f['unit'] and o['currency']==f['currency']]
            if not matches:raise ValidationError('截至当前日期没有同期间、指标、币种与口径的实际值')
            actual=matches[-1];result=evaluate_forecast(f['predicted'],f['low'],f['high'],actual['value']);result.update({'forecast_id':record['id'],'actual_id':actual['id'],'actual':actual['value'],'actual_reviewed':actual['reviewed'],'period':f['period'],'mode':f['mode']})
            return {'id':self.save_record(company,'evaluation',result),'result':result}
        if route=='import-example':
            if company!='NVDA':raise ValidationError('此更新案例只适用于 NVIDIA')
            return self.import_document(DEMO_UPDATE)
        if route=='import':
            if p['document'].get('company')!=company:raise ValidationError('导入资料与当前研究公司不一致')
            return self.import_document(p['document'])
        raise ValidationError('未知操作')
    def import_document(self,p):
        self.check_company(p.get('company'));valid_date(p.get('disclosed_at'))
        from urllib.parse import urlparse
        url=urlparse(p.get('url',''))
        if url.scheme!='https' or not url.netloc:raise ValidationError('来源必须为 HTTPS 链接；后端不会访问该链接')
        if not p.get('id') or not p.get('title') or not p.get('locator'):raise ValidationError('资料缺少 ID、标题或原文位置')
        rows=p.get('observations',[])
        if not rows or len(rows)>200:raise ValidationError('每次导入 1 至 200 个指标')
        import re
        clean=[]
        for o in rows:
            if o.get('company')!=p['company'] or o.get('currency')!='USD' or o.get('unit')!='million' or o.get('scope')!='consolidated' or o.get('basis')!='GAAP' or o.get('kind')!='Disclosed':raise ValidationError('当前导入契约仅支持 USD million / consolidated / GAAP 的披露指标')
            if not re.fullmatch(r'FY\d{4}(Q[1-4])?',o.get('period','')):raise ValidationError('期间格式错误')
            expected='quarterly' if 'Q' in o['period'] else 'annual'
            if o.get('period_type')!=expected:raise ValidationError('单季和全年口径不一致')
            if not o.get('id') or o.get('metric') not in ['revenue','cost','gross_profit','opex','operating_income','net_income','cfo','capex','da','sbc','receivables','inventory','payables','assets','liabilities','equity']:raise ValidationError('缺少 ID 或指标不在字典内')
            clean.append({**o,'source_id':p['id'],'value':float(number(o['value']))})
        doc={k:v for k,v in p.items() if k!='observations'}
        with self.connect() as db:
            if db.execute('SELECT 1 FROM documents WHERE id=?',(doc['id'],)).fetchone():raise ValidationError('资料 ID 已存在，重复导入被拒绝')
            self._document(db,doc)
            for o in clean:db.execute('INSERT INTO observations(id,source_id,company,period,metric,content) VALUES(?,?,?,?,?,?)',(o['id'],doc['id'],p['company'],o['period'],o['metric'],encode(o)))
            # Conservative company-level invalidation, explicitly not a precise field DAG.
            count=db.execute("UPDATE records SET stale=1 WHERE company=? AND kind IN ('model','thesis','memo')",(p['company'],)).rowcount
            self._audit(db,'import',doc['id'],f'新增 {len(clean)} 条指标；{count} 条同公司研究记录待复核')
        return {'imported':len(clean),'affected':count,'message':'新资料已保存，旧快照保留；同公司模型、论点和备忘录标记待复核。'}
    def export(self,company,asof):
        s=self.state(company,asof);lines=[f"# Research Atlas / {company}",f'研究截至 {asof}；单位 USD million；历史案例，非投资建议。','## 来源']
        lines += [f"- {d['title']} | {d['disclosed_at']} | {d['url']} | {d['locator']}" for d in s['documents']]
        lines += ['## 财务诊断',json.dumps(s['diagnostics'],ensure_ascii=False,indent=2),'## 研究记录（含操作时间；不代表全部在研究时点已存在）']
        for r in s['records']:lines += [f"### {r['kind']} / {r['created_at']} / 待复核={bool(r['stale'])}",json.dumps(r['content'],ensure_ascii=False,indent=2)]
        lines += ['## 限制','数据由 AI 辅助录入并保留用户审核状态。当前模型为简化经营预测，默认参数是研究练习假设，未完成完整三表、同行和市场规模覆盖。']
        return '\n\n'.join(lines)
