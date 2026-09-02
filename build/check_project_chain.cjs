// Прогон сквозной практики через API: тем же кодом, что страница.
//
// Цепочка идёт как у участника: промпт шага собирается из разобранных ответов
// предыдущих шагов, ответ ассистента разбирается parseSx из project_core.js.
// Шаги 4 и 7 (анализ и поток эффекта) считает страница — здесь их считает
// то же ядро. Результат — build/runs/project/<модель>/<кейс>_<n>.md (все
// промпты и ответы подряд) и сводка build/runs/project/report.json.
//
// Запуск (ключ — только из окружения):
//   GIGACHAT_AUTH_KEY=$(secret get GIGA1_GIGACHAT_TOKEN) \
//   node build/check_project_chain.cjs --models GigaChat-2,GigaChat-2-Max --presets savings --runs 2
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const C = require('./src/project_core.js');
const PRESETS = JSON.parse(fs.readFileSync(path.join(__dirname, 'src/project_presets.json'), 'utf8'));

const args = process.argv.slice(2);
function opt(name, def) { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : def; }
const MODELS = opt('--models', 'GigaChat-2').split(',');
const PRESET_IDS = opt('--presets', 'savings').split(',');
const RUNS = parseInt(opt('--runs', '1'), 10);
const OUT = path.join(__dirname, 'runs', 'project');

function ask(prompt, model) {
  return execFileSync('python3', [path.join(__dirname, 'gigachat_cli.py'), model],
    { input: prompt, encoding: 'utf8', maxBuffer: 1 << 24, timeout: 300000 });
}

function metricsLines(m) {
  return ['result', 'd1', 'd2', 'control'].filter(k => m[k] && m[k].name)
    .map(k => '- ' + m[k].name + ' (' + C.or(m[k].unit, '—') + ', ' + C.or(m[k].freq, '—') + ') — ' +
      ({ result: 'результат', d1: 'драйвер', d2: 'драйвер', control: 'контрольная' })[k]).join('\n');
}

function runChain(pid, model, n) {
  const P = PRESETS[pid], T = P.table, log = [], score = {};
  const st = { s1: {}, s2: { metrics: {} }, s3: {}, s4: {}, s5: {}, s6: {}, s7: {}, s8: {}, s9: {} };
  function step(name, segs, vals, parser) {
    const pr = C.fillPrompt(segs, vals, 'fill').text;
    const t0 = Date.now();
    let resp = '';
    try { resp = ask(pr, model); } catch (e) { resp = 'ОШИБКА API: ' + String(e).slice(0, 200); }
    const sec = Math.round((Date.now() - t0) / 100) / 10;
    const parsed = parser(resp);
    log.push('\n\n## ' + name + ' (' + sec + ' с)\n\n### Промпт\n\n```\n' + pr + '\n```\n\n### Ответ\n\n```\n' + resp + '\n```\n\n### Разбор\n\n```json\n' + JSON.stringify(parsed, null, 1) + '\n```');
    return parsed;
  }
  // Шаг 1
  let r = step('Шаг 1 · объект и проблема', C.PROMPTS.s1, {
    axis: P.axis, object: P.object, observation: P.observation, action_in: P.action, source: P.source,
    table: C.tableText(T), focus: P.focus, facts: C.facts1(T, P.focus)
  }, C.parseS1);
  Object.assign(st.s1, r.fields); score.s1 = r.found + '/' + r.total;
  // Шаг 2
  r = step('Шаг 2 · метрики', C.PROMPTS.s2, {
    problem: st.s1.problem, action: st.s1.action, columns: C.numericCols(T).join(', '), other: P.other_metrics
  }, C.parseS2);
  st.s2.metrics = r.metrics; score.s2 = r.found + '/' + r.total;
  // Шаг 3
  r = step('Шаг 3 · данные', C.PROMPTS.s3, { metrics: metricsLines(st.s2.metrics), sources: P.sources, columns: C.numericCols(T).join(', ') }, C.parseS3);
  st.s3.rows = r.rows; score.s3 = r.found + ' строк';
  // Шаг 4 — считает страница
  const an = P.analysis.mode === 'pair' ? C.analysisPair(T, P.analysis.x, P.analysis.y) : C.analysisTrend(T, P.analysis.y);
  st.s4 = an; log.push('\n\n## Шаг 4 · анализ (страница)\n\n' + an.text);
  // Шаг 5
  r = step('Шаг 5 · вывод', C.PROMPTS.s5, { problem: st.s1.problem, action: st.s1.action, analysis: an.text, n: String(an.n) }, C.parseS5);
  Object.assign(st.s5, r.fields); score.s5 = r.found + '/' + r.total;
  // Шаг 6
  const F = P.fin;
  r = step('Шаг 6 · допущения', C.PROMPTS.s6, {
    problem: st.s1.problem, hyp: st.s5.hyp,
    fdelta: C.fmtv(F.delta), udelta: F.delta_unit, sdelta: 'гипотеза проекта (допущение)',
    fvolume: C.fmtv(F.volume), uvolume: F.volume_unit, svolume: 'данные выгрузки',
    fprice: C.fmtv(F.price), uprice: F.price_unit, sprice: 'допущение по тарифу',
    fkeep: String(F.keep), skeep: 'допущение'
  }, C.parseS6);
  st.s6 = r.ass; score.s6 = r.found + '/' + r.total;
  const numsOk = ['delta', 'volume', 'price', 'keep'].filter(k => r.ass[k] && r.ass[k].pess !== null && r.ass[k].opt !== null).length;
  score.s6nums = numsOk + '/4';
  // Шаг 7 — считает страница
  const p = { kind: F.kind, delta: F.delta, volume: F.volume, price: F.price, ramp: F.ramp, keep: F.keep, capex: F.capex, opex: F.opex, horizon: F.horizon, rate: F.rate };
  const ass = [];
  ['delta', 'volume', 'price', 'keep'].forEach(k => {
    const a = r.ass[k]; if (!a || a.pess === null || a.opt === null) return;
    ass.push({ key: k, name: { delta: 'Изменение показателя', volume: 'Объём', price: 'Стоимость единицы', keep: 'Срок сохранения' }[k], pess: a.pess, opt: a.opt });
  });
  ass.push({ key: 'capex', name: 'Единовременные затраты', pess: F.capex * 1.5, opt: F.capex * 0.75 });
  ass.push({ key: 'opex', name: 'Ежемесячные затраты', pess: F.opex * 1.6, opt: F.opex * 0.7 });
  const res = C.totals(p), sens = C.sensitivity(p, ass);
  st.s7.text = C.effectText(p, { delta: F.delta_unit, volume: F.volume_unit, price: F.price_unit }, res, sens);
  log.push('\n\n## Шаг 7 · поток эффекта (страница)\n\n' + st.s7.text);
  // Шаг 8
  r = step('Шаг 8 · слайд', C.PROMPTS.s8, { problem: st.s1.problem, hyp: st.s5.hyp, effect: st.s7.text }, C.parseS8);
  Object.assign(st.s8, r.fields); score.s8 = r.found + '/' + r.total;
  // Шаг 9
  const missing = (st.s3.rows || []).filter(x => x.status !== 'есть').map(x => x.metric + ' (' + x.status + ': ' + x.source + ')').join('; ') || 'нет';
  r = step('Шаг 9 · письмо', C.PROMPTS.s9, {
    problem: st.s1.problem, action: st.s1.action,
    result: st.s2.metrics.result ? st.s2.metrics.result.name : '', target: st.s1.target,
    control: st.s2.metrics.control ? st.s2.metrics.control.name : '', missing: missing,
    hyp: st.s5.hyp, refute: st.s5.refute, seffect: st.s8.result, risk: st.s8.risk, first: st.s8.action
  }, C.parseS9);
  Object.assign(st.s9, r.fields); score.s9 = r.found + '/' + r.total;
  return { score, log: log.join(''), st };
}

fs.mkdirSync(OUT, { recursive: true });
const reportFile = path.join(OUT, 'report.json');
const report = fs.existsSync(reportFile) ? JSON.parse(fs.readFileSync(reportFile, 'utf8')) : {};
for (const model of MODELS) {
  fs.mkdirSync(path.join(OUT, model), { recursive: true });
  for (const pid of PRESET_IDS) {
    for (let n = 1; n <= RUNS; n++) {
      const t0 = Date.now();
      const { score, log } = runChain(pid, model, n);
      const file = path.join(OUT, model, pid + '_' + n + '.md');
      fs.writeFileSync(file, '# ' + model + ' · ' + PRESETS[pid].tab + ' · прогон ' + n + '\n' + log);
      const key = model + '/' + pid + '_' + n;
      report[key] = Object.assign({ sec: Math.round((Date.now() - t0) / 1000) }, score);
      fs.writeFileSync(reportFile, JSON.stringify(report, null, 1));
      console.log(key.padEnd(30), JSON.stringify(score), report[key].sec + ' с');
    }
  }
}
