window.computeInputs = function (tables) {
  // Закрытия счетов в месяц (среднее за последние 12 месяцев)
  var cl = tables["closures_dm.csv"];
  var closures = null;
  if (cl) {
    var last12 = cl.slice(-12);
    var sumClosures = 0;
    for (var i = 0; i < last12.length; i++) sumClosures += last12[i]["закрытые_счета"];
    closures = Math.round(sumClosures / last12.length); // округляем до целого
  }
  
  // Доля закрытий после обращения (сумма по столбцам)
  var lnk = tables["linked_crm.csv"];
  var linked = null;
  if (lnk) {
    var totalClosed = 0, closedAfterContact = 0;
    for (var j = 0; j < lnk.length; j++) {
      totalClosed += lnk[j]["закрытых_счетов_всего"];
      closedAfterContact += lnk[j]["закрытий_после_обращения"];
    }
    linked = totalClosed > 0 ? closedAfterContact / totalClosed : null;
  }
  
  // Маржа на счет в месяц (по параметрам)
  var mrg = tables["margin_fin.csv"];
  var margin = null;
  if (mrg && mrg.length === 3) {
    var params = {};
    for (var k = 0; k < mrg.length; k++) params[mrg[k]["параметр"]] = mrg[k]["значение"];
    margin = params["средний_остаток_тыс_руб"] * 1000 
           * params["маржа_проц_годовых"] / 100 
           / params["срок_жизни_счёта_мес"];
  }
  
  return { closures: closures, linked: linked, margin: margin };
}