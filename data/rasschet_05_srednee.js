function buildReport() {
  var data = window.DATA;
  
  // Расчёт среднего, медианы и 90-го перцентиля срока рассмотрения
  var tatDays = data.map(function(row) { return row.tat_days; }).filter(Number.isFinite);
  var avgTat = tatDays.reduce(function(sum, value) { return sum + value; }, 0) / tatDays.length;
  var medTat = median(tatDays);
  var per90Tat = percentile(tatDays, 90);
  
  // Подсчет доли заявок со сроком больше 3 дней
  var overNormCount = tatDays.filter(function(value) { return value > 3; }).length;
  var overNormShare = overNormCount / tatDays.length * 100;
  
  // Корзины сроков рассмотрения
  var bins = [
    ["До 1 дня", 0, 1],
    ["1–3 дня", 1, 3],
    ["3–7 дней", 3, 7],
    ["Больше 7 дней", 7]
  ];
  
  var binCounts = [];
  for(var i = 0; i < bins.length; i++) {
    if(bins[i].length === 3) {
      var count = tatDays.filter(function(value) { 
        return value >= bins[i][1] && value < bins[i][2]; 
      }).length;
    } else {
      var count = tatDays.filter(function(value) { 
        return value >= bins[i][1]; 
      }).length;
    }
    
    var share = count / tatDays.length * 100;
    var conversion = data.filter(function(row) { 
      return (bins[i].length === 3 ? 
              row.tat_days >= bins[i][1] && row.tat_days < bins[i][2] : 
              row.tat_days >= bins[i][1])
           && Number.isFinite(row.issued); 
    }).map(function(row) { return row.issued; }).reduce(function(sum, value) { return sum + value; }, 0) / count * 100 || 0;
    
    binCounts.push({
      label: bins[i][0],
      count: count,
      share: share,
      conversion: conversion
    });
  }
  
  // Недобор выдач
  var bestConversionBin = Math.max.apply(null, binCounts.map(function(bin) { return bin.conversion; }));
  var potentialAdditionalIssues = binCounts.reduce(function(total, bin) {
    return total + (bin.count * (bestConversionBin - bin.conversion)) / 100;
  }, 0);
  
  // Гистограмма распределения срока
  var histBins = Array.from({ length: 28 }, (_, index) => ({
    from: index * 0.5,
    to: (index + 1) * 0.5,
    count: 0
  }));
  histBins.push({from: 14, to: Infinity, count: 0});
  
  tatDays.forEach(function(day) {
    for(var j = 0; j < histBins.length; j++) {
      if((histBins[j].to !== Infinity && day >= histBins[j].from && day < histBins[j].to) ||
         (histBins[j].to === Infinity && day >= histBins[j].from)) {
        histBins[j].count++;
        break;
      }
    }
  });
  
  var values = histBins.map(function(bin) { return bin.count; });
  var labels = histBins.map(function(bin) { return bin.to === Infinity ? ">14" : bin.from + "-" + bin.to; });
  var colors = histBins.map(function(bin) { return bin.from <= 3 ? "#20BA72" : "#E4572E"; });
  
  // Сборка отчёта
  var html = "";
  
  // Блок плитки ключевых показателей
  html += tiles([
    [fmt(avgTat, 1), "Средний срок"],
    [fmt(medTat, 1), "Медианный срок"],
    [fmt(per90Tat, 1), "90-й перцентиль срока"],
    [fmt(overNormShare, 1) + "%", "Доля свыше нормы"]
  ]);
  
  // Блок графика-гистограммы
  html += chartBars(values, labels, null, colors);
  
  // Блок полос долей заявок по корзинам
  html += barRows(binCounts.map(function(bin) {
    return [bin.label, bin.share, fmt(bin.share, 1) + "%"];
  }));
  
  // Блок конверсии в выдаче по корзинам
  html += barRows(binCounts.map(function(bin) {
    return [bin.label, bin.conversion, fmt(bin.conversion, 1) + "%"];
  }), true);
  
  // Таблица корзин
  html += makeTable(
    ["Корзина", "Заявки", "Доля (%)", "Конверсия в выдачу (%)"],
    binCounts.map(function(bin) {
      return [bin.label, bin.count, fmt(bin.share, 1) + "%", fmt(bin.conversion, 1) + "%"];
    })
  );
  
  // Карточка вывода
  html += card("Вывод",
               "<p>" +
                 "Срок рассмотрения составляет в среднем " + fmt(avgTat, 1) + " дня." +
                 " Медианный срок — " + fmt(medTat, 1) + " дня," +
                 " 90-й перцентиль — " + fmt(per90Tat, 1) + " дня." +
                 " Доля заявок с нарушением норматива (" + fmt(overNormShare, 1) + "%)" +
                 " свидетельствует о значительном количестве задержек." +
                 " Потенциальный недобор выдач составляет примерно " + fmt(potentialAdditionalIssues, 0).replace(/(\d)(?=(\d\d\d)+(?!\d))/g, "$1 ") + " заявок.</p>"
              );
  
  return html;
}
