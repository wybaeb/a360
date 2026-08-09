# -*- coding: utf-8 -*-
"""Снимок готового отчёта — для письма заказчику и для проверки глазами.

Открывает отчёт с диска (так же, как его откроет участник) и снимает страницу
целиком. Запуск: python3 build/shot_report.py 03_sezonnost [файл.png]
"""
import io
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from check_reports import browser

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    slug = sys.argv[1] if len(sys.argv) > 1 else "01_vybrosy"
    out = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else f"/tmp/{slug}.png")
    f = ROOT / "reports" / f"{slug}.html"
    d = browser()
    try:
        d.set_window_size(1280, 1000)
        d.get(f.resolve().as_uri())
        time.sleep(3)
        h = d.execute_script("return document.body.scrollHeight")
        d.set_window_size(1280, min(h + 60, 6000))
        time.sleep(1)
        png = d.get_screenshot_as_png()
    finally:
        d.quit()
    out.write_bytes(png)
    from PIL import Image
    im = Image.open(io.BytesIO(png))
    print(f"  {out} · {im.size[0]}×{im.size[1]}")


if __name__ == "__main__":
    main()
