# -*- coding: utf-8 -*-
"""Каркасы мини-инструментов практики: по два файла на вариант.

Схема та же, что в практике занятия 3 (SA-7): готовая страница читает
файлы и рисует результат, а ассистент пишет только модуль расчёта рядом.
Каркас никогда не молчит: нет модуля — объясняет, что положить рядом;
ошибка в модуле — печатает готовое сообщение для ассистента.

  practice_data/<вариант>/инструмент_параметров.html  + rasschet.js от ассистента
      читает выбранные CSV (кнопка «выбрать файлы», несколько сразу),
      вызывает window.computeInputs(tables) → входы дерева, считает параметры
      delta / volume / price по формулам варианта, рисует график входа по
      месяцам, даёт строку «delta=…; volume=…; price=…» с кнопкой копирования.

  practice_data/<вариант>/финмодель.html  + model.js от ассистента
      поля параметров и условий, вызывает window.effectFlows(p) → строки
      по месяцам, считает окупаемость, NPV, доход за первый год, рисует SVG
      (столбики дохода, накопленный поток, дисконтированный), кнопка
      «Сохранить SVG».

Запуск: python3 build/practice_shells.py (после practice_variants.py).
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "practice_data"
VARIANTS = json.loads((ROOT / "build" / "src" / "practice_variants.json").read_text(encoding="utf-8"))

CSS = """
  body{margin:0;background:#fff;color:#2E3641;font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;font-size:16px;line-height:1.5}
  .wrap{max-width:960px;margin:0 auto;padding:24px 18px}
  h1{font-size:23px;margin:0 0 4px} h3{margin:0 0 10px;font-size:17px}
  .sub{color:#6B7580;margin:0 0 18px;font-size:14.5px}
  .card{border:1px solid #e6ecf1;border-radius:14px;padding:16px 18px;margin:0 0 14px}
  .tiles{display:flex;flex-wrap:wrap;gap:18px}
  .tile{min-width:180px}.tile .num{font-size:28px;font-weight:800;line-height:1.1}.tile .lab{color:#6B7580;font-size:13px;margin-top:3px}
  table{border-collapse:collapse;width:100%;font-size:14px}td,th{border-bottom:1px solid #e6ecf1;padding:6px 9px;text-align:left}
  .warn{color:#E4572E}.ok{color:#128a53}
  pre{background:#20262e;color:#e7edf3;border-radius:10px;padding:12px 14px;font-size:13px;white-space:pre-wrap;word-break:break-word}
  button{background:#20BA72;color:#fff;border:0;border-radius:9px;padding:8px 16px;font:inherit;font-weight:700;cursor:pointer}
  button.sec{background:#f4f8f6;color:#2E3641;border:1px solid #d9e2dd;font-weight:600}
  input[type=text],input[type=number]{font:inherit;padding:6px 9px;border:1px solid #d9e2dd;border-radius:8px;width:150px}
  label{display:inline-block;margin:0 14px 8px 0;font-size:14px}label span{display:block;color:#6B7580;font-size:12.5px}
  svg{width:100%;height:auto;display:block}
  .files span{display:inline-block;margin:0 8px 6px 0;padding:3px 10px;border-radius:999px;background:#f4f8f6;border:1px solid #d9e2dd;font-size:13.5px}
  .files span.got{background:#e3f2ea;border-color:#20BA72}
  .line{font-family:ui-monospace,Consolas,monospace;background:#f4f8f6;border:1px solid #d9e2dd;border-radius:8px;padding:8px 10px;display:inline-block;margin:6px 8px 6px 0}
"""

TOOL = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Мини-инструмент: параметры проекта · {title}</title>
<style>{css}</style></head><body><div class="wrap">
<h1>Параметры проекта: {title}</h1>
<p class="sub">Каркас мини-инструмента. Расчёт входов — в файле <b>rasschet.js</b>, который пишет ассистент и который лежит рядом с этим файлом.
Выберите файлы выбранных источников одной кнопкой — инструмент посчитает входы, параметры и итоговую метрику. Данные никуда не отправляются.</p>
<div class="card"><h3>1 · Файлы источников</h3>
<input type="file" id="files" multiple accept=".csv">
<div class="files" id="expected" style="margin-top:10px"></div>
<p id="status" class="warn" style="margin:8px 0 0"></p></div>
<div class="card" id="result" style="display:none"><h3>2 · Входы дерева</h3><table id="inputs"></table></div>
<div class="card" id="params" style="display:none"><h3>3 · Параметры финансовой модели</h3>
<div class="tiles" id="tiles"></div>
<p style="margin:14px 0 4px"><b>Итоговая метрика:</b> <span id="metric"></span></p>
<p style="margin:8px 0 0"><span class="line" id="line"></span><button type="button" id="copy">Копировать параметры</button></p>
<p class="sub" style="margin:8px 0 0">Строку параметров вставьте в тренажёр на шаге «Параметры из инструмента».</p></div>
<div class="card" id="chartCard" style="display:none"><h3>4 · Вход по месяцам</h3><div id="chart"></div></div>
</div>
<script>
var META = {meta};
var tables = {{}};
function parseCsv(text) {{
  var lines = String(text).replace(/^\\uFEFF/, '').split(/\\r?\\n/).filter(function (l) {{ return l.trim() !== ''; }});
  if (!lines.length) return [];
  var head = lines[0].split(';').map(function (h) {{ return h.trim(); }});
  var rows = [];
  for (var i = 1; i < lines.length; i++) {{
    var cells = lines[i].split(';'), row = {{}};
    for (var j = 0; j < head.length; j++) {{
      var v = (cells[j] === undefined ? '' : cells[j]).trim();
      var n = parseFloat(v.replace(',', '.'));
      row[head[j]] = (v !== '' && !isNaN(n) && /^-?[\\d\\s]+([.,]\\d+)?$/.test(v)) ? n : v;
    }}
    rows.push(row);
  }}
  return rows;
}}
function fmt(v) {{
  if (v === null || v === undefined || isNaN(v)) return '—';
  var a = Math.abs(v);
  if (a >= 1000) return Math.round(v).toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ' ');
  return String(Math.round(v * 10000) / 10000).replace('.', ',');
}}
function evalFormula(f, vals) {{
  var s = String(f);
  Object.keys(vals).forEach(function (k) {{ s = s.replace(new RegExp('\\\\b' + k + '\\\\b', 'g'), '(' + vals[k] + ')'); }});
  s = s.replace(/×/g, '*').replace(/÷/g, '/');
  if (!/^[\\d\\s().*\\/+\\-]+$/.test(s)) return NaN;
  try {{ return Function('return (' + s + ')')(); }} catch (e) {{ return NaN; }}
}}
function renderExpected() {{
  document.getElementById('expected').innerHTML = META.inputs.map(function (i) {{
    return '<div style="margin:0 0 6px"><b style="font-size:13.5px">' + i.name + ':</b> ' + META.files.filter(function (f) {{ return f.id === i.id; }}).map(function (f) {{
      return '<span class="' + (tables[f.file] ? 'got' : '') + '">' + (tables[f.file] ? '✓ ' : '') + f.file + '</span>';
    }}).join(' или ') + '</div>';
  }}).join('');
}}
function setStatus(t, ok) {{ var s = document.getElementById('status'); s.textContent = t; s.className = ok ? 'ok' : 'warn'; }}
function compute() {{
  renderExpected();
  var missing = META.inputs.filter(function (i) {{ return !META.files.some(function (f) {{ return f.id === i.id && tables[f.file]; }}); }});
  if (missing.length) {{ setStatus('Ожидаются файлы для входов: ' + missing.map(function (i) {{ return i.id + ' (' + META.files.filter(function (f) {{ return f.id === i.id; }}).map(function (f) {{ return f.file; }}).join(' или ') + ')'; }}).join('; '), false); return; }}
  // Контрольный расчёт каркаса — по загруженным файлам, формулы источников известны.
  var ref = {{}};
  META.inputs.forEach(function (i) {{
    var f = META.files.filter(function (x) {{ return x.id === i.id && tables[x.file]; }})[0];
    try {{ ref[i.id] = Function('rows', META.ref[f.file])(tables[f.file]); }} catch (e) {{ ref[i.id] = null; }}
  }});
  var inputs = null, note = '';
  if (typeof window.computeInputs !== 'function') {{
    note = 'Рядом с этим файлом нет rasschet.js или в нём не объявлена функция window.computeInputs. Показан контрольный расчёт каркаса; сохраните ответ ассистента как rasschet.js в эту папку и обновите страницу, чтобы сверить его расчёт.';
  }} else {{
    try {{ inputs = window.computeInputs(tables); }}
    catch (e) {{ note = 'Ошибка в rasschet.js: ' + e.message + '. Скопируйте ассистенту: «В функции computeInputs ошибка: ' + e.message + '. Исправь и верни файл целиком». Показан контрольный расчёт каркаса.'; inputs = null; }}
  }}
  var t = '<tr><th>Вход</th><th>Расчёт ассистента</th><th>Контрольный расчёт</th><th>Сверка</th><th>Единица</th><th>Файл</th></tr>';
  var mismatch = [], missing = [];
  META.inputs.forEach(function (i) {{
    var used = META.files.filter(function (f) {{ return f.id === i.id && tables[f.file]; }}).map(function (f) {{ return f.file; }}).join(', ');
    var a = inputs ? inputs[i.id] : null, r = ref[i.id], ok = null;
    if (a === null || a === undefined || isNaN(a)) {{ if (inputs) missing.push(i.id); }}
    else if (r !== null && !isNaN(r)) {{ ok = Math.abs(a - r) <= Math.abs(r) * 0.02 + 1e-9; if (!ok) mismatch.push(i.id); }}
    t += '<tr><td>' + i.name + ' (' + i.id + ')</td><td><b>' + fmt(a) + '</b></td><td>' + fmt(r) + '</td><td>' + (ok === null ? '—' : ok ? '<span class="ok">совпадает</span>' : '<span class="warn">расходится</span>') + '</td><td>' + i.unit + '</td><td>' + used + '</td></tr>';
  }});
  document.getElementById('inputs').innerHTML = t; document.getElementById('result').style.display = '';
  if (inputs && missing.length) note = 'Функция computeInputs не вернула значения для: ' + missing.join(', ') + '. Скопируйте ассистенту: «computeInputs возвращает не все входы; нужны поля ' + META.inputs.map(function (i) {{ return i.id; }}).join(', ') + '». Для этих входов взят контрольный расчёт.';
  else if (inputs && mismatch.length) note = 'Расчёт ассистента расходится с контрольным для: ' + mismatch.join(', ') + '. Скопируйте ассистенту: «Для входов ' + mismatch.join(', ') + ' результат отличается от контрольного; проверь формулу и верни файл целиком». В параметры взят контрольный расчёт.';
  else if (inputs) note = 'Файлы загружены; расчёт ассистента совпадает с контрольным.';
  setStatus(note, !!inputs && !missing.length && !mismatch.length);
  var vals = {{}}; META.inputs.forEach(function (i) {{ var a = inputs ? inputs[i.id] : null; var good = a !== null && a !== undefined && !isNaN(a) && mismatch.indexOf(i.id) < 0; vals[i.id] = good ? a : ref[i.id]; }});
  var p = {{}}; ['delta', 'volume', 'price'].forEach(function (k) {{ p[k] = evalFormula(META.params[k].formula, vals); }});
  document.getElementById('tiles').innerHTML = ['delta', 'volume', 'price'].map(function (k) {{
    return '<div class="tile"><div class="num">' + fmt(p[k]) + '</div><div class="lab">' + META.params[k].name + '<br>' + META.params[k].unit + '<br><span style="opacity:.7">' + k + ' = ' + META.params[k].formula + '</span></div></div>';
  }}).join('');
  document.getElementById('metric').textContent = META.metric.name + ' = ' + fmt(p.delta * p.volume * p.price) + ' ' + META.metric.unit;
  var line = 'delta=' + (Math.round(p.delta * 10000) / 10000) + '; volume=' + (Math.round(p.volume * 10000) / 10000) + '; price=' + (Math.round(p.price * 10000) / 10000);
  document.getElementById('line').textContent = line; document.getElementById('params').style.display = '';
  document.getElementById('copy').onclick = function () {{
    var b = this; function done() {{ b.textContent = 'Скопировано'; setTimeout(function () {{ b.textContent = 'Копировать параметры'; }}, 1800); }}
    function fb() {{ var a = document.createElement('textarea'); a.value = line; document.body.appendChild(a); a.select(); try {{ document.execCommand('copy'); done(); }} catch (e) {{ b.textContent = 'Выделите строку вручную'; }} document.body.removeChild(a); }}
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(line).then(done, fb); else fb();
  }};
  drawChart();
}}
function drawChart() {{
  var f = META.files[0], rows = tables[f.file] || [];
  if (!rows.length || rows[0]['месяц'] === undefined) {{ document.getElementById('chartCard').style.display = 'none'; return; }}
  var col = null; Object.keys(rows[0]).forEach(function (k) {{ if (!col && k !== 'месяц' && typeof rows[0][k] === 'number') col = k; }});
  if (!col) return;
  var byMonth = {{}}, order = [];
  rows.forEach(function (r) {{ var m = String(r['месяц']); if (byMonth[m] === undefined) {{ byMonth[m] = 0; order.push(m); }} byMonth[m] += (typeof r[col] === 'number' ? r[col] : 0); }});
  var ys = order.map(function (m) {{ return byMonth[m]; }});
  var W = 960, H = 280, L = 70, R = 20, T = 20, B = 44, pw = W - L - R, ph = H - T - B, n = ys.length;
  var mx = Math.max.apply(null, ys), mn = Math.min.apply(null, ys); if (mx === mn) {{ mx += 1; mn -= 1; }}
  var pad = (mx - mn) * 0.1; mx += pad; mn = Math.max(0, mn - pad);
  var X = function (i) {{ return L + (n > 1 ? pw * i / (n - 1) : pw / 2); }}, Y = function (v) {{ return T + ph * (mx - v) / (mx - mn); }};
  var s = '<svg viewBox="0 0 ' + W + ' ' + H + '" xmlns="http://www.w3.org/2000/svg">';
  var d = ''; ys.forEach(function (v, i) {{ d += (i ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(v).toFixed(1) + ' '; }});
  s += '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + Y(mn) + '" y2="' + Y(mn) + '" stroke="#2E3641" stroke-opacity="0.3"/>';
  s += '<path d="' + d + '" fill="none" stroke="#159A5C" stroke-width="3"/>';
  ys.forEach(function (v, i) {{ s += '<circle cx="' + X(i).toFixed(1) + '" cy="' + Y(v).toFixed(1) + '" r="3.2" fill="#159A5C"/>'; }});
  s += '<text x="' + (L - 8) + '" y="' + (Y(mx - pad) + 4) + '" font-size="12" text-anchor="end" fill="#2E3641">' + fmt(Math.max.apply(null, ys)) + '</text>';
  s += '<text x="' + (L - 8) + '" y="' + (Y(mn + (mn ? pad : 0)) + 4) + '" font-size="12" text-anchor="end" fill="#2E3641">' + fmt(Math.min.apply(null, ys)) + '</text>';
  var every = Math.max(1, Math.ceil(n / 12));
  order.forEach(function (m, i) {{ if (i % every === 0 || i === n - 1) s += '<text x="' + X(i).toFixed(1) + '" y="' + (H - B + 18) + '" font-size="11.5" text-anchor="middle" fill="#2E3641" fill-opacity="0.75">' + m + '</text>'; }});
  s += '<text x="' + L + '" y="' + (H - 8) + '" font-size="12.5" font-weight="700" fill="#2E3641">' + col + ' — ' + f.file + '</text></svg>';
  document.getElementById('chart').innerHTML = s; document.getElementById('chartCard').style.display = '';
}}
document.getElementById('files').addEventListener('change', function () {{
  var list = Array.prototype.slice.call(this.files || []), left = list.length;
  if (!left) return;
  list.forEach(function (file) {{
    var known = META.files.some(function (f) {{ return f.file === file.name; }});
    var rd = new FileReader();
    rd.onload = function () {{ if (known) tables[file.name] = parseCsv(rd.result); else setStatus('Файл не из списка: ' + file.name, false); if (--left === 0) compute(); }};
    rd.readAsText(file, 'utf-8');
  }});
}});
renderExpected(); compute();
</script>
<script src="rasschet.js"></script>
<script>compute();</script>
</body></html>
"""

NPV = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Мини-инструмент: финансовая модель · {title}</title>
<style>{css}</style></head><body><div class="wrap">
<h1>Финансовая модель эффекта: {title}</h1>
<p class="sub">Каркас мини-инструмента. Расчёт потока по месяцам — в файле <b>model.js</b>, который пишет ассистент и который лежит рядом.
Введите параметры проекта из инструмента параметров, проверьте условия и нажмите «Рассчитать».</p>
<div class="card"><h3>1 · Параметры и условия</h3>
<div id="form"></div>
<button type="button" id="calc">Рассчитать</button>
<p id="status" class="warn" style="margin:8px 0 0"></p></div>
<div class="card" id="res" style="display:none"><h3>2 · Результат</h3>
<div class="tiles" id="tiles"></div>
<div id="chart" style="margin-top:14px"></div>
<p style="margin:12px 0 0"><button type="button" id="save">Сохранить SVG</button> <span class="sub">Файл npv.svg загружается в тренажёр на шаге «Финансовая модель».</span></p>
</div>
<div class="card" id="tab" style="display:none"><h3>3 · Поток по месяцам</h3><div style="overflow-x:auto"><table id="rows"></table></div></div>
</div>
<script>
var META = {meta};
var FIELDS = [['delta', 'Изменение показателя в месяц', META.units.delta], ['volume', 'Объём', META.units.volume], ['price', 'Стоимость единицы, руб. в месяц', META.units.price],
  ['ramp', 'Выход на полный уровень, мес.', ''], ['keep', 'Срок сохранения эффекта, мес.', ''], ['capex', 'Единовременные затраты, руб.', ''],
  ['opex', 'Ежемесячные затраты, руб.', ''], ['horizon', 'Горизонт, мес.', ''], ['rate', 'Ставка дисконтирования, доля в год', '']];
function num(v) {{ var n = parseFloat(String(v).replace(/\\s/g, '').replace(',', '.')); return isNaN(n) ? 0 : n; }}
function money(x) {{ var a = Math.abs(x), s; if (a >= 1e6) s = (a / 1e6).toFixed(a >= 1e7 ? 1 : 2).replace('.', ',') + ' млн руб.'; else if (a >= 1e4) s = Math.round(a / 1e3).toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ' ') + ' тыс. руб.'; else s = Math.round(a).toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ' ') + ' руб.'; return (x < 0 ? '−' : '') + s; }}
function form() {{
  document.getElementById('form').innerHTML = FIELDS.map(function (f) {{
    return '<label>' + f[1] + '<span>' + (f[2] || '&nbsp;') + '</span><input type="text" id="f-' + f[0] + '" value="' + META.defaults[f[0]] + '"></label>';
  }}).join('');
}}
function params() {{ var p = {{ kind: META.kind }}; FIELDS.forEach(function (f) {{ p[f[0]] = num(document.getElementById('f-' + f[0]).value); }}); return p; }}
function setStatus(t, ok) {{ var s = document.getElementById('status'); s.textContent = t; s.className = ok ? 'ok' : 'warn'; }}
// Контрольный расчёт каркаса — те же формулы, что в материале «Финансовая модель проекта».
function refFlows(p) {{
  var H = Math.round(p.horizon), full = p.delta * p.volume, m = Math.pow(1 + p.rate, 1 / 12) - 1, rows = [], cum = 0, cumd = 0;
  function ramp(t) {{ return p.ramp <= 0 ? 1 : Math.min(t / p.ramp, 1); }}
  for (var t = 0; t <= H; t++) {{
    var inc = 0, units = 0, cost = t === 0 ? p.capex : p.opex;
    if (t >= 1) {{ if (p.kind === 'cohort') {{ for (var k = Math.max(1, t - p.keep + 1); k <= t; k++) units += full * ramp(k); }} else units = t <= p.keep ? full * ramp(t) : 0; inc = units * p.price; }}
    var cf = inc - cost; cum += cf; var disc = cf / Math.pow(1 + m, t); cumd += disc;
    rows.push({{ t: t, income: inc, cost: cost, cf: cf, cum: cum, disc: disc, cum_disc: cumd }});
  }}
  return rows;
}}
function summary(rows) {{ var pb = null, y1 = 0; rows.forEach(function (r) {{ if (r.t > 0 && pb === null && r.cum >= 0) pb = r.t; if (r.t >= 1 && r.t <= 12) y1 += r.income; }}); return {{ pb: pb, y1: y1, npv: rows[rows.length - 1].cum_disc }}; }}
function calc() {{
  var p = params(), ref = refFlows(p), rs = summary(ref), rows = null, note = '';
  if (typeof window.effectFlows !== 'function') {{
    note = 'Рядом с этим файлом нет model.js или в нём не объявлена функция window.effectFlows. Показан контрольный расчёт каркаса; сохраните ответ ассистента как model.js в эту папку и обновите страницу, чтобы сверить его расчёт.';
  }} else {{
    try {{ rows = window.effectFlows(p); }} catch (e) {{ note = 'Ошибка в model.js: ' + e.message + '. Скопируйте ассистенту: «В функции effectFlows ошибка: ' + e.message + '. Исправь и верни файл целиком». Показан контрольный расчёт.'; rows = null; }}
    if (rows && (!rows.length || rows.length !== Math.round(p.horizon) + 1 || typeof rows[0].cum !== 'number' || typeof rows[rows.length - 1].cum_disc !== 'number')) {{ note = 'effectFlows должна вернуть массив из horizon + 1 строк с полями t, income, cost, cf, cum, cum_disc — скопируйте это ассистенту. Показан контрольный расчёт.'; rows = null; }}
  }}
  var ms = rows ? summary(rows) : null, agree = ms && Math.abs(ms.npv - rs.npv) <= Math.abs(rs.npv) * 0.02 + 1 && ms.pb === rs.pb;
  if (rows && !note) note = agree ? 'Расчёт ассистента совпадает с контрольным расчётом каркаса.' : 'Расчёт ассистента расходится с контрольным: NPV ' + money(ms.npv) + ' против ' + money(rs.npv) + ', окупаемость ' + (ms.pb === null ? 'не достигается' : 'месяц ' + ms.pb) + ' против ' + (rs.pb === null ? 'не достигается' : 'месяца ' + rs.pb) + '. Скопируйте ассистенту: «Результат effectFlows отличается от контрольного; проверь формулу units(t) для когорт и дисконтирование, верни файл целиком». На графике — контрольный расчёт.';
  setStatus(note, !!rows && agree);
  var s = rs;
  document.getElementById('tiles').innerHTML = '<div class="tile"><div class="num">' + money(s.y1) + '</div><div class="lab">Доход за первый год' + (ms ? '<br>расчёт ассистента: ' + money(ms.y1) : '') + '</div></div>' +
    '<div class="tile"><div class="num">' + (s.pb === null ? 'не достигается' : 'месяц ' + s.pb) + '</div><div class="lab">Окупаемость' + (ms ? '<br>расчёт ассистента: ' + (ms.pb === null ? 'не достигается' : 'месяц ' + ms.pb) : '') + '</div></div>' +
    '<div class="tile"><div class="num">' + money(s.npv) + '</div><div class="lab">NPV за ' + Math.round(p.horizon) + ' мес. при ставке ' + (p.rate * 100).toFixed(1).replace('.', ',') + ' %' + (ms ? '<br>расчёт ассистента: ' + money(ms.npv) : '') + '</div></div>';
  var pb = s.pb; rows = ref;
  document.getElementById('chart').innerHTML = chart(rows, pb, Math.round(p.horizon));
  var t = '<tr><th>Мес.</th><th>Доход</th><th>Затраты</th><th>Поток</th><th>Накопленный</th><th>Накопленный дисконтированный</th></tr>';
  rows.forEach(function (r) {{ t += '<tr><td>' + r.t + '</td><td>' + money(r.income) + '</td><td>' + money(r.cost) + '</td><td>' + money(r.cf) + '</td><td>' + money(r.cum) + '</td><td>' + money(r.cum_disc) + '</td></tr>'; }});
  document.getElementById('rows').innerHTML = t; document.getElementById('res').style.display = ''; document.getElementById('tab').style.display = '';
}}
function chart(rows, pb, H) {{
  var W = 960, HH = 340, L = 78, R = 48, T = 18, B = 44, pw = W - L - R, ph = HH - T - B, mx = 0, mn = 0;
  rows.forEach(function (r) {{ mx = Math.max(mx, r.cum, r.income); mn = Math.min(mn, r.cum, -r.cost); }}); if (mx === mn) {{ mx = 1; mn = -1; }}
  var pad = (mx - mn) * 0.08; mx += pad; mn -= pad;
  var y = function (v) {{ return T + ph * (mx - v) / (mx - mn); }}, x = function (t) {{ return L + pw * t / H; }}, bw = Math.max(3, pw / (H + 1) * 0.34), s = [];
  s.push('<svg viewBox="0 0 ' + W + ' ' + HH + '" xmlns="http://www.w3.org/2000/svg" font-family="system-ui, Segoe UI, Roboto, Arial, sans-serif">');
  s.push('<rect x="0" y="0" width="' + W + '" height="' + HH + '" fill="#fff"/>');
  var raw = (mx - mn) / 5, p10 = Math.pow(10, Math.floor(Math.log(raw) / Math.LN10)), m = raw / p10, step = (m < 1.5 ? 1 : m < 3.5 ? 2 : m < 7.5 ? 5 : 10) * p10;
  for (var v = Math.ceil(mn / step) * step; v <= mx; v += step) {{ s.push('<line x1="' + L + '" x2="' + (W - R) + '" y1="' + y(v).toFixed(1) + '" y2="' + y(v).toFixed(1) + '" stroke="#2E3641" stroke-opacity="' + (Math.abs(v) < 1e-9 ? 0.45 : 0.1) + '"/>'); s.push('<text x="' + (L - 8) + '" y="' + (y(v) + 4).toFixed(1) + '" font-size="12" text-anchor="end" fill="#2E3641" fill-opacity="0.7">' + money(v).replace(' руб.', '') + '</text>'); }}
  rows.forEach(function (r) {{ var cx = x(r.t); if (r.income > 0) s.push('<rect x="' + (cx - bw).toFixed(1) + '" y="' + y(r.income).toFixed(1) + '" width="' + bw.toFixed(1) + '" height="' + (y(0) - y(r.income)).toFixed(1) + '" fill="#20BA72" fill-opacity="0.55"/>'); if (r.cost > 0) s.push('<rect x="' + cx.toFixed(1) + '" y="' + y(0).toFixed(1) + '" width="' + bw.toFixed(1) + '" height="' + (y(-r.cost) - y(0)).toFixed(1) + '" fill="#2E3641" fill-opacity="0.35"/>'); }});
  var d = ''; rows.forEach(function (r, i) {{ d += (i ? 'L' : 'M') + x(r.t).toFixed(1) + ' ' + y(r.cum).toFixed(1) + ' '; }}); s.push('<path d="' + d + '" fill="none" stroke="#159A5C" stroke-width="3"/>');
  var dd = ''; rows.forEach(function (r, i) {{ dd += (i ? 'L' : 'M') + x(r.t).toFixed(1) + ' ' + y(r.cum_disc).toFixed(1) + ' '; }}); s.push('<path d="' + dd + '" fill="none" stroke="#159A5C" stroke-width="2" stroke-dasharray="6 5" stroke-opacity="0.8"/>');
  if (pb !== null) {{ var px = x(pb); s.push('<line x1="' + px.toFixed(1) + '" x2="' + px.toFixed(1) + '" y1="' + T + '" y2="' + (T + ph) + '" stroke="#D2564A" stroke-width="1.5" stroke-dasharray="4 4"/>'); s.push('<text x="' + (px + 6).toFixed(1) + '" y="' + (T + 14) + '" font-size="13" font-weight="700" fill="#D2564A">окупаемость: месяц ' + pb + '</text>'); }}
  var ms = H > 24 ? 6 : 3; for (var t = 0; t <= H; t += ms) s.push('<text x="' + x(t).toFixed(1) + '" y="' + (HH - B + 18) + '" font-size="12" text-anchor="middle" fill="#2E3641" fill-opacity="0.7">' + t + '</text>');
  var ly = HH - 8;
  s.push('<rect x="' + L + '" y="' + (ly - 10) + '" width="12" height="10" fill="#20BA72" fill-opacity="0.55"/><text x="' + (L + 18) + '" y="' + ly + '" font-size="12.5" fill="#2E3641" fill-opacity="0.8">доход в месяц</text>');
  s.push('<rect x="' + (L + 130) + '" y="' + (ly - 10) + '" width="12" height="10" fill="#2E3641" fill-opacity="0.35"/><text x="' + (L + 148) + '" y="' + ly + '" font-size="12.5" fill="#2E3641" fill-opacity="0.8">затраты</text>');
  s.push('<line x1="' + (L + 230) + '" x2="' + (L + 256) + '" y1="' + (ly - 5) + '" y2="' + (ly - 5) + '" stroke="#159A5C" stroke-width="3"/><text x="' + (L + 262) + '" y="' + ly + '" font-size="12.5" fill="#2E3641" fill-opacity="0.8">накопленный поток</text>');
  s.push('<line x1="' + (L + 400) + '" x2="' + (L + 426) + '" y1="' + (ly - 5) + '" y2="' + (ly - 5) + '" stroke="#159A5C" stroke-width="2" stroke-dasharray="6 5"/><text x="' + (L + 432) + '" y="' + ly + '" font-size="12.5" fill="#2E3641" fill-opacity="0.8">с дисконтированием (NPV на конце)</text>');
  s.push('</svg>'); return s.join('');
}}
document.getElementById('save').onclick = function () {{
  var svg = document.querySelector('#chart svg'); if (!svg) return;
  var txt = new XMLSerializer().serializeToString(svg);
  var blob = new Blob([txt], {{ type: 'image/svg+xml;charset=utf-8' }});
  var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'npv.svg'; document.body.appendChild(a); a.click(); document.body.removeChild(a);
}};
document.getElementById('calc').onclick = calc;
form();
</script>
<script src="model.js"></script>
<script>calc();</script>
</body></html>
"""


def _meta_tool(v):
    return dict(
        title=v["title"], metric=v["metric"], params=v["params"],
        inputs=[dict(id=i["id"], name=i["name"], unit=i["unit"], file="") for i in v["inputs"]],
        files=[],
    )


def main():
    for v in VARIANTS:
        d = DATA / v["id"]
        # каркас параметров: файлы известны только по выбранной конфигурации,
        # поэтому META.files заполняются страницей по URL? Нет — каркас должен
        # работать без сети: он принимает файл любого из двух источников каждого
        # входа и сам определяет, какой источник загружен.
        files = []
        inputs = []
        for i in v["inputs"]:
            for s in i["sources"]:
                files.append(dict(file=s["file"], input=i["name"], id=i["id"]))
            inputs.append(dict(id=i["id"], name=i["name"], unit=i["unit"], file=" / ".join(s["file"] for s in i["sources"])))
        ref = {}
        for i in v["inputs"]:
            for s in i["sources"]:
                ref[s["file"]] = s["ref"]
        meta = dict(title=v["title"], metric=v["metric"], params=v["params"], inputs=inputs, files=files, ref=ref)
        html = TOOL.format(title=v["title"], css=CSS, meta=json.dumps(meta, ensure_ascii=False).replace("</", "<\\/"))
        (d / "инструмент_параметров.html").write_text(html, encoding="utf-8")
        f = v["fin"]
        defaults = dict(delta="", volume="", price="", ramp=f["ramp"], keep=f["keep"], capex=f["capex"], opex=f["opex"], horizon=f["horizon"], rate=f["rate"])
        meta2 = dict(title=v["title"], kind=f["kind"], defaults=defaults,
                     units=dict(delta=v["params"]["delta"]["unit"], volume=v["params"]["volume"]["unit"], price=v["params"]["price"]["unit"]))
        html2 = NPV.format(title=v["title"], css=CSS, meta=json.dumps(meta2, ensure_ascii=False).replace("</", "<\\/"))
        (d / "финмодель.html").write_text(html2, encoding="utf-8")
        print(v["id"], "каркасы записаны")


if __name__ == "__main__":
    main()
