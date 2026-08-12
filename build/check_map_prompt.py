# -*- coding: utf-8 -*-
"""Прогон эталонов карты источников через промпт проверки (GigaChat API).

Зачем: эталон карты — демонстрационный артефакт. Если ассистент на нём выдаёт
разгром («критический разрыв», «введите Client Master Data»), эталон нельзя
показывать на занятии. Скрипт собирает промпт ровно так же, как страница
тренажёра (P_HEAD/PSEG вынимаются из сгенерированного JS, а не дублируются
здесь — иначе прогон проверял бы не то, что видит участник), гоняет выбранные
эталоны через модель и складывает сырые ответы в build/runs/map/.

Запуск:
    GIGACHAT_AUTH_KEY=$(secret get GIGA1_GIGACHAT_TOKEN) \\
        python3 build/check_map_prompt.py --tag base [--presets rko,churn]
"""
import argparse
import json
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gigachat
import trainer_map

OUT = pathlib.Path(__file__).resolve().parent / "runs" / "map"

# Представительная выборка: три кейса занятия + по одному из каждой группы
# (продукты — два, включая тот, на котором владелец получил разгром).
SAMPLE = ["case_product", "case_process", "case_master",
          "rko", "cc_util", "contact", "onboard", "churn", "portfolio"]


def _unesc(s):
    # P_HEAD/P_TAIL собраны конкатенацией строк — склеиваем обратно ("+")
    s = re.sub(r'"\s*\+\s*\n?\s*"', "", s)
    return (s.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\"))


def prompt_parts():
    """P_HEAD/P_TAIL/PSEG — из тела страницы, чтобы прогон совпадал с тренажёром."""
    js = trainer_map.BODY
    head = _unesc(re.search(r'var P_HEAD="(.*?)";', js, re.S).group(1))
    tail = _unesc(re.search(r'var P_TAIL="(.*?)";', js, re.S).group(1))
    seg_src = re.search(r"var PSEG=\[(.*?)\];", js, re.S).group(1)
    segs = []
    for m in re.finditer(r'\{t:P_HEAD\}|\{t:P_TAIL\}|\{t:"(.*?)"\}|\{k:"(\w+)"\}',
                         seg_src, re.S):
        if m.group(0) == "{t:P_HEAD}":
            segs.append(("t", head))
        elif m.group(0) == "{t:P_TAIL}":
            segs.append(("t", tail))
        elif m.group(1) is not None:
            segs.append(("t", _unesc(m.group(1))))
        else:
            segs.append(("k", m.group(2)))
    return segs


def values(p):
    """Ровно те же строки, что собирает promptVals() на странице."""
    m = p["master"]
    return {
        "q": p["q"],
        "metrics": "\n".join(
            "- %s · %s · %s · наблюдаем %s" % (r[0], r[1], r[2], r[3]) for r in p["metrics"]),
        "sources": "\n".join(
            "- %s · даёт: %s · владелец: %s · обновление: %s · доверие: %s" % tuple(r)
            for r in p["sources"]),
        "quality": "\n".join("- %s: %s" % (r[0], r[1]) for r in p["quality"]),
        "master": ("показатель «%s»; источник A: %s → %s; источник B: %s → %s; выбор: %s"
                   % (m["ind"], m["a"], m["av"], m["b"], m["bv"], m["choice"])),
        "actions": "\n".join("- %s — %s, срок: %s" % tuple(r) for r in p["actions"]),
    }


def build(key):
    p = trainer_map.EPRESETS[key]
    v = values(p)
    return "".join(s if kind == "t" else v[s] for kind, s in prompt_parts())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="run", help="метка прогона (папка внутри runs/map)")
    ap.add_argument("--presets", default="", help="список ключей через запятую")
    ap.add_argument("--model", default="GigaChat-2-Max")
    ap.add_argument("--dry", action="store_true", help="только собрать промпты, без API")
    a = ap.parse_args()
    keys = [k.strip() for k in a.presets.split(",") if k.strip()] or SAMPLE
    d = OUT / a.tag
    d.mkdir(parents=True, exist_ok=True)
    meta = []
    for k in keys:
        pr = build(k)
        (d / (k + "_prompt.md")).write_text(pr, encoding="utf-8")
        if a.dry:
            print(k, len(pr), "симв.")
            continue
        t0 = time.time()
        try:
            ans = gigachat.ask(pr, model=a.model)
            err = None
        except Exception as e:  # noqa: BLE001 — сырой прогон, важен сам факт отказа
            ans, err = "", repr(e)
        (d / (k + ".md")).write_text(ans or ("ОШИБКА: " + str(err)), encoding="utf-8")
        meta.append({"preset": k, "model": a.model, "chars_prompt": len(pr),
                     "chars_answer": len(ans), "sec": round(time.time() - t0, 1),
                     "error": err})
        print("%-14s %5d симв. ответа  %5.1f с  %s" % (k, len(ans), time.time() - t0, err or ""))
    if meta:
        (d / "_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                                      encoding="utf-8")


if __name__ == "__main__":
    main()
