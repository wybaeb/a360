window.computeInputs = function (tables) {
  var f1 = tables["volume_dm.csv"]; var volume = null;
  if (f1) {
    var lastRows = f1.slice(-12);
    var sumVolume = 0;
    for (var i = 0; i < lastRows.length; i++) {
      sumVolume += lastRows[i].объём_операций_млн_руб;
    }
    volume = sumVolume / Math.min(lastRows.length, 12); 
  }
  
  var f2 = tables["drop_dm2.csv"]; var drop = null;
  if (f2) {
    var totalDrop = 0, totalVolume = 0;
    for (var j = 0; j < f2.length; j++) {
      totalDrop += f2[j].недобор_к_прошлому_году_млн_руб;
      totalVolume += f2[j].объём_операций_млн_руб;
    }
    drop = totalVolume > 0 ? totalDrop / totalVolume : null;
  }
  
  var f3 = tables["fee_fin.csv"]; var fee = null;
  if (f3) {
    var params = {};
    for (var k = 0; k < f3.length; k++) {
      params[f3[k].параметр] = f3[k].значение;
    }
    fee = params.средняя_комиссия_проц / 100;
  }
  
  return { volume: volume, drop: drop, fee: fee };
};