# 3. Сезонность: рост, которого нет · GigaChat-2 · прогон 3 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Загружаем файл и преобразуем столбец 'date' в тип datetime
df = pd.read_csv('data.csv')
df['date'] = pd.to_datetime(df['date'])

# Создаем новый датафрейм, содержащий исходный набор данных
base_df = df.copy()

# Группируем данные по годам и месяцам, вычисляем сумму по каждому месяцу каждого года
grouped_by_month_year = base_df.groupby(['date.year', 'date.month']).agg({'amount_mln_rub': 'sum'})
grouped_by_month_year.columns = ['total_amount']

# Добавляем столбцы с порядковыми номерами месяцев (для удобства дальнейших расчетов)
grouped_by_month_year['month_number'] = grouped_by_month_year.index.get_level_values(1).astype(int)

# Строим индексы сезонов (весна, лето, осень, зима)
seasons = {
    'spring': [3, 4, 5],
    'summer': [6, 7, 8],
    'autumn': [9, 10, 11],
    'winter': [12, 1, 2]
}

# Функция для получения индекса сезона по номеру месяца
def get_season(month):
    for season_name, months in seasons.items():
        if month in months:
            return season_name
    return None

# Присваиваем сезоны каждой записи в исходной таблице
base_df['season'] = base_df['date'].dt.month.apply(get_season)

# Вычисляем средние значения суммы кредитов за сопоставимые периоды предыдущего года
previous_years = []
for year in range(base_df['date'].dt.year.min(), base_df['date'].dt.year.max()):
    # Берем последний день текущего года
    last_day_of_year = pd.Timestamp(year=year, month=12, day=31)
    
    # Берем последние дни предшествующих лет, используя временные границы периода
    prev_days = pd.date_range(start=f'{year-1}-12-31', end=f'{year-2}-12-31', freq='D')
    
    # Получаем соответствующие суммы за последние дни предыдущих годов
    previous_sums = base_df[(base_df['date'].isin(prev_days)) & (base_df['date'] <= last_day_of_year)] \
                        .groupby('season')['amount_mln_rub'].mean()
    
    # Сохраняем среднее значение сумм по сезонам
    previous_years.append(previous_sums)

# Объединяем предыдущие средние значения в один датафрейм
previous_years_df = pd.concat(previous_years, axis=1)
previous_years_df.columns = [f'year_{year}' for year in range(base_df['date'].dt.year.min() - 1, 
                                                            base_df['date'].dt.year.min() - 2, -1)]

# Вычитаем средние значения прошлого года из текущих значений
adjusted_data = base_df.merge(previous_years_df, left_on=['date.year', 'season'], right_index=True)
adjusted_data['adjustment'] = adjusted_data['amount_mln_rub'] - adjusted_data[f'year_{base_df["date"].dt.year.min()-1}']

# Форматируем таблицу для отчета
report_table = adjusted_data[['date', 'amount_mln_rub', 'adjustment']]
report_table['date'] = report_table['date'].dt.strftime('%Y-%m-%d')

# Выводим итоговую таблицу
print(report_table)

# Пример строки для отчёта:
# «Сезонная корректировка показывает рост/падение потребления потребительских кредитов относительно аналогичного периода прошлого года: январь 2023 г. (+/- X млн руб.)»
report_string = f"Сезонная корректировка показывает изменение объема выдачи потребительских кредитов относительно аналогичного периода прошлого года: {base_df['date'].min().strftime('%Y')} ({base_df['date'].dt.year.min()} год): +/{round(adjusted_data['adjustment'].sum(), 2)} млн рублей."
```
