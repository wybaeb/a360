# 2. Общая причина: виноват релиз, а не контакт-центр · GigaChat-2 · прогон 3 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Загружаем файл CSV
df = pd.read_csv('data.csv')

# Проверяем структуру данных
print("Первая десятка записей:")
print(df.head(10))

# Переводим недели в даты (если в исходных данных даты представлены строками)
df['week_start'] = pd.to_datetime(df['week_start'])

# Убедимся, что переменные числовые типы
for col in ['calls_th', 'churn_pct', 'app_error_rate_pct']:
    df[col] = pd.to_numeric(df[col], errors='coerce') # Замещаем некорректные значения NaN

# Отбираем только нужные столбцы для анализа
cols_to_analyze = ['calls_th', 'churn_pct', 'app_error_rate_pct']
df_analyzed = df[cols_to_analyze]

# Проверка наличия пропущенных значений
print("\nПропущенные значения в анализируемых колонках:")
print(df_analyzed.isnull().sum())

# Вычисляем частные корреляции между парами признаков при контроле третьего признака
# Используем коэффициент Спирмена (non-parametric correlation)
from scipy.stats import spearmanr

correlations = {}

# Корреляция calls_th и churn_pct при фиксированной app_error_rate_pct
cor_call_churn_app_fixed = spearmanr(df_analyzed['calls_th'], df_analyzed['churn_pct'],
                                     nan_policy='omit',
                                     method='spearman',
                                     axis=0,
                                     fixed factor=df_analyzed['app_error_rate_pct'].values)
correlations['calls_th-churn_pct_fixed-app_error_rate_pct'] = cor_call_churn_app_fixed.correlation

# Корреляция calls_th и app_error_rate_pct при фиксированной churn_pct
cor_call_app_churn_fixed = spearmanr(df_analyzed['calls_th'], df_analyzed['app_error_rate_pct'],
                                     nan_policy='omit',
                                     method='spearman',
                                     axis=0,
                                     fixed factor=df_analyzed['churn_pct'].values)
correlations['calls_th-app_error_rate_pct_fixed-churn_pct'] = cor_call_app_churn_fixed.correlation

# Корреляция churn_pct и app_error_rate_pct при фиксированной calls_th
cor_churn_app_calls_fixed = spearmanr(df_analyzed['churn_pct'], df_analyzed['app_error_rate_pct'],
                                      nan_policy='omit',
                                      method='spearman',
                                      axis=0,
                                      fixed factor=df_analyzed['calls_th'].values)
correlations['churn_pct-app_error_rate_pct_fixed-calls_th'] = cor_churn_app_calls_fixed.correlation

# Выводим результаты
print("\nЧастичные коэффициенты корреляции (Спирмен):")
for key, value in correlations.items():
    print(f"{key}: {value:.4f}")

# Итоговая строка для отчета
report_line = f"Частичная корреляция calls_th и churn_pct при фиксированном app_error_rate_pct: {correlations['calls_th-churn_pct_fixed-app_error_rate_pct']:.4f}"
print(report_line)
```
