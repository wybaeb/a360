# 4. Низкая база: проценты без базы ничего не значат · GigaChat-2 · прогон 1 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Загружаем файл CSV
df = pd.read_csv('data.csv')

# Проверяем структуру данных
print("Структура исходных данных:")
print(df.head())

# Добавляем колонки с приростом в % и доле рынка
df['growth_rate'] = ((df['now_bn_rub'] - df['was_bn_rub']) / df['was_bn_rub']) * 100  # Темпы прироста в %
df['market_share'] = df['now_bn_rub'] / df['now_bn_rub'].sum()  # Доля рынка

# Рассчитываем абсолютный прирост
df['absolute_growth'] = df['now_bn_rub'] - df['was_bn_rub']

# Выводим результат пересчета
print("\nИтоговые показатели:\n")
print(df[['bank', 'growth_rate', 'market_share', 'absolute_growth']])

# Формируем строку для отчета
report_line = f'Абсолютный прирост кредитов составил {np.sum(df["absolute_growth"]):,.2f} млрд рублей.'
print(report_line)
```
