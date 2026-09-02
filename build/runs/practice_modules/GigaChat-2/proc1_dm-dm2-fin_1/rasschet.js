/**
 * Расчёт входных параметров кредитного конвейера: сроки рассмотрения заявки
 */
window.computeInputs = function (tables) {
  /**
   * Вход apps — Заявки в месяц
   */
  const appsTable = tables['apps_dm.csv'];
  let appsResult = null;
  if (appsTable) {
    const rows = appsTable.slice(-12); // берём последние 12 строк
    const sumApps = rows.reduce((acc, row) => acc + parseFloat(row['заявок']), 0);
    appsResult = sumApps / rows.length;
  }

  /**
   * Вход slow — Доля заявок дольше трёх дней
   */
  const slowTable = tables['slow_dm2.csv'];
  let slowResult = null;
  if (slowTable) {
    const totalCount = slowTable.map(row => parseFloat(row['заявок'])).reduce((sum, value) => sum + value, 0);
    const errorCount = slowTable.map(row => parseFloat(row['рассмотрено_дольше_3_дней'])).reduce((sum, value) => sum + value, 0);
    slowResult = totalCount > 0 ? errorCount / totalCount : null;
  }

  /**
   * Вход income — Доход с выдачи в месяц
   */
  const incomeTable = tables['income_fin.csv'];
  let incomeResult = null;
  if (incomeTable) {
    const paramRow = incomeTable.find(row => row['параметр'] === 'средняя_сумма_кредита_руб');
    const creditSum = parseFloat(paramRow['значение']);
    const interestRate = parseFloat(incomeTable.find(row => row['параметр'] === 'маржа_проц_годовых')['значение']) / 100 / 12;
    incomeResult = creditSum * interestRate;
  }

  return {
    apps: appsResult,
    slow: slowResult,
    income: incomeResult
  };
}