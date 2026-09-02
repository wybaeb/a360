window.computeInputs = function (tables) {
  const f1 = tables['volume_dm.csv'];
  let volume = null;
  if (f1) {
    // Вычисляем объем операций за последние 12 месяцев
    const rows = f1.slice(-12);
    const sumVolume = rows.reduce((acc, r) => acc + Number(r['объём_операций_млн_руб'].replace(',', '.')), 0);
    volume = sumVolume / rows.length;
  }
  
  const f2 = tables['drop_dm2.csv'];
  let drop = null;
  if (f2) {
    // Расчет доли недоборной части относительно объема прошлого года
    const totalOper = f2.map(row => Number(row['объём_операций_млн_руб'].replace(',', '.')));
    const totalDrop = f2.map(row => Number(row['недобор_к_прошлому_году_млн_руб'].replace(',', '.')));
    const numerator = totalDrop.reduce((acc, v) => acc + v, 0);
    const denominator = totalOper.reduce((acc, v) => acc + v, 0);
    drop = denominator > 0 ? numerator / denominator : null;
  }

  const f3 = tables['fee_fin.csv'];
  let fee = null;
  if (f3) {
    // Ставка комиссии, деленная на 100
    const finTable = f3[0];
    const commissionRate = finTable['средняя_комиссия_проц'].replace(',', '.');
    fee = parseFloat(commissionRate) / 100;
  }

  return { volume, drop, fee };
}