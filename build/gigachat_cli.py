# -*- coding: utf-8 -*-
"""Один вопрос ассистенту из командной строки: промпт — со stdin, ответ — в stdout.

Нужен прогону цепочки сквозной практики (check_project_chain.cjs), который
живёт на node, чтобы разбирать ответы тем же кодом, что и страница.
Ключ — только из окружения, как в gigachat.py:
    GIGACHAT_AUTH_KEY=$(secret get GIGA1_GIGACHAT_TOKEN) python3 build/gigachat_cli.py GigaChat-2 < prompt.txt
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gigachat  # noqa: E402

model = sys.argv[1] if len(sys.argv) > 1 else "GigaChat-2"
prompt = sys.stdin.read()
sys.stdout.write(gigachat.ask(prompt, model=model))
