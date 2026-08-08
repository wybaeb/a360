# 3. Сезонность: рост, которого нет · GigaChat-2 · прогон 1 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Загрузка данных из CSV-файла
df = pd.read_csv('data.csv')

# Преобразование столбца 'date' в тип datetime
df['date'] = pd.to_datetime(df['date'])

# Выбираем только последние полные годы, чтобы избежать частичных месяцев в последнем периоде
last_year_start = df['date'].dt.year.max() - 1
df = df.query(f'date >= {last_year_start}-01-01 & date < {df["date"].dt.year.max()} -01-01')

# Группируем данные по годам и месяцам, вычисляем месячные суммы и добавляем метки сезонов
df['year_month'] = df['date'].dt.to_period('M') # преобразуем даты в периоды (год+месяц)
df['season'] = df['date'].dt.quarter # определяем сезоны: 1-й квартал, 2-й квартал и т.д.

# Суммируем количество выдач кредитов по каждому месяцу года
grouped_data = df.groupby(['year_month', 'season'])['amount_mln_rub'].sum().reset_index()

# Создаем колонку 'period' для сравнения сопоставимых периодов, исключая январь каждого года
grouped_data['period'] = grouped_data['year_month'].astype(str).str.replace('-01', '')

# Проверка сезонной динамики: сравниваем между годами по одинаковым сезонам и месяцам
comparable_years = [f'{y}' for y in range(grouped_data['year_month'].dt.year.min(), 
                                           grouped_data['year_month'].dt.year.max())]

for year in comparable_years:
    # Берём данные текущего года и предыдущего года для анализа сопоставимости
    current_year = grouped_data.query(f'year_month.dt.year == {year}')
    previous_year = grouped_data.query(f'year_month.dt.year == {year - 1}')
    
    # Сравниваем значения сопоставимых периодов
    compare_result = current_year.merge(previous_year, on=['period'], suffixes=('_current', '_previous'))
    compare_result['change_amount'] = compare_result['amount_mln_rub_current'] / compare_result['amount_mln_rub_previous']
    
    print(f'Сравнение сопоставимых периодов за {year} год:')
    print(compare_result[['period', 'amount_mln_rub_current', 'amount_mln_rub_previous', 'change_amount']])

# Выводим результат сравнения годовых значений первого квартала и четвертого квартала последнего года
final_year = grouped_data['year_month'].dt.year.max()
first_quarter = grouped_data.query(f'season == 1 & year_month.dt.year == {final_year}')
fourth_quarter = grouped_data.query(f'season == 4 & year_month.dt.year == {final_year}')

print(f'\nСезонная динамика за последний год ({final_year}):')
print(first_quarter[['year_month', 'amount_mln_rub']].rename(columns={'amount_mln_rub': '1 квартал'}))
print(fourth_quarter[['year_month', 'amount_mln_rub']].rename(columns={'amount_mln_rub': '4 квартал'}))

# Пример строки для отчета:
report_line = f'Снижение объема выдачи потребительских кредитов в январе {final_year} г. составило {np.round(1 - first_quarter["amount_mln_rub"].values[0]/fourth_quarter["amount_mln_rub"].values[0], 2)*100:.2f}%'
print(report_line)
```
