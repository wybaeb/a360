window.computeInputs = function (tables) {
  // расчёт параметра closures ("Закрытие счетов в месяц")
  const closuresFile = tables['closures_dm.csv'];
  let closuresValue = null;
  if (closuresFile) {
    const last12Rows = closuresFile.slice(-12);
    const closedAccountsSums = [];
    for (let monthData of last12Rows) {
      closedAccountsSums.push(monthData.closed_accounts);
    }
    closuresValue = closedAccountsSums.reduce((acc, curr) => acc + curr) / closedAccountsSums.length;
  }
  
  // расчёт параметра linked ("Доля закрытий после обращения")
  const linkedFile = tables['linked_crm.csv'];
  let linkedValue = null;
  if (linkedFile) {
    let totalClosed = 0, afterContacted = 0;
    for (const row of linkedFile) {
      totalClosed += parseFloat(row.total_closed);
      afterContacted += parseFloat(row.after_contacted);
    }
    linkedValue = totalClosed ? afterContacted / totalClosed : null;
  }

  // расчёт параметра margin ("Маржа на счет в месяц")
  const marginFile = tables['margin_fin.csv'];
  let marginValue = null;
  if (marginFile) {
    const params = {};
    for (const row of marginFile) {
      params[row.parameter] = row.value;
    }
    const avgBalance = parseFloat(params['average_balance_thousand_rub']) * 1000;
    const annualInterestRate = parseFloat(params['annual_interest_rate']);
    const accountLifeMonths = parseFloat(params['account_life_months']);
    marginValue = avgBalance * annualInterestRate / 100 / accountLifeMonths;
  }

  return {
    closures: closuresValue,
    linked: linkedValue,
    margin: marginValue
  };
}