'use strict';
// Workspace-level views: registration, intake, financial identities and comparison.
// Existing modeling and research-record views keep their tested API contracts.
let companyList=[],savedTheme='original',previewTheme='original',intakeDocument=null;
const originalFail=fail;
fail=function(error){originalFail(error);if($('#drawer').open){let alert=$('#drawerError');if(!alert){alert=document.createElement('p');alert.id='drawerError';alert.setAttribute('role','alert');$('#drawerBody').prepend(alert)}alert.textContent=error.message;alert.scrollIntoView({block:'nearest'});}};
Object.assign(names,{overview:'研究看板',financial:'财务数据表',relations:'勾稽与质量',compare:'竞品对比',palette:'配色实验室'});
paramsText.opex_ratio='净经营费用率（含其他经营收益）';
const currency=()=>state?.company.currency||'USD';
const unitText=()=>currency()+' million';
const modes={general:'一般企业',hardware:'硬件与制造',software:'软件',consumer:'消费品',healthcare:'医疗',internet:'互联网',financial:'金融机构'};
const statusName={pass:'数值一致',fail:'存在差额',missing:'缺少输入',comparable:'可比',qualified:'有条件参考',blocked:'不可直接比较'};
const pageHelp={
 overview:['从这里开始','先检查数据是否齐全，再读财务表和勾稽结果。','financial','查看财务数据表'],
 financial:['读懂数值之间的关系','点击数字看来源；点击列标题可排序。报表缺失会留空。','relations','检查勾稽关系'],
 relations:['先解决差异，再解释业绩','展开每条规则查看公式、输入与缺失项。差额不等于财务造假。','evidence','补充或核验资料'],
 compare:['比较之前，先对齐口径','选择同行，核对币种、准则、期间和业务结构。条件不满足时不会排名。','market','记录差异背后的判断'],
 market:['把观察写成可检验判断','写明证据、反证和推翻条件；关联参数只是研究联系，不会自动替你改预测。','model','进入预测模型'],
 model:['每次只改少量参数，观察结果','修改 → 点击重新计算 → 检查现金流 → 填写理由 → 保存快照。高级参数可以稍后调整。','evaluation','冻结独立收入预测'],
 evidence:['把原始资料变成可用数据','点击“录入财务数据”，可从 Excel 粘贴两列；预览校验后再导入。','relations','查看数据勾稽结果'],
 evaluation:['预测必须留下当时的依据','先保存预测，再引入实际值。历史日期的练习会标记为回溯，不代表前瞻成绩。','memo','整理研究结论'],
 memo:['把过程整理成可交付结论','点击保存新版本后再导出；文件直接保存在 D 盘项目目录。','overview','返回研究看板']
};

function guide(){
 const h=pageHelp[page];if(!h)return;
 const target=$('#content');target.insertAdjacentHTML('afterbegin',`<section class="task-guide"><div><span class="mini-eyebrow">当前任务 / NEXT STEP</span><h2>${h[0]}</h2><p>${h[1]}</p></div><button class="secondary" data-go="${h[2]}">${h[3]} →</button></section>`);
}
const originalRender=render;
render=function(){
 if(!state)return;
 Object.assign(labels,state.metric_dictionary||{});
 $('#breadcrumb').textContent=names[page];$('#coverage').textContent=(modes[state.company.mode]||'自定义公司')+' / '+state.company.basis+' / '+state.company.scope;
 $('.edition span').textContent='研究时点快照 · '+unitText();
 $$('nav button').forEach(b=>b.setAttribute('aria-current',b.dataset.page===page?'page':'false'));
 $('#errorBox').hidden=true;
 if(page==='palette'){paletteView();return;}
 if(page==='compare'){compareView();guide();return;}
 if(page==='relations'){relationsView();guide();return;}
 if(page==='overview'){dashboardView();guide();return;}
 if(page==='financial'){statementsView();guide();return;}
 if(page==='model'&&!state.defaults){$('#content').innerHTML=empty(state.company.mode==='financial'?'金融机构使用独立的资产负债与风险口径，当前未开放一般企业 FCFF。可在财务表与勾稽中心研究净利息和资本结构。':'还不能开始预测：至少需要收入、毛利、经营费用和经营利润。先录入并核对数据。')+'<button class="primary" data-intake>录入财务数据</button>';guide();return;}
 if(page==='market'&&!state.defaults){$('#content').innerHTML=empty('先录入基础财务数据，再把市场论点关联到可用的经营参数。金融机构专用假设模板尚未开放。')+'<button class="primary" data-intake>录入财务数据</button>';guide();return;}
 if(['memo','evaluation','evidence'].includes(page)&&!state.diagnostics.years.length){({memo,evaluation,evidence}[page])();}else originalRender();
 guide();
 if(page==='evidence')$('.evidence-tools')?.insertAdjacentHTML('beforebegin','<div class="action-row"><button class="primary" data-intake>录入财务数据 / 粘贴 Excel</button><span class="note">先预览勾稽，不会直接写入。</span></div>');
 if(page==='model'){
   const fields=$$('#modelForm .parameter');const advanced=document.createElement('details');advanced.className='advanced-params';advanced.innerHTML='<summary>高级参数：税、折旧、资金占用与估值</summary>';
   fields.filter(el=>!['gross_margin','opex_ratio'].includes(el.querySelector('input').name)&&!el.querySelector('input').name.startsWith('growth_')).forEach(el=>advanced.append(el));$('#modelForm .parameter-group').append(advanced);
 }
 setCurrencyLabels();
};

function setCurrencyLabels(){
 if(!state)return;const content=$('#content');const walk=document.createTreeWalker(content,NodeFilter.SHOW_TEXT);let n;
 if(currency()!=='USD')while(n=walk.nextNode()){if(n.nodeValue.includes('USD million'))n.nodeValue=n.nodeValue.replaceAll('USD million',unitText())}
 const disabled=$('#forecastForm input[disabled]');if(disabled)disabled.value='营业收入 / '+unitText()+' / '+state.company.basis+' / '+state.company.scope;
}
new MutationObserver(()=>setCurrencyLabels()).observe($('#content'),{childList:true,subtree:true});

function dashboardView(){
 const d=state.diagnostics,years=d.years,coverage=state.relations.coverage;const m=d.current||{};
 if(!years.length){$('#content').innerHTML=`<section class="paper welcome"><span class="mini-eyebrow">建立你的研究对象</span><h2>${esc(state.company.name)} 已准备好接收数据</h2><p>公司档案可以自由新增。没有数据时，系统会保留空白，不会自动生成财务表现。</p><ol><li>选择一份公司公告或财务报表。</li><li>录入来源、期间与财务数据。</li><li>预览勾稽关系，再确认导入。</li></ol><button class="primary" data-intake>第一步：录入财务数据</button></section>`;return;}
 const y=years.at(-1);const checks=state.relations.checks.filter(c=>c.period===y);const v=key=>m[key]==null?'—':fmt(m[key]);
 $('#content').innerHTML=`<div class="dashboard-stats">${stat('营业收入',v('revenue'),unitText(),obs('revenue',y)?`data-metric="${esc(obs('revenue',y).id)}"`:'')}${stat('经营利润',v('operating_income'),state.company.basis,obs('operating_income',y)?`data-metric="${esc(obs('operating_income',y).id)}"`:'')}${stat('经营现金流',v('cfo'),'缺失不补造',obs('cfo',y)?`data-metric="${esc(obs('cfo',y).id)}"`:'')}${stat('待核验指标',state.review_pending,'点击进入证据审核','data-go="evidence"')}</div>
 <div class="dashboard-grid"><section class="paper">${head('从收入到经营利润','按披露结构分解 · '+esc(unitText()))}${[['revenue','营业收入'],['cost','减：营业成本'],['gross_profit','毛利润'],['opex','减：经营费用'],...(m.other_operating_income!=null?[['other_operating_income','加：其他经营收益']]:[]),['operating_income','经营利润']].map(([k,l])=>`<div class="waterfall-row"><span>${l}</span><progress max="${Math.max(Math.abs(m.revenue||1),Math.abs(m[k]||0))}" value="${Math.abs(m[k]||0)}" aria-label="${l}"></progress><b>${metricButton(k,y)}</b></div>`).join('')}<button class="text-button" data-go="relations">查看这些数值是否勾稽 →</button></section>
 <section class="paper">${head('数据质量看板','规则通过说明算术一致，不代表信息完整。')}<div class="quality-counts"><span><b>${coverage.pass}</b>数值一致</span><span><b>${coverage.fail}</b>差额</span><span><b>${coverage.missing}</b>缺项</span></div>${checks.slice(0,5).map(c=>`<div class="check-row"><span>${esc(c.group)} / ${esc(labels[c.target])}</span>${badge(statusName[c.status],c.status==='fail'?'rust':'')}</div>`).join('')}<button class="secondary" data-go="relations">打开全部勾稽规则</button></section></div>
 <section class="paper">${head('趋势与共同百分比表','把利润、现金流与收入放在同一张表中理解；不是跨公司自动排名。')}<div class="table-wrap"><table><thead><tr><th>期间</th><th>收入</th><th>毛利率</th><th>经营利润率</th><th>净利率</th><th>CFO / 收入</th><th>负债 / 资产</th></tr></thead><tbody>${state.relations.common_size.map(r=>`<tr><th>${esc(r.period)}</th><td>${metricButton('revenue',r.period)}</td>${['gross_margin','operating_margin','net_margin','cfo_margin','debt_ratio'].map(k=>`<td>${r[k]==null?'—':fmt(r[k],2)+'%'}</td>`).join('')}</tr>`).join('')}</tbody></table></div></section>
 <div class="dashboard-grid"><section class="paper">${head('业务结构','行业、商业模式和财务分组分别展示。')}<p>${esc(state.company.industry)} / ${esc(state.company.business_models.join('、'))}</p><div class="table-wrap"><table><thead><tr><th>收入分组</th><th>金额</th><th>公司收入占比</th></tr></thead><tbody>${state.company.segments.map(s=>`<tr><td><button class="link-button" data-source="${esc(s.source)}">${esc(s.name)} ↗</button></td><td>${fmt(s.value)}</td><td>${m.revenue?fmt(s.value/m.revenue*100,1)+'%':'—'}</td></tr>`).join('')}</tbody></table></div><p class="note">收入占比不是市场份额。未拆分业务的公司只显示总收入，不编造分部。</p></section><section class="paper">${head('研究进度','每一步都留下可回看的结果')}<div class="progress-list">${[['证据审核',state.observations.length-state.review_pending,'evidence'],['研究论点',records('thesis').length,'market'],['模型快照',records('model').length,'model'],['预测检验',records('evaluation').length,'evaluation'],['备忘录版本',records('memo').length,'memo']].map(([l,n,p])=>`<button data-go="${p}"><span>${l}</span><b>${n}</b><span>查看 →</span></button>`).join('')}</div></section></div>`;
}

function statementsView(){
 const years=state.diagnostics.years;const metrics=[...new Set(state.observations.filter(o=>o.period_type==='annual').map(o=>o.metric))];
 $('#content').innerHTML=`<section class="paper">${head('财务数据工作表','点击数值溯源；按报表筛选，或搜索指标。金额已统一为 '+esc(unitText())+'。')}<div class="table-toolbar"><input id="metricSearch" placeholder="搜索收入、存货、现金…" aria-label="搜索财务指标"><select id="statementFilter" aria-label="报表筛选"><option value="all">全部指标</option><option value="income">损益</option><option value="balance">资产负债</option><option value="cash">现金流</option></select><button class="primary" data-intake>新增一期数据</button></div><div class="table-wrap"><table id="statementTable"><thead><tr><th>指标</th>${years.map((y,i)=>`<th><button class="sort-button" data-sort-column="${i+1}">${esc(y)} ↕</button></th>`).join('')}<th>同比变化</th></tr></thead><tbody>${metrics.map(k=>{const vals=years.map(y=>state.periods[y][k]);const a=vals.at(-2),b=vals.at(-1);return `<tr data-key="${k}" data-label="${esc(labels[k]||k)}"><th>${esc(labels[k]||k)}</th>${years.map((y,i)=>`<td data-value="${vals[i]??''}">${metricButton(k,y)}</td>`).join('')}<td>${a==null||b==null||a===0?'—':fmt((b-a)/Math.abs(a)*100,2)+'%'}</td></tr>`}).join('')||'<tr><td>暂无已导入的年度数据。可先录入数据。</td></tr>'}</tbody></table></div><p class="note">同比变化用上期绝对值作分母；负数跨越零时不能解读为普通业务增长率。跨年度口径重述仍需人工复核。</p></section>`;
 const group=k=>['cfo','cfi','cff','capex','capex_principal','noncash_adjustments','operating_wc_cash','fx_cash','cash_change','cash_open','cash_close'].includes(k)?'cash':['assets','liabilities','equity','receivables','inventory','payables','cash_balance','restricted_cash','cash_securities','debt','current_assets','current_liabilities'].includes(k)?'balance':'income';
 const filter=()=>$$('#statementTable tbody tr[data-key]').forEach(r=>r.hidden=!(r.dataset.label+r.dataset.key).toLowerCase().includes($('#metricSearch').value.toLowerCase())||($('#statementFilter').value!=='all'&&group(r.dataset.key)!==$('#statementFilter').value));
 $('#metricSearch').oninput=filter;$('#statementFilter').onchange=filter;
 $$('[data-sort-column]').forEach(button=>button.onclick=()=>{const index=Number(button.dataset.sortColumn),direction=button.dataset.direction==='asc'?-1:1;button.dataset.direction=direction===1?'asc':'desc';const rows=$$('#statementTable tbody tr[data-key]');rows.sort((a,b)=>{const x=a.cells[index].dataset.value,y=b.cells[index].dataset.value;return x===''?1:y===''?-1:(Number(x)-Number(y))*direction});rows.forEach(r=>$('#statementTable tbody').append(r))});
}

function relationsView(){
 const checks=state.relations.checks;$('#content').innerHTML=`<section class="paper">${head('三表关系与口径检查','差额 = 披露结果 − 按输入计算的结果。容差 '+fmt(state.relations.tolerance,2)+' '+esc(unitText()))}<div class="relation-map"><button data-rule-group="损益">收入 → 毛利 → 经营利润</button><span>↘</span><button data-rule-group="跨表">净利润 → 调整 → 经营现金流</button><span>↘</span><button data-rule-group="现金">期初现金 → 净变动 → 期末现金</button></div><div class="table-toolbar"><select id="ruleStatus" aria-label="勾稽状态"><option value="all">全部状态</option><option value="fail">只看差额</option><option value="missing">只看缺失</option><option value="pass">只看通过</option></select><button class="secondary" data-intake>补充规则所需数据</button></div><div id="ruleList">${checks.map(c=>`<details class="rule-item" data-status="${c.status}" data-group="${c.group}"><summary>${badge(statusName[c.status],c.status==='fail'?'rust':c.status==='missing'?'gold':'')}<span>${esc(c.period)} / ${esc(c.formula)}</span><b>${c.difference==null?'—':fmt(c.difference,2)}</b></summary><div class="rule-body"><p>${c.missing.length?'缺少：'+c.missing.map(k=>esc(labels[k])).join('、'):'计算结果 '+fmt(c.expected,2)+'；披露结果 '+fmt(c.actual,2)}</p><div class="table-wrap"><table><thead><tr><th>输入指标</th><th>值 / ${esc(unitText())}</th><th>状态</th></tr></thead><tbody>${c.inputs.map(k=>`<tr><td>${esc(labels[k]||k)}</td><td>${metricButton(k,c.period)}</td><td>${obs(k,c.period)?'点击数字可核验来源':'未提供；不会按 0 处理'}</td></tr>`).join('')}</tbody></table></div><p class="note">先检查单位、期间、重述和报表分类。规则通过不是审计意见；规则失败也不是欺诈结论。</p></div></details>`).join('')||empty('尚无财务数据，先录入一个期间。')}</div></section>`;
 $('#ruleStatus').onchange=e=>$$('.rule-item').forEach(r=>r.hidden=e.target.value!=='all'&&r.dataset.status!==e.target.value);
 $$('[data-rule-group]').forEach(b=>b.onclick=()=>{$$('.rule-item').forEach(r=>{r.hidden=false;r.open=r.dataset.group.includes(b.dataset.ruleGroup)});$('#ruleStatus').value='all'});
}

async function refreshCompanies(selected){
 const result=await api('companies');companyList=result.companies;const current=selected||$('#company').value;
 $('#company').innerHTML=companyList.map(c=>`<option value="${esc(c.ticker)}">${esc(c.name)} / ${esc(c.ticker)}</option>`).join('');$('#company').value=companyList.some(c=>c.ticker===current)?current:companyList[0]?.ticker;
}
function companyDrawer(){
 drawer('新建研究公司',`<p>支持为任意公司建立独立档案并导入资料。这里不会凭公司名称自动生成财务数据。</p><form id="companyForm" class="form-grid"><label>公司名称<input name="name" required placeholder="例如：某某科技"></label><label>唯一代码<input name="ticker" required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,31}" placeholder="股票代码或自定义标识"></label><label>行业分类<select name="industry"><option value="semiconductors">半导体</option><option value="hardware">硬件与制造</option><option value="software">软件</option><option value="consumer">消费品</option><option value="healthcare">医疗</option><option value="internet">互联网</option><option value="financial">金融</option><option value="unclassified">其他 / 尚未分类</option></select></label><label>商业模式<input name="business_model" required placeholder="订阅、设备销售、银行…"></label><label>分析模板<select name="mode">${Object.entries(modes).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></label><label>呈报币种<select name="currency">${['USD','CNY','EUR','HKD','JPY','GBP'].map(x=>`<option>${x}</option>`).join('')}</select></label><label>会计准则<select name="basis"><option>GAAP</option><option>IFRS</option><option>CAS</option></select></label><label>报表范围<select name="scope"><option value="consolidated">合并</option><option value="parent">母公司 / 单一主体</option></select></label><label class="wide">经营利润的披露结构<select name="operating_identity"><option value="with_other">毛利 − 费用 + 单列其他经营收益</option><option value="gp_less_opex">毛利 − 费用（已包含全部经营项目）</option></select></label><p class="note wide">金融机构可录入报表并检查净利息、资产负债关系；不启用一般企业 FCFF。其他模板先支持基础财务分析，行业专属经营数据需继续补充。</p><div class="form-actions wide"><button class="primary" type="submit">创建公司，进入数据录入</button></div></form>`,'COMPANY / 公司档案');
 $('#companyForm').onsubmit=async e=>{e.preventDefault();try{const result=await api('create-company',Object.fromEntries(new FormData(e.target)));await refreshCompanies(result.ticker);page='overview';$('#drawer').close();await load();intakeDrawer()}catch(err){fail(err)}};
}

function intakeDrawer(){
 let revision=0;
 intakeDocument=null;drawer('录入财务数据',`<p><b>1 填写来源 → 2 粘贴数据 → 3 预览勾稽 → 4 确认导入</b></p><form id="intakeForm" class="form-grid"><label class="wide">来源标题<input name="title" required placeholder="公司年报 / 业绩公告"></label><label class="wide">官方原文链接<input type="url" name="url" required placeholder="https://…"></label><label>披露日期<input type="date" name="disclosed_at" value="${esc(state.asof)}" required></label><label>期间标签<input name="period" value="FY2025" pattern="FY[0-9]{4}(Q[1-4])?" required></label><label>期间开始<input type="date" name="period_start" required></label><label>期间结束<input type="date" name="period_end" required></label><label class="wide">页码 / 表格标题<input name="locator" required placeholder="第 60 页，合并利润表"></label><label>录入单位<select name="unit"><option value="million">百万</option><option value="one">元 / 基础货币单位</option><option value="thousand">千</option><option value="ten_thousand">万</option><option value="billion">十亿</option></select></label><label>口径<input disabled value="${esc(currency()+' / '+state.company.basis+' / '+state.company.scope)}"></label><label class="wide">指标与金额（可直接粘贴 Excel 两列）<textarea id="intakeRows" rows="8" required placeholder="营业收入&#9;1000&#10;营业成本&#9;600&#10;毛利润&#9;400"></textarea></label><details class="wide"><summary>查看支持的指标名称</summary><p class="note">${Object.values(state.metric_dictionary).map(esc).join('、')}。允许英文指标代码；每行一个指标，金额不能有币种符号。</p></details><div class="form-actions wide"><button class="primary" type="submit">预览数据与勾稽</button></div></form><div id="intakePreview"></div>`,'DATA INTAKE / 数据录入');
 $('#intakeForm').addEventListener('input',()=>{revision++;intakeDocument=null;$('#intakePreview').innerHTML='';});
 $('#intakeForm').onsubmit=async e=>{e.preventDefault();try{
  const submittedRevision=revision;const f=Object.fromEntries(new FormData(e.target));const id='doc-'+crypto.randomUUID();const dictionary=state.metric_dictionary;
  const rows=$('#intakeRows').value.trim().split(/\r?\n/).filter(Boolean).map((line,i)=>{const parts=line.trim().split(/\t| {2,}/);if(parts.length!==2)throw Error('第 '+(i+1)+' 行应为两列：指标名、金额。请从 Excel 复制两列，或用 Tab 分隔');const metric=Object.keys(dictionary).find(k=>k===parts[0].trim()||dictionary[k]===parts[0].trim());if(!metric)throw Error('未识别指标：'+parts[0]);const raw=parts[1].trim().replaceAll(',','');if(!/^-?\d+(\.\d+)?$/.test(raw))throw Error('第 '+(i+1)+' 行不是有效金额；负数请使用减号');return {id:id+'-'+i,company:context().company,period:f.period,period_type:f.period.includes('Q')?'quarterly':'annual',period_start:f.period_start,period_end:f.period_end,metric,value:Number(raw),currency:currency(),unit:f.unit,basis:state.company.basis,scope:state.company.scope,kind:'Disclosed'}});
  const doc={id,company:context().company,title:f.title,url:f.url,disclosed_at:f.disclosed_at,locator:f.locator,observations:rows};const result=await api('preview-import',{document:doc});if(submittedRevision!==revision)throw Error('录入内容已变化，请重新预览');intakeDocument=doc;
  $('#intakePreview').innerHTML=`<h3>预览结果 · 尚未保存</h3><p>识别 ${rows.length} 条；统一为 ${esc(unitText())}。${result.relations.coverage.pass} 条规则通过，${result.relations.coverage.fail} 条有差额，${result.relations.coverage.missing} 条缺项。</p><div class="table-wrap"><table><thead><tr><th>指标</th><th>标准化金额</th></tr></thead><tbody>${result.observations.map(o=>`<tr><td>${esc(o.label)}</td><td>${fmt(o.value,4)}</td></tr>`).join('')}</tbody></table></div>${result.relations.checks.filter(c=>c.status==='fail').map(c=>`<p class="note">${esc(c.formula)}：差额 ${fmt(c.difference,2)}</p>`).join('')}<p class="note">有差额的数据可以作为待核验资料保存，但核心报表差额未解决前不启动预测，也不进入竞品直接比较。</p><button id="confirmIntake" class="primary">确认导入这 ${rows.length} 条数据</button>`;
  $('#confirmIntake').onclick=async()=>{try{if(!intakeDocument)throw Error('数据已修改，请重新预览');const disclosed=intakeDocument.disclosed_at;await api('import',{document:intakeDocument});$('#drawer').close();page='relations';await load();if(disclosed>state.asof){$('#content').insertAdjacentHTML('afterbegin',`<section class="task-guide"><div><h2>资料已保存，但尚未进入当前研究时点</h2><p>披露日为 ${esc(disclosed)}。当前日期过滤仍然有效。</p></div><button id="advanceResearchDate" class="primary">查看披露日的研究数据</button></section>`);$('#advanceResearchDate').onclick=()=>{$('#asof').value=disclosed;load()};toast('保存成功；调整研究日期后可查看')}else toast('数据已保存，已打开勾稽中心')}catch(err){fail(err)}};
 }catch(err){fail(err)}};
}

function compareView(){
 $('#content').innerHTML=`<section class="paper">${head('选择比较对象','当前基准：'+esc(state.company.name)+'。同一行业不代表所有指标天然可比。')}<form id="compareForm"><div class="peer-options">${companyList.filter(c=>c.ticker!==context().company).map(c=>`<label><input type="checkbox" name="peer" value="${esc(c.ticker)}" ${c.industry===state.company.industry?'checked':''}>${esc(c.name)} <small>${esc(c.industry)}</small></label>`).join('')}</div><label class="nearby"><input type="checkbox" name="nearby" checked>允许相邻财年参考（年末相差不超过 45 天；不作为严格同期排名）</label><div class="action-row"><button class="primary" type="submit">检查口径并生成对比表</button><button class="secondary" type="button" data-new-company>添加其他竞品</button></div></form></section><div id="peerResults"></div>`;
 $('#compareForm').onsubmit=async e=>{e.preventDefault();try{const result=await api('compare',{peers:new FormData(e.target).getAll('peer'),nearby:e.target.elements.nearby.checked});peerResults(result)}catch(err){fail(err)}};
 $('#compareForm').requestSubmit();
}
function peerResults(result){
 const rows=result.rows;const metrics=['revenue','gross_profit','operating_income','net_income','cfo','receivables','inventory','sbc'];
 $('#peerResults').innerHTML=`<section class="paper">${head('可比性检查表','先读限制，再读差异。待审核、缺资料和跨行业项目不生成排名。')}<div class="table-wrap"><table><thead><tr><th>公司</th><th>年度 / 期末</th><th>币种 / 准则</th><th>比较状态</th><th>为什么</th></tr></thead><tbody>${rows.map(r=>`<tr><th>${esc(r.name)}</th><td>${esc(r.period||'无数据')}<br>${esc(r.period_end||'日期未补齐')}</td><td>${esc(r.currency)} / ${esc(r.basis)}</td><td>${badge(statusName[r.status],r.status==='blocked'?'rust':'gold')}</td><td>${r.reasons.map(esc).join('；')||'检查范围内一致'}</td></tr>`).join('')}</tbody></table></div></section><section class="paper">${head('财务差异矩阵','金额统一为 million；不同币种不自动换汇。点击数值查看该公司的来源。')}<div class="table-wrap"><table><thead><tr><th>指标</th>${rows.map(r=>`<th>${esc(r.name)}</th>`).join('')}</tr></thead><tbody>${metrics.map(k=>`<tr><th>${esc(labels[k]||k)}</th>${rows.map((r,i)=>`<td>${r.status==='blocked'?'不可比':r.values[k]==null?'未接入':`<button class="link-button" data-peer-value="${i}:${k}">${fmt(r.values[k])} ↗</button>`}</td>`).join('')}</tr>`).join('')}${[['gross_margin','毛利率'],['op_margin','经营利润率'],['cash_conversion','CFO / 净利润'],['sbc_ratio','股权激励 / 收入']].map(([k,l])=>`<tr><th>${l}</th>${rows.map(r=>`<td>${r.status==='blocked'?'不可比':r.ratios[k]==null?'未接入':fmt(r.ratios[k],2)+'%'}</td>`).join('')}</tr>`).join('')}</tbody></table></div></section><section class="paper">${head('商业模式与差异解释','以下是来源支持的结构差异；不自动生成竞争力评分。')}<div class="table-wrap"><table><thead><tr><th>公司</th><th>差异维度</th><th>需要怎样理解</th><th>证据</th></tr></thead><tbody>${rows.flatMap(r=>r.differences.length?r.differences.map(d=>{const doc=r.documents.find(s=>s.id===d.source_id);return `<tr><th>${esc(r.name)}</th><td>${esc(d.dimension)}</td><td>${esc(d.description)}</td><td>${doc?`<a href="${esc(doc.url)}" target="_blank" rel="noopener noreferrer">原文 ↗</a>`:'待接入'}</td></tr>`}):[`<tr><th>${esc(r.name)}</th><td colspan="3">尚无证据支持的业务差异记录；不自动补写。</td></tr>`]).join('')}</tbody></table></div><p class="note">${esc(result.note)}</p></section>`;
 $$('[data-peer-value]').forEach(b=>b.onclick=()=>{const [i,k]=b.dataset.peerValue.split(':');const r=rows[Number(i)];const o=r.observations.filter(x=>x.metric===k).at(-1);const d=r.documents.find(x=>x.id===o.source_id);drawer(r.name+' / '+labels[k],`<p>${fmt(o.value)} ${esc(r.currency)} million · ${esc(o.period)}</p><p>${esc(d?.title)} / ${esc(d?.locator)}</p><p>披露日 ${esc(o.disclosed_at)} · ${o.reviewed?'已核验':'待用户核验'}</p>${d?`<a href="${esc(d.url)}" target="_blank" rel="noopener noreferrer">打开来源 ↗</a>`:''}`,'PEER EVIDENCE')});
}

const themes=[['mono','01','纯白与石墨','中性色界面，靠字重和边界区分层级。'],['porcelain','02','瓷白与海盐','偏冷的亮底，低饱和青灰作为操作色。'],['navy','03','雾白与藏蓝','明亮画布，深蓝强调关键动作。'],['plum','04','雾粉与梅紫','浅暖背景，少量深梅色按钮。'],['copper','05','米白与陶红','白纸底，赤陶色标记选中状态。'],['night','06','午夜与银灰','深色底和浅灰文字，不使用暖金。']];
function applyTheme(theme){document.documentElement.dataset.theme=theme;previewTheme=theme;$$('[data-preview-theme]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.previewTheme===theme?'true':'false'))}
function paletteView(){
 $('#content').innerHTML=`${head('这一次由你选颜色','点击色卡会即时预览整个工作台；只有点击“保存我的选择”才会记住。')}<div class="palette-actions"><button class="primary" id="savePalette">保存我的选择</button><button class="secondary" id="revertPalette">恢复已保存配色</button><span id="themeStatus">${savedTheme==='original'?'尚未选择新主题':'已保存：'+esc(themes.find(x=>x[0]===savedTheme)?.[2]||savedTheme)}</span></div><div class="palette-grid">${themes.map(([id,no,name,desc])=>`<button class="palette-choice theme-${id}" data-preview-theme="${id}" aria-pressed="${previewTheme===id}"><span>${no} / ${name}</span><div class="palette-swatches"><i></i><i></i><i></i><i></i></div><div class="palette-sample"><div class="sample-sidebar"></div><div><b>公司研究</b><p>营业收入 / Revenue</p><strong>25,785</strong><span class="sample-action">查看证据 →</span></div></div><p>${desc}</p><small>点击预览整页</small></button>`).join('')}</div><p class="note">配色不会改变指标或研究记录。可先选色，再切换到财务表和预测页观察实际阅读感受。</p>`;
 $$('[data-preview-theme]').forEach(b=>b.onclick=()=>{applyTheme(b.dataset.previewTheme);$('#themeStatus').textContent='预览中，尚未保存：'+themes.find(x=>x[0]===previewTheme)[2]});
 $('#savePalette').onclick=async()=>{try{await api('save-theme',{theme:previewTheme});savedTheme=previewTheme;$('#themeStatus').textContent='选择已保存，刷新后保留';toast('配色已保存到 D 盘本地资料库')}catch(e){fail(e)}};
 $('#revertPalette').onclick=()=>{applyTheme(savedTheme);$('#themeStatus').textContent='已恢复保存的配色'};
}

function startWorkspace(){
 const nav=$('nav');nav.querySelector('[data-page="overview"]').innerHTML='<span>01</span>研究看板';nav.querySelector('[data-page="financial"]').innerHTML='<span>02</span>财务数据表';
 nav.querySelector('[data-page="financial"]').insertAdjacentHTML('afterend','<button data-page="relations"><span>03</span>勾稽与质量</button><button data-page="compare"><span>04</span>竞品对比</button>');
 $('.rail-label').insertAdjacentHTML('beforebegin','<button class="new-company" data-new-company>＋ 新建研究公司</button>');
 $('.top-actions').insertAdjacentHTML('beforeend','<button class="outline" data-page="palette">选择配色</button>');
 const navButtons=$$('nav button');navButtons.forEach((b,i)=>b.querySelector('span').textContent=String(i+1).padStart(2,'0'));
 api('session').then(async session=>{savedTheme=session.theme;applyTheme(savedTheme);await refreshCompanies();const hash=location.hash.slice(1);if(names[hash])page=hash;if(state)render()}).catch(fail);
}
document.addEventListener('click',e=>{
 const button=e.target.closest('button');if(!button)return;
 if(button.hasAttribute('data-intake'))intakeDrawer();
 if(button.hasAttribute('data-new-company'))companyDrawer();
 if(button.dataset.page||button.dataset.go){history.replaceState(null,'','#'+page);if($('#drawer').open)$('#drawer').close();}
});
window.addEventListener('hashchange',()=>{const next=location.hash.slice(1);if(names[next]){page=next;render()}});
startWorkspace();
