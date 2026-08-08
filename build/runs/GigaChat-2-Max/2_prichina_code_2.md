# 2. Общая причина: виноват релиз, а не контакт-центр · GigaChat-2-Max · прогон 2 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Чтение исходной таблицы из csv-файла
data = pd.read_csv('выгрузка.csv')

# Приведение числовых столбцов к float
for col in ['calls_th', 'churn_pct', 'app_error_rate_pct']:
    data[col] = data[col].astype(float)

# Частная корреляция между двумя переменными (здесь используется общий подход через частную ковариацию)
def partial_corr(cov_matrix):
    inv_cov = np.linalg.inv(cov_matrix)
    return -inv_cov / np.sqrt(np.diag(inv_cov).reshape(-1, 1) * np.diag(inv_cov))

# Вычисляем матрицу частных корреляций 
cov_matrix = data[['calls_th', 'churn_pct', 'app_error_rate_pct']].cov()
partial_correlation_matrix = partial_corr(cov_matrix)

# Выводим частные коэффициенты корреляции между обращениями и оттоком при фиксированной доле ошибок
print("Частный коэффициент корреляции между обращениями и оттоком при фиксированной доле ошибок:", 
      round(partial_correlation_matrix.iloc[0, 1], 4))

# Итоговая фраза для отчёта
if abs(partial_correlation_matrix.iloc[0, 1]) > 0.5:
    conclusion = f"Приведена сильная зависимость между числом обращений и оттоком клиентов при учёте доли ошибок в приложениях."
else:
    conclusion = f"Слабая связь числа обращений и уровня оттока выявлена при контроле доли ошибок в мобильных приложениях."
    
print(conclusion)
```
