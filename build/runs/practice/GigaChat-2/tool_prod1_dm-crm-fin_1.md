# промпт

```
Допиши мини-инструмент: одностраничный HTML-файл, который читает несколько CSV-выгрузок, считает входы дерева метрик проекта «Накопительный счёт: удержание закрываемых счетов» и параметры финансовой модели. Основа файла ниже уже готова: чтение файлов, перетаскивание, вывод и график написаны. Нужно заполнить функцию computeInputs — расчёт каждого входа по описанию — и вернуть файл целиком, ничего больше не меняя.

Данные: 3 CSV-файла, кодировка UTF-8 с меткой порядка байтов, разделитель — точка с запятой, десятичный знак — запятая. В функцию computeInputs файлы приходят объектом tables: ключ — имя файла, значение — массив строк; строка — объект с ключами из заголовка файла, числа уже переведены в числа, месяц — строка вида «2025-01», порядок строк как в файле.

Файл 1 «closures_dm.csv» — вход closures («Закрытия счетов в месяц», счетов в месяц). Первые строки:
﻿месяц;закрытые_счета;активные_счета
2024-01;1521;60452
2024-02;1449;63243
2024-03;1509;67165
Расчёт входа closures: среднее значение столбца закрытые_счета за последние 12 строк (месяцев).

Файл 2 «linked_crm.csv» — вход linked («Доля закрытий после обращения», доля от 0 до 1). Первые строки:
﻿месяц;закрытых_счетов_всего;закрытий_после_обращения
2024-01;1521;266
2024-02;1449;224
2024-03;1509;222
Расчёт входа linked: сумма столбца закрытий_после_обращения ÷ сумма столбца закрытых_счетов_всего по всем строкам.

Файл 3 «margin_fin.csv» — вход margin («Маржа на счёт в месяц», руб.). Первые строки:
﻿параметр;значение
средний_остаток_тыс_руб;220
маржа_проц_годовых;3
срок_жизни_счёта_мес;12
Расчёт входа margin: средний_остаток_тыс_руб × 1000 × маржа_проц_годовых ÷ 100 ÷ 12.

Правила для computeInputs: столбцы брать по названию из заголовка, например row["название_столбца"]; «последние 12 строк» — последние 12 элементов массива (arr.slice(-12)); при свёртке по месяцам сначала сложить значения строк с одинаковым месяцем, потом взять последние 12 месяцев по порядку; если файла нет — оставить null; имена переменных латиницей, комментарии по-русски; без async, fetch и внешних библиотек.

Основа файла:
```html
<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>Параметры проекта: Накопительный счёт: удержание закрываемых счетов</title>
<style>body{font-family:Arial,sans-serif;max-width:900px;margin:24px auto;padding:0 16px;color:#222}.drop{border:2px dashed #999;border-radius:12px;padding:24px;text-align:center;color:#555}.drop.over{border-color:#2a9d5c;background:#f0faf4}table{border-collapse:collapse;width:100%;margin:12px 0}td,th{border-bottom:1px solid #ddd;padding:6px 8px;text-align:left}.tile{display:inline-block;min-width:200px;margin:8px 16px 8px 0}.tile b{display:block;font-size:26px}.line{font-family:monospace;background:#f4f4f4;padding:8px 10px;border-radius:8px}#status{color:#b33}</style></head><body>
<h1>Параметры проекта: Накопительный счёт: удержание закрываемых счетов</h1>
<div class="drop" id="drop">Перетащите сюда файлы closures_dm.csv, linked_crm.csv, margin_fin.csv или <label><u>выберите их</u><input type="file" id="files" multiple accept=".csv" style="display:none"></label></div>
<p id="status"></p><div id="out"></div><div id="chart"></div>
<script>
var FILES = ["closures_dm.csv","linked_crm.csv","margin_fin.csv"];
var tables = {};
function parseCsv(text) {
  var lines = text.replace(/^\uFEFF/, "").split(/\r?\n/).filter(function (l) { return l.trim() !== ""; });
  var head = lines[0].split(";").map(function (h) { return h.trim(); }), rows = [];
  for (var i = 1; i < lines.length; i++) {
    var cells = lines[i].split(";"), row = {};
    for (var j = 0; j < head.length; j++) { var v = (cells[j] || "").trim(); var n = parseFloat(v.replace(",", ".")); row[head[j]] = (v !== "" && !isNaN(n)) ? n : v; }
    rows.push(row);
  }
  if (head.length === 2 && head[0] === "параметр") { var wide = {}; rows.forEach(function (r) { wide[r["параметр"]] = r["значение"]; }); rows.forEach(function (r) { for (var k in wide) if (r[k] === undefined) r[k] = wide[k]; }); }
  return rows;
}
if (!Number.prototype.replace) Number.prototype.replace = function () { return String(this); };
if (typeof FileList !== "undefined" && !FileList.prototype.forEach) FileList.prototype.forEach = Array.prototype.forEach;
function computeInputs(tables) {
  // closures — Закрытия счетов в месяц (счетов в месяц): среднее значение столбца закрытые_счета за последние 12 строк (месяцев)
  var closures = null; // ЗАПОЛНИТЬ по описанию выше из tables["closures_dm.csv"]
  // linked — Доля закрытий после обращения (доля от 0 до 1): сумма столбца закрытий_после_обращения ÷ сумма столбца закрытых_счетов_всего по всем строкам
  var linked = null; // ЗАПОЛНИТЬ по описанию выше из tables["linked_crm.csv"]
  // margin — Маржа на счёт в месяц (руб.): средний_остаток_тыс_руб × 1000 × маржа_проц_годовых ÷ 100 ÷ 12
  // файл margin_fin.csv — таблица параметр;значение: значение параметра — tables["margin_fin.csv"][0]["имя_параметра"]
  var margin = null; // ЗАПОЛНИТЬ по описанию выше из tables["margin_fin.csv"]
  return { closures: closures, linked: linked, margin: margin };
}
function fmt(v) { return (v === null || v === undefined || isNaN(v)) ? "—" : String(Math.round(v * 100) / 100).replace(".", ","); }
function render() {
  var missing = FILES.filter(function (f) { return !tables[f]; });
  if (missing.length) { document.getElementById("status").textContent = "Ожидаются файлы: " + missing.join(", "); return; }
  var x = computeInputs(tables);
  var delta = x.closures * x.linked * 1/3;
  var volume = 1;
  var price = x.margin;
  var h = "<h2>Входы</h2><table><tr><th>Вход</th><th>Значение</th></tr>";
  h += "<tr><td>Закрытия счетов в месяц (closures)</td><td>" + fmt(x.closures) + " счетов в месяц</td></tr>";
  h += "<tr><td>Доля закрытий после обращения (linked)</td><td>" + fmt(x.linked) + " доля от 0 до 1</td></tr>";
  h += "<tr><td>Маржа на счёт в месяц (margin)</td><td>" + fmt(x.margin) + " руб.</td></tr>";
  h += "</table><h2>Параметры финансовой модели</h2>";
  h += "<div class=tile><b>" + fmt(delta) + "</b>Изменение показателя, предотвращённых закрытий в месяц</div>";
  h += "<div class=tile><b>" + fmt(volume) + "</b>Объём, —</div>";
  h += "<div class=tile><b>" + fmt(price) + "</b>Стоимость единицы, руб. маржи на счёт в месяц</div>";
  h += "<p>Маржинальный доход от удержанных счетов: <b>" + fmt(delta * volume * price) + "</b> руб. в месяц на когорту</p>";
  h += "<p class=line>delta=" + delta + "; volume=" + volume + "; price=" + price + "</p>";
  document.getElementById("status").textContent = ""; document.getElementById("out").innerHTML = h;
  drawChart();
}
function drawChart() {
  var rows = tables[FILES[0]]; if (!rows || rows[0]["месяц"] === undefined) return;
  var col = Object.keys(rows[0]).filter(function (k) { return k !== "месяц" && typeof rows[0][k] === "number"; })[0]; if (!col) return;
  var by = {}, order = []; rows.forEach(function (r) { var m = String(r["месяц"]); if (by[m] === undefined) { by[m] = 0; order.push(m); } by[m] += r[col]; });
  var ys = order.map(function (m) { return by[m]; }), W = 860, H = 260, L = 60, B = 40, mx = Math.max.apply(null, ys), mn = Math.min.apply(null, ys); if (mx === mn) { mx += 1; mn -= 1; }
  var X = function (i) { return L + (W - L - 20) * i / Math.max(1, ys.length - 1); }, Y = function (v) { return 20 + (H - 20 - B) * (mx - v) / (mx - mn); };
  var d = ys.map(function (v, i) { return (i ? "L" : "M") + X(i).toFixed(1) + " " + Y(v).toFixed(1); }).join(" ");
  var s = "<h2>" + col + " по месяцам</h2><svg viewBox=\"0 0 " + W + " " + H + "\" width=\"100%\" xmlns=\"http://www.w3.org/2000/svg\">";
  s += "<path d=\"" + d + "\" fill=\"none\" stroke=\"#2a9d5c\" stroke-width=\"3\"/>";
  s += "<text x=\"" + (L - 6) + "\" y=\"24\" font-size=\"12\" text-anchor=\"end\">" + fmt(mx) + "</text><text x=\"" + (L - 6) + "\" y=\"" + (H - B) + "\" font-size=\"12\" text-anchor=\"end\">" + fmt(mn) + "</text>";
  order.forEach(function (m, i) { if (i % 3 === 0 || i === order.length - 1) s += "<text x=\"" + X(i).toFixed(1) + "\" y=\"" + (H - 12) + "\" font-size=\"11\" text-anchor=\"middle\">" + m + "</text>"; });
  document.getElementById("chart").innerHTML = s + "</svg>";
}
function readFiles(list) {
  Array.prototype.slice.call(list).forEach(function (file) {
    if (FILES.indexOf(file.name) < 0) { document.getElementById("status").textContent = "Файл не из списка: " + file.name; return; }
    var rd = new FileReader(); rd.onload = function () { tables[file.name] = parseCsv(rd.result); render(); }; rd.readAsText(file, "utf-8");
  });
}
var drop = document.getElementById("drop");
drop.addEventListener("dragover", function (e) { e.preventDefault(); drop.className = "drop over"; });
drop.addEventListener("dragleave", function () { drop.className = "drop"; });
drop.addEventListener("drop", function (e) { e.preventDefault(); drop.className = "drop"; readFiles(e.dataTransfer.files); });
document.getElementById("files").addEventListener("change", function () { readFiles(this.files); });
render();
</script></body></html>
```

Ответ — только полный HTML-файл в тройных кавычках, без пояснений.
```

# ответ

**"""
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Параметры проекта: Накопительный счёт: удержание закрываемых счетов</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 900px; margin: 24px auto; padding: 0 16px; color: #222 }
    .drop { border: 2px dashed #999; border-radius: 12px; padding: 24px; text-align: center; color: #555 }
    .drop.over { border-color: #2a9d5c; background: #f0faf4 }
    table { border-collapse: collapse; width: 100%; margin: 12px 0 }
    td, th { border-bottom: 1px solid #ddd; padding: 6px 8px; text-align: left }
    .tile { display: inline-block; min-width: 200px; margin: 8px 16px 8px 0 }
    .tile b { display: block; font-size: 26px }
    .line { font-family: monospace; background: #f4f4f4; padding: 8px 10px; border-radius: 8px }
    #status { color: #b33 }
  </style>
</head>
<body>
  <h1>Параметры проекта: Накопительный счёт: удержание закрываемых счетов</h1>
  <div class="drop" id="drop">Перетащите сюда файлы closures_dm.csv, linked_crm.csv, margin_fin.csv или 
    <label><u>выберите их</u>
      <input type="file" id="files" multiple accept=".csv" style="display: none"></label>
  </div>
  <p id="status"></p>
  <div id="out"></div>
  <div id="chart"></div>
  
  <script>
    var FILES = ["closures_dm.csv", "linked_crm.csv", "margin_fin.csv"];
    var tables = {};
    
    function parseCsv(text) {
      var lines = text.replace(/^\uFEFF/, "")
        .split(/\r?\n/)
        .filter(function(l) { return l.trim() !== ""; });
      var head = lines[0].split(";")
        .map(function(h) { return h.trim(); }),
        rows = [];
      for (var i = 1; i < lines.length; i++) {
        var cells = lines[i].split(";");
        var row = {};
        for (var j = 0; j < head.length; j++) {
          var v = (cells[j] || "").trim();
          var n = parseFloat(v.replace(",", "."));
          row[head[j]] = (v !== "" && !isNaN(n)) ? n : v;
        }
        rows.push(row);
      }
      if (head.length === 2 && head[0] === "параметр") {
        var wide = {};
        rows.forEach(function(r) { wide[r["параметр"]] = r["значение"]; });
        rows.forEach(function(r) {
          for (var k in wide) if (r[k] === undefined) r[k] = wide[k];
        });
      }
      return rows;
    }
    
    if (!Number.prototype.replace) Number.prototype.replace = function() { return String(this); };
    if (typeof FileList !== "undefined" && !FileList.prototype.forEach) FileList.prototype.forEach =
      Array.prototype.forEach;
    
    function computeInputs(tables) {
      // closures — Закрытия счетов в месяц (счетов в месяц): среднее значение столбца закрытые_счета за последние 12 строк (месяцев)
      var closures = null;
      if (tables["closures_dm.csv"]) {
        var rows = tables["closures_dm.csv"];
        var lastTwelveRows = rows.slice(-12);
        closures = lastTwelveRows.reduce((acc, row) => acc + row.closed_accounts, 0) / 12;
      }
      
      // linked — Доля закрытий после обращения (доля от 0 до 1): сумма столбца закрытий_после_обращения ÷ сумма столбца закрытых_счетов_всего по всем строкам
      var linked = null;
      if (tables["linked_crm.csv"]) {
        var totalClosedAccounts = tables["linked_crm.csv"].reduce(
          (acc, row) => acc + row.closed_accounts_total,
          0
        );
        var closedAfterContact = tables["linked_crm.csv"].reduce(
          (acc, row) => acc + row.closed_after_contact,
          0
        );
        linked = closedAfterContact / totalClosedAccounts;
      }
      
      // margin — Маржа на счёт в месяц (руб.): средний_остаток_тыс_руб × 1000 × маржа_проц_годовых ÷ 100 ÷ 12
      var margin = null;
      if (tables["margin_fin.csv"]) {
        var data = tables["margin_fin.csv"][0];
        var avgBalance = data.avg_balance_thousand_rub * 1000;
        var annualInterestRate = data.interest_rate_percentage_yearly;
        var monthsInLife = data.life_span_months;
        margin = avgBalance * annualInterestRate / 100 / monthsInLife;
      }
      
      return { closures: closures, linked: linked, margin: margin };
    }
    
    function fmt(v) {
      return (v === null || v === undefined || isNaN(v)) ? "—" : String(Math.round(v * 100) / 100).replace(".", ",");
    }
    
    function render() {
      var missing = FILES.filter(f => !tables[f]);
      if (missing.length) {
        document.getElementById("status").textContent = "Ожидаются файлы: " + missing.join(", ");
        return;
      }
      var inputs = computeInputs(tables);
      var delta = inputs.closures * inputs.linked * 1 / 3;
      var volume = 1;
      var price = inputs.margin;
      var h = `
        <h2>Входы</h2>
        <table>
          <tr>
            <th>Вход</th>
            <th>Значение</th>
          </tr>
          <tr>
            <td>Закрытия счетов в месяц (closures)</td>
            <td>${fmt(inputs.closures)} счетов в месяц</td>
          </tr>
          <tr>
            <td>Доля закрытий после обращения (linked)</td>
            <td>${fmt(inputs.linked)} доля от 0 до 1</td>
          </tr>
          <tr>
            <td>Маржа на счёт в месяц (margin)</td>
            <td>${fmt(inputs.margin)} руб.</td>
          </tr>
        </table>
        <h2>Параметры финансовой модели</h2>
        <div class="tile"><b>${fmt(delta)}</b> Изменение показателя, предотвращённых закрытий в месяц</div>
        <div class="tile"><b>${fmt(volume)}</b> Объём, —</div>
        <div class="tile"><b>${fmt(price)}</b> Стоимость единицы, руб. маржи на счёт в месяц</div>
        <p>Маржинальный доход от удержанных счетов: <b>${fmt(delta * volume * price)}</b> руб. в месяц на когорту</p>
        <p class="line">delta=${delta}; volume=${volume}; price=${price}</p>
      `;
      document.getElementById("status").textContent = "";
      document.getElementById("out").innerHTML = h;
      drawChart();
    }
    
    function drawChart() {
      var rows = tables[FILES[0]];
      if (!rows || rows[0]["month"] === undefined) return;
      var col = Object.keys(rows[0])
        .filter(k => k !== "month" && typeof rows[0][k] === "number")[0];
      if (!col) return;
      var by = {}, order = [];
      rows.forEach(r => {
        var month = String(r["month"]);
        if (by[month] === undefined) {
          by[month] = 0;
          order.push(month);
        }
        by[month] += r[col];
      });
      var ys = order.map(m => by[m]), W = 860, H = 260, L = 60, B = 40, mx = Math.max(...ys),
        mn = Math.min(...ys);
      if (mx === mn) { mx += 1; mn -= 1; }
      var X = i => L + (W - L - 20) * i / Math.max(1, ys.length - 1);
      var Y = v => 20 + (H - 20 - B) * (mx - v) / (mx - mn);
      var d = ys.map((v, i) => (i ? "L" : "M") + X(i).toFixed(1) + " " + Y(v).toFixed(1)).join(" ");
      var svg = `<h2>${col} по месяцам</h2>
        <svg viewBox="0 0 ${W} ${H}" width="100%" xmlns="http://www.w3.org/2000/svg">
          <path d="${d}" fill="none" stroke="#2a9d5c" stroke-width="3"/>
          <text x="${L - 6}" y="24" font-size="12" text-anchor="end">${fmt(mx)}</text>
          <text x="${L - 6}" y="${H - B}" font-size="12" text-anchor="end">${fmt(mn)}</text>
          ${order.map(m => m % 3 === 0 || m === order.length - 1 ? `<text x="${X(m)}" y="${H - 12}" font-size="11" text-anchor="middle">${m}</text>` : "")}
        </svg>`;
      document.getElementById("chart").innerHTML = svg;
    }
    
    function readFiles(files) {
      files.forEach(file => {
        if (FILES.indexOf(file.name) < 0) {
          document.getElementById("status").textContent = "Файл не из списка: " + file.name;
          return;
        }
        const reader = new FileReader();
        reader.onload = function() { tables[file.name] = parseCsv(reader.result); render(); };
        reader.readAsText(file, "utf-8");
      });
    }
    
    var drop = document.getElementById("drop");
    drop.addEventListener("dragover", e => { e.preventDefault(); drop.className = "drop over"; });
    drop.addEventListener("dragleave", () => drop.className = "drop");
    drop.addEventListener("drop", e => {
      e.preventDefault();
      drop.className = "drop";
      readFiles(e.dataTransfer.files);
    });
    document.getElementById("files").addEventListener("change", () => readFiles(this.files));
    
    render();
  </script>
</body>
</html>
"""**