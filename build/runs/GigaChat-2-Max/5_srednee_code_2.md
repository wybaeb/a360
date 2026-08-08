# 5. Среднее: норматив выполнен, клиент ждёт неделю · GigaChat-2-Max · прогон 2 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Чтение данных из csv-файла
data = pd.read_csv('выгрузка.csv')

# Проверяем количество записей
print(f'Количество записей: {len(data)}')

# Анализируем распределение срока рассмотрения заявок среди выданных кредитов
issued_data = data[data['issued'] == 1]

# Вычисляем медиану и 90-й процентиль
median_tat_days_issued = issued_data['tat_days'].median()
percentile_90_tat_days_issued = issued_data['tat_days'].quantile(0.9)

# Печать результатов анализа
print(f'\nАнализ сроков рассмотрения одобренных заявок:')
print(f'- Медиана: {median_tat_days_issued:.2f} дней')
print(f'- 90-й процентиль: {percentile_90_tat_days_issued:.2f} дней\n')

# Итоговая строка для отчёта
report_line = f'Для выданных заявок медианный срок рассмотрения составляет {median_tat_days_issued:.2f} дней, ' \
              f'a у 90% заявок этот срок не превышает {percentile_90_tat_days_issued:.2f} дней.'

print(report_line)
```
