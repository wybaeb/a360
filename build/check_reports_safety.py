# -*- coding: utf-8 -*-
"""Проверка готовых HTML-отчётов перед публикацией.

Файлы написаны моделью, а выкладываются на публичный домен под нашим именем.
Поэтому перед публикацией смотрим, что в них нет обращений наружу (внешние
скрипты, шрифты, картинки, аналитика) и нет ничего, кроме расчёта по нашей
выгрузке.

Данные отчёт подключает соседним <script src="выгрузка.js"> — единственный
внешний файл, который ему позволено грузить. Заодно это и проверяем: путь
должен быть именно к нашему .js и без каталогов.

Запуск: python3 build/check_reports_safety.py
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
DATA = ROOT / "data"

EXT = re.compile(r"""(?:src|href)\s*=\s*["']((?:https?:)?//[^"']+)""", re.I)
SRC = re.compile(r"""<script[^>]*\bsrc\s*=\s*["']([^"']+)["']""", re.I)
BAD = re.compile(r"\b(eval|document\.write|localStorage|XMLHttpRequest|WebSocket|fetch)\b")

known = {f.name for f in DATA.glob("*.js")}
bad = 0
for f in sorted(REPORTS.glob("*.html")):
    html = f.read_text(encoding="utf-8")
    ext = EXT.findall(html)
    srcs = SRC.findall(html)
    risky = BAD.findall(html)
    flags = []
    if not srcs:
        flags.append("выгрузка не подключена — нет <script src>")
    for s in srcs:
        if s not in known:
            flags.append(f"посторонний скрипт: {s}")
        elif not (REPORTS / s).exists():
            flags.append(f"файл выгрузки не лежит рядом: {s}")
    if ext:
        flags.append(f"внешние ссылки: {ext[:3]}")
    if risky:
        flags.append(f"запрещённые конструкции: {sorted(set(risky))}")
    bad += bool(flags)
    print(f"  {f.name:24} {'· '.join(flags) if flags else 'чисто'} "
          f"({len(html) // 1024} КБ, подключает {srcs})")
raise SystemExit(1 if bad else 0)
