# 1. Выброс: четыре дня сбоя вместо «конвейер замедлился» · GigaChat-2 · прогон 3 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Чтение данных из CSV-файла
data = pd.read_csv('my_data.csv')

# Создаем копию исходных данных для анализа
df = data.copy()

# Вычисляем медиану сроков рассмотрения заявок
median_tat = df['tat_min'].median()

# Вычисляем среднее абсолютное отклонение (MAD)
mad = np.median(np.abs(df['tat_min'] - median_tat))

# Определяем робастную z-оценку как отношение отклонения от медианы к MAD
robust_z_score = lambda x: (x - median_tat) / mad

# Применяем функцию робастной z-оценки ко всей выборке
df['z_score'] = robust_z_score(df['tat_min'])

# Устанавливаем пороговое значение для выбросов (обычно ±3 является стандартным выбором)
threshold = 3

# Фильтруем выбросы по значениям робастной z-оценки
outlier_indices = abs(df['z_score']) > threshold

# Подсчитываем количество выбросов
num_outliers = outlier_indices.sum()
print(f'Общее количество выбросов: {num_outliers}')

# Выводим индексы строк с выбросами (можно добавить другие поля для подробного отчета)
print('Индексы строк с выбросами:', df[outlier_indices].index)

# Формируем строку для отчёта
report_line = f'Количество выбросов по срокам рассмотрения заявок: {num_outliers}'
print(report_line)
```
