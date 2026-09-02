/* Ядро практического занятия «Проект по варианту»: промпты на мини-инструменты,
 * экономика конфигурации источников, финансовая модель, сборка презентации.
 * Один файл для страницы тренажёра (trainer_practice.html) и для прогона
 * через API (build/check_practice_tools.cjs).
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.PracticeCore = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  var NB = ' ';
  function fi(x) { var s = String(Math.round(Math.abs(x))).replace(/\B(?=(\d{3})+(?!\d))/g, NB); return (x < 0 ? '−' : '') + s; }
  function fr(x, d) { return Number(x).toFixed(d).replace('.', ',').replace(/^-/, '−'); }
  function fmtv(v) {
    if (v === null || v === undefined || isNaN(v)) return '—';
    var a = Math.abs(v);
    if (a >= 1000) return fi(v);
    if (Number.isInteger(v)) return String(v);
    return String(Math.round(v * 10000) / 10000).replace('.', ',');
  }
  function money(x) {
    var a = Math.abs(x);
    if (a >= 1e6) return (x < 0 ? '−' : '') + fr(a / 1e6, a >= 1e7 ? 1 : 2) + ' млн руб.';
    if (a >= 1e4) return (x < 0 ? '−' : '') + fi(a / 1e3) + ' тыс. руб.';
    return fi(x) + ' руб.';
  }
  function clean(s) { return String(s == null ? '' : s).replace(/\s+/g, ' ').trim(); }
  function or(v, d) { var c = clean(v); return c ? c : d; }
  function num(v) {
    if (typeof v === 'number') return v;
    var s = String(v == null ? '' : v).replace(/[\s  ]/g, '').replace(',', '.');
    var m = s.match(/-?\d+(?:\.\d+)?/); return m ? parseFloat(m[0]) : NaN;
  }

  // ── конфигурация источников: скорость, цена, интегральная оценка ───────
  // TTE — дней до первого проверенного значения итоговой метрики: максимум
  // по входам (входы собираются параллельно) плюс день на расчёт.
  // TCO — сумма стоимости источников за горизонт пилота.
  // Оценка качества конфигурации: 100 баллов минус штраф за дни и рубли
  // относительно худшей конфигурации варианта.
  function economy(variant, chosen) {
    var days = 0, cost = 0, rows = [];
    variant.inputs.forEach(function (inp) {
      var s = inp.sources.filter(function (x) { return x.id === chosen[inp.id]; })[0] || inp.sources[0];
      days = Math.max(days, s.days); cost += s.cost;
      rows.push({ input: inp, source: s });
    });
    var worstDays = 0, worstCost = 0, bestDays = 0, bestCost = 0;
    variant.inputs.forEach(function (inp) {
      var d = inp.sources.map(function (s) { return s.days; }), c = inp.sources.map(function (s) { return s.cost; });
      worstDays = Math.max(worstDays, Math.max.apply(null, d)); bestDays = Math.max(bestDays, Math.min.apply(null, d));
      worstCost += Math.max.apply(null, c); bestCost += Math.min.apply(null, c);
    });
    var tte = days + 1, bestTte = bestDays + 1, worstTte = worstDays + 1;
    var pd = worstTte > bestTte ? (tte - bestTte) / (worstTte - bestTte) : 0;
    var pc = worstCost > bestCost ? (cost - bestCost) / (worstCost - bestCost) : 0;
    var score = Math.round(100 - 50 * pd - 50 * pc);
    return { rows: rows, tte: tte, cost: cost, score: score, bestTte: bestTte, bestCost: bestCost, worstTte: worstTte, worstCost: worstCost };
  }

  // ── финансовая модель: повторяет finmodel_core.py ─────────────────────
  function ramp(t, T) { return T <= 0 ? 1 : Math.min(t / T, 1); }
  function flows(p) {
    var H = Math.round(p.horizon), T = p.ramp, R = p.keep, full = p.delta * p.volume;
    var m = Math.pow(1 + p.rate, 1 / 12) - 1, rows = [], cum = 0, cumd = 0;
    for (var t = 0; t <= H; t++) {
      var inc = 0, units = 0, cost;
      if (t === 0) { cost = p.capex; }
      else {
        cost = p.opex;
        if (p.kind === 'cohort') { for (var k = Math.max(1, t - R + 1); k <= t; k++) units += full * ramp(k, T); }
        else { units = (t <= R) ? full * ramp(t, T) : 0; }
        inc = units * p.price;
      }
      var cf = inc - cost; cum += cf; var disc = cf / Math.pow(1 + m, t); cumd += disc;
      rows.push({ t: t, income: inc, cost: cost, cf: cf, cum: cum, disc: disc, cum_disc: cumd });
    }
    return rows;
  }
  function totals(p) {
    var rows = flows(p), pb = null, y1 = 0;
    for (var i = 0; i < rows.length; i++) { var r = rows[i]; if (r.t > 0 && pb === null && r.cum >= 0) pb = r.t; if (r.t >= 1 && r.t <= 12) y1 += r.income; }
    return { rows: rows, npv: rows[rows.length - 1].cum_disc, cum: rows[rows.length - 1].cum, payback: pb, year1: y1, full_month: p.delta * p.volume * p.price, horizon: Math.round(p.horizon) };
  }

  // ── промпт 1: мини-инструмент на нескольких CSV ────────────────────────
  // Промпт даёт ассистенту полное описание инструмента и основу файла:
  // чтение CSV, перетаскивание файлов, вывод и график уже написаны, ассистент
  // дописывает расчёт входов по описанию и возвращает файл целиком. Так
  // промпт переиспользуем: заменил файлы, столбцы и формулы — получил другой
  // инструмент.
  function sampleRows(file, n) {
    var lines = String(file.text || '').split(/\r?\n/).filter(Boolean);
    return lines.slice(0, (n || 3) + 1).join('\n');
  }
  function jsStr(s) { return JSON.stringify(String(s)); }
  function toolSkeleton(variant, rows) {
    var L = [];
    L.push('<!DOCTYPE html>');
    L.push('<html lang="ru"><head><meta charset="utf-8"><title>Параметры проекта: ' + variant.title + '</title>');
    L.push('<style>body{font-family:Arial,sans-serif;max-width:900px;margin:24px auto;padding:0 16px;color:#222}.drop{border:2px dashed #999;border-radius:12px;padding:24px;text-align:center;color:#555}.drop.over{border-color:#2a9d5c;background:#f0faf4}table{border-collapse:collapse;width:100%;margin:12px 0}td,th{border-bottom:1px solid #ddd;padding:6px 8px;text-align:left}.tile{display:inline-block;min-width:200px;margin:8px 16px 8px 0}.tile b{display:block;font-size:26px}.line{font-family:monospace;background:#f4f4f4;padding:8px 10px;border-radius:8px}#status{color:#b33}</style></head><body>');
    L.push('<h1>Параметры проекта: ' + variant.title + '</h1>');
    L.push('<div class="drop" id="drop">Перетащите сюда файлы ' + rows.map(function (r) { return r.source.file; }).join(', ') + ' или <label><u>выберите их</u><input type="file" id="files" multiple accept=".csv" style="display:none"></label></div>');
    L.push('<p id="status"></p><div id="out"></div><div id="chart"></div>');
    L.push('<script>');
    L.push('var FILES = ' + JSON.stringify(rows.map(function (r) { return r.source.file; })) + ';');
    L.push('var tables = {};');
    L.push('function parseCsv(text) {');
    L.push('  var lines = text.replace(/^\\uFEFF/, "").split(/\\r?\\n/).filter(function (l) { return l.trim() !== ""; });');
    L.push('  var head = lines[0].split(";").map(function (h) { return h.trim(); }), rows = [];');
    L.push('  for (var i = 1; i < lines.length; i++) {');
    L.push('    var cells = lines[i].split(";"), row = {};');
    L.push('    for (var j = 0; j < head.length; j++) { var v = (cells[j] || "").trim(); var n = parseFloat(v.replace(",", ".")); row[head[j]] = (v !== "" && !isNaN(n)) ? n : v; }');
    L.push('    rows.push(row);');
    L.push('  }');
    L.push('  if (head.length === 2 && head[0] === "параметр") { var wide = {}; rows.forEach(function (r) { wide[r["параметр"]] = r["значение"]; }); rows.forEach(function (r) { for (var k in wide) if (r[k] === undefined) r[k] = wide[k]; }); }');
    L.push('  return rows;');
    L.push('}');
    L.push('if (!Number.prototype.replace) Number.prototype.replace = function () { return String(this); };');
    L.push('if (typeof FileList !== "undefined" && !FileList.prototype.forEach) FileList.prototype.forEach = Array.prototype.forEach;');
    L.push('function computeInputs(tables) {');
    rows.forEach(function (r, i) {
      L.push('  // ' + r.input.id + ' — ' + r.input.name + ' (' + r.input.unit + '): ' + r.source.calc);
      if (r.source.kind === 'params') L.push('  // файл ' + r.source.file + ' — таблица параметр;значение: значение параметра — tables[' + jsStr(r.source.file) + '][0]["имя_параметра"]');
      L.push('  var ' + r.input.id + ' = null; // ЗАПОЛНИТЬ по описанию выше из tables[' + jsStr(r.source.file) + ']');
    });
    L.push('  return { ' + rows.map(function (r) { return r.input.id + ': ' + r.input.id; }).join(', ') + ' };');
    L.push('}');
    L.push('function fmt(v) { return (v === null || v === undefined || isNaN(v)) ? "—" : String(Math.round(v * 100) / 100).replace(".", ","); }');
    L.push('function render() {');
    L.push('  var missing = FILES.filter(function (f) { return !tables[f]; });');
    L.push('  if (missing.length) { document.getElementById("status").textContent = "Ожидаются файлы: " + missing.join(", "); return; }');
    L.push('  var x = computeInputs(tables);');
    var keys = rows.map(function (r) { return r.input.id; });
    L.push('  var delta = ' + jsFormula(variant.params.delta.formula, keys) + ';');
    L.push('  var volume = ' + jsFormula(variant.params.volume.formula, keys) + ';');
    L.push('  var price = ' + jsFormula(variant.params.price.formula, keys) + ';');
    L.push('  var h = "<h2>Входы</h2><table><tr><th>Вход</th><th>Значение</th></tr>";');
    rows.forEach(function (r) { L.push('  h += "<tr><td>' + r.input.name + ' (' + r.input.id + ')</td><td>" + fmt(x.' + r.input.id + ') + " ' + r.input.unit + '</td></tr>";'); });
    L.push('  h += "</table><h2>Параметры финансовой модели</h2>";');
    L.push('  h += "<div class=tile><b>" + fmt(delta) + "</b>' + variant.params.delta.name + ', ' + variant.params.delta.unit + '</div>";');
    L.push('  h += "<div class=tile><b>" + fmt(volume) + "</b>' + variant.params.volume.name + ', ' + variant.params.volume.unit + '</div>";');
    L.push('  h += "<div class=tile><b>" + fmt(price) + "</b>' + variant.params.price.name + ', ' + variant.params.price.unit + '</div>";');
    L.push('  h += "<p>' + variant.metric.name + ': <b>" + fmt(delta * volume * price) + "</b> ' + variant.metric.unit + '</p>";');
    L.push('  h += "<p class=line>delta=" + delta + "; volume=" + volume + "; price=" + price + "</p>";');
    L.push('  document.getElementById("status").textContent = ""; document.getElementById("out").innerHTML = h;');
    L.push('  drawChart();');
    L.push('}');
    L.push('function drawChart() {');
    L.push('  var rows = tables[FILES[0]]; if (!rows || rows[0]["месяц"] === undefined) return;');
    L.push('  var col = Object.keys(rows[0]).filter(function (k) { return k !== "месяц" && typeof rows[0][k] === "number"; })[0]; if (!col) return;');
    L.push('  var by = {}, order = []; rows.forEach(function (r) { var m = String(r["месяц"]); if (by[m] === undefined) { by[m] = 0; order.push(m); } by[m] += r[col]; });');
    L.push('  var ys = order.map(function (m) { return by[m]; }), W = 860, H = 260, L = 60, B = 40, mx = Math.max.apply(null, ys), mn = Math.min.apply(null, ys); if (mx === mn) { mx += 1; mn -= 1; }');
    L.push('  var X = function (i) { return L + (W - L - 20) * i / Math.max(1, ys.length - 1); }, Y = function (v) { return 20 + (H - 20 - B) * (mx - v) / (mx - mn); };');
    L.push('  var d = ys.map(function (v, i) { return (i ? "L" : "M") + X(i).toFixed(1) + " " + Y(v).toFixed(1); }).join(" ");');
    L.push('  var s = "<h2>" + col + " по месяцам</h2><svg viewBox=\\"0 0 " + W + " " + H + "\\" width=\\"100%\\" xmlns=\\"http://www.w3.org/2000/svg\\">";');
    L.push('  s += "<path d=\\"" + d + "\\" fill=\\"none\\" stroke=\\"#2a9d5c\\" stroke-width=\\"3\\"/>";');
    L.push('  s += "<text x=\\"" + (L - 6) + "\\" y=\\"24\\" font-size=\\"12\\" text-anchor=\\"end\\">" + fmt(mx) + "</text><text x=\\"" + (L - 6) + "\\" y=\\"" + (H - B) + "\\" font-size=\\"12\\" text-anchor=\\"end\\">" + fmt(mn) + "</text>";');
    L.push('  order.forEach(function (m, i) { if (i % 3 === 0 || i === order.length - 1) s += "<text x=\\"" + X(i).toFixed(1) + "\\" y=\\"" + (H - 12) + "\\" font-size=\\"11\\" text-anchor=\\"middle\\">" + m + "</text>"; });');
    L.push('  document.getElementById("chart").innerHTML = s + "</svg>";');
    L.push('}');
    L.push('function readFiles(list) {');
    L.push('  Array.prototype.slice.call(list).forEach(function (file) {');
    L.push('    if (FILES.indexOf(file.name) < 0) { document.getElementById("status").textContent = "Файл не из списка: " + file.name; return; }');
    L.push('    var rd = new FileReader(); rd.onload = function () { tables[file.name] = parseCsv(rd.result); render(); }; rd.readAsText(file, "utf-8");');
    L.push('  });');
    L.push('}');
    L.push('var drop = document.getElementById("drop");');
    L.push('drop.addEventListener("dragover", function (e) { e.preventDefault(); drop.className = "drop over"; });');
    L.push('drop.addEventListener("dragleave", function () { drop.className = "drop"; });');
    L.push('drop.addEventListener("drop", function (e) { e.preventDefault(); drop.className = "drop"; readFiles(e.dataTransfer.files); });');
    L.push('document.getElementById("files").addEventListener("change", function () { readFiles(this.files); });');
    L.push('render();');
    L.push('</script></body></html>');
    return L.join('\n');
  }
  // формула параметра из описания варианта → JS-выражение по объекту x
  function jsFormula(f, keys) {
    var s = String(f).replace(/×/g, '*').replace(/÷/g, '/').replace(/−/g, '-');
    keys.forEach(function (k) { s = s.replace(new RegExp('\\b' + k + '\\b', 'g'), 'x.' + k); });
    return s;
  }
  // variant — описание варианта; chosen — {inputId: sourceId}; files — {fileName: {text}}
  function toolPrompt(variant, chosen, files) {
    var eco = economy(variant, chosen), rows = eco.rows, L = [];
    L.push('Допиши мини-инструмент: одностраничный HTML-файл, который читает несколько CSV-выгрузок, считает входы дерева метрик проекта «' + variant.title + '» и параметры финансовой модели. Основа файла ниже уже готова: чтение файлов, перетаскивание, вывод и график написаны. Нужно заполнить функцию computeInputs — расчёт каждого входа по описанию — и вернуть файл целиком, ничего больше не меняя.');
    L.push('');
    L.push('Данные: ' + rows.length + ' CSV-файла, кодировка UTF-8 с меткой порядка байтов, разделитель — точка с запятой, десятичный знак — запятая. В функцию computeInputs файлы приходят объектом tables: ключ — имя файла, значение — массив строк; строка — объект с ключами из заголовка файла, числа уже переведены в числа, месяц — строка вида «2025-01», порядок строк как в файле.');
    L.push('');
    rows.forEach(function (r, i) {
      var f = files && files[r.source.file];
      L.push('Файл ' + (i + 1) + ' «' + r.source.file + '» — вход ' + r.input.id + ' («' + r.input.name + '», ' + r.input.unit + '). Первые строки:');
      L.push(f ? sampleRows(f, 3) : '(строки файла)');
      L.push('Расчёт входа ' + r.input.id + ': ' + r.source.calc + '.');
      L.push('');
    });
    L.push('Правила для computeInputs: столбцы брать по названию из заголовка, например row["название_столбца"]; «последние 12 строк» — последние 12 элементов массива (arr.slice(-12)); при свёртке по месяцам сначала сложить значения строк с одинаковым месяцем, потом взять последние 12 месяцев по порядку; если файла нет — оставить null; имена переменных латиницей, комментарии по-русски; без async, fetch и внешних библиотек.');
    L.push('');
    L.push('Основа файла:');
    L.push('```html');
    L.push(toolSkeleton(variant, rows));
    L.push('```');
    L.push('');
    L.push('Ответ — только полный HTML-файл в тройных кавычках, без пояснений.');
    return L.join('\n');
  }

  // ── промпт 2: мини-инструмент финансовой модели с SVG ──────────────────
  function npvSkeleton(variant, p) {
    var f = Object.assign({}, variant.fin, p), L = [];
    L.push('<!DOCTYPE html>');
    L.push('<html lang="ru"><head><meta charset="utf-8"><title>Финансовая модель: ' + variant.title + '</title>');
    L.push('<style>body{font-family:Arial,sans-serif;max-width:960px;margin:24px auto;padding:0 16px;color:#222}label{display:inline-block;margin:0 14px 10px 0;font-size:14px}label span{display:block;color:#666;font-size:12px}input{font:inherit;padding:5px 8px;width:140px}button{font:inherit;padding:8px 16px;border:0;border-radius:8px;background:#2a9d5c;color:#fff;cursor:pointer}.tile{display:inline-block;min-width:220px;margin:8px 16px 8px 0}.tile b{display:block;font-size:26px}table{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px}td,th{border-bottom:1px solid #ddd;padding:5px 8px;text-align:left}#status{color:#b33}</style></head><body>');
    L.push('<h1>Финансовая модель эффекта: ' + variant.title + '</h1>');
    L.push('<div id="form"></div><button type="button" id="calc">Рассчитать</button> <button type="button" id="save">Сохранить SVG</button>');
    L.push('<p id="status"></p><div id="out"></div><div id="chart"></div><div id="tab"></div>');
    L.push('<script>');
    L.push('var FIELDS = [["delta", "Изменение показателя в месяц, ' + variant.params.delta.unit + '", ' + p.delta + '], ["volume", "Объём, ' + variant.params.volume.unit + '", ' + p.volume + '], ["price", "Стоимость единицы, руб. в месяц", ' + p.price + '], ["ramp", "Выход на полный уровень, мес.", ' + f.ramp + '], ["keep", "Срок сохранения эффекта, мес.", ' + f.keep + '], ["capex", "Единовременные затраты, руб. (включая данные ' + fi(f.datacost || 0) + ' руб.)", ' + f.capex + '], ["opex", "Ежемесячные затраты, руб.", ' + f.opex + '], ["horizon", "Горизонт, мес.", ' + f.horizon + '], ["rate", "Ставка дисконтирования, доля в год", ' + f.rate + ']];');
    L.push('document.getElementById("form").innerHTML = FIELDS.map(function (f) { return "<label>" + f[1] + "<span>" + f[0] + "</span><input id=\\"f-" + f[0] + "\\" value=\\"" + f[2] + "\\"></label>"; }).join("");');
    L.push('function num(v) { var n = parseFloat(String(v).replace(",", ".")); return isNaN(n) ? 0 : n; }');
    L.push('function money(x) { var a = Math.abs(x), s = a >= 1e6 ? (a / 1e6).toFixed(2).replace(".", ",") + " млн руб." : Math.round(a).toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g, " ") + " руб."; return (x < 0 ? "−" : "") + s; }');
    L.push('function effectFlows(p) {');
    L.push('  // ЗАПОЛНИТЬ по формулам из задания: вернуть массив из horizon + 1 объектов {t, income, cost, cf, cum, cum_disc} для t = 0..horizon');
    L.push('  var rows = [];');
    L.push('  return rows;');
    L.push('}');
    L.push('function calc() {');
    L.push('  var p = { kind: "' + f.kind + '" }; FIELDS.forEach(function (f) { p[f[0]] = num(document.getElementById("f-" + f[0]).value); });');
    L.push('  var rows = effectFlows(p);');
    L.push('  if (!rows || rows.length !== Math.round(p.horizon) + 1) { document.getElementById("status").textContent = "Функция effectFlows должна вернуть horizon + 1 строк"; return; }');
    L.push('  var pb = null, y1 = 0; rows.forEach(function (r) { if (r.t > 0 && pb === null && r.cum >= 0) pb = r.t; if (r.t >= 1 && r.t <= 12) y1 += r.income; });');
    L.push('  var npv = rows[rows.length - 1].cum_disc;');
    L.push('  document.getElementById("status").textContent = "";');
    L.push('  document.getElementById("out").innerHTML = "<div class=tile><b>" + money(y1) + "</b>Доход за первый год</div><div class=tile><b>" + (pb === null ? "не достигается" : "месяц " + pb) + "</b>Окупаемость</div><div class=tile><b>" + money(npv) + "</b>NPV за " + Math.round(p.horizon) + " мес.</div>";');
    L.push('  var t = "<table><tr><th>Мес.</th><th>Доход</th><th>Затраты</th><th>Поток</th><th>Накопленный</th><th>Накопленный дисконтированный</th></tr>";');
    L.push('  rows.forEach(function (r) { t += "<tr><td>" + r.t + "</td><td>" + money(r.income) + "</td><td>" + money(r.cost) + "</td><td>" + money(r.cf) + "</td><td>" + money(r.cum) + "</td><td>" + money(r.cum_disc) + "</td></tr>"; });');
    L.push('  document.getElementById("tab").innerHTML = t + "</table>";');
    L.push('  drawChart(rows, pb, Math.round(p.horizon));');
    L.push('}');
    L.push('function drawChart(rows, pb, H) {');
    L.push('  var W = 960, HH = 340, L = 80, R = 30, T = 20, B = 40, pw = W - L - R, ph = HH - T - B, mx = 0, mn = 0;');
    L.push('  rows.forEach(function (r) { mx = Math.max(mx, r.cum, r.income); mn = Math.min(mn, r.cum, -r.cost); }); if (mx === mn) { mx = 1; mn = -1; }');
    L.push('  var y = function (v) { return T + ph * (mx - v) / (mx - mn); }, x = function (t) { return L + pw * t / H; }, bw = Math.max(3, pw / (H + 1) * 0.34);');
    L.push('  var s = "<svg xmlns=\\"http://www.w3.org/2000/svg\\" viewBox=\\"0 0 " + W + " " + HH + "\\" width=\\"100%\\" font-family=\\"Arial\\"><rect width=\\"" + W + "\\" height=\\"" + HH + "\\" fill=\\"#fff\\"/>";');
    L.push('  s += "<line x1=\\"" + L + "\\" x2=\\"" + (W - R) + "\\" y1=\\"" + y(0) + "\\" y2=\\"" + y(0) + "\\" stroke=\\"#999\\"/>";');
    L.push('  rows.forEach(function (r) { var cx = x(r.t); if (r.income > 0) s += "<rect x=\\"" + (cx - bw) + "\\" y=\\"" + y(r.income) + "\\" width=\\"" + bw + "\\" height=\\"" + (y(0) - y(r.income)) + "\\" fill=\\"#2a9d5c\\" fill-opacity=\\"0.5\\"/>"; if (r.cost > 0) s += "<rect x=\\"" + cx + "\\" y=\\"" + y(0) + "\\" width=\\"" + bw + "\\" height=\\"" + (y(-r.cost) - y(0)) + "\\" fill=\\"#555\\" fill-opacity=\\"0.4\\"/>"; });');
    L.push('  s += "<path d=\\"" + rows.map(function (r, i) { return (i ? "L" : "M") + x(r.t).toFixed(1) + " " + y(r.cum).toFixed(1); }).join(" ") + "\\" fill=\\"none\\" stroke=\\"#1e7a47\\" stroke-width=\\"3\\"/>";');
    L.push('  s += "<path d=\\"" + rows.map(function (r, i) { return (i ? "L" : "M") + x(r.t).toFixed(1) + " " + y(r.cum_disc).toFixed(1); }).join(" ") + "\\" fill=\\"none\\" stroke=\\"#1e7a47\\" stroke-width=\\"2\\" stroke-dasharray=\\"6 5\\"/>";');
    L.push('  if (pb !== null) s += "<line x1=\\"" + x(pb) + "\\" x2=\\"" + x(pb) + "\\" y1=\\"" + T + "\\" y2=\\"" + (T + ph) + "\\" stroke=\\"#c33\\" stroke-dasharray=\\"4 4\\"/><text x=\\"" + (x(pb) + 6) + "\\" y=\\"" + (T + 14) + "\\" font-size=\\"13\\" fill=\\"#c33\\">окупаемость: месяц " + pb + "</text>";');
    L.push('  for (var t = 0; t <= H; t += 3) s += "<text x=\\"" + x(t) + "\\" y=\\"" + (HH - 14) + "\\" font-size=\\"12\\" text-anchor=\\"middle\\">" + t + "</text>";');
    L.push('  s += "<text x=\\"" + (L - 6) + "\\" y=\\"" + (y(mx) + 12) + "\\" font-size=\\"12\\" text-anchor=\\"end\\">" + money(mx) + "</text><text x=\\"" + (L - 6) + "\\" y=\\"" + y(mn) + "\\" font-size=\\"12\\" text-anchor=\\"end\\">" + money(mn) + "</text>";');
    L.push('  document.getElementById("chart").innerHTML = s + "</svg>";');
    L.push('}');
    L.push('document.getElementById("calc").onclick = calc;');
    L.push('document.getElementById("save").onclick = function () { var svg = document.querySelector("#chart svg"); if (!svg) return; var blob = new Blob([new XMLSerializer().serializeToString(svg)], { type: "image/svg+xml;charset=utf-8" }); var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "npv.svg"; document.body.appendChild(a); a.click(); document.body.removeChild(a); };');
    L.push('calc();');
    L.push('</script></body></html>');
    return L.join('\n');
  }
  function npvPrompt(variant, params) {
    var f = Object.assign({}, variant.fin, params.fin || {}), L = [];
    var p = { kind: f.kind, delta: params.delta, volume: params.volume, price: params.price, ramp: f.ramp, keep: f.keep, capex: f.capex, opex: f.opex, horizon: f.horizon, rate: f.rate };
    var res = totals(p);
    L.push('Допиши мини-инструмент финансовой модели проекта «' + variant.title + '»: одностраничный HTML-файл с полями параметров, расчётом потока эффекта по месяцам, окупаемостью, NPV, таблицей и графиком SVG с кнопкой сохранения. Основа файла ниже готова: поля, вывод, таблица, график и сохранение написаны. Нужно заполнить функцию effectFlows(p) по формулам и вернуть файл целиком, ничего больше не меняя.');
    L.push('');
    L.push('Параметры получены из данных: изменение показателя ' + fmtv(p.delta) + ' × объём ' + fmtv(p.volume) + ' × стоимость единицы ' + fmtv(p.price) + ' руб. = эффект ' + money(p.delta * p.volume * p.price).replace(/\.$/, '') + ' в месяц на полном уровне' + (f.kind === 'cohort' ? ' на когорту' : '') + '. Единовременные затраты ' + fi(p.capex) + ' руб. включают стоимость сбора данных ' + fi(f.datacost || 0) + ' руб.');
    L.push('');
    L.push('Поля p — числа: delta (изменение показателя в месяц), volume (объём), price (стоимость единицы, руб. в месяц), ramp (выход на полный уровень, мес.), keep (срок сохранения эффекта, мес.), capex (единовременные затраты, руб.), opex (ежемесячные затраты, руб.), horizon (горизонт, мес.), rate (годовая ставка дисконтирования, доля). Функция возвращает массив из horizon + 1 объектов для t = 0, 1, …, horizon с полями t, income, cost, cf, cum, cum_disc.');
    L.push('');
    L.push('Формулы:');
    L.push('— доля выхода на уровень rampShare(t) = min(t / ramp, 1); при ramp = 0 равна 1;');
    L.push('— full = delta × volume;');
    if (f.kind === 'cohort') L.push('— units(t) для t ≥ 1: сумма full × rampShare(k) по k от max(1, t − keep + 1) до t (когорты каждого месяца живут keep месяцев);');
    else L.push('— units(t) для t ≥ 1: full × rampShare(t), если t ≤ keep, иначе 0;');
    L.push('— income(t) = units(t) × price; income(0) = 0;');
    L.push('— cost(0) = capex; cost(t) = opex для t ≥ 1;');
    L.push('— cf(t) = income(t) − cost(t); cum(t) — накопленная сумма cf от 0 до t;');
    L.push('— месячная ставка m = (1 + rate)^(1/12) − 1; disc(t) = cf(t) / (1 + m)^t; cum_disc(t) — накопленная сумма disc от 0 до t.');
    L.push('');
    L.push('Правила: обычный цикл for, имена латиницей, комментарии по-русски; без async и внешних библиотек; поля p уже числа.');
    L.push('');
    L.push('Основа файла:');
    L.push('```html');
    L.push(npvSkeleton(variant, p));
    L.push('```');
    L.push('');
    L.push('Ответ — только полный HTML-файл в тройных кавычках, без пояснений.');
    return { text: L.join('\n'), expect: res, params: p };
  }

  // ── промпты на модули расчёта для готовых каркасов ────────────────────
  // Схема практики занятия 3: каркас читает файлы и рисует, ассистент пишет
  // только расчёт. Базовая модель не собирает целый инструмент, а функцию
  // из двадцати строк по образцу — собирает.
  function calcPrompt(variant, chosen, files) {
    var eco = economy(variant, chosen), L = [];
    L.push('Напиши файл расчёта rasschet.js для готового мини-инструмента «Параметры проекта: ' + variant.title + '». Инструмент сам читает CSV-файлы и показывает результат; от тебя — одна функция расчёта входов.');
    L.push('');
    L.push('Инструмент вызывает window.computeInputs(tables) и ждёт объект с числами: {' + eco.rows.map(function (r) { return r.input.id + ': число'; }).join(', ') + '}.');
    L.push('tables — объект: ключ — имя файла, значение — массив строк-объектов; ключи строки — названия столбцов из заголовка файла; числа уже переведены в числа (запятая заменена на точку), месяц — строка вида «2025-01»; строки идут в порядке файла.');
    L.push('');
    eco.rows.forEach(function (r, i) {
      var f = files && files[r.source.file];
      L.push('Файл ' + (i + 1) + ': tables["' + r.source.file + '"] — вход ' + r.input.id + ' («' + r.input.name + '», ' + r.input.unit + '). Первые строки файла:');
      L.push(f ? sampleRows(f, 3) : '(строки файла)');
      L.push('Расчёт ' + r.input.id + ': ' + r.source.calc + '.');
      L.push('');
    });
    L.push('Требования:');
    L.push('— только JavaScript, без HTML и без пояснений; объявить функцию именно так: window.computeInputs = function (tables) { ... };');
    L.push('— столбцы брать по названию из заголовка: row["закрытые_счета"]; имена переменных латиницей, комментарии по-русски;');
    L.push('— async и await, fetch и внешние библиотеки не использовать;');
    L.push('— если файла нет (tables["имя"] не определён) — вернуть для этого входа null, не бросать ошибку;');
    L.push('— «последние 12 строк» — это последние 12 элементов массива строк (arr.slice(-12)); при свёртке по месяцам сначала сложить значения строк с одинаковым месяцем, затем взять последние 12 месяцев по порядку.');
    L.push('');
    L.push('Образец оформления (другой проект, другие файлы и столбцы):');
    L.push('window.computeInputs = function (tables) {');
    L.push('  // среднее столбца за последние 12 месяцев');
    L.push('  var a = tables["a_dm.csv"]; var aVal = null;');
    L.push('  if (a) { var last = a.slice(-12), s = 0; for (var i = 0; i < last.length; i++) s += last[i]["выдано"]; aVal = s / last.length; }');
    L.push('  // доля: сумма числителя ÷ сумма знаменателя');
    L.push('  var b = tables["b_dm2.csv"]; var bVal = null;');
    L.push('  if (b) { var n = 0, d = 0; for (var j = 0; j < b.length; j++) { n += b[j]["с_ошибкой"]; d += b[j]["всего"]; } bVal = d ? n / d : null; }');
    L.push('  // параметр из таблицы параметр;значение');
    L.push('  var c = tables["c_fin.csv"]; var cVal = null;');
    L.push('  if (c) { var p = {}; for (var k = 0; k < c.length; k++) p[c[k]["параметр"]] = c[k]["значение"]; cVal = p["ставка_проц"] / 100 * 1000; }');
    L.push('  return { a: aVal, b: bVal, c: cVal };');
    L.push('};');
    L.push('');
    L.push('');
    L.push('Каркас файла для этого проекта — заполни места, отмеченные многоточием, по расчётам выше и верни файл целиком:');
    L.push('window.computeInputs = function (tables) {');
    eco.rows.forEach(function (r, i) {
      L.push('  var f' + (i + 1) + ' = tables["' + r.source.file + '"]; var ' + r.input.id + ' = null;');
      L.push('  if (f' + (i + 1) + ') { ... }   // ' + r.source.calc);
    });
    L.push('  return { ' + eco.rows.map(function (r) { return r.input.id + ': ' + r.input.id; }).join(', ') + ' };');
    L.push('};');
    L.push('');
    L.push('Проверь себя: на этих файлах ' + eco.rows.map(function (r) { return r.input.id + ' ≈ ' + fmtv(r.source.expect); }).join(', ') + '.');
    L.push('');
    L.push('Ответ — только код файла rasschet.js в тройных кавычках.');
    return L.join('\n');
  }
  function modelPrompt(variant, params) {
    var f = variant.fin, L = [];
    var p = { kind: f.kind, delta: params.delta, volume: params.volume, price: params.price, ramp: f.ramp, keep: f.keep, capex: f.capex, opex: f.opex, horizon: f.horizon, rate: f.rate };
    var res = totals(p);
    L.push('Напиши файл model.js для готового мини-инструмента «Финансовая модель эффекта: ' + variant.title + '». Инструмент показывает поля параметров, таблицу и график; от тебя — одна функция расчёта потока по месяцам.');
    L.push('');
    L.push('Инструмент вызывает window.effectFlows(p), где p — объект с числами: delta (изменение показателя в месяц), volume (объём), price (стоимость единицы, руб. в месяц), ramp (выход на полный уровень, мес.), keep (срок сохранения эффекта, мес.), capex (единовременные затраты, руб.), opex (ежемесячные затраты, руб.), horizon (горизонт, мес.), rate (годовая ставка дисконтирования, доля), kind (строка "' + f.kind + '").');
    L.push('Функция возвращает массив из horizon + 1 объектов для t = 0, 1, …, horizon с полями t, income, cost, cf, cum, cum_disc.');
    L.push('');
    L.push('Формулы (повтори точно):');
    L.push('— доля выхода на уровень: rampShare(t) = min(t / ramp, 1); при ramp = 0 равна 1;');
    L.push('— full = delta × volume;');
    if (f.kind === 'cohort') L.push('— units(t) для t ≥ 1: сумма full × rampShare(k) по k от max(1, t − keep + 1) до t — когорты каждого месяца живут keep месяцев;');
    else L.push('— units(t) для t ≥ 1: full × rampShare(t), если t ≤ keep, иначе 0;');
    L.push('— income(t) = units(t) × price; income(0) = 0;');
    L.push('— cost(0) = capex; cost(t) = opex для t ≥ 1;');
    L.push('— cf(t) = income(t) − cost(t); cum(t) — накопленная сумма cf от 0 до t;');
    L.push('— месячная ставка m = (1 + rate)^(1/12) − 1; disc(t) = cf(t) / (1 + m)^t; cum_disc(t) — накопленная сумма disc от 0 до t.');
    L.push('');
    L.push('Требования: только JavaScript без HTML и пояснений; объявить функцию именно так: window.effectFlows = function (p) { ... }; обычный цикл for, без async и внешних библиотек; имена латиницей, комментарии по-русски. Все поля p — числа, приводить их не нужно.');
    L.push('');
    L.push('Каркас функции — заполни места, отмеченные многоточием, по формулам выше и верни файл целиком:');
    L.push('window.effectFlows = function (p) {');
    L.push('  var rows = [], cum = 0, cumDisc = 0;');
    L.push('  var m = ...;                 // месячная ставка из годовой p.rate');
    L.push('  var full = ...;              // delta × volume');
    L.push('  function rampShare(t) { ... }');
    L.push('  for (var t = 0; t <= p.horizon; t++) {');
    L.push('    var units = 0, income = 0, cost = (t === 0) ? p.capex : p.opex;');
    L.push('    if (t >= 1) {');
    L.push('      ...                      // units(t) по формуле для kind = "' + f.kind + '"');
    L.push('      income = units * p.price;');
    L.push('    }');
    L.push('    var cf = income - cost;');
    L.push('    cum += cf;');
    L.push('    var disc = ...;            // cf / (1 + m)^t');
    L.push('    cumDisc += disc;');
    L.push('    rows.push({ t: t, income: income, cost: cost, cf: cf, cum: cum, cum_disc: cumDisc });');
    L.push('  }');
    L.push('  return rows;');
    L.push('};');
    L.push('');
    L.push('Проверь себя: при delta = ' + fmtv(p.delta) + ', volume = ' + fmtv(p.volume) + ', price = ' + fmtv(p.price) + ', ramp = ' + f.ramp + ', keep = ' + f.keep + ', capex = ' + f.capex + ', opex = ' + f.opex + ', horizon = ' + f.horizon + ', rate = ' + f.rate + ' накопленный поток впервые становится неотрицательным в месяце ' + (res.payback === null ? '— (не достигается)' : res.payback) + ', а cum_disc в последнем месяце около ' + fmtv(Math.round(res.npv)) + ' руб.');
    L.push('');
    L.push('Ответ — только код файла model.js в тройных кавычках.');
    return { text: L.join('\n'), expect: res, params: p };
  }
  function extractJs(text) {
    var s = String(text || '');
    var m = s.match(/```(?:javascript|js)?\s*([\s\S]*?)```/i);
    if (m) return m[1].trim();
    var i = s.indexOf('window.');
    return i >= 0 ? s.slice(i).trim() : null;
  }

  // Запасной инструмент: та же основа, расчёт из контрольных функций варианта.
  function toolReference(variant, chosen, files) {
    var rows = economy(variant, chosen).rows, html = toolSkeleton(variant, rows);
    var body = ['function computeInputs(tables) {'];
    rows.forEach(function (r) {
      body.push('  var ' + r.input.id + ' = null;');
      body.push('  if (tables[' + jsStr(r.source.file) + ']) { ' + r.input.id + ' = (function (rows) { ' + r.source.ref + ' })(tables[' + jsStr(r.source.file) + ']); }');
    });
    body.push('  return { ' + rows.map(function (r) { return r.input.id + ': ' + r.input.id; }).join(', ') + ' };');
    body.push('}');
    return html.replace(/function computeInputs\(tables\) \{[\s\S]*?\n\}/, body.join('\n'));
  }
  function npvReference(variant, params) {
    var f = Object.assign({}, variant.fin, params.fin || {}), p = { kind: f.kind, delta: params.delta, volume: params.volume, price: params.price, ramp: f.ramp, keep: f.keep, capex: f.capex, opex: f.opex, horizon: f.horizon, rate: f.rate, datacost: f.datacost || 0 };
    var html = npvSkeleton(variant, p);
    var fn = 'function effectFlows(p) {\n  var rows = [], cum = 0, cumd = 0, m = Math.pow(1 + p.rate, 1 / 12) - 1, full = p.delta * p.volume;\n  function rampShare(t) { return p.ramp <= 0 ? 1 : Math.min(t / p.ramp, 1); }\n  for (var t = 0; t <= p.horizon; t++) {\n    var units = 0, income = 0, cost = t === 0 ? p.capex : p.opex;\n    if (t >= 1) { ' +
      (f.kind === 'cohort' ? 'for (var k = Math.max(1, t - p.keep + 1); k <= t; k++) units += full * rampShare(k);' : 'units = t <= p.keep ? full * rampShare(t) : 0;') +
      ' income = units * p.price; }\n    var cf = income - cost; cum += cf; var disc = cf / Math.pow(1 + m, t); cumd += disc;\n    rows.push({ t: t, income: income, cost: cost, cf: cf, cum: cum, cum_disc: cumd });\n  }\n  return rows;\n}';
    return html.replace(/function effectFlows\(p\) \{[\s\S]*?\n\}/, fn);
  }

  // ── промпт 3: заключение по результатам ────────────────────────────────
  // ctx: {frame, action, eco, inputs:{id:value}, params:{delta,volume,price}, fin:{...}, res:{payback,npv,year1}}
  function conclusionPrompt(variant, ctx) {
    var L = [], e = ctx.eco;
    L.push('Ты — аналитик данных банка. По результатам расчётов ниже напиши заключение по проекту «' + variant.title + '». Используй только приведённые числа, ничего не пересчитывай и не добавляй; деловой язык, без оценок и призывов.');
    L.push('');
    L.push('Проблема: ' + ctx.frame.problem);
    L.push('Что меняем: ' + ctx.action);
    L.push('Итоговая метрика эффекта: ' + variant.metric.name + ' (' + variant.metric.unit + ') = ' + variant.metric.formula + '.');
    L.push('');
    L.push('Конфигурация источников данных (выбор участника):');
    e.rows.forEach(function (r) { L.push('- ' + r.input.name + ' (' + r.input.id + ') — источник «' + r.source.name + '», первое значение через ' + r.source.days + ' дн., стоимость за пилот ' + (r.source.cost ? fi(r.source.cost) + ' руб.' : '0 руб.') + '; значение по выгрузке: ' + fmtv(ctx.inputs[r.input.id]) + ' ' + r.input.unit.replace(/\.$/, '') + '.'); });
    L.push('Срок первого проверенного значения метрики: ' + e.tte + ' дн.; стоимость данных за пилот: ' + (e.cost ? fi(e.cost) + ' руб.' : '0 руб.') + '; интегральная оценка конфигурации: ' + e.score + ' из 100 (лучшая возможная: ' + e.bestTte + ' дн. и ' + fi(e.bestCost) + ' руб.).');
    L.push('');
    L.push('Параметры финансовой модели из мини-инструмента: изменение показателя ' + fmtv(ctx.params.delta) + ' (' + variant.params.delta.unit + '; ' + variant.params.delta.note + '), объём ' + fmtv(ctx.params.volume) + ' (' + variant.params.volume.unit + '), стоимость единицы ' + fmtv(ctx.params.price) + ' (' + variant.params.price.unit + ').');
    L.push('Условия: выход на уровень ' + ctx.fin.ramp + ' мес., срок сохранения эффекта ' + ctx.fin.keep + ' мес., единовременные затраты ' + fi(ctx.fin.capex) + ' руб. (в том числе сбор данных ' + fi(ctx.fin.datacost || 0) + ' руб.), ежемесячные ' + fi(ctx.fin.opex) + ' руб., горизонт ' + ctx.fin.horizon + ' мес., ставка ' + fr(ctx.fin.rate * 100, 1) + ' % годовых.');
    L.push('Результат финансовой модели: доход за первый год ' + money(ctx.res.year1).replace(/\.$/, '') + '; окупаемость — ' + (ctx.res.payback === null ? 'не достигается в горизонте' : 'месяц ' + ctx.res.payback) + '; NPV за ' + ctx.fin.horizon + ' мес. ' + money(ctx.res.npv).replace(/\.$/, '') + '.');
    L.push('');
    L.push('Ответь строго в формате ниже — четыре строки, каждая начинается с названия поля и двоеточия, без вступления и пояснений:');
    L.push('Вывод: <что показали данные и расчёт — 1–2 предложения с числами: параметры эффекта, окупаемость, NPV>');
    L.push('Эффект для бизнеса: <в чём эффект и на каком допущении он держится; какое допущение проверить в первую очередь>');
    L.push('Первое действие: <что сделать на следующей неделе и какие данные начать собирать — исходя из выбранной конфигурации источников>');
    L.push('Когда пересматриваем: <через сколько дней первая сверка метрики по полной выгрузке (исходя из срока первого значения) и при каком значении параметров решение пересматривается>');
    return L.join('\n');
  }
  function parseConclusion(text) {
    var spec = [['conclusion', ['вывод']], ['effect', ['эффект для бизнеса', 'эффект']], ['action', ['первое действие', 'действие']], ['review', ['когда пересматриваем', 'пересмотр', 'когда']]];
    var out = {}, orphans = [], lines = String(text || '').split(/\r?\n/);
    for (var i = 0; i < lines.length; i++) {
      var l = clean(lines[i]).replace(/^[-*•>#:\d.)\s]+/, '').replace(/\*\*|__/g, '').trim(); if (!l) continue;
      var m = l.match(/^([^:]{2,40}):\s*(.*)$/), hit = null;
      if (m) { var k = m[1].toLowerCase().replace(/ё/g, 'е').trim(); spec.forEach(function (sp) { if (!hit) sp[1].forEach(function (a) { if (!hit && k.indexOf(a) === 0) hit = sp[0]; }); }); }
      if (hit) { var v = clean(m[2]).replace(/^[«"]|[»"]$/g, ''); out[hit] = v; }
      else orphans.push(l);
    }
    var missing = spec.filter(function (sp) { return out[sp[0]] === undefined; });
    for (var q = 0; q < missing.length && q < orphans.length; q++) out[missing[q][0]] = orphans[q].replace(/^[^:]{2,40}:\s*/, '');
    return { fields: out, found: spec.filter(function (sp) { return out[sp[0]]; }).length, total: 4 };
  }

  // Извлечь HTML из ответа модели: между ``` или от <!DOCTYPE до </html>.
  function extractHtml(text) {
    var s = String(text || '');
    var m = s.match(/```(?:html)?\s*([\s\S]*?)```/i);
    if (m && /<html|<!doctype/i.test(m[1])) return m[1].trim();
    var i = s.search(/<!doctype html|<html/i);
    if (i >= 0) { var j = s.lastIndexOf('</html>'); return (j > i ? s.slice(i, j + 7) : s.slice(i)).trim(); }
    return null;
  }
  function parseParams(text) {
    var out = {}, m = String(text || '').match(/delta\s*=\s*([-\d.,]+)[;\s]+volume\s*=\s*([-\d.,]+)[;\s]+price\s*=\s*([-\d.,]+)/i);
    if (m) { out.delta = num(m[1]); out.volume = num(m[2]); out.price = num(m[3]); return out; }
    return null;
  }

  return { fi: fi, fr: fr, fmtv: fmtv, money: money, clean: clean, or: or, num: num,
    economy: economy, flows: flows, totals: totals,
    toolPrompt: toolPrompt, npvPrompt: npvPrompt, toolReference: toolReference, npvReference: npvReference, conclusionPrompt: conclusionPrompt, parseConclusion: parseConclusion, calcPrompt: calcPrompt, modelPrompt: modelPrompt, extractHtml: extractHtml, extractJs: extractJs, parseParams: parseParams };
});
