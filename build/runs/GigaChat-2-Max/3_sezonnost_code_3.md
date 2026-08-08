# 3. Сезонность: рост, которого нет · GigaChat-2-Max · прогон 3 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Загрузка данных
df = pd.read_csv('data.csv')

# Преобразование столбца даты в тип datetime
df['date'] = pd.to_datetime(df['date'])

# Создание индекса даты
df.set_index('date', inplace=True)

# Проверка наличия ежедневных записей
if len(df.index.unique()) != len(df):
    print("Ошибка: присутствуют дублирующиеся записи.")
else:
    # Сглаживание данных методом скользящего среднего (по умолчанию окно 7 дней)
    df['amount_smooth'] = df['amount_mln_rub'].rolling(window=7).mean()

    # Разделение дат на годы и месяцы-дни для сравнения сопоставимых периодов
    df['year'] = df.index.year
    df['month_day'] = df.index.strftime('%m-%d')

    # Группировка по месяц/день и вычисление средних значений по годам
    grouped_df = df.groupby(['month_day']).agg({'amount_smooth': ['mean', 'std'], 
                                               'year': lambda x: list(x)})
    
    # Вычисляем стандартное отклонение от среднегодового значения (оцениваем стабильность периода)
    std_deviation = grouped_df['amount_smooth']['std']

    # Итоговый вывод
    avg_values = grouped_df['amount_smooth']['mean']
    print(f"Средние выдачи потребительских кредитов по дням года:\n{avg_values}\n")
    print(f"Показатель стабильности периодов (стандартное отклонение):\n{std_deviation.mean()}")

    # Формулировка для отчёта
    report_line = f"В результате анализа выявлено среднее значение выдач потребительских кредитов по каждому дню года и уровень вариации между годами составляет {round(std_deviation.mean(), 2)} млн рублей."
    print(report_line)
```
