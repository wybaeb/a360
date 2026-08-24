function buildReport() {
  var data = window.DATA;
  
  // Вытаскиваем значения tat_min
  var values = data.map(function(row) { return row.tat_min; }).filter(Number.isFinite);
  
  // Среднее первых 30 дней и последних 30 дней
  var firstMean = values.slice(0, 30).reduce(function(a,b){return a+b},0)/30;
  var lastMean = values.slice(-30).reduce(function(a,b){return a+b},0)/30;
  var changePercentNaive = ((lastMean/firstMean)-1)*100;
  
  // Медиана и MAD
  var medianValue = median(values);
  var mad = median(values.map(function(x) { return Math.abs(x-medianValue); }));
  
  // Робастная Z-оценка и выявление выбросов
  var thresholdZScore = 3.5;
  var outlierThresholdMinutes = 0.6745 * thresholdZScore * mad + medianValue;
  var outliers = [];
  for(var i=0; i<data.length; i++) {
    var value = data[i].tat_min;
    if (!Number.isFinite(value)) continue;
    var robustZScore = 0.6745*(value-medianValue)/mad;
    if(Math.abs(robustZScore)>thresholdZScore){
      outliers.push({
        date: data[i].date,
        value: value,
        zscore: robustZScore
      });
    }
  }
  
  // Очищенный ряд без выбросов
  var cleanValues = values.filter(function(val) {
    return !outliers.some(function(outl) { return val === outl.value; });
  });
  
  // Пересчёт среднего первых 30 и последних 30 дней без выбросов
  var firstCleanMean = cleanValues.slice(0, 30).reduce(function(a,b){return a+b},0)/30;
  var lastCleanMean = cleanValues.slice(-30).reduce(function(a,b){return a+b},0)/30;
  var changePercentCleaned = ((lastCleanMean/firstCleanMean)-1)*100;
  
  // Подготовка графиков и таблиц
  var highlightIndexes = outliers.map(function(outl) {
    return data.findIndex(function(d) { return d.date == outl.date && Number.isFinite(d.tat_min); });
  });
  
  // Блок №1: Плитки ключевых показателей
  var tilesData = [
    ["Средние первые 30 дней", fmt(firstMean)],
    ["Средние последние 30 дней", fmt(lastMean)],
    ["Изменение %", fmt(changePercentNaive)+"%"],
    ["Медиана", fmt(medianValue)],
    ["MAD", fmt(mad)],
    ["Порог выброса", fmt(outlierThresholdMinutes)+" мин"],
    ["Изменение % после очистки", fmt(changePercentCleaned)+"%"]
  ];
  
  // Блок №2: Линейный график с выделенными выбросами
  var lineChartHTML = chartLine(
    values,
    ["Первые 30 дней", "Последние 30 дней"],
    highlightIndexes
  );
  
  // Добавляем линию порога и точки выбросов
  var svgHeight = 300;
  var svgWidth = 600;
  var marginTop = 20;
  var marginLeft = 50;
  var yScaleFactor = (svgHeight-marginTop*2)/(Math.max.apply(null,values)-Math.min.apply(null,values));
  var xScaleFactor = (svgWidth-marginLeft*2)/values.length;
  
  var thresholdY = svgHeight - marginTop - (outlierThresholdMinutes-Math.min.apply(null,values))*yScaleFactor;
  
  lineChartHTML += '<line x1="'+(marginLeft)+'px" y1="'+thresholdY+'px" x2="'+(svgWidth-marginLeft)+'px" y2="'+thresholdY+'px" style="stroke:#E4572E; stroke-width:2; stroke-dasharray:5 4"/>';
  lineChartHTML += '<text x="50%" y="'+thresholdY+'" text-anchor="middle" dy="-.3em" font-size="12px" fill="#E4572E">порог '+fmt(outlierThresholdMinutes)+' мин</text>';
  
  outliers.forEach(function(outl) {
    var index = data.findIndex(function(d) { return d.date == outl.date && Number.isFinite(d.tat_min); });
    var xPos = marginLeft+index*xScaleFactor;
    var yPos = svgHeight - marginTop - (outl.value-Math.min.apply(null,values))*yScaleFactor;
    lineChartHTML += '<circle cx="'+xPos+'px" cy="'+yPos+'px" r="4" fill="#E4572E"/>';
  });
  
  // Блок №3: Горизонтальные полосы
  var barRowsData = [
    ["Средние первые 30 дней", firstMean, fmt(firstMean)],
    ["Средние последние 30 дней", lastMean, fmt(lastMean)],
    ["Средние первые 30 дней (после очистки)", firstCleanMean, fmt(firstCleanMean)],
    ["Средние последние 30 дней (после очистки)", lastCleanMean, fmt(lastCleanMean)]
  ];
  
  // Блок №4: Таблица с днями-выбросами
  var tableHeaders = ["Дата", "Значение минут", "Робастная Z-оценка"];
  var tableBody = outliers.map(function(outl) {
    return [outl.date, fmt(outl.value), fmt(outl.zscore)];
  });
  
  // Блок №5: Карточка вывода
  var conclusionText = '';
  if (changePercentCleaned > 5 || changePercentCleaned < -5) {
    conclusionText = 'После исключения выбросов наблюдается значительное ';
    if (changePercentCleaned > 0) {
      conclusionText += 'увеличение';
    } else {
      conclusionText += 'снижение';
    }
    conclusionText += ' срока рассмотрения заявок.';
  } else {
    conclusionText = 'Значимое изменение срока рассмотрения заявок отсутствует.';
  }
  
  // Сборка HTML отчета
  var html = "";
  html += tiles(tilesData);
  html += card('Линейный график', lineChartHTML);
  html += barRows(barRowsData);
  html += card('Таблица дней-выбросов', makeTable(tableHeaders, tableBody));
  html += card('Вывод', '<p>'+conclusionText+'</p>');
  
  return html;
}
