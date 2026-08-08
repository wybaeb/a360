# -*- coding: utf-8 -*-
"""Датасеты для самостоятельной практики — те же ряды, что на живых демо кикоффа.

Данные в demos/*.html считаются в браузере детерминированным PRNG (mulberry32 +
Box-Muller). Здесь тот же генератор портирован на Python — 1:1, включая
32-битную арифметику Math.imul. Иначе числа в CSV разошлись бы с цифрами на
слайдах, и участник, повторяя разбор дома, получил бы «не тот» ответ.

Все данные синтетические.

Запуск: python3 build/gen_data.py
"""
import csv
import datetime as dt
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data"

M32 = 0xFFFFFFFF


def _imul(a, b):
    """Math.imul: младшие 32 бита произведения. Знак значения не имеет —
    дальше всё равно берутся только эти биты."""
    return (a * b) & M32


def rng(seed):
    """mulberry32 — тот же PRNG, что в demo_common.py (функция rng).

    Вся арифметика ведётся в беззнаковых 32 битах: у JS-версии операнды
    приводятся к int32, но набор битов от этого не меняется, а сдвиг >>> в JS
    работает как обычный >> над беззнаковым представлением.
    """
    state = [seed & M32]

    def nxt():
        a = (state[0] + 0x6D2B79F5) & M32
        state[0] = a
        t = _imul(a ^ (a >> 15), 1 | a)
        t = ((t + _imul(t ^ (t >> 7), 61 | t)) & M32) ^ t
        return ((t ^ (t >> 14)) & M32) / 4294967296.0

    return nxt


def nrm(r):
    """Box-Muller поверх rng — как функция nrm в demo_common.py."""
    def nxt():
        u = 0.0
        v = 0.0
        while not u:
            u = r()
        while not v:
            v = r()
        return math.sqrt(-2 * math.log(u)) * math.cos(2 * math.pi * v)
    return nxt


def jsday(d):
    """Date.getDay(): 0 — воскресенье."""
    return (d.weekday() + 1) % 7


def quant(a, q):
    s = sorted(a)
    i = (len(s) - 1) * q
    lo, hi = math.floor(i), math.ceil(i)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def write(name, header, rows):
    p = OUT / name
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  {name:28} {len(rows):>6} строк")
    return p


# ── 1. Выбросы: срок рассмотрения заявки, 90 дней ───────────────────────────
def demo1():
    r = rng(11)
    g = nrm(r)
    N = 90
    start = dt.date(2026, 5, 4)
    raw, dates = [], []
    for i in range(N):
        d = start + dt.timedelta(days=i)
        dates.append(d)
        wd = jsday(d)
        w = 3.4 if wd == 1 else 1.6 if wd == 5 else -2.4 if wd in (0, 6) else 0.0
        raw.append(41.2 + 0.013 * i + w + g() * 3.1)
    for k, v in {43: 296, 57: 388, 70: 441, 82: 512}.items():
        raw[k] = float(v)
    return write("loan_tat_90d.csv", ["date", "tat_min"],
                 [[d.isoformat(), round(v, 1)] for d, v in zip(dates, raw)])


# ── 2. Общая причина: обращения, отток, ошибки в приложении ─────────────────
def demo2():
    r = rng(23)
    g = nrm(r)
    N = 26
    start = dt.date(2026, 2, 2)
    rows = []
    for i in range(N):
        d = start + dt.timedelta(days=7 * i)
        wave = 4.2 + 15 * math.exp(-(((i - 17) / 4.2) ** 2))
        z = max(1.5, wave + g() * 1.1)
        x = 29 + 2.05 * z + g() * 6.2
        y = 2.05 + 0.135 * z + g() * 0.44
        rows.append([d.isoformat(), round(x, 1), round(y, 2), round(z, 2)])
    return write("weekly_ops_26w.csv",
                 ["week_start", "calls_th", "churn_pct", "app_error_rate_pct"], rows)


# ── 3. Сезонность: дневные выдачи потребкредитов, 3 года ────────────────────
def demo3():
    r = rng(5)
    g = nrm(r)
    N = 1095
    start = dt.date(2023, 1, 1)
    rows = []
    for i in range(N):
        d = start + dt.timedelta(days=i)
        doy = (d - dt.date(d.year, 1, 1)).days
        trend = 118 * (1 - 0.000165 * i)
        ann = 1 + 0.30 * math.cos(2 * math.pi * (doy - 344) / 365)
        dom = d.day
        mon = (1 + 0.34 * math.exp(-(((dom - 6) / 1.7) ** 2))
                 + 0.26 * math.exp(-(((dom - 21) / 1.7) ** 2)) - 0.09)
        wf = [0.52, 1.10, 1.13, 1.09, 1.06, 0.99, 0.71][jsday(d)]
        rows.append([d.isoformat(), round(trend * ann * mon * wf * (1 + g() * 0.055), 2)])
    return write("issues_daily_3y.csv", ["date", "amount_mln_rub"], rows)


# ── 4. Низкая база: рынок ипотеки ──────────────────────────────────────────
def demo4():
    banks = [("Мы", 142.0, 168.0), ("Банк А", 11.5, 17.5), ("Банк Б", 6.8, 10.9),
             ("Банк В", 58.0, 63.2), ("Прочие", 61.0, 58.0)]
    return write("mortgage_market.csv", ["bank", "was_bn_rub", "now_bn_rub"],
                 [[n, w, x] for n, w, x in banks])


# ── 5. Среднее против распределения: заявки МСБ за квартал ──────────────────
def demo5():
    r = rng(31)
    g = nrm(r)
    N = 18400
    t = []
    for _ in range(N):
        if r() < 0.71:
            t.append(math.exp(-1.9 + g() * 0.55))          # автоскоринг: часы
        else:
            t.append(max(0.6, 6.4 + g() * 3.0 + (7 * r() if r() < 0.12 else 0)))
    # Флаг выдачи в демо не считался из данных — конверсия по корзинам задана
    # как факт из отчёта. Здесь он материализован тем же PRNG, чтобы участник
    # мог посчитать конверсию сам и получить ровно те же 71/62/44/31 %.
    conv = [(0, 1, 0.71), (1, 3, 0.62), (3, 7, 0.44), (7, 1e9, 0.31)]
    r2 = rng(97)
    rows = []
    for i, v in enumerate(t, 1):
        p = next(c for lo, hi, c in conv if lo <= v < hi)
        rows.append([f"APP-{i:05d}", round(v, 3), int(r2() < p)])
    return write("msb_applications_q.csv", ["app_id", "tat_days", "issued"], rows)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    print("датасеты ->", OUT)
    for f in (demo1, demo2, demo3, demo4, demo5):
        f()

    # Самопроверка: цифры из CSV должны совпасть с цифрами на слайдах.
    import statistics as st
    tat = [float(row["tat_min"]) for row in csv.DictReader(open(OUT / "loan_tat_90d.csv"))]
    med = quant(tat, 0.5)
    mad = quant([abs(v - med) for v in tat], 0.5)
    out = [v for v in tat if abs(0.6745 * (v - med) / mad) > 3.5]
    clean = [v for v in tat if abs(0.6745 * (v - med) / mad) <= 3.5]
    print("\nсамопроверка демо 1: выбросов", len(out),
          "| сырое", f"{st.mean(tat[:30]):.1f}->{st.mean(tat[-30:]):.1f}",
          f"({st.mean(tat[-30:]) / st.mean(tat[:30]) * 100 - 100:+.0f} %)",
          "| очищенное", f"{st.mean(clean[:30]):.1f}->{st.mean(clean[-30:]):.1f}",
          f"({st.mean(clean[-30:]) / st.mean(clean[:30]) * 100 - 100:+.0f} %)")

    w = list(csv.DictReader(open(OUT / "weekly_ops_26w.csv")))
    calls = [float(x["calls_th"]) for x in w]
    churn = [float(x["churn_pct"]) for x in w]
    err = [float(x["app_error_rate_pct"]) for x in w]

    def corr(a, b):
        ma, mb = st.mean(a), st.mean(b)
        n = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        return n / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))

    rab, rac, rbc = corr(calls, churn), corr(err, calls), corr(err, churn)
    rp = (rab - rac * rbc) / math.sqrt((1 - rac ** 2) * (1 - rbc ** 2))
    print("самопроверка демо 2: r(обращения,отток)", f"{rab:.2f}",
          "| r(ошибки,обращения)", f"{rac:.2f}", "| r(ошибки,отток)", f"{rbc:.2f}",
          "| частная", f"{rp:.2f}")

    m = [float(x["tat_days"]) for x in csv.DictReader(open(OUT / "msb_applications_q.csv"))]
    print("самопроверка демо 5: среднее", f"{st.mean(m):.2f}", "| медиана",
          f"{quant(m, 0.5):.2f}", "| p90", f"{quant(m, 0.9):.1f}",
          "| >3 дней", f"{sum(v > 3 for v in m) / len(m) * 100:.0f} %")
