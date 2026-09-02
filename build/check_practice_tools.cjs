// Узкое звено практики: соберёт ли ассистент мини-инструмент на нескольких CSV
// и мини-инструмент финансовой модели с SVG — и будут ли они считать верно.
//
// Для каждой модели и прогона: промпт → ответ → HTML в build/runs/practice/
// <модель>/tool_<вариант>_<n>.html → открыть в браузере, загрузить выбранные
// CSV в поле файла, прочитать текст страницы и сверить параметры с ожидаемыми
// (из описания варианта). То же для NPV-инструмента: сверка окупаемости и NPV
// с расчётом ядра. Сводка — build/runs/practice/report.json.
//
//   GIGACHAT_AUTH_KEY=$(secret get GIGA1_GIGACHAT_TOKEN) node build/check_practice_tools.cjs \
//     --models GigaChat-2,GigaChat-2-Max --runs 3 --variant prod1 --chosen dm,crm,fin --what tool,npv
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const puppeteer = require('puppeteer-core');
const C = require('./src/practice_core.js');
const VARIANTS = JSON.parse(fs.readFileSync(path.join(__dirname, 'src/practice_variants.json'), 'utf8'));
const ROOT = path.join(__dirname, '..');
const OUT = path.join(__dirname, 'runs', 'practice');

const args = process.argv.slice(2);
function opt(name, def) { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : def; }
const MODELS = opt('--models', 'GigaChat-2').split(',');
const RUNS = parseInt(opt('--runs', '1'), 10);
const VID = opt('--variant', 'prod1');
const WHAT = opt('--what', 'tool,npv').split(',');
const V = VARIANTS.filter(v => v.id === VID)[0];
const chosenIds = opt('--chosen', V.inputs.map(i => i.sources[0].id).join(',')).split(',');
const chosen = {}; V.inputs.forEach((inp, i) => { chosen[inp.id] = chosenIds[i]; });

function ask(prompt, model) {
  return execFileSync('python3', [path.join(__dirname, 'gigachat_cli.py'), model], { input: prompt, encoding: 'utf8', maxBuffer: 1 << 24, timeout: 300000 });
}
function near(a, b, rel) { return Math.abs(a - b) <= Math.abs(b) * (rel || 0.03) + 1e-9; }

async function openAndRead(browser, file, uploads) {
  const p = await browser.newPage(); const errs = [];
  p.on('pageerror', e => errs.push(String(e).slice(0, 200)));
  p.on('console', m => { if (m.type() === 'error') errs.push(m.text().slice(0, 200)); });
  p.on('dialog', d => { errs.push('dialog: ' + d.message().slice(0, 120)); d.dismiss().catch(() => {}); });
  await p.goto('file://' + file, { waitUntil: 'load' });
  if (uploads && uploads.length) {
    const has = await p.$('input[type=file]');
    if (!has) { await p.close(); return { text: '', errs: errs.concat(['нет input[type=file]']), svg: false }; }
    // Файлы подкладываются через DataTransfer: CDP-загрузка на file:// зависает.
    const payload = uploads.map(f => ({ name: path.basename(f), text: fs.readFileSync(f, 'utf8') }));
    await p.evaluate(list => {
      const inp = document.querySelector('input[type=file]');
      const dt = new DataTransfer();
      list.forEach(f => dt.items.add(new File([f.text], f.name, { type: 'text/csv' })));
      inp.files = dt.files;
      inp.dispatchEvent(new Event('input', { bubbles: true }));
      inp.dispatchEvent(new Event('change', { bubbles: true }));
    }, payload);
    await new Promise(r => setTimeout(r, 1500));
    // если есть кнопка «рассчитать» — нажать
    await p.evaluate(() => { const b = Array.from(document.querySelectorAll('button')).find(x => /рассчит|посчит|загруз/i.test(x.textContent)); if (b) b.click(); });
    await new Promise(r => setTimeout(r, 800));
  } else {
    await new Promise(r => setTimeout(r, 800));
    const btn = await p.$('button');
    if (btn) { try { await btn.click(); } catch (e) { } await new Promise(r => setTimeout(r, 500)); }
  }
  const text = await p.evaluate(() => document.body.innerText);
  const svg = await p.evaluate(() => !!document.querySelector('svg'));
  const saveBtn = await p.evaluate(() => Array.from(document.querySelectorAll('button,a')).some(b => /svg/i.test(b.textContent)));
  await p.close();
  return { text, errs, svg, saveBtn };
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const reportFile = path.join(OUT, 'report.json');
  const report = fs.existsSync(reportFile) ? JSON.parse(fs.readFileSync(reportFile, 'utf8')) : {};
  const browser = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const files = {}; const uploads = [];
  V.inputs.forEach(inp => inp.sources.forEach(s => { files[s.file] = { text: fs.readFileSync(path.join(ROOT, 'practice_data', V.id, s.file), 'utf8') }; }));
  V.inputs.forEach(inp => { const s = inp.sources.filter(x => x.id === chosen[inp.id])[0]; uploads.push(path.join(ROOT, 'practice_data', V.id, s.file)); });
  const expected = {}; V.inputs.forEach(inp => { expected[inp.id] = inp.sources.filter(x => x.id === chosen[inp.id])[0].expect; });
  const expDelta = expected.closures * expected.linked / 3;
  for (const model of MODELS) {
    fs.mkdirSync(path.join(OUT, model), { recursive: true });
    for (let n = 1; n <= RUNS; n++) {
      if (WHAT.includes('tool')) {
        const key = model + '/tool_' + VID + '_' + chosenIds.join('-') + '_' + n;
        const pr = C.toolPrompt(V, chosen, files);
        const t0 = Date.now(); let resp = '';
        try { resp = ask(pr, model); } catch (e) { resp = 'ОШИБКА API ' + e; }
        const html = C.extractHtml(resp);
        const base = path.join(OUT, model, 'tool_' + VID + '_' + chosenIds.join('-') + '_' + n);
        fs.writeFileSync(base + '.md', '# промпт\n\n```\n' + pr + '\n```\n\n# ответ\n\n' + resp);
        let res = { sec: Math.round((Date.now() - t0) / 1000), html: !!html };
        if (html) {
          fs.writeFileSync(base + '.html', html);
          const r = await openAndRead(browser, base + '.html', uploads);
          const pp = C.parseParams(r.text);
          res.errors = r.errs.length; res.err0 = r.errs[0] || '';
          res.params = pp; res.svg = r.svg;
          res.deltaOk = !!(pp && near(pp.delta, expDelta, 0.05));
          res.priceOk = !!(pp && near(pp.price, expected.margin, 0.03));
          res.ok = res.deltaOk && res.priceOk && r.errs.length === 0;
          res.textLen = r.text.length;
          fs.writeFileSync(base + '.txt', r.text);
        } else res.ok = false;
        report[key] = res; fs.writeFileSync(reportFile, JSON.stringify(report, null, 1));
        console.log(key.padEnd(46), res.ok ? 'ОК ' : 'НЕТ', JSON.stringify(res));
      }
      if (WHAT.includes('npv')) {
        const key = model + '/npv_' + VID + '_' + n;
        const np = C.npvPrompt(V, { delta: 100, volume: 1, price: 550 });
        const t0 = Date.now(); let resp = '';
        try { resp = ask(np.text, model); } catch (e) { resp = 'ОШИБКА API ' + e; }
        const html = C.extractHtml(resp);
        const base = path.join(OUT, model, 'npv_' + VID + '_' + n);
        fs.writeFileSync(base + '.md', '# промпт\n\n```\n' + np.text + '\n```\n\n# ответ\n\n' + resp);
        let res = { sec: Math.round((Date.now() - t0) / 1000), html: !!html };
        if (html) {
          fs.writeFileSync(base + '.html', html);
          const r = await openAndRead(browser, base + '.html', null);
          res.errors = r.errs.length; res.err0 = r.errs[0] || ''; res.svg = r.svg; res.saveBtn = r.saveBtn;
          const t = r.text.replace(/[\s  ]/g, '');
          // NPV ≈ 8 034 655 → ищем 8034655 / 8 034 655 / 8,03 млн / 8 034 тыс
          const npvStr = Math.round(np.expect.npv);
          res.npvOk = t.indexOf(String(npvStr).slice(0, 4)) >= 0 || /8,0[0-9]млн/.test(t);
          res.paybackOk = new RegExp('(Окупаемость[^0-9]{0,30}' + np.expect.payback + '\\b)|(\\b' + np.expect.payback + '[^0-9]{0,10}мес)', 'i').test(r.text);
          res.ok = res.npvOk && res.paybackOk && r.svg && r.saveBtn && r.errs.length === 0;
          fs.writeFileSync(base + '.txt', r.text);
        } else res.ok = false;
        report[key] = res; fs.writeFileSync(reportFile, JSON.stringify(report, null, 1));
        console.log(key.padEnd(46), res.ok ? 'ОК ' : 'НЕТ', JSON.stringify(res));
      }
    }
  }
  await browser.close();
})();
