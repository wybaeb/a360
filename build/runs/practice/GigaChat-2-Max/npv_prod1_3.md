# промпт

```
Допиши мини-инструмент финансовой модели проекта «Накопительный счёт: удержание закрываемых счетов»: одностраничный HTML-файл с полями параметров, расчётом потока эффекта по месяцам, окупаемостью, NPV, таблицей и графиком SVG с кнопкой сохранения. Основа файла ниже готова: поля, вывод, таблица, график и сохранение написаны. Нужно заполнить функцию effectFlows(p) по формулам и вернуть файл целиком, ничего больше не меняя.

Поля p — числа: delta (изменение показателя в месяц), volume (объём), price (стоимость единицы, руб. в месяц), ramp (выход на полный уровень, мес.), keep (срок сохранения эффекта, мес.), capex (единовременные затраты, руб.), opex (ежемесячные затраты, руб.), horizon (горизонт, мес.), rate (годовая ставка дисконтирования, доля). Функция возвращает массив из horizon + 1 объектов для t = 0, 1, …, horizon с полями t, income, cost, cf, cum, cum_disc.

Формулы:
— доля выхода на уровень rampShare(t) = min(t / ramp, 1); при ramp = 0 равна 1;
— full = delta × volume;
— units(t) для t ≥ 1: сумма full × rampShare(k) по k от max(1, t − keep + 1) до t (когорты каждого месяца живут keep месяцев);
— income(t) = units(t) × price; income(0) = 0;
— cost(0) = capex; cost(t) = opex для t ≥ 1;
— cf(t) = income(t) − cost(t); cum(t) — накопленная сумма cf от 0 до t;
— месячная ставка m = (1 + rate)^(1/12) − 1; disc(t) = cf(t) / (1 + m)^t; cum_disc(t) — накопленная сумма disc от 0 до t.

Правила: обычный цикл for, имена латиницей, комментарии по-русски; без async и внешних библиотек; поля p уже числа.

Основа файла:
```html
<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>Финансовая модель: Накопительный счёт: удержание закрываемых счетов</title>
<style>body{font-family:Arial,sans-serif;max-width:960px;margin:24px auto;padding:0 16px;color:#222}label{display:inline-block;margin:0 14px 10px 0;font-size:14px}label span{display:block;color:#666;font-size:12px}input{font:inherit;padding:5px 8px;width:140px}button{font:inherit;padding:8px 16px;border:0;border-radius:8px;background:#2a9d5c;color:#fff;cursor:pointer}.tile{display:inline-block;min-width:220px;margin:8px 16px 8px 0}.tile b{display:block;font-size:26px}table{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px}td,th{border-bottom:1px solid #ddd;padding:5px 8px;text-align:left}#status{color:#b33}</style></head><body>
<h1>Финансовая модель эффекта: Накопительный счёт: удержание закрываемых счетов</h1>
<div id="form"></div><button type="button" id="calc">Рассчитать</button> <button type="button" id="save">Сохранить SVG</button>
<p id="status"></p><div id="out"></div><div id="chart"></div><div id="tab"></div>
<script>
var FIELDS = [["delta", "Изменение показателя в месяц, предотвращённых закрытий в месяц", 100], ["volume", "Объём, —", 1], ["price", "Стоимость единицы, руб. в месяц", 550], ["ramp", "Выход на полный уровень, мес.", 3], ["keep", "Срок сохранения эффекта, мес.", 12], ["capex", "Единовременные затраты, руб.", 600000], ["opex", "Ежемесячные затраты, руб.", 50000], ["horizon", "Горизонт, мес.", 24], ["rate", "Ставка дисконтирования, доля в год", 0.15]];
document.getElementById("form").innerHTML = FIELDS.map(function (f) { return "<label>" + f[1] + "<span>" + f[0] + "</span><input id=\"f-" + f[0] + "\" value=\"" + f[2] + "\"></label>"; }).join("");
function num(v) { var n = parseFloat(String(v).replace(",", ".")); return isNaN(n) ? 0 : n; }
function money(x) { var a = Math.abs(x), s = a >= 1e6 ? (a / 1e6).toFixed(2).replace(".", ",") + " млн руб." : Math.round(a).toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " руб."; return (x < 0 ? "−" : "") + s; }
function effectFlows(p) {
  // ЗАПОЛНИТЬ по формулам из задания: вернуть массив из horizon + 1 объектов {t, income, cost, cf, cum, cum_disc} для t = 0..horizon
  var rows = [];
  return rows;
}
function calc() {
  var p = {}; FIELDS.forEach(function (f) { p[f[0]] = num(document.getElementById("f-" + f[0]).value); });
  var rows = effectFlows(p);
  if (!rows || rows.length !== Math.round(p.horizon) + 1) { document.getElementById("status").textContent = "Функция effectFlows должна вернуть horizon + 1 строк"; return; }
  var pb = null, y1 = 0; rows.forEach(function (r) { if (r.t > 0 && pb === null && r.cum >= 0) pb = r.t; if (r.t >= 1 && r.t <= 12) y1 += r.income; });
  var npv = rows[rows.length - 1].cum_disc;
  document.getElementById("status").textContent = "";
  document.getElementById("out").innerHTML = "<div class=tile><b>" + money(y1) + "</b>Доход за первый год</div><div class=tile><b>" + (pb === null ? "не достигается" : "месяц " + pb) + "</b>Окупаемость</div><div class=tile><b>" + money(npv) + "</b>NPV за " + Math.round(p.horizon) + " мес.</div>";
  var t = "<table><tr><th>Мес.</th><th>Доход</th><th>Затраты</th><th>Поток</th><th>Накопленный</th><th>Накопленный дисконтированный</th></tr>";
  rows.forEach(function (r) { t += "<tr><td>" + r.t + "</td><td>" + money(r.income) + "</td><td>" + money(r.cost) + "</td><td>" + money(r.cf) + "</td><td>" + money(r.cum) + "</td><td>" + money(r.cum_disc) + "</td></tr>"; });
  document.getElementById("tab").innerHTML = t + "</table>";
  drawChart(rows, pb, Math.round(p.horizon));
}
function drawChart(rows, pb, H) {
  var W = 960, HH = 340, L = 80, R = 30, T = 20, B = 40, pw = W - L - R, ph = HH - T - B, mx = 0, mn = 0;
  rows.forEach(function (r) { mx = Math.max(mx, r.cum, r.income); mn = Math.min(mn, r.cum, -r.cost); }); if (mx === mn) { mx = 1; mn = -1; }
  var y = function (v) { return T + ph * (mx - v) / (mx - mn); }, x = function (t) { return L + pw * t / H; }, bw = Math.max(3, pw / (H + 1) * 0.34);
  var s = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 " + W + " " + HH + "\" width=\"100%\" font-family=\"Arial\"><rect width=\"" + W + "\" height=\"" + HH + "\" fill=\"#fff\"/>";
  s += "<line x1=\"" + L + "\" x2=\"" + (W - R) + "\" y1=\"" + y(0) + "\" y2=\"" + y(0) + "\" stroke=\"#999\"/>";
  rows.forEach(function (r) { var cx = x(r.t); if (r.income > 0) s += "<rect x=\"" + (cx - bw) + "\" y=\"" + y(r.income) + "\" width=\"" + bw + "\" height=\"" + (y(0) - y(r.income)) + "\" fill=\"#2a9d5c\" fill-opacity=\"0.5\"/>"; if (r.cost > 0) s += "<rect x=\"" + cx + "\" y=\"" + y(0) + "\" width=\"" + bw + "\" height=\"" + (y(-r.cost) - y(0)) + "\" fill=\"#555\" fill-opacity=\"0.4\"/>"; });
  s += "<path d=\"" + rows.map(function (r, i) { return (i ? "L" : "M") + x(r.t).toFixed(1) + " " + y(r.cum).toFixed(1); }).join(" ") + "\" fill=\"none\" stroke=\"#1e7a47\" stroke-width=\"3\"/>";
  s += "<path d=\"" + rows.map(function (r, i) { return (i ? "L" : "M") + x(r.t).toFixed(1) + " " + y(r.cum_disc).toFixed(1); }).join(" ") + "\" fill=\"none\" stroke=\"#1e7a47\" stroke-width=\"2\" stroke-dasharray=\"6 5\"/>";
  if (pb !== null) s += "<line x1=\"" + x(pb) + "\" x2=\"" + x(pb) + "\" y1=\"" + T + "\" y2=\"" + (T + ph) + "\" stroke=\"#c33\" stroke-dasharray=\"4 4\"/><text x=\"" + (x(pb) + 6) + "\" y=\"" + (T + 14) + "\" font-size=\"13\" fill=\"#c33\">окупаемость: месяц " + pb + "</text>";
  for (var t = 0; t <= H; t += 3) s += "<text x=\"" + x(t) + "\" y=\"" + (HH - 14) + "\" font-size=\"12\" text-anchor=\"middle\">" + t + "</text>";
  s += "<text x=\"" + (L - 6) + "\" y=\"" + (y(mx) + 12) + "\" font-size=\"12\" text-anchor=\"end\">" + money(mx) + "</text><text x=\"" + (L - 6) + "\" y=\"" + y(mn) + "\" font-size=\"12\" text-anchor=\"end\">" + money(mn) + "</text>";
  document.getElementById("chart").innerHTML = s + "</svg>";
}
document.getElementById("calc").onclick = calc;
document.getElementById("save").onclick = function () { var svg = document.querySelector("#chart svg"); if (!svg) return; var blob = new Blob([new XMLSerializer().serializeToString(svg)], { type: "image/svg+xml;charset=utf-8" }); var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "npv.svg"; document.body.appendChild(a); a.click(); document.body.removeChild(a); };
calc();
</script></body></html>
```

Ответ — только полный HTML-файл в тройных кавычках, без пояснений.
```

# ответ

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Финансовая модель: Накопительный счёт: удержание закрываемых счетов</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 960px;
      margin: 24px auto;
      padding: 0 16px;
      color: #222;
    }
    label {
      display: inline-block;
      margin: 0 14px 10px 0;
      font-size: 14px;
    }
    label span {
      display: block;
      color: #666;
      font-size: 12px;
    }
    input {
      font: inherit;
      padding: 5px 8px;
      width: 140px;
    }
    button {
      font: inherit;
      padding: 8px 16px;
      border: 0;
      border-radius: 8px;
      background: #2a9d5c;
      color: #fff;
      cursor: pointer;
    }
    .tile {
      display: inline-block;
      min-width: 220px;
      margin: 8px 16px 8px 0;
    }
    .tile b {
      display: block;
      font-size: 26px;
    }
    table {
      border-collapse: collapse;
      width: 100%;
      margin: 12px 0;
      font-size: 14px;
    }
    td,
    th {
      border-bottom: 1px solid #ddd;
      padding: 5px 8px;
      text-align: left;
    }
    #status {
      color: #b33;
    }
  </style>
</head>
<body>
  <h1>Финансовая модель эффекта: Накопительный счёт: удержание закрываемых счетов</h1>
  <div id="form"></div>
  <button type="button" id="calc">Рассчитать</button>
  <button type="button" id="save">Сохранить SVG</button>
  <p id="status"></p>
  <div id="out"></div>
  <div id="chart"></div>
  <div id="tab"></div>
  <script>
    var FIELDS = [
      ["delta", "Изменение показателя в месяц, предотвращённых закрытий в месяц", 100],
      ["volume", "Объём, —", 1],
      ["price", "Стоимость единицы, руб. в месяц", 550],
      ["ramp", "Выход на полный уровень, мес.", 3],
      ["keep", "Срок сохранения эффекта, мес.", 12],
      ["capex", "Единовременные затраты, руб.", 600000],
      ["opex", "Ежемесячные затраты, руб.", 50000],
      ["horizon", "Горизонт, мес.", 24],
      ["rate", "Ставка дисконтирования, доля в год", 0.15]
    ];
    document.getElementById("form").innerHTML = FIELDS.map(function(f) {
      return "<label>" + f[1] + "<span>" + f[0] + "</span><input id=\"f-" + f[0] + "\" value=\"" + f[2] + "\"></label>";
    }).join("");
    
    function num(v) {
      var n = parseFloat(String(v).replace(",", "."));
      return isNaN(n) ? 0 : n;
    }
    
    function money(x) {
      var a = Math.abs(x),
          s = a >= 1e6 ? (a / 1e6).toFixed(2).replace(".", ",") + " млн руб." : Math.round(a).toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " руб.";
      return (x < 0 ? "-" : "") + s;
    }
    
    function effectFlows(p) {
      var rows = [], 
          rampShare = function(t) { return Math.min((t / p.ramp), 1); },
          full = p.delta * p.volume,
          m = Math.pow(1 + p.rate, 1 / 12) - 1, // месячная ставка дисконтирования
          cumIncome = 0, cumCF = 0, cumDisc = 0;
      
      for (var t = 0; t <= p.horizon; t++) {
        var income = 0, cost = 0, cf = 0, disc = 0;
        
        if (t == 0) {
          income = 0;
          cost = p.capex;
        } else {
          var startK = Math.max(1, t - p.keep + 1),
              endK = t;
          
          // подсчёт дохода
          for (var k = startK; k <= endK; k++) {
            income += full * rampShare(k);
          }
          income *= p.price;
          
          // ежемесячные расходы
          cost = p.opex;
        }
        
        // денежный поток и накопленные суммы
        cf = income - cost;
        cumIncome += income;
        cumCF += cf;
        disc = cf / Math.pow(1 + m, t);
        cumDisc += disc;
        
        rows.push({t: t, income: income, cost: cost, cf: cf, cum: cumCF, cum_disc: cumDisc});
      }
      
      return rows;
    }
    
    function calc() {
      var p = {};
      FIELDS.forEach(function(f) { p[f[0]] = num(document.getElementById("f-" + f[0]).value); });
      var rows = effectFlows(p);
      if (!rows || rows.length !== Math.round(p.horizon) + 1) {
        document.getElementById("status").textContent = "Функция effectFlows должна вернуть horizon + 1 строк";
        return;
      }
      var pb = null, y1 = 0;
      rows.forEach(function(r) {
        if (r.t > 0 && pb === null && r.cum >= 0) pb = r.t;
        if (r.t >= 1 && r.t <= 12) y1 += r.income;
      });
      var npv = rows[rows.length - 1].cum_disc;
      document.getElementById("status").textContent = "";
      document.getElementById("out").innerHTML =
        "<div class='tile'><b>" + money(y1) + "</b> Доход за первый год</div>" +
        "<div class='tile'><b>" + (pb === null ? "не достигается" : "месяц " + pb) + "</b> Окупаемость</div>" +
        "<div class='tile'><b>" + money(npv) + "</b> NPV за " + Math.round(p.horizon) + " мес.</div>";
  
      var t = "<table><tr><th>Мес.</th><th>Доход</th><th>Затраты</th><th>Поток</th><th>Накопленный</th><th>Накопленный дисконтированный</th></tr>";
      rows.forEach(function(r) {
        t += "<tr><td>" + r.t + "</td><td>" + money(r.income) + "</td><td>" + money(r.cost) + "</td><td>" + money(r.cf) + "</td><td>" + money(r.cum) + "</td><td>" + money(r.cum_disc) + "</td></tr>";
      });
      document.getElementById("tab").innerHTML = t + "</table>";
      drawChart(rows, pb, Math.round(p.horizon));
    }
    
    function drawChart(rows, pb, H) {
      var W = 960, HH = 340, L = 80, R = 30, T = 20, B = 40, pw = W - L - R, ph = HH - T - B, mx = 0, mn = 0;
      rows.forEach(function(r) { mx = Math.max(mx, r.cum, r.income); mn = Math.min(mn, r.cum, -r.cost); });
      if (mx === mn) { mx = 1; mn = -1; }
      var y = function(v) { return T + ph * (mx - v) / (mx - mn); },
          x = function(t) { return L + pw * t / H; },
          bw = Math.max(3, pw / (H + 1) * 0.34);
      var s = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 " + W + " " + HH + "\" width=\"100%\" font-family=\"Arial\"><rect width=\"" + W + "\" height=\"" + HH + "\" fill=\"#fff\"/>";
      s += "<line x1=\"" + L + "\" x2=\"" + (W - R) + "\" y1=\"" + y(0) + "\" y2=\"" + y(0) + "\" stroke=\"#999\"/>";
      rows.forEach(function(r) {
        var cx = x(r.t);
        if (r.income > 0) s += "<rect x=\"" + (cx - bw) + "\" y=\"" + y(r.income) + "\" width=\"" + bw + "\" height=\"" + (y(0) - y(r.income)) + "\" fill=\"#2a9d5c\" fill-opacity=\"0.5\"/>";
        if (r.cost > 0) s += "<rect x=\"" + cx + "\" y=\"" + y(0) + "\" width=\"" + bw + "\" height=\"" + (y(-r.cost) - y(0)) + "\" fill=\"#555\" fill-opacity=\"0.4\"/>";
      });
      s += "<path d=\"" + rows.map(function(r, i) { return (i ? "L" : "M") + x(r.t).toFixed(1) + " " + y(r.cum).toFixed(1); }).join(" ") + "\" fill=\"none\" stroke=\"#1e7a47\" stroke-width=\"3\"/>";
      s += "<path d=\"" + rows.map(function(r, i) { return (i ? "L" : "M") + x(r.t).toFixed(1) + " " + y(r.cum_disc).toFixed(1); }).join(" ") + "\" fill=\"none\" stroke=\"#1e7a47\" stroke-width=\"2\" stroke-dasharray=\"6 5\"/>";
      if (pb !== null) s += "<line x1=\"" + x(pb) + "\" x2=\"" + x(pb) + "\" y1=\"" + T + "\" y2=\"" + (T + ph) + "\" stroke=\"#c33\" stroke-dasharray=\"4 4\"/><text x=\"" + (x(pb) + 6) + "\" y=\"" + (T + 14) + "\" font-size=\"13\" fill=\"#c33\">окупаемость: месяц " + pb + "</text>";
      for (var t = 0; t <= H; t += 3) s += "<text x=\"" + x(t) + "\" y=\"" + (HH - 14) + "\" font-size=\"12\" text-anchor=\"middle\">" + t + "</text>";
      s += "<text x=\"" + (L - 6) + "\" y=\"" + (y(mx) + 12) + "\" font-size=\"12\" text-anchor=\"end\">" + money(mx) + "</text><text x=\"" + (L - 6) + "\" y=\"" + y(mn) + "\" font-size=\"12\" text-anchor=\"end\">" + money(mn) + "</text>";
      document.getElementById("chart").innerHTML = s + "</svg>";
    }
    
    document.getElementById("calc").onclick = calc;
    document.getElementById("save").onclick = function() {
      var svg = document.querySelector("#chart svg");
      if (!svg) return;
      var blob = new Blob([new XMLSerializer().serializeToString(svg)], {type: "image/svg+xml;charset=utf-8"});
      var a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "npv.svg";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    };
    calc();
  </script>
</body>
</html>
```