# 4. Низкая база: проценты без базы ничего не значат · GigaChat-2-Max · прогон 2 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Чтение исходного csv-файла
df = pd.read_csv('data.csv')

# Добавляем столбец с приростом в миллиардах рублей
df['growth_abs'] = df['now_bn_rub'] - df['was_bn_rub']

# Суммы выдачи всех банков год назад и сейчас
total_was = df['was_bn_rub'].sum()
total_now = df['now_bn_rub'].sum()

# Доли каждого банка на рынке год назад и сейчас
df['share_was'] = df['was_bn_rub'] / total_was
df['share_now'] = df['now_bn_rub'] / total_now

# Прирост долей на рынке
df['growth_share'] = df['share_now'] - df['share_was']

# Вывод итоговых значений
print(df)

# Итоговая строка для отчёта
report_string = f'За прошедший год рынок вырос на {np.round(total_now - total_was, 1)} млрд руб., наибольший рост показали банки: ' + \
                ', '.join(df.nlargest(3, 'growth_abs')['bank'])

print(report_string)
```
