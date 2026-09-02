window.computeInputs = function (tables) {
  var f1 = tables["closures_dm.csv"]; var closures = null;
  if (f1) {
    var last = f1.slice(-12); var sum = 0;
    for (var i = 0; i < last.length; i++) sum += last[i]["закрытые_счета"];
    closures = Math.round(sum / last.length);
  }
  
  var f2 = tables["linked_crm.csv"]; var linked = null;
  if (f2) {
    var numerator = 0, denominator = 0;
    for (var j = 0; j < f2.length; j++) {
      numerator += f2[j]["закрытий_после_обращения"];
      denominator += f2[j]["закрытых_счетов_всего"];
    }
    linked = denominator > 0 ? numerator / denominator : null;
  }
  
  var f3 = tables["margin_fin.csv"]; var margin = null;
  if (f3) {
    var params = {};
    for (var k = 0; k < f3.length; k++)
      params[f3[k]["параметр"]] = f3[k]["значение"];
    
    margin = params["средний_остаток_тыс_руб"] * 1000 *
             params["маржа_проц_годовых"] / 100 /
             params["срок_жизни_счёта_мес"];
  }
  
  return { closures: closures, linked: linked, margin: margin };
};