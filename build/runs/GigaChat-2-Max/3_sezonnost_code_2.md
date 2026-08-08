# 3. Сезонность: рост, которого нет · GigaChat-2-Max · прогон 2 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Загрузка данных
data = pd.read_csv('file.csv', parse_dates=['date'])

# Сортировка по дате
data.sort_values(by='date', inplace=True)

# Установка даты как индекс
data.set_index('date', inplace=True)

# Преобразование индекса дат в ежемесячные значения 
monthly_data = data.resample('M').sum()

# Вычисление значений предыдущего года для каждого месяца
monthly_data['prev_year_amount'] = monthly_data['amount_mln_rub'].shift(12)

# Расчёт разницы между текущим годом и предыдущим
monthly_data['diff_with_prev_year'] = monthly_data['amount_mln_rub'] - monthly_data['prev_year_amount']

# Расчёт процентной разницы
monthly_data['percent_diff'] = (monthly_data['diff_with_prev_year'] / monthly_data['prev_year_amount']) * 100

# Фильтрация последних трёх лет
last_three_years = monthly_data.tail(36)

# Итоговые числа
avg_monthly_change = last_three_years['diff_with_prev_year'].mean()
avg_percent_change = last_three_years['percent_diff'].mean()

print(f"Среднее изменение выдачи потребительских кредитов месяц к месяцу за последние три года составило {avg_monthly_change:.2f} млн рублей.")
print(f"В среднем изменения составили {avg_percent_change:.2f}% относительно аналогичного периода прошлого года.")

# Вывод для отчёта
report_line = f"Сезонность снята методом сравнения сопоставимых месяцев год к году, среднее изменение объёмов выдач составляет {avg_monthly_change:.2f} млн руб., или {avg_percent_change:.2f}%."
print(report_line)
```
