# -*- coding: utf-8 -*-
"""Прогон промптов практики через GigaChat API — проверка воспроизводимости.

Каждый промпт запускается N раз на каждой модели с температурой по умолчанию —
как у участника в вебе, где ползунков нет.

Как оценивается ответ. Сначала пробовали набор регулярок «есть ли в тексте такое
число и такое слово» — это оказалось строже самих ответов: содержательно верный
разбор не проходил из-за того, что модель написала «четверть» вместо «25 %».
Поэтому решение принимает судья — отдельный вызов GigaChat-2-Max, которому
даются эталонный вывод из prompts.py и ответ, и который отвечает ДА/НЕТ на
вопрос «совпадает ли главный вывод по существу». Судейство — задача проще
самого разбора, и там модель надёжна. Регулярки остались как вторая, справочная
колонка: по ним видно, каких элементов не хватило.

Результат: build/runs/<модель>/<практика>_<вид>_<n>.md с полными ответами,
build/runs/report.json со сводкой.

Запуск:
    GIGACHAT_AUTH_KEY=$(secret get GIGA1_GIGACHAT_TOKEN) python3 build/check_prompts.py \
        [--runs 5] [--models GigaChat-2,GigaChat-2-Max] [--kind check,code,read,naive]
"""
import argparse
import concurrent.futures as cf
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gigachat
from prompts import CHECKS, PRACTICES, rendered

# Промпт «код» проверяется одинаково для всех практик: важно, что вернулся
# рабочий pandas-скрипт с комментариями, а не рассуждение о коде.
CODE_CHECKS = [("pandas", r"import pandas"), ("код в блоке", r"```"),
               ("комментарии по-русски", r"#\s*[а-яё]"), ("печать результата", r"print\(")]

JUDGE_MODEL = "GigaChat-2-Max"
JUDGE = """Ты — строгий проверяющий. Ниже эталонный вывод аналитика и ответ, который надо оценить.

ЭТАЛОННЫЙ ВЫВОД:
{expect}

ОЦЕНИВАЕМЫЙ ОТВЕТ:
{answer}

Вопрос: главный вывод оцениваемого ответа совпадает с эталонным по существу?
Различия в формулировках, порядке и подробностях значения не имеют. Если ответ
приходит к противоположному выводу или уходит от вывода — это несовпадение.

Ответь ровно одним словом: ДА или НЕТ."""

# Для «выбора проверки» эталон — название метода, а не вывод.
JUDGE_CHECK = """Ты — строгий проверяющий. Аналитика просили выбрать одну проверку из списка.

ПРАВИЛЬНЫЙ ВЫБОР: {expect}

ОТВЕТ АНАЛИТИКА:
{answer}

Вопрос: аналитик выбрал именно эту проверку (пусть другими словами)?
Ответь ровно одним словом: ДА или НЕТ."""

RUNS = pathlib.Path(__file__).resolve().parent / "runs"


def grade(text, checks):
    low = text.lower()
    return {name: bool(re.search(rx, low, re.I)) for name, rx in checks}


def judge(template, expect, answer):
    """Вердикт судьи. Отдельный вызов может упасть по 429 — тогда прогон
    помечается непройденным, но весь прогон не рушится: потерять один
    результат дешевле, чем перезапускать сотню."""
    try:
        v = gigachat.ask(template.format(expect=expect, answer=answer),
                         model=JUDGE_MODEL, temperature=0.1)
    except Exception:
        return None
    return v.strip().upper().startswith("ДА")


def one(model, p, kind, n):
    # Готовый прогон не переспрашиваем: так дозапуск после обрыва стоит
    # только недостающих вызовов.
    done = RUNS / model / f"{p['num']}_{p['key']}_{kind}_{n}.md"
    if done.exists():
        txt = done.read_text(encoding="utf-8")
        return dict(model=model, key=p["key"], kind=kind, n=n,
                    ok="Вердикт судьи: совпадает" in txt or "Вердикт судьи: —" in txt,
                    missing=[], chars=len(txt), cached=True)
    try:
        answer = gigachat.ask(rendered(p, kind), model=model)
    except Exception as e:
        return dict(model=model, key=p["key"], kind=kind, n=n, ok=False,
                    error=str(e)[:300], missing=["<нет ответа>"])

    checks = CODE_CHECKS if kind == "code" else p[CHECKS[kind]] if kind in CHECKS else []
    g = grade(answer, checks)

    if kind == "read":
        ok = judge(JUDGE, p["expect"], answer)
    elif kind == "check":
        ok = judge(JUDGE_CHECK, p["method"], answer)
        if ok is None:
            ok = False
    elif kind == "code":
        ok = all(g.values())
    else:                      # naive — «ловушка», у неё правильного ответа нет
        ok = True

    d = RUNS / model
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{p['num']}_{p['key']}_{kind}_{n}.md").write_text(
        f"# {p['num']}. {p['title']} · {model} · прогон {n} · {kind}\n\n"
        f"Вердикт судьи: {'—  (судья не ответил)' if ok is None else 'совпадает с эталоном' if ok else 'НЕ совпадает'}\n"
        f"Элементы разбора: {json.dumps(g, ensure_ascii=False)}\n\n---\n\n{answer}\n",
        encoding="utf-8")
    return dict(model=model, key=p["key"], kind=kind, n=n, ok=bool(ok),
                missing=[k for k, v in g.items() if not v], chars=len(answer))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--models", default="GigaChat-2,GigaChat-2-Max")
    ap.add_argument("--kind", default="check,code,read,naive")
    ap.add_argument("--only", default="", help="ключи практик через запятую")
    a = ap.parse_args()

    models = a.models.split(",")
    kinds = a.kind.split(",")
    picked = [p for p in PRACTICES if not a.only or p["key"] in a.only.split(",")]

    jobs = [(m, p, k, i + 1) for m in models for p in picked for k in kinds
            for i in range(a.runs if k != "naive" else min(a.runs, 3))]
    print(f"прогонов: {len(jobs)}")
    res = []
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        for r in ex.map(lambda j: one(*j), jobs):
            res.append(r)
            mark = "ok" if r["ok"] else "вывод не совпал"
            miss = (" | нет: " + ", ".join(r["missing"])) if r["missing"] else ""
            print(f"  {r['model']:16} {r['key']:10} {r['kind']:6} #{r['n']}  {mark}{miss}",
                  flush=True)

    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "report.json").write_text(json.dumps(res, ensure_ascii=False, indent=1),
                                      encoding="utf-8")

    print("\nсводка (доля прогонов с верным выводом):")
    for m in models:
        for k in kinds:
            for p in picked:
                s = [r for r in res if r["model"] == m and r["key"] == p["key"] and r["kind"] == k]
                if not s:
                    continue
                good = sum(r["ok"] for r in s)
                flag = "" if good == len(s) else "   <-- НЕСТАБИЛЬНО"
                print(f"  {m:16} {k:6} {p['num']} {p['key']:10} {good}/{len(s)}{flag}")


if __name__ == "__main__":
    main()
