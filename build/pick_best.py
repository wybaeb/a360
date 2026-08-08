# -*- coding: utf-8 -*-
"""Выбор образцового ответа GigaChat для каждой практики -> build/runs/best.json.

На страницу практики попадает настоящий ответ модели с прогона, а не написанный
нами «правильный» образец: иначе участник сравнивал бы свой результат с текстом,
которого модель никогда не выдавала.

Правило выбора: берём прогон, который судья засчитал, с более сильной модели;
из засчитанных — самый короткий, чтобы страница не превращалась в простыню.

Запуск: python3 build/pick_best.py
"""
import html
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from prompts import PRACTICES

RUNS = pathlib.Path(__file__).resolve().parent / "runs"
LIMIT = 2200          # знаков; длиннее — обрезаем по границе абзаца
PREFER = "GigaChat-2-Max"


def to_html(md):
    """Минимальная разметка: у ответов встречаются только заголовки, жирный,
    списки и абзацы. Полноценный markdown-парсер здесь был бы лишней зависимостью."""
    out, lst = [], False
    for raw in md.split("\n"):
        line = html.escape(raw.strip())
        line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
        line = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", line)
        # Пустые строки и markdown-разделители («---») закрывают список
        # и дальше не выводятся: на странице они читались бы как мусор.
        if not line or re.fullmatch(r"[-–—*_]{3,}", line):
            if lst:
                out.append("</ul>")
                lst = False
            continue
        if re.match(r"^#{1,6}\s", line):
            if lst:
                out.append("</ul>")
                lst = False
            out.append("<h4>" + re.sub(r"^#{1,6}\s*", "", line) + "</h4>")
        elif re.match(r"^[-–—•]\s", line):
            if not lst:
                out.append("<ul>")
                lst = True
            out.append("<li>" + re.sub(r"^[-–—•]\s*", "", line) + "</li>")
        else:
            if lst:
                out.append("</ul>")
                lst = False
            out.append("<p>" + line + "</p>")
    if lst:
        out.append("</ul>")
    return "".join(out)


def trim(md):
    if len(md) <= LIMIT:
        return md, False
    cut = md[:LIMIT]
    i = cut.rfind("\n\n")
    return (cut[:i] if i > LIMIT // 2 else cut).rstrip(), True


def main():
    rep = json.loads((RUNS / "report.json").read_text(encoding="utf-8"))
    best = {}
    for p in PRACTICES:
        cands = [r for r in rep if r["key"] == p["key"] and r["kind"] == "read" and r["ok"]]
        if not cands:
            print(f"  {p['key']}: засчитанных прогонов нет — пример не ставим")
            continue
        cands.sort(key=lambda r: (r["model"] != PREFER, r["chars"]))
        r = cands[0]
        f = RUNS / r["model"] / f"{p['num']}_{p['key']}_read_{r['n']}.md"
        md = f.read_text(encoding="utf-8").split("---\n", 1)[1].strip()
        md, cut = trim(md)
        body = to_html(md)
        if cut:
            body += '<p class="sub" style="margin:0">…ответ приведён с сокращением.</p>'
        best[p["key"]] = {"model": r["model"], "n": r["n"], "answer": body}
        print(f"  {p['key']:10} {r['model']:16} прогон {r['n']}, {r['chars']} знаков"
              f"{' (сокращён)' if cut else ''}")
    (RUNS / "best.json").write_text(json.dumps(best, ensure_ascii=False, indent=1),
                                    encoding="utf-8")


if __name__ == "__main__":
    main()
