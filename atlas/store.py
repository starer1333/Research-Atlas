"""Local versioned research storage. Document content is never executed. Optional SEC ingestion is explicit."""
import sqlite3,json,hashlib,uuid
from pathlib import Path
from datetime import datetime,timezone
from contextlib import contextmanager
from .seed import COMPANIES,DOCUMENTS,observations,DEMO_UPDATE
from .engine import diagnose,defaults,scenario_set,ValidationError,valid_date,number,evaluate_forecast
from .relations import METRICS,dashboard,reconcile
from .peer_seed import AMD_PROFILE,AMD_DOC,AMD_DATA,CALCULATED,DIFFERENTIATION
from .v3 import build_v3_view
from .semantic import build_semantic_snapshot

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
            CREATE TABLE IF NOT EXISTS companies(id TEXT PRIMARY KEY,content TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,content TEXT NOT NULL);
            ''')
            if not db.execute('SELECT 1 FROM documents LIMIT 1').fetchone():
                for d in DOCUMENTS:self._document(db,d)
                for o in observations():db.execute('INSERT INTO observations(id,source_id,company,period,metric,content) VALUES(?,?,?,?,?,?)',(o['id'],o['source_id'],o['company'],o['period'],o['metric'],encode(o)))
                self._audit(db,'seed','dataset','公开来源摘录初始化；全部等待用户审核')
            for ticker,original in {**COMPANIES,'AMD':AMD_PROFILE}.items():
                profile={'currency':'USD','basis':'GAAP','scope':'consolidated','industry':'semiconductors' if ticker in ['NVDA','AMD'] else 'software','business_models':['硬件平台'] if ticker=='NVDA' else ['软件订阅'],'operating_identity':'gp_less_opex','tolerance':.01,**original}
                if ticker=='NVDA':profile['periods']={'FY2025':{'end':'2025-01-26'},'FY2024':{'end':'2024-01-28'}}
                db.execute('INSERT OR IGNORE INTO companies VALUES(?,?)',(ticker,encode(profile)))
            if not db.execute('SELECT 1 FROM documents WHERE id=?',(AMD_DOC['id'],)).fetchone():
                self._document(db,AMD_DOC)
                for period,metrics in AMD_DATA.items():
                    for metric,value in metrics.items():
                        row={'id':f'AMD-{period}-{metric}','company':'AMD','period':period,'period_type':'annual','metric':metric,'label':METRICS[metric],'value':value,'currency':'USD','unit':'million','scope':'consolidated','basis':'GAAP','source_id':AMD_DOC['id'],'kind':'Calculated' if metric in CALCULATED else 'Disclosed','formula':CALCULATED.get(metric),'period_start':AMD_PROFILE['periods'][period]['start'],'period_end':AMD_PROFILE['periods'][period]['end']}
                        db.execute('INSERT INTO observations(id,source_id,company,period,metric,content) VALUES(?,?,?,?,?,?)',(row['id'],row['source_id'],'AMD',period,metric,encode(row)))
                self._audit(db,'seed_peer','AMD','新增官方年报历史案例，全部待用户审核；既有记录保留')
            from .intel_seed import seed
            seed(self,db,encode,METRICS)
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
        return self.profile(company)
    def profile(self,company):
        with self.connect() as db:r=db.execute('SELECT content FROM companies WHERE id=?',(company,)).fetchone()
        if not r:raise ValidationError('未知公司；请先新建公司档案')
        return {**json.loads(r['content']),'ticker':company}
    def companies(self):
        with self.connect() as db:return [{**json.loads(r['content']),'ticker':r['id']} for r in db.execute('SELECT * FROM companies ORDER BY id')]
    def create_company(self,p):
        import re
        ticker=str(p.get('ticker','')).strip().upper();name=str(p.get('name','')).strip()
        if not re.fullmatch(r'[A-Z0-9][A-Z0-9._-]{0,31}',ticker) or not name:raise ValidationError('填写公司名称与唯一代码（字母、数字、点、横线，最多 32 字符）')
        mode=p.get('mode','general');currency=p.get('currency','USD');basis=p.get('basis','GAAP');scope=p.get('scope','consolidated')
        if str(p.get('industry','')).strip().lower()=='financial':mode='financial'
        if mode not in ['general','hardware','software','consumer','healthcare','internet','automotive','financial']:raise ValidationError('未知分析模板')
        if currency not in ['USD','CNY','EUR','HKD','JPY','GBP'] or basis not in ['GAAP','IFRS','CAS'] or scope not in ['consolidated','parent']:raise ValidationError('币种、准则或报表口径无效')
        profile={'name':name,'mode':mode,'currency':currency,'basis':basis,'scope':scope,'industry':str(p.get('industry','unclassified')).strip() or 'unclassified','business_models':[str(p.get('business_model','待补充'))],'subtitle':str(p.get('industry','待分类'))+' / '+str(p.get('business_model','待补充')),'question':str(p.get('question','增长、盈利和现金流是否相互支持？')),'segments':[],'business_segments':[],'products':[],'context_entities':[],'business_summary':None,'business_source_ids':[],'market':[],'unknowns':['请先导入带来源的财务数据。','行业分类与实际商业模式需要研究者确认。'],'operating_identity':p.get('operating_identity','with_other'),'periods':{},'tolerance':.01}
        if profile['operating_identity'] not in ['with_other','gp_less_opex']:raise ValidationError('无效经营利润口径')
        with self.connect() as db:
            if db.execute('SELECT 1 FROM companies WHERE id=?',(ticker,)).fetchone():raise ValidationError('公司代码已存在；请直接选择该公司')
            db.execute('INSERT INTO companies VALUES(?,?)',(ticker,encode(profile)));self._audit(db,'create_company',ticker,'新建公司档案；未编造任何指标')
        return {'ticker':ticker,'message':'档案已建立，下一步导入财务数据'}
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
            all_records=[{**dict(r),'content':json.loads(r['content'])} for r in db.execute('SELECT * FROM records WHERE company=? ORDER BY created_at DESC',(company,))]
            # Research memory follows its explicit research-as-of, not wall-clock creation time.
            # This keeps retrospective exercises usable while preventing a later-as-of conclusion
            # from leaking into an earlier evidence view. Records without an as-of remain visible
            # for legacy compatibility and are still exposed in the all-time revision history.
            records=[r for r in all_records if not r['content'].get('asof') or r['content'].get('asof')<=asof]
            audit=[dict(r) for r in db.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 40')]
        visible_sources={d['id'] for d in docs}
        profile=self.profile(company);profile['segments']=[s for s in profile.get('segments',[]) if s.get('source') in visible_sources]
        profile['business_segments']=[s for s in profile.get('business_segments',[]) if set(s.get('source_ids',[]) or ([s.get('source')] if s.get('source') else [])) & visible_sources]
        profile['products']=[p for p in profile.get('products',[]) if set(p.get('source_ids',[]) or ([p.get('source')] if p.get('source') else [])) & visible_sources]
        profile['context_entities']=[e for e in profile.get('context_entities',[]) if set(e.get('source_ids',[]) or ([e.get('source')] if e.get('source') else [])) & visible_sources]
        profile['business_source_ids']=[x for x in profile.get('business_source_ids',[]) if x in visible_sources]
        if profile.get('business_summary') and not profile['business_source_ids']:profile['business_summary']=None
        profile['market']=[m for m in profile.get('market',[]) if m.get('source') in visible_sources];diagnostics=diagnose(periods)
        for o in obs:
            if o.get('period_end'):profile.setdefault('periods',{})[o['period']]={'start':o.get('period_start'),'end':o['period_end']}
        latest_year=diagnostics['years'][-1] if diagnostics['years'] else None
        source_periods={'nv-fy25':'FY2025','ad-fy24':'FY2024'}
        profile['segments']=[s for s in profile['segments'] if s.get('period',source_periods.get(s['source']))==latest_year]
        if latest_year and not profile['segments'] and diagnostics['current'].get('revenue') is not None:
            revenue=next(o for o in reversed(obs) if o['period']==latest_year and o['metric']=='revenue')
            profile['segments']=[{'name':'合并或主体总收入（未拆分业务）','value':revenue['value'],'source':revenue['source_id'],'kind':'Disclosed','period':latest_year,'semantic_role':'consolidated_total'}]
        required={'revenue','gross_profit','operating_income','opex'}
        if diagnostics['years'] and required <= set(diagnostics['current']) and diagnostics['current']['revenue'] and profile['segments']:
            params=defaults(company,diagnostics['current'],profile['segments'])
        else:params=None
        # Legacy AMD calculated liabilities receive observation-level lineage IDs.
        # Dependencies must resolve to concrete observations, not merely metric names.
        for o in obs:
            if o['company']=='AMD' and o['metric']=='liabilities' and o.get('kind')=='Calculated':
                o['depends_on']=[x['id'] for x in obs if x['period']==o['period'] and x['metric'] in ['assets','equity']]
        checks=dashboard(periods,profile,obs)
        diagnostics['checks']=[{'label':c['formula'],'status':c['status'],'difference':c['difference'],'inputs':c['inputs']} for c in checks['checks'] if c['period']==latest_year and c['id'] in ['gross','operating','balance']]
        if profile['mode']=='financial':params=None
        result={'company':profile,'asof':asof,'documents':docs,'observations':obs,'periods':periods,'diagnostics':diagnostics,'relations':checks,'metric_dictionary':METRICS,'defaults':params,'records':records,'revision_history_all_time':all_records,'audit':audit,'ai':{'status':'not_connected','message':'未调用模型 API；V3 findings、Industry Driver Modules 与 Company Map 来自确定性规则和显式模板。'},'storage':'SQLite 本地持久化','review_pending':sum(not o['reviewed'] for o in obs)}
        result['semantic']=build_semantic_snapshot(result)
        result['v3']=build_v3_view(profile,diagnostics,periods,obs,docs,checks,result['semantic'])
        return result
    def calculate(self,company,asof,params):
        s=self.state(company,asof)
        if not s['diagnostics']['years']:raise ValidationError('截至研究日期没有可用的年度输入')
        if s['company']['mode']=='financial':raise ValidationError('金融机构不能使用一般企业 FCFF；请使用金融业务报表口径')
        if s['defaults'] is None:raise ValidationError('年度输入不完整，不能启动预测模型')
        c=s['company'];metrics=s['diagnostics']['current'];year=int(s['diagnostics']['years'][-1][2:])
        # Revenue groups are sourced from a specific annual release; never silently rebase.
        expected=s['diagnostics']['years'][-1]
        if c['mode']=='financial':raise ValidationError('金融机构不能套用一般企业 FCFF 模型；可使用基础报表与净利息勾稽')
        if any(x['period']==expected and ((x['id'] in ['gross','operating'] and x['status']!='pass') or (x['id']=='balance' and x['status']=='fail')) for x in s['relations']['checks']):raise ValidationError('核心损益输入未通过勾稽，或资产负债存在差额；请先在勾稽中心核对')
        if abs(sum(x['value'] for x in c['segments'])-metrics['revenue'])>.01:raise ValidationError('收入分组与最新合并收入不一致，请先审核与更新分组')
        result=scenario_set(company,metrics,c['segments'],params,year)
        chosen={}
        for o in s['observations']:
            if o['period']==expected:chosen[(o['metric'],o['basis'])]=o
        inputs=list(chosen.values())
        result.update({'asof':asof,'input_ids':[o['id'] for o in inputs],'inputs':inputs,'documents':s['documents'],'review_pending':sum(not o['reviewed'] for o in inputs),'period':expected,'segments':c['segments']})
        return result
    def import_starter_pack(self,pack):
        profile=dict(pack.get('company') or {});ticker=str(profile.get('ticker','')).upper()
        if not ticker or not pack.get('documents') or not pack.get('observations'):raise ValidationError('Starter Pack 缺少公司、来源或财务 observations')
        with self.connect() as db:
            if db.execute('SELECT 1 FROM companies WHERE id=?',(ticker,)).fetchone():raise ValidationError('该公司已存在；SEC Starter Pack 不自动覆盖既有研究档案')
            db.execute('INSERT INTO companies VALUES(?,?)',(ticker,encode({k:v for k,v in profile.items() if k!='ticker'})))
            known_docs=set()
            for d in pack['documents']:
                if d.get('company')!=ticker:raise ValidationError('Starter Pack document 公司不一致')
                self._document(db,d);known_docs.add(d['id'])
            imported=0
            for o in pack['observations']:
                if o.get('company')!=ticker or o.get('source_id') not in known_docs:raise ValidationError('Starter Pack observation 来源链无效')
                if o.get('metric') not in METRICS:continue
                db.execute('INSERT INTO observations(id,source_id,company,period,metric,content) VALUES(?,?,?,?,?,?)',(o['id'],o['source_id'],ticker,o['period'],o['metric'],encode(o)));imported+=1
            self._audit(db,'starter_pack',ticker,f"SourceAdapter={pack.get('adapter')}；导入 {imported} 条财务 observations；全部待人工核验")
        return {'ticker':ticker,'asof':pack.get('asof'),'adapter':pack.get('adapter'),'imported':imported,'coverage':pack.get('coverage',{}),'message':'SEC Starter Research Pack 已导入；所有 observations 仍为待人工核验。'}

    def save_record(self,company,kind,content):
        self.check_company(company);ident=identity()
        with self.connect() as db:
            db.execute('INSERT INTO records VALUES(?,?,?,?,?,0)',(ident,company,kind,now(),encode(content)));self._audit(db,'save_'+kind,ident,'用户保存研究记录')
        return ident
    def action(self,route,p):
        if route=='create-company':return self.create_company(p)
        if route=='save-theme':
            name=p.get('theme')
            if name not in ['original','mono','porcelain','navy','plum','copper','night']:raise ValidationError('请选择预设主题')
            with self.connect() as db:db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',('theme',encode(name)))
            return {'theme':name}
        company=p.get('company');self.check_company(company)
        from .research import ROUTES,handle
        if route in ROUTES:return handle(self,route,p)
        if route=='compare':return self.compare(company,p.get('peers',[]),p['asof'],p.get('nearby',False))
        if route=='preview-import':return self.preview_import(p['document'],company)
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
            profile=self.profile(company)
            return {'id':self.save_record(company,'forecast',{**vals,'asof':p['asof'],'period':period,'metric':'revenue','unit':'million','currency':profile['currency'],'basis':profile['basis'],'scope':profile['scope'],'reason':p['reason'],'mode':'historical_exercise' if p['asof']<now()[:10] else 'prospective_unverified'})}
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
    def validate_document(self,p):
        profile=self.check_company(p.get('company'));valid_date(p.get('disclosed_at'))
        with self.connect() as db:
            existing=[json.loads(r['content']) for r in db.execute('SELECT content FROM observations WHERE company=?',(p['company'],))]
        known_windows=dict(profile.get('periods',{}))
        for old in existing:
            if old.get('period_end'):known_windows[old['period']]={'start':old.get('period_start'),'end':old['period_end']}
        from urllib.parse import urlparse
        url=urlparse(p.get('url',''))
        if url.scheme!='https' or not url.netloc:raise ValidationError('来源必须为 HTTPS 链接；后端不会访问该链接')
        if not p.get('id') or not p.get('title') or not p.get('locator'):raise ValidationError('资料缺少 ID、标题或原文位置')
        rows=p.get('observations',[])
        if not rows or len(rows)>200:raise ValidationError('每次导入 1 至 200 个指标')
        import re
        clean=[];seen=set();period_windows={};scales={'one':.000001,'thousand':.001,'ten_thousand':.01,'million':1,'billion':1000}
        for o in rows:
            if o.get('company')!=p['company'] or o.get('currency')!=profile['currency'] or o.get('unit') not in scales or o.get('scope')!=profile['scope'] or o.get('basis')!=profile['basis'] or o.get('kind')!='Disclosed':raise ValidationError('导入币种、准则和报表范围须与公司档案一致；单位可用元/千/万/百万/十亿')
            if not re.fullmatch(r'FY\d{4}(Q[1-4])?',o.get('period','')):raise ValidationError('期间格式错误')
            expected='quarterly' if 'Q' in o['period'] else 'annual'
            if o.get('period_type')!=expected:raise ValidationError('单季和全年口径不一致')
            if not o.get('id') or o.get('metric') not in METRICS:raise ValidationError('缺少 ID 或指标不在字典内')
            if o['metric']=='non_gaap_op':raise ValidationError('调整后利润需独立口径映射，不能作为本次法定报表导入')
            k=(o['period'],o['metric'])
            if k in seen:raise ValidationError('同一资料里不能重复录入同期间同指标')
            seen.add(k)
            if o.get('period_start') or o.get('period_end'):
                start=valid_date(o.get('period_start'));end=valid_date(o.get('period_end'))
                if start>end or end>p['disclosed_at']:raise ValidationError('期间起止日期或披露日期顺序错误')
                if o['period'] in period_windows and period_windows[o['period']]!=(start,end):raise ValidationError('同一期间标签不能对应不同起止日期')
                period_windows[o['period']]=(start,end)
                known=known_windows.get(o['period'],{})
                if known.get('end') and known['end']!=end or known.get('start') and known['start']!=start:raise ValidationError('期间标签与已有资料起止日期冲突；请先确认财政期间，不可直接混合')
            clean.append({**o,'label':METRICS[o['metric']],'source_id':p['id'],'raw_value':float(number(o['value'])),'raw_unit':o['unit'],'unit':'million','value':float(number(o['value'])*number(scales[o['unit']]))})
        doc={k:v for k,v in p.items() if k!='observations'}
        return doc,clean
    def preview_import(self,p,company):
        if p.get('company')!=company:raise ValidationError('预览资料与当前公司不一致')
        doc,clean=self.validate_document(p);periods={}
        for o in clean:periods.setdefault(o['period'],{})[o['metric']]=o['value']
        return {'document':doc,'observations':clean,'relations':dashboard(periods,self.profile(company),clean),'saved':False}
    def import_document(self,p):
        doc,clean=self.validate_document(p)
        with self.connect() as db:
            if db.execute('SELECT 1 FROM documents WHERE id=?',(doc['id'],)).fetchone():raise ValidationError('资料 ID 已存在，重复导入被拒绝')
            self._document(db,doc)
            for o in clean:db.execute('INSERT INTO observations(id,source_id,company,period,metric,content) VALUES(?,?,?,?,?,?)',(o['id'],doc['id'],p['company'],o['period'],o['metric'],encode(o)))
            # Conservative company-level invalidation, explicitly not a precise field DAG.
            count=db.execute("UPDATE records SET stale=1 WHERE company=? AND kind IN ('model','thesis','memo','driver','research')",(p['company'],)).rowcount
            for saved in db.execute("SELECT id,company,content FROM records WHERE kind IN ('comparison','business-note')").fetchall():
                content=json.loads(saved['content'])
                if p['company'] in content.get('company_ids',[saved['company']]):
                    db.execute('UPDATE records SET stale=1 WHERE id=?',(saved['id'],));count+=1
            self._audit(db,'import',doc['id'],f'新增 {len(clean)} 条指标；{count} 条同公司研究记录待复核')
        return {'imported':len(clean),'affected':count,'message':'新资料已保存，旧快照保留；同公司模型、论点和备忘录标记待复核。'}
    def export(self,company,asof):
        s=self.state(company,asof);lines=[f"# Research Atlas / {company}",f"研究截至 {asof}；单位 {s['company']['currency']} million；{s['company']['basis']} / {s['company']['scope']}；研究记录，非投资建议。",'## 来源']
        lines += [f"- {d['title']} | {d['disclosed_at']} | {d['url']} | {d['locator']}" for d in s['documents']]
        lines += ['## 财务诊断',json.dumps(s['diagnostics'],ensure_ascii=False,indent=2),'## 勾稽与输入',json.dumps(s['relations'],ensure_ascii=False,indent=2),json.dumps(s['observations'],ensure_ascii=False,indent=2),'## 研究记录（按显式研究 as-of 过滤；操作时间仅供审计）']
        for r in s['records']:lines += [f"### {r['kind']} / {r['created_at']} / 待复核={bool(r['stale'])}",json.dumps(r['content'],ensure_ascii=False,indent=2)]
        lines += ['## 限制','数据由 AI 辅助录入并保留用户审核状态。当前模型为简化经营预测，默认参数是研究练习假设，未完成完整三表、同行和市场规模覆盖。']
        return '\\n\\n'.join(lines)

    def theme(self):
        with self.connect() as db:r=db.execute('SELECT content FROM settings WHERE key=?',('theme',)).fetchone()
        return json.loads(r['content']) if r else 'original'

    def compare(self,company,peers,asof,nearby=False):
        from datetime import date
        if not isinstance(peers,list) or len(peers)>5:raise ValidationError('一次选择 1 至 5 家竞品')
        ids=list(dict.fromkeys([company]+peers));states=[self.state(c,asof) for c in ids];base=states[0]
        rows=[]
        for s in states:
            p=s['company'];years=s['diagnostics']['years'];year=years[-1] if years else None
            metadata=p.get('periods',{}).get(year,{})
            rows.append({'ticker':p['ticker'],'name':p['name'],'industry':p['industry'],'business_models':p['business_models'],'currency':p['currency'],'basis':p['basis'],'scope':p['scope'],'period':year,'period_end':metadata.get('end'),'period_start':metadata.get('start'),'values':s['diagnostics'].get('current',{}),'ratios':s['diagnostics']['ratios'],'observations':[o for o in s['observations'] if o['period']==year],'review_pending':sum(not o['reviewed'] for o in s['observations'] if o['period']==year),'differences':[{'dimension':a,'description':b,'source_id':c} for a,b,c in DIFFERENTIATION.get(p['ticker'],[]) if c in {d['id'] for d in s['documents']}],'documents':s['documents'],'status':'comparable','reasons':[]})
        anchor=rows[0]
        for row in rows:
            reasons=[];blocking=[]
            if not row['period']:blocking.append('当前研究时点无年度数据')
            for key,title in [('industry','行业'),('currency','币种'),('basis','会计准则'),('scope','合并范围')]:
                if row[key]!=anchor[key] or key=='industry' and row[key]=='unclassified':blocking.append(title+'不一致或未分类')
            if not row['period_end'] or not anchor['period_end']:blocking.append('缺少财政期间结束日期')
            else:
                gap=abs((date.fromisoformat(row['period_end'])-date.fromisoformat(anchor['period_end'])).days)
                if gap:
                    if nearby and gap<=45:reasons.append(f'财年末相差 {gap} 天；仅作相邻年度参考')
                    else:blocking.append(f'财年末相差 {gap} 天，不是严格同期')
            if not row['period_start'] or not anchor['period_start']:
                reasons.append('部分期间起始日未补齐；时长未完全核验')
                if not nearby:blocking.append('严格比较需要完整期间起止日期')
            elif abs((date.fromisoformat(row['period_end'])-date.fromisoformat(row['period_start'])).days-(date.fromisoformat(anchor['period_end'])-date.fromisoformat(anchor['period_start'])).days)>7:blocking.append('年度时长不一致')
            if row['review_pending']:reasons.append(f"{row['review_pending']} 条输入待用户审核")
            if row['ticker']!=anchor['ticker']:reasons.append('业务与产品组合可能不同；不能由合并利润率差异直接推断产品竞争力')
            current_checks=next(s for s in states if s['company']['ticker']==row['ticker'])['relations']['checks']
            if any(c['status']=='fail' and c['period']==row['period'] for c in current_checks):blocking.append('存在未解决的报表勾稽差异')
            row['reasons']=blocking+reasons;row['status']='blocked' if blocking else 'qualified' if reasons else 'comparable';row['ranking_allowed']=not blocking and not reasons
        from .research import metric_comparability
        metric_comparability(rows,states,nearby)
        return {'asof':asof,'rows':rows,'nearby':bool(nearby),'note':'逐指标判断可比性；无量纲比例不因币种不同一律隐藏。业务结构、会计政策与期间仍需核验，不自动排名。公司收入占比不是市场份额。'}
