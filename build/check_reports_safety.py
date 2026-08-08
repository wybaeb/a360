# -*- coding: utf-8 -*-
"""Проверка готовых HTML-отчётов перед публикацией.

Файлы написаны моделью, а выкладываются на публичный домен под нашим именем.
Поэтому перед публикацией смотрим, что в них нет обращений наружу (внешние
скрипты, шрифты, картинки, аналитика) и нет ничего, кроме расчёта по нашему CSV.

Запуск: python3 build/check_reports_safety.py
"""
import pathlib
import re

REPORTS = pathlib.Path(__file__).resolve().parent.parent / "reports"
EXT = re.compile(r"""(?:src|href)\s*=\s*["']((?:https?:)?//[^"']+)""", re.I)
# Путь к данным модель кладёт то прямо в fetch(), то в переменную выше —
# поэтому ищем не форму вызова, а сам путь к нашему CSV где угодно в файле.
FETCH = re.compile(r"""["']((?:\.\./)?data/[\w.\-]+\.csv)["']""")
BAD = re.compile(r"\b(eval|document\.write|localStorage|XMLHttpRequest|WebSocket)\b")

bad = 0
for f in sorted(REPORTS.glob("*.html")):
    html = f.read_text(encoding="utf-8")
    ext = EXT.findall(html)
    fetches = FETCH.findall(html)
    risky = BAD.findall(html)
    wrong_fetch = [u for u in fetches if not u.startswith("../data/")]
    flags = []
    if "fetch(" not in html:
        flags.append("данные не загружаются — нет fetch")
    if not fetches:
        flags.append("не видно пути к выгрузке: данные могли быть вшиты в файл")
    if ext:
        flags.append(f"внешние ссылки: {ext[:3]}")
    if wrong_fetch:
        flags.append(f"посторонний fetch: {wrong_fetch}")
    if risky:
        flags.append(f"опасные конструкции: {sorted(set(risky))}")
    bad += bool(flags)
    print(f"  {f.name:24} {'· '.join(flags) if flags else 'чисто'} "
          f"({len(html) // 1024} КБ, fetch {fetches})")
raise SystemExit(1 if bad else 0)
