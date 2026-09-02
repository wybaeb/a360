window.computeInputs = function (tables) {
  // среднее заявок за последние 12 месяцев
  var appsTable = tables["apps_dm.csv"];
  var apps = null;
  if (appsTable) {
    var lastApps = appsTable.slice(-12);
    var sumApps = 0;
    for (var i = 0; i < lastApps.length; i++) {
      sumApps += lastApps[i].заявок;
    }
    apps = Math.round(sumApps / lastApps.length); // округляем среднее значение заявок
  }
  
  // доля медленно обработанных заявок
  var slowTable = tables["slow_dm2.csv"];
  var slow = null;
  if (slowTable) {
    var totalSlow = 0, totalApps = 0;
    for (var j = 0; j < slowTable.length; j++) {
      totalSlow += slowTable[j].рассмотрено_дольше_3_дней;
      totalApps += slowTable[j].заявок;
    }
    slow = totalApps > 0 ? totalSlow / totalApps : null;
  }
  
  // доход с одной выдачи кредита в месяц
  var incomeTable = tables["income_fin.csv"];
  var income = null;
  if (incomeTable) {
    var params = {};
    for (var k = 0; k < incomeTable.length; k++) {
      params[incomeTable[k].параметр] = incomeTable[k].значение;
    }
    income = params.средняя_сумма_кредита_руб * params.маржа_проц_годовых / 100 / 12;
  }
  
  return { apps: apps, slow: slow, income: income };
}