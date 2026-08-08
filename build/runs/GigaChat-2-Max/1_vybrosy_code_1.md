# 1. Выброс: четыре дня сбоя вместо «конвейер замедлился» · GigaChat-2-Max · прогон 1 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Загрузка данных
data = pd.read_csv('выгрузка.csv')

# Расчёт медианы и среднего абсолютного отклонения (MAD)
median_tat_min = data['tat_min'].median()
mad_tat_min = np.median(np.abs(data['tat_min'] - median_tat_min))

# Константа k=1.4826 используется для приведения MAD к масштабу стандартного отклонения
k = 1.4826
robust_z_scores = abs((data['tat_min'] - median_tat_min)) / (k * mad_tat_min)

# Определение порога для выявления выбросов (обычно используют порог >= 3.5)
threshold = 3.5

# Поиск индексов выбросов
outliers_indices = robust_z_scores > threshold

# Вывод числа найденных выбросов
num_outliers = outliers_indices.sum()
print(f'Число выявленных выбросов: {num_outliers}')

# Итоговая фраза для отчёта
if num_outliers == 0:
    print("Выбросы не обнаружены.")
else:
    print(f"В ходе анализа выявлено {num_outliers} выброса(ов).")
```
