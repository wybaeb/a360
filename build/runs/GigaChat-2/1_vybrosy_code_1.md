# 1. Выброс: четыре дня сбоя вместо «конвейер замедлился» · GigaChat-2 · прогон 1 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Загружаем файл
df = pd.read_csv('data.csv')

# Проверяем структуру данных
print(f'Загружено {len(df)} строк')

# Выбираем столбец 'tat_min'
col_name = 'tat_min'
data = df[col_name]

# Вычисляем медиану
median = data.median()
print(f'Медиана значений: {median:.4f}')

# Вычисляем медианный абсолютный отклонение (MAD)
mad = np.median(np.abs(data - median))
print(f'Median Absolute Deviation (MAD): {mad:.4f}')

# Определяем робастную z-оценку (zscore)
robust_z_score = (data - median) / (1.4826 * mad) # множитель 1.4826 корректирует распределение Гаусса

# Фильтруем выбросы: z-оценка больше 3.5 считается выбросом
threshold = 3.5
outlier_mask = np.abs(robust_z_score) > threshold

# Получаем индексы выбросов
outliers_index = outlier_mask.index[outlier_mask]

# Выводим количество обнаруженных выбросов
num_outliers = len(outliers_index)
print(f'Обнаружено выбросов: {num_outliers}')

# Создаем строку для отчета
report_row = f'{col_name}, {median:.4f}, {mad:.4f}, {num_outliers}'
print(report_row)

# Выводим заголовок таблицы для отчета
header = f'{col_name}, Медиана, MAD, Количество выбросов'
print(header)
```
