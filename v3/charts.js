(function(){
'use strict';
const instances=new Map();
const css=(name,fallback)=>getComputedStyle(document.documentElement).getPropertyValue(name).trim()||fallback;
const colors=()=>({ink:css('--ink','#1d1d1f'),muted:css('--muted','#6e6e73'),line:css('--line','rgba(0,0,0,.10)'),dataPrimary:css('--data-primary','#2f6f9f'),dataSecondary:css('--data-secondary','#706f85'),dataCash:css('--data-cash','#3f7d68'),dataWorking:css('--data-working','#7a6f9b'),dataInventory:css('--data-inventory','#a67a3d'),surface:css('--surface','#fff')});
const reduced=()=>matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
const compact=v=>v==null?'—':new Intl.NumberFormat('en-US',{notation:'compact',maximumFractionDigits:1}).format(v);
const pct=v=>v==null?'—':Number(v).toLocaleString('en-US',{maximumFractionDigits:1})+'%';
const ratio=(a,b)=>a==null||!b?null:a/b*100;
function init(el){if(!el||!window.echarts)return null;instances.get(el.id)?.dispose();const c=echarts.init(el);instances.set(el.id,c);return c}
function empty(el){if(el)el.innerHTML='<div class="chart-unavailable">Interactive chart unavailable. Research data is unchanged.</div>'}
function trajectory(el,s){
 const c=init(el);if(!c)return empty(el);const p=colors(),years=s.diagnostics.years||[],rows=years.map(y=>({y,r:s.periods[y]?.revenue,m:ratio(s.periods[y]?.operating_income,s.periods[y]?.revenue)})).filter(x=>x.r!=null);
 c.setOption({animationDuration:reduced()?0:600,legend:{top:0,left:0,textStyle:{color:p.muted,fontSize:10}},tooltip:{trigger:'axis',backgroundColor:'rgba(29,29,31,.92)',borderWidth:0,textStyle:{color:'#fff'},formatter:a=>[a[0]?.axisValue,...a.map(x=>x.marker+' '+x.seriesName+': '+(x.seriesName==='Operating margin'?pct(x.value):compact(x.value)))].join('<br>')},grid:{left:50,right:42,top:42,bottom:38},xAxis:{type:'category',data:rows.map(x=>x.y),axisTick:{show:false},axisLine:{lineStyle:{color:p.line}},axisLabel:{color:p.muted,fontSize:9}},yAxis:[{type:'value',splitLine:{lineStyle:{color:p.line}},axisLabel:{color:p.muted,fontSize:9,formatter:compact}},{type:'value',splitLine:{show:false},axisLabel:{color:p.muted,fontSize:9,formatter:v=>v+'%'}}],series:[{name:'Revenue',type:'bar',data:rows.map(x=>x.r),barMaxWidth:40,itemStyle:{color:p.dataPrimary,borderRadius:[5,5,2,2]}},{name:'Operating margin',type:'line',yAxisIndex:1,data:rows.map(x=>x.m),smooth:.2,symbolSize:7,lineStyle:{width:3,color:p.dataSecondary},itemStyle:{color:p.dataSecondary}}]},true)
}
function workingCapital(el,s){
 const c=init(el);if(!c)return empty(el);const p=colors(),years=s.diagnostics.years||[],rows=years.map(y=>({y,cfo:s.periods[y]?.cfo,receivables:s.periods[y]?.receivables,inventory:s.periods[y]?.inventory})).filter(x=>x.cfo!=null||x.receivables!=null||x.inventory!=null);
 c.setOption({animationDuration:reduced()?0:600,legend:{top:0,left:0,textStyle:{color:p.muted,fontSize:10}},tooltip:{trigger:'axis',backgroundColor:'rgba(29,29,31,.92)',borderWidth:0,textStyle:{color:'#fff'}},grid:{left:50,right:18,top:42,bottom:38},xAxis:{type:'category',data:rows.map(x=>x.y),axisTick:{show:false},axisLine:{lineStyle:{color:p.line}},axisLabel:{color:p.muted,fontSize:9}},yAxis:{type:'value',splitLine:{lineStyle:{color:p.line}},axisLabel:{color:p.muted,fontSize:9,formatter:compact}},series:[['CFO','cfo',p.dataCash],['Receivables','receivables',p.dataWorking],['Inventory','inventory',p.dataInventory]].map(([name,k,color])=>({name,type:'line',data:rows.map(x=>x[k]??null),connectNulls:false,smooth:.18,symbolSize:6,lineStyle:{width:2.4,color},itemStyle:{color}}))},true)
}
function segmentMix(el,s){
 const c=init(el);if(!c)return empty(el);const p=colors(),data=(s.company.segments||[]).filter(x=>Number(x.value)>0).map(x=>({name:x.name,value:Number(x.value)}));if(!data.length)return empty(el);
 c.setOption({animationDuration:reduced()?0:600,color:[p.dataPrimary,p.dataSecondary,p.dataCash,p.dataInventory,'#7f95a6','#9b8a78'],tooltip:{trigger:'item',formatter:x=>x.name+'<br>'+compact(x.value)+' · '+x.percent+'%'},legend:{orient:'vertical',right:0,top:'center',textStyle:{color:p.muted,fontSize:9}},series:[{type:'pie',radius:['52%','76%'],center:['38%','50%'],data,itemStyle:{borderColor:p.surface,borderWidth:3,borderRadius:7},label:{show:false},emphasis:{label:{show:true,fontWeight:650}}}]},true)
}
function resizeAll(){instances.forEach(c=>c.resize())}
window.AtlasPreviewCharts={trajectory,workingCapital,segmentMix,resizeAll};
})();