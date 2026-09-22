const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{spawn}=require('node:child_process'),vm=require('node:vm');
const root=path.resolve(__dirname,'..'),runtime=path.join(root,'.runtime','pages-qa');fs.mkdirSync(runtime,{recursive:true});
for(const k of ['TEMP','TMP','TMPDIR'])process.env[k]=runtime;
const data=JSON.parse(fs.readFileSync(path.join(root,'pages/data.json'),'utf8'));
const source=fs.readFileSync(path.join(root,'pages/app.js'),'utf8');
const sandbox={document:{querySelector:()=>({}),querySelectorAll:()=>[]}};vm.createContext(sandbox);
vm.runInContext(source.split("$('#content').addEventListener")[0],sandbox);
let parity=0;
for(const s of Object.values(data)){const rows=sandbox.calculate(s,s.driver.params);for(let i=0;i<5;i++)for(const k of ['revenue','cost','gross_profit','net_opex','ebit','cash_tax','receivables','inventory','payables','nwc','delta_nwc','da','capex','fcff']){assert.ok(Math.abs(rows[i][k]-s.reference_model[i][k])<=.0051,`${s.company.ticker} ${i} ${k}`);parity++;}}
const web=path.join(runtime,'web','Research-Atlas');fs.mkdirSync(web,{recursive:true});for(const file of fs.readdirSync(path.join(root,'pages')))fs.copyFileSync(path.join(root,'pages',file),path.join(web,file));
const server=spawn('D:/python/python.exe',['-B','-m','http.server','8774','--bind','127.0.0.1','--directory',path.dirname(web)],{env:process.env,windowsHide:true,stdio:'ignore'});
const {chromium}=require('C:/Users/wangbohan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{let context;try{for(let n=0;n<30;n++){try{const r=await fetch('http://127.0.0.1:8774/Research-Atlas/');if(r.ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
context=await chromium.launchPersistentContext(path.join(runtime,'profile'),{executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--disable-background-networking','--disable-component-update','--disable-breakpad','--disable-crash-reporter','--disk-cache-dir='+path.join(runtime,'cache'),'--crash-dumps-dir='+path.join(runtime,'crashes')]});
const page=await context.newPage(),errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
await page.goto('http://127.0.0.1:8774/Research-Atlas/');await page.locator('.cards').waitFor();
await page.locator('[data-evidence]').first().click();await page.locator('dialog[open]').waitFor();assert.match(await page.locator('#evidenceBody').textContent(),/待人工复核/);await page.locator('#close').click();
for(const t of Object.keys(data)){await page.locator('#company').selectOption(t);await page.locator('[data-view="drivers"]').click();assert.equal(await page.locator('#modelOutput tbody tr').count(),5);const before=await page.locator('#modelOutput').textContent();await page.locator('[name="opex_growth"]').fill('20');await page.locator('#modelForm button').click();assert.notEqual(await page.locator('#modelOutput').textContent(),before);}
for(const width of [1280,390]){await page.setViewportSize({width,height:900});for(const view of ['financial','relations','compare','drivers']){await page.locator('[data-view="'+view+'"]').click();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,view+' overflow '+width);}}
await page.locator('#theme').selectOption('night');assert.equal(await page.locator('body').getAttribute('data-theme'),'night');await page.screenshot({path:path.join(runtime,'mobile.png'),fullPage:true});
assert.deepEqual(errors,[]);assert.ok(requests.every(u=>u.startsWith('http://127.0.0.1:8774/Research-Atlas/')));const result={parity_checks:parity,companies:4,widths:[1280,390],errors,requests,checks:['subpath assets','evidence modal','company switching','scenario recalculation','theme switching','no external requests']};fs.writeFileSync(path.join(runtime,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}finally{if(context)await context.close();server.kill();}})().catch(e=>{console.error(e);process.exitCode=1;});
