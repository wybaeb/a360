window.computeInputs = function (tables) {
  // расчет объема (volume)
  var f1 = tables['volume_dm.csv'];
  var volume = null;
  if (f1) {
    const rows = f1.slice(-12); // берем последние 12 строк
    let sumVolume = 0;
    for (let row of rows) {
      sumVolume += parseFloat(row['объём_операций_млн_руб']);
    }
    volume = sumVolume / rows.length;
  }
  
  // расчет доли просадки (drop)
  var f2 = tables['drop_dm2.csv'];
  var drop = null;
  if (f2) {
    let numerator = 0, denominator = 0;
    for (const row of f2) {
      numerator += parseFloat(row['недобор_к_прошлому_году_млн_руб']);
      denominator += parseFloat(row['объём_операций_млн_руб']);
    }
    drop = denominator ? numerator / denominator : null;
  }

  // расчет ставки комиссии (fee)
  var f3 = tables['fee_fin.csv'];
  var fee = null;
  if (f3) {
    const params = {};
    for (let row of f3) {
      params[row['параметр']] = row['значение'];
    }
    fee = params['средняя_комиссия_проц'] ? parseFloat(params['средняя_комиссия_проц']) / 100 : null;
  }

  return { volume: volume, drop: drop, fee: fee };
}