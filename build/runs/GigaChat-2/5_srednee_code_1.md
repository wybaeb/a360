# 5. Среднее: норматив выполнен, клиент ждёт неделю · GigaChat-2 · прогон 1 · code

Вердикт судьи: совпадает с эталоном
Элементы разбора: {"pandas": true, "код в блоке": true, "комментарии по-русски": true, "печать результата": true}

---

```python
```
# Импортируем необходимые библиотеки
import pandas as pd
import numpy as np

# Загружаем данные из CSV-файла
data = pd.read_csv('your_file.csv')

# Проверяем структуру данных и наличие нужных столбцов
print("Первая строка данных:")
print(data.head(1))

# Считаем количество записей и проверим пустые значения
print(f"Общее количество строк: {len(data)}")
print(f"Пропущенные значения: {data.isnull().sum()}")

# Фильтруем строки, где 'issued' равен 1 (заявки выданы)
issued_apps = data[data['issued'] == 1]

# Вычисляем медиану и 90-й перцентиль срока рассмотрения заявки (tat_days)
median_tat = np.median(issued_apps['tat_days'])
percentile_90 = np.percentile(issued_apps['tat_days'], 90)

# Выводим результаты анализа
print(f"Медиана срока рассмотрения заявок: {median_tat:.2f} дней")
print(f"90-й перцентиль срока рассмотрения заявок: {percentile_90:.2f} дней")

# Формируем строку для отчета
report_string = f"Анализ распределения сроков рассмотрения заявок: медиана = {median_tat:.2f}, 90-й перцентиль = {percentile_90:.2f}"

# Печать результата и строки для отчета
print(report_string)

# Сохранение отчета в файл
with open('report.txt', 'w') as file:
    file.write(report_string)
```
```
