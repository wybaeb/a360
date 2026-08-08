# 3. Сезонность: рост, которого нет · GigaChat-2-Max · прогон 1 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Загрузка данных
data = pd.read_csv('your_data.csv', parse_dates=['date'])

# Сортировка по дате
data.sort_values(by='date', inplace=True)

# Создание колонки с годом и месяцем
data['year'] = data['date'].dt.year
data['month'] = data['date'].dt.month

# Построение индекса сезонности методом средней сезонной компоненты
seasonal_index = data.groupby(['month'])['amount_mln_rub'].mean()

# Расчёт среднего значения по каждому месяцу каждого года отдельно
avg_by_year_month = data.groupby(['year', 'month'])['amount_mln_rub'].mean().reset_index()

# Добавляем индекс сезонности к каждой строке 
avg_by_year_month['seasonal_adjusted_amount'] = avg_by_year_month.apply(
    lambda row: row['amount_mln_rub'] / seasonal_index[row['month']], axis=1
)

# Вычисление изменений от периода к периоду
comparative_analysis = avg_by_year_month.pivot(index='month', columns='year', values='seasonal_adjusted_amount')
change_yoy = comparative_analysis.pct_change(axis=1).dropna(how='all', axis=1)*100

# Итоговый вывод: изменение выдачи кредитов по месяцам относительно предыдущего года (%)
print(change_yoy.round(2))

# Вывод общей динамики изменения кредитований за последний доступный год относительно предпоследнего
last_two_years = change_yoy.columns[-2:]
final_result = f'Изменение выдач потребительских кредитов в {last_two_years[1]} г. относительно {last_two_years[0]} г.: {change_yoy[last_two_years[1]].mean():.2f}%'
print(final_result)
```
