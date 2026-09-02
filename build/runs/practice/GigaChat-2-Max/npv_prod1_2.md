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

```html
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Финансовая модель Накопительного счёта</title>
<style>
body { font-family: Arial, sans-serif; }
input[type=number], input[type=text] { width: 100px; margin-right: 10px; text-align: right; }
button { padding: 5px 10px; cursor: pointer; }
table { border-collapse: collapse; width: 100%; margin-top: 20px; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
th { background-color: #f2f2f2; }
.output h2 { display: inline-block; margin-right: 30px; font-size: 24px; }
svg { width: 100%; height: auto; }
.gridline { stroke-dasharray: 5,5; stroke-width: 1; opacity: 0.5; }
.text-label { dominant-baseline: middle; text-anchor: middle; }
.income-bar { fill: steelblue; }
.cum-line { stroke: black; stroke-width: 2; }
.disc-cum-line { stroke: red; stroke-width: 2; stroke-dasharray: 5,5; }
.break-even-marker { stroke: green; stroke-width: 2; }
</style>
<script>
function calculate() {
    const inputs = document.querySelectorAll('input');
    let params = {};
    for(let i = 0; i < inputs.length; i++) {
        if(inputs[i].type === 'number') {
            params[inputs[i].id] = parseFloat(inputs[i].value.replace(',', '.'));
        } else {
            params[inputs[i].id] = inputs[i].value.trim();
        }
    }
    
    // Расчет модели
    function rampShare(t, ramp) {
        return Math.min((t / ramp), 1);
    }
    
    const { delta, volume, price, ramp, keep, capex, opex, horizon, rate } = params;
    const months = [];
    let cumIncome = 0, cumCF = 0, cumDisc = 0;
    const monthlyRate = Math.pow(1 + rate, 1/12) - 1;
    
    for(let t = 0; t <= horizon; t++) {
        let rampSharesSum = 0;
        
        for(let k = Math.max(1, t - keep + 1); k <= t; k++) {
            rampSharesSum += rampShare(k, ramp);
        }
        
        const units = delta * volume * rampSharesSum;
        const income = t > 0 ? units * price : 0;
        const cost = t == 0 ? capex : opex;
        const cashFlow = income - cost;
        const discountFactor = 1 / Math.pow(1 + monthlyRate, t);
        const discountedCashFlow = cashFlow * discountFactor;
        
        cumIncome += income;
        cumCF += cashFlow;
        cumDisc += discountedCashFlow;
        
        months.push({
            month: t,
            income,
            cost,
            cashFlow,
            cumCF,
            discountedCashFlow,
            cumDisc
        });
    }
    
    // Найти месяц окупаемости
    let paybackMonth = null;
    for(let i = 1; i <= horizon; i++) {
        if(months[i].cumCF >= 0 && !paybackMonth) {
            paybackMonth = i;
        }
    }
    paybackMonth = paybackMonth || 'Не достигается';
    
    // Подготовка вывода
    const firstYearIncome = months.slice(1, 13).reduce((acc, m) => acc + m.income, 0);
    const npvHorizon = months[horizon].cumDisc.toFixed(2);
    
    document.getElementById('first-year-income').innerText = formatNumber(firstYearIncome);
    document.getElementById('payback-month').innerText = paybackMonth;
    document.getElementById('npv-horizon').innerText = formatNumber(npvHorizon);
    
    renderTable(months);
    renderChart(months, paybackMonth);
}

// Форматирует число с разделителем тысяч
function formatNumber(num) {
    return num.toLocaleString('ru-RU', { maximumFractionDigits: 0 });
}

// Рендерит таблицу
function renderTable(data) {
    const tableBody = document.getElementById('data-table-body');
    while(tableBody.firstChild) {
        tableBody.removeChild(tableBody.firstChild);
    }
    
    data.forEach(row => {
        const tr = document.createElement('tr');
        ['month', 'income', 'cost', 'cashFlow', 'cumCF', 'discountedCashFlow', 'cumDisc'].forEach(key => {
            const cell = document.createElement('td');
            cell.innerText = key.startsWith('cum') ? formatNumber(row[key]) : row[key];
            tr.appendChild(cell);
        });
        tableBody.appendChild(tr);
    });
}

// Рендерит график
function renderChart(data, breakEvenMonth) {
    const w = 960, h = 340, barWidth = 20, xPadding = 40, yPadding = 30;
    const yMax = d3.max(data.map(d => d.income)) * 1.1;
    const yScale = d3.scaleLinear().domain([0, yMax]).range([h - yPadding, yPadding]);
    const xScale = d3.scaleBand().domain(data.map(d => d.month)).range([xPadding, w - xPadding]).paddingInner(0.2);
    
    const svgEl = document.getElementById('chart-svg');
    svgEl.setAttribute('width', w);
    svgEl.setAttribute('height', h);
    svgEl.innerHTML = '';
    
    // Столбцы доходов
    data.forEach(d => {
        const rectHeight = yScale(0) - yScale(d.income);
        const barX = xScale(d.month) + xScale.bandwidth()/2 - barWidth/2;
        const barY = yScale(d.income);
        const barRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        barRect.setAttribute('class', 'income-bar');
        barRect.setAttribute('x', barX);
        barRect.setAttribute('y', barY);
        barRect.setAttribute('width', barWidth);
        barRect.setAttribute('height', rectHeight);
        svgEl.appendChild(barRect);
    });
    
    // Линии кумулятивного CF и дисконтированного CF
    const lineGenerator = d3.line()
        .x(d => xScale(d.month) + xScale.bandwidth()/2)
        .y(d => yScale(d.cumCF))
        .curve(d3.curveMonotoneX);
    
    const discLineGenerator = d3.line()
        .x(d => xScale(d.month) + xScale.bandwidth()/2)
        .y(d => yScale(d.cumDisc))
        .curve(d3.curveMonotoneX);
    
    const pathCum = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    pathCum.setAttribute('d', lineGenerator(data));
    pathCum.setAttribute('class', 'cum-line');
    svgEl.appendChild(pathCum);
    
    const pathDiscCum = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    pathDiscCum.setAttribute('d', discLineGenerator(data));
    pathDiscCum.setAttribute('class', 'disc-cum-line');
    svgEl.appendChild(pathDiscCum);
    
    // Отметка точки окупаемости
    if(breakEvenMonth !== 'Не достигается' && breakEvenMonth != null) {
        const markerLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        markerLine.setAttribute('class', 'break-even-marker');
        markerLine.setAttribute('x1', xScale(parseInt(breakEvenMonth)));
        markerLine.setAttribute('x2', xScale(parseInt(breakEvenMonth)));
        markerLine.setAttribute('y1', yPadding);
        markerLine.setAttribute('y2', h - yPadding);
        svgEl.appendChild(markerLine);
    }
    
    // Оси и метки
    const gridLinesCount = 5;
    const stepSize = yMax / gridLinesCount;
    for(let i = 0; i <= gridLinesCount; i++) {
        const value = i * stepSize;
        const yPos = yScale(value);
        const gridLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        gridLine.setAttribute('class', 'gridline');
        gridLine.setAttribute('x1', xPadding);
        gridLine.setAttribute('x2', w - xPadding);
        gridLine.setAttribute('y1', yPos);
        gridLine.setAttribute('y2', yPos);
        svgEl.appendChild(gridLine);
        
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('class', 'text-label');
        label.setAttribute('x', xPadding - 10);
        label.setAttribute('y', yPos + 5);
        label.innerText = formatNumber(Math.round(value));
        svgEl.appendChild(label);
    }
    
    // Метки осей X
    data.forEach(d => {
        const tickLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        tickLabel.setAttribute('class', 'text-label');
        tickLabel.setAttribute('x', xScale(d.month) + xScale.bandwidth()/2);
        tickLabel.setAttribute('y', h - yPadding + 20);
        tickLabel.innerText = d.month;
        svgEl.appendChild(tickLabel);
    });
}

// Сохранение графика
function saveSVG() {
    const serializer = new XMLSerializer();
    const svgData = serializer.serializeToString(document.getElementById("chart-svg"));
    const blob = new Blob([`<?xml version="1.0" standalone="no"?>\n${svgData}`], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'npv.svg';
    link.click();
    URL.revokeObjectURL(url);
}

window.onload = () => {
    calculate(); // Рассчитываем сразу при загрузке страницы
};
</script>
</head>
<body>
<h1>Финансовая модель эффекта проекта "Накопительный счет"</h1>
<div style="display: flex; align-items: center; gap: 10px;">
    <label>Изменение показателя в месяц:</label><input id="delta" type="number" value="100"><br/>
    <label>Объём:</label><input id="volume" type="number" value="1"><br/>
    <label>Стоимость единицы:</label><input id="price" type="number" value="550"><br/>
    <label>Выход на уровень:</label><input id="ramp" type="number" value="3"><br/>
    <label>Срок сохранения эффекта:</label><input id="keep" type="number" value="12"><br/>
    <label>Единовременные затраты:</label><input id="capex" type="number" value="600000"><br/>
    <label>Ежемесячные затраты:</label><input id="opex" type="number" value="50000"><br/>
    <label>Горизонт:</label><input id="horizon" type="number" value="24"><br/>
    <label>Годовая ставка дисконтирования:</label><input id="rate" type="number" value="0.15"><br/>
    <button onclick="calculate()">Рассчитать</button>
</div>
<div class="output">
    <h2>Доход за первый год: </h2><span id="first-year-income"></span><br />
    <h2>Окупаемость, мес.: </h2><span id="payback-month"></span><br />
    <h2>NPV за горизонт: </h2><span id="npv-horizon"></span>
</div>
<table id="data-table">
    <thead>
        <tr>
            <th>Месяц</th>
            <th>Доход</th>
            <th>Затраты</th>
            <th>Поток</th>
            <th>Накопл. поток</th>
            <th>Дисконт.</th>
            <th>Накопл. дисконт.</th>
        </tr>
    </thead>
    <tbody id="data-table-body"></tbody>
</table>
<div>
    <button onclick="saveSVG()">Сохранить SVG</button>
</div>
<svg id="chart-svg" viewBox="0 0 960 340" xmlns="http://www.w3.org/2000/svg"></svg>
</body>
</html>
```