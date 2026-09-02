window.computeInputs = function (tables) {
  // Расчёт closures: среднее значение столбца 'закрытые_счета' за последние 12 месяцев
  var closuresData = tables['closures_dm.csv']; var closuresVal = null;
  if (closuresData) {
    var lastMonths = closuresData.slice(-12);
    var sumClosedAccounts = 0;
    for (var i = 0; i < lastMonths.length; i++) {
      sumClosedAccounts += lastMonths[i]['закрытые_счета'];
    }
    closuresVal = Math.round(sumClosedAccounts / lastMonths.length); // округляем до целого
  }
  
  // Расчёт linked: сумма 'закрытий_после_обращения' ÷ сумму 'закрытых_счетов_всего'
  var linkedData = tables['linked_crm.csv']; var linkedVal = null;
  if (linkedData) {
    var totalAfterCallClosures = 0, totalAllClosures = 0;
    for (var j = 0; j < linkedData.length; j++) {
      totalAfterCallClosures += linkedData[j]['закрытий_после_обращения'];
      totalAllClosures += linkedData[j]['закрытых_счетов_всего'];
    }
    linkedVal = totalAllClosures > 0 ? totalAfterCallClosures / totalAllClosures : null;
  }

  // Расчёт margin: средний остаток × 1000 × процентная ставка ÷ 100 ÷ срок жизни счёта
  var marginData = tables['margin_fin.csv']; var marginVal = null;
  if (marginData) {
    var params = {};
    for (var k = 0; k < marginData.length; k++) {
      params[marginData[k]['параметр']] = marginData[k]['значение'];
    }
    marginVal = Math.round(params['средний_остаток_тыс_руб'] * 1000 * params['маржа_проц_годовых'] / 100 / params['срок_жизни_счёта_мес']);
  }

  return { closures: closuresVal, linked: linkedVal, margin: marginVal };
}