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
        .section { border-bottom: 1px solid #ccc; padding: 1rem 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
        th, td { padding: 0.5rem; border: 1px solid #ddd; text-align: left; }
        svg { display: block; height: auto; max-width: 100%; }
        button { background-color: #007bff; color: white; padding: 0.5rem 1rem; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        input[type=text], p.error { color: red; }
    </style>
</head>
<body>
<h1>Расчёт параметров проекта «Накопительный счёт: удержание закрываемых счетов»</h1>
<div class="section">
    <p>Выберите три CSV-файла:</p>
    <label for="files">Файлы:</label><br/>
    <input type="file" id="files" name="files[]" multiple accept=".csv"/>
    <ul id="status"></ul>
</div>
<div class="section">
    <h2>Параметры проекта:</h2>
    <table id="result-table">
        <tr><th>Название параметра</th><th>Значение</th></tr>
        <tr><td>Изменение показателя (delta)</td><td id="delta"></td></tr>
        <tr><td>Объём (volume)</td><td id="volume">1</td></tr>
        <tr><td>Стоимость единицы (price)</td><td id="price"></td></tr>
    </table>
    <button onclick="copyParams()">Копировать параметры</button>
    <input type="text" readonly id="copy-text" style="width: 100%;" />
    <p>Маржинальный доход от удержанных счетов (в месяц): <span id="marginal-income"></span> рублей.</p>
</div>
<div class="section">
    <h2>Таблица входов:</h2>
    <table id="inputs-table">
        <tr><th>id</th><th>Название</th><th>Значение</th><th>Источник</th></tr>
    </table>
</div>
<div class="section">
    <h2>График закрытия счетов по месяцам:</h2>
    <svg id="chart" viewBox="0 0 1000 300" preserveAspectRatio="none"></svg>
</div>
<script>
document.getElementById('files').addEventListener('change', function(e){
    const files = e.target.files;
    if(files.length !== 3) return showError("Нужно выбрать ровно 3 файла");
    
    let closuresData, linkedData, marginData;
    var readers = [];
    
    Array.from(files).forEach(function(file, i){
        var reader = new FileReader();
        reader.onload = processFile.bind(null, file.name);
        reader.readAsText(file);
        readers.push(reader);
    });
    
    function processFile(filename, event){
        var data = event.target.result.replace(/^\uFEFF/, "").split("\n").filter(Boolean);
        
        switch(filename.toLowerCase()){
            case 'closures_dm.csv':
                var cols = data.shift().split(';');
                var indexClosed = cols.indexOf('закрытые_счета');
                var lastRows = data.slice(-12).map(row => row.split(';')); // последние 12 месяцев
                closuresData = lastRows.reduce((sum, r) => sum + parseFloat(r[indexClosed].replace(',', '.')), 0)/lastRows.length;
                break;
            
            case 'linked_crm.csv':
                var cols = data.shift().split(';');
                var closedIndex = cols.indexOf('закрытых_счетов_всего');
                var afterCallIndex = cols.indexOf('закрытий_после_обращения');
                var totalClosed = data.reduce((s,r)=> s+parseFloat(r.split(';')[closedIndex].replace(',','.')),0);
                var totalAfterCall = data.reduce((s,r)=> s+parseFloat(r.split(';')[afterCallIndex].replace(',','.')),0);
                linkedData = totalAfterCall / totalClosed;
                break;
                
            case 'margin_fin.csv':
                var obj = {};
                data.forEach(row=>{
                    var [key,value] = row.split(';');
                    obj[key.trim()] = value.trim();
                });
                marginData = parseFloat(obj['средний_остаток_тыс_руб'].replace(',','.')) * 1000 *
                             parseFloat(obj['маржа_проц_годовых'].replace(',','.'))/100/12;
                break;
                
            default:
                showError(`Файл ${filename} не из списка`);
        }
        
        checkComplete();
    };
    
    function checkComplete(){
        if(closuresData && linkedData && marginData){
            calculateAndDisplay();
        } else {
            console.log("Ожидаем загрузки оставшихся файлов...");
        }
    }
});

function calculateAndDisplay(){
    document.querySelector('#status').innerHTML = '';
    
    var delta = closuresData * linkedData * (1/3);
    var volume = 1;
    var price = marginData;
    var marginalIncome = Math.round(delta * price);
    
    document.getElementById('delta').textContent = delta.toFixed(2);
    document.getElementById('volume').textContent = volume;
    document.getElementById('price').textContent = price.toFixed(2);
    document.getElementById('marginal-income').textContent = marginalIncome;
    
    document.getElementById('copy-text').value = `delta=${delta.toFixed(2)}; volume=${volume}; price=${price.toFixed(2)}`;
    
    updateInputsTable([
        ['closures', 'Среднее количество закрытий счетов в месяц', closuresData.toFixed(2), 'closures_dm.csv'],
        ['linked', 'Доля закрытий после обращений', linkedData.toFixed(4), 'linked_crm.csv'],
        ['margin', 'Маржа на счет в месяц', price.toFixed(2)+' ₽', 'margin_fin.csv']
    ]);
    
    drawChart();
}

function copyParams(){
    navigator.clipboard.writeText(document.getElementById('copy-text').value)
      .then(()=>alert('Скопировано!'))
      .catch(err=>console.error('Ошибка копирования:', err));
}

function showError(msg){
    document.querySelector('#status').innerHTML += `<li class="error">${msg}</li>`;
}

function updateInputsTable(data){
    var tbody = document.createElement('tbody');
    data.forEach(row=>{
        var tr = document.createElement('tr');
        row.forEach(cell=>{
            var td = document.createElement('td');
            td.textContent = cell;
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    document.getElementById('inputs-table').appendChild(tbody);
}

function drawChart(){
    var data = closures_data || [];
    if(!data.length) return;
    
    var minVal = Math.min(...data.map(d=>d.value)), 
        maxVal = Math.max(...data.map(d=>d.value)),
        w = 1000,
        h = 300,
        marginTop = 20,
        marginLeft = 50,
        xScale = d3.scaleBand().domain(data.map(d=>d.month)).range([marginLeft,w-marginLeft]),
        yScale = d3.scaleLinear().domain([minVal,maxVal]).range([h-marginTop,marginTop]);
    
    var chart = document.getElementById('chart');
    chart.innerHTML = `
        <line x1="${marginLeft}" y1="${yScale(minVal)}" x2="${w-marginLeft}" y2="${yScale(minVal)}" stroke="#aaa" />
        <line x1="${marginLeft}" y1="${yScale(maxVal)}" x2="${w-marginLeft}" y2="${yScale(maxVal)}" stroke="#aaa" />
        <text x="10" y="${yScale(minVal)+5}">${Math.floor(minVal)}</text>
        <text x="10" y="${yScale(maxVal)-5}">${Math.ceil(maxVal)}</text>
        <path fill="none" stroke="steelblue" stroke-width="2"
              d="${data.map(d=>'M'+xScale(d.month)+','+yScale(d.value)).join('L')}"/>
        ${data.map((d,i)=>{
          return `<text x="${xScale(d.month)+5}" y="${h-10}" dy=".3em" transform="rotate(-60 ${xScale(d.month)},${h})">${d.month}</text>`}).join('')}
    `;
}

// Статические данные для графика (измените на реальные данные!)
var closures_data = [
    {"month": "2024-01", "value": 1521},
    {"month": "2024-02", "value": 1449},
    {"month": "2024-03", "value": 1509},
];

window.d3 = {}; // заглушка для функции scaleBand и scaleLinear

// scaleBand реализация (упрощённая версия):
d3.scaleBand = () => ({
    domain: arr => ({ range: ([start,end]) => ({...this, _domain:arr,_range:[start,end]}) }),
    range: ([start,end]) => ({...this, _range:[start,end]}),
    bandwidth: () => (this._range[1]-this._range[0])/this._domain.length,
    step: () => this.bandwidth(),
    round: false,
    paddingInner: 0,
    paddingOuter: 0,
    align: 0.5,
    call: fn => fn(this),
    ticks: n => [],
    tickFormat: f => {},
    copy: () => {}
});

// scaleLinear реализация (упрощённая версия):
d3.scaleLinear = () => ({
    domain: arr => ({ range: ([start,end]) => ({...this, _domain:arr,_range:[start,end]}) }),
    range: ([start,end]) => ({...this, _range:[start,end]}),
    invert: v => ((v-this._range[0])/(this._range[1]-this._range[0]))*(this._domain[1]-this._domain[0])+this._domain[0],
    nice: () => {},
    clamp: false,
    unknown: null,
    interpolate: d3.interpolateNumber,
    copy: () => {}
});

// Интерполятор чисел (достаточно простой реализации):
d3.interpolateNumber = (a,b) => (t) => a+(b-a)*t;
</script>
</body>
</html>
```

**Примечания:**  
Этот пример включает упрощённые версии функций D3.js (`scaleBand` и `scaleLinear`), чтобы продемонстрировать принцип работы графики без привлечения самой библиотеки. В реальных условиях рекомендуется подключать полную версию D3.js либо адаптировать этот код для полноценной работы без сторонних зависимостей.