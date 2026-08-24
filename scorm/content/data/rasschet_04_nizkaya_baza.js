function buildReport() {
  var data = window.DATA;
  
  // Расчёт показателей
  var totalWas = data.reduce(function(sum, row) { return sum + row.was_bn_rub; }, 0);
  var totalNow = data.reduce(function(sum, row) { return sum + row.now_bn_rub; }, 0);
  var marketGrowthRate = ((totalNow / totalWas - 1) * 100).toFixed(1);
  
  // Темпы прироста и абсолютные приросты
  var growthRates = [];
  for (var i = 0; i < data.length; i++) {
    var rate = ((data[i].now_bn_rub / data[i].was_bn_rub - 1) * 100).toFixed(1);
    var absGrowth = (data[i].now_bn_rub - data[i].was_bn_rub).toFixed(1);
    growthRates.push({
      bank: data[i].bank,
      was: data[i].was_bn_rub,
      now: data[i].now_bn_rub,
      growthRate: parseFloat(rate),
      absoluteGrowth: parseFloat(absGrowth)
    });
  }
  
  // Рыночные доли
  var sharesBefore = [], sharesAfter = [];
  for (i = 0; i < data.length; i++) {
    var shareBefore = (data[i].was_bn_rub / totalWas * 100).toFixed(1);
    var shareAfter = (data[i].now_bn_rub / totalNow * 100).toFixed(1);
    sharesBefore.push(parseFloat(shareBefore));
    sharesAfter.push(parseFloat(shareAfter));
    
    growthRates[i].shareBefore = parseFloat(shareBefore);
    growthRates[i].shareAfter = parseFloat(shareAfter);
    growthRates[i].shareChange = parseFloat(shareAfter) - parseFloat(shareBefore);
  }
  
  // Блок плитки ключевых чисел
  var keyTiles = [
    ["Рынок был", fmt(totalWas)],
    ["Рынок стал", fmt(totalNow)],
    ["Прирост «Мы», млрд ₽", fmt(growthRates.find(function(r){return r.bank === "Мы";}).absoluteGrowth)],
    ["Изменение доли «Мы», п.п.", fmt(growthRates.find(function(r){return r.bank === "Мы";}).shareChange)]
  ];
  
  // Столбчатый график
  var valuesBefore = data.map(function(row) { return row.was_bn_rub; }).filter(Number.isFinite);
  var valuesAfter = data.map(function(row) { return row.now_bn_rub; }).filter(Number.isFinite);
  var labels = data.map(function(row) { return row.bank; });
  var chartData = valuesBefore.concat(valuesAfter);
  var colors = Array(data.length).fill("#c8d2dc").concat(Array(data.length).fill("#20BA72"));
  
  // Горизонтальные полосы темпов прироста и абсолютных приростов
  var ratesForBar = growthRates.map(function(row) { return [row.bank, row.growthRate, fmt(row.growthRate) + "%"]; });
  var absGrowthsForBar = growthRates.map(function(row) { return [row.bank, row.absoluteGrowth, fmt(row.absoluteGrowth)]; });
  
  // Таблица итоговых результатов
  var tableHeaders = ["Игрок", "Было", "Стало", "Темп, %", "Прирост, млрд ₽", "Доля была, %", "Доля стала, %", "Изменение доли, п.п."];
  var tableBody = growthRates.map(function(row) {
    return [
      row.bank,
      fmt(row.was),
      fmt(row.now),
      fmt(row.growthRate) + "%",
      fmt(row.absoluteGrowth),
      fmt(row.shareBefore) + "%",
      fmt(row.shareAfter) + "%",
      fmt(row.shareChange) + " п.п."
    ];
  });
  
  // Формирование HTML-разметки отчета
  var html = "";
  html += tiles(keyTiles);
  html += chartBars(chartData, labels, colors);
  html += barRows(ratesForBar);
  html += barRows(absGrowthsForBar);
  html += makeTable(tableHeaders, tableBody);
  
  // Управленческий вывод
  var ourRow = growthRates.find(row => row.bank === "Мы");
  if (Math.abs(ourRow.shareChange) <= 5) {
    html += card("Вывод", "<p>Заметного изменения доли рынка у игрока \"Мы\" не произошло.</p>");
  } else if (ourRow.shareChange > 0) {
    html += card("Вывод", "<p>Доля рынка игрока \"Мы\" увеличилась на " + fmt(ourRow.shareChange) + " п.п., несмотря на низкий темп прироста.</p>");
  } else {
    html += card("Вывод", "<p>Доля рынка игрока \"Мы\" снизилась на " + fmt(-ourRow.shareChange) + " п.п., несмотря на положительный абсолютный прирост.</p>");
  }
  
  return html;
};
