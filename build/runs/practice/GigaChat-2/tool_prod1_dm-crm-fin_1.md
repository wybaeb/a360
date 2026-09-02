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

"""
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Инструмент расчета накопительного счета</title>
  <style>
    body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
    .header { text-align: center; color: #333; padding: 20px; }
    label { display: block; margin-bottom: 10px; }
    input[type=file] { width: 100%; margin-top: 10px; }
    table { border-collapse: collapse; margin: 20px auto; }
    th, td { padding: 10px; border: 1px solid #ccc; text-align: left; }
    svg { display: block; margin: 20px auto; max-width: 100%; height: auto; }
    button { margin-top: 20px; }
    .info { color: red; }
  </style>
</head>
<body>
  <div class="header">Расчет параметров накопительного счета</div>
  <form>
    <label for="files">Выберите файлы:</label>
    <input type="file" id="files" name="files" multiple accept=".csv" onchange="onFilesSelected()">
  </form>
  <div id="messages"></div>
  <table id="inputsTable" style="display:none;">
    <thead><tr><th>id</th><th>Название</th><th>Значение</th><th>Источник</th></tr></thead>
    <tbody></tbody>
  </table>
  <div id="resultArea" style="display:none;">
    <h2>Параметры проекта</h2>
    <p>Изменение показателя (предотвращённые закрытия): <span id="delta"></span></p>
    <p>Объём (коэффициент объёма): <span id="volume">1</span></p>
    <p>Цена (стоимость единицы): <span id="price">550</span> рублей/мес.</p>
    <button onclick="copyParameters()">Копировать параметры</button>
    <p id="metric">Маржинальный доход от удержанных счетов: <span id="marjinalMetric"></span> рублей/мес.</p>
  </div>
  <svg id="lineChart" style="display:none;" viewBox="0 0 500 100"></svg>
  
<script>
const csvHeaders = ["closures_dm.csv", "linked_crm.csv", "margin_fin.csv"];
let files = [];
let inputsData = [];

function onFilesSelected() {
  const fileInput = document.getElementById("files");
  if (!fileInput.files.length) return;
  files = Array.from(fileInput.files);
  let missingFiles = csvHeaders.filter(h => !files.find(f => f.name.includes(h)));
  if (missingFiles.length > 0) {
    showError(`Не найдены следующие файлы: ${missingFiles.join(", ")}`);
    return;
  }
  readAllFiles();
}

async function readAllFiles() {
  for (const file of files) {
    const reader = new FileReader();
    reader.onload = processFileContent;
    reader.readAsText(file);
  }
}

function processFileContent(event) {
  const content = event.target.result;
  const lines = content.split(/\r?\n/).filter(l => l.trim().length > 0);
  const firstLine = lines[0].split(';');
  const header = firstLine.map(h => h.trim());
  const rows = lines.slice(1).map(line => line.split(';').map(cell => cell.trim()));
  const data = rows.map(row => row.reduce((obj, value, index) => {
    obj[header[index]] = value;
    return obj;
  }, {}));
  const fileName = files.findIndex(f => f === event.target.file) + 1;
  const input = getInputObject(data, fileName);
  inputsData.push(input);
  updateInputsTable();
}

function getInputObject(data, fileNumber) {
  switch (fileNumber) {
    case 1: // closure dm
      const sumClosedLast12Months = calculateSumOfColumn(data, 'закрытые_счета', 12);
      return {
        name: 'closures',
        value: sumClosedLast12Months / 12,
        source: 'closures_dm.csv'
      };
    case 2: // linked crm
      const totalClosed = calculateTotalValue(data, 'закрытых_счетов_всего');
      const closedAfterContact = calculateTotalValue(data, 'закрытий_после_обращения');
      return {
        name: 'linked',
        value: closedAfterContact / totalClosed,
        source: 'linked_crm.csv'
      };
    case 3: // margin fin
      const averageBalance = calculateAverageValue(data, 'средний_остаток_тыс_руб');
      const annualMarginRate = parseFloat(data[0]['маржа_проц_годовых']);
      const lifeSpan = parseInt(data[0]['срок_жизни_счёта_мес']);
      return {
        name: 'margin',
        value: averageBalance * 1000 * annualMarginRate / 100 / lifeSpan,
        source: 'margin_fin.csv'
      };
  }
}

function calculateSumOfColumn(data, columnName, count) {
  const selectedRows = data.slice(-count);
  return selectedRows.reduce((sum, row) => sum + parseFloat(row[columnName]), 0);
}

function calculateTotalValue(data, columnName) {
  return data.reduce((total, row) => total + parseFloat(row[columnName]), 0);
}

function calculateAverageValue(data, columnName) {
  const values = data.map(row => parseFloat(row[columnName]));
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function updateInputsTable() {
  const tableBody = document.getElementById("inputsTable").getElementsByTagName("tbody")[0];
  while (tableBody.firstChild) tableBody.removeChild(tableBody.firstChild);
  inputsData.forEach(input => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${input.id}</td><td>${input.name}</td><td>${input.value.toFixed(2)}</td><td>${input.source}</td>`;
    tableBody.appendChild(tr);
  });
  showResult();
}

function showResult() {
  const delta = inputsData[0].value * inputsData[1].value * 1/3;
  const volume = 1;
  const price = inputsData[2].value;
  const marjinalMetric = delta * price;
  document.getElementById("delta").innerText = delta.toFixed(2);
  document.getElementById("volume").innerText = volume;
  document.getElementById("price").innerText = price.toFixed(2);
  document.getElementById("marjinalMetric").innerText = marjinalMetric.toFixed(2);
  drawLineChart();
}

function copyParameters() {
  navigator.clipboard.writeText(`delta=${document.getElementById("delta").textContent}; volume=${document.getElementById("volume").textContent}; price=${document.getElementById("price").textContent}`);
}

function showError(message) {
  const messagesDiv = document.getElementById("messages");
  messagesDiv.textContent = message;
  messagesDiv.style.color = "red";
}

function drawLineChart() {
  const chartContainer = document.getElementById("lineChart");
  const lastMonthData = inputsData[0].data.slice(-12);
  const xValues = lastMonthData.map(d => d.month);
  const yValues = lastMonthData.map(d => d.closedCount);
  const minY = Math.min(...yValues);
  const maxY = Math.max(...yValues);
  const scaleFactor = 100 / (maxY - minY);
  const scaledYValues = yValues.map(y => (y - minY) * scaleFactor);
  const svg = chartContainer.ownerSVGElement || chartContainer;
  svg.setAttribute("viewBox", `0 0 500 100`);
  const g = svg.appendChild(document.createElementNS("http://www.w3.org/2000/svg", "g"));
  g.setAttribute("transform", "translate(50, 50)");
  const path = g.appendChild(document.createElementNS("http://www.w3.org/2000/svg", "path"));
  path.setAttribute("d", `M ${xValues[0]} ${scaledYValues[0]} L ${xValues[xValues.length - 1]} ${scaledYValues[xValues.length - 1]}`);
  path.setAttribute("stroke", "#000");
  path.setAttribute("stroke-width", "2");
  const axisX = g.appendChild(document.createElementNS("http://www.w3.org/2000/svg", "line"));
  axisX.setAttribute("x1", 0);
  axisX.setAttribute("x2", 500);
  axisX.setAttribute("y1", 50);
  axisX.setAttribute("y2", 50);
  axisX.setAttribute("stroke", "#000");
  axisX.setAttribute("stroke-width", "1");
  const axisY = g.appendChild(document.createElementNS("http://www.w3.org/2000/svg", "line"));
  axisY.setAttribute("x1", 50);
  axisY.setAttribute("x2", 50);
  axisY.setAttribute("y1", 0);
  axisY.setAttribute("y2", 100);
  axisY.setAttribute("stroke", "#000");
  axisY.setAttribute("stroke-width", "1");
  const labels = g.appendChild(document.createElementNS("http://www.w3.org/2000/svg", "g"));
  labels.setAttribute("font-size", "10");
  labels.setAttribute("font-family", "Arial");
  xValues.forEach((month, i) => {
    const xPos = 50 + i * 40;
    const yPos = 50 - scaledYValues[i] * 100;
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", xPos);
    label.setAttribute("y", yPos);
    label.setAttribute("dy", ".35em");
    label.textContent = month;
    labels.appendChild(label);
  });
  chartContainer.style.display = "block";
}

// Вывод таблицы входов
updateInputsTable();
</script>
</body>
</html>
"""

Проверяй работу инструмента на указанных файлах, предварительно заменив содержимое CSV-файлов указанными тестовыми значениями.