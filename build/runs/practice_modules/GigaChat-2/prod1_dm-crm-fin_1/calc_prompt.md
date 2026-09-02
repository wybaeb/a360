# промпт

```
Напиши файл расчёта rasschet.js для готового мини-инструмента «Параметры проекта: Накопительный счёт: удержание закрываемых счетов». Инструмент сам читает CSV-файлы и показывает результат; от тебя — одна функция расчёта входов.

Инструмент вызывает window.computeInputs(tables) и ждёт объект с числами: {closures: число, linked: число, margin: число}.
tables — объект: ключ — имя файла, значение — массив строк-объектов; ключи строки — названия столбцов из заголовка файла; числа уже переведены в числа (запятая заменена на точку), месяц — строка вида «2025-01»; строки идут в порядке файла.

Файл 1: tables["closures_dm.csv"] — вход closures («Закрытия счетов в месяц», счетов в месяц). Первые строки файла:
﻿месяц;закрытые_счета;активные_счета
2024-01;1521;60452
2024-02;1449;63243
2024-03;1509;67165
Расчёт closures: среднее значение столбца закрытые_счета за последние 12 строк (месяцев).

Файл 2: tables["linked_crm.csv"] — вход linked («Доля закрытий после обращения», доля от 0 до 1). Первые строки файла:
﻿месяц;закрытых_счетов_всего;закрытий_после_обращения
2024-01;1521;266
2024-02;1449;224
2024-03;1509;222
Расчёт linked: сумма столбца закрытий_после_обращения ÷ сумма столбца закрытых_счетов_всего по всем строкам.

Файл 3: tables["margin_fin.csv"] — вход margin («Маржа на счёт в месяц», руб.). Первые строки файла:
﻿параметр;значение
средний_остаток_тыс_руб;220
маржа_проц_годовых;3
срок_жизни_счёта_мес;12
Расчёт margin: средний_остаток_тыс_руб × 1000 × маржа_проц_годовых ÷ 100 ÷ 12.

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


Каркас файла для этого проекта — заполни места, отмеченные многоточием, по расчётам выше и верни файл целиком:
window.computeInputs = function (tables) {
  var f1 = tables["closures_dm.csv"]; var closures = null;
  if (f1) { ... }   // среднее значение столбца закрытые_счета за последние 12 строк (месяцев)
  var f2 = tables["linked_crm.csv"]; var linked = null;
  if (f2) { ... }   // сумма столбца закрытий_после_обращения ÷ сумма столбца закрытых_счетов_всего по всем строкам
  var f3 = tables["margin_fin.csv"]; var margin = null;
  if (f3) { ... }   // средний_остаток_тыс_руб × 1000 × маржа_проц_годовых ÷ 100 ÷ 12
  return { closures: closures, linked: linked, margin: margin };
};

Проверь себя: на этих файлах closures ≈ 1 866, linked ≈ 0,1593, margin ≈ 550.

Ответ — только код файла rasschet.js в тройных кавычках.
```

# ответ

```
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
```