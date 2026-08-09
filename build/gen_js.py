# -*- coding: utf-8 -*-
"""Выгрузки в виде .js — чтобы страница, написанная GigaChat, работала с диска.

Зачем не CSV. Отчёт, который модель пишет по промпту, участник скачивает и кладёт
рядом с выгрузкой на своём компьютере. Если такая страница грузит данные через
fetch("данные.csv"), браузер её блокирует: у файлов, открытых по file://, нет
источника, и любой fetch считается кросс-доменным запросом. Обойти это без
локального веб-сервера нельзя.

Обычный <script src="данные.js"> этому правилу не подчиняется — классические
скрипты грузятся с file:// как и раньше. Поэтому те же ряды кладём ещё и в .js:
файл объявляет window.DATA — массив объектов с теми же полями, что в CSV,
числа уже числами. Ни парсинга, ни fetch на стороне модели не остаётся.

CSV и TXT никуда не деваются: CSV нужен для Python и Excel, TXT — для вложения
в веб-версию GigaChat, которая CSV не принимает.

Запуск: python3 build/gen_js.py
"""
import csv
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"

HEAD = """// Аналитика 360 · учебная выгрузка «{name}»
// Подключается тегом <script src="{name}.js"></script>; после этого строки
// доступны как window.DATA — массив объектов с полями: {fields}.
// Числа уже числа: parseFloat не нужен. Данные синтетические.
window.DATA = [
"""

TAIL = """];
window.DATA_NAME = "{name}";
window.DATA_FIELDS = {fields};
"""


def _num(s):
    """Число там, где это действительно число: '0.149' -> 0.149, 'APP-1' -> строка."""
    try:
        v = float(s)
    except (TypeError, ValueError):
        return s
    return int(v) if v.is_integer() and "." not in s and "e" not in s.lower() else v


def build(csv_path):
    with csv_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    name = csv_path.stem
    fields = list(rows[0].keys())
    body = ",\n".join(json.dumps({k: _num(v) for k, v in r.items()},
                                 ensure_ascii=False, separators=(",", ":"))
                      for r in rows)
    js = (HEAD.format(name=name, fields=", ".join(fields)) + body + "\n" +
          TAIL.format(name=name, fields=json.dumps(fields, ensure_ascii=False)))
    out = DATA / f"{name}.js"
    out.write_text(js, encoding="utf-8")
    # Копия рядом с готовыми отчётами: опубликованный отчёт и скачанный участником
    # — один и тот же файл, оба подключают выгрузку соседним <script src>.
    REPORTS.mkdir(exist_ok=True)
    shutil.copy2(out, REPORTS / f"{name}.js")
    return name, len(rows), out.stat().st_size


def main():
    for f in sorted(DATA.glob("*.csv")):
        name, n, size = build(f)
        print(f"  {name + '.js':28} {n:>6} строк · {size // 1024:>4} КБ")


if __name__ == "__main__":
    main()
