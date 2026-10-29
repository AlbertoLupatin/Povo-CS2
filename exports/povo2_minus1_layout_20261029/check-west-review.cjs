const {chromium}=require('C:/Users/Alberto/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const b=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 try{
  const p=await b.newPage({viewport:{width:780,height:1200}}),errors=[];
  p.on('pageerror',e=>{errors.push(e.message);console.log('ERROR',e.message);});
  await p.goto('http://127.0.0.1:8782');const f=p.frames()[1];
  await f.locator('[data-detail]').filter({hasText:'WEST office corridor'}).waitFor({timeout:20000});
  await p.screenshot({path:__dirname+'/west-review-3d.png',fullPage:true});
  await f.locator('[data-view]').selectOption('top');
  await p.screenshot({path:__dirname+'/west-review-plan.png',fullPage:true});
  await f.locator('[data-lab-context]').check();
  if(!(await f.locator('.p2-labels').textContent()).includes('RESTRICTED LABS'))throw Error('missing restricted context');
  await p.screenshot({path:__dirname+'/west-review-context.png',fullPage:true});
  await f.locator('[data-lab-context]').uncheck();
  await f.locator('[data-floor-toggle="0"]').click();await f.locator('[data-floor-toggle="-2"]').click();
  const d=await f.locator('[data-detail]').textContent();console.log('alignment',d);
  if(!d.includes('0: WEST corridor')||!d.includes('−1: WEST office corridor')||!d.includes('−2: Aligned WEST corridor'))throw Error('alignment selection');
  await f.locator('[data-view]').selectOption('iso');await f.locator('[data-home]').click();
  await p.screenshot({path:__dirname+'/west-review-stacked.png',fullPage:true});
  await p.setViewportSize({width:360,height:1100});await p.waitForTimeout(150);
  if(await f.locator('#povo2-layout-review').evaluate(e=>e.scrollWidth>e.clientWidth))throw Error('mobile overflow');
  if(errors.length)throw Error(errors.join(';'));
  console.log('Western review: runtime, floor toggles, plan, restricted context, shared axis and mobile fit pass.');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exit(1)});
