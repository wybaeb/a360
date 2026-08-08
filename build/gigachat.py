# -*- coding: utf-8 -*-
"""Минимальный клиент GigaChat API — только то, что нужно для проверки промптов.

Ключ авторизации берётся ТОЛЬКО из окружения (GIGACHAT_AUTH_KEY) и никуда
не печатается. Запуск:

    GIGACHAT_AUTH_KEY=$(secret get GIGA1_GIGACHAT_TOKEN) python3 build/check_prompts.py

verify=False: цепочка НУЦ Минцифры в контейнере не установлена, а тянуть
корневой сертификат внутрь репозитория ради проверки промптов незачем.
Через клиент не ходят ни персональные, ни клиентские данные — только учебные
синтетические выгрузки.
"""
import os
import ssl
import time
import uuid

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OAUTH = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
BASE = "https://gigachat.devices.sberbank.ru/api/v1"

_token = {"value": None, "exp": 0}


def token():
    if _token["value"] and time.time() < _token["exp"] - 60:
        return _token["value"]
    key = os.environ.get("GIGACHAT_AUTH_KEY")
    if not key:
        raise SystemExit("нет GIGACHAT_AUTH_KEY: запускать как "
                         "GIGACHAT_AUTH_KEY=$(secret get GIGA1_GIGACHAT_TOKEN) python3 ...")
    r = requests.post(OAUTH, headers={
        "Authorization": "Basic " + key,
        "RqUID": str(uuid.uuid4()),
        "Content-Type": "application/x-www-form-urlencoded",
    }, data={"scope": "GIGACHAT_API_PERS"}, verify=False, timeout=60)
    r.raise_for_status()
    d = r.json()
    _token["value"] = d["access_token"]
    _token["exp"] = d.get("expires_at", 0) / 1000 or time.time() + 1500
    return _token["value"]


def ask(prompt, model="GigaChat-2", retries=5, **kw):
    """Один вопрос — один ответ. Возвращает текст."""
    body = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    body.update(kw)
    last = None
    for i in range(retries):
        try:
            r = requests.post(f"{BASE}/chat/completions",
                              headers={"Authorization": "Bearer " + token(),
                                       "Content-Type": "application/json"},
                              json=body, verify=False, timeout=240)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            last = f"HTTP {r.status_code}: {r.text[:200]}"
            # 429 приходит на всплеске параллельных запросов — ждём дольше
            time.sleep((30 if r.status_code == 429 else 3) * (i + 1))
            continue
        except (requests.RequestException, ssl.SSLError) as e:
            last = repr(e)
        time.sleep(2 + 3 * i)
    raise RuntimeError(last)


def models():
    r = requests.get(f"{BASE}/models", headers={"Authorization": "Bearer " + token()},
                     verify=False, timeout=60)
    r.raise_for_status()
    return [m["id"] for m in r.json()["data"]]
