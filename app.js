'use strict';
const $ = id => document.getElementById(id);
const cases = {
  hardware: {name:'北辰设备（虚构）',growth:'销量增长',margin:35,chain:['零部件采购','整机制造与研发','经销渠道 → 消费者'],detail:['成本 / 供应风险','产品组合 / 良率','出货 ≠ 终端销售'],question:'研究问题：销量增长是否以渠道库存积压为代价？需要销售、库存和回款证据共同验证。',counter:'反证与未知：目前没有终端动销、渠道库存或成交均价证据；不得由竞品降价直接推导销量下降。',source:'模拟案例 H-001：年度销量 100,000 台；平均每台收入 2,000 元。仅用于界面与公式验证。'},
  software: {name:'云栈软件（虚构）',growth:'平均付费客户增长',margin:75,chain:['研发与基础设施','年度订阅服务','企业付费客户'],detail:['研发费用 / 云资源成本','履约期间 / 收入确认','留存 / 扩张 / 客户集中度'],question:'研究问题：客户增长能否抵消流失？需要留存率和收入确认期间；ARR 不直接等于报表收入。',counter:'反证与未知：缺少新增、流失及扩张客户的明细。此简化模型使用年度平均客户数，不把期末客户数直接当作全年收入驱动。',source:'模拟案例 S-001：年度平均付费客户 2,000 个；每客户年均确认收入 12,000 元。没有真实 ARR 或留存数据。'}
};
const state = Object.fromEntries(Object.keys(cases).map(k=>[k,{growth:10,margin:cases[k].margin,notes:'',revisions:[]}]));
const evidence = {disclosedAt:'2026-03-01',periodEnd:'2025-12-31'};
let kind = 'hardware';
const format = value => value.toLocaleString('zh-CN',{maximumFractionDigits:2});
function visible(){return AtlasModel.available(evidence,$('asof').value);}
function showEvidence(title,body){$('evidenceTitle').textContent=title;$('evidenceBody').textContent=body;}
function inspect(){showEvidence('基期输入 · 模拟来源',cases[kind].source+'\n\n数据类别：Simulated（独立于真实 Disclosed）\n币种 / 单位：CNY / 元、百万元\n期间：2025-01-01 至 2025-12-31 / 全年\n口径：虚构公司合并口径\n模拟可用日期：2026-03-01\n来源：内置教学 fixture；页码：不适用\n审核状态：待人工审核\n截至当前研究日期：'+(visible()?'可用':'不可用；不得参与计算'));}
function render(){
  const c=cases[kind],s=state[kind],ok=visible();
  $('growth').value=s.growth;$('margin').value=s.margin;$('growthLabel').textContent=c.growth+' · Assumed 假设';
  $('growthValue').textContent=s.growth+'%';$('marginValue').textContent=s.margin+'%';
  $('researchQuestion').textContent=c.question;$('counter').textContent=c.counter;$('notes').value=s.notes;
  $('chain').replaceChildren(...c.chain.map((label,i)=>{const div=document.createElement('div');div.textContent=label;const small=document.createElement('small');small.textContent=c.detail[i];div.append(small);return div;}));
  const r=AtlasModel.scenario(kind,s.growth,s.margin);
  $('metrics').replaceChildren(...[['基期收入 / 百万元',ok?format(r.base):'—','Simulated · 点击核验'],['模拟基期','FY2025','全年 / 合并口径'],['人工审核','待核验','尚未开展真实公司审核']].map(([label,value,note])=>{const b=document.createElement('button');b.className='metric';for(const [tag,text] of [['span',label],['strong',value],['small',note]]){const el=document.createElement(tag);el.textContent=text;b.append(el);}b.onclick=inspect;return b;}));
  $('revenue').textContent=ok?format(r.revenue):'—';$('profit').textContent=ok?'情景毛利润 '+format(r.grossProfit)+' 百万元 / Calculated':'该日期尚无可用基期数据，计算已阻止。';
  $('bar').style.width=ok?(1+s.growth/100)/1.5*100+'%':'0%';
  $('commit').disabled=!ok;
  $('revisions').replaceChildren();
  const entries=s.revisions.length?s.revisions.map(x=>`${x.time} · ${x.reason}；增长 ${x.before.growth}% → ${x.after.growth}%；毛利率 ${x.before.margin}% → ${x.after.margin}%；情景收入 ${format(x.revenue)} 百万元；研究截至 ${x.asOf}`):['还没有已提交的假设修订。拖动参数只改变预览，提交时才记录原因。'];
  entries.forEach(t=>{const li=document.createElement('li');li.textContent=t;$('revisions').append(li);});
}
$('industry').onchange=()=>{kind=$('industry').value;$('reason').value='';$('status').textContent='';render();inspect();};
$('asof').onchange=()=>{render();inspect();};
for(const id of ['growth','margin']) $(id).oninput=()=>{state[kind][id]=Number($(id).value);render();};
$('notes').oninput=()=>{state[kind].notes=$('notes').value;};
$('formulaButton').onclick=()=>{if(!visible()){inspect();return;}const s=state[kind],r=AtlasModel.scenario(kind,s.growth,s.margin);showEvidence('Calculated · 公式与输入',r.formula+'\n\n增长 = '+s.growth+'%\n收入 = '+format(r.revenue)+' 百万元\n毛利润 = 收入 × '+s.margin+'% = '+format(r.grossProfit)+' 百万元\n\n基于模拟输入的假设结果，不是预测承诺。模型未计算估值。');};
$('commit').onclick=()=>{if(!visible())return;const reason=$('reason').value.trim();if(!reason){$('status').textContent='请写明修改依据或实验目的。';return;}const s=state[kind],last=s.revisions.at(-1),before=last?last.after:{growth:10,margin:cases[kind].margin};s.revisions.push({time:new Date().toISOString(),reason,before:{...before},after:{growth:s.growth,margin:s.margin},asOf:$('asof').value,revenue:AtlasModel.scenario(kind,s.growth,s.margin).revenue});$('reason').value='';$('status').textContent='已保存在本会话，导出后可留档。';render();};
$('export').onclick=()=>{const s=state[kind],r=AtlasModel.scenario(kind,s.growth,s.margin);const contents=['# Research Atlas｜'+cases[kind].name,'模拟教学案例；非真实公司研究；人工审核未完成。','研究截至：'+$('asof').value,'## 来源与边界',cases[kind].source,'模拟可用日期：2026-03-01；基期 FY2025；全年；合并口径；人民币百万元。',cases[kind].question,cases[kind].counter,'## 当前情景',visible()?`${r.formula}\n增长 ${s.growth}%；毛利率 ${s.margin}%；收入 ${r.revenue}；毛利润 ${r.grossProfit}。`:'截至研究日期无可用基期数据；计算结果已隐藏。','## 人工笔记',s.notes||'尚未填写','## 完整修订记录（包含其他研究截至日期的历史操作，不应作为当前时点可得证据）',JSON.stringify(s.revisions,null,2),'## 尚未验证','真实资料抽取、模型 API、完整财务模型及安全边界尚未验证。'].join('\n\n');const url=URL.createObjectURL(new Blob([contents],{type:'text/markdown;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='research-atlas-'+kind+'.md';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);$('status').textContent='已请求浏览器导出；请将保存位置选择到 D 盘。';};
render();
