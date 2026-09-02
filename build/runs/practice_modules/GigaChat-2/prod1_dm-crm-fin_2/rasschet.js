window.computeInputs = function (tables) {
  var f1 = tables['closures_dm.csv'];
  var closures = null;
  if (f1) {
    const rows = f1.slice(-12);  // берем последние 12 месяцев
    let sumClosed = 0;
    for (let r of rows) {
      sumClosed += parseFloat(r['закрытые_счета']);
    }
    closures = sumClosed / rows.length;
  }
  
  var f2 = tables['linked_crm.csv'];
  var linked = null;
  if (f2) {
    let totalClosed = 0;
    let closedAfter = 0;
    for (const row of f2) {
      totalClosed += parseFloat(row['закрытых_счетов_всего']);
      closedAfter += parseFloat(row['закрытий_после_обращения']);
    }
    linked = closedAfter / totalClosed;
  }

  var f3 = tables['margin_fin.csv'];
  var margin = null;
  if (f3) {
    const data = f3[0];
    const avgBalance = parseFloat(data['средний_остаток_тыс_руб']) * 1000;
    const interestRate = parseFloat(data['маржа_проц_годовых']) / 100;
    const lifeTime = parseInt(data['срок_жизни_счёта_мес']);
    margin = avgBalance * interestRate / 12 / lifeTime;
  }

  return { closures: closures, linked: linked, margin: margin };
}