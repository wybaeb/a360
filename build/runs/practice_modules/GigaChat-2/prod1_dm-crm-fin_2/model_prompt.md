# промпт

```
Напиши файл model.js для готового мини-инструмента «Финансовая модель эффекта: Накопительный счёт: удержание закрываемых счетов». Инструмент показывает поля параметров, таблицу и график; от тебя — одна функция расчёта потока по месяцам.

Инструмент вызывает window.effectFlows(p), где p — объект с числами: delta (изменение показателя в месяц), volume (объём), price (стоимость единицы, руб. в месяц), ramp (выход на полный уровень, мес.), keep (срок сохранения эффекта, мес.), capex (единовременные затраты, руб.), opex (ежемесячные затраты, руб.), horizon (горизонт, мес.), rate (годовая ставка дисконтирования, доля), kind (строка "cohort").
Функция возвращает массив из horizon + 1 объектов для t = 0, 1, …, horizon с полями t, income, cost, cf, cum, cum_disc.

Формулы (повтори точно):
— доля выхода на уровень: rampShare(t) = min(t / ramp, 1); при ramp = 0 равна 1;
— full = delta × volume;
— units(t) для t ≥ 1: сумма full × rampShare(k) по k от max(1, t − keep + 1) до t — когорты каждого месяца живут keep месяцев;
— income(t) = units(t) × price; income(0) = 0;
— cost(0) = capex; cost(t) = opex для t ≥ 1;
— cf(t) = income(t) − cost(t); cum(t) — накопленная сумма cf от 0 до t;
— месячная ставка m = (1 + rate)^(1/12) − 1; disc(t) = cf(t) / (1 + m)^t; cum_disc(t) — накопленная сумма disc от 0 до t.

Требования: только JavaScript без HTML и пояснений; объявить функцию именно так: window.effectFlows = function (p) { ... }; обычный цикл for, без async и внешних библиотек; имена латиницей, комментарии по-русски. Все поля p — числа, приводить их не нужно.

Каркас функции — заполни места, отмеченные многоточием, по формулам выше и верни файл целиком:
window.effectFlows = function (p) {
  var rows = [], cum = 0, cumDisc = 0;
  var m = ...;                 // месячная ставка из годовой p.rate
  var full = ...;              // delta × volume
  function rampShare(t) { ... }
  for (var t = 0; t <= p.horizon; t++) {
    var units = 0, income = 0, cost = (t === 0) ? p.capex : p.opex;
    if (t >= 1) {
      ...                      // units(t) по формуле для kind = "cohort"
      income = units * p.price;
    }
    var cf = income - cost;
    cum += cf;
    var disc = ...;            // cf / (1 + m)^t
    cumDisc += disc;
    rows.push({ t: t, income: income, cost: cost, cf: cf, cum: cum, cum_disc: cumDisc });
  }
  return rows;
};

Проверь себя: при delta = 99,08, volume = 1, price = 550, ramp = 3, keep = 12, capex = 600000, opex = 50000, horizon = 24, rate = 0.15 накопленный поток впервые становится неотрицательным в месяце 7, а cum_disc в последнем месяце около 7 945 641 руб.

Ответ — только код файла model.js в тройных кавычках.
```

# ответ

```
window.effectFlows = function (p) {
  var rows = [], cum = 0, cumDisc = 0;
  var m = Math.pow((1 + p.rate), (1 / 12)) - 1;   // месячная ставка из годовой p.rate
  var full = p.delta * p.volume;                  // delta × volume

  function rampShare(t) {
    return Math.min(t / p.ramp, 1);
  }

  for (var t = 0; t <= p.horizon; t++) {
    var units = 0, income = 0, cost = (t === 0) ? p.capex : p.opex;
    if (t >= 1) {
      // Сумма full × rampShare(k) по k от max(1, t − keep + 1) до t
      for (var k = Math.max(1, t - p.keep + 1); k <= t; k++) {
        units += full * rampShare(k);
      }
      income = units * p.price;
    }
    var cf = income - cost;
    cum += cf;
    var disc = cf / (1 + m) ** t;                     //cf / (1 + m)^t
    cumDisc += disc;
    rows.push({
      t: t,
      income: income,
      cost: cost,
      cf: cf,
      cum: cum,
      cum_disc: cumDisc
    });
  }
  return rows;
}
```