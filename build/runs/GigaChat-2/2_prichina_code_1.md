# 2. Общая причина: виноват релиз, а не контакт-центр · GigaChat-2 · прогон 1 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Загружаем файл CSV
df = pd.read_csv('data.csv')

# Проверяем структуру данных
print("Первые пять записей:")
print(df.head())

# Выбираем столбцы для анализа
columns_to_analyze = ['calls_th', 'churn_pct', 'app_error_rate_pct']

# Проверка наличия пропущенных значений
print("\nПроверка наличия пропущенных значений:")
print(df[columns_to_analyze].isnull().sum())

# Преобразуем данные к числовому типу
df[columns_to_analyze] = df[columns_to_analyze].apply(pd.to_numeric, errors='coerce')

# Убедимся, что теперь нет пропусков
print("\nПропущенные значения заменены на NaN:")
print(df.isnull().sum())

# Удалим записи с пустыми значениями
df_cleaned = df.dropna(subset=columns_to_analyze)

# Рассчитываем ковариацию между парами переменных
cov_matrix = df_cleaned[columns_to_analyze].cov()
print("\nКовариационная матрица:")
print(cov_matrix)

# Рассчитываем коэффициент частной корреляции Спирмена с фиксацией третьего показателя
# Используем функцию Kendall's tau-b для учета порядка ранжирования
from scipy.stats import kendalltau

def partial_correlation(x, y, z):
    r_xy = kendalltau(x, y)[0]
    r_xz = kendalltau(x, z)[0]
    r_yz = kendalltau(y, z)[0]
    
    numerator = r_xy - r_xz * r_yz
    denominator = np.sqrt((1 - r_xz**2) * (1 - r_yz**2))
    
    if denominator == 0:
        return 0
    else:
        return numerator / denominator

# Пример вычисления частичной корреляции между двумя показателями
# при фиксированном третьем показателе
result = partial_correlation(df_cleaned['calls_th'], df_cleaned['churn_pct'], df_cleaned['app_error_rate_pct'])
print(f"\nЧастичная корреляция между calls_th и churn_pct при фиксированном app_error_rate_pct: {result:.4f}")

# Формулируем строку для отчета
report_string = f"Частичная корреляция между обращениями в контакт-центр и отбоем по картам при фиксированной доле ошибок в мобильном приложении составила {result:.4f}"
print(report_string)
```
