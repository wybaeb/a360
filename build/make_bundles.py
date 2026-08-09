# -*- coding: utf-8 -*-
"""Архив на каждый разбор: готовый отчёт + выгрузка рядом, чтобы проверить за минуту.

Смысл архива — снять с участника единственный шаг, на котором всё ломается:
файл данных и страница должны лежать в одной папке. Скачал, распаковал, открыл
двойным кликом — работает без интернета и без сервера. Это же и есть проверка,
что сценарий из промпта действительно воспроизводится.

Запуск: python3 build/make_bundles.py
"""
import pathlib
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from prompts import PRACTICES

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
DATA = ROOT / "data"
OUT = ROOT / "downloads"

README = """Аналитика 360 · разбор {num}: {title}

Что здесь лежит
  {html}   — отчёт, который написал GigaChat по промпту со страницы практики
  {js}   — учебная выгрузка, которую этот отчёт читает

Как открыть
  1. Распакуйте обе штуки в одну папку — они должны лежать рядом.
  2. Откройте {html} двойным кликом. Откроется в браузере.
  3. Страница сама посчитает всё заново из выгрузки и нарисует графики.
     Интернет не нужен: ни одной внешней ссылки внутри нет.

Если открылся пустой лист — файлы оказались в разных папках либо
{js} переименован. Имя менять нельзя: отчёт ищет его по имени.

Что должно получиться
  {expect}

Данные синтетические, сгенерированы для обучения.
Совпадения с реальными клиентами и сделками случайны.
"""


def build(p):
    html = REPORTS / f"{p['slug']}.html"
    js = DATA / p["js"]
    if not html.exists():
        return None
    OUT.mkdir(exist_ok=True)
    z = OUT / f"{p['slug']}.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
        f.writestr(html.name, html.read_text(encoding="utf-8"))
        f.writestr(js.name, js.read_text(encoding="utf-8"))
        f.writestr("КАК-ОТКРЫТЬ.txt", README.format(
            num=p["num"], title=p["title"], html=html.name, js=js.name,
            expect=p["expect"]))
    return z


def main():
    made = 0
    for p in PRACTICES:
        z = build(p)
        if z:
            made += 1
            print(f"  {z.name:22} {z.stat().st_size // 1024:>5} КБ")
        else:
            print(f"  {p['slug']:22} отчёта нет — архив не собран")
    print(f"  архивов: {made} из {len(PRACTICES)}")


if __name__ == "__main__":
    main()
