# 2. Общая причина: виноват релиз, а не контакт-центр · GigaChat-2-Max · прогон 3 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Загрузка данных из csv-файла
data = pd.read_csv('выгрузка.csv')

# Приведение процентных значений к долям (избавляемся от процентов)
data['churn_pct'] /= 100
data['app_error_rate_pct'] /= 100

# Частная корреляция между двумя переменными (например, call_th и churn_pct),
# учитывая влияние третьей переменной (app_error_rate_pct).

# Корреляционная матрица исходных признаков
corr_matrix = data.corr()

# Формула частной корреляции (пример расчета частной корреляции между calls_th и churn_pct):
# r_(x,y.z) = (r_xy - r_xz * r_yz) / sqrt((1-r_xz^2)*(1-r_yz^2))
r_calls_churn = corr_matrix.loc['calls_th', 'churn_pct']
r_calls_app_err = corr_matrix.loc['calls_th', 'app_error_rate_pct']
r_churn_app_err = corr_matrix.loc['churn_pct', 'app_error_rate_pct']

partial_corr = (
    (r_calls_churn - r_calls_app_err * r_churn_app_err) /
    np.sqrt((1 - r_calls_app_err**2) * (1 - r_churn_app_err**2))
)

print(f'Частная корреляция между обращениями в контакт-центр и оттоком клиентов '
      f'(при учёте доли ошибок в приложении): {partial_corr:.4f}')

# Итоговая фраза для отчёта
if abs(partial_corr) > 0.5:
    conclusion = ('Связь обращений в контакт-центр и оттока клиентов достаточно тесна даже '
                  'после учета влияния уровня ошибок мобильного приложения.')
else:
    conclusion = ('Связь обращений в контакт-центр и оттока клиентов слаба или отсутствует '
                  'даже после исключения влияния уровня ошибок мобильного приложения.')
    
print(conclusion)
```
