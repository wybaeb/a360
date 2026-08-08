# 1. Выброс: четыре дня сбоя вместо «конвейер замедлился» · GigaChat-2-Max · прогон 3 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Загрузка данных из csv-файла
data = pd.read_csv('выгрузка.csv')

# Расчёт медианы и абсолютного отклонения от медианы (MAD)
median_tat_min = data['tat_min'].median()
mad_tat_min = np.median(np.abs(data['tat_min'] - median_tat_min))

# Константа для робастной Z-оценки (обычно используется значение около 1.4826)
k = 1.4826

# Определение порогового значения (например, 3-кратное отклонение от нормы)
threshold = k * mad_tat_min * 3

# Фильтрация значений, выходящих за границы
outliers = data[(np.abs(data['tat_min'] - median_tat_min)) > threshold]

# Итоговая информация
num_outliers = len(outliers)
print(f'Количество выбросов: {num_outliers}')
if num_outliers == 0:
    print("Выбросы отсутствуют.")
else:
    print(f"В наборе обнаружено {num_outliers} выброса(ов).")
```
