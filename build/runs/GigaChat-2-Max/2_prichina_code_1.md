# 2. Общая причина: виноват релиз, а не контакт-центр · GigaChat-2-Max · прогон 1 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Загрузка данных из csv-файла
data = pd.read_csv('выгрузка.csv')

# Проверка частной корреляции между двумя переменными при фиксированной третьей
def partial_correlation(dataframe, var1, var2, control_var):
    """
    Вычисляет частную корреляцию между двумя переменными при контроле влияния третьей переменной.
    
    Args:
        dataframe: исходный датафрейм
        var1: первая переменная
        var2: вторая переменная
        control_var: третья переменная, влияние которой мы хотим исключить
        
    Returns:
        Частная корреляция между var1 и var2 при исключении влияния control_var
    """
    # Рассчитываем коэффициенты парной регрессии каждой переменной относительно контрольной
    beta_1_control = np.polyfit(dataframe[control_var], dataframe[var1], deg=1)[0]
    beta_2_control = np.polyfit(dataframe[control_var], dataframe[var2], deg=1)[0]
    
    # Удаляем влияние контрольной переменной
    residual_1 = dataframe[var1] - beta_1_control * dataframe[control_var]
    residual_2 = dataframe[var2] - beta_2_control * dataframe[control_var]
    
    # Корреляция остатков даёт искомую частную корреляцию
    return np.corrcoef(residual_1, residual_2)[0][1]

# Проверим связь обращений в контакт-центр (calls_th) и оттока клиентов (churn_pct),
# контролируя долю ошибок в мобильном приложении (app_error_rate_pct).
corr_calls_churn_fixed_app_errors = partial_correlation(
    data, 'calls_th', 'churn_pct', 'app_error_rate_pct'
)

print(f'Частная корреляция между обращениями в контакт-центр и оттоком клиентов '
      f'(при фиксированной доле сессий с ошибкой): {corr_calls_churn_fixed_app_errors:.4f}')

# Итоговая фраза для отчёта
report_line = (
    f"В результате анализа выявлена частная корреляция между количеством "
    f"обращений в контакт-центр и уровнем оттока клиентов (r={corr_calls_churn_fixed_app_errors:.4f}), "
    f"учитывая влияние доли сессий с ошибкой."
)

print(report_line)
```
