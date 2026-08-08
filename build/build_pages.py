# -*- coding: utf-8 -*-
"""Сборка страниц артефактов: HTML → парольный гейт → корень репозитория.

Одни и те же исходники дают две версии:
  корень репозитория — зашифрованные страницы для GitHub Pages;
  scorm/ — те же страницы без шифрования, для LMS заказчика (там доступ
  ограничивает сама LMS, второй пароль только мешал бы).

Запуск:
    python3 build/build_pages.py --password 'ПАРОЛЬ'
    A360_PASSWORD='ПАРОЛЬ' python3 build/build_pages.py
"""
import argparse
import csv
import os
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import gate
import longread
import practice
import theme

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE_URL = "https://wybaeb.github.io/a360/"

HUB_BODY = """
<header><div class="wrap">
  <div class="eyebrow">Карпов Курсы × Сбер · Аналитика 360</div>
  <h1>Материалы практической части</h1>
  <p class="lead">Всё, что нужно между вводной встречей и Шагом 1: теория, вынесенная
     из занятия, и самостоятельная практика с GigaChat на тех же данных, что были
     в разборах.</p>
  <div class="meta">
    <span class="chip">Шаги <b>1–4</b></span>
    <span class="chip">Данные <b>синтетические</b></span>
  </div>
</div></header>

<section><div class="wrap">
<h2>Что здесь есть</h2>

<div class="card acc">
<h4><a href="longread.html">1 · Лонгрид: пять ошибок вывода</a></h4>
<p>Предчтение к практической части. Пять ошибок, из-за которых решение стоит дороже:
выброс, общая причина, сезонность, низкая база, среднее. Для каждой — как выглядит,
почему обманывает, какой проверкой ловится и что спросить у аналитика. Каждое
методическое утверждение — со ссылкой на первоисточник.</p>
<p class="sub" style="margin:0">Чтение 12 минут. Формул для запоминания нет.</p>
</div>

<div class="card acc">
<h4><a href="practice.html">2 · Практика: повторите разборы в GigaChat</a></h4>
<p>Те же пять разборов, что были на встрече, — но руками. Пятнадцать готовых промптов
с кнопкой копирования, пошаговая инструкция для веб-версии GigaChat, эталонные ответы
и таблица воспроизводимости. Программировать не нужно, файлы загружать не нужно.</p>
<p class="sub" style="margin:0">40–60 минут. Проверено на GigaChat 2 и GigaChat 2 Max.</p>
</div>

<div class="card">
<h4>3 · Данные</h4>
<p>Пять синтетических выгрузок, на которых построены разборы, — в CSV и TXT.
Ссылки на них лежат внизу страницы практики.</p>
</div>
</div></section>

<section><div class="wrap">
<h2>Что сделать до Шага 1</h2>
<ol class="steps">
  <li><b>Прочитайте лонгрид.</b> На встрече теорию не читаем — она вынесена сюда
      сознательно, и без неё занятие работает вдвое хуже.</li>
  <li><b>Пройдите хотя бы два разбора из практики.</b> Любые два: важно один раз
      увидеть, как проверка переворачивает вывод.</li>
  <li><b>Возьмите свой показатель.</b> Тот, по которому недавно принималось спорное
      решение, — с ним и придёте на Шаг 1.</li>
</ol>
<div class="card warn">
<p><b>Правило работы с данными.</b> В кейсы и промпты берём только учебные
и обезличенные данные. Реальные клиентские выгрузки во внешние сервисы
не отправляем.</p>
</div>
</div></section>

<footer><div class="wrap">
  Аналитика 360 · практическая часть, Шаги 1–4 · Карпов Курсы для Сбера.<br>
  Страницы закрыты паролем. Все данные в примерах синтетические.
</div></footer>
"""

PAGES = [
    ("index.html", "Материалы практической части · Аналитика 360",
     "Материалы практической части", HUB_BODY,
     "Здесь лонгрид к первой встрече и самостоятельная практика с GigaChat."),
    ("longread.html", "Пять ошибок вывода · Аналитика 360",
     "Лонгрид: пять ошибок вывода", longread.BODY,
     "Предчтение к практической части. Чтение — 12 минут."),
    ("practice.html", "Самостоятельная практика в GigaChat · Аналитика 360",
     "Практика в GigaChat", None,
     "Пять разборов с вводной встречи, которые можно повторить самому."),
]


def make_txt():
    """TXT-копии выгрузок: веб-версия GigaChat принимает txt, но не csv."""
    d = ROOT / "data"
    for f in sorted(d.glob("*.csv")):
        with f.open(encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        (d / (f.stem + ".txt")).write_text(
            "\n".join(" | ".join(r) for r in rows), encoding="utf-8")
    print("  txt-копии выгрузок:", len(list(d.glob('*.txt'))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--password", default=os.environ.get("A360_PASSWORD"))
    a = ap.parse_args()
    if not a.password:
        sys.exit("нужен пароль: --password '...' или A360_PASSWORD=...")

    make_txt()
    scorm = ROOT / "scorm" / "content"
    scorm.mkdir(parents=True, exist_ok=True)

    for name, title, heading, body, intro in PAGES:
        html = theme.page(title, body if body is not None else practice.body())
        (scorm / name).write_text(html, encoding="utf-8")          # открытая версия
        (ROOT / name).write_text(
            gate.wrap(html, a.password, title, heading, intro), encoding="utf-8")
        print(f"  {name:15} открытая {len(html) // 1024:>4} КБ · "
              f"зашифрованная {len(( ROOT / name).read_text(encoding='utf-8')) // 1024:>4} КБ")

    # Ассеты и данные нужны обеим версиям: пути в HTML относительные.
    for sub in ("assets", "data"):
        dst = scorm / sub
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(ROOT / sub, dst)
    print("  scorm/content: страницы, assets, data")


if __name__ == "__main__":
    main()
