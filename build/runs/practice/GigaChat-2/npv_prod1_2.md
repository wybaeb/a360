# промпт

```
Сделай одностраничный HTML-инструмент: финансовая модель эффекта проекта «Накопительный счёт: удержание закрываемых счетов» — поток эффекта по месяцам, окупаемость и NPV, график в SVG с кнопкой сохранения.

Параметры — поля ввода со значениями по умолчанию и кнопка «Рассчитать» (расчёт также при загрузке страницы):
delta = 100 — изменение показателя в месяц (предотвращённых закрытий в месяц)
volume = 1 — объём (—)
price = 550 — стоимость единицы, руб. в месяц (руб. маржи на счёт в месяц)
ramp = 3 — выход на полный уровень, мес.
keep = 12 — срок сохранения эффекта, мес.
capex = 600000 — единовременные затраты, руб.
opex = 50000 — ежемесячные затраты, руб.
horizon = 24 — горизонт, мес.
rate = 0.15 — годовая ставка дисконтирования, доля

Расчёт по месяцам t от 0 до horizon (повтори формулы точно):
— доля выхода на уровень: ramp_share(t) = min(t / ramp, 1), при ramp = 0 равна 1;
— full = delta × volume;
— units(t) для t ≥ 1: сумма full × ramp_share(k) по k от max(1, t − keep + 1) до t (когорты каждого месяца живут keep месяцев);
— income(t) = units(t) × price; income(0) = 0;
— cost(0) = capex; cost(t) = opex для t ≥ 1;
— cf(t) = income(t) − cost(t); cum(t) — накопленная сумма cf;
— месячная ставка m = (1 + rate)^(1/12) − 1; disc(t) = cf(t) / (1 + m)^t; cum_disc(t) — накопленная сумма disc;
— окупаемость — первый месяц t ≥ 1, где cum(t) ≥ 0 (если нет — «не достигается»); NPV = cum_disc(horizon); доход за первый год — сумма income(t) для t от 1 до 12.

Вывод: три числа крупно с названиями — «Доход за первый год», «Окупаемость, мес.», «NPV за горизонт» (рубли — с разделителями тысяч, без копеек); под ними таблица по месяцам: t, доход, затраты, поток, накопленный поток, накопленный дисконтированный.
График — inline SVG шириной 100 % (viewBox 0 0 960 340): столбики дохода по месяцам, линия накопленного потока, пунктирная линия накопленного дисконтированного потока, вертикальная отметка месяца окупаемости с подписью, подписи оси месяцев и сетка значений; всё без внешних библиотек.
Кнопка «Сохранить SVG»: сериализовать элемент svg через XMLSerializer, сделать Blob с типом image/svg+xml;charset=utf-8, скачать через ссылку с атрибутом download="npv.svg". В корневой элемент svg добавить атрибут xmlns="http://www.w3.org/2000/svg", чтобы файл открывался отдельно.

Требования к коду: один HTML-файл без внешних библиотек и запросов в сеть; имена переменных и функций латиницей, русский только в подписях; без async и await; числа из полей разбирать после замены запятой на точку.

Проверь себя: при значениях по умолчанию окупаемость — месяц 7, NPV за 24 мес. около 8,03 млн руб, доход за первый год около 3,65 млн руб. Если получилось иначе — проверь формулу units(t) и дисконтирование.

Ответ — только полный HTML-файл в тройных кавычках, без пояснений.
```

# ответ

```
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Финансовая модель Накопительного счёта</title>
  <style>
    body { font-family: Arial, sans-serif; }
    .container { width: 960px; margin: auto; padding: 20px; background-color: #fafafa; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,.1);}
    input { display: block; margin-bottom: 10px; width: 100%; }
    button { margin-top: 10px; width: 100%; }
    table { border-collapse: collapse; width: 100%; }
    th, td { text-align: center; padding: 8px; border: 1px solid #ddd; }
    svg { width: 100%; height: 340px; }
    .line { fill: none; stroke-width: 2; }
    .bar { fill: steelblue; }
    .disc-line { stroke-dasharray: 3,3; }
    .month-label { text-anchor: middle; alignment-baseline: central; font-size: 12px; }
  </style>
</head>
<body>
<div class="container">
  <input type="number" id="delta" value="100"> Предотвращённые закрытия в месяц
  <input type="number" id="volume" value="1"> Объём (количество счетов)
  <input type="number" id="price" value="550"> Стоимость счета в месяц, руб.
  <input type="number" id="ramp" value="3"> Время выхода на максимальный эффект, мес.
  <input type="number" id="keep" value="12"> Срок сохранения эффекта, мес.
  <input type="number" id="capex" value="600000"> Единовременные затраты, руб.
  <input type="number" id="opex" value="50000"> Ежемесячные затраты, руб.
  <input type="number" id="horizon" value="24"> Горизонт расчётов, мес.
  <input type="number" id="rate" step="0.01" value="0.15"> Годовая ставка дисконтирования, %
  <button onclick="calculate()">Рассчитать</button>
  
  <div id="results"></div>
  <table id="table-data">
    <thead><tr><th>Месяц</th><th>Доход</th><th>Затраты</th><th>Поток</th><th>Накопленный поток</th><th>Дисконтированный поток</th></tr></thead>
    <tbody></tbody>
  </table>
  
  <svg id="chart" viewBox="0 0 960 340"></svg>
</div>
<script>
const delta = document.getElementById('delta');
const volume = document.getElementById('volume');
const price = document.getElementById('price');
const ramp = document.getElementById('ramp');
const keep = document.getElementById('keep');
const capex = document.getElementById('capex');
const opex = document.getElementById('opex');
const horizon = document.getElementById('horizon');
const rate = document.getElementById('rate');
const results = document.getElementById('results');
const chart = document.getElementById('chart');
const tableData = document.getElementById('table-data');

let monthLabels = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];

function calculate() {
  const fields = [delta.valueAsNumber, volume.valueAsNumber, price.valueAsNumber,
                  ramp.valueAsNumber, keep.valueAsNumber, capex.valueAsNumber,
                  opex.valueAsNumber, horizon.valueAsNumber, parseFloat(rate.value)];

  if (!fields.every(x => x)) return alert("Заполните все обязательные поля!");

  let totalIncome = 0, cumulativeFlow = 0, cumulativeDisc = 0;
  const m = Math.pow((1 + rate.value), 1/12) - 1;
  const rampShare = [];
  for (let i=0; i<horizon.valueAsNumber; i++) {
    rampShare[i] = Math.min(i/ramp.valueAsNumber, 1);
  }

  const data = Array.from({length:horizon.valueAsNumber}, (_, t) => {
    let full = delta.valueAsNumber * volume.valueAsNumber;
    let units = 0;
    for (let k=max(1, t - keep.valueAsNumber + 1); k<=t; k++) {
      units += full * rampShare[k-1];
    }
    let income = units * price.valueAsNumber;
    let cost = (t === 0 ? capex.valueAsNumber : opex.valueAsNumber);
    let flow = income - cost;
    let disc = flow / (1 + m)**t;
    cumulativeFlow += flow;
    cumulativeDisc += disc;
    return [t+1, income, cost, flow, cumulativeFlow, cumulativeDisc];
  });

  // Расчёт итоговых показателей
  const firstYearIncome = data.slice(0, 12).reduce((sum, [_, inc]) => sum + inc, 0);
  const paybackMonth = data.findIndex(d => d[5] >= 0) + 1 || 'Не достигнута';
  const npv = cumulativeDisc[horizon.valueAsNumber-1];

  // Заполнение таблицы и графика
  data.forEach((d, idx) => {
    const [month, income, cost, flow, cumFlow, cumDisc] = d;
    tableData.tBodies[0].insertRow().append(...[
      document.createTextNode(month),
      document.createTextNode(income.toLocaleString()),
      document.createTextNode(cost.toLocaleString()),
      document.createTextNode(flow.toLocaleString()),
      document.createTextNode(cumFlow.toLocaleString()),
      document.createTextNode(cumDisc.toFixed(2))
    ]);
  });

  // Создание SVG-графика
  const svg = chart.getSVGDocument();
  const defs = svg.createElementNS('http://www.w3.org/2000/svg', 'defs');
  const barStyle = svg.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
  barStyle.setAttribute('id', 'bar-gradient');
  barStyle.setAttribute('x1', '0%'); barStyle.setAttribute('y1', '0%');
  barStyle.setAttribute('x2', '0%'); barStyle.setAttribute('y2', '100%');
  barStyle.setAttribute('gradientUnits', 'objectBoundingBox');
  barStyle.appendChild(svg.createElementNS('http://www.w3.org/2000/svg', 'stop'));
  barStyle.firstChild.setAttribute('offset', '0%');
  barStyle.firstChild.setAttribute('stop-color', 'steelblue');
  barStyle.lastChild.setAttribute('offset', '100%');
  barStyle.lastChild.setAttribute('stop-color', 'lightsteelblue');
  defs.appendChild(barStyle);
  svg.appendChild(defs);

  const g = svg.createElementNS('http://www.w3.org/2000/svg', 'g');
  g.setAttribute('transform', `translate(10, 30)`);

  const rect = svg.createElementNS('http://www.w3.org/2000/svg', 'rect');
  rect.setAttribute('width', '940');
  rect.setAttribute('height', '250');
  rect.setAttribute('fill', 'none');
  g.appendChild(rect);

  const barGroup = svg.createElementNS('http://www.w3.org/2000/svg', 'g');
  barGroup.setAttribute('transform', `translate(10, 50)`);
  data.forEach(([month, _, __, flow], idx) => {
    const bar = svg.createElementNS('http://www.w3.org/2000/svg', 'rect');
    bar.setAttribute('x', `${idx*30}`);
    bar.setAttribute('y', `${250-flow}`);
    bar.setAttribute('width', '25');
    bar.setAttribute('height', `${flow}`);
    bar.setAttribute('fill', 'url(#bar-gradient)');
    barGroup.appendChild(bar);
  });

  const line = svg.createElementNS('http://www.w3.org/2000/svg', 'path');
  line.setAttribute('class', 'line');
  line.setAttribute('d', `M 0 ${250} L 940 250`);
  g.appendChild(line);

  const discLine = svg.createElementNS('http://www.w3.org/2000/svg', 'path');
  discLine.setAttribute('class', 'disc-line');
  discLine.setAttribute('d', `M 0 0 L 940 0`);
  g.appendChild(discLine);

  const labels = svg.createElementNS('http://www.w3.org/2000/svg', 'text');
  labels.setAttribute('class', 'month-label');
  labels.setAttribute('x', '470');
  labels.setAttribute('y', '270');
  labels.textContent = 'Накопленный дисконтированный поток';
  g.appendChild(labels);

  const months = svg.createElementNS('http://www.w3.org/2000/svg', 'g');
  months.setAttribute('transform', `translate(10, 300)`);
  monthLabels.forEach((label, idx) => {
    const labelEl = svg.createElementNS('http://www.w3.org/2000/svg', 'text');
    labelEl.setAttribute('class', 'month-label');
    labelEl.setAttribute('x', `${idx*30+15}`);
    labelEl.setAttribute('y', '20');
    labelEl.textContent = label;
    months.appendChild(labelEl);
  });

  const paybackMark = svg.createElementNS('http://www.w3.org/2000/svg', 'circle');
  paybackMark.setAttribute('cx', `${data.findIndex(d => d[5] >= 0)*30+15}`);
  paybackMark.setAttribute('cy', '250');
  paybackMark.setAttribute('r', '5');
  paybackMark.setAttribute('stroke', 'red');
  paybackMark.setAttribute('stroke-width', '2');
  paybackMark.setAttribute('fill', 'none');
  g.appendChild(paybackMark);

  const paybackLabel = svg.createElementNS('http://www.w3.org/2000/svg', 'text');
  paybackLabel.setAttribute('class', 'month-label');
  paybackLabel.setAttribute('x', `${paybackMark.getAttribute('cx')}`);
  paybackLabel.setAttribute('y', '270');
  paybackLabel.textContent = `Срок окупаемости: ${paybackMonth}`;
  g.appendChild(paybackLabel);

  svg.appendChild(g);

  // Обновление результата расчёта
  results.innerHTML = `
    Доход за первый год: ${firstYearIncome.toLocaleString()} рублей.<br />
    Окупаемость, мес.: ${paybackMonth}<br />
    NPV за горизонт: ${npv.toLocaleString()} рублей.`;
}

// Вызываем расчёт при старте страницы
window.onload = () => calculate();

// Сохранение графика в SVG
document.querySelector('#save-svg').addEventListener('click', function() {
  const serializer = new XMLSerializer();
  const xml = serializer.serializeToString(chart.getSVGDocument());
  const blob = new Blob([xml], {type: 'image/svg+xml;charset=utf-8'});
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = 'npv.svg';
  link.click();
});
</script>
</body>
</html>
```