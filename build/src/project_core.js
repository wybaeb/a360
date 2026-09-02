/* Ядро сквозной практики «Проект от проблемы до эффекта».
 *
 * Один файл на страницу тренажёра (встраивается в trainer_project.html) и на
 * прогон цепочки через API (build/check_project_chain.cjs): промпты, разбор
 * ответов ассистента, расчёты страницы (связь, тренд, поток эффекта) и
 * тексты, которые переходят с шага на шаг. Поэтому то, что участник копирует
 * в ассистента, — ровно то, что прогнано через API, а не его пересказ.
 *
 * Принцип разделения труда: ассистент формулирует и выбирает, страница
 * считает. Веб-версия ассистента не читает CSV и ненадёжна в арифметике,
 * поэтому таблицы маленькие и встроены в промпт текстом, а все числа
 * (корреляция, наклон, поток эффекта, NPV) считаются здесь.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.ProjectCore = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  var NB = ' ';

  // ── числа и текст ──────────────────────────────────────────────────────
  function num(v) {
    if (typeof v === 'number') return v;
    var s = String(v == null ? '' : v).replace(/[\s  ]/g, '').replace(',', '.');
    var m = s.match(/-?\d+(?:\.\d+)?/);
    return m ? parseFloat(m[0]) : NaN;
  }
  function firstNum(s) { var n = num(s); return isNaN(n) ? null : n; }
  function fi(x) {
    var s = String(Math.round(Math.abs(x))).replace(/\B(?=(\d{3})+(?!\d))/g, NB);
    return (x < 0 ? '−' : '') + s;
  }
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

  // ── таблица данных ─────────────────────────────────────────────────────
  // Первая строка — названия столбцов; разделитель — точка с запятой,
  // табуляция (вставка из Excel) или запятая. Первый столбец — метка строки.
  function parseTable(text) {
    var lines = String(text || '').replace(/^﻿/, '').split(/\r?\n/)
      .map(function (l) { return l.trim(); }).filter(Boolean);
    if (lines.length < 2) return null;
    var sep = lines[0].indexOf('\t') >= 0 ? '\t' : lines[0].indexOf(';') >= 0 ? ';' : ',';
    var cols = lines[0].split(sep).map(clean);
    var rows = [];
    for (var i = 1; i < lines.length; i++) {
      var cells = lines[i].split(sep).map(clean);
      if (cells.length < 2) continue;
      while (cells.length < cols.length) cells.push('');
      rows.push(cells.slice(0, cols.length));
    }
    return rows.length ? { cols: cols, rows: rows } : null;
  }
  function tableText(t, max) {
    var rows = t.rows.slice(0, max || 40);
    return t.cols.join(';') + '\n' + rows.map(function (r) { return r.join(';'); }).join('\n');
  }
  function numericCols(t) {
    var out = [];
    for (var j = 1; j < t.cols.length; j++) {
      var ok = 0, n = 0;
      for (var i = 0; i < t.rows.length; i++) {
        if (clean(t.rows[i][j]) === '') continue;
        n++; if (!isNaN(num(t.rows[i][j]))) ok++;
      }
      if (n && ok >= n * 0.8) out.push(t.cols[j]);
    }
    return out;
  }
  function column(t, name) {
    var j = t.cols.indexOf(name);
    if (j < 0) return [];
    return t.rows.map(function (r) { return num(r[j]); });
  }
  function labels(t) { return t.rows.map(function (r) { return r[0]; }); }
  function isMonthly(t) {
    return t.rows.length >= 6 && t.rows.every(function (r) { return /^\d{4}-\d{2}$/.test(r[0]); });
  }

  // ── статистика ─────────────────────────────────────────────────────────
  function mean(a) { var s = 0; for (var i = 0; i < a.length; i++) s += a[i]; return a.length ? s / a.length : 0; }
  function pairs(x, y) {
    var px = [], py = [];
    for (var i = 0; i < Math.min(x.length, y.length); i++) if (!isNaN(x[i]) && !isNaN(y[i])) { px.push(x[i]); py.push(y[i]); }
    return { x: px, y: py };
  }
  function pearson(x, y) {
    var p = pairs(x, y), mx = mean(p.x), my = mean(p.y), sxy = 0, sxx = 0, syy = 0;
    for (var i = 0; i < p.x.length; i++) { var dx = p.x[i] - mx, dy = p.y[i] - my; sxy += dx * dy; sxx += dx * dx; syy += dy * dy; }
    if (!sxx || !syy) return 0;
    return sxy / Math.sqrt(sxx * syy);
  }
  function linfit(x, y) {
    var p = pairs(x, y), mx = mean(p.x), my = mean(p.y), sxy = 0, sxx = 0;
    for (var i = 0; i < p.x.length; i++) { sxy += (p.x[i] - mx) * (p.y[i] - my); sxx += (p.x[i] - mx) * (p.x[i] - mx); }
    var b = sxx ? sxy / sxx : 0;
    return { a: my - b * mx, b: b, n: p.x.length };
  }
  function strength(r) {
    var a = Math.abs(r);
    if (a >= 0.7) return 'сильная';
    if (a >= 0.4) return 'умеренная';
    if (a >= 0.2) return 'слабая';
    return 'связи нет';
  }
  function niceStep(x) {
    var a = Math.abs(x); if (!a) return 1;
    var p = Math.pow(10, Math.floor(Math.log10(a)));
    var m = a / p, c = m < 1.5 ? 1 : m < 3.5 ? 2 : m < 7.5 ? 5 : 10;
    return c * p;
  }

  // Связь двух показателей: коэффициент, наклон, диапазоны, текст для промпта.
  function analysisPair(t, xName, yName) {
    var x = column(t, xName), y = column(t, yName), p = pairs(x, y);
    if (p.x.length < 3) return null;
    var r = pearson(x, y), f = linfit(x, y);
    var step = niceStep((Math.max.apply(null, p.x) - Math.min.apply(null, p.x)) / 5);
    var dy = f.b * step;
    var unit = isMonthly(t) ? 'месяцам' : 'строкам таблицы';
    var text = 'Связь показателей «' + xName + '» и «' + yName + '» по ' + p.x.length + ' ' + unit +
      ': коэффициент корреляции Пирсона r = ' + fr(r, 2) + ' (' + strength(r) +
      (Math.abs(r) >= 0.2 ? (r > 0 ? ' прямая' : ' обратная') : '') + ' связь). ' +
      'По линии регрессии при увеличении «' + xName + '» на ' + fmtv(step) +
      ' показатель «' + yName + '» в среднем ' + (dy >= 0 ? 'больше' : 'меньше') + ' на ' + fmtv(Math.abs(Math.round(dy * 100) / 100)) + '. ' +
      'Диапазон «' + xName + '»: ' + fmtv(Math.min.apply(null, p.x)) + '–' + fmtv(Math.max.apply(null, p.x)) +
      '; диапазон «' + yName + '»: ' + fmtv(Math.min.apply(null, p.y)) + '–' + fmtv(Math.max.apply(null, p.y)) + '.';
    return { mode: 'pair', x: xName, y: yName, r: r, strength: strength(r), fit: f, n: p.x.length,
      step: step, dy: dy, xs: p.x, ys: p.y, text: text };
  }

  // Динамика одного показателя: первое/последнее, тренд, сравнение годов.
  function analysisTrend(t, yName) {
    var y = column(t, yName), lab = labels(t), n = y.length;
    if (n < 4) return null;
    var idx = []; for (var i = 0; i < n; i++) idx.push(i);
    var f = linfit(idx, y);
    var monthly = isMonthly(t);
    var text = 'Показатель «' + yName + '» за ' + n + (monthly ? ' месяцев' : ' периодов') + ': ' +
      'первое значение ' + fmtv(y[0]) + ' (' + lab[0] + '), последнее ' + fmtv(y[n - 1]) + ' (' + lab[n - 1] + '). ' +
      (monthly && n >= 24 ? '' : 'Изменение ' + fr((y[n - 1] / y[0] - 1) * 100, 1) + ' %. ') +
      'Тренд по линии регрессии: ' + (f.b >= 0 ? '+' : '−') + fmtv(Math.abs(Math.round(f.b * 10) / 10)) + ' за период. ';
    var yoy = [];
    if (monthly && n >= 24) {
      var last12 = y.slice(n - 12), prev12 = y.slice(n - 24, n - 12);
      var m1 = mean(last12), m0 = mean(prev12);
      text += 'Среднее за последние 12 месяцев ' + fmtv(Math.round(m1 * 10) / 10) + ' против ' +
        fmtv(Math.round(m0 * 10) / 10) + ' за предыдущие 12 (' + (m1 >= m0 ? '+' : '−') + fr(Math.abs(m1 / m0 - 1) * 100, 1) + ' %). ';
      var below = [];
      for (var k = 12; k < n; k++) {
        var d = y[k] / y[k - 12] - 1; yoy.push({ label: lab[k], d: d });
        if (d < -0.05) below.push(lab[k] + ' (' + fr(d * 100, 1) + ' %)');
      }
      text += 'Месяцы ниже того же месяца прошлого года более чем на 5 %: ' + (below.length ? below.join(', ') : 'нет') + '.';
    }
    return { mode: 'trend', y: yName, ys: y, labels: lab, fit: f, n: n, yoy: yoy, text: text };
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
      rows.push({ t: t, units: units, income: inc, cost: cost, cf: cf, cum: cum, disc: disc, cum_disc: cumd });
    }
    return rows;
  }
  function totals(p) {
    var rows = flows(p), pb = null, pbd = null, y1 = 0, inc = 0, cost = 0;
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      if (r.t > 0 && pb === null && r.cum >= 0) pb = r.t;
      if (r.t > 0 && pbd === null && r.cum_disc >= 0) pbd = r.t;
      if (r.t >= 1 && r.t <= 12) y1 += r.income; inc += r.income; cost += r.cost;
    }
    return { rows: rows, npv: rows[rows.length - 1].cum_disc, cum: rows[rows.length - 1].cum,
      payback: pb, payback_disc: pbd, year1: y1, full_month: p.delta * p.volume * p.price,
      income: inc, cost: cost, horizon: Math.round(p.horizon) };
  }
  function sensitivity(p, ass) {
    var base = totals(p).npv, out = [];
    for (var i = 0; i < ass.length; i++) {
      var a = ass[i];
      if (a.pess === null || a.opt === null || isNaN(a.pess) || isNaN(a.opt)) continue;
      var q = JSON.parse(JSON.stringify(p)); q[a.key] = a.pess; var np = totals(q).npv;
      q = JSON.parse(JSON.stringify(p)); q[a.key] = a.opt; var no = totals(q).npv;
      out.push({ key: a.key, name: a.name, base: p[a.key], pess: a.pess, opt: a.opt, npv_pess: np, npv_opt: no,
        flips: (np < 0) !== (base < 0), span: Math.abs(no - np) });
    }
    out.sort(function (a, b) { return b.span - a.span; });
    return out;
  }
  // Текст расчёта — вход для промпта слайда и для письма.
  function effectText(p, units, res, sens) {
    var L = [];
    L.push('Формула: ' + fmtv(p.delta) + ' (' + or(units.delta, 'изменение показателя') + ') × ' +
      fmtv(p.volume) + ' (' + or(units.volume, 'объём') + ') × ' + fmtv(p.price) + ' руб. (' + or(units.price, 'стоимость единицы в месяц') + ') = ' +
      money(res.full_month) + ' в месяц на полном уровне' + (p.kind === 'cohort' ? ' на каждую месячную когорту' : '') + '.');
    L.push('Сроки: выход на уровень ' + p.ramp + ' мес.; срок сохранения эффекта ' + p.keep + ' мес.; горизонт ' + res.horizon + ' мес.; ставка дисконтирования ' + fr(p.rate * 100, 1) + ' %.');
    L.push('Затраты: единовременно ' + money(p.capex) + ', ежемесячно ' + money(p.opex) + '.');
    L.push('Результат: доход за первый год ' + money(res.year1) + '; окупаемость ' + (res.payback === null ? 'не достигается в горизонте' : 'на ' + res.payback + '-й месяц') + '; NPV за ' + res.horizon + ' мес. ' + money(res.npv) + '.');
    var crit = sens.filter(function (r) { return r.flips; });
    if (crit.length) L.push('Главное допущение: вывод меняется при пессимистичном значении — ' +
      crit.map(function (r) { return r.name.toLowerCase() + ' = ' + fmtv(r.pess) + ' (NPV ' + money(r.npv_pess) + ')'; }).join('; ') + '.');
    else if (sens.length) L.push('Главное допущение: ни одно допущение по отдельности не меняет вывод; самое влиятельное — ' +
      sens[0].name.toLowerCase() + ' (пессимистичное ' + fmtv(sens[0].pess) + ' даёт NPV ' + money(sens[0].npv_pess) + ', оптимистичное ' + fmtv(sens[0].opt) + ' — ' + money(sens[0].npv_opt) + ').');
    return L.join('\n');
  }

  // Значения показателя для промпта шага 1: ряд — первое/последнее/наибольшее/наименьшее,
  // срезы — только наибольшее и наименьшее (порядок строк там ничего не значит).
  function facts1(t, focus) {
    if (!t || !focus) return '';
    var y = column(t, focus), lab = labels(t), n = y.length; if (!n) return '';
    var mx = 0, mn = 0; for (var i = 1; i < n; i++) { if (y[i] > y[mx]) mx = i; if (y[i] < y[mn]) mn = i; }
    var s = '';
    if (isMonthly(t)) s += 'первое ' + fmtv(y[0]) + ' (' + lab[0] + '), последнее ' + fmtv(y[n - 1]) + ' (' + lab[n - 1] + '), ';
    s += 'наибольшее ' + fmtv(y[mx]) + ' (' + lab[mx] + '), наименьшее ' + fmtv(y[mn]) + ' (' + lab[mn] + ')';
    if (isMonthly(t) && n >= 24) {
      var m1 = mean(y.slice(n - 12)), m0 = mean(y.slice(n - 24, n - 12)), below = [];
      s += '; среднее за последние 12 месяцев ' + fmtv(Math.round(m1 * 10) / 10) + ' против ' + fmtv(Math.round(m0 * 10) / 10) +
        ' за предыдущие 12 (' + (m1 >= m0 ? '+' : '−') + fr(Math.abs(m1 / m0 - 1) * 100, 1) + ' %)';
      for (var k = n - 12; k < n; k++) if (y[k] / y[k - 12] - 1 < -0.05) below.push(lab[k] + ' (' + fr((y[k] / y[k - 12] - 1) * 100, 1) + ' %)');
      if (below.length) s += '; месяцы последнего года ниже того же месяца прошлого года более чем на 5 %: ' + below.join(', ');
    }
    return s;
  }

  // ── промпты ────────────────────────────────────────────────────────────
  // Сегменты: {t: текст} и {k: ключ}. Ключ подставляется значением из vals
  // или шаблонным выражением PH[k] в [скобках].
  var PH = {
    axis: '[ось: продукт, процесс или бизнес-инициатива]',
    object: '[объект изменений]',
    observation: '[что вы наблюдаете — одной фразой]',
    source: '[откуда данные]',
    table: '[таблица данных: первая строка — названия столбцов]',
    focus: '[показатель из таблицы]',
    facts: '[значения показателя: первое, последнее, наибольшее, наименьшее — считает страница]',
    action_in: '[что вы предполагаете изменить]',
    problem: '[проблема из шага 1]',
    action: '[что меняем из шага 1]',
    columns: '[показатели из таблицы]',
    other: '[другие показатели подразделения]',
    metrics: '[метрики из шага 2 — по одной в строке]',
    sources: '[источники, которые есть у подразделения]',
    analysis: '[результат анализа из шага 4]',
    n: '[число наблюдений]',
    hyp: '[гипотеза из шага 5]',
    fdelta: '[базовое изменение показателя]', udelta: '[единица]', sdelta: '[данные или допущение]',
    fvolume: '[базовый объём]', uvolume: '[единица]', svolume: '[данные или допущение]',
    fprice: '[базовая стоимость единицы]', uprice: '[единица]', sprice: '[данные или допущение]',
    fkeep: '[срок сохранения, мес.]', skeep: '[данные или допущение]',
    effect: '[расчёт из шага 7]',
    result: '[метрика результата из шага 2]', target: '[целевое значение из шага 1]',
    control: '[контрольная метрика из шага 2]', missing: '[данные, которых нет, из шага 3]',
    refute: '[что опровергнет гипотезу, из шага 5]',
    seffect: '[строка «Результат» слайда из шага 8]', risk: '[строка «Риск» из шага 8]',
    first: '[строка «Действие» из шага 8]'
  };

  var PROMPTS = {
    s1: [
      { t: 'Ты — аналитик данных банка. Помоги сформулировать проблему для проекта изменений по правилам ниже. Числа бери только из таблицы, ничего не пересчитывай и не выдумывай; если чего-то нет в данных — так и напиши: нет в данных.\n\nОбъект изменений (ось «' }, { k: 'axis' }, { t: '»): ' }, { k: 'object' },
      { t: '.\nНаблюдение руководителя: ' }, { k: 'observation' },
      { t: '.\nИсточник данных: ' }, { k: 'source' },
      { t: '.\n\nДанные (разделитель — точка с запятой, десятичный знак — запятая):\n' }, { k: 'table' },
      { t: '\n\nПоказатель, который беспокоит: ' }, { k: 'focus' },
      { t: '. Его значения по таблице (посчитаны заранее, используй их как есть): ' }, { k: 'facts' },
      { t: '.\nЧто руководитель предполагает изменить: ' }, { k: 'action_in' },
      { t: '.\n\nСформулированная проблема отвечает четырём условиям: содержит показатель с его значением, период и источник; называет целевой уровень; указывает, что именно можно изменить; не содержит оценок вместо чисел.\n\nОтветь строго в формате ниже — пять строк, каждая начинается с названия поля и двоеточия, без вступления, пояснений и пустых строк:\nПроблема: <одно предложение: показатель, его значения из строки «значения по таблице» с их периодами или срезами, источник>\nПоказатель: <название столбца из таблицы как есть>\nИсточник: <источник данных одной фразой>\nЦелевое значение: <число: значение показателя, к которому стремимся, и срок; если данных для цели нет — предложи число, исходя из лучшего значения в таблице, и добавь слово «допущение»>\nЧто меняем: <предполагаемое изменение из условия, сформулированное одним предложением как действие; не заменяй его другим>' }
    ],
    s2: [
      { t: 'Ты — аналитик данных банка. Для проекта ниже подбери метрики по принципу дерева: результат — запаздывающая метрика, по которой судят об итоге; драйверы — опережающие метрики, которые наблюдаются раньше результата и на которые действует изменение; контрольная — метрика, которая не должна ухудшиться.\n\nПроблема: ' }, { k: 'problem' },
      { t: '\nЧто меняем: ' }, { k: 'action' },
      { t: '\nПоказатели, которые уже есть в данных: ' }, { k: 'columns' },
      { t: '.\nДругие показатели, которые подразделение может наблюдать: ' }, { k: 'other' },
      { t: '.\n\nПравила: результат — из показателей, которые есть в данных; драйверы выбирай так, чтобы изменение действовало на них напрямую; названия показателей из списков не переименовывай; показатели, которых нет ни в одном списке, не добавляй, кроме одного, если без него дерево не собирается, — тогда пометь его словом «новый».\n\nОтветь строго в формате ниже — четыре строки, поля разделены вертикальной чертой, без вступления и пояснений:\nРезультат: <название> | <единица измерения> | <как часто наблюдается> | <почему это запаздывающая метрика, до 12 слов>\nДрайвер 1: <название> | <единица измерения> | <как часто наблюдается> | <как влияет на результат, до 12 слов>\nДрайвер 2: <название> | <единица измерения> | <как часто наблюдается> | <как влияет на результат, до 12 слов>\nКонтрольная: <название> | <единица измерения> | <как часто наблюдается> | <что не должно ухудшиться, до 12 слов>' }
    ],
    s3: [
      { t: 'Ты — аналитик данных банка. Составь план по данным для метрик проекта: для каждой метрики определи, собирается ли она сейчас, и как получить первое проверенное значение.\n\nМетрики проекта:\n' }, { k: 'metrics' },
      { t: '\nИсточники, которые есть у подразделения: ' }, { k: 'sources' },
      { t: '.\nПоказатели, которые уже есть в выгрузке первого источника (для них статус «есть», источник — эта выгрузка, срок — дни): ' }, { k: 'columns' },
      { t: '.\n\nПравила: используй только перечисленные источники; метрика, названная так же, как показатель выгрузки, уже собирается — не проси заводить для неё новое поле; если метрику нельзя посчитать из них — статус «нет» и что нужно завести (новое поле, регулярная выгрузка, кодификатор причин); статус «частично», если данные есть, но нерегулярно или без нужного разреза; срок первого проверенного значения оценивай по частоте обновления источника.\n\nОтветь строго таблицей — по одной строке на метрику, поля разделены вертикальной чертой, без заголовка, вступления и пояснений; в первом поле — название метрики как в списке выше, без слов «результат», «драйвер», «контрольная»:\n<метрика> | <есть / частично / нет> | <источник или чего не хватает> | <как получить первое значение> | <срок: дни, недели или месяцы>' }
    ],
    s5: [
      { t: 'Ты — аналитик данных банка. Разложи результат анализа на факт, интерпретацию и гипотезу. Факт — только то, что показали числа; интерпретация — одно возможное объяснение, помеченное как предположение; гипотеза — проверяемое утверждение в форме «если …, то … изменится на … за …». Числа не пересчитывай и новых не добавляй. Гипотеза — только про изменение из строки «Что меняем»; других действий не предлагай.\n\nПроблема: ' }, { k: 'problem' },
      { t: '\nЧто меняем: ' }, { k: 'action' },
      { t: '\nРезультат анализа: ' }, { k: 'analysis' },
      { t: '\nОграничения: связь по агрегированным данным не доказывает причину; число наблюдений — ' }, { k: 'n' },
      { t: '.\n\nОтветь строго в формате ниже — четыре строки, каждая начинается с названия поля и двоеточия, без вступления и пояснений:\nФакт: <одно предложение с числами из результата анализа>\nИнтерпретация: <одно предложение, начинается со слова «Возможно»>\nГипотеза: <если [что меняем], то [показатель результата] изменится на [число или доля] за [срок]>\nЧто опровергнет: <какое наблюдение после изменения покажет, что гипотеза неверна>' }
    ],
    s6: [
      { t: 'Ты — аналитик данных банка, проверяешь допущения финансовой модели. Формула эффекта: изменение показателя × объём × стоимость единицы в месяц. Для каждого множителя и для срока сохранения эффекта укажи, подтверждён ли он данными или это допущение, и задай пессимистичное и оптимистичное значения: пессимистичное — то, при котором проект всё ещё можно защитить, оптимистичное — реалистичный верх. Значения — числа в тех же единицах, что базовое; базовые значения не меняй и эффект не считай. Если множитель равен 1 и единица «—», он не используется: напиши для него 1 | 1 | 1 | данные | не используется.\n\nПроект: ' }, { k: 'problem' },
      { t: '\nГипотеза: ' }, { k: 'hyp' },
      { t: '\nМножители:\nИзменение показателя — базовое ' }, { k: 'fdelta' }, { t: ' (' }, { k: 'udelta' }, { t: '); откуда: ' }, { k: 'sdelta' },
      { t: '\nОбъём — базовое ' }, { k: 'fvolume' }, { t: ' (' }, { k: 'uvolume' }, { t: '); откуда: ' }, { k: 'svolume' },
      { t: '\nСтоимость единицы — базовое ' }, { k: 'fprice' }, { t: ' (' }, { k: 'uprice' }, { t: '); откуда: ' }, { k: 'sprice' },
      { t: '\nСрок сохранения эффекта — базовое ' }, { k: 'fkeep' }, { t: ' мес.; откуда: ' }, { k: 'skeep' },
      { t: '\n\nОтветь строго в формате ниже — четыре строки, поля разделены вертикальной чертой, без вступления и пояснений; числа пиши без единиц измерения:\nИзменение показателя: <базовое> | <пессимистичное> | <оптимистичное> | <данные или допущение> | <обоснование, до 15 слов>\nОбъём: <базовое> | <пессимистичное> | <оптимистичное> | <данные или допущение> | <обоснование, до 15 слов>\nСтоимость единицы: <базовое> | <пессимистичное> | <оптимистичное> | <данные или допущение> | <обоснование, до 15 слов>\nСрок сохранения: <базовое> | <пессимистичное> | <оптимистичное> | <данные или допущение> | <обоснование, до 15 слов>' }
    ],
    s8: [
      { t: 'Ты — аналитик данных банка, готовишь слайд «Эффект для бизнеса» для презентации проекта. Используй только числа из расчёта ниже, не пересчитывай их и не добавляй новых; язык деловой, без оценок и призывов.\n\nПроект: ' }, { k: 'problem' },
      { t: '\nГипотеза: ' }, { k: 'hyp' },
      { t: '\nРасчёт: ' }, { k: 'effect' },
      { t: '\n\nОтветь строго в формате ниже — пять строк, каждая начинается с названия поля и двоеточия, без вступления и пояснений:\nЗаголовок: <название проекта в 5–8 слов; называет предмет, а не вывод>\nФормула: <строка «Формула» из расчёта, без изменений>\nРезультат: <строка «Результат» из расчёта, без изменений>\nРиск: <допущение из строки «Главное допущение» расчёта и его пессимистичное значение>\nДействие: <что сделать в первую очередь, чтобы подтвердить это допущение данными: какую выгрузку или сверку заказать>' }
    ],
    s9: [
      { t: 'Ты — аналитик данных банка, помогаешь руководителю написать письмо команде по итогам проекта. Письмо содержит решения, а не расчёт. Используй только сведения ниже, числа не меняй и не добавляй; деловой язык, без лозунгов и оценок людей; объём — до 250 слов.\n\nСведения о проекте:\nПроблема: ' }, { k: 'problem' },
      { t: '\nЧто меняем: ' }, { k: 'action' },
      { t: '\nМетрика результата: ' }, { k: 'result' },
      { t: '\nЦелевое значение: ' }, { k: 'target' },
      { t: '\nКонтрольная метрика: ' }, { k: 'control' },
      { t: '\nДанные, которых нет: ' }, { k: 'missing' },
      { t: '\nГипотеза: ' }, { k: 'hyp' },
      { t: '\nЧто опровергнет гипотезу: ' }, { k: 'refute' },
      { t: '\nЭффект: ' }, { k: 'seffect' },
      { t: '\nГлавное допущение: ' }, { k: 'risk' },
      { t: '\nПервое действие: ' }, { k: 'first' },
      { t: '\n\nСодержание абзацев: 1) «Что меняем и почему» — объект, проблема с числом, что меняется в работе; 2) «По какому показателю судим» — метрика результата, текущее и целевое значение, срок, контрольная метрика; 3) «Какие данные начинаем собирать» — чего не хватало, как появится, с какого момента, кто отвечает (роль, не имя); 4) «Первое действие» — что делается на следующей неделе и кем (роль); 5) «Когда пересматриваем» — когда первая сверка и условие, при котором гипотеза отклоняется.\n\nОтветь строго пятью абзацами без вступления, обращения и подписи. Каждый абзац — одна строка: название раздела, двоеточие и сразу текст абзаца. Названия разделов: Что меняем и почему; По какому показателю судим; Какие данные начинаем собирать; Первое действие; Когда пересматриваем.' }
    ]
  };

  // Сборка промпта: text — для копирования, parts — для подсветки.
  function fillPrompt(segs, vals, mode) {
    var text = '', parts = [];
    for (var i = 0; i < segs.length; i++) {
      var s = segs[i];
      if (s.t !== undefined) { text += s.t; parts.push({ t: s.t }); continue; }
      var v = vals[s.k];
      var has = v !== undefined && v !== null && clean(v) !== '';
      if (mode === 'tpl' || !has) { text += PH[s.k]; parts.push({ ph: PH[s.k] }); }
      else { text += String(v); parts.push({ v: String(v) }); }
    }
    return { text: text, parts: parts };
  }
  function promptKeys(segs) { return segs.filter(function (s) { return s.k; }).map(function (s) { return s.k; }); }

  // ── разбор ответов ─────────────────────────────────────────────────────
  function normKey(s) {
    return clean(s).toLowerCase().replace(/ё/g, 'е').replace(/[*_«»"“”:.\-–—]/g, ' ').replace(/\s+/g, ' ').trim();
  }
  function stripLine(l) {
    return clean(l).replace(/^[-*•>#:\d.)\s]+/, '').replace(/\*\*|__/g, '').replace(/^<|>$/g, '').trim();
  }
  // Строки «Ключ: значение»; ключ ищется по началу строки среди псевдонимов.
  function parseKV(text, spec) {
    var out = {}, found = 0, lines = String(text || '').split(/\r?\n/);
    var cur = null, orphans = [];
    for (var i = 0; i < lines.length; i++) {
      var l = stripLine(lines[i]);
      if (!l) { cur = null; continue; }
      var m = l.match(/^([^:|]{2,60}):\s*(.*)$/);
      var hit = null;
      if (m) {
        var k = normKey(m[1]);
        for (var f = 0; f < spec.length && !hit; f++)
          for (var a = 0; a < spec[f].aliases.length; a++)
            if (k === spec[f].aliases[a] || k.indexOf(spec[f].aliases[a]) === 0) { hit = spec[f]; break; }
      }
      if (hit) {
        if (out[hit.key] === undefined) found++;
        var val = clean(m[2]).replace(/^[«"“]|[»"”]$/g, '');
        if (/^<[^>]*>$/.test(val)) val = '';          // модель повторила шаблонное выражение
        out[hit.key] = val;
        cur = (hit.multi || val === '') ? hit.key : null;
      } else if (cur && out[cur] !== undefined) {
        var cont = l.replace(/^<[^>]*>\s*/, '');
        if (cont) out[cur] = (out[cur] + '\n' + cont).trim();   // значение на следующей строке или абзац письма
        if (!spec.filter(function (f) { return f.key === cur; })[0].multi) cur = null;
      } else if (m) {
        orphans.push(l);   // «Ключ: значение» с чужим ключом — возможно, модель переименовала поле
      } else {
        orphans.push(l);   // строка без ключа
      }
    }
    // Модель опустила названия полей: оставшиеся строки раздаются незаполненным
    // полям по порядку — формат ответа задан построчно, порядок в нём фиксирован.
    if (found < spec.length && orphans.length && !spec[0].multi) {
      var missing = spec.filter(function (f) { return out[f.key] === undefined; });
      for (var q = 0; q < missing.length && q < orphans.length; q++) {
        var ov = orphans[q].replace(/^[^:]{2,60}:\s*/, '');
        if (!ov) continue;
        out[missing[q].key] = ov; found++;
      }
    }
    return { fields: out, found: found, total: spec.length };
  }
  function splitBar(v) {
    var c = String(v || '').split('|').map(function (x) { return clean(x).replace(/^[<«"]|[>»"]$/g, ''); });
    while (c.length && c[0] === '') c.shift();                 // строка markdown-таблицы начинается с «|»
    while (c.length > 1 && c[c.length - 1] === '') c.pop();
    return c;
  }

  var SPEC = {
    s1: [
      { key: 'problem', aliases: ['проблема'] },
      { key: 'metric', aliases: ['показатель'] },
      { key: 'source', aliases: ['источник'] },
      { key: 'target', aliases: ['целевое значение', 'целевое', 'цель'] },
      { key: 'action', aliases: ['что меняем', 'изменение', 'решение', 'действие'] }
    ],
    s2: [
      { key: 'result', aliases: ['результат'] },
      { key: 'd1', aliases: ['драйвер 1', 'драйвер1', 'драйвер один', 'драйвер а'] },
      { key: 'd2', aliases: ['драйвер 2', 'драйвер2', 'драйвер два', 'драйвер б'] },
      { key: 'control', aliases: ['контрольная', 'контроль'] }
    ],
    s5: [
      { key: 'fact', aliases: ['факт'] },
      { key: 'interp', aliases: ['интерпретация'] },
      { key: 'hyp', aliases: ['гипотеза'] },
      { key: 'refute', aliases: ['что опровергнет', 'опровержение', 'опровергнет', 'проверка'] }
    ],
    s6: [
      { key: 'delta', aliases: ['изменение показателя', 'изменение', 'дельта'] },
      { key: 'volume', aliases: ['объем', 'объём'] },
      { key: 'price', aliases: ['стоимость единицы', 'стоимость', 'цена'] },
      { key: 'keep', aliases: ['срок сохранения', 'срок'] }
    ],
    s8: [
      { key: 'title', aliases: ['заголовок'] },
      { key: 'formula', aliases: ['формула'] },
      { key: 'result', aliases: ['результат'] },
      { key: 'risk', aliases: ['риск'] },
      { key: 'action', aliases: ['действие'] }
    ],
    s9: [
      { key: 'p1', aliases: ['что меняем и почему', 'что меняем'], multi: true },
      { key: 'p2', aliases: ['по какому показателю судим', 'по какому показателю', 'показатель'], multi: true },
      { key: 'p3', aliases: ['какие данные начинаем собирать', 'какие данные', 'данные'], multi: true },
      { key: 'p4', aliases: ['первое действие', 'действие'], multi: true },
      { key: 'p5', aliases: ['когда пересматриваем', 'пересмотр', 'когда'], multi: true }
    ]
  };

  function parseS1(text) { return parseKV(text, SPEC.s1); }
  function parseS2(text) {
    var r = parseKV(text, SPEC.s2), m = {};
    Object.keys(r.fields).forEach(function (k) {
      var c = splitBar(r.fields[k]);
      m[k] = { name: c[0] || '', unit: c[1] || '', freq: c[2] || '', note: c.slice(3).join(' | ') };
    });
    return { metrics: m, found: r.found, total: r.total };
  }
  function parseS3(text) {
    var rows = [], lines = String(text || '').split(/\r?\n/);
    for (var i = 0; i < lines.length; i++) {
      var l = stripLine(lines[i]);
      if (l.indexOf('|') < 0) continue;
      var c = splitBar(l).filter(function (x, j, arr) { return !(j === 0 && x === '') && !(j === arr.length - 1 && x === ''); });
      if (c.length < 3) continue;
      if (/^-{2,}/.test(c[0]) || /^метрика$/i.test(c[0])) continue;   // разделители и заголовок markdown
      var st = normKey(c[1]);
      var status = /нет/.test(st) ? 'нет' : /частич|нерегул|по запросу/.test(st) ? 'частично' : /есть|да|собир/.test(st) ? 'есть' : c[1];
      rows.push({ metric: c[0], status: status, source: c[2] || '', how: c[3] || '', term: c[4] || '' });
    }
    return { rows: rows, found: rows.length };
  }
  function parseS5(text) { return parseKV(text, SPEC.s5); }
  function parseS6(text) {
    var r = parseKV(text, SPEC.s6), a = {};
    Object.keys(r.fields).forEach(function (k) {
      var c = splitBar(r.fields[k]);
      var nums = c.slice(0, 3).map(firstNum);
      // если модель сдвинула столбцы (без базового), берём два первых числа как пес./опт.
      var rest = c.slice(3).join(' | ');
      a[k] = { base: nums[0], pess: nums[1], opt: nums[2], kind: /допущ/i.test(rest) ? 'допущение' : /данн/i.test(rest) ? 'данные' : '', why: c.slice(4).join(' | ') || c[3] || '' };
    });
    return { ass: a, found: r.found, total: r.total };
  }
  function parseS8(text) { return parseKV(text, SPEC.s8); }
  function parseS9(text) { return parseKV(text, SPEC.s9); }

  // ── экспорт проекта ────────────────────────────────────────────────────
  function projectMarkdown(st) {
    var L = [];
    function h(t) { L.push('', '## ' + t, ''); }
    L.push('# Проект: ' + or(st.s8 && st.s8.title, or(st.s1 && st.s1.object, 'без названия')));
    L.push('', 'Собрано в тренажёре сквозной практики. Каркас: проблема → метрика → данные → инструмент → анализ → вывод → эффект.');
    h('1. Проблема');
    L.push('- Объект изменений (' + or(st.s1.axis, '—') + '): ' + or(st.s1.object, '—'));
    L.push('- Проблема: ' + or(st.s1.problem, '—'));
    L.push('- Показатель: ' + or(st.s1.metric, '—') + '; источник: ' + or(st.s1.source, '—'));
    L.push('- Целевое значение: ' + or(st.s1.target, '—'));
    L.push('- Что меняем: ' + or(st.s1.action, '—'));
    h('2. Метрики');
    ['result', 'd1', 'd2', 'control'].forEach(function (k) {
      var m = st.s2.metrics[k]; if (!m || !m.name) return;
      L.push('- ' + ({ result: 'Результат', d1: 'Драйвер', d2: 'Драйвер', control: 'Контрольная' })[k] + ': ' + m.name + ' (' + or(m.unit, '—') + ', ' + or(m.freq, '—') + ') — ' + or(m.note, ''));
    });
    h('3. Данные');
    L.push('| Метрика | Статус | Источник | Как получить | Срок |', '|---|---|---|---|---|');
    (st.s3.rows || []).forEach(function (r) { L.push('| ' + [r.metric, r.status, r.source, r.how, r.term].map(function (x) { return or(x, '—'); }).join(' | ') + ' |'); });
    h('4. Инструмент и анализ');
    L.push('- Инструмент: ' + or(st.s4.tool, 'расчёт страницы тренажёра'));
    L.push('- Результат анализа: ' + or(st.s4.text, '—'));
    h('5. Вывод');
    L.push('- Факт: ' + or(st.s5.fact, '—'));
    L.push('- Интерпретация: ' + or(st.s5.interp, '—'));
    L.push('- Гипотеза: ' + or(st.s5.hyp, '—'));
    L.push('- Что опровергнет: ' + or(st.s5.refute, '—'));
    h('6. Эффект для бизнеса');
    L.push('- ' + or(st.s7.text, '—'));
    if (st.s8.title) {
      L.push('', '**Слайд «Эффект для бизнеса»**', '');
      L.push('- Заголовок: ' + st.s8.title);
      L.push('- Формула: ' + or(st.s8.formula, '—'));
      L.push('- Результат: ' + or(st.s8.result, '—'));
      L.push('- Риск: ' + or(st.s8.risk, '—'));
      L.push('- Действие: ' + or(st.s8.action, '—'));
    }
    h('7. Письмо команде');
    [['Что меняем и почему', 'p1'], ['По какому показателю судим', 'p2'], ['Какие данные начинаем собирать', 'p3'], ['Первое действие', 'p4'], ['Когда пересматриваем', 'p5']]
      .forEach(function (x) { L.push('**' + x[0] + '.** ' + or(st.s9[x[1]], '—'), ''); });
    return L.join('\n');
  }

  return {
    num: num, fi: fi, fr: fr, fmtv: fmtv, money: money, clean: clean, or: or, firstNum: firstNum,
    parseTable: parseTable, tableText: tableText, numericCols: numericCols, column: column, labels: labels, isMonthly: isMonthly,
    pearson: pearson, linfit: linfit, strength: strength, niceStep: niceStep, mean: mean,
    analysisPair: analysisPair, analysisTrend: analysisTrend, facts1: facts1,
    flows: flows, totals: totals, sensitivity: sensitivity, effectText: effectText,
    PH: PH, PROMPTS: PROMPTS, fillPrompt: fillPrompt, promptKeys: promptKeys,
    parseS1: parseS1, parseS2: parseS2, parseS3: parseS3, parseS5: parseS5, parseS6: parseS6, parseS8: parseS8, parseS9: parseS9,
    projectMarkdown: projectMarkdown
  };
});
