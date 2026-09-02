window.computeInputs = function (tables) {
  var f1 = tables["volume_dm.csv"]; var volume = null;
  if (f1) {
    var last = f1.slice(-12);
    var sum = 0;
    for (var i = 0; i < last.length; i++) {
      sum += last[i]["объём_операций_млн_руб"];
    }
    volume = sum / Math.min(last.length, 12); // учитываем случай меньше 12 записей
  }
  
  var f2 = tables["drop_dm2.csv"]; var drop = null;
  if (f2) {
    var numeratorSum = 0;
    var denominatorSum = 0;
    for (var j = 0; j < f2.length; j++) {
      numeratorSum += f2[j]["недобор_к_прошлому_году_млн_руб"];
      denominatorSum += f2[j]["объём_операций_млн_руб"];
    }
    drop = denominatorSum > 0 ? numeratorSum / denominatorSum : null;
  }
  
  var f3 = tables["fee_fin.csv"]; var fee = null;
  if (f3) {
    var params = {};
    for (var k = 0; k < f3.length; k++) {
      params[f3[k]["параметр"]] = f3[k]["значение"];
    }
    fee = params["средняя_комиссия_проц"] / 100;
  }
  
  return { volume: volume, drop: drop, fee: fee };
};