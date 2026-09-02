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
    .form-control { width: 100%; padding: 10px; margin-bottom: 15px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { text-align: center; padding: 8px; border: 1px solid #ddd; }
    button { background-color: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer; }
    svg { display: block; width: 100%; height: auto; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Финансовая модель накопления счета</h1>
    <form id="financial-model">
      <label for="delta">Изменение показателя (закрытий/мес.): </label>
      <input type="text" id="delta" value="100" required>
      <label for="volume">Объём (количество): </label>
      <input type="text" id="volume" value="1" required>
      <label for="price">Цена услуги (руб./мес.): </label>
      <input type="text" id="price" value="550" required>
      <label for="ramp">Выход на уровень (месяцев): </label>
      <input type="text" id="ramp" value="3" required>
      <label for="keep">Срок удержания (месяцев): </label>
      <input type="text" id="keep" value="12" required>
      <label for="capex">Единовременные затраты (руб.): </label>
      <input type="text" id="capex" value="600000" required>
      <label for="opex">Операционные расходы (руб./мес.): </label>
      <input type="text" id="opex" value="50000" required>
      <label for="horizon">Горизонт расчёта (месяцев): </label>
      <input type="text" id="horizon" value="24" required>
      <label for="rate">Годовая ставка дисконтирования (%): </label>
      <input type="text" id="rate" value="15" required>
      <button type="submit">Рассчитать</button>
    </form>
    <div id="results"></div>
    <svg id="chart-svg" viewBox="0 0 960 340" preserveAspectRatio="none"></svg>
  </div>
  
  <script>
    const deltaInput = document.getElementById('delta');
    const volumeInput = document.getElementById('volume');
    const priceInput = document.getElementById('price');
    const rampInput = document.getElementById('ramp');
    const keepInput = document.getElementById('keep');
    const capexInput = document.getElementById('capex');
    const opexInput = document.getElementById('opex');
    const horizonInput = document.getElementById('horizon');
    const rateInput = document.getElementById('rate');
    
    const inputs = [deltaInput, volumeInput, priceInput, rampInput, keepInput, capexInput, opexInput, horizonInput, rateInput];

    function parseFloatOrDefault(input, defaultValue) {
      return isNaN(parseFloat(input.value)) ? defaultValue : parseFloat(input.value.replace(',', '.'));
    }

    function calculate() {
      const delta = parseFloatOrDefault(deltaInput, 100);
      const volume = parseFloatOrDefault(volumeInput, 1);
      const price = parseFloatOrDefault(priceInput, 550);
      const ramp = parseFloatOrDefault(rampInput, 3);
      const keep = parseFloatOrDefault(keepInput, 12);
      const capex = parseFloatOrDefault(capexInput, 600000);
      const opex = parseFloatOrDefault(opexInput, 50000);
      const horizon = parseFloatOrDefault(horizonInput, 24);
      const rate = parseFloatOrDefault(rateInput, 0.15);
      
      // Расчёт
      let units = [];
      let income = [];
      let cost = [];
      let flow = [];
      let cumFlow = [];
      let cumDisc = [];
      let cumulativeCost = capex;
      let cumulativeIncome = 0;
      let discountFactor = Math.pow((1 + rate / 100), 1 / 12) - 1;

      for (let t = 0; t <= horizon; t++) {
        const rampShare = t >= ramp ? 1 : t / ramp;
        const full = delta * volume;
        const unitsT = full * rampShare * Math.min(t - keep + 1, t);
        const incomeT = unitsT * price;
        const costT = t > 0 ? opex : capex;
        const flowT = incomeT - costT;
        const cumFlowT = flowT + cumFlow[cumFlow.length - 1] || 0;
        const discT = flowT / Math.pow(1 + discountFactor, t);
        const cumDiscT = discT + cumDisc[cumDisc.length - 1] || 0;
        
        units.push(unitsT);
        income.push(incomeT);
        cost.push(costT);
        flow.push(flowT);
        cumFlow.push(cumFlowT);
        cumDisc.push(cumDiscT);
      }

      // Окончательные значения
      const firstYearIncome = income.slice(1, 13).reduce((acc, val) => acc + val, 0);
      const paybackMonth = cumFlow.findIndex(v => v >= 0) + 1;
      const npv = cumDisc[horizon];

      // Результаты
      const resultsDiv = document.getElementById('results');
      resultsDiv.innerHTML = `
        <p><strong>Доход за первый год:</strong> ${firstYearIncome.toLocaleString()} рублей</p>
        <p><strong>Окупаемость, мес.:</strong> ${paybackMonth}</p>
        <p><strong>NPV за горизонт:</strong> ${npv.toLocaleString()} рублей</p>
      `;

      // График
      const chartSvg = document.getElementById('chart-svg');
      chartSvg.innerHTML = '';

      const lineHeight = 300;
      const barWidth = 20;
      const totalBars = 12;
      const yScale = lineHeight / (cumFlow[cumFlow.length - 1]);

      const g = chartSvg.appendChild(document.createElementNS("http://www.w3.org/2000/svg", 'g'));

      g.appendChild(createBarChart(units, barWidth, totalBars, lineHeight, yScale));
      g.appendChild(createLineChart(cumFlow, yScale, lineHeight));
      g.appendChild(createDiscountedLineChart(cumDisc, yScale, lineHeight));
      g.appendChild(createPaybackMarker(paybackMonth, yScale, lineHeight));
      createAxes(g, yScale, lineHeight);
    }

    function createBarChart(data, barWidth, totalBars, lineHeight, yScale) {
      const bars = data.map((value, index) => {
        const x = index * barWidth;
        const y = lineHeight - value * yScale;
        return `<rect x="${x}" y="${y}" width="${barWidth}" height="${lineHeight - y}" fill="steelblue"/>`;
      });
      return bars.join('');
    }

    function createLineChart(data, yScale, lineHeight) {
      const points = data.map((value, index) => {
        const x = index * 20;
        const y = lineHeight - value * yScale;
        return `<circle cx="${x}" cy="${y}" r="3" fill="red"/>`;
      });
      return `<path d="M0,${lineHeight} L${data.length * 20},${lineHeight}" stroke="black"/>
               ${points.join('')}`;
    }

    function createDiscountedLineChart(data, yScale, lineHeight) {
      const points = data.map((value, index) => {
        const x = index * 20;
        const y = lineHeight - value * yScale;
        return `<circle cx="${x}" cy="${y}" r="3" fill="green"/>`;
      });
      return `<path d="M0,${lineHeight} L${data.length * 20},${lineHeight}" stroke-dasharray="5,5" stroke="green"/>
               ${points.join('')}`;
    }

    function createPaybackMarker(month, yScale, lineHeight) {
      const markerX = month * 20;
      const markerY = lineHeight - 20;
      return `<line x1="${markerX}" y1="${markerY}" x2="${markerX}" y2="${lineHeight}" stroke="black"/>
              <text x="${markerX}" y="${markerY}" dy="1em">Месяц окупаемости</text>`;
    }

    function createAxes(g, yScale, lineHeight) {
      const xAxis = `<line x1="0" y1="${lineHeight}" x2="${totalBars * 20}" y2="${lineHeight}" stroke="black"/>`;
      const yAxis = `<line x1="0" y1="0" x2="0" y2="${lineHeight}" stroke="black"/>`;
      const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
      const labels = months.map((month, index) => `<text x="${index * 20 + 10}" y="${lineHeight + 20}" dy="0.35em">${month}</text>`).join('');
      g.appendChild(xAxis);
      g.appendChild(yAxis);
      g.appendChild(labels);
    }

    window.addEventListener('load', () => {
      calculate();
    });

    document.getElementById('financial-model').addEventListener('submit', event => {
      event.preventDefault();
      calculate();
    });

    const saveButton = document.querySelector('#chart-svg + button');
    saveButton.addEventListener('click', () => {
      const serializer = new XMLSerializer();
      const svgContent = serializer.serializeToString(chartSvg);
      const blob = new Blob([svgContent], {type: 'image/svg+xml;charset=utf-8'});
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'npv.svg';
      link.click();
    });
  </script>
</body>
</html>
```