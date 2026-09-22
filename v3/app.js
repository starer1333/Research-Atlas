'use strict';
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)],fmt=(v,d=0)=>v==null?'—':Number(v).toLocaleString('en-US',{maximumFractionDigits:d,minimumFractionDigits:d}),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const previewView=new URLSearchParams(location.search).get('view');
let db={},ticker='NVDA',page=previewView==='business'?'analysis':'research',tab=previewView==='business'?'business':'financials';
const ratio=(a,b)=>a==null||!b?null:a/b*100,growth=(a,b)=>a==null||b==null||!a?null:(b/a-1)*100;
function state(){return db[ticker]}
function chartHost(id,label){return '<div class="chart-canvas" id="'+id+'" role="img" aria-label="'+esc(label)+'"></div>'}
function sceneTone(){
  if(page==='research')return 'blue';
  if(page==='evidence')return 'teal';
  if(page==='report')return 'gold';
  if(page==='analysis'){
    return ({financials:'lavender',business:'green',peers:'mint',scenario:'gold'})[tab]||'lavender';
  }
  return 'blue';
}
function setAmbient(){
  delete document.documentElement.dataset.ambient;
  document.documentElement.dataset.tone=sceneTone();
}
function smoothRender(){
  if(document.startViewTransition){document.startViewTransition(()=>render())}
  else render();
}
function plannerPreview(){
  return '<div class="planner-shell"><div class="planner-head"><div><span class="eyebrow">V3-10 · OPTIONAL AI RESEARCH PLANNER</span><h3>AI plans the investigation. It does not own the facts.</h3></div><span class="ai-badge">OFF BY DEFAULT</span></div><p>Local V3 can send a compact grounded snapshot to an OpenAI-compatible model to suggest research questions, evidence to seek and counter-evidence. The model cannot write observations, verify evidence, calculate finance or create a final claim.</p><div class="planner-boundaries"><span>ai_suggested</span><span>not_verified</span><span>explicit save only</span><span>source-ID constrained</span></div><small>Public Pages intentionally does not call any AI provider.</small></div>'
}
function renderCharts(){
  requestAnimationFrame(()=>{
    if(!window.AtlasPreviewCharts)return;
    const s=state();if(!s)return;
    const t=$('#chart-trajectory');if(t)AtlasPreviewCharts.trajectory(t,s);
    const w=$('#chart-working-capital');if(w)AtlasPreviewCharts.workingCapital(w,s);
    const m=$('#chart-segment-mix');if(m)AtlasPreviewCharts.segmentMix(m,s);
  })
}
function latestObs(metric){const s=state(),y=s.diagnostics.years.at(-1);return s.observations.findLast(o=>o.metric===metric&&o.period===y)}
function source(id){return state().documents.find(d=>d.id===id)}
function findings(s){const c=s.diagnostics.current,p=s.diagnostics.previous,r=s.diagnostics.ratios||{},out=[];const rev=growth(p.revenue,c.revenue),cfo=growth(p.cfo,c.cfo),ar=growth(p.receivables,c.receivables),inv=growth(p.inventory,c.inventory),cost=growth(p.cost,c.cost);
 const add=(id,cat,title,statement,why,q,mech,metrics,sev='watch')=>out.push({id,cat,title,statement,why,q,mech,metrics,sev});
 if(rev!=null&&cfo!=null&&rev-cfo>=10)add('cash','Cash conversion','利润与现金的增长出现分化','收入同比约 +'+fmt(rev,1)+'%，经营现金流同比约 +'+fmt(cfo,1)+'%。','增长没有以相同速度转化为经营现金流，应该继续检查营运资金和业务结构。','为什么收入增长没有同步转化为经营现金流？',['付款条件/客户结构','存货准备与产品切换','应付节奏','现金流时点因素'],['revenue','cfo','receivables','inventory','payables'],'high');
 if(rev!=null&&ar!=null&&ar-rev>=10)add('ar','Working capital','应收账款增速快于收入','应收同比约 +'+fmt(ar,1)+'%，高于收入增速 '+fmt(ar-rev,1)+'pp。','可能反映回款节奏、客户结构或季末确认时点变化。','应收账款为什么比收入增长更快？',['付款条件','客户集中度','季末收入节奏','正常增长占资'],['receivables','revenue','cfo']);
 const base=cost??rev;if(base!=null&&inv!=null&&inv-base>=10)add('inv','Working capital','存货增速高于业务基准','存货同比约 +'+fmt(inv,1)+'%，高于'+(cost!=null?'成本':'收入')+'增速 '+fmt(inv-base,1)+'pp。','它可能是需求准备，也可能来自产品切换、渠道和供应链节奏。','存货增长是在为未来需求准备，还是反映周转变化？',['提前备货','产品切换','供应链策略','需求/渠道变化'],['inventory','cost','revenue','cfo']);
 const gm0=ratio(p.gross_profit,p.revenue),gm1=ratio(c.gross_profit,c.revenue);if(gm0!=null&&gm1!=null&&Math.abs(gm1-gm0)>=2)add('gm','Profitability','毛利率发生明显变化','毛利率从 '+fmt(gm0,1)+'% 变为 '+fmt(gm1,1)+'%。','需要结合价格、产品组合、成本、规模和会计分类解释。','什么因素解释了毛利率的变化？',['产品组合/价格','投入成本','规模/利用率','业务/地区组合'],['revenue','gross_profit','cost']);
 if(r.cash_conversion!=null&&c.net_income>0&&r.cash_conversion<80)add('eq','Earnings quality','净利润向经营现金流的转化偏弱','CFO / Net income 约 '+fmt(r.cash_conversion,1)+'%。','单期偏低不等于利润失真，应先检查营运资金和非现金因素。','净利润和经营现金流为什么存在差异？',['营运资金','非现金费用','税费时点','业务组合'],['net_income','cfo','receivables','inventory','payables']);
 const seg=s.company.segments||[],revNow=c.revenue;if(seg.length&&revNow){const top=seg.reduce((a,b)=>a.value>b.value?a:b),share=top.value/revNow*100;if(share>=60)add('seg','Segment economics','收入集中在主要业务板块',top.name+' 约占当前收入 '+fmt(share,1)+'%。','集中度本身不是好坏判断，但该业务的需求、价格与竞争更重要。','主要业务板块的增长驱动是否可持续？',['终端需求','产品与价格','客户集中度','竞争与替代'],['revenue']);}
 return out.slice(0,5)}
function nav(){$$('[data-page]').forEach(b=>b.setAttribute('aria-current',b.dataset.page===page?'page':'false'))}
function metric(l,v,n){return '<div class="metric"><small>'+esc(l)+'</small><b>'+v+'</b><small>'+esc(n||'')+'</small></div>'}
function head(k,t,n){return '<div class="section-head"><div><span class="eyebrow">'+esc(k)+'</span><h2>'+esc(t)+'</h2></div><p>'+esc(n||'')+'</p></div>'}
function coverage(s){return '<div class="coverage"><span class="eyebrow">SOURCE COVERAGE</span><strong>'+s.documents.length+'</strong><p>份公开来源</p><p>'+s.observations.length+' observations · 全部仍为待人工复核</p></div>'}
function chart(s){const rows=s.diagnostics.years.map(y=>({y,r:s.periods[y]?.revenue,m:ratio(s.periods[y]?.operating_income,s.periods[y]?.revenue)})).filter(x=>x.r!=null),w=620,h=220,p=36,max=Math.max(...rows.map(x=>x.r))*1.1,step=(w-p*2)/rows.length,bw=Math.min(72,step*.5),mmax=Math.max(1,...rows.map(x=>Math.abs(x.m||0)))*1.2,pts=[];let out='<svg viewBox="0 0 '+w+' '+h+'">';[0,.25,.5,.75,1].forEach(t=>{const yy=h-p-(h-p*2)*t;out+='<line class="gridline" x1="'+p+'" x2="'+(w-p)+'" y1="'+yy+'" y2="'+yy+'"/>'});rows.forEach((x,i)=>{const xx=p+step*i+step/2,yy=h-p-x.r/max*(h-p*2);out+='<rect class="bar" x="'+(xx-bw/2)+'" y="'+yy+'" width="'+bw+'" height="'+(h-p-yy)+'"/><text class="axis" text-anchor="middle" x="'+xx+'" y="'+(h-11)+'">'+x.y+'</text>';if(x.m!=null)pts.push([xx,h-p-x.m/mmax*(h-p*2)])});if(pts.length){out+='<path class="line" d="'+pts.map((x,i)=>(i?'L':'M')+x[0]+' '+x[1]).join(' ')+'"/>';pts.forEach(x=>out+='<circle class="dot" r="4" cx="'+x[0]+'" cy="'+x[1]+'"/>')}return out+'</svg>'}
function seg(s){const rev=s.diagnostics.current.revenue||1,arr=s.company.segments||[];return arr.length?'<div class="segments">'+arr.map(x=>{const pct=x.value/rev*100;return '<div><div class="segment-top"><span>'+esc(x.name)+'</span><b>'+fmt(x.value)+' · '+fmt(pct,1)+'%</b></div><div class="track"><div class="fill" style="width:'+Math.min(100,pct)+'%"></div></div></div>'}).join('')+'</div>':'<div class="empty">没有分部结构。</div>'}
function findingCard(f){return '<article class="finding '+f.sev+'" data-id="'+f.id+'"><span class="eyebrow">'+f.cat+'</span><h3>'+f.title+'</h3><p>'+f.statement+'</p><div class="actions"><button data-act="why">Why?</button><button data-act="evidence">Evidence</button><button data-act="compare">Compare</button><button data-act="research">Add to Research</button></div><div class="detail" hidden><div><span class="eyebrow">WHY THIS MATTERS</span><p>'+f.why+'</p></div><div><span class="eyebrow">POSSIBLE MECHANISMS</span><ul>'+f.mech.map(x=>'<li>'+x+'</li>').join('')+'</ul></div></div></article>'}
function renderResearch(s){
 const f=findings(s),r=s.diagnostics.ratios,curr=s.diagnostics.current,y=s.diagnostics.years.at(-1);
 const ai='<details class="context-disclosure"><summary>打开 Optional AI Research Planner</summary><div class="context-body">'+plannerPreview()+'</div></details>';
 $('#content').innerHTML=
 '<div class="hero"><div><span class="eyebrow">60-second company view</span><h1>'+esc(s.company.name)+'</h1><p>'+esc(s.company.subtitle||s.company.industry)+'。先看少量高信号变化，再进入证据、比较和更深分析；系统提出问题，但不会自动替用户形成最终判断。</p></div>'+coverage(s)+'</div>'+
 '<div class="metrics">'+metric('Revenue',fmt(curr.revenue),y)+metric('Revenue growth',r.revenue_growth==null?'—':fmt(r.revenue_growth,1)+'%','YoY')+metric('Operating margin',r.op_margin==null?'—':fmt(r.op_margin,1)+'%','GAAP')+metric('Cash conversion',r.cash_conversion==null?'—':fmt(r.cash_conversion,1)+'%','CFO / Net income')+'</div>'+
 '<section class="section">'+head('What changed','值得研究的变化','先看少量高信号关系。异常关系是 investigation trigger，不是“公司好/坏”的结论。')+'<div class="findings">'+(f.length?f.map(findingCard).join(''):'<div class="empty">没有触发预设高信号规则。</div>')+'</div></section>'+
 '<section class="section">'+head('Financial trajectory','先看趋势，再决定往哪里钻','ECharts 用于 inspection，不替代 evidence 和解释。')+'<div class="grid2"><div class="card chart-card"><div class="chart-title"><h3>Revenue × Operating Margin</h3><span>Trend</span></div>'+chartHost('chart-trajectory','Revenue and operating margin trend')+'</div><div class="card chart-card"><div class="chart-title"><h3>Cash & Working Capital</h3><span>Relationship</span></div>'+chartHost('chart-working-capital','Cash and working capital trend')+'</div></div></section>'+
 '<section class="section">'+head('Questions worth investigating','从问题进入，而不是从模型参数进入','这是 V3 的主路径；选择问题后再进入 Evidence / Compare / Scenario。')+f.map((x,i)=>'<div class="question"><span>0'+(i+1)+'</span><b>'+x.q+'</b><button class="linkbtn" data-q="'+i+'">开始研究 →</button></div>').join('')+'</section>'+
 '<section class="section">'+head('Optional intelligence','AI 只规划研究，不拥有事实','Public preview 只展示边界；真实 planner 在本地 runtime 中显式启用。')+ai+'</section>'
}
function renderEvidence(s){const checks=s.relations.checks||[];$('#content').innerHTML='<div class="hero"><div><span class="eyebrow">EVIDENCE</span><h1>事实从哪里来？</h1><p>每个数字都要能回到来源、期间、口径和审核状态。Data Integrity 只负责识别数据问题，不代表 Financial Quality。</p></div>'+coverage(s)+'</div><section class="section">'+head('SOURCE REGISTRY','当前来源','点击打开证据面板。')+s.documents.map(d=>'<div class="source"><div><h3>'+esc(d.title)+'</h3><p>'+esc(d.disclosed_at)+' · '+esc(d.locator)+'</p></div><button data-source="'+d.id+'">查看来源</button></div>').join('')+'</section><section class="section">'+head('DATA INTEGRITY','后台完整性检查','Assets = Liabilities + Equity 在这里，不再作为财务质量结论。')+'<details class="integrity"><summary>展开 '+checks.length+' 条 consistency checks</summary>'+checks.slice(-12).map(c=>'<div class="source"><div><h3>'+esc(c.formula)+'</h3><p>'+esc(c.period)+' · '+esc(c.verification||'unresolved')+'</p></div><b>'+esc(c.status)+'</b></div>').join('')+'</details></section>'}
function peerTable(){const s=state(),peers=Object.values(db).filter(x=>x.company.industry===s.company.industry).slice(0,3);return '<div class="gate"><span class="eyebrow">COMPARABILITY GATE</span><h3>先判断“能不能比”</h3><ul><li>Period / accounting basis / scope：当前 fixture 只做历史研究参考。</li><li>Business mix：不同公司业务组合不同，因此利润率差异只能 qualified comparison。</li><li>不自动输出竞争排名。</li></ul></div><table class="peer"><thead><tr><th>Metric</th>'+peers.map(x=>'<th>'+x.company.ticker+'</th>').join('')+'</tr></thead><tbody>'+[['Revenue growth','revenue_growth'],['Gross margin','gross_margin'],['Operating margin','op_margin'],['Cash conversion','cash_conversion']].map(([l,k])=>'<tr><td>'+l+'</td>'+peers.map(x=>'<td>'+fmt(x.diagnostics.ratios[k],1)+'%</td>').join('')+'</tr>').join('')+'</tbody></table>'}
function previewIndustry(s){
  const software=(s.company.mode==='software'||/software/i.test(s.company.industry||''));
  return software?{
    label:'SaaS / Subscription',
    reason:'mode=software',
    drivers:[
      ['Recurring base','ARR / RPO / subscription revenue','Revenue'],
      ['Retention / churn','gross retention / logo retention','Revenue'],
      ['Expansion / NRR','NRR / DBNRR / seats','Revenue'],
      ['Pricing / packaging','ARPU / price uplift','Revenue · Gross profit'],
      ['SBC / opex','SBC / R&D / S&M','Operating income · CFO']
    ],
    notes:['ARR/RPO definitions vary and are not interchangeable with revenue.','Retention definitions and customer cohorts differ across issuers.']
  }:{
    label:'Semiconductor / Hardware',
    reason:'industry / hardware fixture',
    drivers:[
      ['Volume / demand','shipments / units / compute demand','Revenue'],
      ['ASP / pricing','ASP / price-mix','Revenue · Gross profit'],
      ['Product mix','segment / product mix','Revenue · Gross profit'],
      ['Unit cost / yield','wafer cost / yield / utilization','Cost · Gross profit'],
      ['Inventory / transition','DIO / write-downs','Inventory · CFO'],
      ['Capacity / CapEx','capacity commitments','CapEx · Assets']
    ],
    notes:['Gross margin needs fabless vs integrated-manufacturing context.','Segment revenue is not market share.']
  }
}
function previewCompanyMap(s,m){
  const segs=s.company.segments||[];
  const metrics=['Revenue','Gross profit','CFO','Inventory'];
  const products=s.company.mode==='software'?['Product / platform candidates']:['GPU / platform candidates'];
  const layer=(title,rows,kind)=>'<section class="map-layer"><span class="eyebrow">'+title+'</span><div class="map-stack">'+rows.map(x=>'<article class="map-node '+(kind==='driver'?'map-driver':'')+'"><b>'+esc(x)+'</b><small>'+(kind==='driver'?'industry template':'preview node')+'</small></article>').join('')+'</div></section>';
  return '<div class="company-map">'+
    layer('Company',[s.company.name],'company')+'<div class="map-arrow">→</div>'+
    layer('Segments / Products',[...segs.map(x=>x.name),...products].slice(0,5),'business')+'<div class="map-arrow">→</div>'+
    layer('Context',['Customer / Competitor / Geography','evidence slot'],'context')+'<div class="map-arrow">→</div>'+
    layer('Operating Drivers',m.drivers.map(x=>x[0]).slice(0,6),'driver')+'<div class="map-arrow">→</div>'+
    layer('Financial Outcomes',metrics,'metric')+
  '</div><p class="map-boundary">Evidence-backed objects, pending-review candidates and industry templates remain separate states. Static preview does not fabricate live SEC entities.</p>'
}
function businessPreview(s){
  const sourceDoc=s.documents.find(d=>/10-k|annual/i.test((d.title||'')+' '+(d.locator||'')))||s.documents[0];
  const segs=s.company.segments||[];
  const m=previewIndustry(s);
  const segmentCards=segs.length?segs.map(x=>'<div class="candidate-row"><div><b>'+esc(x.name)+'</b><small>existing structured fixture · source-linked</small></div><span class="candidate-tag">evidence object</span></div>').join(''):'<div class="empty">静态 fixture 没有 segment rows。</div>';
  const segmentChart=segs.some(x=>Number(x.value)>0)?chartHost('chart-segment-mix','Numeric segment mix'):'';
  const drivers=m.drivers.map(d=>'<article class="driver-card"><div class="driver-top"><span class="candidate-tag">template</span><span class="driver-status">not a company fact</span></div><h4>'+esc(d[0])+'</h4><p>'+esc(d[1])+'</p><dl><dt>Financial links</dt><dd>'+esc(d[2])+'</dd><dt>Comparability</dt><dd>qualified / check definition</dd></dl></article>').join('');
  return head('V3-7 · COMPANY / PRODUCT MAP','Company → Segment / Product → Context → Driver → Financial Outcome','静态页面展示 V3-7 / V3-8 的交互结构；真正的 SEC 语义对象和 source lineage 在本地 V3 backend 生成。')+
  '<div class="card">'+previewCompanyMap(s,m)+'</div>'+
  '<section class="section">'+head('V3-8 · INDUSTRY DRIVER MODULE',m.label,'Selection: '+m.reason+'。行业 driver 只告诉研究者下一步应该找什么证据。')+
  '<div class="card"><div class="driver-grid">'+drivers+'</div><details class="integrity driver-notes"><summary>Comparability notes</summary><ul>'+m.notes.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul></details></div></section>'+
  '<div class="grid2"><div class="card"><span class="eyebrow">10-K · ITEM 1 BUSINESS</span><h3 class="business-title">What the filing says</h3><p class="business-copy">本地 V3-6 会从最新 SEC 10-K primary HTML 中定位 Item 1. Business，并显示 source、locator、review state 与 filing excerpt。静态预览不发起 SEC 网络请求，因此这里不伪造年报摘录。</p><div class="source-meta"><b>'+esc(sourceDoc?.title||'SEC source available in local V3')+'</b><small>deterministic parser · no LLM · source fingerprinted</small></div></div>'+
  '<div class="card"><span class="eyebrow">SEGMENT CANDIDATES</span><h3 class="business-title">How the company is organized</h3>'+segmentChart+'<div class="candidate-list">'+segmentCards+'</div></div></div>'+
  '<div class="grid2 business-row"><div class="card"><span class="eyebrow">PRODUCT / PLATFORM CANDIDATES</span><h3 class="business-title">What it sells or offers</h3><div class="empty compact">静态 fixture 未包含 live 10-K Product candidates。Local V3-6 会保留 source / excerpt / review state，未验证的 Product 不会自动映射到 Segment。</div></div>'+
  '<div class="card"><span class="eyebrow">SEMANTIC CONTRACT 3.3</span><h3 class="business-title">Evidence structure</h3><div class="semantic-chain"><span>Company</span><i>→</i><span>Segment</span><i>→</i><span>Product</span><i>→</i><span>ContextEntity</span><i>→</i><span>Driver</span><i>→</i><span>Metric</span></div><p class="business-copy">ContextEntity supports Customer / Competitor / Geography / Channel / Risk. Template ≠ company fact; candidate ≠ reviewed evidence.</p></div></div>'
}
function renderAnalysis(s){$('#content').innerHTML='<div class="hero"><div><span class="eyebrow">ANALYSIS</span><h1>发生了什么，为什么？</h1><p>Financials / Business / Peers / Scenario 都属于 Analysis，不再占据一级导航。</p></div>'+coverage(s)+'</div><div class="subnav"><button data-tab="financials" class="'+(tab==='financials'?'active':'')+'">Financials</button><button data-tab="business" class="'+(tab==='business'?'active':'')+'">Business</button><button data-tab="peers" class="'+(tab==='peers'?'active':'')+'">Peers</button><button data-tab="scenario" class="'+(tab==='scenario'?'active':'')+'">Scenario</button></div><section class="section">'+(tab==='financials'?head('FINANCIAL DIAGNOSTICS','关系优先，不是 ratio 展览','Growth → Profitability → Cash → Working Capital。')+'<div class="findings">'+findings(s).slice(0,3).map(findingCard).join('')+'</div>':tab==='business'?businessPreview(s):tab==='peers'?head('COMPARATIVE REASONING','先判断能不能比，再解释差异','Peer comparison 不等于 leaderboard。')+peerTable():head('QUESTION-FIRST SCENARIO','Scenario 由研究问题触发','静态预览暂不写入参数和版本。')+'<div class="empty"><h3>先保存一个 Research Question</h3><p>V3 不再让用户一进入产品就调 WACC / growth / margin。研究问题 → mechanism → scenario。</p></div>')+'</section>'}
function renderReport(s){$('#content').innerHTML='<div class="hero"><div><span class="eyebrow">RESEARCH MEMORY</span><h1>我现在怎么看？</h1><p>Report 汇集研究问题、证据、反证、情景和 revision。静态预览不保存真实记录。</p></div>'+coverage(s)+'</div><section class="section">'+head('CURRENT RESEARCH THREADS','正在研究的问题','这里最终会连接 Claim / Counter-evidence / What changes my mind。')+'<div class="timeline">'+findings(s).slice(0,3).map((f,i)=>'<article><span class="eyebrow">OPEN QUESTION · 0'+(i+1)+'</span><h3>'+f.q+'</h3><p>'+f.why+'</p></article>').join('')+'</div></section>'}
function render(){const s=state();if(!s)return;setAmbient();nav();$('#ticker').textContent=ticker;$('#companyName').textContent=s.company.name;$('#subtitle').textContent=s.company.subtitle||s.company.industry;if(page==='research')renderResearch(s);if(page==='evidence')renderEvidence(s);if(page==='analysis')renderAnalysis(s);if(page==='report')renderReport(s);const content=$('#content');content.classList.remove('is-entering');requestAnimationFrame(()=>content.classList.add('is-entering'));renderCharts()}
function openEvidenceFor(f){const s=state(),ys=s.diagnostics.years.slice(-2),obs=s.observations.filter(o=>f.metrics.includes(o.metric)&&ys.includes(o.period));$('#drawerTitle').textContent=f.title;$('#drawerBody').innerHTML=obs.map(o=>{const d=source(o.source_id);return '<div class="ev"><span class="eyebrow">'+esc(o.kind)+' · PENDING REVIEW</span><h3>'+esc(o.label||o.metric)+'</h3><dl><dt>Value</dt><dd>'+fmt(o.value)+' '+esc(o.currency)+' '+esc(o.unit)+'</dd><dt>Period</dt><dd>'+esc(o.period)+'</dd><dt>Basis / Scope</dt><dd>'+esc(o.basis)+' · '+esc(o.scope)+'</dd><dt>Source</dt><dd>'+esc(d?.title||o.source_id)+'</dd><dt>Locator</dt><dd>'+esc(d?.locator||'—')+'</dd></dl>'+((d&&d.url)?'<a target="_blank" rel="noopener noreferrer" href="'+esc(d.url)+'">打开官方原文 ↗</a>':'')+'</div>'}).join('');$('#drawer').showModal()}
document.addEventListener('click',e=>{const p=e.target.closest('[data-page]');if(p){page=p.dataset.page;smoothRender();return}const t=e.target.closest('[data-tab]');if(t){tab=t.dataset.tab;setAmbient();smoothRender();return}const src=e.target.closest('[data-source]');if(src){const d=source(src.dataset.source);$('#drawerTitle').textContent=d.title;$('#drawerBody').innerHTML='<div class="ev"><dl><dt>Disclosed</dt><dd>'+d.disclosed_at+'</dd><dt>Locator</dt><dd>'+esc(d.locator)+'</dd></dl><a target="_blank" rel="noopener noreferrer" href="'+esc(d.url)+'">打开官方原文 ↗</a></div>';$('#drawer').showModal();return}const a=e.target.closest('[data-act]');if(a){const card=a.closest('[data-id]'),f=findings(state()).find(x=>x.id===card.dataset.id);if(a.dataset.act==='why')card.querySelector('.detail').hidden=!card.querySelector('.detail').hidden;if(a.dataset.act==='evidence')openEvidenceFor(f);if(a.dataset.act==='compare'){page='analysis';tab='peers';render()}if(a.dataset.act==='research'){page='report';render()}return}});
window.addEventListener('resize',()=>window.AtlasPreviewCharts?.resizeAll());
$('#close').onclick=()=>$('#drawer').close();$('#company').onchange=e=>{ticker=e.target.value;render()};
fetch('../data.json').then(r=>r.json()).then(x=>{db=x;$('#company').innerHTML=Object.keys(db).map(k=>'<option>'+k+'</option>').join('');render()}).catch(()=>{$('#content').innerHTML='<div class="empty">预览资料加载失败，请稍后刷新。</div>'});