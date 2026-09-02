window.computeInputs = function (tables) {
  // вычисляем среднее закрытия счетов
  const f1 = tables['closures_dm.csv'];
  let closures = null;
  if (f1) {
    const rows = f1.slice(-12); // берем последние 12 строк
    const total = rows.reduce((acc, r) => acc + parseFloat(r['закрытые_счета']), 0);
    closures = total / rows.length;
  }

  // вычисляем долю связанных клиентов среди закрытых
  const f2 = tables['linked_crm.csv'];
  let linked = null;
  if (f2) {
    const sums = f2.map(row => ({ month: row['месяц'], numClosed: parseFloat(row['закрытых_счетов_всего']), linked: parseFloat(row['закрытий_после_обращения']) }));
    const totals = sums.reduce((acc, {numClosed, linked}) => ({totalClosed: acc.totalClosed + numClosed, totalLinked: acc.totalLinked + linked}), {totalClosed: 0, totalLinked: 0});
    linked = totals.totalLinked / totals.totalClosed;
  }

  // вычисляем размер маржи
  const f3 = tables['margin_fin.csv'];
  let margin = null;
  if (f3) {
    const [paramRow] = f3;
    const avgBalance = parseFloat(paramRow['средний_остаток_тыс_руб']);
    const annualMargin = parseFloat(paramRow['маржа_проц_годовых']);
    const months = parseFloat(paramRow['срок_жизни_счёта_мес']);
    margin = avgBalance * 1000 * annualMargin / 100 / months;
  }

  return { closures, linked, margin };
}