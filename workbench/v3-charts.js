(function(){
  'use strict';
  const instances=new Map();
  const reduced=()=>window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const css=(name,fallback)=>{
    const value=getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return value||fallback;
  };
  const palette=()=>({
    ink:css('--ink','#1d1d1f'),
    muted:css('--muted','#6e6e73'),
    line:css('--line','rgba(0,0,0,.10)'),
    accent:css('--accent','#0066cc'),
    dataPrimary:css('--data-primary','#2f6f9f'),
    dataSecondary:css('--data-secondary','#706f85'),
    dataCash:css('--data-cash','#3f7d68'),
    dataWorking:css('--data-working','#7a6f9b'),
    dataInventory:css('--data-inventory','#a67a3d'),
    dataForecast:css('--data-forecast','#5f6b76'),
    success:css('--success','#247a45'),
    warning:css('--warning','#9b6a1f'),
    danger:css('--danger','#b73a35'),
    surface:css('--surface','#ffffff')
  });
  const compact=v=>v==null?'—':new Intl.NumberFormat('en-US',{notation:'compact',maximumFractionDigits:1}).format(v);
  const percent=v=>v==null?'—':Number(v).toLocaleString('en-US',{maximumFractionDigits:1})+'%';
  function init(el){
    if(!el||!window.echarts)return null;
    const old=instances.get(el.id);
    if(old){old.dispose();instances.delete(el.id)}
    const chart=window.echarts.init(el,null,{renderer:'canvas'});
    instances.set(el.id,chart);
    return chart;
  }
  function unavailable(el){
    if(el)el.innerHTML='<div class="chart-unavailable">Interactive chart unavailable. Research data remains unchanged.</div>';
  }
  function baseOption(){
    const p=palette();
    return {
      animationDuration:reduced()?0:620,
      animationDurationUpdate:reduced()?0:360,
      animationEasing:'cubicOut',
      textStyle:{fontFamily:'-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",sans-serif',color:p.ink},
      aria:{enabled:true},
      grid:{left:54,right:42,top:46,bottom:42,containLabel:false},
      legend:{top:0,left:0,itemWidth:10,itemHeight:6,textStyle:{color:p.muted,fontSize:12}},
      tooltip:{trigger:'axis',backgroundColor:'rgba(29,29,31,.92)',borderWidth:0,textStyle:{color:'#fff',fontSize:12},padding:[10,12],extraCssText:'border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.16);'},
      xAxis:{type:'category',axisTick:{show:false},axisLine:{lineStyle:{color:p.line}},axisLabel:{color:p.muted,fontSize:12}},
      yAxis:{type:'value',splitLine:{lineStyle:{color:p.line}},axisLine:{show:false},axisTick:{show:false},axisLabel:{color:p.muted,fontSize:12,formatter:compact}}
    };
  }
  function trajectory(el,rows){
    const chart=init(el);if(!chart)return unavailable(el);
    const p=palette(), clean=(rows||[]).filter(r=>r.revenue!=null);
    if(!clean.length)return unavailable(el);
    const option=baseOption();
    option.xAxis.data=clean.map(r=>r.period);
    option.yAxis=[
      {...option.yAxis,name:'Revenue',nameTextStyle:{color:p.muted,fontSize:12}},
      {type:'value',name:'Margin',min:null,max:null,splitLine:{show:false},axisLine:{show:false},axisTick:{show:false},axisLabel:{color:p.muted,fontSize:12,formatter:v=>v+'%'}}
    ];
    option.tooltip.formatter=params=>{
      const period=params[0]?.axisValue||'';
      return [period].concat(params.map(x=>x.marker+' '+x.seriesName+': '+(x.seriesName==='Operating margin'?percent(x.value):compact(x.value)))).join('<br>');
    };
    option.series=[
      {name:'Revenue',type:'bar',data:clean.map(r=>r.revenue),barMaxWidth:42,itemStyle:{color:p.dataPrimary,borderRadius:[5,5,2,2]},emphasis:{focus:'series'}},
      {name:'Operating margin',type:'line',yAxisIndex:1,data:clean.map(r=>r.operating_margin),smooth:.24,showSymbol:true,symbolSize:7,lineStyle:{width:3,color:p.dataSecondary},itemStyle:{color:p.dataSecondary},emphasis:{focus:'series'}}
    ];
    chart.setOption(option,true);
  }
  function workingCapital(el,rows){
    const chart=init(el);if(!chart)return unavailable(el);
    const p=palette(), clean=(rows||[]).filter(r=>r.cfo!=null||r.receivables!=null||r.inventory!=null);
    if(!clean.length)return unavailable(el);
    const option=baseOption();
    option.xAxis.data=clean.map(r=>r.period);
    option.series=[
      ['CFO','cfo',p.dataCash],
      ['Receivables','receivables',p.dataWorking],
      ['Inventory','inventory',p.dataInventory]
    ].map(([name,key,color])=>({name,type:'line',data:clean.map(r=>r[key]??null),smooth:.18,connectNulls:false,symbolSize:6,lineStyle:{width:2.4,color},itemStyle:{color},emphasis:{focus:'series'}}));
    chart.setOption(option,true);
  }
  function segmentMix(el,segments){
    const chart=init(el);if(!chart)return unavailable(el);
    const p=palette(), data=(segments||[]).filter(s=>Number.isFinite(Number(s.value))&&Number(s.value)>0).map(s=>({name:s.name,value:Number(s.value)}));
    if(!data.length)return unavailable(el);
    const colors=[p.dataPrimary,p.dataSecondary,p.dataCash,p.dataInventory,'#7f95a6','#9b8a78','#8b93a1'];
    chart.setOption({
      animationDuration:reduced()?0:620,
      color:colors,
      tooltip:{trigger:'item',formatter:x=>x.name+'<br>'+compact(x.value)+' · '+x.percent+'%'},
      legend:{orient:'vertical',right:0,top:'center',textStyle:{color:p.muted,fontSize:12}},
      series:[{name:'Segment mix',type:'pie',radius:['52%','76%'],center:['38%','50%'],avoidLabelOverlap:true,itemStyle:{borderColor:p.surface,borderWidth:3,borderRadius:8},label:{show:false},emphasis:{label:{show:true,fontSize:12,fontWeight:600}},data}]
    },true);
  }
  function bridge(el,rows){
    const chart=init(el);if(!chart)return unavailable(el);
    const p=palette(), items=(rows||[]).filter(x=>x&&x.value!=null);
    if(!items.length)return unavailable(el);
    let running=0;
    const base=[],pos=[],neg=[];
    items.forEach(item=>{
      const value=Number(item.value)||0;
      if(value>=0){base.push(running);pos.push(value);neg.push('-')}
      else{base.push(running+value);pos.push('-');neg.push(Math.abs(value))}
      running+=value;
    });
    chart.setOption({
      animationDuration:reduced()?0:620,
      tooltip:{trigger:'axis',axisPointer:{type:'shadow'},formatter:params=>{
        const i=params[0]?.dataIndex??0, item=items[i];
        return (item?.name||'Bridge')+'<br>Δ '+(item?.value>0?'+':'')+compact(item?.value);
      }},
      grid:{left:46,right:18,top:26,bottom:64},
      xAxis:{type:'category',data:items.map(x=>x.name),axisLabel:{color:p.muted,fontSize:12,rotate:18},axisTick:{show:false},axisLine:{lineStyle:{color:p.line}}},
      yAxis:{type:'value',axisLabel:{color:p.muted,fontSize:12,formatter:compact},splitLine:{lineStyle:{color:p.line}}},
      series:[
        {type:'bar',stack:'total',silent:true,itemStyle:{borderColor:'transparent',color:'transparent'},emphasis:{itemStyle:{borderColor:'transparent',color:'transparent'}},data:base},
        {name:'Increase',type:'bar',stack:'total',data:pos,itemStyle:{color:p.success,borderRadius:[4,4,2,2]}},
        {name:'Decrease',type:'bar',stack:'total',data:neg,itemStyle:{color:p.danger,borderRadius:[4,4,2,2]}}
      ]
    },true);
  }
  function peer(el,rows){
    const chart=init(el);if(!chart)return unavailable(el);
    const p=palette(), metrics=[
      ['revenue_growth','Revenue growth'],
      ['gross_margin','Gross margin'],
      ['op_margin','Operating margin'],
      ['cash_conversion','Cash conversion']
    ];
    if(!(rows||[]).length)return unavailable(el);
    chart.setOption({
      animationDuration:reduced()?0:620,
      tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
      legend:{top:0,textStyle:{color:p.muted,fontSize:12}},
      grid:{left:54,right:18,top:42,bottom:42},
      xAxis:{type:'category',data:metrics.map(x=>x[1]),axisLabel:{color:p.muted,fontSize:12},axisTick:{show:false},axisLine:{lineStyle:{color:p.line}}},
      yAxis:{type:'value',axisLabel:{color:p.muted,fontSize:12,formatter:v=>v+'%'},splitLine:{lineStyle:{color:p.line}}},
      series:rows.map((row,i)=>({
        name:row.ticker,
        type:'bar',
        barMaxWidth:28,
        data:metrics.map(([key])=>row.metric_checks?.[key]?.status==='qualified'?row.metric_checks[key].value:null),
        itemStyle:{color:[p.dataPrimary,p.dataSecondary,p.dataCash,p.dataInventory][i%4],borderRadius:[4,4,2,2]}
      }))
    },true);
  }
  function scenario(el,rows){
    const chart=init(el);if(!chart)return unavailable(el);
    const p=palette(), clean=rows||[];
    if(!clean.length)return unavailable(el);
    const option=baseOption();
    option.xAxis.data=clean.map(r=>r.year);
    option.series=[
      {name:'Revenue',type:'bar',data:clean.map(r=>r.revenue),barMaxWidth:34,itemStyle:{color:p.dataPrimary,borderRadius:[5,5,2,2]}},
      {name:'EBIT',type:'line',data:clean.map(r=>r.ebit),smooth:.2,lineStyle:{width:2.5,color:p.dataSecondary},itemStyle:{color:p.dataSecondary}},
      {name:'FCFF',type:'line',data:clean.map(r=>r.fcff),smooth:.2,lineStyle:{width:2.5,color:p.dataCash},itemStyle:{color:p.dataCash}}
    ];
    chart.setOption(option,true);
  }
  function resizeAll(){instances.forEach(chart=>chart.resize())}
  window.AtlasCharts={trajectory,workingCapital,segmentMix,bridge,peer,scenario,resizeAll};
})();