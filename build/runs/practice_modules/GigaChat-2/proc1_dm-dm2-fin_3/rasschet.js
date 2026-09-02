/**
 * Расчёт входных параметров инструмента
 */
window.computeInputs = function (tables) {
  /**
   * Чтение входных файлов и расчёт показателей
   */

  // Чтение файла заявок apps_dm.csv
  const appsTable = tables['apps_dm.csv'];
  let apps = null;
  if (appsTable) {
    const rows = appsTable.slice(-12); // последние 12 строк
    const totalApps = rows.reduce((acc, row) => acc + parseFloat(row['заявок']), 0);
    apps = totalApps / rows.length;
  }

  // Чтение файла доли длительных заявок slow_dm2.csv
  const slowTable = tables['slow_dm2.csv'];
  let slow = null;
  if (slowTable) {
    const rows = slowTable.map(row => [row['рассмотрено_дольше_3_дней'], row['заявок']]);
    const sums = rows.reduce((acc, [d, z]) => ([acc[0] + d, acc[1] + z]), [0, 0]);
    slow = sums[0] / sums[1];
  }

  // Чтение файла дохода income_fin.csv
  const incomeTable = tables['income_fin.csv'];
  let income = null;
  if (incomeTable) {
    const paramRows = incomeTable.filter(row => row['параметр'] === 'средняя_сумма_кредита_руб');
    const creditSum = parseFloat(paramRows[0]['значение']);
    const marge = parseFloat(incomeTable.find(row => row['параметр'] === 'маржа_проц_годовых')['значение']);
    income = creditSum * marge / 100 / 12;
  }

  // Возвращаем рассчитанные параметры
  return {
    apps: apps,
    slow: slow,
    income: income
  };
}