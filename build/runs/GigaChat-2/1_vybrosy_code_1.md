# 1. Выброс: четыре дня сбоя вместо «конвейер замедлился» · GigaChat-2 · прогон 1 · code

Вердикт судьи: НЕ совпадает
Элементы разбора: {"pandas": true, "код в блоке": false, "комментарии по-русски": true, "печать результата": true}

---

# Импортируем необходимые библиотеки

import pandas as pd
import numpy as np

# Загружаем файл CSV
df = pd.read_csv('выгрузка.csv')

# Проверим структуру датасета
print(df.info())

# Убедимся, что дата представлена корректно
df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d') # приведем даты к правильному типу
df.set_index('date', inplace=True) # установим индексом колонку 'date'

# Отобразим первые несколько записей, чтобы убедиться, что структура данных соответствует ожидаемому формату
print(df.head(5))

# Посчитаем медиану срока рассмотрения заявок
median_tat_min = df['tat_min'].median()

# Вычислим медианный абсолютный отклонение (MAD)
mad_tat_min = np.median(np.abs(df['tat_min'] - median_tat_min))

# Найдём порог выброса на основе робастной z-оценки
z_threshold = 3 * mad_tat_min / np.sqrt(2)

# Применим робастную z-оценку, выделяя значения вне порога
robust_z_scores = ((df['tat_min'] - median_tat_min) / z_threshold).abs()
outlier_indices = robust_z_scores > 1.0

# Подсчитаем количество выбросов
n_outliers = outlier_indices.sum()

# Выведем результат проверки
print(f'Медиана значений tat_min: {median_tat_min:.2f}')
print(f'MAD (медианное абсолютное отклонение): {mad_tat_min:.4f}')
print(f'Порог робастной z-оценки: {z_threshold:.4f}')
print(f'Количество выбросов: {n_outliers}')

# Сформируем строку для отчёта
report_string = f'''
Проверка выбросов по медиане и MAD (робастная z-оценка):
Медианное значение тат_min: {median_tat_min:.2f}
MAD (медианный абсолютный сдвиг): {mad_tat_min:.4f}
Порог робастной z-оценки: {z_threshold:.4f}
Обнаружено выбросов: {n_outliers}
'''

# Выводим отчет в консоль
print(report_string)
