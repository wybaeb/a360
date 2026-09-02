/**
* Расчёт параметров проекта 'Кредитный конвейер'
* Вход: объекты таблиц, полученные через window.tables
* Выход: объект расчётов {apps: число, slow: число, income: число}
*/
window.computeInputs = function (tables) {
  /**
   * Вычисляем apps: среднее количество заявок за последние 12 месяцев
   */
  const appsFile = tables['apps_dm.csv'];
  let appsVal = null;
  if (appsFile) {
    const arr = appsFile.slice(-12);
    const sum = arr.reduce((acc, item) => acc + parseFloat(item['заявок']), 0);
    appsVal = sum / arr.length;
  }
  
  /**
   * Рассчитываем долю slow: отношение количества долгозавершённых дел к общему числу заявок
   */
  const slowFile = tables['slow_dm2.csv'];
  let slowVal = null;
  if (slowFile) {
    let totalNumerator = 0, totalDenominator = 0;
    for (const row of slowFile) {
      totalNumerator += parseFloat(row['рассмотрено_дольше_3_дней']);
      totalDenominator += parseFloat(row['заявок']);
    }
    slowVal = totalDenominator > 0 ? totalNumerator / totalDenominator : null;
  }

  /**
   * Доходность projectsFin: средний кредит * годовая ставка / 12 месяцев
   */
  const finFile = tables['income_fin.csv'];
  let incomeVal = null;
  if (finFile) {
    const rows = finFile;
    const avgCredit = parseFloat(rows[0]['средняя_сумма_кредита_руб']);
    const margeRate = parseFloat(rows[0]['маржа_проц_годовых']) / 100;
    incomeVal = avgCredit * margeRate / 12;
  }

  return { apps: appsVal, slow: slowVal, income: incomeVal };
}