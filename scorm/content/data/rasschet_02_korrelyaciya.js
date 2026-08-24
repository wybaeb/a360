function buildReport() {
  var data = window.DATA;
  
  // Выбираем ряды данных
  var weeks = data.map(function(row) { return row.week_start; });
  var calls = data.map(function(row) { return row.calls_th; }).filter(Number.isFinite);
  var churns = data.map(function(row) { return row.churn_pct; }).filter(Number.isFinite);
  var errors = data.map(function(row) { return row.app_error_rate_pct; }).filter(Number.isFinite);
  
  // Корреляции Пирсона
  var corr_calls_churn = correlation(calls, churns);
  var corr_errors_calls = correlation(errors, calls);
  var corr_errors_churn = correlation(errors, churns);
  
  // Частная корреляция
  var partial_corr_calls_churn = (corr_calls_churn - corr_errors_calls * corr_errors_churn) /
                                Math.sqrt((1 - Math.pow(corr_errors_calls, 2)) *
                                          (1 - Math.pow(corr_errors_churn, 2)));
  
  // Нормализованные данные для графика
  var normCalls = calls.map(function(val) { return val / Math.max.apply(null, calls); });
  var normChurns = churns.map(function(val) { return val / Math.max.apply(null, churns); });
  var normErrors = errors.map(function(val) { return val / Math.max.apply(null, errors); });
  
  // Подготовка HTML
  var html = "";
  
  // Блок 1: Плитки с корреляциями
  html += tiles([
    ["Корреляция обращений и оттока", fmt(corr_calls_churn, 2)],
    ["Корреляция ошибок и обращений", fmt(corr_errors_calls, 2)],
    ["Корреляция ошибок и оттока", fmt(corr_errors_churn, 2)],
    ["Частная корреляция обращений и оттока", fmt(partial_corr_calls_churn, 2)]
  ]);
  
  // Блок 2: Сравнение связей
  html += card("Связь обращений и оттока",
               '<div style="display: flex; justify-content: space-between;">'
             + '  <span>' + fmt(corr_calls_churn, 2) + '</span>'
             + '  <span>(без учета ошибок)</span>'
             + '</div>'
             + '<div style="display: flex; justify-content: space-between;">'
             + '  <span>' + fmt(partial_corr_calls_churn, 2) + '</span>'
             + '  <span>(с учетом ошибок)</span>'
             + '</div>');
  
  // Блок 3: линейные графики нормированных рядов (по одному на ряд)
  html += card("Обращения по неделям (нормировано)",
    chartLine(normCalls, ["нед. 1", "нед. 26"], []));
  html += card("Отток по неделям (нормировано)",
    chartLine(normChurns, ["нед. 1", "нед. 26"], []));
  html += card("Доля ошибок по неделям (нормировано)",
    chartLine(normErrors, ["нед. 1", "нед. 26"], []));

  
  // Блок 4: Горизонтальные полосы
  html += barRows([
    ["Обрат./отток", Math.abs(corr_calls_churn), fmt(Math.abs(corr_calls_churn), 2)],
    ["Ошибки/обращение", Math.abs(corr_errors_calls), fmt(Math.abs(corr_errors_calls), 2)],
    ["Ошибки/отток", Math.abs(corr_errors_churn), fmt(Math.abs(corr_errors_churn), 2)],
    ["Частная корр.", Math.abs(partial_corr_calls_churn), fmt(Math.abs(partial_corr_calls_churn), 2)]
  ]);
  
  // Блок 5: Таблица
  html += makeTable(["Неделя", "Обращения", "Отток", "Ошибка"], 
                    data.map(function(row) {
                      return [row.week_start, fmt(row.calls_th), fmt(row.churn_pct)+"%", fmt(row.app_error_rate_pct)+"%"];
                    }));
  
  // Блок 6: Итоговая интерпретация
  if (Math.abs(corr_calls_churn - partial_corr_calls_churn) <= 0.05) {
    html += card("Вывод", "<p>Зависимость обращений и оттока значимо не изменилась при учете доли ошибок.</p>");
  } else if (partial_corr_calls_churn > corr_calls_churn) {
    html += card("Вывод", "<p>При учете доли ошибок зависимость обращений и оттока усилилась.</p>");
  } else {
    html += card("Вывод", "<p>При учете доли ошибок зависимость обращений и оттока снизилась.</p>");
  }
  
  return html;
}
