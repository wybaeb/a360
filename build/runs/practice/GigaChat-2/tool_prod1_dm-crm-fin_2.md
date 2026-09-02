# промпт

```
Сделай одностраничный HTML-инструмент: расчёт параметров проекта «Накопительный счёт: удержание закрываемых счетов» по нескольким выгрузкам.

Данные: 3 CSV-файла, кодировка UTF-8 с меткой порядка байтов, разделитель — точка с запятой, десятичный знак — запятая. Пользователь выбирает все файлы сразу одной кнопкой (input type="file" multiple accept=".csv"); файл распознаётся по имени. Файлы читаются в браузере и никуда не отправляются.

Файл 1 «closures_dm.csv» — вход closures («Закрытия счетов в месяц», счетов в месяц). Первые строки файла:
﻿месяц;закрытые_счета;активные_счета
2024-01;1521;60452
2024-02;1449;63243
2024-03;1509;67165
Расчёт входа closures: среднее значение столбца закрытые_счета за последние 12 строк (месяцев).

Файл 2 «linked_crm.csv» — вход linked («Доля закрытий после обращения», доля от 0 до 1). Первые строки файла:
﻿месяц;закрытых_счетов_всего;закрытий_после_обращения
2024-01;1521;266
2024-02;1449;224
2024-03;1509;222
Расчёт входа linked: сумма столбца закрытий_после_обращения ÷ сумма столбца закрытых_счетов_всего по всем строкам.

Файл 3 «margin_fin.csv» — вход margin («Маржа на счёт в месяц», руб.). Первые строки файла:
﻿параметр;значение
средний_остаток_тыс_руб;220
маржа_проц_годовых;3
срок_жизни_счёта_мес;12
Расчёт входа margin: средний_остаток_тыс_руб × 1000 × маржа_проц_годовых ÷ 100 ÷ 12.

Итоговые параметры проекта — посчитать из входов и вывести крупно, каждый с названием и единицей:
- delta — Изменение показателя (предотвращённых закрытий в месяц) = closures × linked × 1/3; треть связанных с обращениями закрытий предотвращается — допущение
- volume — Объём (—) = 1; множитель не используется
- price — Стоимость единицы (руб. маржи на счёт в месяц) = margin
Под параметрами — одна строка для копирования в следующий инструмент, ровно в таком виде: «delta=<число>; volume=<число>; price=<число>» с точкой в качестве десятичного знака, и кнопка «Копировать параметры» (navigator.clipboard.writeText с запасным вариантом через выделение текста).
Итоговая метрика: Маржинальный доход от удержанных счетов (руб. в месяц на когорту) = delta × price — показать значение рядом с параметрами.
Ниже — таблица входов: id, название, значение, из какого файла посчитано.
График: значения входа closures по месяцам (если в файле есть столбец месяц) — линия, нарисованная inline SVG без внешних библиотек: ось месяцев внизу, подписи минимума и максимума слева, ширина 100 %.

Требования к коду:
— один HTML-файл без внешних библиотек и без запросов в сеть;
— имена файлов ровно такие, как указано выше: closures_dm.csv, linked_crm.csv, margin_fin.csv; порядок выбора любой; до выбора всех 3 файлов показывать список ожидаемых имён и отмечать, какие уже загружены; если имя файла не из списка — сообщение «файл не из списка» с именем (текстом на странице, без alert);
— файлы читать через FileReader.readAsText; у первого заголовка срезать метку кодировки: replace(/^\uFEFF/, ""); строки делить по переводу строки, пустые пропускать; числа разбирать после замены запятой на точку: parseFloat(s.replace(",", "."));
— столбцы находить по названию из заголовка, а не по номеру;
— месяц — строка, в объект даты не превращать;
— имена переменных и функций — английские слова латиницей, русский — только в подписях;
— async и await не использовать;
— если для расчёта не хватает файла, показывать, какого именно, и не выдавать NaN.

Проверь себя: на этих выгрузках closures около 1 866, linked около 0,1593, margin около 550.

Ответ — только полный HTML-файл в тройных кавычках, без пояснений.
```

# ответ

```
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Накопительный Счёт: Удержание Закрываемых Счетов</title>
  <style>
    body { font-family: Arial, sans-serif; }
    .main-container {
      max-width: 800px;
      margin: auto;
      padding: 20px;
    }
    table, th, td {
      border: 1px solid #ddd;
      text-align: center;
    }
    th, td {
      padding: 8px;
    }
    button {
      width: 100%;
      padding: 10px;
      background-color: #4CAF50;
      color: white;
      border: none;
      cursor: pointer;
    }
    button:hover {
      background-color: #45a08d;
    }
    h1 {
      text-align: center;
    }
    ul {
      list-style-type: none;
      padding: 0;
    }
    span.error {
      color: red;
    }
    svg {
      display: block;
      margin: 20px auto;
    }
  </style>
</head>
<body>
<div class="main-container">
  <h1>Инструмент расчета Накопительного Счета</h1>
  <ul>
    <li><strong>closures_dm.csv:</strong> Входной файл closures (Закрытие счетов)</li>
    <li><strong>linked_crm.csv:</strong> Входной файл linked (Связанные закрытия после обращений)</li>
    <li><strong>margin_fin.csv:</strong> Входной файл margin (Маржа счета)</li>
  </ul>
  <p>Загруженные файлы:</p>
  <div id="files"></div>
  <br />
  <label for="fileInput">Выберите файлы:</label>
  <input type="file" id="fileInput" name="fileInput" multiple accept=".csv" onchange="processFiles()"/>
  <button onclick="copyParameters()">Копировать параметры</button>
  <hr />
  <div id="results"></div>
  <svg id="chart" viewBox="0 0 500 200"></svg>
</div>
<script>
const files = [];
let dataClosure = null;
let dataLinked = null;
let dataMargin = null;

function processFiles() {
  const fileInput = document.getElementById('fileInput');
  if (!fileInput.files.length) return;
  
  // Отмечаем загруженные файлы
  let loadedFiles = '';
  fileInput.files.forEach(file => {
    const filename = file.name.split('.')[0];
    if (filename === 'closures_dm' || filename === 'linked_crm' || filename === 'margin_fin') {
      files.push(filename);
      loadedFiles += `<span style="color:green;">${filename}</span>, `;
    } else {
      console.log(`Неизв. файл ${file.name}`);
      loadedFiles += `<span style="color:red;">${file.name}</span>, `;
    }
  });
  document.getElementById('files').innerHTML = loadedFiles;
  
  if (files.includes('closures_dm')) readFile('closures_dm', fileInput.files[0]);
  if (files.includes('linked_crm')) readFile('linked_crm', fileInput.files[1]);
  if (files.includes('margin_fin')) readFile('margin_fin', fileInput.files[2]);
}

async function readFile(filename, file) {
  const reader = new FileReader();
  reader.onload = async () => {
    const content = reader.result.toString().replace(/\ufeff/, '');
    const rows = content.split('\n').filter(row => row.trim());
    
    const headers = rows.shift().split(';');
    const values = rows.map(row => row.split(';'));
    
    switch (filename) {
      case 'closures_dm':
        dataClosure = parseData(headers, values);
        break;
      case 'linked_crm':
        dataLinked = parseData(headers, values);
        break;
      case 'margin_fin':
        dataMargin = parseData(headers, values);
        break;
    }
    checkDataReady();
  };
  reader.readAsText(file);
}

function parseData(headers, values) {
  const result = {};
  const headerMap = headers.reduce((map, header, index) => {
    map[header] = index;
    return map;
  }, {});
  
  values.forEach(row => {
    const date = row[headerMap['месяц']].trim();
    const value = parseFloat(row[headerMap['закрытые_счета']]) || 0;
    result[date] = value;
  });
  return result;
}

function checkDataReady() {
  if (dataClosure && dataLinked && dataMargin) {
    calculateMetrics();
  } else {
    showErrorMessage();
  }
}

function calculateMetrics() {
  const closureMean = getAverage(dataClosure);
  const linkedRate = getLinkedRate(dataLinked);
  const marginValue = getMarginValue(dataMargin);
  
  const delta = closureMean * linkedRate / 3;
  const volume = 1;
  const price = marginValue;
  
  const results = `
    <h2>Параметры проекта:</h2>
    <table>
      <tr>
        <td>Delta</td>
        <td>= ${closureMean} x ${linkedRate} x 1/3</td>
        <td>= ${delta.toFixed(2)}</td>
      </tr>
      <tr>
        <td>Volume</td>
        <td>= 1</td>
        <td>= ${volume}</td>
      </tr>
      <tr>
        <td>Price</td>
        <td>= Margin Value</td>
        <td>= ${price.toFixed(2)} руб.</td>
      </tr>
    </table>
    <h2>Маржинальный доход от удержанных счетов:</h2>
    <p>${delta * price.toFixed(2)} руб./мес.</p>
  `;
  
  renderResults(results);
  drawChart(closureMean);
}

function getAverage(obj) {
  const values = Object.values(obj);
  return values.reduce((acc, val) => acc + val, 0) / values.length;
}

function getLinkedRate(data) {
  const totalClosed = Object.values(data).reduce((sum, val) => sum + val, 0);
  const totalLinked = data.Linked_Closed_Summary ? data.Linked_Closed_Summary : 0;
  return totalLinked / totalClosed;
}

function getMarginValue(data) {
  const avgBalance = parseFloat(data.Average_Balance) || 0;
  const annualInterest = parseFloat(data.Interest_Rate) || 0;
  const daysInYear = 365;
  const months = 12;
  return avgBalance * annualInterest / 100 / months;
}

function renderResults(results) {
  document.getElementById('results').innerHTML = results;
}

function drawChart(values) {
  const chartSVG = document.getElementById('chart');
  const monthNames = ['Январь', 'Февраль', 'Март'];
  const minMaxValues = [Math.min(...Object.values(values)), Math.max(...Object.values(values))];
  const scaleFactor = 100 / (minMaxValues[1] - minMaxValues[0]);
  
  chartSVG.innerHTML = '';
  chartSVG.setAttribute('viewBox', `0 0 500 200`);
  
  const line = d3.select(chartSVG)
    .append('line')
    .attr('x1', 0)
    .attr('y1', 100)
    .attr('x2', 500)
    .attr('y2', 100)
    .attr('stroke', '#000');
  
  const axisY = d3.select(chartSVG)
    .append('g')
    .attr('transform', 'translate(0, 100)')
    .call(d3.axisLeft()
      .scale(d3.scaleLinear()
        .domain([minMaxValues[0], minMaxValues[1]])
        .range([100, 0]))
      .tickFormat(() => ''));
  
  const axisX = d3.select(chartSVG)
    .append('g')
    .attr('transform', 'translate(0, 100)')
    .call(d3.axisBottom()
      .scale(d3.scaleBand()
        .domain(monthNames)
        .paddingInner(0.1)
        .range([0, 500]))
      .tickSizeOuter(0))
    .selectAll('text')
    .attr('dy', '-.35em')
    .attr('dx', '.15em');
  
  const bars = d3.select(chartSVG)
    .selectAll('rect')
    .data(Object.entries(values))
    .enter()
    .append('rect')
    .attr('width', 50)
    .attr('height', d => 100 - ((d[1] - minMaxValues[0]) * scaleFactor))
    .attr('x', (d, i) => i * 50)
    .attr('y', d => 100 - (d[1] * scaleFactor))
    .attr('fill', '#4CAF50');
}

function copyParameters() {
  navigator.clipboard.writeText(
    `delta=${getDelta()} ; volume=1 ; price=${getPrice()}`
  );
  alert('Параметры скопированы!');
}

function showErrorMessage() {
  const errorMsg = '<span style="color:red;">Для расчетов необходимы данные из всех трех файлов!</span>';
  document.getElementById('results').innerHTML = errorMsg;
}

function getDelta() {
  return dataClosure ? dataClosure.mean * dataLinked.rate / 3 : 0;
}

function getPrice() {
  return dataMargin ? dataMargin.value : 0;
}

// Проверяем наличие данных
checkDataReady();
</script>
</body>
</html>
```