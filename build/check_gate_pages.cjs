const puppeteer=require('puppeteer-core');
const fs=require('fs');
const pw=fs.readFileSync('/tmp/claude-0/-root-work-sessions-max--76387277381017/fc47512f-3713-456a-b17c-dad2781d7db3/scratchpad/.a360pw','utf8').trim();
const R='/root/work/sessions/max--76387277381017/a360/';
const pages=fs.readdirSync(R).filter(f=>f.endsWith('.html'));
(async()=>{
 const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});
 let bad=0;
 for(const f of pages){
  const p=await b.newPage(); const errs=[];
  p.on('pageerror',e=>errs.push(String(e).slice(0,120)));
  p.on('console',m=>{if(m.type()==='error')errs.push(m.text().slice(0,120))});
  await p.goto('file://'+R+f,{waitUntil:'networkidle0'});
  await p.evaluate(()=>localStorage.clear());
  if(await p.evaluate(()=>!!document.getElementById('pw'))){
    await p.type('#pw',pw); await p.click('#go'); await new Promise(r=>setTimeout(r,1400));
  }
  const st=await p.evaluate(()=>({gate:!!document.getElementById('pw'),txt:document.body.innerText.length,
    inputs:document.querySelectorAll('input,textarea,select,button').length}));
  const ok = !st.gate && st.txt>800 && errs.length===0;
  if(!ok) bad++;
  console.log((ok?'ок      ':'СЛОМАНО '), f.padEnd(24), 'текст',String(st.txt).padStart(6), 'элементов',String(st.inputs).padStart(3), errs[0]||'');
  await p.close();
 }
 console.log(bad? ('СТРАНИЦ СЛОМАНО: '+bad) : 'все страницы открываются через пароль без ошибок');
 await b.close();
})();
