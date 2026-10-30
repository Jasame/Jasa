const fs=require('fs');const assert=require('assert');const {JSDOM,VirtualConsole}=require(process.env.JWB_JSDOM_PATH||'jsdom');
const data=JSON.parse(fs.readFileSync(process.env.JWB_FIXTURES||'/tmp/jwb-suite-dom-data.json'));
const html=fs.readFileSync(require('path').resolve(__dirname,'../static/admin.html'),'utf8');
const source=fs.readFileSync(require('path').resolve(__dirname,'../static/admin.js'),'utf8');
const errors=[],requests=[];const virtual=new VirtualConsole();virtual.on('jsdomError',e=>errors.push(e.message));
const dom=new JSDOM(html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/g,''),{url:'https://jasa.hk/bank/admin/',runScripts:'dangerously',pretendToBeVisual:true,virtualConsole:virtual});const w=dom.window;
w.HTMLDialogElement.prototype.showModal=function(){this.open=true;};
w.HTMLDialogElement.prototype.close=function(){if(!this.open)return;this.open=false;w.setTimeout(()=>this.dispatchEvent(new w.Event('close')),0);};
w.AbortController=global.AbortController;w.fetch=async function(url,options={}){const u=new URL(url);const key=u.pathname.replace('/bank/api/','');requests.push(u.toString());if(options.signal?.aborted)throw new DOMException('Aborted','AbortError');return {ok:true,status:200,json:async()=>structuredClone(key==='admin/actions'?{message:'管理完成 / Admin action completed'}:data[key]||data['admin/records'])};};
const tick=()=>new Promise(resolve=>setTimeout(resolve,15));
const vm=require('vm');const evaluate=code=>vm.runInContext(code,dom.getInternalVMContext());
const click=(selector)=>{const el=w.document.querySelector(selector);assert(el,'Missing '+selector);el.click();};
(async()=>{
 evaluate(source);evaluate(fs.readFileSync(require('path').resolve(__dirname,'../static/admin-growth.js'),'utf8'));await tick();await tick();assert(w.document.querySelector('h1').textContent.includes('数据总览'));
 for(const view of ['overview','users','applications','records','ledger','mail','system','audit','operations']){
  evaluate(`navigate('${view}')`);await tick();assert(w.document.querySelector('#content').textContent.trim(),'Empty view '+view);assert(!w.document.querySelector('.error-box'),'Error in '+view);assert(!w.document.querySelector('.nav').closest('details:not([open])'),'Desktop nav hidden by native disclosure');const toggle=w.document.querySelector('.admin-nav-toggle');assert(toggle);toggle.click();assert.equal(toggle.getAttribute('aria-expanded'),'true');toggle.click();assert.equal(toggle.getAttribute('aria-expanded'),'false');
  assert(!w.document.querySelector('#content img'),'Unescaped image in '+view);assert(!w.pwned);
 }
 evaluate("navigate('users')");await tick();click('[data-action="user"]');await tick();assert(w.document.querySelector('#detail').open);assert(w.document.querySelector('#detailTitle').textContent.includes('owner@example.com'));
 assert(w.document.querySelector('#detail').textContent.includes('••••'));
 click('[data-action="language"]');await tick();assert(w.document.documentElement.lang==='en');assert(w.document.querySelector('#detail').textContent.includes('Demo balances'));
 click('[data-action="scope"][data-view="records"]');await tick();assert(!w.document.querySelector('#detail').open);assert(w.document.querySelector('.filter-badge'));assert(requests.at(-1).includes('userId=suite-owner-test'));
 click('[data-action="record"]');await tick();assert(w.document.querySelector('#detail').open);assert(!w.document.querySelector('#detail img'));assert(!w.pwned);click('[data-action="close"]');await tick();
 evaluate("navigate('records')");await tick();w.document.querySelector('input[name="q"]').value='two@example.com';w.document.querySelector('#filterForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await tick();assert(requests.at(-1).includes('q=two%40example.com'));
 for(const view of ['overview','users','applications','records','ledger','mail','system','audit','operations']){evaluate(`navigate('${view}')`);await tick();assert(w.document.querySelector('h1').textContent);assert(!w.document.querySelector('#content img'));}
 const previous=w.fetch;w.fetch=async()=>({status:500,ok:false,json:async()=>({message:'服务异常 / Service unavailable'})});evaluate("navigate('users')");await tick();assert(w.document.querySelector('.error-box'));w.fetch=previous;click('[data-action="refresh"]');await tick();assert(!w.document.querySelector('.error-box'));
 assert.equal(errors.length,0,errors.join('\n'));assert(requests.every(u=>u.startsWith('https://jasa.hk/bank/api/')));
 evaluate("navigate('users')");await tick();click('[data-action="user"]');await tick();click('[data-action="manage"][data-kind="adjust-wallet"]');assert(w.document.querySelector('#manageAmount'));assert(w.document.querySelector('#manageFactor'));w.document.querySelector('#manageAmount').value='100';w.document.querySelector('#manageReason').value='DOM test adjustment';w.document.querySelector('#managePassword').value='local-test-password';w.document.querySelector('#adminManagementForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await tick();await tick();assert(requests.some(u=>u.includes('/admin/actions')));evaluate("navigate('system')");await tick();click('[data-action="manageRules"]');assert(w.document.querySelector('#manageIncome'));click('[data-action="close"]');
 console.log('Admin native-event regression: all 9 views in Chinese/English, detail dialogs, scoped search, form submission, retry, /bank paths and XSS escaping: PASS');
 console.log('Note: DOM checks do not measure browser layout or visual rendering.');w.close();
})().catch(e=>{console.error(e);w.close();process.exit(1)});
