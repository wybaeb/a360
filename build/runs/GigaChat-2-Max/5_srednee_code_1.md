# 5. Среднее: норматив выполнен, клиент ждёт неделю · GigaChat-2-Max · прогон 1 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
import pandas as pd
import numpy as np

# Загрузка данных
data = pd.read_csv('выгрузка.csv')

# Проверяем наличие пропущенных значений
print("Количество пропусков:")
print(data.isnull().sum())

# Анализируем распределение срока рассмотрения заявок среди выданных кредитов
issued_data = data[data['issued'] == 1]

# Вычисляем медиану и 90-й перцентиль сроков рассмотрения выданных заявок
median_tat_issued = issued_data['tat_days'].median()
percentile_90_tat_issued = np.percentile(issued_data['tat_days'], 90)

# Выводим результаты анализа
print(f"\nМедиана срока рассмотрения выданных заявок: {median_tat_issued:.2f} дней")
print(f"90-й перцентиль срока рассмотрения выданных заявок: {percentile_90_tat_issued:.2f} дней\n")

# Итоговая строка для отчёта
report_line = f"Время рассмотрения заявок составляет в среднем около {median_tat_issued:.0f} дней, причем у 90% одобренных заявок срок рассмотрения не превышает {percentile_90_tat_issued:.0f} дней."

print(report_line)
```
