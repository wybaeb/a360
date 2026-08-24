function buildReport() {
  var data = window.DATA;
  
  // Суммы по кварталам и годам
  var sumsByQuarterYear = {};
  for (var i = 0; i < data.length; i++) {
    var row = data[i];
    var year = row.date.split('-')[0];
    var month = Number(row.date.split('-')[1]);
    var quarter = Math.ceil(month / 3);
    
    if (!sumsByQuarterYear[year]) sumsByQuarterYear[year] = [];
    while (sumsByQuarterYear[year].length < quarter) sumsByQuarterYear[year].push(0);
    sumsByQuarterYear[year][quarter - 1] += row.amount_mln_rub;
  }
  
  // Годовые суммы
  var annualSums = Object.keys(sumsByQuarterYear).map(function(year) {
    return {
      year: year,
      sum: sumsByQuarterYear[year].reduce(function(a, b) { return a + b }, 0),
      quarters: sumsByQuarterYear[year]
    };
  });
  
  // Расчёт изменений
  var q4_2025_q3_2025_change = ((sumsByQuarterYear['2025'][3] / sumsByQuarterYear['2025'][2] - 1) * 100);
  var q4_2025_q4_2024_change = ((sumsByQuarterYear['2025'][3] / sumsByQuarterYear['2024'][3] - 1) * 100);
  var y2025_y2024_change = ((annualSums.find(function(y) { return y.year === '2025' }).sum /
                             annualSums.find(function(y) { return y.year === '2024' }).sum - 1) * 100);
  
  // Форматирование чисел
  var formattedQ4_2025_Q3_2025 = fmt(q4_2025_q3_2025_change) + '%';
  var formattedQ4_2025_Q4_2024 = fmt(q4_2025_q4_2024_change) + '%';
  var formattedY2025_Y2024 = fmt(y2025_y2024_change) + '%';
  
  // Подготовка данных для графика месяцев
  var monthlyData = [], colors = [];
  for (i = 0; i < data.length; i++) {
    var d = new Date(data[i].date);
    var key = d.getFullYear() + '-' + ('0' + (d.getMonth()+1)).slice(-2);
    if (!monthlyData[key]) {
      monthlyData[key] = 0;
      colors.push(d.getFullYear());
    }
    monthlyData[key] += data[i].amount_mln_rub;
  }
  var values = Object.values(monthlyData);
  var labels = Object.keys(monthlyData);
  
  // Цвета для месяцев
  var colorMap = {'2023': '#A8E0C4', '2024': '#5BC98D', '2025': '#20BA72'};
  var barColors = labels.map(function(label) { return colorMap[label.split('-')[0]] });
  
  // Блок плитки ключевых показателей
  var tilesBlock = tiles([
    ['IV/III 2025', formattedQ4_2025_Q3_2025],
    ['IV/IV 2024–2025', formattedQ4_2025_Q4_2024],
    ['Год 2025 к 2024', formattedY2025_Y2024],
    ['Итог 2025', fmt(annualSums.find(function(y) { return y.year === '2025' }).sum)]
  ]);
  
  // Столбчатый график по месяцам
  var monthsChart = chartBars(values, labels, barColors);
  
  // Горизонтальные полосы годовых итогов
  var yearsBarRows = barRows([
    ['2023', annualSums.find(function(y) { return y.year === '2023' }).sum, 
     fmt(annualSums.find(function(y) { return y.year === '2023' }).sum)],
    ['2024', annualSums.find(function(y) { return y.year === '2024' }).sum, 
     fmt(annualSums.find(function(y) { return y.year === '2024' }).sum)],
    ['2025', annualSums.find(function(y) { return y.year === '2025' }).sum, 
     fmt(annualSums.find(function(y) { return y.year === '2025' }).sum)]
  ]);
  
  // Горизонтальные полосы квартальных итогов
  var quartersBarRows = barRows([
    ['I кв. 2024', sumsByQuarterYear['2024'][0], fmt(sumsByQuarterYear['2024'][0])],
    ['II кв. 2024', sumsByQuarterYear['2024'][1], fmt(sumsByQuarterYear['2024'][1])],
    ['III кв. 2024', sumsByQuarterYear['2024'][2], fmt(sumsByQuarterYear['2024'][2])],
    ['IV кв. 2024', sumsByQuarterYear['2024'][3], fmt(sumsByQuarterYear['2024'][3])],
    ['I кв. 2025', sumsByQuarterYear['2025'][0], fmt(sumsByQuarterYear['2025'][0])],
    ['II кв. 2025', sumsByQuarterYear['2025'][1], fmt(sumsByQuarterYear['2025'][1])],
    ['III кв. 2025', sumsByQuarterYear['2025'][2], fmt(sumsByQuarterYear['2025'][2])],
    ['IV кв. 2025', sumsByQuarterYear['2025'][3], fmt(sumsByQuarterYear['2025'][3])]
  ]);
  
  // Итоги в таблице
  var tableHeadings = ['Год', 'I кв.', 'II кв.', 'III кв.', 'IV кв.', 'Итого'];
  var tableBody = annualSums.map(function(y) {
    return [
      y.year,
      fmt(y.quarters[0]),
      fmt(y.quarters[1]),
      fmt(y.quarters[2]),
      fmt(y.quarters[3]),
      fmt(y.sum)
    ];
  });
  var resultsTable = makeTable(tableHeadings, tableBody);
  
  // Управленческий вывод
  var conclusionText = '<p>';
  if (Math.abs(y2025_y2024_change) <= 5) {
    conclusionText += 'Значимое изменение объема потребительских кредитов отсутствует.';
  } else if (q4_2025_q4_2024_change > 0 && y2025_y2024_change > 0) {
    conclusionText += 'Наблюдается устойчивый рост потребительского кредитования.';
  } else if (q4_2025_q4_2024_change < 0 || y2025_y2024_change < 0) {
    conclusionText += 'Объем потребительских кредитов сокращается.';
  }
  conclusionText += '</p>';
  
  // Сборка отчёта
  var html = '';
  html += card('Ключевые показатели', tilesBlock);
  html += card('Выдачи по месяцам', monthsChart);
  html += card('Горизонтальные полосы годов', yearsBarRows);
  html += card('Горизонтальные полосы кварталов', quartersBarRows);
  html += card('Таблица результатов', resultsTable);
  html += card('Вывод', conclusionText);
  
  return html;
}
