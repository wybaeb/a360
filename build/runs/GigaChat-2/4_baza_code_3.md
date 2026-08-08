# 4. Низкая база: проценты без базы ничего не значат · GigaChat-2 · прогон 3 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Чтение исходных данных
data = pd.read_csv('my_data.csv')

# Названия столбцов зададим вручную
data.columns = ['bank', 'was_bn_rub', 'now_bn_rub']

# Проверка корректности загруженных данных
print(f'Загружено {len(data)} записей.')

# Проверим наличие пустых значений и заменим их нулями
data.fillna(0, inplace=True)

# Рассчитаем темпы прироста в абсолютных значениях
data['abs_growth'] = data['now_bn_rub'] - data['was_bn_rub']

# Рассчитаем долю рынка текущего периода относительно прошлого года
data['market_share'] = data['now_bn_rub'] / data['was_bn_rub]

# Получим сводную таблицу по банкам
result_table = data.pivot(index='bank', values=['abs_growth', 'market_share'])

# Округлим значения долей рынка до трёх знаков после запятой
result_table['market_share'] = result_table['market_share'].round(3)

# Печать результатов в удобочитаемом виде
print(result_table.to_string())

# Формулировка для отчета
report_output = f"""
Проверена динамика выдачи кредитов банковскими организациями:
- Темпы прироста в абсолютных деньгах указаны в колонке abs_growth.
- Доля рынка текущего периода относительно прошлого года указана в колонке market_share.
"""
```
