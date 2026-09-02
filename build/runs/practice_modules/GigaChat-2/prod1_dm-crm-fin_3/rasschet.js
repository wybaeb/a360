window.computeInputs = function (tables) {
  var f1 = tables['closures_dm.csv'];
  var closures = null;
  if (f1) {
    const data = f1.map(row => parseFloat(row['закрытые_счета']));
    let last12 = data.slice(-12);
    closures = last12.reduce((sum, val) => sum + val, 0) / last12.length;
  }
  
  var f2 = tables['linked_crm.csv'];
  var linked = null;
  if (f2) {
    const totals = f2.map(row => [parseFloat(row['закрытых_счетов_всего']), parseFloat(row['закрытий_после_обращения'])]);
    const sums = totals.reduce((acc, [total, closed]) => [acc[0] + total, acc[1] + closed], [0, 0]);
    linked = sums[1] / sums[0];
  }

  var f3 = tables['margin_fin.csv'];
  var margin = null;
  if (f3) {
    const params = f3.find(row => row['параметр'] === 'средний_остаток_тыс_руб');
    const averageBalance = parseFloat(params['значение']);
    margin = averageBalance * 1000 * parseFloat(f3.find(row => row['параметр'] === 'маржа_проц_годовых')['значение']) /
      100 / 12;
  }

  return { closures: closures, linked: linked, margin: margin };
}