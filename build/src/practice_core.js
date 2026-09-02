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
  function sampleRows(file, n) {
    var lines = String(file.text || '').split(/\r?\n/).filter(Boolean);
    return lines.slice(0, (n || 3) + 1).join('\n');
  }
  // variant — описание варианта; chosen — {inputId: sourceId}; files — {fileName: {text}} (для примеров строк)
  function toolPrompt(variant, chosen, files) {
    var eco = economy(variant, chosen), N = eco.rows.length;
    var L = [];
    L.push('Сделай одностраничный HTML-инструмент: расчёт параметров проекта «' + variant.title + '» по нескольким выгрузкам.');
    L.push('');
    L.push('Данные: ' + N + ' CSV-файла, кодировка UTF-8 с меткой порядка байтов, разделитель — точка с запятой, десятичный знак — запятая. Пользователь выбирает все файлы сразу одной кнопкой (input type="file" multiple accept=".csv"); файл распознаётся по имени. Файлы читаются в браузере и никуда не отправляются.');
    L.push('');
    eco.rows.forEach(function (r, i) {
      var f = files && files[r.source.file];
      L.push('Файл ' + (i + 1) + ' «' + r.source.file + '» — вход ' + r.input.id + ' («' + r.input.name + '», ' + r.input.unit + '). Первые строки файла:');
      L.push(f ? sampleRows(f, 3) : '(строки файла)');
      L.push('Расчёт входа ' + r.input.id + ': ' + r.source.calc + '.');
      L.push('');
    });
    L.push('Итоговые параметры проекта — посчитать из входов и вывести крупно, каждый с названием и единицей:');
    Object.keys(variant.params).forEach(function (k) {
      var p = variant.params[k];
      L.push('- ' + k + ' — ' + p.name + ' (' + p.unit + ') = ' + p.formula + (p.note ? '; ' + p.note : ''));
    });
    L.push('Под параметрами — одна строка для копирования в следующий инструмент, ровно в таком виде: «delta=<число>; volume=<число>; price=<число>» с точкой в качестве десятичного знака, и кнопка «Копировать параметры» (navigator.clipboard.writeText с запасным вариантом через выделение текста).');
    L.push('Итоговая метрика: ' + variant.metric.name + ' (' + variant.metric.unit + ') = ' + variant.metric.formula + ' — показать значение рядом с параметрами.');
    L.push('Ниже — таблица входов: id, название, значение, из какого файла посчитано.');
    L.push('График: значения входа ' + eco.rows[0].input.id + ' по месяцам (если в файле есть столбец месяц) — линия, нарисованная inline SVG без внешних библиотек: ось месяцев внизу, подписи минимума и максимума слева, ширина 100 %.');
    L.push('');
    L.push('Требования к коду:');
    L.push('— один HTML-файл без внешних библиотек и без запросов в сеть;');
    L.push('— имена файлов ровно такие, как указано выше: ' + eco.rows.map(function (r) { return r.source.file; }).join(', ') + '; порядок выбора любой; до выбора всех ' + N + ' файлов показывать список ожидаемых имён и отмечать, какие уже загружены; если имя файла не из списка — сообщение «файл не из списка» с именем (текстом на странице, без alert);');
    L.push('— файлы читать через FileReader.readAsText; у первого заголовка срезать метку кодировки: replace(/^\\uFEFF/, ""); строки делить по переводу строки, пустые пропускать; числа разбирать после замены запятой на точку: parseFloat(s.replace(",", "."));');
    L.push('— столбцы находить по названию из заголовка, а не по номеру;');
    L.push('— месяц — строка, в объект даты не превращать;');
    L.push('— имена переменных и функций — английские слова латиницей, русский — только в подписях;');
    L.push('— async и await не использовать;');
    L.push('— если для расчёта не хватает файла, показывать, какого именно, и не выдавать NaN.');
    L.push('');
    var checks = eco.rows.map(function (r) { return r.input.id + ' около ' + fmtv(r.source.expect); });
    L.push('Проверь себя: на этих выгрузках ' + checks.join(', ') + '.');
    L.push('');
    L.push('Ответ — только полный HTML-файл в тройных кавычках, без пояснений.');
    return L.join('\n');
  }

  // ── промпт 2: мини-инструмент финансовой модели с SVG ──────────────────
  function npvPrompt(variant, params) {
    var f = variant.fin, L = [];
    var p = { kind: f.kind, delta: params.delta, volume: params.volume, price: params.price, ramp: f.ramp, keep: f.keep, capex: f.capex, opex: f.opex, horizon: f.horizon, rate: f.rate };
    var res = totals(p);
    L.push('Сделай одностраничный HTML-инструмент: финансовая модель эффекта проекта «' + variant.title + '» — поток эффекта по месяцам, окупаемость и NPV, график в SVG с кнопкой сохранения.');
    L.push('');
    L.push('Параметры — поля ввода со значениями по умолчанию и кнопка «Рассчитать» (расчёт также при загрузке страницы):');
    L.push('delta = ' + String(params.delta) + ' — изменение показателя в месяц (' + variant.params.delta.unit + ')');
    L.push('volume = ' + String(params.volume) + ' — объём (' + variant.params.volume.unit + ')');
    L.push('price = ' + String(params.price) + ' — стоимость единицы, руб. в месяц (' + variant.params.price.unit + ')');
    L.push('ramp = ' + f.ramp + ' — выход на полный уровень, мес.');
    L.push('keep = ' + f.keep + ' — срок сохранения эффекта, мес.');
    L.push('capex = ' + f.capex + ' — единовременные затраты, руб.');
    L.push('opex = ' + f.opex + ' — ежемесячные затраты, руб.');
    L.push('horizon = ' + f.horizon + ' — горизонт, мес.');
    L.push('rate = ' + f.rate + ' — годовая ставка дисконтирования, доля');
    L.push('');
    L.push('Расчёт по месяцам t от 0 до horizon (повтори формулы точно):');
    L.push('— доля выхода на уровень: ramp_share(t) = min(t / ramp, 1), при ramp = 0 равна 1;');
    L.push('— full = delta × volume;');
    if (f.kind === 'cohort') L.push('— units(t) для t ≥ 1: сумма full × ramp_share(k) по k от max(1, t − keep + 1) до t (когорты каждого месяца живут keep месяцев);');
    else L.push('— units(t) для t ≥ 1: full × ramp_share(t), если t ≤ keep, иначе 0;');
    L.push('— income(t) = units(t) × price; income(0) = 0;');
    L.push('— cost(0) = capex; cost(t) = opex для t ≥ 1;');
    L.push('— cf(t) = income(t) − cost(t); cum(t) — накопленная сумма cf;');
    L.push('— месячная ставка m = (1 + rate)^(1/12) − 1; disc(t) = cf(t) / (1 + m)^t; cum_disc(t) — накопленная сумма disc;');
    L.push('— окупаемость — первый месяц t ≥ 1, где cum(t) ≥ 0 (если нет — «не достигается»); NPV = cum_disc(horizon); доход за первый год — сумма income(t) для t от 1 до 12.');
    L.push('');
    L.push('Вывод: три числа крупно с названиями — «Доход за первый год», «Окупаемость, мес.», «NPV за горизонт» (рубли — с разделителями тысяч, без копеек); под ними таблица по месяцам: t, доход, затраты, поток, накопленный поток, накопленный дисконтированный.');
    L.push('График — inline SVG шириной 100 % (viewBox 0 0 960 340): столбики дохода по месяцам, линия накопленного потока, пунктирная линия накопленного дисконтированного потока, вертикальная отметка месяца окупаемости с подписью, подписи оси месяцев и сетка значений; всё без внешних библиотек.');
    L.push('Кнопка «Сохранить SVG»: сериализовать элемент svg через XMLSerializer, сделать Blob с типом image/svg+xml;charset=utf-8, скачать через ссылку с атрибутом download="npv.svg". В корневой элемент svg добавить атрибут xmlns="http://www.w3.org/2000/svg", чтобы файл открывался отдельно.');
    L.push('');
    L.push('Требования к коду: один HTML-файл без внешних библиотек и запросов в сеть; имена переменных и функций латиницей, русский только в подписях; без async и await; числа из полей разбирать после замены запятой на точку.');
    L.push('');
    L.push('Проверь себя: при значениях по умолчанию окупаемость — месяц ' + (res.payback === null ? 'не достигается' : res.payback) + ', NPV за ' + f.horizon + ' мес. около ' + money(res.npv).replace(/\.$/, '') + ', доход за первый год около ' + money(res.year1).replace(/\.$/, '') + '. Если получилось иначе — проверь формулу units(t) и дисконтирование.');
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

  return { fi: fi, fr: fr, fmtv: fmtv, money: money, clean: clean, num: num,
    economy: economy, flows: flows, totals: totals,
    toolPrompt: toolPrompt, npvPrompt: npvPrompt, calcPrompt: calcPrompt, modelPrompt: modelPrompt, extractHtml: extractHtml, extractJs: extractJs, parseParams: parseParams };
});
