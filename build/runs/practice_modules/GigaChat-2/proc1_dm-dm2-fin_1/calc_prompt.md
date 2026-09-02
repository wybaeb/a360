# промпт

```
Напиши файл расчёта rasschet.js для готового мини-инструмента «Параметры проекта: Кредитный конвейер: срок рассмотрения заявки». Инструмент сам читает CSV-файлы и показывает результат; от тебя — одна функция расчёта входов.

Инструмент вызывает window.computeInputs(tables) и ждёт объект с числами: {apps: число, slow: число, income: число}.
tables — объект: ключ — имя файла, значение — массив строк-объектов; ключи строки — названия столбцов из заголовка файла; числа уже переведены в числа (запятая заменена на точку), месяц — строка вида «2025-01»; строки идут в порядке файла.

Файл 1: tables["apps_dm.csv"] — вход apps («Заявки в месяц», заявок в месяц). Первые строки файла:
﻿месяц;заявок
2024-01;5410
2024-02;4997
2024-03;5426
Расчёт apps: среднее значение столбца заявок за последние 12 строк (месяцев).

Файл 2: tables["slow_dm2.csv"] — вход slow («Доля заявок дольше трёх дней», доля от 0 до 1). Первые строки файла:
﻿месяц;заявок;рассмотрено_дольше_3_дней
2024-01;5410;1604
2024-02;4997;1453
2024-03;5426;1656
Расчёт slow: сумма столбца рассмотрено_дольше_3_дней ÷ сумма столбца заявок по всем строкам.

Файл 3: tables["income_fin.csv"] — вход income («Доход с выдачи в месяц», руб.). Первые строки файла:
﻿параметр;значение
средняя_сумма_кредита_руб;350000
маржа_проц_годовых;5
Расчёт income: средняя_сумма_кредита_руб × маржа_проц_годовых ÷ 100 ÷ 12.

Требования:
— только JavaScript, без HTML и без пояснений; объявить функцию именно так: window.computeInputs = function (tables) { ... };
— столбцы брать по названию из заголовка: row["закрытые_счета"]; имена переменных латиницей, комментарии по-русски;
— async и await, fetch и внешние библиотеки не использовать;
— если файла нет (tables["имя"] не определён) — вернуть для этого входа null, не бросать ошибку;
— «последние 12 строк» — это последние 12 элементов массива строк (arr.slice(-12)); при свёртке по месяцам сначала сложить значения строк с одинаковым месяцем, затем взять последние 12 месяцев по порядку.

Образец оформления (другой проект, другие файлы и столбцы):
window.computeInputs = function (tables) {
  // среднее столбца за последние 12 месяцев
  var a = tables["a_dm.csv"]; var aVal = null;
  if (a) { var last = a.slice(-12), s = 0; for (var i = 0; i < last.length; i++) s += last[i]["выдано"]; aVal = s / last.length; }
  // доля: сумма числителя ÷ сумма знаменателя
  var b = tables["b_dm2.csv"]; var bVal = null;
  if (b) { var n = 0, d = 0; for (var j = 0; j < b.length; j++) { n += b[j]["с_ошибкой"]; d += b[j]["всего"]; } bVal = d ? n / d : null; }
  // параметр из таблицы параметр;значение
  var c = tables["c_fin.csv"]; var cVal = null;
  if (c) { var p = {}; for (var k = 0; k < c.length; k++) p[c[k]["параметр"]] = c[k]["значение"]; cVal = p["ставка_проц"] / 100 * 1000; }
  return { a: aVal, b: bVal, c: cVal };
};

Проверь себя: на этих файлах apps ≈ 5 782, slow ≈ 0,3008, income ≈ 1 458.

Ответ — только код файла rasschet.js в тройных кавычках.
```

# ответ

```
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
```