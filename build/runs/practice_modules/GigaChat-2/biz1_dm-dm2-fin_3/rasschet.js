window.computeInputs = function (tables) {
  // Восстановление объема операций
  const f1 = tables['volume_dm.csv'];
  let volume = null;
  if (f1) {
    // Извлечение последних 12 месяцев
    const rows = f1.slice(-12);
    // Вычисление среднего объема операций
    const totalVolume = rows.reduce((acc, r) => acc + parseFloat(r['объём_операций_млн_руб'].replace(',', '.')), 0);
    volume = totalVolume / rows.length;
  }
  
  // Доля просадки к прошлому году
  const f2 = tables['drop_dm2.csv'];
  let drop = null;
  if (f2) {
    // Расчет суммы значений двух колонок
    const numerator = f2.map(row => parseFloat(row['недобор_к_прошлому_году_млн_руб'].replace(',', '.'))).reduce((sum, val) => sum + val, 0);
    const denominator = f2.map(row => parseFloat(row['объём_операций_млн_руб'].replace(',', '.')).toFixed(2)).reduce((sum, val) => sum + parseFloat(val), 0);
    drop = denominator > 0 ? numerator / denominator : null;
  }

  // Ставка комиссии
  const f3 = tables['fee_fin.csv'];
  let fee = null;
  if (f3) {
    // Считывание параметра средней комиссии в процентах
    const paramRow = f3.find(row => row['параметр'] === 'средняя_комиссия_проц');
    fee = paramRow && parseFloat(paramRow['значение'].replace(',', '.')) / 100;
  }

  return { volume, drop, fee };
}