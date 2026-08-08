# 5. Среднее: норматив выполнен, клиент ждёт неделю · GigaChat-2-Max · прогон 3 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Загрузка данных из csv-файла
data = pd.read_csv('выгрузка.csv')

# Фильтрация выданных заявок (issued == 1)
issued_data = data[data['issued'] == 1]

# Анализ срока рассмотрения заявок (tat_days)
median_tat = issued_data['tat_days'].median()
percentile_90 = np.percentile(issued_data['tat_days'], 90)

# Печать результатов анализа
print(f'Медиана сроков рассмотрения заявок: {median_tat:.2f} дней')
print(f'90-й процентиль сроков рассмотрения заявок: {percentile_90:.2f} дней')

# Итоговая строка для отчёта
report_line = f'Анализ показывает, что медианное значение срока рассмотрения составляет {median_tat:.2f} дней, ' \
              f'при этом срок обработки 90% заявок укладывается в интервал до {percentile_90:.2f} дней.'

print(report_line)
```
