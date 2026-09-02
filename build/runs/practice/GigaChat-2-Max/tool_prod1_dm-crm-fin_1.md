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
    <title>Инструмент расчета параметров проекта</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .data-table { width: 100%; border-collapse: collapse; text-align: left; }
        .data-table th, .data-table td { padding: 8px; border-bottom: 1px solid #ddd; }
        input[type=file] { display: block; margin-top: 1em; }
        svg { height: 200px; background-color: white; }
        path.line { fill: none; stroke: steelblue; stroke-width: 2px; }
        .axis { font-size: 12px; color: gray; }
        h2 { font-weight: bold; margin-bottom: 0.5em; }
        .params-output { font-size: 1.5em; line-height: 1.5; }
        button { cursor: pointer; }
    </style>
</head>
<body>
<h1>Расчет параметров проекта</h1>
<p>Выберите три файла:</p>
<input type="file" id="files-input" multiple accept=".csv"/>
<div id="status"></div>
<div class="params-output" style="display:none;">
    <h2>Параметры проекта:</h2>
    <table class="data-table">
        <tr><th>Название параметра</th><th>Значение</th></tr>
        <tr><td>Изменение показателя (delta)</td><td id="delta-value">...</td></tr>
        <tr><td>Объём (volume)</td><td id="volume-value">...</td></tr>
        <tr><td>Стоимость единицы (price)</td><td id="price-value">...</td></tr>
    </table>
    <br/>
    <span id="copy-string">delta=...; volume=...; price=...</span>&nbsp;<button onclick="copyToClipboard()">Копировать параметры</button>
    <br/><strong>Маржинальный доход от удержанных счетов (в месяц):</strong> <span id="marjinal-income">...</span> рублей.<br/>
</div>
<br/>
<h2>Таблица входов:</h2>
<table class="data-table" id="inputs-table">
    <thead><tr><th>id</th><th>Название</th><th>Значение</th><th>Из файла</th></tr></thead>
    <tbody></tbody>
</table>

<script>
function readCsv(file, callback) {
    var reader = new FileReader();
    reader.onload = function(e) {
        var csvData = e.target.result.replace(/^\uFEFF/, "").split("\n").map(row => row.split(";"));
        // Удаляем последнюю строку, если она пустая
        if (!csvData[csvData.length - 1][0]) csvData.pop();
        callback(csvData);
    };
    reader.readAsText(file);
}

document.getElementById('files-input').onchange = function(event) {
    document.getElementById('status').innerHTML = '';
    var files = event.target.files;
    var fileNames = ['closures_dm.csv', 'linked_crm.csv', 'margin_fin.csv'];
    var results = {};
    
    for(var i = 0; i < files.length; i++) {
        var filename = files[i].name;
        
        if(!fileNames.includes(filename)) {
            document.getElementById('status').innerHTML += '<p>Файл "' + filename + '" не из списка.</p>';
            continue;
        }
        
        readCsv(files[i], function(data) {
            processFile(filename, data, results);
            
            if(Object.keys(results).length === 3) {
                calculateProjectParameters(results);
            } else {
                updateStatus(results);
            }
        });
    }
};

function processFile(filename, data, results) {
    switch(filename) {
        case 'closures_dm.csv':
            var closedSum = 0;
            var lastRows = data.slice(-12);
            for(var j = 1; j < lastRows.length; j++) {
                closedSum += parseFloat(lastRows[j][1].replace(',', '.'));
            }
            results['closures'] = closedSum / Math.min(12, lastRows.length - 1);
            break;
        case 'linked_crm.csv':
            var totalClosed = 0;
            var afterCallClosed = 0;
            for(var k = 1; k < data.length; k++) {
                totalClosed += parseFloat(data[k][1].replace(',', '.'));
                afterCallClosed += parseFloat(data[k][2].replace(',', '.'));
            }
            results['linked'] = afterCallClosed / totalClosed;
            break;
        case 'margin_fin.csv':
            var avgBalance = parseFloat(data.find(r => r[0] == 'средний_остаток_тыс_руб')[1].replace(',', '.')) * 1000;
            var interestRate = parseFloat(data.find(r => r[0] == 'маржа_проц_годовых')[1].replace(',', '.')) / 100;
            var accountLifeMonths = parseInt(data.find(r => r[0] == 'срок_жизни_счёта_мес')[1]);
            results['margin'] = avgBalance * interestRate / accountLifeMonths;
            break;
    }
}

function calculateProjectParameters(results) {
    var delta = results.closures * results.linked / 3;
    var volume = 1;
    var price = results.margin;
    var marjIncome = delta * price;
    
    document.getElementById('delta-value').textContent = delta.toFixed(2);
    document.getElementById('volume-value').textContent = volume;
    document.getElementById('price-value').textContent = price.toFixed(2);
    document.getElementById('marjinal-income').textContent = marjIncome.toFixed(2);
    document.getElementById('copy-string').textContent = `delta=${delta.toFixed(2)}; volume=${volume}; price=${price.toFixed(2)}`;
    document.querySelector('.params-output').style.display = 'block';
    
    renderInputsTable(results);
    drawClosuresChart(results.closures_data);
}

function renderInputsTable(results) {
    var tableBody = document.getElementById('inputs-table').tBodies[0];
    while(tableBody.firstChild) tableBody.removeChild(tableBody.firstChild);
    
    Object.entries(results).forEach(([key, value]) => {
        var tr = document.createElement('tr');
        tr.innerHTML = `<td>${key}</td><td>${value.toFixed ? value.toFixed(2) : value}</td><td>из ${getFilenameForInput(key)}</td>`;
        tableBody.appendChild(tr);
    });
}

function getFilenameForInput(inputName) {
    return {'closures': 'closures_dm.csv',
            'linked': 'linked_crm.csv',
            'margin': 'margin_fin.csv'}[inputName];
}

function copyToClipboard() {
    navigator.clipboard.writeText(document.getElementById('copy-string').textContent)
      .then(() => console.log('Скопировано!'))
      .catch(err => console.error('Ошибка копирования:', err));
}

function drawClosuresChart(closuresData) {
    var minValue = Infinity;
    var maxValue = -Infinity;
    var xScale = d3.scaleBand().domain(d3.range(closuresData.length)).range([0, window.innerWidth]).paddingInner(0.1);
    var yScale = d3.scaleLinear().range([window.innerHeight - 50, 10]);
    
    closuresData.forEach(function(row) {
        var val = parseFloat(row[1].replace(',', '.'));
        minValue = Math.min(minValue, val);
        maxValue = Math.max(maxValue, val);
    });
    
    yScale.domain([minValue, maxValue]);
    
    var chartSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    chartSvg.setAttribute('width', '100%');
    chartSvg.setAttribute('height', window.innerHeight);
    document.body.appendChild(chartSvg);
    
    var linePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    linePath.setAttribute('class', 'line');
    linePath.setAttribute('d', 'M' + xScale(0) + ',' + yScale(parseFloat(closuresData[0][1].replace(',', '.'))));
    
    closuresData.forEach(function(row, index) {
        var val = parseFloat(row[1].replace(',', '.'));
        linePath.setAttribute('d', linePath.getAttribute('d') + (' L' + xScale(index) + ',' + yScale(val)));
    });
    
    chartSvg.appendChild(linePath);
    
    var axisLeft = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    axisLeft.textContent = `${maxValue}`;
    axisLeft.setAttribute('x', '-10');
    axisLeft.setAttribute('y', '10');
    axisLeft.setAttribute('transform', 'rotate(-90)');
    axisLeft.classList.add('axis');
    chartSvg.appendChild(axisLeft);
    
    var axisRight = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    axisRight.textContent = `${minValue}`;
    axisRight.setAttribute('x', '-10');
    axisRight.setAttribute('y', window.innerHeight - 40);
    axisRight.setAttribute('transform', 'rotate(-90)');
    axisRight.classList.add('axis');
    chartSvg.appendChild(axisRight);
}

function updateStatus(results) {
    var statusDiv = document.getElementById('status');
    statusDiv.innerHTML = '';
    fileNames.forEach(name => {
        var p = document.createElement('p');
        p.textContent = name + ': ';
        if(results[name.replace('.csv','')] !== undefined) {
            p.textContent += 'загружено';
        } else {
            p.textContent += 'не загружено';
        }
        statusDiv.appendChild(p);
    });
}
</script>
</body>
</html>
```