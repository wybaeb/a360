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

Проверь себя: на этих файлах closures ≈ 1 866, linked ≈ 0,1593, margin ≈ 550.

Ответ — только код файла rasschet.js в тройных кавычках.
```

# ответ

```javascript
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
```