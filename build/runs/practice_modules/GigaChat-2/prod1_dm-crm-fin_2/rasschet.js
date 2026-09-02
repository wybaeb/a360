/**
 * Расчёт параметров накопительного счёта: удержание закрываемых счетов
 */
window.computeInputs = function (tables) {
  /**
   * Расчёт параметра 'closures' (закрытие счетов)
   */
  const closuresFile = tables['closures_dm.csv'];
  let closuresVal = null;
  if (closuresFile) {
    const data = closuresFile.slice(-12); // берём последние 12 месяцев
    const sums = data.reduce((acc, item) => acc + parseFloat(item['закрытые_счета']), 0);
    closuresVal = sums / data.length;
  }
  
  /**
   * Расчёт параметра 'linked' (доля закрытия после обращения)
   */
  const linkedFile = tables['linked_crm.csv'];
  let linkedVal = null;
  if (linkedFile) {
    const totals = linkedFile.map(row => [row['закрытых_счетов_всего'], row['закрытий_после_обращения']]);
    const sumAllClosed = totals.reduce((prev, [total]) => prev + total, 0);
    const sumLinked = totals.reduce((prev, [, linked]) => prev + linked, 0);
    linkedVal = sumAllClosed > 0 ? sumLinked / sumAllClosed : null;
  }

  /**
   * Расчёт параметра 'margin' (маржа счета)
   */
  const marginFile = tables['margin_fin.csv'];
  let marginVal = null;
  if (marginFile) {
    const params = marginFile.find(row => row['параметр'] === 'средний_остаток_тыс_руб');
    const rate = marginFile.find(row => row['параметр'] === 'маржа_проц_годовых');
    const duration = marginFile.find(row => row['параметр'] === 'срок_жизни_счёта_мес');
    if (params && rate && duration) {
      const averageBalance = parseFloat(params['значение']) * 1000;
      const annualRate = parseFloat(rate['значение']);
      const term = parseInt(duration['значение']);
      marginVal = averageBalance * annualRate / 100 / term;
    }
  }

  return {
    closures: closuresVal,
    linked: linkedVal,
    margin: marginVal
  };
}