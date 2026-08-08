# 4. Низкая база: проценты без базы ничего не значат · GigaChat-2-Max · прогон 1 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Чтение исходной таблицы
df = pd.read_csv('data.csv')

# Расчет темпов прироста выдачи кредитов в процентах
df['growth_rate'] = ((df['now_bn_rub'] / df['was_bn_rub']) - 1) * 100

# Пересчёт абсолютного прироста в миллиардах рублей
df['absolute_growth_bn_rub'] = df['now_bn_rub'] - df['was_bn_rub']

# Общая сумма выданных кредитов годом ранее и теперь
total_was = df['was_bn_rub'].sum()
total_now = df['now_bn_rub'].sum()

# Доли каждого банка на рынке годом ранее и сейчас
df['market_share_was'] = df['was_bn_rub'] / total_was * 100
df['market_share_now'] = df['now_bn_rub'] / total_now * 100

# Выводим результат расчётов в консоль
print(df)

# Итоговая таблица для отчёта
result_df = df.copy()
result_columns = ['bank', 'was_bn_rub', 'now_bn_rub', 
                  'growth_rate', 'absolute_growth_bn_rub',
                  'market_share_was', 'market_share_now']

# Округляем значения для красивого отображения
for col in result_columns[3:]:
    if col == 'growth_rate':
        result_df[col] = result_df[col].round(2).astype(str) + '%'
    else:
        result_df[col] = result_df[col].round(2)

# Вывод итогового результата
print(result_df.to_string(index=False))

# Подготовка текста для отчета
report_text = f'За прошедший год общий объем кредитных выдач вырос с {total_was:.2f} млрд руб. до {total_now:.2f} млрд руб.'
print(report_text)
```
