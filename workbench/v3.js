'use strict';
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=(v,d=0)=>v==null?'—':Number(v).toLocaleString('en-US',{maximumFractionDigits:d,minimumFractionDigits:d});
let token='',companies=[],sourceCapabilities={},state=null,page='research',analysisTab='financials',selectedFinding=null,selectedQuestionId=null,peerResult=null,scenarioResult=null,plannerResult=null,serial=0;
const PAGE_ORDER=['research','evidence','analysis','report'];
const TAB_ORDER=['financials','business','peers','scenario'];
function directionBetween(order,from,to){const a=order.indexOf(from),b=order.indexOf(to);return b<a?'backward':'forward'}

function context(){return {company:state?.company?.ticker||resolveCompany($('#companySearch').value)?.ticker||'NVDA',asof:$('#asof').value}}
function toast(msg){const t=$('#toast');t.textContent=msg;t.hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>t.hidden=true,3200)}
function showError(msg){const b=$('#error');b.textContent=msg;b.hidden=false}
function clearError(){$('#error').hidden=true}
async function getJson(url){const r=await fetch(url);const d=await r.json();if(!r.ok)throw new Error(d.error||'读取失败');return d}
async function post(route,payload){const r=await fetch('/api/'+route,{method:'POST',headers:{'Content-Type':'application/json','X-Atlas-Token':token},body:JSON.stringify({...context(),...payload})});const d=await r.json();if(!r.ok)throw new Error(d.error||'操作失败');return d}
function resolveCompany(q){q=String(q||'').trim().toLowerCase();return companies.find(c=>c.ticker.toLowerCase()===q||c.name.toLowerCase()===q||c.name.toLowerCase().includes(q))}
function renderCompanyMenu(filter=''){
  const menu=$('#companyMenu');if(!menu)return;
  const q=String(filter||'').trim().toLowerCase();
  const rows=companies.filter(company=>!q||company.ticker.toLowerCase().includes(q)||company.name.toLowerCase().includes(q)).slice(0,12);
  menu.innerHTML=rows.length?rows.map(company=>'<button type="button" class="combo-option" role="option" data-company-option="'+esc(company.ticker)+'" aria-selected="'+(state?.company?.ticker===company.ticker?'true':'false')+'"><span>'+esc(company.ticker)+'</span><small>'+esc(company.name)+'</small></button>').join(''):'<div class="combo-option" aria-disabled="true"><span>没有匹配项</span><small>按 Enter 可尝试 SEC ticker</small></div>';
}
function setCompanyMenu(open){
  const box=$('#companyCombobox'),menu=$('#companyMenu'),input=$('#companySearch'),toggle=$('#companyToggle');
  if(!box||!menu)return;
  box.dataset.open=open?'true':'false';menu.hidden=!open;
  input?.setAttribute('aria-expanded',open?'true':'false');toggle?.setAttribute('aria-expanded',open?'true':'false');
  if(open)renderCompanyMenu(input?.value||'');
}
async function openCompanyQuery(query=$('#companySearch').value.trim()){
  const existing=resolveCompany(query);
  if(existing){setCompanyMenu(false);await load(existing.ticker);return}
  if(!query)return;
  if(!sourceCapabilities.sec?.enabled){
    showError('当前未启用 SEC SourceAdapter。设置 ATLAS_SEC_USER_AGENT 并用 --enable-sec 启动后，可直接输入美国上市公司 ticker。');
    return;
  }
  clearError();setCompanyMenu(false);$('#status').textContent='SEC EDGAR：正在解析公司、filings 与 Company Facts…';
  try{
    const result=await post('sec-starter-pack',{query});
    const list=await getJson('/api/companies');companies=list.companies||companies;renderCompanyMenu('');
    if(result.asof)$('#asof').value=result.asof;
    toast('Starter Research Pack 已建立；财务 observations 待人工核验');
    await load(result.ticker);
  }catch(e){showError(e.message);$('#status').textContent='SEC Starter Pack 建立失败'}
}
function setNav(){
  $('[data-page]').forEach(b=>b.setAttribute('aria-current',b.dataset.page===page?'page':'false'));
}
function syncSlidingChrome(){
  requestAnimationFrame(()=>{
    const nav=document.querySelector('.v3-rail nav');
    const active=nav?.querySelector('button[aria-current="page"]');
    if(nav&&active){
      nav.style.setProperty('--nav-indicator-y',active.offsetTop+'px');
      nav.style.setProperty('--nav-indicator-h',active.offsetHeight+'px');
      nav.style.setProperty('--nav-indicator-o','1');
    }
    const sub=document.querySelector('.subnav');
    const selected=sub?.querySelector('button[aria-current="page"]');
    if(sub&&selected){
      sub.style.setProperty('--sub-indicator-x',selected.offsetLeft+'px');
      sub.style.setProperty('--sub-indicator-w',selected.offsetWidth+'px');
      sub.style.setProperty('--sub-indicator-o','1');
    }
  })
}
function stat(label,value,note){return '<div class="metric"><span>'+esc(label)+'</span><strong>'+value+'</strong><small>'+esc(note||'')+'</small></div>'}
function sectionHead(kicker,title,note){return '<div class="section-head"><div><span class="eyebrow">'+esc(kicker)+'</span><h2>'+esc(title)+'</h2></div><p>'+esc(note||'')+'</p></div>'}
function sourceById(id){return state.documents.find(d=>d.id===id)}
function obsById(id){return state.observations.find(o=>o.id===id)}
function semanticObsById(id){return state.semantic?.observations?.find(o=>o.id===id)}
function questionRecordById(id){return state.records.find(r=>r.kind==='question'&&r.id===id)}
function claimsForQuestion(id){return (state.semantic?.claims||[]).filter(c=>c.question_id===id).sort((a,b)=>String(a.created_at).localeCompare(String(b.created_at)))}
function latestClaimForQuestion(id){return claimsForQuestion(id).at(-1)||null}
function sourceIdsForFinding(f){return [...new Set((f.evidence_ids||[]).map(id=>obsById(id)?.source_id).filter(Boolean))]}
function sourceIdsForEvidence(ids){return [...new Set(ids.map(id=>obsById(id)?.source_id).filter(Boolean))]}
function provenanceLine(id){
  const p=semanticObsById(id)?.provenance||{},d=sourceById(p.primary_source_id||obsById(id)?.source_id);
  return [p.source_type||d?.source_type||'curated',p.disclosed_at||d?.disclosed_at,p.locator||d?.locator,p.source_tag].filter(Boolean).join(' · ')
}
function claimEvidenceRow(id,role,checked){
  const o=obsById(id);if(!o)return '';
  const p=semanticObsById(id)?.provenance||{};
  return '<label class="claim-evidence-row" data-evidence-id="'+esc(id)+'"><input type="checkbox" name="'+role+'" value="'+esc(id)+'" '+(checked?'checked':'')+'><span><b>'+esc(o.label||o.metric)+' · '+esc(o.period)+'</b><small>'+fmt(o.value)+' '+esc(o.currency||'')+' '+esc(o.unit||'')+' · '+esc(p.review_state||(!o.reviewed?'pending_review':'reviewed'))+'</small><em>'+esc(provenanceLine(id)||'provenance unavailable')+'</em></span></label>'
}
function sourceCoverage(){
  const c=state.v3.source_coverage;
  return '<div class="source-summary"><span class="eyebrow">SOURCE COVERAGE</span><strong>'+fmt(c.documents)+'</strong><p>份当前研究时点可用资料</p><p>'+fmt(c.observations)+' observations · '+fmt(c.pending_review)+' 待人工核验</p></div>'
}
function chartHost(id,label){return '<div class="chart-canvas" id="'+id+'" role="img" aria-label="'+esc(label)+'"></div>'}
function setAmbient(){
  // UI Freeze: one fixed blue theme across the entire V3 app.
  delete document.documentElement.dataset.ambient;
  delete document.documentElement.dataset.tone;
}
function smoothRender(direction='forward'){
  const content=$('#content');
  const reduced=window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches;
  if(!content||reduced){render();return Promise.resolve()}
  const token=++smoothRender.token;
  content.getAnimations().forEach(a=>a.cancel());
  content.style.pointerEvents='none';
  // The page stays spatially fixed. Only the selection pill/plate slides.
  // Content simply dissolves and resolves in place.
  const out=content.animate(
    [{opacity:1,filter:'blur(0px)'},{opacity:.14,filter:'blur(1px)'}],
    {duration:105,easing:'cubic-bezier(.4,0,1,1)',fill:'forwards'}
  );
  return out.finished.catch(()=>{}).then(()=>{
    if(token!==smoothRender.token)return;
    render();
    content.getAnimations().forEach(a=>a.cancel());
    const incoming=content.animate(
      [{opacity:.14,filter:'blur(1.2px)'},{opacity:1,filter:'blur(0px)'}],
      {duration:360,easing:'cubic-bezier(.22,1,.36,1)',fill:'both'}
    );
    return incoming.finished.catch(()=>{}).then(()=>{
      if(token===smoothRender.token){
        content.style.pointerEvents='';
        content.style.opacity='';
        content.style.transform='';
        content.style.filter='';
      }
    })
  })
}
smoothRender.token=0;
function plannerView(){
  const cap=sourceCapabilities.ai||{};
  const status=cap.enabled?'<span class="ai-badge">OPTIONAL AI · '+esc(cap.model||'enabled')+'</span>':'<span class="ai-badge muted-badge">OFF BY DEFAULT</span>';
  if(!cap.enabled)return '<div class="planner-shell"><div class="planner-head"><div><span class="eyebrow">V3-10 · AI RESEARCH PLANNER</span><h3>让 AI 规划“下一步查什么”，不让它拥有事实。</h3></div>'+status+'</div><p>Planner 只读取 compact research snapshot，生成问题、待查证据和反证路径。它不能写 Observation、不能标记 verified、不能替你形成投资结论。</p><div class="planner-enable"><code>ATLAS_AI_BASE_URL / ATLAS_AI_API_KEY / ATLAS_AI_MODEL</code><span>然后使用 <b>--enable-ai</b> 启动。本功能完全可选。</span></div></div>';
  if(!plannerResult)return '<div class="planner-shell"><div class="planner-head"><div><span class="eyebrow">V3-10 · AI RESEARCH PLANNER</span><h3>Grounded planning, human-owned judgment.</h3></div>'+status+'</div><p>当前模型只会收到 findings、行业 driver、source metadata 和允许引用的 evidence/source IDs；默认不发送原始文档全文。</p><button class="primary-action" data-run-planner>生成研究计划</button></div>';
  return '<div class="planner-shell"><div class="planner-head"><div><span class="eyebrow">AI-SUGGESTED · NOT VERIFIED</span><h3>'+esc(plannerResult.summary||'Suggested research plan')+'</h3></div>'+status+'</div><div class="plan-grid">'+plannerResult.items.map((item,i)=>'<article class="plan-item"><span class="plan-index">0'+(i+1)+'</span><h4>'+esc(item.question)+'</h4><p>'+esc(item.why_now||'')+'</p><dl><dt>Evidence to check</dt><dd>'+esc((item.evidence_to_check||[]).join(' · ')||'Model did not specify')+'</dd><dt>Counter-evidence</dt><dd>'+esc((item.counter_evidence||[]).join(' · ')||'Model did not specify')+'</dd><dt>Next actions</dt><dd>'+esc((item.suggested_actions||[]).join(' · ')||'Open sources and test the question')+'</dd></dl>'+(item.reference_warning?'<small class="planner-warning">'+esc(item.reference_warning)+'</small>':'')+'<button class="text-action" data-plan-question="'+i+'">Add question →</button></article>').join('')+'</div><p class="planner-boundary">'+esc(plannerResult.boundary||'AI output is a research plan, not a fact or final judgment.')+'</p></div>'
}
function renderCharts(){
  requestAnimationFrame(()=>{
    if(!window.AtlasCharts||!state)return;
    const trajectory=$('#chart-trajectory');if(trajectory)window.AtlasCharts.trajectory(trajectory,state.v3.trajectory||[]);
    const wc=$('#chart-working-capital');if(wc)window.AtlasCharts.workingCapital(wc,state.v3.trajectory||[]);
    const bridge=$('#chart-profit-bridge');if(bridge)window.AtlasCharts.bridge(bridge,state.diagnostics.bridges||[]);
    const segment=$('#chart-segment-mix');if(segment)window.AtlasCharts.segmentMix(segment,state.v3.business_map?.segments||[]);
    const peer=$('#chart-peer');if(peer&&peerResult)window.AtlasCharts.peer(peer,peerResult.rows||[]);
    const scenario=$('#chart-scenario');if(scenario&&scenarioResult)window.AtlasCharts.scenario(scenario,scenarioResult.scenarios?.base?.rows||[]);
  });
}
function nextStep(){
  const questions=state.records.filter(r=>r.kind==='question');
  let text='先阅读 3–5 条高信号 finding，选择一个问题深入。', action='查看第一条 finding', target='first-finding';
  if(questions.length){text='你已经保存研究问题。下一步把支持证据、反证与可推翻条件组织成阶段性判断。';action='进入 Claim Workspace';target='report'}
  if(state.review_pending>0 && page==='evidence'){text='有 '+state.review_pending+' 条指标仍待人工核验。基础勾稽只用于发现数据问题。';action='查看待审核来源';target='pending'}
  const box=$('#nextStep');box.hidden=false;box.innerHTML='<div><b>NEXT STEP</b><br><span>'+esc(text)+'</span></div><button data-next="'+target+'">'+esc(action)+' →</button>';
}
function trajectorySvg(rows){
  const clean=rows.filter(r=>r.revenue!=null); if(!clean.length)return '<div class="empty">缺少可绘制的收入历史。</div>';
  const w=620,h=220,pad=36,max=Math.max(...clean.map(r=>r.revenue))*1.12||1;
  const barW=Math.min(74,(w-pad*2)/clean.length*.52),step=(w-pad*2)/clean.length;
  const margins=clean.map(r=>r.operating_margin).filter(v=>v!=null),mMax=Math.max(1,...margins.map(Math.abs))*1.25;
  let svg='<svg class="chart-svg" viewBox="0 0 '+w+' '+h+'" role="img" aria-label="收入柱状图与经营利润率折线图">';
  [0,.25,.5,.75,1].forEach(t=>{const y=h-pad-(h-pad*2)*t;svg+='<line class="chart-grid" x1="'+pad+'" x2="'+(w-pad)+'" y1="'+y+'" y2="'+y+'"/>'});
  const points=[];
  clean.forEach((r,i)=>{const x=pad+step*i+step/2,y=h-pad-r.revenue/max*(h-pad*2),height=h-pad-y;
    svg+='<rect class="chart-bar" x="'+(x-barW/2)+'" y="'+y+'" width="'+barW+'" height="'+height+'"><title>'+esc(r.period)+' revenue '+fmt(r.revenue)+'</title></rect>';
    svg+='<text class="chart-axis" text-anchor="middle" x="'+x+'" y="'+(h-12)+'">'+esc(r.period)+'</text>';
    if(r.operating_margin!=null){const ly=h-pad-(r.operating_margin/mMax)*(h-pad*2);points.push([x,ly,r.operating_margin])}
  });
  if(points.length){svg+='<path class="chart-line" d="'+points.map((p,i)=>(i?'L':'M')+p[0]+' '+p[1]).join(' ')+'"/>';points.forEach(p=>svg+='<circle class="chart-dot" cx="'+p[0]+'" cy="'+p[1]+'" r="4"><title>Operating margin '+fmt(p[2],1)+'%</title></circle>')}
  svg+='</svg><p style="font-size:10px;color:var(--muted)">柱：Revenue · 线：Operating margin。图表用于发现趋势，点击 Evidence 查看原始披露。</p>';
  return svg
}
function cashSvg(rows){
  const clean=rows.filter(r=>r.cfo!=null||r.inventory!=null||r.receivables!=null);if(!clean.length)return '<div class="empty">现金与营运资金数据不足。</div>';
  const keys=[['cfo','CFO'],['receivables','Receivables'],['inventory','Inventory']],max=Math.max(1,...clean.flatMap(r=>keys.map(k=>Math.abs(r[k[0]]||0))));
  let out='<div style="display:grid;gap:13px">';
  clean.forEach(r=>{out+='<div><b style="font-size:11px">'+esc(r.period)+'</b><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:5px">';
    keys.forEach(k=>{const v=r[k[0]];const width=v==null?0:Math.max(3,Math.abs(v)/max*100);out+='<div><span style="display:block;font-size:9px;color:var(--muted)">'+k[1]+'</span><div style="height:8px;background:#e7e2d7;margin:3px 0"><div style="height:100%;width:'+width+'%;background:'+(k[0]==='cfo'?'#355d4a':'#9a6655')+'"></div></div><small>'+fmt(v)+'</small></div>'});out+='</div></div>'});
  return out+'</div>'
}
function segments(){
  const seg=state.v3.business_map.segments||[],revenue=state.v3.trajectory.at(-1)?.revenue||Math.max(1,...seg.map(s=>s.value||0));
  if(!seg.length)return '<div class="empty">当前档案没有可验证的业务分部候选；不会用推测补齐。</div>';
  const numeric=seg.some(s=>s.value!=null);
  if(numeric)return '<div class="segment-list">'+seg.map(s=>{const pct=revenue?Math.max(0,(s.value||0)/revenue*100):0;return '<div class="segment-row"><div class="segment-name"><span>'+esc(s.name)+'</span><b>'+fmt(s.value)+' · '+fmt(pct,1)+'%</b></div><div class="segment-track"><div class="segment-fill" style="width:'+Math.min(100,pct)+'%"></div></div></div>'}).join('')+'</div>';
  return '<div class="source-list">'+seg.map(s=>'<div class="source-item"><div><h3>'+esc(s.name)+'</h3><p>'+esc(s.review_state||'pending_review')+' · '+esc(s.locator||'10-K business text')+'</p>'+(s.excerpt?'<p style="margin-top:5px;font-size:10px;color:var(--muted)">'+esc(s.excerpt)+'</p>':'')+'</div>'+(s.source?'<button data-source="'+esc(s.source)+'">Evidence</button>':'')+'</div>').join('')+'</div>'
}
function products(){
  const rows=state.v3.business_map.products||[];
  if(!rows.length)return '<div class="empty">没有从 10-K Item 1 明确列表中提取到 Product / Platform / Service 候选。</div>';
  return '<div class="source-list">'+rows.map(p=>'<div class="source-item"><div><h3>'+esc(p.name)+'</h3><p>'+esc(p.category||'Product candidate')+' · '+esc(p.review_state||'pending_review')+'</p>'+(p.excerpt?'<p style="margin-top:5px;font-size:10px;color:var(--muted)">'+esc(p.excerpt)+'</p>':'')+'</div>'+((p.source_ids||[])[0]?'<button data-source="'+esc(p.source_ids[0])+'">Evidence</button>':'')+'</div>').join('')+'</div>'
}
function companyMapView(){
  const map=state.v3.company_map||{},nodes=map.nodes||[],layers=map.layers||[];
  if(!nodes.length)return '<div class="empty">Company Map 尚未建立。</div>';
  const byId=new Map(nodes.map(n=>[n.id,n]));
  return '<div class="company-map">'+layers.map(layer=>{
    const rows=(layer.node_ids||[]).map(id=>byId.get(id)).filter(Boolean).slice(0,8);
    return '<section class="map-layer"><span class="eyebrow">'+esc(layer.label)+'</span><div class="map-stack">'+(rows.length?rows.map(n=>{
      const src=(n.source_ids||[])[0],status=n.status||'unknown',question=n.meta?.question;
      return '<article class="map-node map-'+esc(n.kind)+'"><div><b>'+esc(n.label)+'</b><small>'+esc(n.kind)+' · '+esc(status)+'</small>'+(question?'<p>'+esc(question)+'</p>':'')+'</div>'+(src?'<button data-source="'+esc(src)+'">Evidence</button>':'')+'</article>'
    }).join(''):'<div class="map-empty">No evidence-backed nodes yet</div>')+'</div></section>'
  }).join('<div class="map-arrow">→</div>')+'</div><p class="map-boundary">'+esc(map.boundary||'')+'</p>'
}
function industryDriverView(){
  const m=state.v3.industry_module||{};
  const drivers=m.drivers||[];
  return '<div class="industry-head"><div><span class="eyebrow">INDUSTRY DRIVER MODULE</span><h3>'+esc(m.label||'General company')+'</h3><p>'+esc(m.description||'')+'</p></div><div class="module-reason"><b>Selection</b><span>'+esc(m.selection_reason||'')+'</span></div></div>'+
    '<div class="driver-grid">'+drivers.map(d=>'<article class="driver-card"><div class="driver-top"><span class="signal">'+esc(d.category)+'</span><span class="driver-status">'+esc(d.evidence_status)+'</span></div><h4>'+esc(d.label)+'</h4><p>'+esc(d.question)+'</p><dl><dt>Financial links</dt><dd>'+esc((d.linked_metrics||[]).join(' · ')||'No canonical financial metric')+'</dd><dt>Operating KPIs</dt><dd>'+esc((d.operating_kpis||[]).join(' · ')||'Needs company evidence')+'</dd><dt>Comparability</dt><dd>'+esc(d.comparison)+'</dd></dl></article>').join('')+'</div>'+
    '<details class="integrity driver-notes"><summary>Comparability notes</summary><ul>'+((m.comparability||[]).map(x=>'<li>'+esc(x)+'</li>').join(''))+'</ul><p>'+esc(m.boundary||'')+'</p></details>'
}
function insightCard(f){
  const detail='<div class="insight-detail" id="detail-'+esc(f.id)+'" hidden><div><span class="eyebrow">WHY THIS MATTERS</span><p>'+esc(f.why)+'</p><p style="margin-top:8px;font-size:10px">Priority '+fmt(f.priority.total)+' = materiality '+fmt(f.priority.materiality)+' + divergence '+fmt(f.priority.divergence)+' + industry '+fmt(f.priority.industry_relevance)+' + evidence '+fmt(f.priority.evidence_quality)+' − gap '+fmt(f.priority.data_gap_penalty)+'</p></div><div><span class="eyebrow">POSSIBLE MECHANISMS</span><ul>'+f.possible_mechanisms.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul></div></div>';
  return '<article class="insight" data-severity="'+esc(f.severity)+'" data-finding="'+esc(f.id)+'"><div class="insight-top"><div><span class="eyebrow">'+esc(f.category)+'</span><h3>'+esc(f.title)+'</h3><p>'+esc(f.statement)+'</p></div><span class="signal">'+esc(f.severity)+' signal</span></div><div class="insight-actions"><button data-action="why" data-id="'+esc(f.id)+'">Why?</button><button data-action="evidence" data-id="'+esc(f.id)+'">Evidence</button><button data-action="compare" data-id="'+esc(f.id)+'">Compare</button><button data-action="research" data-id="'+esc(f.id)+'">Add to Research</button></div>'+detail+'</article>'
}
function renderResearch(){
  const v=state.v3,t=v.trajectory.at(-1)||{},r=state.diagnostics.ratios||{};
  const businessContext=
    '<details class="context-disclosure"><summary>展开 Company / Product Map 与行业研究模板</summary><div class="context-body">'+
      '<div>'+companyMapView()+'</div>'+
      '<div class="grid-2" style="margin-top:28px"><div class="paper">'+segments()+'</div><div class="paper"><span class="eyebrow">Industry module</span><h3 style="font-size:17px;font-weight:650;letter-spacing:-.02em;margin:6px 0 8px">'+esc(v.industry_module?.label||'General company')+'</h3><p style="font-size:10px;color:var(--muted);line-height:1.6;margin:0">'+esc(v.industry_module?.description||'')+'</p><span class="eyebrow" style="margin-top:18px">Known gaps</span><ul style="font-size:10px;color:var(--muted);line-height:1.65;padding-left:17px">'+(v.business_map.unknowns||[]).slice(0,4).map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul></div></div>'+
    '</div></details>';
  const aiContext='<details class="context-disclosure"><summary>打开 Optional AI Research Planner</summary><div class="context-body">'+plannerView()+'</div></details>';

  $('#content').innerHTML=
  '<div class="page-intro"><div><span class="eyebrow">60-second company view</span><h1>'+esc(state.company.name)+'</h1><p>'+esc(v.summary)+' 当前研究视图只使用截至 '+esc(state.asof)+' 已披露的数据；系统先提出问题，再由研究者形成判断。</p></div>'+sourceCoverage()+'</div>'+
  '<div class="metrics-row">'+stat('Revenue',fmt(t.revenue),t.period||'')+stat('Revenue growth',r.revenue_growth==null?'—':fmt(r.revenue_growth,1)+'%','YoY')+stat('Operating margin',r.op_margin==null?'—':fmt(r.op_margin,1)+'%','GAAP')+stat('Cash conversion',r.cash_conversion==null?'—':fmt(r.cash_conversion,1)+'%','CFO / Net income')+'</div>'+
  '<section class="section" id="findings">'+sectionHead('What changed','值得研究的变化','先看少量高信号关系。Deterministic diagnostics 只负责提出 investigation trigger，不替研究者形成结论。')+'<div class="insight-list">'+(v.findings.length?v.findings.map(insightCard).join(''):'<div class="empty">当前资料没有触发预设高信号规则。你仍可从业务、竞争或自定义问题开始。</div>')+'</div></section>'+
  '<section class="section">'+sectionHead('Financial trajectory','先看趋势，再决定往哪里钻','同一屏只回答一个分析问题；图表用于 inspection，不承担评分或结论。')+'<div class="grid-2"><div class="paper chart-card"><div class="chart-title"><h3>Revenue × Operating Margin</h3><span>Trend</span></div>'+chartHost('chart-trajectory','Revenue and operating margin trend')+'</div><div class="paper chart-card"><div class="chart-title"><h3>Cash & Working Capital</h3><span>Relationship</span></div>'+chartHost('chart-working-capital','CFO receivables and inventory trend')+'</div></div></section>'+
  '<section class="section">'+sectionHead('Questions worth investigating','从问题进入，而不是从模型参数进入','选择一个问题后，再去 Evidence / Compare / Scenario 建立证据链。')+'<div class="question-list">'+v.questions.map((q,i)=>'<div class="question"><b>'+esc(q)+'</b><button data-question="'+i+'">开始研究 →</button></div>').join('')+'</div></section>'+
  '<section class="section">'+sectionHead('Business context','深度信息按需展开','Company / Segment / Product / Driver 仍然保留，但不再和核心研究路径争夺首屏注意力。')+businessContext+'</section>'+
  '<section class="section">'+sectionHead('Optional intelligence','AI 只规划研究，不拥有事实','默认关闭。只有在需要扩展研究问题或查证路径时再进入。')+aiContext+'</section>';
}
function renderEvidence(){
  const v=state.v3,c=v.source_coverage,integ=v.data_integrity;
  $('#content').innerHTML='<div class="page-intro"><div><span class="eyebrow">EVIDENCE</span><h1>事实从哪里来？</h1><p>Evidence 是全局能力，不是最后一步。每个数字都应能回到 document、period、scope、basis 与 review state。</p></div>'+sourceCoverage()+'</div>'+
  '<div class="metrics-row">'+stat('Documents',fmt(c.documents),'current as-of')+stat('Observations',fmt(c.observations),'structured facts')+stat('Reviewed',fmt(c.reviewed),'human confirmed')+stat('Pending',fmt(c.pending_review),'needs review')+'</div>'+
  '<section class="section">'+sectionHead('SOURCE REGISTRY','当前研究时点可用资料','点击查看原始 URL、披露时间和定位信息。')+'<div class="source-list">'+state.documents.map(d=>'<div class="source-item"><div><h3>'+esc(d.title)+'</h3><p>'+esc(d.disclosed_at)+' · '+esc(d.locator||'未录入定位')+'</p></div><button data-source="'+esc(d.id)+'">查看来源</button></div>').join('')+'</div></section>'+
  '<section class="section">'+sectionHead('DATA INTEGRITY','后台完整性检查','这层用于发现提取/映射/单位/期间/口径错误，不代表公司质量。')+'<details class="integrity"><summary>'+esc(integ.status.toUpperCase())+' · pass '+fmt(integ.coverage.pass)+' / fail '+fmt(integ.coverage.fail)+' / missing '+fmt(integ.coverage.missing)+'</summary><p>'+esc(integ.definition)+'</p><div class="source-list">'+state.relations.checks.slice(-12).map(c=>'<div class="source-item"><div><h3>'+esc(c.formula)+'</h3><p>'+esc(c.period)+' · '+esc(c.verification)+' · reviewed '+(c.reviewed?'yes':'no')+'</p></div><span class="signal">'+esc(c.status)+'</span></div>').join('')+'</div></details></section>';
}
function analysisSubnav(){
  return '<div class="subnav"><button data-tab="financials" aria-current="'+(analysisTab==='financials'?'page':'false')+'">Financials</button><button data-tab="business" aria-current="'+(analysisTab==='business'?'page':'false')+'">Business</button><button data-tab="peers" aria-current="'+(analysisTab==='peers'?'page':'false')+'">Peers</button><button data-tab="scenario" aria-current="'+(analysisTab==='scenario'?'page':'false')+'">Scenario</button></div>'
}
function bridgeViz(){
  const b=state.diagnostics.bridges||[];if(!b.length)return '<div class="empty">缺少足够的连续年度数据，无法构建经营利润 bridge。</div>';
  const max=Math.max(1,...b.map(x=>Math.abs(x.value||0)));
  return '<div class="bridge">'+b.map(x=>'<div class="bridge-step '+(x.value<0?'neg':'')+'"><div class="bar" style="height:'+Math.max(8,Math.abs(x.value)/max*130)+'px"></div><b>'+(x.value>0?'+':'')+fmt(x.value)+'</b><small>'+esc(x.name)+'</small></div>').join('')+'</div>'
}
function renderFinancials(){
  return sectionHead('FINANCIAL DIAGNOSTICS','关系优先，不是 ratio 展览','Growth → Profitability → Cash → Working Capital → Capital intensity。')+
  '<div class="grid-2"><div class="paper"><div class="chart-title"><h3>Operating Profit Bridge</h3><span>Waterfall logic</span></div>'+chartHost('chart-profit-bridge','Operating profit bridge accounting decomposition')+'<p style="font-size:10px;color:var(--muted)">这是会计分解，不等于商业因果。</p></div><div class="paper"><div class="chart-title"><h3>Prioritized findings</h3><span>'+fmt(state.v3.findings.length)+' signals</span></div><div class="insight-list">'+state.v3.findings.slice(0,3).map(insightCard).join('')+'</div></div></div>'
}
function renderBusiness(){
  const b=state.v3.business_map||{},source=(b.business_source_ids||[])[0];
  const filing='<div class="paper"><span class="eyebrow">10-K · ITEM 1 BUSINESS</span><h3 style="margin-top:8px">What the filing says</h3><p style="margin-top:8px;white-space:pre-line">'+esc(b.business_summary||'当前研究时点没有可用的 Item 1 Business 文本。')+'</p><p style="margin-top:8px;font-size:10px;color:var(--muted)">'+esc(b.business_review_state||'unavailable')+' · '+esc(b.business_extraction_method||'no extraction')+'</p>'+(source?'<button style="margin-top:10px" data-source="'+esc(source)+'">打开 10-K 来源</button>':'')+'</div>';
  const numericSegments=(b.segments||[]).some(x=>x.value!=null);
  const seg='<div class="paper"><span class="eyebrow">SEGMENT CANDIDATES</span><h3 style="margin-top:8px">How the company says it is organized</h3>'+(numericSegments?chartHost('chart-segment-mix','Numeric segment mix'):'')+'<div style="margin-top:12px">'+segments()+'</div></div>';
  const prod='<div class="paper"><span class="eyebrow">PRODUCT / PLATFORM CANDIDATES</span><h3 style="margin-top:8px">What it sells or offers</h3><div style="margin-top:12px">'+products()+'</div><p style="margin-top:10px;font-size:10px;color:var(--muted)">候选必须保留 source / excerpt / review state；未映射到 Segment 时不会自动猜测归属。</p></div>';
  return sectionHead('V3-7 · COMPANY / PRODUCT MAP','从“公司介绍”升级为可追溯的经营结构图','Company → Segment → Product → Operating Driver → Financial Outcome；V3-8 行业模板只提出应该研究什么，不伪装成公司披露。')+
  '<div class="paper">'+companyMapView()+'</div>'+
  '<section class="section">'+sectionHead('V3-8','Industry Driver Module','根据 mode / SIC / industry keywords 透明选择行业模块；每个 driver 明确 KPI、财务链接和可比性边界。')+'<div class="paper">'+industryDriverView()+'</div></section>'+
  '<div class="grid-2">'+filing+seg+'</div><div class="grid-2" style="margin-top:16px">'+prod+'<div class="paper"><span class="eyebrow">RESEARCH BOUNDARY</span><h3 style="margin-top:8px">Template ≠ company fact</h3><p style="font-size:11px;color:var(--muted);line-height:1.65">行业 driver 用于告诉研究者下一步应该找什么证据。只有带来源、locator 和 review state 的 Business / Segment / Product 才进入 evidence-backed 公司地图。</p></div></div>'
}
function cellValue(row,key){return row?.metric_checks?.[key]?.value}
function renderPeerResult(){
  if(!peerResult)return '<div class="empty"><h2>选择一个 finding，再比较。</h2><p>Compare 会先检查 period / basis / scope / industry，再展示差异。</p><button class="quiet" data-load-peers>加载默认同行</button></div>';
  const rows=peerResult.rows||[],metrics=[['revenue_growth','Revenue growth'],['gross_margin','Gross margin'],['op_margin','Operating margin'],['cash_conversion','Cash conversion']];
  const anchor=rows[0],others=rows.slice(1);
  return '<div class="gate"><span class="eyebrow">COMPARABILITY GATE</span><h3>'+esc(anchor?.ticker||'Anchor')+' vs '+esc(others.map(x=>x.ticker).join(' / '))+'</h3><ul>'+others.flatMap(r=>(r.reasons||[]).map(x=>'<li>'+esc(r.ticker)+': '+esc(x)+'</li>')).join('')+'</ul><p style="font-size:11px;color:var(--muted)">无阻断理由也不等于业务完全相同；逐指标仍使用 metric_checks。</p></div>'+chartHost('chart-peer','Qualified peer metric comparison')+
  '<table class="heatmap"><thead><tr><th>Metric</th>'+rows.map(r=>'<th>'+esc(r.ticker)+'</th>').join('')+'</tr></thead><tbody>'+metrics.map(m=>'<tr><td>'+m[1]+'</td>'+rows.map(r=>{const c=r.metric_checks?.[m[0]],v=c?.value;return '<td class="heat" style="--heat:'+(v==null?0.04:0.11)+'" title="'+esc((c?.reasons||c?.notes||[]).join(' · '))+'">'+(v==null?'blocked':fmt(v,1)+'%')+'<br><small>'+esc(c?.status||'')+'</small></td>'}).join('')+'</tr>').join('')+'</tbody></table>'
}
function renderPeers(){return sectionHead('COMPARATIVE REASONING','先判断能不能比，再解释为什么不同','Peer Comparison 不是排名表；blocked / qualified 状态必须先于图表。')+renderPeerResult()}
function selectedQuestion(){
  const selected=questionRecordById(selectedQuestionId);
  const qs=state.records.filter(r=>r.kind==='question');return selected?.content?.question||qs[0]?.content?.question||selectedFinding?.question||null
}
function renderScenario(){
  const q=selectedQuestion();
  if(!q)return '<div class="empty"><h2>Scenario 还没有研究问题。</h2><p>V3 不允许用户一进入产品就随意调参数。先从 finding 保存一个问题，再测试假设。</p><button class="quiet" data-go-research>返回 Research</button></div>';
  let body='<div class="gate"><span class="eyebrow">QUESTION-FIRST SCENARIO</span><h3>'+esc(q)+'</h3><p style="font-size:11px;color:var(--muted)">用当前基础假设做一次 deterministic model run。它回答“如果这些假设成立会怎样”，不是概率预测。</p><button class="quiet" data-run-scenario>运行当前基础情景</button></div>';
  if(scenarioResult){
    const rows=scenarioResult.scenarios?.base?.rows||[];
    body+='<div class="paper"><div class="chart-title"><h3>Base scenario</h3><span>Calculated</span></div>'+chartHost('chart-scenario','Calculated base scenario trajectory')+'<table class="heatmap"><thead><tr><th>Year</th><th>Revenue</th><th>EBIT</th><th>FCFF</th></tr></thead><tbody>'+rows.map(r=>'<tr><td>'+esc(r.year)+'</td><td>'+fmt(r.revenue)+'</td><td>'+fmt(r.ebit)+'</td><td>'+fmt(r.fcff)+'</td></tr>').join('')+'</tbody></table><p style="font-size:10px;color:var(--muted)">高级参数编辑继续保留在 V2；V3 P0 先验证 question → scenario 的进入逻辑。</p></div>'
  }
  return body
}
function renderAnalysis(){
  $('#content').innerHTML='<div class="page-intro"><div><span class="eyebrow">ANALYSIS</span><h1>发生了什么，为什么？</h1><p>这里把财务关系、业务机制、同行和情景放在一个研究上下文里。工具按问题触发，而不是全部摆在一级导航。</p></div>'+sourceCoverage()+'</div>'+analysisSubnav()+'<section class="section">'+({financials:renderFinancials,business:renderBusiness,peers:renderPeers,scenario:renderScenario}[analysisTab])()+'</section>';
}
function renderClaimWorkspace(question){
  if(!question)return '<div class="empty"><h2>先建立一个 Research Question。</h2><p>Claim 必须挂在明确的问题上；没有 Question 时不创建孤立结论。</p></div>';
  const qid=question.id,q=question.content||{},claims=claimsForQuestion(qid),latest=claims.at(-1)||null;
  const support=new Set(latest?.supporting_evidence_ids||q.evidence_ids||[]);
  const counter=new Set(latest?.counter_evidence_ids||[]);
  const observations=[...state.observations].sort((a,b)=>String(b.period).localeCompare(String(a.period))||String(a.metric).localeCompare(String(b.metric))).slice(0,40);
  const evidenceRows=observations.map(o=>'<div class="claim-evidence-pair">'+claimEvidenceRow(o.id,'supporting',support.has(o.id))+claimEvidenceRow(o.id,'counter',counter.has(o.id))+'</div>').join('');
  const current=latest?'<article class="current-claim"><div><span class="eyebrow">CURRENT CLAIM · '+esc(latest.status)+'</span><h3>'+esc(latest.conclusion)+'</h3><p>'+esc(latest.alternative||'No alternative explanation recorded.')+'</p></div><dl><dt>Support</dt><dd>'+fmt(latest.supporting_evidence_ids.length)+' observations</dd><dt>Counter</dt><dd>'+fmt(latest.counter_evidence_ids.length)+' observations</dd><dt>Falsification trigger</dt><dd>'+esc(latest.change_trigger||'—')+'</dd></dl></article>':'<div class="claim-empty-state"><span class="eyebrow">NO CLAIM YET</span><h3>Question 已存在，但研究者尚未形成阶段性判断。</h3><p>先选 evidence，再写 claim；系统不会把 finding 自动升级为 conclusion。</p></div>';
  return '<div class="claim-workspace" data-claim-workspace="'+esc(qid)+'">'+
    '<header class="claim-workspace-head"><div><span class="eyebrow">CLAIM WORKSPACE</span><h2>'+esc(q.question)+'</h2><p>'+esc(q.reason||'')+'</p></div><span class="signal">'+esc(q.status||'open')+'</span></header>'+
    current+
    '<form id="claimForm" class="claim-form" data-question-id="'+esc(qid)+'">'+
      '<input type="hidden" name="parent_id" value="'+esc(latest?.id||'')+'">'+
      '<div class="claim-grid"><label><span>Current claim</span><textarea name="conclusion" rows="4" required placeholder="What do you currently believe, given the evidence?">'+esc(latest?.conclusion||'')+'</textarea></label>'+
      '<label><span>Alternative explanation</span><textarea name="alternative" rows="4" required placeholder="What else could explain the same evidence?">'+esc(latest?.alternative||'')+'</textarea></label></div>'+
      '<div class="claim-grid"><label><span>What would change my mind?</span><textarea name="next_evidence" rows="3" required placeholder="A concrete falsification trigger or next evidence.">'+esc(latest?.change_trigger||'')+'</textarea></label>'+
      '<label><span>Revision reason</span><textarea name="change_reason" rows="3" required placeholder="'+(latest?'What changed since the previous claim?':'Why is this the initial claim?')+'"></textarea></label></div>'+
      '<div class="claim-status-row"><label><span>Status</span><select name="status">'+['open','supported','challenged','withdrawn'].map(s=>'<option value="'+s+'" '+((latest?.status||'open')===s?'selected':'')+'>'+s+'</option>').join('')+'</select></label><p>Evidence can support or challenge a claim. The same observation cannot be both.</p></div>'+
      '<div class="evidence-matrix-head"><div><span class="eyebrow">EVIDENCE MATRIX</span><h3>Support vs counter-evidence</h3></div><div class="matrix-legend"><span>Left = supporting</span><span>Right = counter</span></div></div>'+
      '<div class="claim-evidence-list">'+evidenceRows+'</div>'+
      '<div class="claim-submit"><p>'+(latest?'Saving creates a new immutable revision; the previous claim remains in history.':'Saving creates the first researcher-authored Claim for this Question.')+'</p><button class="primary-action" type="submit">Save claim revision →</button></div>'+
    '</form>'+
    (claims.length?'<div class="claim-history"><span class="eyebrow">CLAIM HISTORY</span>'+claims.slice().reverse().map((x,i)=>'<article><b>'+esc(x.status)+' · '+esc(x.created_at?.slice(0,10)||'')+'</b><p>'+esc(x.conclusion)+'</p><small>'+(i===0?'current':'prior revision')+'</small></article>').join('')+'</div>':'')+
  '</div>'
}
function renderReport(){
  const records=state.records.filter(r=>['question','research','memo','driver','comparison'].includes(r.kind));
  const questions=state.records.filter(r=>r.kind==='question');
  if(questions.length&&!questions.some(q=>q.id===selectedQuestionId))selectedQuestionId=questions[0].id;
  const selected=questionRecordById(selectedQuestionId);
  $('#content').innerHTML='<div class="page-intro"><div><span class="eyebrow">RESEARCH MEMORY</span><h1>我现在怎么看？</h1><p>Report 现在以 Claim Workspace 为核心：Question → support / counter-evidence → Claim → falsification trigger → immutable Revision。</p></div>'+sourceCoverage()+'</div>'+
  '<section class="section">'+sectionHead('CURRENT RESEARCH THREADS','选择一个问题进入 Claim Workspace','Question 可以先保存；Claim 必须显式引用证据与反证。')+'<div class="question-list">'+questions.map(r=>'<div class="question '+(r.id===selectedQuestionId?'is-selected':'')+'"><div><b>'+esc(r.content.question)+'</b><small>'+esc(r.content.reason||'')+'</small></div><span class="signal">'+esc(r.content.status||'open')+'</span><button data-open-claim="'+esc(r.id)+'">'+(r.id===selectedQuestionId?'Editing':'Open workspace')+' →</button></div>').join('')+'</div>'+(questions.length?'':'<div class="empty">还没有保存研究问题。回到 Research，从一条 finding 开始。</div>')+'</section>'+
  '<section class="section">'+renderClaimWorkspace(selected)+'</section>'+
  '<section class="section">'+sectionHead('REVISION TIMELINE','研究判断如何变化','旧版本不覆盖；stale 表示新证据到来后需要复核。')+'<div class="timeline">'+(records.length?records.map(r=>'<article class="revision"><span class="eyebrow">'+esc(r.kind)+' · '+esc(r.created_at?.slice(0,10)||'')+'</span><h3>'+esc(r.content.question||r.content.title||r.content.reason||'保存的研究记录')+'</h3><p>'+esc(r.content.conclusion||r.content.change_reason||r.content.reason||'')+'</p><span class="signal">'+(r.stale?'review needed':'saved')+'</span></article>').join(''):'<div class="empty">暂无版本记录。</div>')+'</div></section>';
}
function render(){
  if(!state)return;setAmbient();setNav();nextStep();
  if(page==='research')renderResearch();
  if(page==='evidence')renderEvidence();
  if(page==='analysis')renderAnalysis();
  if(page==='report')renderReport();
  renderCharts();
  syncSlidingChrome();
}
function openEvidence(f){
  const ids=f?.evidence_ids||[];const obs=ids.map(obsById).filter(Boolean),sources=[...new Set(obs.map(o=>o.source_id))].map(sourceById).filter(Boolean);
  $('#drawerTitle').textContent=f?.title||'Evidence';
  $('#drawerBody').innerHTML=(obs.length?obs.map(o=>{const d=sourceById(o.source_id),p=semanticObsById(o.id)?.provenance||{};return '<article class="evidence-card"><span class="eyebrow">'+esc(o.kind)+' · '+(o.reviewed?'REVIEWED':'PENDING REVIEW')+'</span><h3>'+esc(o.label||o.metric)+'</h3><dl><dt>Value</dt><dd>'+fmt(o.value)+' '+esc(o.currency||'')+' '+esc(o.unit||'')+'</dd><dt>Period</dt><dd>'+esc(o.period)+' · '+esc(o.period_type||'')+'</dd><dt>Scope</dt><dd>'+esc(o.basis||'')+' · '+esc(o.scope||'')+'</dd><dt>Source type</dt><dd>'+esc(p.source_type||d?.source_type||'curated')+'</dd><dt>Disclosed</dt><dd>'+esc(p.disclosed_at||o.disclosed_at||d?.disclosed_at||'')+'</dd><dt>Source</dt><dd>'+esc(d?.title||o.source_id)+'</dd><dt>Locator</dt><dd>'+esc(p.locator||d?.locator||'—')+'</dd><dt>Source tag</dt><dd>'+esc(p.source_tag||o.source_tag||'—')+'</dd><dt>Extraction</dt><dd>'+esc(p.extraction_method||p.extraction_review_id||'direct / curated')+'</dd></dl>'+(p.quote?'<blockquote class="provenance-quote">'+esc(p.quote)+'</blockquote>':'')+(d?.url?'<a href="'+esc(d.url)+'" target="_blank" rel="noopener noreferrer">打开官方原文 ↗</a>':'')+'</article>'}).join(''):'<div class="empty">这条 finding 暂无结构化 evidence ID。</div>')+(sources.length?'<p style="font-size:10px;color:var(--muted)">Provenance envelope 来自 Semantic Contract；缺失字段保持缺失，不自动补写。</p>':'');
  $('#evidenceDrawer').showModal();
}
function openSource(id){
  const d=sourceById(id);if(!d)return toast('当前研究时点没有这份来源');
  $('#drawerTitle').textContent=d.title;
  $('#drawerBody').innerHTML='<article class="evidence-card"><dl><dt>Disclosed</dt><dd>'+esc(d.disclosed_at)+'</dd><dt>Locator</dt><dd>'+esc(d.locator||'—')+'</dd><dt>Note</dt><dd>'+esc(d.note||'—')+'</dd></dl><a href="'+esc(d.url)+'" target="_blank" rel="noopener noreferrer">打开原始来源 ↗</a></article>';
  $('#evidenceDrawer').showModal();
}
async function saveQuestion(f){
  const source_ids=sourceIdsForFinding(f);if(!source_ids.length)return toast('这条问题还没有可保存的来源链');
  try{const r=await post('question-save',{question:f.question,reason:f.statement,finding_id:f.id,evidence_ids:f.evidence_ids,source_ids,status:'open'});selectedQuestionId=r.id;toast('研究问题已保存');await load()}catch(e){showError(e.message)}
}
async function loadPeers(options={}){
  const candidates=companies.filter(c=>c.ticker!==state.company.ticker&&c.industry===state.company.industry).slice(0,2);
  if(!candidates.length)return toast('当前 fixture 没有同业公司可比较');
  try{
    peerResult=await post('compare',{peers:candidates.map(c=>c.ticker),nearby:true});
    if(options.animate)smoothRender(options.direction||'forward');else render();
  }catch(e){showError(e.message)}
}
async function runScenario(){
  if(!state.defaults)return toast('当前公司/数据不足，无法使用一般企业模型');
  try{scenarioResult=await post('calculate',{params:state.defaults});render()}catch(e){showError(e.message)}
}
async function startQuestion(q){
  const source_ids=state.documents.slice(0,Math.min(2,state.documents.length)).map(d=>d.id);
  if(!source_ids.length)return toast('没有可关联的来源');
  try{const r=await post('question-save',{question:q,reason:'用户从 60-second Company View 选择该问题。',finding_id:null,evidence_ids:[],source_ids,status:'open'});selectedQuestionId=r.id;toast('研究问题已保存');await load()}catch(e){showError(e.message)}
}
async function runPlanner(){
  if(!sourceCapabilities.ai?.enabled)return toast('AI Research Planner 当前关闭');
  plannerResult=null;toast('正在生成 grounded research plan…');
  try{plannerResult=await post('ai-plan',{focus:selectedQuestion()||state.v3.questions?.[0]||''});render()}catch(e){showError(e.message)}
}
async function savePlannerQuestion(index){
  const item=plannerResult?.items?.[index];if(!item)return;
  if(!(item.source_ids||[]).length)return toast('该 AI 建议没有可验证 source ID，暂不保存');
  try{
    const r=await post('question-save',{question:item.question,reason:'AI planner suggestion selected by user. '+(item.why_now||''),finding_id:null,evidence_ids:item.evidence_ids||[],source_ids:item.source_ids,status:'open'});
    selectedQuestionId=r.id;toast('AI 建议已作为 Research Question 保存；仍需人工判断');await load();
  }catch(e){showError(e.message)}
}
async function load(ticker){
  const current=++serial;clearError();$('#status').textContent='正在建立 point-in-time research view…';
  try{
    const q=new URLSearchParams({company:ticker||context().company,asof:$('#asof').value});
    const next=await getJson('/api/state?'+q);
    if(current!==serial)return;state=next;peerResult=null;scenarioResult=null;plannerResult=null;setAmbient();
    $('#companySearch').value=state.company.ticker;$('#companyTicker').textContent=state.company.ticker;$('#companyName').textContent=state.company.name;$('#companySubtitle').textContent=state.company.subtitle||state.company.industry;$('#storageState').textContent=state.storage;
    $('#status').textContent='Ready · '+state.v3.source_coverage.documents+' sources · '+state.v3.source_coverage.pending_review+' pending review · as of '+state.asof;render()
  }catch(e){showError(e.message);$('#status').textContent='Research view unavailable'}
}
async function init(){
  try{
    const session=await getJson('/api/session');token=session.token;companies=session.companies||[];sourceCapabilities=session.sources||{};
    renderCompanyMenu('');
    $('#companyHint').textContent=sourceCapabilities.sec?.enabled?'可输入已有公司，或输入新的美国上市公司 ticker，由 SEC EDGAR 建立 Starter Research Pack。':'当前使用本地资料；设置 ATLAS_SEC_USER_AGENT 并以 --enable-sec 启动后，可直接从 SEC 建立 Starter Research Pack。';
    await load(companies.find(c=>c.ticker==='NVDA')?.ticker||companies[0]?.ticker||'NVDA')
  }catch(e){showError(e.message)}
}
document.addEventListener('click',async e=>{
  const nav=e.target.closest('[data-page]');if(nav){
    const next=nav.dataset.page,dir=directionBetween(PAGE_ORDER,page,next);page=next;smoothRender(dir);return
  }
  const tab=e.target.closest('[data-tab]');if(tab){
    const next=tab.dataset.tab,dir=directionBetween(TAB_ORDER,analysisTab,next);analysisTab=next;setAmbient();
    if(analysisTab==='peers'&&!peerResult)await loadPeers({animate:true,direction:dir});else smoothRender(dir);return
  }
  const a=e.target.closest('[data-action]');if(a){const f=state.v3.findings.find(x=>x.id===a.dataset.id);selectedFinding=f;
    if(a.dataset.action==='why'){const d=$('#detail-'+CSS.escape(f.id));d.hidden=!d.hidden}
    if(a.dataset.action==='evidence')openEvidence(f);
    if(a.dataset.action==='compare'){
      const dir=page==='analysis'?directionBetween(TAB_ORDER,analysisTab,'peers'):directionBetween(PAGE_ORDER,page,'analysis');
      page='analysis';analysisTab='peers';await loadPeers({animate:true,direction:dir})
    }
    if(a.dataset.action==='research')await saveQuestion(f);return}
  const q=e.target.closest('[data-question]');if(q){await startQuestion(state.v3.questions[Number(q.dataset.question)]);return}
  const openClaim=e.target.closest('[data-open-claim]');if(openClaim){selectedQuestionId=openClaim.dataset.openClaim;render();return}
  const s=e.target.closest('[data-source]');if(s){openSource(s.dataset.source);return}
  if(e.target.closest('[data-load-peers]')){await loadPeers();return}
  if(e.target.closest('[data-run-scenario]')){await runScenario();return}
  if(e.target.closest('[data-go-research]')){const dir=directionBetween(PAGE_ORDER,page,'research');page='research';smoothRender(dir);return}
  if(e.target.closest('[data-run-planner]')){await runPlanner();return}
  const pq=e.target.closest('[data-plan-question]');if(pq){await savePlannerQuestion(Number(pq.dataset.planQuestion));return}
  const n=e.target.closest('[data-next]');if(n){
    if(n.dataset.next==='analysis'){const dir=directionBetween(PAGE_ORDER,page,'analysis');page='analysis';analysisTab='financials';smoothRender(dir)}
    else if(n.dataset.next==='report'){const dir=directionBetween(PAGE_ORDER,page,'report');page='report';smoothRender(dir)}
    else if(n.dataset.next==='first-finding'){$('#findings')?.scrollIntoView({behavior:'smooth'})}
    else if(n.dataset.next==='pending'){document.querySelector('.source-list')?.scrollIntoView({behavior:'smooth'})}
    return
  }
});
document.addEventListener('submit',async e=>{
  if(e.target.id!=='claimForm')return;
  e.preventDefault();clearError();
  const form=e.target,data=new FormData(form),question=questionRecordById(form.dataset.questionId);
  if(!question)return showError('Research Question 不存在或已不在当前 as-of。');
  const supporting=data.getAll('supporting'),counter=data.getAll('counter');
  const overlap=supporting.filter(x=>counter.includes(x));
  if(overlap.length)return showError('同一 observation 不能同时作为 supporting 与 counter-evidence。');
  if(!supporting.length&&!counter.length)return showError('Claim 至少需要一条明确 evidence。');
  const evidence=[...new Set([...supporting,...counter])],source_ids=sourceIdsForEvidence(evidence);
  if(!source_ids.length)return showError('所选 evidence 没有可解析的来源链。');
  const payload={
    question:question.content.question,question_id:question.id,
    conclusion:String(data.get('conclusion')||'').trim(),
    alternative:String(data.get('alternative')||'').trim(),
    next_evidence:String(data.get('next_evidence')||'').trim(),
    change_reason:String(data.get('change_reason')||'').trim(),
    status:String(data.get('status')||'open'),
    supporting_evidence_ids:supporting,counter_evidence_ids:counter,source_ids
  };
  const parent=String(data.get('parent_id')||'').trim();if(parent)payload.parent_id=parent;
  try{await post('research-save',payload);toast(parent?'Claim revision saved':'Initial claim saved');await load()}catch(err){showError(err.message)}
});
$('#companyToggle').addEventListener('click',()=>setCompanyMenu($('#companyMenu').hidden));
$('#companySearch').addEventListener('focus',()=>setCompanyMenu(true));
$('#companySearch').addEventListener('input',()=>{renderCompanyMenu($('#companySearch').value);setCompanyMenu(true)});
$('#companySearch').addEventListener('keydown',async e=>{
  if(e.key==='Enter'){e.preventDefault();await openCompanyQuery()}
  if(e.key==='Escape'){setCompanyMenu(false);$('#companySearch').blur()}
  if(e.key==='ArrowDown'){
    e.preventDefault();setCompanyMenu(true);
    $('#companyMenu .combo-option:not([aria-disabled="true"])')?.focus();
  }
});
$('#companyMenu').addEventListener('click',async e=>{
  const option=e.target.closest('[data-company-option]');if(!option)return;
  $('#companySearch').value=option.dataset.companyOption;setCompanyMenu(false);await load(option.dataset.companyOption);
});
$('#companyMenu').addEventListener('keydown',async e=>{
  const options=[...$('#companyMenu').querySelectorAll('[data-company-option]')],current=options.indexOf(document.activeElement);
  if(e.key==='ArrowDown'){e.preventDefault();options[Math.min(options.length-1,current+1)]?.focus()}
  if(e.key==='ArrowUp'){e.preventDefault();(current<=0?$('#companySearch'):options[current-1])?.focus()}
  if(e.key==='Enter'&&document.activeElement?.dataset?.companyOption){e.preventDefault();const ticker=document.activeElement.dataset.companyOption;$('#companySearch').value=ticker;setCompanyMenu(false);await load(ticker)}
  if(e.key==='Escape'){setCompanyMenu(false);$('#companySearch').focus()}
});
document.addEventListener('pointerdown',e=>{if(!e.target.closest('#companyCombobox'))setCompanyMenu(false)});
$('#asof').addEventListener('change',()=>load(context().company));
$('#closeDrawer').addEventListener('click',()=>$('#evidenceDrawer').close());
$('#evidenceDrawer').addEventListener('click',e=>{
  const d=$('#evidenceDrawer'),r=d.getBoundingClientRect();
  if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();
});
$('#exportButton').addEventListener('click',async()=>{try{const r=await post('export-file',{});toast('研究包已保存：'+r.filename)}catch(e){showError(e.message)}});
window.addEventListener('resize',()=>window.AtlasCharts?.resizeAll());
init();
