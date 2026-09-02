/**
 * Расчёт входных параметров инструмента 'Накопительный счёт'
 */
window.computeInputs = function (tables) {
  /**
   * Считаем средние закрытия счетов за последние 12 месяцев
   */
  const closureFile = tables['closures_dm.csv'];
  let closureVal = null;
  if (closureFile) {
    const last12 = closureFile.slice(-12);
    let sum = 0;
    for (let i = 0; i < last12.length; i++) {
      sum += parseFloat(last12[i]['закрытые_счета']);
    }
    closureVal = sum / last12.length;
  }
  
  /**
   * Рассчитываем долю обращений клиентов при закрытии счета
   */
  const linkedFile = tables['linked_crm.csv'];
  let linkedVal = null;
  if (linkedFile) {
    let numerator = 0;
    let denominator = 0;
    for (const row of linkedFile) {
      numerator += parseFloat(row['закрытий_после_обращения']);
      denominator += parseFloat(row['закрытых_счетов_всего']);
    }
    linkedVal = denominator > 0 ? numerator / denominator : null;
  }

  /**
   * Вычисляем ежемесячную маржу накопительного счёта
   */
  const marginFile = tables['margin_fin.csv'];
  let marginVal = null;
  if (marginFile) {
    const rows = marginFile;
    const avgBalance = parseFloat(rows[0]['средний_остаток_тыс_руб']) * 1000;
    const annualInterestRate = parseFloat(rows[0]['маржа_проц_годовых']);
    const months = parseInt(rows[0]['срок_жизни_счёта_мес']);
    marginVal = avgBalance * annualInterestRate / 100 / months;
  }

  return {
    closures: closureVal,
    linked: linkedVal,
    margin: marginVal
  };
}