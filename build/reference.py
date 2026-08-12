# -*- coding: utf-8 -*-
"""Эталонные ответы по пяти датасетам — на них проверяются ответы GigaChat.

Считаются из тех же CSV, что скачивает участник. Числа отсюда попадают
и на страницу практики («что должно получиться»), и в проверку промптов
(check_prompts.py), поэтому расхождение слайдов и практики исключено.

Запуск: python3 build/reference.py
"""
import csv
import math
import pathlib
import statistics as st

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"


def rows(name):
    with (DATA / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def quant(a, q):
    s = sorted(a)
    i = (len(s) - 1) * q
    lo, hi = math.floor(i), math.ceil(i)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def corr(a, b):
    ma, mb = st.mean(a), st.mean(b)
    n = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    return n / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))


def slope(y):
    n = len(y)
    sx = sum(range(n))
    sy = sum(y)
    sxx = sum(i * i for i in range(n))
    sxy = sum(i * v for i, v in enumerate(y))
    b = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    return b, (sy - b * sx) / n


def d1():
    tat = [float(r["tat_min"]) for r in rows("loan_tat_90d.csv")]
    dates = [r["date"] for r in rows("loan_tat_90d.csv")]
    med = quant(tat, 0.5)
    mad = quant([abs(v - med) for v in tat], 0.5)
    rz = [0.6745 * (v - med) / mad for v in tat]
    out = [d for d, z in zip(dates, rz) if abs(z) > 3.5]
    clean = [v for v, z in zip(tat, rz) if abs(z) <= 3.5]
    return {
        "наивный рост, %": round((st.mean(tat[-30:]) / st.mean(tat[:30]) - 1) * 100),
        "медиана, мин": round(med, 1),
        "порог выброса, мин": round(med + 3.5 * mad / 0.6745, 1),
        "выбросов": len(out),
        "даты выбросов": out,
        "рост после очистки, %": round((st.mean(clean[-30:]) / st.mean(clean[:30]) - 1) * 100),
    }


def d2():
    w = rows("weekly_ops_26w.csv")
    calls = [float(x["calls_th"]) for x in w]
    churn = [float(x["churn_pct"]) for x in w]
    err = [float(x["app_error_rate_pct"]) for x in w]
    rab, rac, rbc = corr(calls, churn), corr(err, calls), corr(err, churn)
    return {
        "r(обращения, отток)": round(rab, 2),
        "r(ошибки, обращения)": round(rac, 2),
        "r(ошибки, отток)": round(rbc, 2),
        "частная r при фикс. ошибках": round(
            (rab - rac * rbc) / math.sqrt((1 - rac ** 2) * (1 - rbc ** 2)), 2),
    }


def d3():
    import datetime as dt
    r = rows("issues_daily_3y.csv")
    y = [float(x["amount_mln_rub"]) for x in r]
    d = [dt.date.fromisoformat(x["date"]) for x in r]
    n = len(y)

    def cma(a, w):
        h = (w - 1) // 2
        return [None if i < h or i >= len(a) - h else sum(a[i - h:i + h + 1]) / w
                for i in range(len(a))]

    def prof(a, w, key):
        m = cma(a, w)
        b = {}
        for i, v in enumerate(a):
            if m[i] is None:
                continue
            b.setdefault(key(d[i]), []).append(v / m[i])
        f = {k: quant(v, 0.5) for k, v in b.items()}
        mu = st.mean(f.values())
        return {k: v / mu for k, v in f.items()}

    jsday = lambda x: (x.weekday() + 1) % 7
    wk = prof(y, 7, jsday)
    y1 = [v / wk[jsday(d[i])] for i, v in enumerate(y)]
    yr = prof(y1, 365, lambda x: x.month - 1)
    y2 = [v / yr[d[i].month - 1] for i, v in enumerate(y1)]
    mn = prof(y2, 31, lambda x: x.day)
    adj = [v / mn[d[i].day] for i, v in enumerate(y2)]

    # Эталон для участника — суммы за календарные кварталы: так считает готовый
    # отчёт по этой выгрузке, лонгрид «Пять ошибок вывода» и демо-разбор.
    qs, ys = {}, {}
    for date, v in zip(d, y):
        qs[(date.year, (date.month - 1) // 3 + 1)] = \
            qs.get((date.year, (date.month - 1) // 3 + 1), 0.0) + v
        ys[date.year] = ys.get(date.year, 0.0) + v
    (yl, ql), (yp, qp) = sorted(qs)[-1], sorted(qs)[-2]
    qoq = qs[(yl, ql)] / qs[(yp, qp)] - 1
    yoy = qs[(yl, ql)] / qs[(yl - 1, ql)] - 1
    years = sorted(ys)

    # Вспомогательный вариант: то же сравнение скользящим окном 92/91 дня по
    # средним значениям. Граница окна не совпадает с границей квартала, поэтому
    # число получается другим (+39 вместо +36) — на слайды и в отчёты идёт
    # только календарный вариант выше.
    win = st.mean(y[n - 92:]) / st.mean(y[n - 183:n - 92]) - 1

    b, a = slope(adj)
    b12, a12 = slope(adj[n - 365:])
    return {
        "IV кв. к III кв., календарные кварталы по суммам, % (эталон)": round(qoq * 100, 2),
        "IV кв. к IV кв. прошлого года, %": round(yoy * 100, 2),
        "годовые итоги, млн ₽": {str(k): round(ys[k], 1) for k in years},
        "год к году, %": {f"{years[i]} к {years[i - 1]}":
                          round((ys[years[i]] / ys[years[i - 1]] - 1) * 100, 1)
                          for i in range(1, len(years))},
        "то же скользящим окном 92/91 дн. по средним, % (не эталон)": round(win * 100, 2),
        "тренд за 3 года, очищенный ряд, %": round(b * (n - 1) / a * 100),
        "тренд за 12 мес., %": round(b12 * 364 / a12 * 100),
        "воскресенье к вторнику": round(wk[0] / wk[2], 2),
    }


def d4():
    b = rows("mortgage_market.csv")
    was = {x["bank"]: float(x["was_bn_rub"]) for x in b}
    now = {x["bank"]: float(x["now_bn_rub"]) for x in b}
    sw, sn = sum(was.values()), sum(now.values())
    return {
        "темп прироста, %": {k: round((now[k] / was[k] - 1) * 100) for k in was},
        "прирост, млрд ₽": {k: round(now[k] - was[k], 1) for k in was},
        "доля рынка, п.п.": {k: round(now[k] / sn * 100 - was[k] / sw * 100, 1) for k in was},
    }


def d5():
    m = rows("msb_applications_q.csv")
    t = [float(x["tat_days"]) for x in m]
    iss = [int(x["issued"]) for x in m]
    buckets = [("<1 дн", 0, 1), ("1–3 дн", 1, 3), ("3–7 дн", 3, 7), (">7 дн", 7, 1e9)]
    conv = {}
    for name, lo, hi in buckets:
        sel = [i for i, v in zip(iss, t) if lo <= v < hi]
        conv[name] = (len(sel), round(st.mean(sel) * 100))
    return {
        "среднее, дней": round(st.mean(t), 2),
        "медиана, дней": round(quant(t, 0.5), 2),
        "p90, дней": round(quant(t, 0.9), 1),
        "доля > 3 дней, %": round(sum(v > 3 for v in t) / len(t) * 100),
        "конверсия по корзинам (n, %)": conv,
    }


ALL = {"1 · выбросы": d1, "2 · общая причина": d2, "3 · сезонность": d3,
       "4 · низкая база": d4, "5 · среднее": d5}

if __name__ == "__main__":
    import json
    for k, f in ALL.items():
        print(k)
        print(json.dumps(f(), ensure_ascii=False, indent=2))
        print()
