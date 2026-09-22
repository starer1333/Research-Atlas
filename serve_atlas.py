"""Start with: D:\\python\\python.exe -B serve_atlas.py. All writes are workspace-local."""
import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
RUNTIME=ROOT/'.runtime'/'workbench';RUNTIME.mkdir(parents=True,exist_ok=True)
for k in ['TEMP','TMP','TMPDIR']:os.environ[k]=str(RUNTIME)
sys.dont_write_bytecode=True
import json,secrets,argparse
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlsplit,parse_qs
from atlas.store import Store
from atlas.engine import ValidationError
from atlas.sources import SecEdgarAdapter
from atlas.planner import PlannerConfig, PlannerError, ResearchPlanner

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8766);parser.add_argument('--db',default=str(RUNTIME/'research.sqlite3'));parser.add_argument('--enable-sec',action='store_true');parser.add_argument('--sec-user-agent',default=os.environ.get('ATLAS_SEC_USER_AGENT',''));parser.add_argument('--enable-ai',action='store_true');parser.add_argument('--ai-base-url',default=os.environ.get('ATLAS_AI_BASE_URL',''));parser.add_argument('--ai-api-key',default=os.environ.get('ATLAS_AI_API_KEY',''));parser.add_argument('--ai-model',default=os.environ.get('ATLAS_AI_MODEL',''));args=parser.parse_args()
    dbpath=Path(args.db).resolve()
    if ROOT not in dbpath.parents:raise SystemExit('Database must remain inside the D-drive project')
    store=Store(dbpath);token=secrets.token_urlsafe(32);origin=f'http://127.0.0.1:{args.port}'
    sec_requested=args.enable_sec
    if sec_requested and not args.sec_user_agent:raise SystemExit('SEC access requires --sec-user-agent or ATLAS_SEC_USER_AGENT')
    sec_adapter=SecEdgarAdapter(args.sec_user_agent) if sec_requested else None
    ai_planner=None
    if args.enable_ai:
        try:ai_planner=ResearchPlanner(PlannerConfig.validate(args.ai_base_url,args.ai_api_key,args.ai_model))
        except PlannerError as e:raise SystemExit(str(e))
    assets={'/':'v3-index.html','/index.html':'v3-index.html','/v3':'v3-index.html','/v3.css':'v3.css','/v3-liquid.css':'v3-liquid.css','/v3-charts.js':'v3-charts.js','/v3.js':'v3.js','/v2':'index.html','/workbench.css':'workbench.css','/workbench.js':'workbench.js','/workspace.js':'workspace.js','/workspace.css':'workspace.css','/themes.css':'themes.css'}
    assets.update({'/research.js':'research.js','/research.css':'research.css'})
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def reply(self,data,status=200,mime='application/json; charset=utf-8'):
            body=(json.dumps(data,ensure_ascii=False,allow_nan=False).encode() if mime.startswith('application/json') else data if isinstance(data,bytes) else data.encode())
            self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.send_header('Content-Security-Policy',"default-src 'self'; connect-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");self.end_headers();self.wfile.write(body)
        def allowed(self):return self.headers.get('Host')==f'127.0.0.1:{args.port}'
        def do_GET(self):
            if not self.allowed():return self.reply({'error':'Host rejected'},403)
            parsed=urlsplit(self.path);q=parse_qs(parsed.query);route=parsed.path
            try:
                if route=='/api/session':return self.reply({'token':token,'companies':store.companies(),'theme':store.theme(),'sources':{'sec':{'enabled':bool(sec_adapter),'adapter':'sec-edgar-direct','note':'Official SEC EDGAR; opt-in network access'},'ai':ai_planner.capability() if ai_planner else {'enabled':False,'provider':'openai-compatible','writes_facts':False,'persists_automatically':False,'note':'Optional AI Research Planner is off by default'}}})
                if route=='/api/companies':return self.reply({'companies':store.companies()})
                if route=='/api/state':return self.reply(store.state(q.get('company',['NVDA'])[0],q.get('asof',['2025-03-01'])[0]))
                if route=='/api/export':return self.reply(store.export(q['company'][0],q['asof'][0]),mime='text/markdown; charset=utf-8')
                if route in assets:
                    p=ROOT/'workbench'/assets[route];return self.reply(p.read_bytes(),mime='text/html; charset=utf-8' if p.suffix=='.html' else 'text/css; charset=utf-8' if p.suffix=='.css' else 'text/javascript; charset=utf-8')
                return self.reply({'error':'Not found'},404)
            except (ValidationError,KeyError) as e:return self.reply({'error':str(e)},400)
        def do_POST(self):
            if not self.allowed() or self.headers.get('Origin')!=origin or not secrets.compare_digest(self.headers.get('X-Atlas-Token',''),token):return self.reply({'error':'本地写入验证失败'},403)
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=1000000:raise ValidationError('请求大小限制为 1MB')
                if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValidationError('仅接受 JSON')
                p=json.loads(self.rfile.read(size));route=urlsplit(self.path).path
                if not route.startswith('/api/'):return self.reply({'error':'Not found'},404)
                if route=='/api/sec-starter-pack':
                    if not sec_adapter:raise ValidationError('SEC SourceAdapter 未启用；启动服务时设置 ATLAS_SEC_USER_AGENT 并使用 --enable-sec')
                    pack=sec_adapter.starter_pack(p.get('query'))
                    return self.reply(store.import_starter_pack(pack))
                if route=='/api/ai-plan':
                    if not ai_planner:raise ValidationError('AI Research Planner 未启用；设置 ATLAS_AI_BASE_URL / ATLAS_AI_API_KEY / ATLAS_AI_MODEL 并使用 --enable-ai')
                    company=p.get('company','NVDA');asof=p.get('asof','2025-03-01')
                    try:return self.reply(ai_planner.plan(store.state(company,asof),focus=p.get('focus')))
                    except PlannerError as e:raise ValidationError(str(e))
                result=store.action(route[5:],p);return self.reply(result)
            except (ValueError,KeyError,TypeError) as e:return self.reply({'error':str(e)},400)
            except Exception:return self.reply({'error':'操作失败，数据未提交；请检查重复 ID 或输入格式'},400)
    print(f'Research Atlas ready: {origin}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
if __name__=='__main__':main()
