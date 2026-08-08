# -*- coding: utf-8 -*-
"""HTML-обработчики датасетов: генерация в GigaChat и проверка в настоящем браузере.

Промпт «html» просит модель написать самодостаточную страницу, которая грузит
CSV, лежащий рядом, считает проверку и рисует результат. Проверка здесь не
формальная: страница кладётся в repo/reports, весь репозиторий поднимается
локальным http-сервером (fetch по file:// браузер запрещает), страница
открывается в headless Chrome и проверяется на три вещи:

  1. в консоли нет ошибок JavaScript;
  2. полосы-диаграммы нарисованы и имеют ненулевую ширину;
  3. в тексте страницы есть все ключевые числа разбора — те же, что на слайдах.

Проходит только та версия, которая выполнила все три условия. Её и кладём
в reports/ — участник открывает готовую ссылку, а не «пример кода».

Запуск:
    GIGACHAT_AUTH_KEY=$(secret get GIGA1_GIGACHAT_TOKEN) \
        python3 build/check_reports.py [--attempts 4] [--model GigaChat-2-Max] [--only baza]
"""
import argparse
import functools
import http.server
import json
import pathlib
import re
import socketserver
import sys
import threading
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gigachat
from prompts import PRACTICES, rendered

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
RUNS = pathlib.Path(__file__).resolve().parent / "runs"
FENCE = re.compile(r"```(?:html)?\s*\n(.*?)```", re.S)

# Ключевые числа разбора. Проверяем не форматирование, а сам факт: страница
# досчитала до тех же величин, что показаны на занятии. Каждый элемент —
# список допустимых написаний, достаточно одного.
EXPECT = {
    # Проверяем величину, а не её форматирование: страница может написать
    # «+74 %» или «74,5 %», «25 %» или «25,3 %» — оба варианта верные.
    "vybrosy":   [[r"7[45][.,]?\d*"], [r"\b4\b|четыр"], [r"41[.,]3"],
                  [r"16\.06|2026-06-16"], [r"[34][.,]?\d*\s*%"]],
    "prichina":  [[r"0[.,]8[34]"], [r"0[.,]9[23]"], [r"0[.,]89"], [r"0[.,]0[678]"]],
    # Для сезонности мало верных чисел: вывод обязан назвать снижение. Первая
    # прошедшая версия писала «объёмы стабильны» при −6,8 % год к году —
    # числа верные, а вывод противоположен разбору.
    "sezonnost": [[r"3[56][.,]?\d*\s*%"], [r"[-−]\s?[67][.,]?\d*\s*%"],
                  [r"38\s?0[56]\d"], [r"33\s?39\d"],
                  [r"снижа|сниже|падени|падает|сокраща|сжима|уменьша|отрицательн"]],
    "baza":      [[r"\+?26([.,]\d)?"], [r"4[.,]1"], [r"2[.,]1"], [r"52[.,]9"]],
    "srednee":   [[r"2[.,](08|1)"], [r"0[.,]2"], [r"7[.,]9"], [r"2[45][.,]?\d*\s*%"]],
}


# Полоса должна быть пропорциональна числу. Отдельная проверка нужна там, где
# смысл разбора именно в разнице величин: если частная корреляция 0,07
# нарисована во всю ширину рядом с 0,93, страница говорит обратное тому,
# что показывает разбор.
# Значение по умолчанию ловит вырожденный случай «все полосы одинаковой длины»:
# так модель делала, когда забывала поделить на максимум. Там, где смысл разбора
# именно в разнице величин, порог жёстче.
BAR_RATIO_DEFAULT = 0.98
BAR_RATIO = {"prichina": 0.3, "srednee": 0.3}


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(directory, port=8799):
    handler = functools.partial(Quiet, directory=str(directory))
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def browser():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    o = Options()
    for a in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars"):
        o.add_argument(a)
    o.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    d = webdriver.Chrome(options=o)
    d.set_window_size(1280, 1000)
    return d


def verify(d, url, key):
    """Три условия: нет ошибок JS, есть непустой SVG, есть все ключевые числа."""
    d.get(url)
    time.sleep(4)
    # favicon.ico Chrome просит сам и пишет 404 уровнем SEVERE — к странице
    # это отношения не имеет и провалом считаться не должно.
    errs = [e["message"] for e in d.get_log("browser")
            if e["level"] == "SEVERE" and "favicon" not in e["message"]]
    bars = d.execute_script(
        "var b=document.querySelectorAll('.bar');var w=0;"
        "b.forEach(function(x){if(x.getBoundingClientRect().width>1)w++});"
        "return [b.length, w]")
    text = d.execute_script("return document.body.innerText") or ""
    missing = [alts[0] for alts in EXPECT[key]
               if not any(re.search(rx, text, re.I) for rx in alts)]
    # undefined и NaN на странице — признак того, что часть расчёта или подписей
    # не собралась; для участника это выглядит как сломанный отчёт.
    if re.search(r"\bundefined\b|\bNaN\b", text):
        missing.append("на странице есть undefined или NaN")
    widths = d.execute_script(
        "return Array.from(document.querySelectorAll('.bar'))"
        ".map(function(x){return x.getBoundingClientRect().width})"
        ".filter(function(w){return w>0})")
    ratio = (min(widths) / max(widths)) if widths else 1.0
    bar_ok = ratio <= BAR_RATIO.get(key, BAR_RATIO_DEFAULT)
    return {
        "js_errors": errs[:3],
        "bars": bars,
        "bar_ratio": round(ratio, 3),
        "bar_scale_ok": bar_ok,
        "missing_numbers": missing,
        "ok": not errs and bars[1] >= 3 and not missing and bar_ok,
        "text": text[:1500],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--attempts", type=int, default=4)
    ap.add_argument("--model", default="GigaChat-2-Max")
    ap.add_argument("--only", default="")
    a = ap.parse_args()

    REPORTS.mkdir(exist_ok=True)
    picked = [p for p in PRACTICES if not a.only or p["key"] in a.only.split(",")]
    srv = serve(ROOT)
    d = browser()
    log = {}
    try:
        for p in picked:
            prompt = rendered(p, "html")
            got = None
            for n in range(1, a.attempts + 1):
                try:
                    ans = gigachat.ask(prompt, model=a.model)
                except Exception as e:
                    print(f"  {p['key']:10} попытка {n}: ошибка API — {str(e)[:80]}", flush=True)
                    continue
                blocks = FENCE.findall(ans)
                html = blocks[0] if blocks else (ans if "<html" in ans.lower() else "")
                if not html.strip():
                    print(f"  {p['key']:10} попытка {n}: модель не вернула HTML", flush=True)
                    continue
                f = REPORTS / f"{p['slug']}.html"
                f.write_text(html, encoding="utf-8")
                v = verify(d, f"http://127.0.0.1:8799/reports/{f.name}", p["key"])
                v["attempt"], v["model"] = n, a.model
                print(f"  {p['key']:10} попытка {n}: "
                      f"{'ok' if v['ok'] else 'нет'} · полос {v['bars']} · "
                      f"ошибок JS {len(v['js_errors'])} · "
                      f"масштаб полос {'ok' if v.get('bar_scale_ok', True) else 'СБИТ'} · "
                      f"не нашлось чисел: {v['missing_numbers'] or '—'}", flush=True)
                (RUNS / "html").mkdir(parents=True, exist_ok=True)
                (RUNS / "html" / f"{p['slug']}_{n}.json").write_text(
                    json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
                # Неудачные версии тоже сохраняем: по ним видно, что именно
                # модель делает не так, и правится промпт, а не результат.
                (RUNS / "html" / f"{p['slug']}_{n}.html").write_text(html, encoding="utf-8")
                if v["ok"]:
                    got = v
                    break
                f.unlink(missing_ok=True)
            log[p["key"]] = got or {"ok": False}
            if not got:
                print(f"  {p['key']:10} НЕ СОБРАЛСЯ за {a.attempts} попыток", flush=True)
    finally:
        d.quit()
        srv.shutdown()

    (RUNS / "html_report.json").write_text(json.dumps(log, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
    good = sum(1 for v in log.values() if v.get("ok"))
    print(f"\nсобрано и проверено: {good} из {len(picked)}")


if __name__ == "__main__":
    main()
