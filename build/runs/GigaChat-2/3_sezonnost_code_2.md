# 3. Сезонность: рост, которого нет · GigaChat-2 · прогон 2 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Загружаем файл CSV в DataFrame
df = pd.read_csv('data.csv')

# Преобразуем столбец 'date' в тип datetime
df['date'] = pd.to_datetime(df['date'])

# Устанавливаем 'date' как индекс, чтобы удобно фильтровать даты
df.set_index('date', inplace=True)

# Создаем новую колонку 'year_month' для группировки по месяцам года
df['year_month'] = df.index.to_period('M').astype(str)

# Группируем данные по годам и месяцам, вычисляем сумму выдач по каждому месяцу
grouped = df.groupby(['year_month'])['amount_mln_rub'].sum().reset_index()

# Добавляем новый столбец 'prev_year' для хранения значения предыдущего месяца
grouped['prev_year'] = grouped['amount_mln_rub'].shift(12)

# Удаляем первую строку (для которой нет предыдущее значение)
grouped.drop(grouped.index[0], inplace=True)

# Вычисляем процентное изменение между сопоставимыми периодами текущего и прошлого года
grouped['percent_change'] = ((grouped['amount_mln_rub'] / grouped['prev_year']) * 100).round(2)

# Фильтруем месяцы с большим ростом относительно предыдущего года
filtered_data = grouped.query("percent_change > 100")

# Выводим итоговые результаты
print(f"Таблица сравнения сопоставимых периодов по месяцам:")
print(grouped[['year_month', 'amount_mln_rub', 'prev_year', 'percent_change']])

# Пример строки для отчета:
report_line = f"За январь {grouped.iloc[-1]['year_month']} объем выданных кредитов составил {grouped.iloc[-1]['amount_mln_rub']:.2f} млн рублей, увеличившись на {grouped.iloc[-1]['percent_change']:.2f}% по сравнению с аналогичным периодом прошлого года."

print(report_line)
```
