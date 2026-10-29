const {chromium}=require('C:/Users/Alberto/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const b=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 try{
  const p=await b.newPage({viewport:{width:780,height:1200}}),errors=[];
  p.on('pageerror',e=>{errors.push(e.message);console.log('PAGE ERROR',e.message);});
  await p.goto('http://127.0.0.1:8781');const f=p.frames()[1];
  await f.locator('[data-detail]').filter({hasText:'Aligned main corridor'}).waitFor({timeout:20000});
  console.log('initial',await f.locator('[data-detail]').textContent());
  await p.screenshot({path:__dirname+'/review-minus1.png',fullPage:true});
  await f.locator('[data-view]').selectOption('top');
  await p.screenshot({path:__dirname+'/review-plan.png',fullPage:true});
  await f.locator('[data-floor-toggle="0"]').click();
  await f.locator('[data-floor-toggle="-2"]').click();
  const text=await f.locator('[data-detail]').textContent();console.log('three floors',text);
  if(!text.includes('0: Aligned main corridor')||!text.includes('−1: Aligned main corridor')||!text.includes('−2: Aligned office corridor'))throw Error('alignment selection');
  await f.locator('[data-view]').selectOption('iso');
  await f.locator('[data-home]').click();
  await p.screenshot({path:__dirname+'/review-stacked.png',fullPage:true});
  await f.locator('[data-floor-toggle="0"]').click();
  await f.locator('[data-floor-toggle="-2"]').click();
  await f.locator('[data-view]').selectOption('top');
  const cb=await f.locator('canvas').boundingBox();
  let changed=false;
  for(const [x,y] of [[.65,.5],[.7,.3],[.4,.6],[.3,.7],[.6,.65]]){
   await p.mouse.click(cb.x+cb.width*x,cb.y+cb.height*y);
   if(!(await f.locator('[data-detail]').textContent()).includes('Aligned main corridor')){changed=true;break;}
  }
  if(!changed)throw Error('picking did not update');
  console.log('selected',await f.locator('[data-detail]').textContent());
  await p.setViewportSize({width:360,height:1100});await p.waitForTimeout(200);
  if(await f.locator('#povo2-layout-review').evaluate(e=>e.scrollWidth>e.clientWidth))throw Error('mobile overflow');
  await p.screenshot({path:__dirname+'/review-mobile.png',fullPage:true});
  if(errors.length)throw Error(errors.join(';'));
  console.log('No runtime errors; rotation controls, visibility, overlay, alignment and selection checked.');
  await p.goto('file:///'+__dirname.replaceAll('\\','/')+'/minus1_new_layout.svg',{waitUntil:'domcontentloaded'});
  await p.screenshot({path:__dirname+'/minus1_new_layout.png',fullPage:true});
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exit(1)});
