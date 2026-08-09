# -*- coding: utf-8 -*-
"""HTML-обработчики датасетов: генерация в GigaChat и проверка в настоящем браузере.

Промпт «html» просит модель написать самодостаточную страницу: она подключает
соседний файл выгрузки тегом <script src="…​.js">, считает проверку и рисует
результат. Проверка здесь не формальная — страница открывается в headless Chrome
прямо с диска, по file://, то есть ровно так, как её откроет участник, и
проверяется на пять вещей:

  1. в консоли нет ошибок JavaScript;
  2. график нарисован: в svg есть фигуры и он имеет ненулевую ширину;
  3. в атрибутах svg нет NaN, undefined и Infinity — от них фигуры молча исчезают;
  4. полосы нарисованы и их длина пропорциональна числам;
  5. в тексте страницы есть все ключевые числа разбора — те же, что на слайдах.

Проходит только та версия, которая выполнила все условия. Её и кладём
в reports/ — участник открывает готовую ссылку, а не «пример кода».

Запуск:
    GIGACHAT_AUTH_KEY=$(secret get GIGA1_GIGACHAT_TOKEN) \
        python3 build/check_reports.py [--attempts 4] [--model GigaChat-2-Max] [--only baza]
"""
import argparse
import json
import pathlib
import re
import sys
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
                  [r"38\s?0[56]\d"], [r"33\s?39\d"]],
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

# Отдельно проверяем текст под заголовком «Вывод». Числа страница считает верно,
# а вот итоговую фразу пишет модель — и она регулярно противоречит собственным
# числам: «срок рассмотрения увеличился» при +3,8 % после очистки, «объёмы
# стабильны» при −6,8 % год к году. Такую страницу публиковать нельзя.
CONCLUSION = {
    "vybrosy": r"не замедл|замедления нет|значимых изменений нет|не подтвержда|"
               r"в пределах|выброс|аномал|инцидент|сбо",
    "sezonnost": r"снижа|сниже|падени|падает|сокраща|сжима|уменьша|отрицательн",
    "baza": r"низк\w+ баз|эффект баз|небольш\w+ баз|мал\w+ баз|сильнее всех|"
            r"больше всех|наибольш\w+ прирост|2[.,]1\s*п",
}


def browser():
    """Chrome со своим профилем на диске: в /tmp контейнера места мало, а без
    свободного места рендерер падает с «Unable to receive message from renderer»."""
    import tempfile
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    o = Options()
    tmp = pathlib.Path("/root/work/.chrometmp")
    tmp.mkdir(parents=True, exist_ok=True)
    profile = tempfile.mkdtemp(dir=str(tmp))
    for a in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars",
              f"--user-data-dir={profile}", f"--disk-cache-dir={profile}/cache",
              "--disable-gpu"):
        o.add_argument(a)
    o.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    d = webdriver.Chrome(options=o)
    d.set_window_size(1280, 1000)
    return d


def verify(d, url, key):
    """Условия приёмки: нет ошибок JS, график и полосы нарисованы, числа сошлись."""
    d.get(url)
    time.sleep(4)
    # Атрибуты svg — самое хрупкое место: NaN в points или width не даёт ошибки
    # в консоли, элемент просто не рисуется. Поэтому смотрим их отдельно.
    svg_bad = d.execute_script(
        "var bad=[];"
        "document.querySelectorAll('svg *').forEach(function(e){"
        " for(var i=0;i<e.attributes.length;i++){var a=e.attributes[i];"
        "  if(/NaN|undefined|Infinity/.test(a.value))"
        "   bad.push(e.tagName+'@'+a.name+'='+a.value.slice(0,40));}});"
        "return bad.slice(0,5)")
    marks = d.execute_script(
        "return document.querySelectorAll("
        "'svg polyline,svg rect,svg circle,svg path,svg line').length")
    svg_w = d.execute_script(
        "var s=document.querySelector('svg');"
        "return s? Math.round(s.getBoundingClientRect().width):0")
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
    # Плитка, где осталась одна единица измерения без числа: значение прогнали
    # через форматирование чисел строкой и получили пустоту. Выглядит как
    # «%» или «п.п.» отдельной строкой.
    orphan = re.findall(r"(?m)^\s*(%|п\.\s?п\.|млрд ₽|мин\.?)\s*$", text)
    if orphan:
        missing.append(f"плитки без числа: {orphan[:3]}")
    tail = text.rsplit("Вывод", 1)[-1]
    if key in CONCLUSION and not re.search(CONCLUSION[key], tail, re.I):
        missing.append("вывод противоречит числам разбора")
    # У каждой полосы обязаны быть своя подпись и своё число. Модель повторяет
    # одну и ту же ошибку: ищет .val не внутри строки, а в родительской карточке —
    # тогда все значения пишутся в одну ячейку, а три полосы остаются пустыми.
    blank = d.execute_script(
        "var n=0;document.querySelectorAll('.row').forEach(function(r){"
        " var v=r.querySelector('.val'), l=r.querySelector('.lab');"
        " if(!v||!v.textContent.trim()||!l||!l.textContent.trim())n++});"
        "return n")
    if blank:
        missing.append(f"полос без подписи или числа: {blank}")
    # Пустая первая колонка таблицы — след той же ошибки: даты и названия
    # прогоняются через форматирование чисел и превращаются в пустые ячейки.
    empty_cells = d.execute_script(
        "var n=0;document.querySelectorAll('tbody tr, table tr').forEach(function(r){"
        " var c=r.querySelector('td'); if(c && !c.textContent.trim())n++});"
        "return n")
    if empty_cells:
        missing.append(f"строк таблицы с пустой первой ячейкой: {empty_cells}")
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
        "svg_marks": marks,
        "svg_width": svg_w,
        "svg_bad_attrs": svg_bad,
        "missing_numbers": missing,
        "ok": (not errs and bars[1] >= 3 and not missing and bar_ok
               and marks >= 8 and svg_w > 300 and not svg_bad),
        "text": text[:1500],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--attempts", type=int, default=4)
    ap.add_argument("--model", default="GigaChat-2-Max")
    ap.add_argument("--only", default="")
    ap.add_argument("--verify-only", action="store_true",
                    help="ничего не запрашивать у модели: перепроверить то, "
                         "что уже лежит в reports/")
    a = ap.parse_args()

    if a.verify_only:
        d = browser()
        try:
            for p in [x for x in PRACTICES if not a.only or x["key"] in a.only.split(",")]:
                f = REPORTS / f"{p['slug']}.html"
                if not f.exists():
                    print(f"  {p['key']:10} страницы нет", flush=True)
                    continue
                v = verify(d, f.resolve().as_uri(), p["key"])
                print(f"  {p['key']:10} {'ok' if v['ok'] else 'НЕ ПРОХОДИТ'} · "
                      f"полос {v['bars']} · фигур в svg {v['svg_marks']} "
                      f"шириной {v['svg_width']} · ошибок JS {len(v['js_errors'])} · "
                      f"замечания: {v['missing_numbers'] or '—'}", flush=True)
        finally:
            d.quit()
        return

    REPORTS.mkdir(exist_ok=True)
    picked = [p for p in PRACTICES if not a.only or p["key"] in a.only.split(",")]
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
                # Открываем ровно так, как это сделает участник: файл с диска,
                # выгрузка соседним <script src>. Если страница работает по
                # file://, то на Pages по http она работает тем более.
                try:
                    v = verify(d, f.resolve().as_uri(), p["key"])
                except Exception as e:      # упавший рендерер не должен ронять прогон
                    print(f"  {p['key']:10} попытка {n}: браузер упал ({str(e)[:60]}), "
                          f"перезапускаю", flush=True)
                    try:
                        d.quit()
                    except Exception:
                        pass
                    d = browser()
                    v = verify(d, f.resolve().as_uri(), p["key"])
                v["attempt"], v["model"] = n, a.model
                print(f"  {p['key']:10} попытка {n}: "
                      f"{'ok' if v['ok'] else 'нет'} · полос {v['bars']} · "
                      f"фигур в svg {v['svg_marks']} шириной {v['svg_width']} · "
                      f"ошибок JS {len(v['js_errors'])} · "
                      f"масштаб полос {'ok' if v.get('bar_scale_ok', True) else 'СБИТ'} · "
                      f"мусор в svg: {v['svg_bad_attrs'] or '—'} · "
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
            # Результат по каждому разбору сразу кладём отдельным файлом: так пять
            # разборов можно гнать параллельно, не затирая общий отчёт.
            (RUNS / "html" / f"{p['key']}_result.json").write_text(
                json.dumps(log[p["key"]], ensure_ascii=False, indent=1), encoding="utf-8")
            if not got:
                print(f"  {p['key']:10} НЕ СОБРАЛСЯ за {a.attempts} попыток", flush=True)
    finally:
        d.quit()

    # Общий отчёт собираем из отдельных файлов — чтобы параллельные запуски
    # по разным разборам складывались, а не затирали друг друга.
    full = {}
    for p in PRACTICES:
        f = RUNS / "html" / f"{p['key']}_result.json"
        if f.exists():
            full[p["key"]] = json.loads(f.read_text(encoding="utf-8"))
    (RUNS / "html_report.json").write_text(json.dumps(full, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
    good = sum(1 for v in log.values() if v.get("ok"))
    print(f"\nсобрано и проверено: {good} из {len(picked)}")


if __name__ == "__main__":
    main()
