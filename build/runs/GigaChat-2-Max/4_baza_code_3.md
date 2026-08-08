# 4. Низкая база: проценты без базы ничего не значат · GigaChat-2-Max · прогон 3 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Чтение исходной таблицы
df = pd.read_csv('data.csv')

# Расчет прироста выдачи в абсолютных рублях
df['growth_abs'] = df['now_bn_rub'] - df['was_bn_rub']

# Подсчет общей суммы выдач годом ранее и текущей
total_was = df['was_bn_rub'].sum()
total_now = df['now_bn_rub'].sum()

# Добавляем столбец с долей банка в общем рынке год назад и сейчас
df['share_was'] = df['was_bn_rub'] / total_was * 100
df['share_now'] = df['now_bn_rub'] / total_now * 100

# Рассчитываем изменение доли рынка каждого банка
df['delta_share'] = df['share_now'] - df['share_was']

# Итоговая таблица с результатами расчетов
print(df)

# Формирование выводимой строки отчета
report_string = f"Суммарный прирост рынка составил {round(total_now - total_was)} млрд рублей."

# Печать результата для отчёта
print(report_string)
```
