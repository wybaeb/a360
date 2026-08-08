# 1. Выброс: четыре дня сбоя вместо «конвейер замедлился» · GigaChat-2 · прогон 2 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Загружаем данные
data = pd.read_csv('my_data.csv')

# Проверяем структуру данных
print(f'Загружено {len(data)} записей')

# Определяем столбцы для анализа
col_name = 'tat_min'

# Вычисляем медиану
median_tat = data[col_name].median()

# Вычисляем среднее абсолютное отклонение от медианы (MAD)
mad_tat = np.median(np.abs(data[col_name] - median_tat))

# Определяем пороговое значение выброса (обычно ±3 * MAD)
threshold = 3 * mad_tat

# Строим робастную z-оценку (Z-score)
z_scores = ((data[col_name] - median_tat) / mad_tat)

# Фильтруем выбросы
outliers = abs(z_scores) > threshold

# Подсчитываем количество выбросов
num_outliers = outliers.sum()

# Выводим результаты
print(f'Медиана срока рассмотрения: {median_tat:.2f}')
print(f'MAD (среднее абсолютное отклонение): {mad_tat:.2f}')
print(f'Количество выбросов: {num_outliers}')

# Формулировка вывода для отчета
report_output = f'''
Робастный анализ выбросов показал, что среднее абсолютное отклонение (MAD) составляет {mad_tat:.2f}, 
причем медианный срок рассмотрения заявок равен {median_tat:.2f}. Всего было обнаружено {num_outliers} выбросов.'''

# Печать результата
print(report_output)
```
