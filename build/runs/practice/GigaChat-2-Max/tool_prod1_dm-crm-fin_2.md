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

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Расчёт параметров проекта Накопительный счёт</title>
  <style>
    body { font-family: Arial, sans-serif; }
    h1 { text-align: center; color: #333; }
    .result { display: flex; justify-content: space-between; align-items: baseline; font-size: 2x; padding-top: 2rem; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 1rem; }
    th, td { border: 1px solid #ddd; padding: 0.5rem; text-align: left; }
    tbody tr:nth-child(even) { background-color: #f2f2f2; }
    svg { height: 200px; width: 100%; fill: none; stroke-width: 2; stroke-linecap: round; }
    path.line { stroke: steelblue; }
    .axis { font-size: smaller; }
    button { cursor: pointer; padding: 0.5em 1em; }
    pre { white-space: nowrap; overflow-x: auto; }
  </style>
</head>
<body>
<h1>Расчёт параметров проекта «Накопительный счёт: удержание закрываемых счетов»</h1>
<div>
  <label for="files">Выберите три файла:</label><br>
  <input type="file" id="files" name="files[]" multiple accept=".csv"><br>
  <div id="status"></div>
</div>
<div class="result">
  <p>Изменение показателя (предотвращённых закрытий в месяц): <span id="delta"></span></p>
  <p>Объём (-): <span id="volume"></span></p>
  <p>Стоимость единицы (руб. маржи на счёт в месяц): <span id="price"></span></p>
  <p>Маржинальный доход от удержанных счетов (руб. в месяц на когорту): <span id="income"></span></p>
</div>
<p>Для следующего инструмента:</p>
<pre contenteditable id="copyable"></pre>
<button onclick="copyToClipboard()">Копировать параметры</button>
<br><table id="inputsTable">
  <thead><tr><th>id</th><th>Название</th><th>Значение</th><th>Источник</th></tr></thead>
  <tbody></tbody>
</table>
<div style="width: 100%;" id="chartContainer"></div>
<script>
function loadFiles(files) {
  var expectedNames = ["closures_dm.csv", "linked_crm.csv", "margin_fin.csv"];
  var loadedFiles = {};
  
  document.getElementById("status").innerHTML = "";
  if (!files || files.length !== 3) return showError("Нужно выбрать ровно три файла.");
  
  for(var i=0; i<files.length; ++i){
    var fileName = files[i].name.trim();
    if(expectedNames.includes(fileName)) {
      loadedFiles[fileName] = true;
    } else {
      showError(`Файл ${fileName} не из списка.`);
      return;
    }
  }
  
  function processFile(file, cb) {
    var reader = new FileReader();
    reader.onload = function(event) {
      var csvData = event.target.result.replace(/^\uFEFF/, "").split("\n");
      var rows = [];
      for(var j=0; j<csvData.length; ++j) {
        var row = csvData[j];
        if(row.trim()) rows.push(row.split(';'));
      }
      
      cb(rows);
    };
    reader.readAsText(file);
  }
  
  var closureRows, linkedRows, marginRows;
  
  // Чтение файлов последовательно
  processFile(files[0], function(closureData) {
    closureRows = closureData;
    
    processFile(files[1], function(linkedData) {
      linkedRows = linkedData;
      
      processFile(files[2], function(marginData) {
        marginRows = marginData;
        
        calculateParameters(closureRows, linkedRows, marginRows);
      });
    });
  });
}

// Выдать ошибку на экран
function showError(message) {
  document.getElementById("status").textContent += message + "\n";
}

// Найти индекс колонки по её заголовку
function findColumnIndex(headers, columnName) {
  for(var i=0; i<headers.length; ++i)
    if(headers[i].trim().toLowerCase() === columnName.toLowerCase())
      return i;
  return -1;
}

// Расчёт показателей
function calculateParameters(closureRows, linkedRows, marginRows) {
  try {
    const headersClosure = closureRows.shift(); 
    const closedColIdx = findColumnIndex(headersClosure, 'закрытые_счета');
    const activeColIdx = findColumnIndex(headersClosure, 'активные_счета');
    
    const lastTwelveMonthsClosedSum = closureRows.slice(-12).reduce((sum, row) => sum + parseFloat(row[closedColIdx].replace(',', '.')), 0);
    const closures = Math.round(lastTwelveMonthsClosedSum / 12 * 10)/10;
    
    const headersLinked = linkedRows.shift();
    const totalClosedColIdx = findColumnIndex(headersLinked, 'закрытых_счетов_всего');
    const afterCallClosedColIdx = findColumnIndex(headersLinked, 'закрытий_после_обращения');
    
    let totalClosedSum = 0, afterCallClosedSum = 0;
    linkedRows.forEach(function(row) {
      totalClosedSum += parseFloat(row[totalClosedColIdx].replace(',', '.'));
      afterCallClosedSum += parseFloat(row[afterCallClosedColIdx].replace(',', '.'));
    });
    const linked = afterCallClosedSum / totalClosedSum;
    
    const headersMargin = marginRows.shift();
    const avgBalanceColIdx = findColumnIndex(headersMargin, 'средний_остаток_тыс_руб');
    const rateColIdx = findColumnIndex(headersMargin, 'маржа_проц_годовых');
    const lifeSpanColIdx = findColumnIndex(headersMargin, 'срок_жизни_счёта_мес');
    
    const avgBalance = parseFloat(marginRows[0][avgBalanceColIdx].replace(',', '.')) * 1000;
    const annualRate = parseFloat(marginRows[0][rateColIdx].replace(',', '.')) / 100;
    const lifeSpanInMonths = parseFloat(marginRows[0][lifeSpanColIdx].replace(',', '.'));
    const margin = avgBalance * annualRate / lifeSpanInMonths;
    
    const delta = closures * linked / 3;
    const volume = 1;
    const price = margin;
    const income = delta * price;
    
    document.getElementById("delta").textContent = delta.toFixed(2);
    document.getElementById("volume").textContent = volume;
    document.getElementById("price").textContent = price.toFixed(2);
    document.getElementById("income").textContent = income.toFixed(2);
    
    document.getElementById("copyable").textContent = `delta=${delta}; volume=${volume}; price=${price}`;
    
    renderInputsTable(delta, volume, price, closures, linked, margin);
    drawChart(closureRows, headersClosure);
  } catch(err) {
    console.error(err);
    showError("Ошибка обработки данных.");
  }
}

// Отрисовка таблицы исходных значений
function renderInputsTable(delta, volume, price, closures, linked, margin) {
  var inputsTBody = document.querySelector("#inputsTable > tbody");
  while(inputsTBody.firstChild) inputsTBody.removeChild(inputsTBody.firstChild);
  
  addRow("delta", "Изменение показателя", delta, "");
  addRow("volume", "Объём", volume, "");
  addRow("price", "Стоимость единицы", price, "");
  addRow("closures", "Среднее количество закрытий", closures, "closures_dm.csv");
  addRow("linked", "Доля закрытий после обращений", linked, "linked_crm.csv");
  addRow("margin", "Маржа на счет в месяц", margin, "margin_fin.csv");
  
  function addRow(id, title, value, source) {
    var row = document.createElement("tr");
    row.innerHTML = `<td>${id}</td><td>${title}</td><td>${value}</td><td>${source}</td>`;
    inputsTBody.appendChild(row);
  }
}

// Копирование в буфер обмена
function copyToClipboard() {
  navigator.clipboard && navigator.clipboard.writeText(document.getElementById("copyable").textContent)
    ? showError("Параметры скопированы.")
    : fallbackCopyToClipboard();
}

// Альтернативное копирование путём выделения текста
function fallbackCopyToClipboard() {
  var range = document.createRange();
  range.selectNodeContents(document.getElementById("copyable"));
  window.getSelection().removeAllRanges();
  window.getSelection().addRange(range);
  document.execCommand("copy");
  window.getSelection().removeAllRanges();
  showError("Параметры скопированы вручную.");
}

// График закрытия счетов по месяцам
function drawChart(data, headers) {
  var monthColIdx = findColumnIndex(headers, 'месяц');
  var closedColIdx = findColumnIndex(headers, 'закрытые_счета');
  
  var months = data.map(r => r[monthColIdx]);
  var values = data.map(r => parseFloat(r[closedColIdx].replace(',', '.')));
  
  var minValue = Math.min(...values), maxValue = Math.max(...values);
  var chartWidth = document.body.clientWidth;
  var chartHeight = 200;
  var xStep = chartWidth / (months.length - 1);
  
  var yScaleFactor = chartHeight / (maxValue - minValue);
  
  var points = values.map((v,i) => `${i*xStep},${chartHeight-(v-minValue)*yScaleFactor}`);
  
  var svg = '<svg viewBox="0 0 '+chartWidth+' '+chartHeight+'">' +
            '<path d="M' + points.join(' L') + '" class="line"/>' +
            '<g transform="translate(0,'+chartHeight+') scale(1,-1)" class="axis">'+
              '<text x="'+chartWidth*0.02+'" y="'+(minValue*yScaleFactor)+'" dy="-.35em">'+minValue+'</text>'+
              '<text x="'+chartWidth*0.02+'" y="'+(maxValue*yScaleFactor)+'" dy="-.35em">'+maxValue+'</text>'+
            '</g>'+
          '</svg>';
  
  document.getElementById("chartContainer").innerHTML = svg;
}

document.getElementById("files").onchange = function(evt) {
  loadFiles(this.files);
};
</script>
</body>
</html>
```