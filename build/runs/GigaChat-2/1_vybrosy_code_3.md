# 1. Выброс: четыре дня сбоя вместо «конвейер замедлился» · GigaChat-2 · прогон 3 · code

Вердикт судьи: НЕ совпадает
Элементы разбора: {"pandas": true, "код в блоке": false, "комментарии по-русски": true, "печать результата": true}

---

# Импортируем необходимые библиотеки
import pandas as pd
import numpy as np

# Загружаем файл CSV в DataFrame df
df = pd.read_csv('data.csv')

# Проверим структуру данных и типы переменных
print(df.info())

# Переведём столбец 'date' в тип datetime
df['date'] = pd.to_datetime(df['date'])

# Для робастной обработки выбросов используем медианный центр и медианный абсолютный
# отклонение (MAD). Вычислим среднюю медиану и MAD для поля tat_min
median_tat = df['tat_min'].median()
mad_tat = np.median(np.abs(df['tat_min'] - median_tat))

# Определяем пороговую величину выбросов (обычно берут несколько сигм от медианы)
threshold = 3 * mad_tat / np.sqrt(2)

# Вычисляем значения Z-статистики (робастную z-оценку):
z_scores = (df['tat_min'] - median_tat) / mad_tat

# Найдём индексы наблюдений, где значение Z-оценки превышает пороговое значение
outlier_indices = np.where(z_scores > threshold)[0]

# Отобразим количество обнаруженных выбросов
num_outliers = len(outlier_indices)
print(f'Количество выбросов: {num_outliers}')

# Создадим новую колонку с флагом наличия выброса
df['is_outlier'] = False
df.loc[outlier_indices, 'is_outlier'] = True

# Сформируем строку для отчёта:
report_line = f'Обнаружено выбросов: {num_outliers}, дата первого выброса: {df["date"].iloc[outlier_indices[0]]}'

# Выводим результаты в консоль
print(report_line)

# Пример вставки строки в отчёт:
# Обнаружено выбросов: 5, дата первого выброса: 2023-10-06

# Можно сохранить результат с меткой выбросов в новый файл
df.to_csv('outlier_detected_data.csv', index=False)
