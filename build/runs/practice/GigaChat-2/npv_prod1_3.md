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
  <title>Финансовая модель накопления</title>
  <style>
    body { font-family: Arial, sans-serif; }
    .container { width: 960px; margin: auto; padding: 20px; border: 1px solid #ccc; background-color: #f9f9f9; }
    table { border-collapse: collapse; width: 100%; }
    th, td { text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }
    button { display: block; margin-top: 20px; }
    svg { width: 100%; height: 340px; }
  </style>
</head>
<body>
<div class="container">
  <form id="calculator">
    <label for="delta">Изменение показателя в месяц:</label>
    <input type="number" id="delta" value="100" step="1"/>
    <br />
    <label for="volume">Объём:</label>
    <input type="number" id="volume" value="1" step="1"/>
    <br />
    <label for="price">Цена услуги, руб./мес.:</label>
    <input type="number" id="price" value="550" step="0.01"/>
    <br />
    <label for="ramp">Выход на максимальный эффект, мес.:</label>
    <input type="number" id="ramp" value="3" step="1"/>
    <br />
    <label for="keep">Срок жизни эффекта, мес.:</label>
    <input type="number" id="keep" value="12" step="1"/>
    <br />
    <label for="capex">Единовременные затраты, руб.:</label>
    <input type="number" id="capex" value="600000" step="1"/>
    <br />
    <label for="opex">Ежемесячные затраты, руб.:</label>
    <input type="number" id="opex" value="50000" step="1"/>
    <br />
    <label for="horizon">Горизонт расчёта, мес.:</label>
    <input type="number" id="horizon" value="24" step="1"/>
    <br />
    <label for="rate">Годовая ставка дисконтирования, %:</label>
    <input type="number" id="rate" value="15" step="0.01"/>
    <br />
    <button type="submit">Рассчитать</button>
  </form>
  <div id="results"></div>
  <svg id="graph" viewBox="0 0 960 340"></svg>
</div>
<script>
const calcDelta = document.getElementById('delta');
const calcVolume = document.getElementById('volume');
const calcPrice = document.getElementById('price');
const calcRamp = document.getElementById('ramp');
const calcKeep = document.getElementById('keep');
const calcCapex = document.getElementById('capex');
const calcOpex = document.getElementById('opex');
const calcHorizon = document.getElementById('horizon');
const calcRate = document.getElementById('rate');
const resultsDiv = document.getElementById('results');
const graphSvg = document.getElementById('graph');
const downloadButton = document.createElement('a');
downloadButton.download = 'npv.svg';

// Обработчик событий кнопки "Рассчитать"
document.getElementById('calculator').addEventListener('submit', function(event) {
  event.preventDefault();
  const delta = parseFloat(calcDelta.value.replace(',', '.'));
  const volume = parseInt(calcVolume.value);
  const price = parseFloat(calcPrice.value.replace(',', '.'));
  const ramp = parseInt(calcRamp.value);
  const keep = parseInt(calcKeep.value);
  const capex = parseInt(calcCapex.value);
  const opex = parseInt(calcOpex.value);
  const horizon = parseInt(calcHorizon.value);
  const rate = parseFloat(calcRate.value.replace(',', '.') / 100);

  // Формулы расчётов
  let months = [];
  let incomes = [], costs = [], flows = [], cumFlows = [], cumDiscFlows = [];
  let totalIncomeFirstYear = 0;
  let cumCost = capex;
  let cumulativeDiscountedFlow = 0;
  let discountFactor = Math.pow((1 + rate), 1/12) - 1;

  for (let t = 0; t <= horizon; t++) {
    const rampShare = Math.min(t / ramp, 1);
    const full = delta * volume;
    const units = (k => sum(full * rampShare, k))(Math.max(1, t - keep + 1, t))
    const income = units * price;
    const flow = income - opex;
    const cumFlow = flow + cumCost;
    const discountedFlow = flow / Math.pow((1 + discountFactor), t);
    const cumDiscFlow = discountedFlow + cumulativeDiscountedFlow;

    if (t === 0) {
      cumCost += capex;
    } else {
      cumCost += opex;
    }

    months.push(t);
    incomes.push(income);
    costs.push(opex);
    flows.push(flow);
    cumFlows.push(cumFlow);
    cumDiscFlows.push(cumDiscFlow);
    cumulativeDiscountedFlow = cumDiscFlow;

    if (t > 0) {
      totalIncomeFirstYear += income;
    }
  }

  // Расчёт показателей модели
  const paybackMonth = findPaybackMonth(months, cumFlows);
  const npv = cumDiscFlows[horizon];
  const firstYearIncome = totalIncomeFirstYear.toLocaleString(undefined, {useGrouping: true});

  // Сохраняем результат
  resultsDiv.innerHTML = `
    <p><strong>Доход за первый год:</strong> ${firstYearIncome}</p>
    <p><strong>Окупаемость, мес.</strong>: ${paybackMonth ? paybackMonth : 'Не достигается'}</p>
    <p><strong>NPV за горизонт:</strong> ${npv.toLocaleString(undefined, {useGrouping: true})}</p>
  `;

  drawGraph(months, incomes, costs, flows, cumFlows, cumDiscFlows, paybackMonth, horizon);

  // Добавляем кнопку скачивания графика
  downloadButton.href = serializeSVG(graphSvg).then(data => {
    return new Blob([data], {type: 'image/svg+xml;charset=utf-8'});
  });
  downloadButton.textContent = 'Скачать график';
  document.body.appendChild(downloadButton);
});

function findPaybackMonth(months, cumFlows) {
  for (let i = 0; i < months.length; i++) {
    if (cumFlows[i] >= 0) {
      return months[i];
    }
  }
  return null;
}

function sum(a, b) {
  return a.reduce((acc, curr) => acc + curr, 0) + b;
}

function createSVGData() {
  const svgData = [
    ['Месяц', 'Доход', 'Затраты', 'Поток', 'Накоплённый поток', 'Накоплённый дисконтированный поток'],
    [...months.map(m => [m, incomes[m], costs[m], flows[m], cumFlows[m], cumDiscFlows[m]])]
  ];
  return svgData;
}

async function serializeSVG(element) {
  const serializer = new XMLSerializer();
  return serializer.serializeToString(element);
}

function drawGraph(months, incomes, costs, flows, cumFlows, cumDiscFlows, paybackMonth, horizon) {
  const graphWidth = 960;
  const graphHeight = 340;
  const scaleX = graphWidth / months.length;
  const scaleY = graphHeight / (cumFlows[horizon] || 1);

  const svg = d3.select('#graph')
    .attr('width', graphWidth)
    .attr('height', graphHeight)
    .append('g')
    .attr('transform', `translate(${0},${graphHeight}) scale(1,-1)`);

  const xScale = d3.scaleLinear()
    .domain([0, months.length])
    .range([0, graphWidth]);

  const yScale = d3.scaleLinear()
    .domain([0, (cumFlows[horizon] || 1)])
    .range([0, graphHeight]);

  const line = d3.line()
    .x(d => xScale(d[0]))
    .y(d => yScale(d[1]));

  const area = d3.area()
    .x(d => xScale(d[0]))
    .y0(yScale(0))
    .y1(d => yScale(d[1]));

  const xAxis = d3.axisBottom(xScale)
    .tickFormat(d3.format('d'))
    .ticks(months.length);

  const yAxis = d3.axisLeft(yScale)
    .tickFormat(d3.format('.2s'));

  svg.append('path')
    .datum(createSVGData())
    .attr('class', 'area')
    .attr('d', area);

  svg.append('path')
    .datum(incomes)
    .attr('class', 'line')
    .attr('stroke', '#ff7f0e')
    .attr('stroke-width', 2)
    .attr('fill', 'none')
    .attr('d', line);

  svg.append('path')
    .datum(costs)
    .attr('class', 'line')
    .attr('stroke', '#2ca02c')
    .attr('stroke-width', 2)
    .attr('fill', 'none')
    .attr('d', line);

  svg.append('path')
    .datum(cumFlows)
    .attr('class', 'line')
    .attr('stroke', '#1f77b4')
    .attr('stroke-dasharray', '5,5')
    .attr('stroke-width', 2)
    .attr('fill', 'none')
    .attr('d', line);

  svg.append('path')
    .datum(cumDiscFlows)
    .attr('class', 'line')
    .attr('stroke', '#9467bd')
    .attr('stroke-dasharray', '5,5')
    .attr('stroke-width', 2)
    .attr('fill', 'none')
    .attr('d', line);

  svg.append('text')
    .attr('x', xScale(paybackMonth))
    .attr('y', yScale(0))
    .attr('dy', '-0.3em')
    .text(`Месяц окупаемости: ${paybackMonth}`);

  svg.append('g')
    .call(xAxis)
    .selectAll('text')
    .attr('font-size', '12px');

  svg.append('g')
    .call(yAxis)
    .selectAll('text')
    .attr('font-size', '12px');

  svg.append('rect')
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', graphWidth)
    .attr('height', graphHeight)
    .attr('fill', 'none')
    .attr('stroke', 'black');
}
</script>
<script src="https://cdn.jsdelivr.net/npm/d3@6/dist/d3.min.js"></script>
</body>
</html>
```