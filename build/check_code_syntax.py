# -*- coding: utf-8 -*-
"""Дополнительная проверка промпта «код»: разбирается ли выданный скрипт Python-ом.

Регулярки в check_prompts.py отвечают только на вопрос «код вообще пришёл».
Синтаксически битый скрипт они бы пропустили, а участник получил бы ошибку
при первом же запуске. Здесь из каждого ответа вынимается блок кода и
прогоняется через ast.parse — это не запуск (данные у всех разные), но
синтаксис и отступы проверяются полностью.

Запуск: python3 build/check_code_syntax.py
"""
import ast
import pathlib
import re

RUNS = pathlib.Path(__file__).resolve().parent / "runs"
FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S)


def blocks(md):
    found = FENCE.findall(md)
    if found:
        return found
    # Ответ без ограждения: берём всё от первого import до конца.
    i = md.find("import ")
    return [md[i:]] if i >= 0 else []


def main():
    ok = bad = empty = 0
    for f in sorted(RUNS.glob("*/[1-5]_*_code_*.md")):
        body = f.read_text(encoding="utf-8").split("---\n", 1)[-1]
        b = blocks(body)
        if not b:
            empty += 1
            print("  нет кода:", f.parent.name, f.name)
            continue
        try:
            ast.parse("\n".join(b))
            ok += 1
        except SyntaxError as e:
            bad += 1
            print(f"  синтаксис: {f.parent.name} {f.name} — строка {e.lineno}: {e.msg}")
    print(f"\nразбирается Python-ом: {ok} из {ok + bad + empty}"
          f"{f', с ошибкой: {bad}' if bad else ''}{f', без кода: {empty}' if empty else ''}")
    return ok, bad, empty


if __name__ == "__main__":
    main()
