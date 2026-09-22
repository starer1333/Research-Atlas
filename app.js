'use strict';
const $=s=>document.querySelector(s), esc=s=>String(s??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>n==null?'—':Number(n).toLocaleString('en-US',{maximumFractionDigits:2});
let data, ticker='NVDA', view='financial';
const names={opex_growth:'费用增长 %',tax_rate:'现金税率 %',da_ratio:'折旧 / 收入 %',capex_ratio:'资本开支 / 收入 %',dso:'应收天数',dio:'存货天数',dpo:'应付天数',opening_nwc:'期初营运资金',volume_growth:'销量指数增长 %',price_growth:'价格指数变化 %',unit_cost_growth:'单位成本变化 %',retention:'客户留存 %',expansion:'留存客户扩张 %',new_customer_rate:'新增客户比例 %',new_customer_timing:'新增收入确认比例',service_cost_growth:'服务成本增长 %'};
const ranges={opex_growth:[-80,200],tax_rate:[0,60],da_ratio:[0,50],capex_ratio:[0,100],dso:[0,730],dio:[0,730],dpo:[0,730],opening_nwc:[-1e12,1e12],volume_growth:[-80,200],price_growth:[-80,100],unit_cost_growth:[-80,100],retention:[0,100],expansion:[-80,100],new_customer_rate:[0,200],new_customer_timing:[0,1],service_cost_growth:[-80,100]};
function calculate(s,p){
 for(const k of Object.keys(s.driver.params)){if(!Number.isFinite(p[k])||p[k]<ranges[k][0]||p[k]>ranges[k][1])throw Error(names[k]+' 超出允许范围');}
 const m=s.diagnostics.current;let revenue=m.revenue,cost=m.cost,opex=m.gross_profit-m.operating_income,nwc=p.opening_nwc,runrate=revenue;const rows=[];
 for(let t=1;t<=5;t++){
  if(s.driver.template==='hardware'){revenue*=(1+p.volume_growth/100)*(1+p.price_growth/100);cost*=(1+p.volume_growth/100)*(1+p.unit_cost_growth/100);}
  else{const retained=runrate*p.retention/100,expanded=retained*p.expansion/100,added=runrate*p.new_customer_rate/100;revenue=retained+expanded+added*p.new_customer_timing;runrate=retained+expanded+added;cost*=1+p.service_cost_growth/100;}
  opex*=1+p.opex_growth/100;const gross_profit=revenue-cost,ebit=gross_profit-opex,cash_tax=Math.max(ebit,0)*p.tax_rate/100,receivables=revenue*p.dso/365,inventory=cost*p.dio/365,payables=cost*p.dpo/365,next=receivables+inventory-payables,delta_nwc=next-nwc,da=revenue*p.da_ratio/100,capex=revenue*p.capex_ratio/100;nwc=next;
  rows.push({year:'FY'+(Number(s.diagnostics.years.at(-1).slice(2))+t)+'E',revenue,cost,gross_profit,net_opex:opex,ebit,cash_tax,receivables,inventory,payables,nwc,delta_nwc,da,capex,fcff:ebit-cash_tax+da-capex-delta_nwc});
 }return rows;
}
function table(headers,rows){return '<div class="table-wrap"><table><thead><tr>'+headers.map(x=>'<th>'+esc(x)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map(x=>'<td>'+x+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';}
function numberButton(s,period,metric){const o=s.observations.findLast(x=>x.period===period&&x.metric===metric);return o?'<button data-evidence="'+esc(o.id)+'" data-ticker="'+esc(s.company.ticker)+'" aria-label="查看'+esc(s.metric_dictionary[metric])+'来源">'+fmt(o.value)+'</button>':'—';}
function render(){
 const s=data[ticker],m=s.diagnostics.current,year=s.diagnostics.years.at(-1);$('#title').textContent=s.company.name+' / '+ticker;$('#question').textContent=s.company.question;
 document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-current',b.dataset.view===view?'page':'false'));
 let html='';
 if(view==='financial'){
 html='<div class="cards">'+[['营业收入',m.revenue],['毛利',m.gross_profit],['经营利润',m.operating_income],['经营现金流',m.cfo]].map(([l,v])=>'<div class="card"><span>'+l+'</span><strong>'+fmt(v)+'</strong><small>'+year+' · USD million</small></div>').join('')+'</div><h2>财务底稿 / Financial statements</h2><p>点击带下划线的数字，核对原始披露、期间、口径与计算依据。</p>';
 const keys=['revenue','cost','gross_profit','opex','other_operating_income','operating_income','net_income','cfo','capex','receivables','inventory','payables','assets','liabilities','equity'];
 html+=table(['指标 · USD million',...s.diagnostics.years],keys.map(k=>[esc(s.metric_dictionary[k]||k),...s.diagnostics.years.map(y=>numberButton(s,y,k))]));
 html+='<h2>下一步研究</h2><p>先核对报表勾稽，再解释竞争差异，最后进入经营情景。规模与利润率并不能单独证明护城河。</p>';
 }else if(view==='relations'){
 const labels={pass:'数值一致',fail:'存在差异',missing:'输入不足'};
 html='<h2>报表之间是否说得通？</h2><p>数值一致不等于独立验证。由资产减权益推算的负债，再代入资产负债恒等式，只能验证计算一致性。</p><div class="checks">'+s.relations.checks.filter(c=>c.period===year).map(c=>'<div class="card"><h3>'+esc(c.formula)+'</h3><p>'+esc(labels[c.status]||c.status)+' · 差额 '+fmt(c.difference)+'</p><p class="muted">'+esc(c.verification||c.verification_status||'仍需审核输入来源')+'</p><details><summary>展开输入与判定明细</summary><pre>'+esc(JSON.stringify(c,null,2))+'</pre></details></div>').join('')+'</div>';
 }else if(view==='compare'){
 const peers=s.company.mode==='software'?['ADBE']:['NVDA','AMD','INTC'];
 html='<h2>竞争差异 / Peer context</h2><p>统一 USD million、US GAAP、合并口径。财年结束日不同；以下为描述性比较，不计算竞争排名或 GPU 市占率。Adobe 暂无已核验同业样例。</p>';
 html+=table(['公司 / 基期','财年结束','收入','毛利率','经营利润率','CFO'],peers.map(t=>{const p=data[t],v=p.diagnostics.current,y=p.diagnostics.years.at(-1);return [esc(t+' / '+y),esc(p.company.periods?.[y]?.end),numberButton(p,y,'revenue'),fmt(v.gross_profit/v.revenue*100)+'%',fmt(v.operating_income/v.revenue*100)+'%',numberButton(p,y,'cfo')];}));
 html+='<div class="grid">'+peers.map(t=>'<article class="card"><h3>'+esc(data[t].company.name)+'</h3>'+data[t].differentiation.map(([a,b,id])=>'<p><b>'+esc(a)+'</b><br>'+esc(b)+' <a target="_blank" rel="noopener noreferrer" href="'+esc(data[t].documents.find(d=>d.id===id)?.url||'#')+'">原始资料 ↗</a></p>').join('')+'</article>').join('')+'</div>';
 }else{
 html='<h2>'+(s.driver.template==='hardware'?'量、价、成本 → 利润 → 资金占用':'留存、扩张、新客确认 → 利润 → 资金占用')+'</h2><p>全部参数均为 Assumed（假设）。五年使用固定参数；经营指数不等于真实销量或 ARR。期末余额估计周转天数，不能当作平均余额周转率。</p><form id="modelForm">'+Object.entries(s.driver.params).map(([k,v])=>'<label>'+esc(names[k])+'<input required type="number" step="any" min="'+ranges[k][0]+'" max="'+ranges[k][1]+'" name="'+k+'" value="'+v+'"></label>').join('')+'<button type="submit">重新计算情景 →</button></form><p id="modelError" role="alert"></p><div id="modelOutput"></div><details><summary>模型公式与边界</summary><p>硬件收入 = 上期收入 × (1 + 量增速) × (1 + 价增速)。软件收入 = 留存收入 + 扩张收入 + 新客户运行率 × 当年确认比例；基期收入作为期初运行率是模型假设。</p><p>EBIT = 收入 − 成本 − 净经营费用。NWC = 应收 + 存货 − 应付。FCFF = EBIT − 现金税 + 折旧 − 资本开支 − ΔNWC。FCFF 不等于披露 CFO。</p><p>没有完整预测三张报表、合同负债、税损结转或融资。结果不是估值结论；须在完整版保存依据、反证和修改记录。</p></details>';
 }
 $('#content').innerHTML=html;
 if(view==='drivers'){$('#modelForm').addEventListener('submit',e=>{e.preventDefault();runModel();});runModel();}
}
function runModel(){try{const p=Object.fromEntries([...new FormData($('#modelForm'))].map(([k,v])=>[k,Number(v)])),rows=calculate(data[ticker],p);$('#modelError').textContent='';$('#modelOutput').innerHTML='<h3>情景结果 · Assumed + Calculated · USD million</h3>'+table(['财年预测','收入','经营利润','现金税','Δ营运资金','资本开支','FCFF'],rows.map(r=>[r.year,...['revenue','ebit','cash_tax','delta_nwc','capex','fcff'].map(k=>fmt(r[k]))]));}catch(e){$('#modelOutput').replaceChildren();$('#modelError').textContent=e.message;}}
$('#content').addEventListener('click',e=>{const b=e.target.closest('[data-evidence]');if(!b)return;const s=data[b.dataset.ticker],o=s.observations.find(x=>x.id===b.dataset.evidence),d=s.documents.find(x=>x.id===o.source_id);$('#evidenceBody').innerHTML='<h3>'+esc(o.label||s.metric_dictionary[o.metric])+' · '+fmt(o.value)+'</h3><p>'+esc(o.kind)+' / '+esc(o.period)+' / '+esc(o.currency)+' '+esc(o.unit)+' / '+esc(o.basis)+' / '+esc(o.scope)+'</p><p>审核状态：待人工复核<br>披露日期：'+esc(d.disclosed_at)+'</p><p>'+esc(d.locator)+'</p><blockquote>'+esc(d.excerpt)+'</blockquote><p>'+esc(o.formula||d.note||'')+'</p><a target="_blank" rel="noopener noreferrer" href="'+esc(d.url)+'">'+esc(d.title)+' ↗</a>';$('#evidence').showModal();});
$('#close').onclick=()=>$('#evidence').close();$('#company').onchange=e=>{ticker=e.target.value;render();};$('#theme').onchange=e=>document.body.dataset.theme=e.target.value;
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{view=b.dataset.view;render();});
fetch('./data.json').then(r=>{if(!r.ok)throw Error('资料加载失败');return r.json();}).then(d=>{data=d;render();}).catch(()=>{$('#title').textContent='资料暂时无法加载';$('#content').innerHTML='<p>请刷新页面重试，或从左侧下载本地完整版。离线运行时需通过本地 HTTP 服务打开。</p>';});
