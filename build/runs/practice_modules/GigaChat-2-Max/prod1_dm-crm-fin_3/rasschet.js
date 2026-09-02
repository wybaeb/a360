window.computeInputs = function (tables) {
  // среднее закрытий счетов за последние 12 месяцев
  var closuresData = tables["closures_dm.csv"];
  var closures = null;
  if (closuresData) {
    var lastMonths = closuresData.slice(-12);
    var sumClosedAccounts = 0;
    for (var i = 0; i < lastMonths.length; i++) {
      sumClosedAccounts += lastMonths[i]["закрытые_счета"];
    }
    closures = Math.round(sumClosedAccounts / lastMonths.length); // округляем до целого
  }
  
  // доля закрытий после обращений
  var linkedData = tables["linked_crm.csv"];
  var linked = null;
  if (linkedData) {
    var totalClosures = 0, afterContactClosures = 0;
    for (var j = 0; j < linkedData.length; j++) {
      totalClosures += linkedData[j]["закрытых_счетов_всего"];
      afterContactClosures += linkedData[j]["закрытий_после_обращения"];
    }
    linked = totalClosures > 0 ? afterContactClosures / totalClosures : null;
  }
  
  // расчёт маржи
  var marginData = tables["margin_fin.csv"];
  var margin = null;
  if (marginData && marginData.length >= 3) {
    var avgBalance = parseFloat(marginData.find(row => row["параметр"] === "средний_остаток_тыс_руб")["значение"]);
    var interestRate = parseFloat(marginData.find(row => row["параметр"] === "маржа_проц_годовых")["значение"]);
    var lifeSpan = parseInt(marginData.find(row => row["параметр"] === "срок_жизни_счёта_мес")["значение"]);
    
    margin = avgBalance * 1000 * interestRate / 100 / 12;
  }
  
  return { closures: closures, linked: linked, margin: margin };
}