// Узкое звено практики, схема «каркас + модуль»: ассистент пишет rasschet.js
// для каркаса параметров и model.js для каркаса финмодели. Каждый модуль
// кладётся рядом с копией каркаса в build/runs/practice_modules/<модель>/<n>/,
// каркас открывается в браузере, в него загружаются CSV выбранных источников
// (или вводятся параметры), и результат сверяется с ожидаемыми значениями.
//
//   GIGACHAT_AUTH_KEY=$(secret get GIGA1_GIGACHAT_TOKEN) node build/check_practice_modules.cjs \
//     --models GigaChat-2,GigaChat-2-Max --runs 3 --variant prod1 --chosen dm,crm,fin --what calc,model
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const puppeteer = require('puppeteer-core');
const C = require('./src/practice_core.js');
const VARIANTS = JSON.parse(fs.readFileSync(path.join(__dirname, 'src/practice_variants.json'), 'utf8'));
const ROOT = path.join(__dirname, '..');
const OUT = path.join(__dirname, 'runs', 'practice_modules');

const args = process.argv.slice(2);
function opt(name, def) { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : def; }
const MODELS = opt('--models', 'GigaChat-2').split(',');
const RUNS = parseInt(opt('--runs', '1'), 10);
const VIDS = opt('--variant', 'prod1').split(',');
const WHAT = opt('--what', 'calc,model').split(',');
const CHOSEN = opt('--chosen', '');

function ask(prompt, model) {
  return execFileSync('python3', [path.join(__dirname, 'gigachat_cli.py'), model], { input: prompt, encoding: 'utf8', maxBuffer: 1 << 24, timeout: 300000 });
}
function near(a, b, rel) { return Math.abs(a - b) <= Math.abs(b) * (rel || 0.03) + 1e-9; }

async function open(browser, file, uploads, fields) {
  const p = await browser.newPage(); const errs = [];
  p.on('pageerror', e => errs.push(String(e).slice(0, 200)));
  p.on('console', m => { if (m.type() === 'error') errs.push(m.text().slice(0, 200)); });
  p.on('dialog', d => { errs.push('dialog: ' + d.message().slice(0, 100)); d.dismiss().catch(() => {}); });
  await p.goto('file://' + file, { waitUntil: 'load' });
  await new Promise(r => setTimeout(r, 300));
  if (uploads) {
    const payload = uploads.map(f => ({ name: path.basename(f), text: fs.readFileSync(f, 'utf8') }));
    await p.evaluate(list => {
      const inp = document.querySelector('input[type=file]'); const dt = new DataTransfer();
      list.forEach(f => dt.items.add(new File([f.text], f.name, { type: 'text/csv' })));
      inp.files = dt.files; inp.dispatchEvent(new Event('change', { bubbles: true }));
    }, payload);
    await new Promise(r => setTimeout(r, 800));
  }
  if (fields) {
    await p.evaluate(f => { Object.keys(f).forEach(k => { const el = document.getElementById('f-' + k); if (el) el.value = f[k]; }); document.getElementById('calc').click(); }, fields);
    await new Promise(r => setTimeout(r, 500));
  }
  const text = await p.evaluate(() => document.body.innerText);
  const status = await p.evaluate(() => (document.getElementById('status') || {}).textContent || '');
  await p.close();
  return { text, errs, status };
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const reportFile = path.join(OUT, 'report.json');
  const report = fs.existsSync(reportFile) ? JSON.parse(fs.readFileSync(reportFile, 'utf8')) : {};
  const browser = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--disable-dev-shm-usage', '--allow-file-access-from-files'] });
  for (const VID of VIDS) {
    const V = VARIANTS.filter(v => v.id === VID)[0];
    const chosenIds = (CHOSEN || V.inputs.map(i => i.sources[0].id).join(',')).split(',');
    const chosen = {}; V.inputs.forEach((inp, i) => { chosen[inp.id] = chosenIds[i] || inp.sources[0].id; });
    const files = {}; const uploads = []; const expected = {};
    V.inputs.forEach(inp => inp.sources.forEach(s => { files[s.file] = { text: fs.readFileSync(path.join(ROOT, 'practice_data', V.id, s.file), 'utf8') }; }));
    V.inputs.forEach(inp => { const s = inp.sources.filter(x => x.id === chosen[inp.id])[0]; uploads.push(path.join(ROOT, 'practice_data', V.id, s.file)); expected[inp.id] = s.expect; });
    const evalF = (f) => { let s = String(f); Object.keys(expected).forEach(k => { s = s.replace(new RegExp('\\b' + k + '\\b', 'g'), '(' + expected[k] + ')'); }); return Function('return (' + s.replace(/×/g, '*').replace(/÷/g, '/') + ')')(); };
    const expDelta = evalF(V.params.delta.formula), expPrice = evalF(V.params.price.formula), expVol = evalF(V.params.volume.formula);
    for (const model of MODELS) {
      for (let n = 1; n <= RUNS; n++) {
        const dir = path.join(OUT, model, VID + '_' + chosenIds.join('-') + '_' + n); fs.mkdirSync(dir, { recursive: true });
        if (WHAT.includes('calc')) {
          const key = model + '/calc_' + VID + '_' + chosenIds.join('-') + '_' + n;
          const pr = C.calcPrompt(V, chosen, files); const t0 = Date.now(); let resp = '';
          try { resp = ask(pr, model); } catch (e) { resp = 'ОШИБКА API ' + e; }
          const js = C.extractJs(resp);
          fs.writeFileSync(path.join(dir, 'calc_prompt.md'), '# промпт\n\n```\n' + pr + '\n```\n\n# ответ\n\n' + resp);
          let res = { sec: Math.round((Date.now() - t0) / 1000), js: !!js };
          if (js) {
            fs.writeFileSync(path.join(dir, 'rasschet.js'), js);
            fs.copyFileSync(path.join(ROOT, 'practice_data', VID, 'инструмент_параметров.html'), path.join(dir, 'инструмент_параметров.html'));
            const r = await open(browser, path.join(dir, 'инструмент_параметров.html'), uploads, null);
            const pp = C.parseParams(r.text);
            res.errors = r.errs.length; res.err0 = r.errs[0] || ''; res.status = r.status.slice(0, 120); res.params = pp;
            res.ok = !!(pp && near(pp.delta, expDelta, 0.05) && near(pp.price, expPrice, 0.03) && near(pp.volume, expVol, 0.01));
            fs.writeFileSync(path.join(dir, 'calc_page.txt'), r.text);
          } else res.ok = false;
          report[key] = res; fs.writeFileSync(reportFile, JSON.stringify(report, null, 1));
          console.log(key.padEnd(44), res.ok ? 'ОК ' : 'НЕТ', JSON.stringify(res));
        }
        if (WHAT.includes('model')) {
          const key = model + '/model_' + VID + '_' + n;
          const params = { delta: Math.round(expDelta * 100) / 100, volume: expVol, price: Math.round(expPrice * 100) / 100 };
          const mp = C.modelPrompt(V, params); const t0 = Date.now(); let resp = '';
          try { resp = ask(mp.text, model); } catch (e) { resp = 'ОШИБКА API ' + e; }
          const js = C.extractJs(resp);
          fs.writeFileSync(path.join(dir, 'model_prompt.md'), '# промпт\n\n```\n' + mp.text + '\n```\n\n# ответ\n\n' + resp);
          let res = { sec: Math.round((Date.now() - t0) / 1000), js: !!js };
          if (js) {
            fs.writeFileSync(path.join(dir, 'model.js'), js);
            fs.copyFileSync(path.join(ROOT, 'practice_data', VID, 'финмодель.html'), path.join(dir, 'финмодель.html'));
            const r = await open(browser, path.join(dir, 'финмодель.html'), null, params);
            res.errors = r.errs.length; res.err0 = r.errs[0] || ''; res.status = r.status.slice(0, 120);
            const t = r.text.replace(/[\s  ]/g, '');
            const npvTxt = C.money(mp.expect.npv).replace(/[\s  ]/g, '');
            res.npvOk = t.indexOf(npvTxt) >= 0;
            res.paybackOk = mp.expect.payback === null ? /недостигается/.test(t) : t.indexOf('месяц' + mp.expect.payback + 'Окупаемость') >= 0 || new RegExp('месяц' + mp.expect.payback + '\\b').test(t);
            res.ok = res.npvOk && res.paybackOk && r.errs.length === 0;
            fs.writeFileSync(path.join(dir, 'model_page.txt'), r.text);
          } else res.ok = false;
          report[key] = res; fs.writeFileSync(reportFile, JSON.stringify(report, null, 1));
          console.log(key.padEnd(44), res.ok ? 'ОК ' : 'НЕТ', JSON.stringify(res));
        }
      }
    }
  }
  await browser.close();
})();
