# -*- coding: utf-8 -*-
"""Лонгрид-справочник «Метрики и качество данных».

Справочная страница курса: сюда ведут кнопки «?» тренажёров (якорь #m-<id>
у каждой метрики) и кнопка «i» замера эффективности (#eco).

Принцип страницы (правка владельца от 12.08): на слайдах — выжимка, здесь —
полное детальное изложение. По каждой метрике справочника даётся формула
расчёта, источник данных в банке, управленческое применение и стандартная
методика с типовыми оговорками; длинные выкладки убраны под расхлоп
(<details class="more">), короткие идут прямо в тексте. Названия метрик —
общепринятые в российских банках и сквозные для всех артефактов курса
(слайды, тренажёры, справочник): TAT, STP, SLA, NPS, CSAT, CAC, LTV, ARPU,
Churn, ROI, NPV, TCO, TTE.

Определения метрик — из единого источника metrics_data.py (того же, что
собирает тренажёр «Дерево метрик»): краткая часть карточки и подсказка
в тренажёре не расходятся. Развёрнутая часть (формула, источник, методика)
живёт здесь, в словаре DETAIL.

Опора текста — «Менеджмент цифрового продукта» (Я. Шуваев): классификация
метрик (качество опыта / управленческий учёт / инвестиционные), опережающие
и запаздывающие, денежный поток, дисконтирование и NPV, точки прибыльности
и окупаемости, финансовая модель портфеля инициатив. Пересказ своими словами, без
прямого цитирования (договор с издателем).

Иллюстрации: готовые SVG слайдов деки Шага 1 (decks/step1_data_landscape.json)
переносятся в текст как есть — участник видит в справочнике ту же картинку,
что была на встрече; модели графиков review_r4 (fig_npv2, fig_ci_real,
fig_accum2, fig_tradeoff, fig_cod2, fig_portfolio) воспроизведены здесь
инлайновым SVG теми же формулами, что и PNG слайдов, — с укрупнёнными
подписями под чтение с телефона.
"""
import json as _json
import math as _math
import os as _os

from metrics_data import M, metric
from sources import SOURCES_METRICS, ref_metrics
from longread_figs import (fig, npv_curve,
                           _txt, _plate, _poly, _svg, _axes, DARK, ACC, DEEP, WARN)

READ_MIN = 35

# ── Переиспользование готовых слайдов деки Шага 1 ───────────────────────────
_DECK_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                           "..", "..", "kk_sber_a360", "decks",
                           "step1_data_landscape.json")


def _deck_slides():
    try:
        with open(_DECK_PATH, encoding="utf-8") as f:
            deck = _json.load(f)
    except OSError:
        return []
    return deck.get("slides", []) if isinstance(deck, dict) else deck


_SLIDES = {s.get("id"): (s.get("diagram") or "") for s in _deck_slides()}


def _slide_svg(sid):
    """SVG готового слайда (960×540) без внешних зависимостей.

    Слайды с внешними файлами (<image href="/illustrations/...» и т. п.)
    на страницах не загрузятся — такие пропускаем; data:-URI допустимы.
    """
    svg = _SLIDES.get(sid, "")
    if 'href="/' in svg or "/illustrations/" in svg or "/icons/" in svg:
        return ""
    svg = svg.replace(' height="100%"', '', 1)
    return _strip_org(svg)


def _slide_fig(sid, caption):
    svg = _slide_svg(sid)
    return fig(svg, caption) if svg else ""


# Подписи слайдов иногда несут организационный слой презентации: адрес сайта
# материалов и отсылки к номерам занятий. В тексте они лишние — курс должен
# читаться самостоятельно, вне конкретного потока и его расписания.
_ORG_IN_SLIDES = [
    (": wybaeb.github.io/a360", ""),
    (" · теория и источники — лонгрид «Роль данных»", ""),
    ("На Шаге 4 это же дерево вы строите по своему проекту в тренажёре.",
     "То же дерево вы строите по своему проекту в тренажёре."),
]


def _strip_org(svg):
    for old, new in _ORG_IN_SLIDES:
        svg = svg.replace(old, new)
    return svg


# ── Типографика формул ──────────────────────────────────────────────────────
# Правило владельца: «формулы — крупно или никак». Отдельного класса в theme.py
# нет (общий модуль не правим), поэтому стиль задаётся инлайново.

def _F(expr, note=None):
    """Выключная формула: крупно, по центру, с необязательной расшифровкой."""
    out = ('<p style="font-size:20px;line-height:1.5;text-align:center;'
           'margin:18px 0 8px;font-weight:700;font-variant-numeric:tabular-nums">'
           f'{expr}</p>')
    if note:
        out += ('<p class="sub" style="text-align:center;margin:0 0 18px;'
                f'font-size:14.5px">{note}</p>')
    return out


def _more(summary, html):
    """Расхлоп для длинной математической выкладки."""
    return (f'<details class="more"><summary>{summary}</summary>{html}</details>')


# ── Локальные версии общих фигур с укрупнёнными подписями ───────────────────
# Правило волны: тексты в иллюстрациях, предназначенные для чтения, — не мельче
# 13px (в координатах 920px); подписи осей — второстепенные, можно мельче.
# Общий longread_figs не редактируем — укрупняем локально.

def _enlarge(svg, pairs):
    """Точечное укрупнение подписей в готовом SVG: замена атрибутов текста."""
    for old, new in pairs:
        svg = svg.replace(old, new)
    return svg


def npv_curve_lg():
    return _enlarge(npv_curve(), [
        (f'font-size="12" fill="{WARN}" font-weight="700"',
         f'font-size="13" fill="{WARN}" font-weight="700"'),
        (f'font-size="12" fill="{DEEP}" font-weight="700"',
         f'font-size="13" fill="{DEEP}" font-weight="700"'),
        (f'font-size="12.5" fill="{DEEP}" font-weight="800"',
         f'font-size="13.5" fill="{DEEP}" font-weight="800"'),
    ])


def ci_funnel_lg():
    """Последовательное наблюдение метрики — та же модель, что PNG слайда
    r4_a3 (kk_sber_a360/build/review_r4/fig_ci_real.py, график согласован
    владельцем в р4): поток Бернулли с истинной конверсией p = 0.23 при
    пороге решения 0.20 (seed 15), бегущая оценка и 95 % интервал Вильсона;
    наблюдение закрывается, когда нижняя граница продержалась выше порога
    30 наблюдений подряд, — n = 869, график обрывается ровно в этой точке.
    Точки пересчитываются здесь той же симуляцией (numpy), композиция
    повторяет PNG: подписи линий справа от края данных, плашка события
    остановки со стрелкой к точке.
    """
    import numpy as np
    P_TRUE, THR, SEED = 0.23, 0.20, 15
    Z = 1.959963984540054
    STABLE, N_MAX, N_MIN = 30, 5000, 20

    rng = np.random.default_rng(SEED)
    hits = rng.random(N_MAX) < P_TRUE
    k = np.cumsum(hits)
    n = np.arange(1, N_MAX + 1).astype(float)
    p = k / n
    denom = 1 + Z * Z / n
    centre = (p + Z * Z / (2 * n)) / denom
    halfw = (Z / denom) * np.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n))
    lo, hi = centre - halfw, centre + halfw
    run, stop = 0, None
    for i in range(N_MIN, N_MAX):
        run = run + 1 if lo[i] >= THR else 0
        if run >= STABLE:
            stop = i
            break
    n_stop = int(n[stop])                       # 869 (сходится с PNG слайда)
    idx = list(range(N_MIN - 1, stop + 1, 2))   # прореживание для веса SVG
    if idx[-1] != stop:
        idx.append(stop)

    # геометрия: справа от края данных — свободная зона под подписи (как в PNG)
    X0, Y0, X1, Y1 = 60, 24, 880, 330
    YMIN, YMAX = 0.10, 0.40
    NLIM = n_stop * 1.5
    gx = lambda v: X0 + (v - N_MIN) / (NLIM - N_MIN) * (X1 - X0)
    gy = lambda v: Y1 - (min(max(v, YMIN), YMAX) - YMIN) / (YMAX - YMIN) * (Y1 - Y0)

    s = []
    # сетка и оси
    for yt in (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40):
        s.append(f'<line x1="{X0}" y1="{gy(yt):.1f}" x2="{X1}" y2="{gy(yt):.1f}" '
                 f'stroke="#e7ece9" stroke-width="1"/>')
        s.append(_txt(X0 - 8, gy(yt) + 4, f"{yt:.0%}".replace("%", " %"), 11.5,
                      None, DARK, op=0.6, anchor="end"))
    for xt in (200, 400, 600, 800, 1000, 1200):
        s.append(f'<line x1="{gx(xt):.1f}" y1="{Y0}" x2="{gx(xt):.1f}" y2="{Y1}" '
                 f'stroke="#e7ece9" stroke-width="1"/>')
        s.append(_txt(gx(xt), Y1 + 18, str(xt), 11.5, None, DARK, op=0.6, anchor="middle"))
    s.append(_axes(X0, Y0, X1, Y1))
    s.append(_txt(X1, Y1 + 36, "наблюдений накоплено →", 12, None, DARK, op=0.6, anchor="end"))
    s.append(_txt(X0 - 8, 12, "конверсия", 12, None, DARK, op=0.6))

    # интервал Вильсона (полоса) + бегущая оценка; график обрывается в n_stop
    band_up = [(gx(n[i]), gy(hi[i])) for i in idx]
    band_lo = [(gx(n[i]), gy(lo[i])) for i in idx]
    area = ' '.join(f'{x:.1f},{y:.1f}' for x, y in band_up) + ' ' + \
           ' '.join(f'{x:.1f},{y:.1f}' for x, y in reversed(band_lo))
    s.append(f'<polygon points="{area}" fill="{ACC}" fill-opacity="0.16"/>')
    s.append(_poly(band_up, ACC, 1.7))
    s.append(_poly(band_lo, ACC, 1.7))
    s.append(_poly([(gx(n[i]), gy(p[i])) for i in idx], DEEP, 2.6))

    # порог решения
    s.append(f'<line x1="{X0}" y1="{gy(THR):.1f}" x2="{X1}" y2="{gy(THR):.1f}" '
             f'stroke="{WARN}" stroke-width="2" stroke-dasharray="7 5"/>')

    # точка остановки
    xe = gx(n_stop)
    s.append(f'<line x1="{xe:.1f}" y1="{Y0 + 4}" x2="{xe:.1f}" y2="{Y1}" '
             f'stroke="{DARK}" stroke-opacity="0.55" stroke-width="1.4" stroke-dasharray="3 4"/>')
    s.append(f'<circle cx="{xe:.1f}" cy="{gy(p[stop]):.1f}" r="6" fill="{DEEP}" '
             f'stroke="#ffffff" stroke-width="2"/>')
    s.append(f'<circle cx="{xe:.1f}" cy="{gy(lo[stop]):.1f}" r="5" fill="{ACC}" '
             f'stroke="#ffffff" stroke-width="2"/>')

    # подписи — однотипно, справа от края данных (как в PNG слайда)
    s.append(_txt(xe + 16, gy(hi[stop]) + 4, "95 % доверительный интервал (±E)", 13, "700", ACC))
    s.append(_txt(xe + 16, gy(p[stop]) + 4, "оценка конверсии (p̂)", 13, "700", DEEP))
    s.append(_txt(xe + 16, gy(THR) + 20, "порог решения 20 %", 13, "800", WARN))

    # событие остановки: плашка в свободной зоне справа-снизу, стрелка к точке
    bx, by, bw, bh = xe + 22, gy(THR) + 30, 250, 66
    s.append(_plate(bx, by, bw, bh, "#f7fbf8", stroke=ACC))
    s.append(_txt(bx + 14, by + 20, "наблюдение закрыто:", 13, "700"))
    s.append(_txt(bx + 14, by + 38, f"n = {n_stop} — нижняя граница", 13, "700"))
    s.append(_txt(bx + 14, by + 56, "устойчиво выше порога", 13, "700"))
    ax0, ay0 = bx + 6, by + 6
    ax1, ay1 = xe + 3, gy(lo[stop]) + 8
    s.append(f'<path d="M {ax0:.1f} {ay0:.1f} Q {xe - 6:.1f} {by - 4:.1f} {ax1:.1f} {ay1:.1f}" '
             f'fill="none" stroke="{DARK}" stroke-width="1.6"/>')
    s.append(f'<polygon points="{ax1 - 5:.1f},{ay1 + 9:.1f} {ax1 + 4:.1f},{ay1 + 8:.1f} '
             f'{ax1 - 1:.1f},{ay1 - 2:.1f}" fill="{DARK}"/>')
    return _svg(374, ''.join(s))


def accumulation2_lg():
    """Две фазы накопления — математическая модель (не эскиз).

    Та же модель, что в PNG слайда r4_a2 (kk_sber_a360/build/review_r4/
    fig_accum2.py): фаза 1 — приток RATE = 40 клиентов в день до целевого
    объёма N = 969 ≈ 970 из формулы выборки (p = 0.23, E = 2,65 п.п.) —
    набор завершается в день N/RATE ≈ 24; фаза 2 — по каждому клиенту метрика
    зреет горизонт H = 90 дней, поэтому кривая «клиенты с полным горизонтом»
    — кривая набора, сдвинутая вправо ровно на H (финиш — день ≈ 114).
    GST завершает досрочно только набор (n = 600, день 15 → финиш 105).
    """
    RATE, N, H_DAYS = 40, 969, 90
    T_FSS = N / RATE                     # 24.2
    T_GST, T_DONE = 15.0, N / RATE + H_DAYS   # 15 · 114.2
    T_MAX = 128
    X0, Y0, X1, Y1 = 60, 34, 880, 300
    gx = lambda d: X0 + d / T_MAX * (X1 - X0 - 16)
    gy = lambda c: Y1 - c / 1180 * (Y1 - Y0 - 10)

    s = []
    s.append(_axes(X0, Y0, X1, Y1))
    s.append(_txt(X1, 316, "день эксперимента →", 12, None, DARK, op=0.6, anchor="end"))
    s.append(_txt(X0 - 8, Y0 - 12, "клиентов накоплено", 12, None, DARK, op=0.6))
    for d in (0, 15, 24, 90):
        s.append(_txt(gx(d), 316, str(d), 12, None, DARK, op=0.6, anchor="middle"))
    # целевой объём — отметка на оси y
    s.append(f'<line x1="{X0}" y1="{gy(N):.1f}" x2="{gx(T_FSS):.1f}" y2="{gy(N):.1f}" '
             f'stroke="{DARK}" stroke-opacity="0.4" stroke-width="1.3" stroke-dasharray="5 5"/>')
    s.append(_txt(X0 - 8, gy(N) + 4, "n ≈ 970", 12, "700", DARK, op=0.7, anchor="end"))
    # фаза 2: клиенты с полным горизонтом (кривая набора, сдвинутая на 90 дней)
    s.append(f'<polygon points="{gx(H_DAYS):.1f},{Y1} {gx(T_DONE):.1f},{gy(N):.1f} '
             f'{gx(T_MAX):.1f},{gy(N):.1f} {gx(T_MAX):.1f},{Y1}" fill="{ACC}" fill-opacity="0.14"/>')
    s.append(_poly([(gx(H_DAYS), Y1), (gx(T_DONE), gy(N)), (gx(T_MAX), gy(N))], ACC, 2.6))
    # фаза 1: набор 40 клиентов в день до плато n ≈ 970
    s.append(_poly([(gx(0), Y1), (gx(T_FSS), gy(N)), (gx(T_MAX), gy(N))], DEEP, 2.6))
    # GST и FSS — вертикали с ярлыками и расшифровкой
    for d, name in ((T_GST, "GST"), (T_FSS, "FSS")):
        s.append(f'<line x1="{gx(d):.1f}" y1="52" x2="{gx(d):.1f}" y2="{Y1}" '
                 f'stroke="{DEEP}" stroke-width="1.6" stroke-dasharray="6 5"/>')
        s.append(_txt(gx(d), 46, name, 13, "800", DEEP, anchor="middle"))
    s.append(_txt(240, 50, "GST · участников достаточно, набор закрыт досрочно (день 15)", 13, "700"))
    s.append(_txt(240, 70, "FSS · плановое завершение набора — n ≈ 970 (день ≈ 24)", 13, "700"))
    # подписи кривых
    s.append(_txt(240, 103, "клиентов набрано (40 в день)", 13, "700", DEEP))
    s.append(_txt(680, 200, "клиенты с полным горизонтом 90 дней", 13, "700", ACC, anchor="end"))
    # финиш: данные по всей выборке
    s.append(f'<line x1="{gx(T_DONE):.1f}" y1="90" x2="{gx(T_DONE):.1f}" y2="{Y1}" '
             f'stroke="{DARK}" stroke-opacity="0.55" stroke-width="1.4" stroke-dasharray="3 4"/>')
    s.append(f'<circle cx="{gx(T_DONE):.1f}" cy="{gy(N):.1f}" r="6" fill="{ACC}" '
             f'stroke="#ffffff" stroke-width="2"/>')
    s.append(_txt(735, 130, "данные по всей выборке — день ≈ 114 (24 + 90)", 13, "700", anchor="end"))
    # главный вывод модели
    s.append(_txt(240, 152, "GST сокращает только фазу 1: финиш — день 105 вместо ≈ 114.", 13, "700", WARN))
    s.append(_txt(240, 172, "Горизонт 90 дней не сжимается", 13, "700", WARN))
    # ленты фаз
    s.append(f'<rect x="{X0}" y="328" width="{gx(T_FSS) - X0:.1f}" height="24" rx="7" fill="{ACC}" fill-opacity="0.8"/>')
    s.append(f'<rect x="{gx(T_FSS) + 3:.1f}" y="328" width="{gx(T_DONE) - gx(T_FSS) - 3:.1f}" height="24" rx="7" fill="{DEEP}" fill-opacity="0.25"/>')
    s.append(_txt((X0 + gx(T_FSS)) / 2, 345, "фаза 1", 13, "700", "#ffffff", anchor="middle"))
    s.append(_txt((gx(T_FSS) + gx(T_DONE)) / 2, 345, "фаза 2 · накапливаются данные (горизонт 90 дней)", 13, "700", DEEP, anchor="middle"))
    return _svg(368, ''.join(s))


GRAY = "#98A2AD"
GRID = "#e3e8e5"

# Точки графика — одиннадцать реальных метрик трёх кейсов тренажёра, те же,
# что в модели review_r4/fig_tradeoff.py: (id, подпись, сдвиг подписи по Y).
_TRADEOFF_PTS = [
    ("actB",  "Активация: флаг CRM",            5),
    ("rw",    "Доля досье на доработку",       36),
    ("rev",   "Доход по продукту",            -14),
    ("act",   "Активация: витрина DWH",         5),
    ("err",   "Ошибки в заявке",                5),
    ("dict",  "Словарь определений портфеля",   5),
    ("tat",   "Срок доставки карты",            5),
    ("mn",    "Ручная выборка кейсов",          5),
    ("adhoc", "Точечные сверки",               17),
    ("churn", "Отток за 90 дней",               5),
    ("pnl",   "P&amp;L продукта",               5),
]
_TRADEOFF_MANUAL = {"mn", "adhoc"}   # ручные конфигурации сбора
_TRADEOFF_MONTHS = 3                 # горизонт владения для TCO


def tradeoff_scatter_lg():
    """Компромисс TTE × TCO на реальных метриках тренажёра.

    Та же модель, что в PNG слайда r5_b1 (review_r4/fig_tradeoff.py): TCO
    за три месяца против времени до проверенного значения, фронт Парето,
    изолиния равной интегральной оценки и две лучшие конфигурации.
    Числа берутся из metrics_data, поэтому график и паспорта метрик
    не расходятся.
    """
    pts = []
    for mid, label, dy in _TRADEOFF_PTS:
        m = metric(mid)
        tco = m["capex"] + _TRADEOFF_MONTHS * m["opex"]
        pts.append(dict(id=mid, label=label, dy=dy, tte=m["tte"], tco=tco,
                        score=1000.0 / (tco * m["tte"])))
    front = {i for i, a in enumerate(pts)
             if not any(b["tte"] <= a["tte"] and b["tco"] <= a["tco"]
                        and (b["tte"] < a["tte"] or b["tco"] < a["tco"])
                        for j, b in enumerate(pts) if j != i)}
    best = sorted(range(len(pts)), key=lambda i: -pts[i]["score"])[:2]
    for i in best:
        pts[i]["label"] += " · %s" % ("%.2f" % pts[i]["score"]).replace(".", ",")

    X0, Y0, X1, Y1 = 76, 46, 884, 330
    XMAX, YMAX = 118.0, 300.0
    px = lambda t: X0 + t / XMAX * (X1 - X0)
    py = lambda c: Y1 - c / YMAX * (Y1 - Y0)
    s = []
    for c in range(0, 301, 60):                       # сетка и подписи оси Y
        s.append(f'<line x1="{X0}" y1="{py(c):.1f}" x2="{X1}" y2="{py(c):.1f}" '
                 f'stroke="{GRID}" stroke-width="1"/>')
        s.append(_txt(X0 - 10, py(c) + 4, str(c), 12.5, None, DARK, op=0.6, anchor="end"))
    for t in range(0, 106, 15):                       # сетка и подписи оси X
        s.append(f'<line x1="{px(t):.1f}" y1="{Y0}" x2="{px(t):.1f}" y2="{Y1}" '
                 f'stroke="{GRID}" stroke-width="1"/>')
        s.append(_txt(px(t), Y1 + 20, str(t), 12.5, None, DARK, op=0.6, anchor="middle"))
    s.append(_axes(X0, Y0, X1, Y1))
    s.append(_txt(X1, Y1 + 42, "TTE — дней до проверенного значения →", 13.5, "700", DARK, anchor="end"))
    s.append(_txt(X0 - 10, Y0 - 14, "TCO за 3 месяца, т₽", 13.5, "700", DARK))
    s.append(_txt(X0 + 14, Y0 + 22, "Интегральная оценка качества данных = 1 / (TCO × TTE)",
                  13.5, "700", DARK))
    s.append(_txt(X0 + 14, Y0 + 42, "TCO = CAPEX + 3 мес × OPEX · у обведённых точек — оценка ×10⁻³",
                  12.5, None, DARK, op=0.75))

    K = pts[best[0]]["tco"] * pts[best[0]]["tte"]     # изолиния равной оценки
    iso = [(px(K / c), py(c)) for c in [YMAX - 4] +
           [YMAX - 4 - i * (YMAX - 10) / 40 for i in range(1, 41)]
           if 0 < K / c <= XMAX]
    s.append(_poly(iso, DARK, 1.8, dash="5 4", op=0.45))

    fr = sorted(front, key=lambda i: pts[i]["tte"])   # фронт Парето
    s.append(_poly([(px(pts[i]["tte"]), py(pts[i]["tco"])) for i in fr], ACC, 2.5))

    for i, d in enumerate(pts):
        x, y = px(d["tte"]), py(d["tco"])
        if d["id"] in _TRADEOFF_MANUAL:
            s.append(f'<polygon points="{x:.1f},{y - 9:.1f} {x + 9:.1f},{y:.1f} '
                     f'{x:.1f},{y + 9:.1f} {x - 9:.1f},{y:.1f}" fill="{WARN}" '
                     f'stroke="#ffffff" stroke-width="1.4"/>')
        else:
            col = DEEP if i in front else GRAY
            s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{8 if i in front else 6.5}" '
                     f'fill="{col}" stroke="#ffffff" stroke-width="1.5"/>')
    for i in best:
        s.append(f'<circle cx="{px(pts[i]["tte"]):.1f}" cy="{py(pts[i]["tco"]):.1f}" '
                 f'r="15" fill="none" stroke="{DEEP}" stroke-width="2.6"/>')
    for d in pts:
        # Белая обводка под текстом: подписи ближних точек проходят рядом
        # с линией фронта, и без подложки они читаются хуже.
        s.append(f'<text x="{px(d["tte"]) + 19:.1f}" y="{py(d["tco"]) + d["dy"]:.1f}" '
                 f'font-size="13" font-weight="700" fill="{DARK}" stroke="#ffffff" '
                 f'stroke-width="3.5" stroke-linejoin="round" '
                 f'style="paint-order:stroke fill">{d["label"]}</text>')

    LEG = [(76, 402, "line", ACC, "фронт Парето: обе оси сразу не улучшить"),
           (420, 402, "ring", DEEP, "лучшие по интегральной оценке"),
           (76, 428, "dot", GRAY, "доминируемые конфигурации"),
           (330, 428, "diamond", WARN, "ручной сбор: OPEX обесценивает экономию"),
           (640, 428, "dash", DARK, "равная оценка: TCO × TTE = const")]
    for x, y, kind, col, text in LEG:
        cy = y - 4
        if kind == "line":
            s.append(f'<line x1="{x - 11}" y1="{cy}" x2="{x + 11}" y2="{cy}" '
                     f'stroke="{ACC}" stroke-width="2.5"/>')
            s.append(f'<circle cx="{x}" cy="{cy}" r="6" fill="{DEEP}" stroke="#ffffff" stroke-width="1.4"/>')
        elif kind == "ring":
            s.append(f'<circle cx="{x}" cy="{cy}" r="9" fill="none" stroke="{col}" stroke-width="2.4"/>')
        elif kind == "dot":
            s.append(f'<circle cx="{x}" cy="{cy}" r="6.5" fill="{col}" stroke="#ffffff" stroke-width="1.4"/>')
        elif kind == "diamond":
            s.append(f'<polygon points="{x},{cy - 8} {x + 8},{cy} {x},{cy + 8} {x - 8},{cy}" '
                     f'fill="{col}" stroke="#ffffff" stroke-width="1.4"/>')
        else:
            s.append(f'<line x1="{x - 13}" y1="{cy}" x2="{x + 13}" y2="{cy}" stroke="{col}" '
                     f'stroke-width="1.8" stroke-dasharray="5 4" stroke-opacity="0.45"/>')
        s.append(_txt(x + 22, y, text, 13, None, DARK, op=0.85))
    return _svg(446, ''.join(s))


def cod_profiles_lg():
    """Локальная копия cod_profiles: карточки шире, подписи 14/13px вместо 13/11."""
    s = []
    W, H, GX, GY = 292, 120, 12, 46
    PROF = [
        ("Линейный", "каждый месяц — одинаковая потеря", lambda t: t),
        ("Фиксированный срок", "до даты потерь нет, после — штраф", lambda t: 0.06 if t < 0.55 else 0.95),
        ("Делать сейчас", "штраф уже накапливается и растёт", lambda t: 0.35 + 0.6 * t),
        ("Логарифмический", "основные потери — в начале", lambda t: _math.log1p(t * 12) / _math.log1p(12)),
        ("Незаметный", "технический долг: потери долго не видны", lambda t: (_math.exp(2.6 * t) - 1) / (_math.exp(2.6) - 1)),
        ("Разовая стоимость", "единовременная потеря", lambda t: 0.82),
    ]
    for i, (name, sub, f) in enumerate(PROF):
        cx, cy = 10 + (i % 3) * (W + GX), 8 + (i // 3) * (H + GY + 30)
        s.append(_plate(cx, cy, W, H + 34, "#fbfdfc"))
        s.append(_txt(cx + 14, cy + 23, name, 14, "700"))
        x0, y0, x1, y1 = cx + 14, cy + 32, cx + W - 14, cy + H - 4
        s.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{DARK}" stroke-opacity="0.25" stroke-width="1.2"/>')
        s.append(_poly([(x0 + t * (x1 - x0), y1 - 4 - f(t) * (y1 - y0 - 8))
                        for t in [j / 36 for j in range(37)]], DEEP, 2.2))
        s.append(_txt(cx + 14, cy + H + 23, sub, 13, None, DARK, op=0.75))
    return _svg(2 * (120 + 46 + 30) + 10, ''.join(s))


# ── Новые фигуры справочника ────────────────────────────────────────────────

def discount_bars():
    """Механика дисконтирования: одинаковый номинальный поток по месяцам —
    и он же, приведённый к сегодняшнему дню множителем 1/(1+r)^t.
    Ставка r = 1 %/мес (12 % годовых) — та же, что в примерах финансовой модели.
    """
    R, H, NOM = 0.01, 36, 180.0
    X0, Y0, X1, Y1 = 62, 122, 880, 302
    s = []
    # верхняя полоса — легенда и вывод: над столбцами, чтобы ничего не перекрывать
    s.append(_plate(X0, 6, 556, 82, "#f7fbf8", stroke=ACC))
    s.append(_txt(X0 + 20, 32, "светлое — номинал суммы, как он стоит в бюджете", 14, "700", DARK))
    s.append(_txt(X0 + 20, 54, "тёмное — та же сумма, приведённая к сегодня: 100 000 / (1 + r)ᵗ",
                  14, "700", DEEP))
    s.append(_txt(X0 + 20, 76, "ставка дисконта r = 1 % в месяц (12 % годовых)", 13.5,
                  None, DARK, op=0.8))
    s.append(_plate(X0 + 574, 6, 244, 82, "#fdf5f4", stroke=WARN))
    s.append(_txt(X0 + 592, 32, "через 36 месяцев", 14, "700", WARN))
    s.append(_txt(X0 + 592, 54, "100 000 ₽ стоят сегодня", 14, "700", WARN))
    s.append(_txt(X0 + 592, 76, "около 69 900 ₽", 14, "800", WARN))
    s.append(_axes(X0, Y0, X1, Y1))
    bw = (X1 - X0 - 26) / H
    for t in range(1, H + 1):
        x = X0 + 10 + (t - 1) * bw
        h_disc = NOM / (1 + R) ** t
        s.append(f'<rect x="{x:.1f}" y="{Y1 - NOM:.1f}" width="{bw - 4:.1f}" '
                 f'height="{NOM:.1f}" rx="2" fill="{ACC}" fill-opacity="0.22"/>')
        s.append(f'<rect x="{x:.1f}" y="{Y1 - h_disc:.1f}" width="{bw - 4:.1f}" '
                 f'height="{h_disc:.1f}" rx="2" fill="{DEEP}" fill-opacity="0.85"/>')
    s.append(_poly([(X0 + 10 + (t - 1) * bw + (bw - 4) / 2, Y1 - NOM / (1 + R) ** t)
                    for t in range(1, H + 1)], WARN, 2.4))
    for t in (1, 12, 24, 36):
        x = X0 + 10 + (t - 1) * bw + (bw - 4) / 2
        s.append(_txt(x, Y1 + 22, str(t), 12.5, None, DARK, op=0.65, anchor="middle"))
    s.append(_txt(X1, Y1 + 42, "месяц поступления, t →", 12.5, None, DARK, op=0.65, anchor="end"))
    s.append(_txt(X0 - 8, Y0 - 12, "одна и та же сумма 100 000 ₽, поступившая в месяце t",
                  13, None, DARK, op=0.7))
    xe = X0 + 10 + (H - 1) * bw + (bw - 4) / 2
    s.append(f'<circle cx="{xe:.1f}" cy="{Y1 - NOM / (1 + R) ** H:.1f}" r="6" '
             f'fill="{WARN}" stroke="#ffffff" stroke-width="2"/>')
    return _svg(356, ''.join(s))


def tco_stack():
    """Совокупная стоимость владения двух конфигураций на горизонте пилота:
    дорогой старт с дешёвой эксплуатацией против дешёвого старта с ручным
    трудом. Точка пересечения TCO — момент, когда «дешёвый» вариант
    становится дороже. Числа — из паспортов метрик кейса «Корпоративный
    блок»: журнал этапов workflow (CAPEX 180 т₽, OPEX 45 т₽/мес) и ручная
    выборка кейсов (CAPEX 15 т₽, OPEX 45 т₽/мес) — здесь для наглядности
    сравниваются журнал (180 / 12) и ручная выборка (15 / 45).
    """
    A_CAP, A_OP = 180.0, 12.0    # витрина: дорого построить, дёшево держать
    B_CAP, B_OP = 15.0, 45.0     # ручная выборка: почти бесплатный старт
    H = 24
    X0, Y0, X1, Y1 = 62, 30, 880, 300
    ymax = max(A_CAP + A_OP * H, B_CAP + B_OP * H) * 1.12
    gx = lambda m: X0 + m / H * (X1 - X0 - 150)
    gy = lambda v: Y1 - v / ymax * (Y1 - Y0)
    s = [_axes(X0, Y0, X1, Y1)]
    for v in (0, 250, 500, 750, 1000):
        s.append(f'<line x1="{X0}" y1="{gy(v):.1f}" x2="{X1 - 150}" y2="{gy(v):.1f}" '
                 f'stroke="#e7ece9" stroke-width="1"/>')
        s.append(_txt(X0 - 8, gy(v) + 4, f"{v}", 11.5, None, DARK, op=0.6, anchor="end"))
    for m in (0, 6, 12, 18, 24):
        s.append(_txt(gx(m), Y1 + 20, str(m), 12, None, DARK, op=0.65, anchor="middle"))
    s.append(_txt(gx(H) + 6, Y1 + 40, "месяцы владения →", 12.5, None, DARK, op=0.65, anchor="end"))
    s.append(_txt(X0 - 8, Y0 - 12, "TCO нарастающим итогом, т₽", 12.5, None, DARK, op=0.65))
    s.append(_poly([(gx(m), gy(A_CAP + A_OP * m)) for m in range(H + 1)], DEEP, 2.8))
    s.append(_poly([(gx(m), gy(B_CAP + B_OP * m)) for m in range(H + 1)], WARN, 2.8))
    mx = (A_CAP - B_CAP) / (B_OP - A_OP)
    s.append(f'<circle cx="{gx(mx):.1f}" cy="{gy(A_CAP + A_OP * mx):.1f}" r="7" '
             f'fill="{DARK}" stroke="#ffffff" stroke-width="2"/>')
    s.append(f'<line x1="{gx(mx):.1f}" y1="{gy(A_CAP + A_OP * mx):.1f}" x2="{gx(mx):.1f}" '
             f'y2="{Y1}" stroke="{DARK}" stroke-opacity="0.5" stroke-width="1.4" stroke-dasharray="4 4"/>')
    mx_s = f"{mx:.1f}".replace(".", ",")
    s.append(_txt(gx(mx) + 14, gy(A_CAP + A_OP * mx) - 34,
                  f"месяц {mx_s} — «дешёвая» конфигурация", 13.5, "700", DARK))
    s.append(_txt(gx(mx) + 14, gy(A_CAP + A_OP * mx) - 15,
                  "сравнялась по совокупной стоимости владения", 13.5, "700", DARK))
    s.append(_txt(gx(H) + 12, gy(A_CAP + A_OP * H) + 5, "витрина процесса:", 13.5, "700", DEEP))
    s.append(_txt(gx(H) + 12, gy(A_CAP + A_OP * H) + 24, "CAPEX 180 т₽ + 12 т₽/мес", 13, None, DARK, op=0.85))
    s.append(_txt(gx(H) + 12, gy(B_CAP + B_OP * H) + 5, "ручная выборка:", 13.5, "700", WARN))
    s.append(_txt(gx(H) + 12, gy(B_CAP + B_OP * H) + 24, "CAPEX 15 т₽ + 45 т₽/мес", 13, None, DARK, op=0.85))
    return _svg(348, ''.join(s))


def dq_index():
    """Интегральная оценка качества данных: шесть частных измерений
    со своими весами сворачиваются в одно число. Значения — учебные,
    из кейса розничной витрины активации.
    """
    ROWS = [
        ("Полнота", "доля записей без пропусков в обязательных полях", 0.25, 0.94),
        ("Уникальность", "доля объектов без дублей после дедупликации", 0.20, 0.99),
        ("Корректность", "доля значений, прошедших форматные и справочные проверки", 0.20, 0.91),
        ("Согласованность", "доля показателей, совпадающих между системами", 0.15, 0.78),
        ("Актуальность", "доля обновлений, пришедших в срок регламента", 0.15, 0.96),
        ("Прослеживаемость", "доля показателей, доводимых до первичной записи", 0.05, 0.70),
    ]
    total = sum(w * v for _, _, w, v in ROWS)
    s = []
    X0, XW = 372, 350
    for i, (name, sub, w, v) in enumerate(ROWS):
        y = 20 + i * 62
        s.append(_txt(14, y + 18, name, 14.5, "800", DARK))
        s.append(_txt(14, y + 38, sub, 12.5, None, DARK, op=0.7))
        s.append(f'<rect x="{X0}" y="{y + 6}" width="{XW}" height="26" rx="7" '
                 f'fill="{DARK}" fill-opacity="0.07"/>')
        s.append(f'<rect x="{X0}" y="{y + 6}" width="{XW * v:.1f}" height="26" rx="7" '
                 f'fill="{ACC if v >= 0.9 else WARN}" fill-opacity="0.85"/>')
        s.append(_txt(X0 + XW * v - 10, y + 25, f"{v:.0%}".replace("%", " %"), 13.5, "800",
                      "#ffffff", anchor="end"))
        s.append(_txt(X0 + XW + 16, y + 25, f"вес {w:.2f}".replace(".", ","), 13.5, "700",
                      DARK, op=0.8))
    y = 20 + len(ROWS) * 62 + 6
    s.append(_plate(14, y, 892, 76, "#eef7f1", stroke=ACC))
    s.append(_txt(36, y + 32, "Интегральная оценка качества данных = Σ (вес × частная оценка)",
                  15, "800", DARK))
    s.append(_txt(36, y + 58,
                  f"0,25·94 % + 0,20·99 % + 0,20·91 % + 0,15·78 % + 0,15·96 % + 0,05·70 % = "
                  f"{total:.3f}".replace(".", ",") + " → 91 из 100", 14, "700", DEEP))
    return _svg(y + 96, ''.join(s))


def passport_curve():
    """Паспорт инициативы → NPV-кривая. Модель листа «Модель» финансовой
    модели портфеля (kk_sber_a360/build/review_r4/fig_portfolio.py):
    накопленная прибыль — парабола через три точки:
        y(t0) = −C0 (расходы к старту),
        вершина в месяце t0 + P (выход на прибыльность),
        ноль в месяце t0 + O (окупаемость).
    Здесь показана одна инициатива: t0 = 6, C0 = 1,116 млн ₽, P = 6, O = 18.
    """
    T0, C0, P, O, H = 6, 1.116, 6, 18, 36
    R = 1 / 120.0
    x2, x3 = T0 + O, T0 + 2 * P - O
    a = -C0 / ((T0 - x3) * (T0 - x2))
    cum = [0.0] * (H + 1)
    for m in range(1, H + 1):
        cum[m] = a * (m - x3) * (m - x2) if m >= T0 else 0.0
    npv, acc = [0.0] * (H + 1), 0.0
    for m in range(1, H + 1):
        acc += (cum[m] - cum[m - 1]) / (1 + R) ** m
        npv[m] = acc

    X0, Y0, X1, Y1 = 66, 30, 880, 318
    lo, hi = -2.4, 5.4
    gx = lambda m: X0 + m / H * (X1 - X0 - 40)
    gy = lambda v: Y1 - (v - lo) / (hi - lo) * (Y1 - Y0)
    s = [_axes(X0, Y0, X1, Y1)]
    for v in (-2, -1, 0, 1, 2, 3, 4, 5):
        s.append(f'<line x1="{X0}" y1="{gy(v):.1f}" x2="{X1 - 40}" y2="{gy(v):.1f}" '
                 f'stroke="#e7ece9" stroke-width="1"/>')
        s.append(_txt(X0 - 8, gy(v) + 4, str(v), 11.5, None, DARK, op=0.6, anchor="end"))
    s.append(f'<line x1="{X0}" y1="{gy(0):.1f}" x2="{X1 - 40}" y2="{gy(0):.1f}" '
             f'stroke="{DARK}" stroke-opacity="0.45" stroke-width="1.6"/>')
    for m in (0, 6, 12, 18, 24, 30, 36):
        s.append(_txt(gx(m), Y1 + 20, str(m), 12, None, DARK, op=0.65, anchor="middle"))
    s.append(_txt(X1 - 40, Y1 + 40, "месяцы портфеля →", 12.5, None, DARK, op=0.65, anchor="end"))
    s.append(_txt(X0 - 8, Y0 - 12, "накопленный поток, млн ₽", 12.5, None, DARK, op=0.65))
    s.append(_poly([(gx(m), gy(cum[m])) for m in range(T0, H + 1)], ACC, 2.0, dash="6 4"))
    s.append(_poly([(gx(m), gy(npv[m])) for m in range(T0, H + 1)], DEEP, 3.0))

    # Точки паспорта помечаются номерными кружками, расшифровка — единой
    # легендой в свободной верхней левой зоне: подписи у самих точек
    # накладывались бы друг на друга.
    def badge(m, v, num, col):
        s.append(f'<circle cx="{gx(m):.1f}" cy="{gy(v):.1f}" r="11" fill="{col}" '
                 f'stroke="#ffffff" stroke-width="2.4"/>')
        s.append(_txt(gx(m), gy(v) + 5, num, 13, "800", "#ffffff", anchor="middle"))

    badge(T0, npv[T0], "1", WARN)
    badge(T0 + P, npv[T0 + P], "2", WARN)
    badge(T0 + O, 0, "3", DEEP)
    badge(H, npv[H], "4", DEEP)

    LX, LY = X0 + 26, 40
    s.append(_plate(LX, LY, 500, 116, "#f7fbf8", stroke=ACC))
    LEG = [
        ("1", WARN, "месяц старта — 6, расходы к старту 1,12 млн ₽"),
        ("2", WARN, "выход на прибыльность — через 6 мес., минимум кривой в месяце 12"),
        ("3", DEEP, "окупаемость — через 18 мес., ноль в месяце 24"),
        ("4", DEEP, "NPV за горизонт 36 месяцев"),
    ]
    for i, (num, col, text) in enumerate(LEG):
        y = LY + 26 + i * 25
        s.append(f'<circle cx="{LX + 26}" cy="{y - 5}" r="9.5" fill="{col}"/>')
        s.append(_txt(LX + 26, y, num, 12, "800", "#ffffff", anchor="middle"))
        s.append(_txt(LX + 44, y, text, 13.5, "700", DARK))
    # подписи кривых на белой подложке: линии проходят рядом, без подложки
    # текст читается хуже
    def curve_label(x_end, y, text, col, w):
        s.append(f'<rect x="{x_end - w:.1f}" y="{y - 15:.1f}" width="{w}" height="21" '
                 f'rx="5" fill="#ffffff" fill-opacity="0.88"/>')
        s.append(_txt(x_end - 6, y, text, 13.5, "700", col, anchor="end"))

    s.append(f'<line x1="{gx(34.6):.1f}" y1="52" x2="{gx(34.6):.1f}" '
             f'y2="{gy(cum[34]) - 6:.1f}" stroke="{ACC}" stroke-width="1.4"/>')
    curve_label(gx(36), 48, "накопленный поток без дисконта", ACC, 232)
    curve_label(gx(36), gy(npv[31]) + 30, "NPV — тот же поток, приведённый к сегодня", DEEP, 320)
    return _svg(370, ''.join(s))


def portfolio_curve():
    """Кривые инициатив складываются в кривую портфеля.

    Полная копия модели PNG слайда r4_p1 (kk_sber_a360/build/review_r4/
    fig_portfolio.py): 14 паспортов инициатив из финансовой модели портфеля,
    накопленная прибыль каждой — парабола через три точки паспорта,
    дисконт 1/120 в месяц; суммарная кривая — почленная сумма.
    Дно, окупаемость и NPV портфеля вычисляются, а не рисуются.
    """
    PASSPORTS = [
        (9, 1.116, 6, 18), (3, 1.116, 6, 22), (6, 1.116, 6, 18),
        (9, 1.116, 6, 18), (12, 1.116, 6, 18), (12, 1.116, 6, 18),
        (6, 1.116, 4, 12), (6, 1.116, 6, 18), (9, 1.116, 6, 18),
        (9, 1.116, 6, 18), (12, 3.348, 4, 12), (3, 5.022, 6, 18),
        (6, 3.348, 6, 18), (9, 5.022, 6, 18),
    ]
    H, R = 36, 1 / 120.0

    def curve(t0, c0, prof, payb):
        x2, x3 = t0 + payb, t0 + 2 * prof - payb
        a = -c0 / ((t0 - x3) * (t0 - x2))
        cum = [a * (m - x3) * (m - x2) if m >= t0 else 0.0 for m in range(H + 1)]
        out, acc = [0.0] * (H + 1), 0.0
        for m in range(1, H + 1):
            acc += (cum[m] - cum[m - 1]) / (1 + R) ** m
            out[m] = acc
        return out

    curves = [curve(*p) for p in PASSPORTS]
    total = [sum(c[m] for c in curves) for m in range(H + 1)]
    i_dip = min(range(1, H + 1), key=lambda m: total[m])
    m_pay = next(m for m in range(i_dip + 1, H + 1) if total[m] >= 0)

    X0, Y0, X1, Y1 = 70, 30, 880, 322
    lo, hi = -46.0, 100.0
    gx = lambda m: X0 + m / H * (X1 - X0 - 30)
    gy = lambda v: Y1 - (v - lo) / (hi - lo) * (Y1 - Y0)
    s = [_axes(X0, Y0, X1, Y1)]
    for v in (-40, -20, 0, 20, 40, 60, 80, 100):
        s.append(f'<line x1="{X0}" y1="{gy(v):.1f}" x2="{X1 - 30}" y2="{gy(v):.1f}" '
                 f'stroke="#e7ece9" stroke-width="1"/>')
        s.append(_txt(X0 - 8, gy(v) + 4, str(v), 11.5, None, DARK, op=0.6, anchor="end"))
    s.append(f'<line x1="{X0}" y1="{gy(0):.1f}" x2="{X1 - 30}" y2="{gy(0):.1f}" '
             f'stroke="{DARK}" stroke-opacity="0.45" stroke-width="1.6"/>')
    for m in (0, 6, 12, 18, 24, 30, 36):
        s.append(_txt(gx(m), Y1 + 20, str(m), 12, None, DARK, op=0.65, anchor="middle"))
    s.append(_txt(X1 - 30, Y1 + 40, "месяцы портфеля →", 12.5, None, DARK, op=0.65, anchor="end"))
    s.append(_txt(X0 - 8, Y0 - 12, "NPV нарастающим итогом, млн ₽", 12.5, None, DARK, op=0.65))
    for c in curves:
        st = next((m for m in range(1, H + 1) if c[m] != 0), 1)
        s.append(_poly([(gx(m), gy(c[m])) for m in range(st - 1, H + 1)], ACC, 1.7, op=0.7))
    s.append(_poly([(gx(m), gy(total[m])) for m in range(1, H + 1)], DEEP, 3.4))

    s.append(_txt(gx(1.4), gy(76), "NPV-кривые 14 инициатив: каждая построена", 13.5, "700", DARK))
    s.append(_txt(gx(1.4), gy(70), "из своего паспорта инициативы", 13.5, "700", DARK))
    s.append(f'<path d="M {gx(6):.1f} {gy(66):.1f} Q {gx(8):.1f} {gy(30):.1f} '
             f'{gx(9.2):.1f} {gy(-4):.1f}" fill="none" stroke="{ACC}" stroke-width="1.8"/>')
    s.append(f'<polygon points="{gx(9.2) - 5:.1f},{gy(-4) - 8:.1f} {gx(9.2) + 5:.1f},'
             f'{gy(-4) - 7:.1f} {gx(9.2):.1f},{gy(-4) + 3:.1f}" fill="{ACC}"/>')
    s.append(_txt(gx(13.2), gy(58), "кривая портфеля — сумма потоков инициатив", 14, "800", DEEP))
    s.append(f'<path d="M {gx(27):.1f} {gy(54):.1f} Q {gx(29.6):.1f} {gy(48):.1f} '
             f'{gx(30.4):.1f} {gy(total[30]) - 10:.1f}" fill="none" stroke="{DEEP}" stroke-width="1.9"/>')
    s.append(f'<polygon points="{gx(30.4) - 5:.1f},{gy(total[30]) - 16:.1f} {gx(30.4) + 5:.1f},'
             f'{gy(total[30]) - 15:.1f} {gx(30.4):.1f},{gy(total[30]) - 5:.1f}" fill="{DEEP}"/>')

    dip = total[i_dip]
    s.append(f'<circle cx="{gx(i_dip):.1f}" cy="{gy(dip):.1f}" r="7" fill="{WARN}" '
             f'stroke="#ffffff" stroke-width="2.2"/>')
    dip_s = f"{abs(dip):.1f}".replace(".", ",")
    s.append(_txt(gx(i_dip) + 14, gy(dip) + 10,
                  f"минимум: −{dip_s} млн ₽ (месяц {i_dip}) —", 13.5, "700", WARN))
    s.append(_txt(gx(i_dip) + 14, gy(dip) + 30, "пик потребности в финансировании",
                  13.5, "700", WARN))
    s.append(f'<line x1="{gx(m_pay):.1f}" y1="{Y0 + 6}" x2="{gx(m_pay):.1f}" y2="{Y1}" '
             f'stroke="{DEEP}" stroke-width="1.5" stroke-dasharray="3 4" stroke-opacity="0.6"/>')
    s.append(f'<circle cx="{gx(m_pay):.1f}" cy="{gy(0):.1f}" r="7" fill="{DEEP}" '
             f'stroke="#ffffff" stroke-width="2.2"/>')
    s.append(_txt(gx(m_pay) + 12, gy(0) + 26, f"окупаемость портфеля — месяц {m_pay}",
                  13.5, "700", DEEP))
    s.append(f'<circle cx="{gx(H):.1f}" cy="{gy(total[H]):.1f}" r="7.5" fill="{DEEP}" '
             f'stroke="#ffffff" stroke-width="2.2"/>')
    npv_s = f"{total[H]:.1f}".replace(".", ",")
    s.append(_plate(gx(16.4), gy(96), 322, 40, "#f7fbf8", stroke=ACC))
    s.append(_txt(gx(17.2), gy(96) + 26, f"NPV портфеля за 36 мес. = +{npv_s} млн ₽",
                  14.5, "800", DEEP))
    return _svg(374, ''.join(s))


def sample_size_sensitivity():
    """Квадратичный рост объёма выборки при ужесточении погрешности:
    n = (Z·σ/E)² для доли p = 0,5 и уровня доверия 95 %.
    """
    Z, SIG = 1.96, 0.5
    ERR = [0.10, 0.07, 0.05, 0.04, 0.03, 0.02, 0.015, 0.01]
    X0, Y0, X1, Y1 = 74, 30, 880, 292
    ns = [(Z * SIG / e) ** 2 for e in ERR]
    nmax = max(ns)
    gx = lambda i: X0 + 30 + i * (X1 - X0 - 90) / (len(ERR) - 1)
    gy = lambda v: Y1 - v / nmax * (Y1 - Y0 - 14)
    s = [_axes(X0, Y0, X1, Y1)]
    for i, (e, n) in enumerate(zip(ERR, ns)):
        s.append(f'<rect x="{gx(i) - 22:.1f}" y="{gy(n):.1f}" width="44" '
                 f'height="{Y1 - gy(n):.1f}" rx="6" fill="{ACC if e >= 0.03 else WARN}" '
                 f'fill-opacity="0.85"/>')
        s.append(_txt(gx(i), gy(n) - 10, f"{n:,.0f}".replace(",", " "), 13, "800",
                      DARK, anchor="middle"))
        lbl = (f"{e * 100:.1f}".rstrip("0").rstrip(".").replace(".", ",") + " %")
        s.append(_txt(gx(i), Y1 + 22, lbl, 12.5, "700", DARK, op=0.8, anchor="middle"))
    s.append(_txt(X1 - 20, Y1 + 44, "допустимая погрешность E →", 12.5, None, DARK,
                  op=0.65, anchor="end"))
    s.append(_txt(X0 - 8, Y0 - 12, "нужный объём наблюдений n", 12.5, None, DARK, op=0.65))
    s.append(_plate(X0 + 40, Y0 + 6, 430, 66, "#f7fbf8", stroke=ACC))
    s.append(_txt(X0 + 58, Y0 + 30, "n = (Z · σ / E)²  при Z = 1,96 и σ = 0,5", 14.5, "800", DARK))
    s.append(_txt(X0 + 58, Y0 + 54, "погрешность вдвое строже — наблюдений вчетверо больше",
                  13.5, "700", DEEP))
    return _svg(346, ''.join(s))


# ── Полные определения метрик: формула, источник, применение, методика ──────
# Ключ — id метрики из metrics_data.M. Значение — четыре части расхлопа.
# Названия и сокращения — общепринятые в российских банках; те же, что
# в тренажёрах и на слайдах.

DETAIL = {
    # ── Розница · кредитная карта ──
    "app": (
        "Число уникальных заявок на карту за период после дедупликации: "
        "<code>APP = COUNT(DISTINCT заявка)</code> по ключу «клиент + продукт + период». "
        "Разрезы — канал привлечения, регион, сегмент клиента.",
        "Фронтальная система и CRM: заявка регистрируется в момент подачи, статус "
        "меняется по ходу рассмотрения. Данные доступны онлайн, витрина обновляется "
        "ежедневно.",
        "Верх воронки продукта: по нему планируют нагрузку на скоринг и оценивают "
        "работу каналов. Само по себе число заявок ни хорошо, ни плохо — смысл "
        "появляется в связке с одобрением и выдачами.",
        "Считать уникальные заявки, а не строки выгрузки: одна заявка, поданная в "
        "отделении и продублированная в мобильном приложении, — это одна заявка. "
        "Сравнение недель между собой требует поправки на сезонность спроса: конец "
        "месяца и предпраздничные недели дают устойчивый всплеск."),
    "appr": (
        "Доля заявок, по которым принято положительное решение: "
        "<code>Approval&nbsp;Rate = одобренные / рассмотренные × 100 %</code>. "
        "В знаменателе — только рассмотренные заявки; отозванные и незавершённые "
        "клиентом исключаются.",
        "Лог скоринговой системы и автоматизированной системы принятия решений: "
        "по каждой заявке фиксируются версия скоркарты, набранный балл и итог.",
        "Показывает, какой части входящего потока банк готов выдать карту. Вместе "
        "с потоком заявок расчётно определяет выдачи. Резкое движение уровня "
        "одобрения — почти всегда изменение риск-правил или качества входящего "
        "потока, а не «рынок».",
        "Обязательно фиксировать версию скоркарты и дату вступления изменений: "
        "сравнение уровня одобрения до и после смены правил без этой отметки "
        "бессмысленно. Отдельно считают уровень одобрения по каналам — дешёвый "
        "трафик обычно даёт заметно более низкое одобрение."),
    "tat": (
        "Срок доставки карты — распределение величины «дата вручения − дата "
        "выпуска» в днях. Управленческие значения: "
        "<code>медиана</code> и <code>90-й перцентиль</code>, а также доля "
        "доставок в норматив.",
        "Реестр внешней курьерской службы, поступающий по договору регулярной "
        "выгрузкой; ключ связи — номер отправления, сопоставленный с номером "
        "заявки. Без пункта договора о выгрузке метрика существует «по запросу».",
        "Сильнейший опережающий сигнал активации: чем дольше клиент ждёт карту, "
        "тем холоднее он к моменту вручения. Используется в переговорах с "
        "подрядчиком и в решении «где вмешиваться, чтобы поднять активацию».",
        "Смотреть на медиану и 90-й перцентиль, а не на среднее: одна партия, "
        "застрявшая на складе, сдвигает среднее на дни. Недоставленные карты — "
        "цензурированные наблюдения: их нельзя просто выбросить, иначе срок "
        "систематически занижается; корректно учитывать их как «дольше, чем "
        "текущий срок ожидания»."),
    "err": (
        "Доля заявок, содержащих хотя бы одну ошибку оформления: "
        "<code>ER = заявки с ошибкой / все заявки × 100 %</code>. "
        "Дополнительный разрез — структура причин по кодификатору "
        "(адрес, телефон, скан документа, несоответствие данных).",
        "Проверки фронтальной системы и результаты верификации; причина ошибки "
        "фиксируется кодом из справочника, а не свободным текстом сотрудника.",
        "Ранний сигнал, предсказывающий и активацию, и отток: связь здесь — "
        "«предсказывает», а не «определяет», ошибка не входит в формулу "
        "активации, но надёжно предвещает проблему. По структуре причин "
        "выбирают, что исправлять: обучение фронта, форму или проверку данных.",
        "Заявка с тремя ошибками — это одна ошибочная заявка, а не три: числитель "
        "считается по факту наличия хотя бы одной ошибки, структура причин — "
        "отдельной таблицей. Без кодификатора причин метрика не работает: "
        "свободный текст не группируется и обрабатывается вручную."),
    "iss": (
        "Количество выданных карт за период. Расчётно — "
        "<code>ISS = APP × Approval&nbsp;Rate</code>; фактически — число "
        "транзакций выдачи в автоматизированной банковской системе.",
        "Автоматизированная банковская система (АБС): факт выдачи — это проводка "
        "и запись о выпуске карты. CRM показывает «оформлено», АБС — «выдано»; "
        "официальным считается значение АБС.",
        "План-факт продаж продукта, база для расчёта активации и дохода. Первый "
        "расчётный уровень дерева розничного продукта.",
        "Расчётное значение обязательно сверяется с фактом АБС: расхождение "
        "больше одного-двух процентов — это дефект склейки данных (потерянные "
        "ключи, задвоенные выдачи), а не «погрешность». Когорта выдач "
        "определяется по дате выдачи, а не по дате заявки, иначе активация "
        "считается по «плавающей» базе."),
    "act": (
        "Доля карт, по которым прошла первая расходная операция в течение "
        "30 дней от выдачи: "
        "<code>ACT₃₀ = карты с первой операцией ≤ 30 дн. / выданные карты "
        "когорты × 100 %</code>. Расчёт когортный: знаменатель — карты, "
        "выданные в одном месяце.",
        "Витрина транзакций (первая расходная операция) — официальный источник; "
        "флаг активации в CRM — быстрый, но меряет выпуск карты, а не операцию. "
        "Какой из них master-source, фиксируется письменно.",
        "Ключевой показатель продукта: по нему принимают решения о доставке, "
        "коммуникации и приветственных механиках. Ставится в цели продуктовой "
        "команде и показывается на комитете.",
        "Типичный источник расхождений в отчётности: разница между определениями CRM и "
        "витрины устойчиво даёт несколько процентных пунктов. Определение "
        "«операции» должно быть закрыто регламентом: расходная операция, порог "
        "суммы, исключение переводов между своими счетами. Окно 30 дней "
        "фиксированное — «активация с начала года» и «активация за 30 дней» "
        "не сравниваются между собой."),
    "alive": (
        "Доля клиентов портфеля с хотя бы одной операцией за период: "
        "<code>Active = клиенты с операцией за период / клиенты портфеля × "
        "100 %</code>. Период по умолчанию — календарный месяц.",
        "Витрина транзакций и реестр действующих договоров АБС. Пополняется "
        "выдачами и активацией, вымывается оттоком.",
        "База, на которой зарабатывает продукт: доход считается от активных, а не "
        "от выданных. По этой метрике выбирают, во что вкладываться — в доставку, "
        "коммуникацию или оформление, — раньше, чем это увидит доход.",
        "Определение «активности» фиксируется одинаково для всех продуктов "
        "портфеля, иначе доли несравнимы. Считать по когортам выдачи: общая доля "
        "активных растёт просто от роста портфеля и маскирует ухудшение по "
        "свежим когортам."),
    "churn": (
        "Доля клиентов, прекративших операции: "
        "<code>Churn₉₀ = клиенты без операций 90 дней подряд / клиенты на начало "
        "периода × 100 %</code>. В банковской практике различают поведенческий "
        "отток (нет операций) и договорный (закрыт договор).",
        "Витрина транзакций — для поведенческого оттока, статусы договоров АБС — "
        "для договорного. На комитет обычно выносят поведенческий: он приходит "
        "раньше.",
        "Показатель удержания и вход в расчёт жизненной ценности клиента "
        "(<code>LTV = ARPU / Churn</code>). Управляют им выше по дереву — "
        "ошибками оформления, скоростью доставки, качеством обслуживания.",
        "Метрика накопительная и медленная по построению: чтобы увидеть отток за "
        "90 дней, нужно прожить 90 дней, — ускорить деньгами нельзя. Поэтому "
        "в зрелом дереве отток предсказывают ранние сигналы. Считать когортно и "
        "всегда указывать, какой отток имеется в виду: поведенческий и "
        "договорный различаются в разы."),
    "rev": (
        "Доход по продукту за месяц: "
        "<code>Доход = процентный доход + комиссионный доход − стоимость "
        "фондирования</code>. Процентный доход считается от средних остатков "
        "задолженности, комиссионный складывается из межбанковской комиссии "
        "и платы за обслуживание.",
        "Управленческий учёт: отчёт о финансовых результатах в разрезе продукта, "
        "собираемый из проводок АБС по статьям доходов и расходов.",
        "Итог месяца, по которому продукт отчитывается перед бизнес-блоком; база "
        "для план-факта и для расчёта финансового результата продукта.",
        "Запаздывающая метрика: когда она сдвинулась, причина случилась месяцы "
        "назад. Различать начисленный и полученный доход, а также фиксировать "
        "правило аллокации общих расходов — без него доходность продуктов "
        "несравнима между собой."),
    "pnl": (
        "Финансовый результат продукта с учётом стоимости денег во времени: "
        "<code>NPV = Σ CFₜ / (1 + r)ᵗ − IC</code>, где CFₜ — денежный поток "
        "месяца, r — месячная ставка дисконтирования, IC — начальные инвестиции. "
        "В поток входят доход, стоимость привлечения, обслуживание и стоимость "
        "риска (резервы).",
        "Финансовая модель продукта, сверяемая с управленческим учётом по "
        "фактическим доходам и расходам; ставка дисконтирования задаётся "
        "казначейством.",
        "Язык инвестиционного комитета: по нему принимается решение продолжать, "
        "масштабировать или закрывать продукт. Порог из инвестиционных правил "
        "банка — например, положительный NPV к 36-му месяцу.",
        "Без порога показатель неинтерпретируем: по значению NPV не видно, что "
        "делать. Горизонт и ставка должны быть одинаковыми у всех продуктов, "
        "иначе сравнение подменяется выбором допущений. Подробный разбор — в "
        "разделе «NPV: как считается результат инициативы» этого справочника."),

    # ── Уровень 2 розничного кейса: два источника активации ──
    "actA": (
        "Определение то же, что у активации за 30 дней: доля карт с первой "
        "расходной операцией в 30 дней от выдачи. Отличие — источник: "
        "<code>ACT = f(транзакции витрины)</code>, прослеживается до "
        "конкретных операций.",
        "Витрина хранилища данных с зафиксированным владельцем, регламентом "
        "обновления и правилом расчёта; обновление — ночным регламентом.",
        "Официальное значение активации для отчётности и комитета. Дороже флага "
        "CRM в постройке, но не порождает разногласий — а расхождение значений "
        "и есть главная скрытая стоимость данных на уровне комитета.",
        "Витрина должна иметь владельца и SLA обновления; изменение правила "
        "расчёта — только через регламент с датой вступления и пересчётом "
        "истории. Это и есть master-source."),
    "actB": (
        "Доля карт с установленным флагом активации в CRM: "
        "<code>ACT_CRM = карты с флагом / выданные карты × 100 %</code>. "
        "Флаг ставится в момент выпуска карты, а не первой операции.",
        "CRM: поле карточки клиента, доступное онлайн, без ночного регламента.",
        "Оперативный мониторинг: годится, чтобы заметить обвал за сутки. Для "
        "отчётности требует накопительной сверки с витриной.",
        "Систематическое смещение вверх: флаг меряет выпуск, а не операцию, "
        "поэтому значение по CRM устойчиво выше витринного. Главный урок кейса: "
        "быстрая метрика на первом уровне не даёт быстрого решения — сверка на "
        "следующем уровне обесценивает выигрыш."),

    # ── Корпоративный блок · подключение юрлиц ──
    "ts": (
        "Журнал этапов процесса — не число, а таблица событий "
        "<code>(заявка, этап, отметка времени)</code>. Из неё считаются "
        "длительности этапов <code>Δₖ = tₖ₊₁ − tₖ</code> и сквозное время "
        "процесса как сумма по критическому пути.",
        "Система управления бизнес-процессами и CRM, склеенные сквозным ключом "
        "заявки; события выгружаются в витрину процесса.",
        "Единственный источник, по которому видно, на каком этапе теряется время. "
        "На нём строятся время подключения, доля просрочек и разбор узких мест.",
        "Требует сквозного ключа между системами и единого справочника этапов: "
        "если каждая система называет этапы по-своему, журнал не склеивается. "
        "Отметки времени приводятся к одному часовому поясу; события, "
        "проставленные «задним числом», помечаются отдельным признаком."),
    "mn": (
        "Оценка по выборке досье: <code>оценка = среднее (или медиана) по n "
        "разобранным делам</code> с погрешностью <code>±Z·σ/√n</code>. "
        "Точность растёт только как корень из числа разобранных дел.",
        "Ручной разбор досье сотрудниками фронт-офиса, результат — в таблице "
        "Excel; систематического следа процесса при этом не появляется.",
        "Способ получить оценку там, где следа процесса нет. Годится как "
        "разовая диагностика, не годится как регулярная метрика.",
        "Обманчиво дешёвая конфигурация: старт почти бесплатный, но ручной труд "
        "повторяется каждый месяц полновесными операционными расходами. "
        "Выборка должна быть случайной, а не «что под рукой», иначе оценка "
        "смещена; протокол разбора фиксируется, иначе два сотрудника считают "
        "по-разному."),
    "rw": (
        "Доля заявок юрлиц, возвращённых на доработку документов: "
        "<code>RW = заявки хотя бы с одним возвратом / поданные заявки × "
        "100 %</code>. Рядом полезна вторая величина — среднее число возвратов "
        "на заявку.",
        "Статусы заявки в CRM и журнал проверки документов; причина возврата — "
        "код из справочника.",
        "Ранний сигнал длинного подключения: каждый возврат добавляет дни к "
        "сроку и снижает вероятность, что клиент дойдёт до активной работы.",
        "Считать заявки, а не события возврата: заявка с тремя возвратами — "
        "это одна возвращённая заявка. Разрез по причинам показывает, что "
        "исправлять: комплект документов, обучение менеджеров или форму заявки."),
    "t2a": (
        "Сквозное время от подачи заявки до начала операций: "
        "<code>T2A = дата первой операции по счёту − дата подачи заявки</code>. "
        "Управленческие значения — медиана и 90-й перцентиль.",
        "След процесса: журнал этапов workflow (полный) либо ручная выборка "
        "досье (частичный). Дата первой операции — из АБС.",
        "Обещание клиенту и норматив блока; вход в расчёт числа активных "
        "юрлиц и комиссионного дохода.",
        "Существует только при полном следе процесса с общим ключом: без ключа "
        "«время подключения» — это чьё-то мнение. Клиенты, не дошедшие до "
        "операций, — цензурированные наблюдения; их исключение занижает срок. "
        "Смотреть на медиану и 90-й перцентиль: среднее маскирует хвост."),
    "actv": (
        "Число юрлиц, начавших реальные операции по счёту за месяц: "
        "<code>ACTV = COUNT(DISTINCT клиент) с оборотом &gt; 0 за месяц</code>.",
        "АБС: обороты по расчётному счёту, реестр действующих договоров "
        "расчётно-кассового обслуживания.",
        "База комиссионного дохода блока и продолжение скорости подключения "
        "в деньгах: каждый лишний день процесса — это отвал части клиентов "
        "до старта оборота.",
        "Определение активности («оборот больше нуля» либо «не менее N "
        "платежей») фиксируется один раз и не меняется задним числом. "
        "Считать когортно по месяцу подключения — общий рост числа активных "
        "маскирует ухудшение по свежим когортам."),
    "fee": (
        "Комиссионный доход расчётно-кассового обслуживания за месяц: "
        "<code>Fee = Σ комиссий по операциям и обслуживанию</code>. "
        "На клиента — <code>Fee / ACTV</code>.",
        "АБС и управленческий учёт: статьи комиссионных доходов в отчёте о "
        "финансовых результатах блока.",
        "Запаздывающий итог корпоративного блока: план-факт, отчётность перед "
        "бизнес-блоком. Управляют им выше по дереву — скоростью подключения "
        "и активацией.",
        "Различать начисленную и фактически полученную комиссию; фиксировать "
        "правило аллокации расходов на обслуживание. Сравнение месяцев требует "
        "поправки на число рабочих дней."),

    # ── Портфель продуктов: единая методика показателей ──
    "dict": (
        "Словарь определений — регламент, а не число. Измеряется покрытием: "
        "<code>покрытие = показатели с зафиксированным определением / "
        "показатели портфеля × 100 %</code>.",
        "Методологическая функция: документ с владельцем, версией и датой "
        "вступления изменений; определения продублированы в витринах.",
        "Даёт право складывать денежные потоки продуктов и сравнивать продукты "
        "между собой: на портфельном уровне расхождения рождаются в методиках "
        "расчёта, а не в выгрузках.",
        "У словаря должен быть один владелец и регламент изменений с пересчётом "
        "истории. Без версионирования сравнение периодов теряет смысл без "
        "каких-либо признаков ошибки: определение поменялось, а значения "
        "соседних кварталов остались рядом в одной таблице."),
    "adhoc": (
        "Точечные сверки — трудозатраты, а не показатель: "
        "<code>объём = число разборов × средние трудозатраты на разбор</code>.",
        "Протоколы комитетов и переписка: методики выравниваются от случая "
        "к случаю, когда два значения разошлись публично.",
        "Способ дожить до следующего комитета без единой методики. "
        "Накопленного эффекта не даёт.",
        "Почти нулевой вход и постоянные операционные расходы: к следующему "
        "комитету показатели портфеля снова складываются из несравнимых "
        "потоков, и спор начинается с чистого листа."),
    "npvp": (
        "NPV каждого продукта портфеля: "
        "<code>NPV = Σ CFₜ / (1 + r)ᵗ − IC</code>. На кривой читаются три "
        "точки: минимум — выход на прибыльность, точка пересечения нуля — окупаемость, "
        "значение на горизонте — итоговая оценка.",
        "Финансовые модели продуктов, сверяемые с управленческим учётом; "
        "источник активации и дохода — витрины с зафиксированным владельцем.",
        "Сравнение продуктов между собой и вклад продукта в поток портфеля.",
        "Наследует скорость и доверие своих входов: на активации, которой нельзя доверять, "
        "кривая не становится быстрее — она становится спорной. Горизонт и "
        "ставка дисконтирования у всех продуктов одинаковые."),
    "cmp": (
        "Сопоставимость — свойство портфеля: "
        "<code>доля продуктов, показатели которых посчитаны по единой "
        "методике</code>. Проверяется чек-листом: одинаковы ли горизонт, "
        "ставка, состав расходов и определение активации.",
        "Методология портфеля плюс паспорта продуктов в витрине.",
        "Даёт право складывать потоки продуктов в поток портфеля и сравнивать "
        "продукты между собой.",
        "Держится на словаре определений: без него сумма потоков арифметически "
        "считается, но экономически не значит ничего."),
    "alloc": (
        "Решение о перераспределении ресурсов. Критерий — прирост NPV портфеля "
        "на единицу ресурса: <code>ΔNPV портфеля / Δбюджета</code>.",
        "Инвестиционный комитет: решение фиксируется протоколом, входные "
        "данные — кривые продуктов и паспорта.",
        "Итог портфельного уровня: куда переложить бюджет и людей между "
        "продуктами по их вкладу в поток портфеля.",
        "Верно только на сопоставимых и проверенных значениях: ошибка в любом "
        "из входов масштабируется на весь портфель."),

    # ── Портфель инициатив ──
    "fmv": (
        "Витрина финансовых моделей — таблица паспортов инициатив: по каждой "
        "<code>(месяц старта t₀; расходы к старту C₀; месяцев до "
        "прибыльности P; месяцев до окупаемости O)</code>. Из этих четырёх "
        "чисел строится NPV-кривая инициативы.",
        "Финансовые модели команд, загруженные в единую витрину по одному "
        "шаблону; прослеживаемость — до расчётов конкретной команды.",
        "Единственный источник, из которого кривые инициатив складываются в "
        "кривую портфеля без ручной нормализации. На нём считаются минимум "
        "портфеля, окупаемость и NPV на горизонте.",
        "Единая методика четырёх параметров важнее точности каждого: "
        "инициативы сравнимы, если «выход на прибыльность» у всех означает "
        "одно и то же. Витрина версионируется — при пересмотре модели "
        "сохраняется предыдущая редакция паспорта."),
    "mreq": (
        "Те же четыре параметра паспорта инициативы, но собранные из заявок "
        "и презентаций владельцев: <code>(t₀, C₀, P, O)</code> в свободной "
        "форме.",
        "Excel-файлы и слайды владельцев инициатив, присланные к бюджетному "
        "циклу.",
        "Быстрый способ увидеть состав портфеля, когда витрины ещё нет.",
        "Обманчиво дешёвый источник: прибыльность и окупаемость каждый считает "
        "по своей методике, поэтому перед сложением кривых появляется ручная "
        "нормализация — недели на сочленении и спорная сумма. Быстрый источник "
        "не равен быстрому решению."),
    "factp": (
        "План-факт инициатив по месяцам: "
        "<code>отклонение = факт − план</code> по расходам и доходам; "
        "<code>освоение = факт / план × 100 %</code>.",
        "Учётные системы банка: проводки АБС и системы планирования ресурсов "
        "предприятия в разрезе центров финансовой ответственности и статей "
        "затрат.",
        "Сверка модели портфеля с реальностью в месяц закрытия: отклонение "
        "кривой от плана видно сразу, и перестановка стартов инициатив "
        "успевает за реальностью.",
        "Требует соответствия статей затрат учёта и статей финансовой модели — без "
        "этой таблицы соответствия план-факт превращается в спор о том, что "
        "считать расходами инициативы."),
    "statr": (
        "Ежемесячный отчёт владельца инициативы о ходе работ: статус, "
        "процент готовности, риски. Числовой формы, пригодной для сложения, "
        "не имеет.",
        "Presentation-отчёты и письма владельцев инициатив.",
        "Оперативный контроль хода работ при отсутствии план-факта из учёта.",
        "Классическая цена «дешёвого» контроля: «всё по плану» держится до "
        "пересмотра бюджета, отклонение фактических расходов от модели "
        "всплывает с лагом около полутора месяцев — когда сдвигать старты "
        "уже поздно."),
    "npvi": (
        "NPV-кривая инициативы целиком вычисляется из четырёх параметров "
        "паспорта. Накопленная прибыль задаётся параболой через три точки: "
        "<code>y(t₀) = −C₀</code>, вершина в месяце <code>t₀ + P</code>, ноль "
        "в месяце <code>t₀ + O</code>. Месячный поток — приращение "
        "накопленной прибыли, NPV — накопленная сумма приведённых потоков.",
        "Расчёт на данных витрины финансовых моделей или заявок менеджеров; фактический "
        "ход — из план-факта учёта.",
        "Единица сложения портфеля: кривые инициатив суммируются помесячно "
        "в кривую портфеля.",
        "Расчёт второго уровня — наследует скорость и доверие источника "
        "паспортов: на разнородных паспортах кривая не быстрее, а спорнее. "
        "Полная выкладка модели — в разделе «Паспорт инициативы: четыре "
        "параметра, из которых получается кривая»."),
    "npvsum": (
        "Помесячная сумма приведённых потоков всех инициатив: "
        "<code>NPV_портфеля(m) = Σᵢ NPVᵢ(m)</code>. Минимум суммарной кривой — "
        "пик потребности в финансировании, пересечение нуля — окупаемость "
        "портфеля, значение на горизонте — NPV портфеля.",
        "Витрина паспортов инициатив; сложение выполняется в модели портфеля.",
        "Три ответа комитету одной картинкой: сколько денег понадобится и "
        "в каком месяце, когда портфель выйдет в ноль и сколько заработает "
        "за горизонт.",
        "Складывать кривые допустимо, только если паспорта всех инициатив "
        "посчитаны по одной методике и приведены к одной ставке "
        "дисконтирования; иначе сумма арифметически считается, но "
        "экономически не значит ничего."),
    "prio": (
        "Состав и порядок стартов инициатив, максимизирующие NPV портфеля. "
        "Практический критерий отбора — стоимость задержки, делённая на "
        "длительность: <code>CD3 = стоимость задержки / длительность</code>; "
        "проверка — пересчёт суммарной кривой при сдвиге месяцев старта.",
        "Модель портфеля на витрине паспортов плюс фактический ход инициатив "
        "из учёта.",
        "Итоговое решение портфельного уровня: что запускаем сейчас, что "
        "сдвигаем, что не запускаем вовсе.",
        "От перестановки двух инициатив во времени меняются минимум, окупаемость "
        "и доходность всего портфеля, поэтому решение пересчитывается при "
        "каждом сдвиге сроков — и требует одновременно проверенных кривых и "
        "фактического хода, а не отчётов «всё по плану»."),

    # ── Процесс · кредитный конвейер ──
    "pc_apps": (
        "Число кредитных заявок, поступивших в конвейер за день: "
        "<code>COUNT(DISTINCT заявка) по дате подачи</code>. Разрезы — канал, "
        "продукт, регион.",
        "Фронт-офис и каналы самообслуживания; заявка регистрируется в момент "
        "подачи, данные доступны онлайн.",
        "Метрика нагрузки: по ней планируются смены андеррайтеров и видно, "
        "когда конвейер захлёбывается.",
        "Сравнивать дни и недели между собой можно только с поправкой на "
        "сезонность спроса на кредиты и на число рабочих дней."),
    "pc_stp": (
        "Доля заявок, решение по которым принято автоматически, без участия "
        "человека: <code>STP = автоматические решения / все решения × "
        "100 %</code>. STP — straight-through processing, сквозная обработка.",
        "Лог автоматизированной системы принятия решений: по каждой заявке "
        "фиксируется, было ли решение автоматическим или ушло на ручной "
        "андеррайтинг.",
        "Главный рычаг скорости и себестоимости конвейера: автоматическое "
        "решение занимает минуты, ручное — часы и дни. Повышение доли "
        "автоматических решений при неизменном качестве портфеля — типовая "
        "цель процессной команды.",
        "Рост доли автоматических решений сам по себе не достижение: он должен "
        "сопровождаться контролем качества портфеля (уровень просрочки по "
        "когортам). Заявки, отклонённые автоматом, тоже входят в числитель — "
        "это автоматическое решение."),
    "pc_docret": (
        "Доля заявок, возвращённых клиенту за документами: "
        "<code>DocRet = заявки хотя бы с одним дозапросом / заявки в работе × "
        "100 %</code>.",
        "Журнал этапов конвейера и статусы фронт-офиса; причина дозапроса — "
        "код из справочника.",
        "Ранний сигнал качества входа: растут дозапросы — через недели "
        "вырастет срок принятия решения и упадёт доля доведённых до выдачи.",
        "Каждый дозапрос — разрыв процесса: заявка стоит, клиент остывает, "
        "часть клиентов уходит туда, где решение быстрее. Причинам дозапроса "
        "нужен кодификатор, а не свободный текст."),
    "pc_load": (
        "Число заявок, обработанных одним андеррайтером за день: "
        "<code>Load = обработанные заявки / (андеррайтеры × рабочие дни)</code>.",
        "Журнал ручного андеррайтинга: у каждой заявки есть исполнитель и "
        "отметки времени взятия в работу и решения.",
        "Метрика производительности роли, а не оценка конкретного человека. "
        "Вместе с потоком заявок определяет очередь на ручное рассмотрение.",
        "Перегруженный андеррайтинг — самая частая причина расползания срока "
        "решения. Сравнивать команды можно только при одинаковом определении "
        "«обработанной заявки»: отказ по формальному признаку и полноценный "
        "разбор — разная работа."),
    "pc_log": (
        "Журнал этапов конвейера — таблица событий "
        "<code>(заявка, этап, отметка времени, исполнитель)</code>. Из неё "
        "считаются длительности этапов и сквозной срок принятия решения.",
        "Система управления бизнес-процессами, скоринговая система и АБС, "
        "склеенные сквозным ключом заявки; выгрузка — в витрину процесса.",
        "Единственный источник, в котором закрыты разрывы между системами и "
        "видно, на каком этапе теряется время.",
        "Без сквозного ключа «срок решения» существует только как чьё-то "
        "мнение. Нужен единый справочник этапов и приведение отметок времени "
        "к одному часовому поясу; события, проставленные задним числом, "
        "помечаются признаком."),
    "pc_smp": (
        "Оценка по выборке досье: среднее или медиана по n разобранным делам "
        "с погрешностью <code>±Z·σ/√n</code>.",
        "Ручной разбор кредитных досье: сотрудники восстанавливают путь заявки "
        "по документам и переписке.",
        "Разовая диагностика там, где следа процесса нет.",
        "Ручной труд повторяется каждый месяц полновесными операционными "
        "расходами, проверенная картина накапливается неделями, а разрывы "
        "между системами остаются невидимыми: время по этапам не разложить."),
    "pc_tat": (
        "Срок принятия решения (turnaround time): "
        "<code>TAT = время решения − время подачи заявки</code>. "
        "Управленческие значения — медиана и 90-й перцентиль.",
        "След процесса из журнала этапов конвейера либо ручной выборки досье; "
        "отметки времени — из фронт-офиса и системы принятия решений.",
        "Центральная метрика кредитного конвейера: её обещают клиенту "
        "(«решение за один день») и по ней меряют процесс.",
        "Смотреть на медиану и 90-й перцентиль: среднее маскирует хвост долгих "
        "заявок. Заявки, по которым решение ещё не принято, — цензурированные "
        "наблюдения; их исключение занижает срок. Ночные и выходные часы "
        "учитываются по правилу, зафиксированному в регламенте, — календарное "
        "и рабочее время отличаются в разы."),
    "pc_sla": (
        "Доля решений, уложившихся в норматив: "
        "<code>SLA% = решения со сроком ≤ норматива / все решения × 100 %</code>. "
        "Норматив (например, 24 часа) фиксируется соглашением об уровне "
        "сервиса — SLA, service level agreement.",
        "То же распределение срока принятия решения, что и у TAT; норматив — "
        "из регламента продукта.",
        "Управленческая форма срока решения: именно это значение ставят в цели "
        "процессной команде и показывают комитету.",
        "Медиана может выглядеть прилично, а доля решений в срок — падать "
        "из-за хвоста долгих заявок; поэтому обе метрики смотрят вместе. "
        "Норматив и правило учёта нерабочего времени должны быть одинаковыми "
        "во всех отчётах."),
    "pc_out": (
        "Доля одобренных заявок, дошедших до фактической выдачи: "
        "<code>Take-up = выдачи / одобренные заявки × 100 %</code>. "
        "Расчёт когортный — по месяцу одобрения.",
        "АБС (факт выдачи) и лог системы принятия решений (одобрение), "
        "связанные ключом заявки.",
        "Связывает процессные показатели с коммерческим результатом: пока банк "
        "думает, клиент получает решение в другом банке — каждый лишний день "
        "срока решения срезает долю доведённых до выдачи.",
        "Когорта считается по дате одобрения, а не по дате выдачи, иначе "
        "показатель «улучшается» просто от роста потока. Часть отказов "
        "клиента — ценовые: их полезно выделять отдельным кодом."),
    "pc_cost": (
        "Стоимость обработки одной заявки: "
        "<code>Cost per application = расходы конвейера за период / "
        "обработанные заявки</code>. В расходы входят фонд оплаты труда "
        "андеррайтинга, лицензии систем, стоимость внешних проверок.",
        "Управленческий учёт: расходы центра финансовой ответственности "
        "конвейера, отнесённые к числу обработанных заявок.",
        "Запаздывающий итог процессной оси. Вместе с долей решений в срок "
        "образует пару «цена — скорость», по которой сравнивают конвейеры "
        "разных продуктов.",
        "Когда стоимость обработки выросла, причины — доля ручных решений, "
        "дозапросы и загрузка андеррайтинга — случились выше по дереву "
        "неделями раньше. Правило аллокации общих расходов фиксируется, иначе "
        "конвейеры несравнимы."),

    # ── Универсальный конструктор ──
    "u_traffic": (
        "Входящий поток воронки за период: число заявок, визитов или "
        "обращений — <code>COUNT(DISTINCT обращение)</code>.",
        "Фронтальные системы, каналы самообслуживания, системы обращений.",
        "Общая точка старта продуктовых и процессных деревьев.",
        "Сама по себе величина ни хороша, ни плоха: смысл появляется в связке "
        "с конверсией. Требует дедупликации по каналам."),
    "u_conv": (
        "Доля перешедших на следующий шаг воронки: "
        "<code>CR = перешедшие / вошедшие на шаг × 100 %</code>.",
        "События фронтальных систем и CRM, привязанные к идентификатору "
        "клиента или сессии.",
        "Главный управляемый рычаг верха дерева: по конверсии видно, где "
        "именно теряется поток.",
        "Сравнивать конверсию можно только при одинаковом определении шага и "
        "одинаковой базе; при малых числах — обязательно смотреть абсолютную "
        "базу, а не только проценты."),
    "u_tat": (
        "Сквозное время процесса от входа до результата: "
        "<code>время завершения − время входа</code>; управленческие "
        "значения — медиана и 90-й перцентиль.",
        "След процесса с общим ключом между системами.",
        "Норматив процесса и обещание клиенту.",
        "Существует только при полном следе процесса: без общего ключа "
        "«время» — это чьё-то мнение. Незавершённые случаи — цензурированные "
        "наблюдения."),
    "u_err": (
        "Доля ошибок или возвратов на доработку: "
        "<code>ER = случаи с ошибкой / все случаи × 100 %</code>.",
        "Проверки систем и журнал возвратов; причина — код из справочника.",
        "Универсальный ранний сигнал деградации качества входа.",
        "Требует кодификатора причин, иначе обрабатывается вручную. Считать "
        "случаи, а не события ошибки."),
    "u_ops": (
        "Число операций на сотрудника в день: "
        "<code>операции / (сотрудники × рабочие дни)</code>.",
        "Журналы операционных систем с признаком исполнителя.",
        "Ключевая метрика процессной оси: производительность роли, а не "
        "человека.",
        "Сравнивается между командами только при одинаковом определении "
        "«операции». Использование метрики как оценки конкретного сотрудника "
        "быстро приводит к искажению данных на входе."),
    "u_nps": (
        "Индекс лояльности: <code>NPS = доля промоутеров − доля "
        "критиков</code>. Клиент отвечает на вопрос о готовности "
        "рекомендовать по десятибалльной шкале; 9–10 — промоутеры, 7–8 — "
        "нейтральные, 0–6 — критики. Значение — от −100 до +100.",
        "Система опросов: рассылки, опрос после обслуживания, виджет в "
        "приложении.",
        "Показатель отношения к продукту в целом; используется как "
        "опережающий сигнал оттока.",
        "Самая частая поломка — репрезентативность: индекс, собранный по "
        "дошедшим до конца обслуживания, систематически завышен, потому что "
        "недовольные до опроса не доходят. Всегда указывать размер выборки и "
        "долю ответивших; сравнивать значения между каналами и странами без "
        "оговорок нельзя."),
    "u_csat": (
        "Индекс удовлетворённости: <code>CSAT = доля положительных ответов / "
        "все ответы × 100 %</code>. Оценка ставится сразу после контакта по "
        "пятибалльной или двоичной шкале.",
        "Опрос сразу после взаимодействия: в чате, в приложении, по "
        "смс-ссылке.",
        "Быстрая обратная связь по конкретному эпизоду обслуживания.",
        "Дешевле и быстрее индекса лояльности, но локальнее: меряет эпизод, "
        "а не отношение к продукту. Доля ответивших так же критична, как и "
        "у индекса лояльности."),
    "u_cac": (
        "Стоимость привлечения одного клиента: "
        "<code>CAC = расходы на привлечение за период / число привлечённых "
        "клиентов за период</code>. В расходы входят реклама, комиссия "
        "партнёрам и работа продаж.",
        "Маркетинговый бюджет из управленческого учёта и данные о "
        "привлечённых клиентах из CRM.",
        "Оценка эффективности каналов и вход в юнит-экономику.",
        "Смысл появляется только в паре с жизненной ценностью клиента: "
        "устойчивая экономика требует <code>CAC &lt; LTV</code>. Считать "
        "по каналам и когортам; относить расходы к периоду привлечения, "
        "а не к периоду оплаты счёта."),
    "u_price": (
        "Цена или тариф продукта — управляемый параметр; производные "
        "величины: средняя эффективная ставка, средний тариф по портфелю.",
        "Тарифный справочник и параметры договора в АБС.",
        "Самый быстрый рычаг монетизации.",
        "Каждое ценовое решение тянет за собой пересчёт конверсии и оттока: "
        "изолированный рост цены почти всегда компенсируется падением потока, "
        "и проверять это нужно экспериментом, а не мнением."),
    "u_iss": (
        "Результат воронки за период: "
        "<code>сделки = поток × конверсия</code>; факт — из учётной системы.",
        "АБС или учётная система продукта.",
        "Первый расчётный уровень большинства деревьев; план-факт продаж.",
        "Расчётное значение сверяется с фактом: расхождение больше одного-двух "
        "процентов — дефект склейки данных."),
    "u_mau": (
        "Число уникальных клиентов с операциями за месяц: "
        "<code>MAU = COUNT(DISTINCT клиент) за 30 дней</code>. Дневной аналог "
        "— DAU; отношение <code>DAU / MAU</code> показывает частоту "
        "возвращения.",
        "Витрина событий и транзакций.",
        "Накопительная метрика базы: пополняется новыми сделками, вымывается "
        "оттоком.",
        "Определение «активности» фиксируется и не меняется задним числом. "
        "Общий рост числа активных маскирует ухудшение по свежим когортам — "
        "смотреть когортно."),
    "u_churn": (
        "Доля клиентов, прекративших пользоваться продуктом за период: "
        "<code>Churn = ушедшие за период / клиенты на начало периода × "
        "100 %</code>. Обратная величина — коэффициент удержания "
        "<code>CRR = 100 % − Churn</code>.",
        "Витрина транзакций (поведенческий отток) и статусы договоров "
        "(договорный отток).",
        "Показатель удержания и знаменатель в оценке жизненной ценности "
        "клиента.",
        "Медленная по построению: нужно прожить горизонт наблюдения, поэтому "
        "в зрелых деревьях отток предсказывают ранние сигналы. Всегда "
        "указывать период и вид оттока."),
    "u_aov": (
        "Средняя сумма операции: <code>AOV = оборот / число операций</code>. "
        "Родственная величина — средний доход на клиента "
        "<code>ARPU = доход / число клиентов</code>.",
        "Витрина транзакций.",
        "Вход в расчёт дохода и жизненной ценности клиента.",
        "Чувствителен к выбросам: одна крупная сделка двигает среднее — рядом "
        "со средним чеком всегда полезна медиана и 90-й перцентиль."),
    "u_ltv": (
        "Жизненная ценность клиента — доход за всё время его жизни в "
        "продукте. Практическая формула: "
        "<code>LTV = ARPU / Churn</code> либо развёрнуто "
        "<code>LTV = средний чек × частота покупок × срок жизни</code>. "
        "Для длинных продуктов считается дисконтированная версия.",
        "Витрина транзакций и история договоров; для прогнозной оценки — "
        "модель на исторических когортах.",
        "Делает стоимость привлечения интерпретируемой: инициатива "
        "экономически состоятельна, пока <code>CAC &lt; LTV</code>.",
        "Дорогая и медленная в надёжном расчёте: нужна история достаточной "
        "длины. Прогнозная и фактическая ценность клиента — разные величины, "
        "их нельзя смешивать в одной таблице. Всегда указывать горизонт "
        "расчёта."),
    "u_rev": (
        "Выручка или доход за период: <code>Σ поступлений по продукту</code> "
        "в разрезе статей управленческого учёта.",
        "Управленческий учёт: отчёт о финансовых результатах в разрезе "
        "продукта.",
        "Итог периода, по которому продукт отчитывается.",
        "Запаздывающая метрика: планы ставятся по ней, а управление "
        "происходит выше по дереву — опережающими метриками."),
    "u_mrr": (
        "Повторяющаяся месячная выручка: "
        "<code>MRR = активные клиенты × средний платёж</code>. "
        "Раскладывается на прирост от новых, расширение, сжатие и потери "
        "от оттока.",
        "Биллинг и учётная система подписок или обслуживания.",
        "Более предсказуемая форма дохода: по ней строят прогноз и оценивают "
        "устойчивость продукта.",
        "Разовые платежи в этот показатель не входят — их учитывают "
        "отдельно, иначе прогноз завышается."),
    "u_roi": (
        "Возврат инвестиций: "
        "<code>ROI = (доход − затраты) / затраты × 100 %</code>. "
        "Показывает, какой процент от вложенных средств вернулся прибылью.",
        "Управленческий учёт и финансовая модель инициативы.",
        "Итоговая инвестиционная метрика; удобна для быстрого сравнения "
        "небольших инициатив.",
        "Сравнивать по ней можно только инициативы с одинаковым горизонтом и "
        "одинаковой базой расчёта затрат. Стоимость денег во времени "
        "показатель не учитывает — для длинных инициатив корректнее NPV."),
    "u_npv": (
        "Чистая приведённая стоимость: "
        "<code>NPV = Σ CFₜ / (1 + r)ᵗ − IC</code>, где CFₜ — денежный поток "
        "периода t, r — ставка дисконтирования, IC — начальные инвестиции. "
        "Родственный показатель — внутренняя норма доходности IRR: ставка, "
        "при которой NPV обращается в ноль.",
        "Финансовая модель инициативы, сверяемая с управленческим учётом; "
        "ставка дисконтирования — из казначейства.",
        "Язык инвестиционного комитета: по NPV сравнивают инициативы между "
        "собой и с альтернативой «не делать».",
        "Порог превращает значение показателя в решение: например, положительный NPV к "
        "36-му месяцу. Горизонт и ставка у сравниваемых инициатив должны "
        "совпадать. Полный разбор — в разделе «NPV: как считается результат "
        "инициативы» этого справочника."),
}

_TYPE = {
    "leading": ("опережающая", "#20BA72"),
    "calc": ("расчётная", "#2E6BB8"),
    "lagging": ("запаздывающая", "#D9822B"),
}

# Группы справочника повторяют кейсы тренажёра «Дерево метрик»: участник,
# пришедший по кнопке «?», попадает в знакомый ему раздел.
_GROUPS = [
    ("Розница · кредитная карта",
     "Дерево метрик розничного продукта: от заявок и доставки — к финансовому результату "
     "продукта. Две последние метрики группы — альтернативные источники "
     "активации из второго уровня кейса.",
     ["app", "appr", "tat", "err", "iss", "act", "alive", "churn", "rev", "pnl",
      "actA", "actB"]),
    ("Корпоративный блок · подключение юрлиц",
     "Процесс подключения юридического лица: от следа процесса — к "
     "комиссионному доходу блока.",
     ["ts", "mn", "rw", "t2a", "actv", "fee"]),
    ("Процесс · кредитный конвейер",
     "Процессная ось глазами руководителя: доля автоматических решений и "
     "дозапросы документов определяют срок принятия решения, срок — долю "
     "решений в норматив, а скорость — коммерческий результат.",
     ["pc_apps", "pc_stp", "pc_docret", "pc_load", "pc_log", "pc_smp",
      "pc_tat", "pc_sla", "pc_out", "pc_cost"]),
    ("Портфель инициатив",
     "Портфельный уровень: паспорта инициатив превращаются в NPV-кривые, "
     "кривые складываются в кривую портфеля, а из неё следует порядок стартов.",
     ["fmv", "mreq", "factp", "statr", "npvi", "npvsum", "prio"]),
    ("Портфель продуктов · единая методика показателей",
     "Показатели уровня продуктового портфеля: они складываются между собой "
     "только тогда, когда посчитаны по одному словарю определений.",
     ["dict", "adhoc", "npvp", "cmp", "alloc"]),
    ("Универсальный конструктор",
     "Метрики свободного режима — те же понятия в отраслевой нотации; их "
     "хватает, чтобы собрать дерево почти любого подразделения.",
     ["u_traffic", "u_conv", "u_tat", "u_err", "u_ops", "u_nps", "u_csat", "u_cac",
      "u_price", "u_iss", "u_mau", "u_churn", "u_aov", "u_ltv", "u_rev", "u_mrr",
      "u_roi", "u_npv"]),
]

# Страховка от рассинхронизации: если в metrics_data появится метрика, которую
# ещё не разложили по кейсам, она всё равно попадёт в справочник — иначе
# кнопка «?» тренажёра приведёт на несуществующий якорь.
_LISTED = {mid for _, _, ids in _GROUPS for mid in ids}
_REST = [mid for mid in M if mid not in _LISTED]
if _REST:
    _GROUPS.append(("Прочие метрики справочника",
                    "Метрики, добавленные в конструктор последними.", _REST))


def _metric_card(mid):
    m = M[mid]
    tname, tcolor = _TYPE[m["type"]]
    det = ""
    if mid in DETAIL:
        formula, source, use, method = DETAIL[mid]
        det = ('<details class="more" style="margin:14px 0 0">'
               '<summary>Полное определение: формула, источник, методика</summary>'
               f'<p><b>Как рассчитывается.</b> {formula}</p>'
               f'<p><b>Откуда берётся в банке.</b> {source}</p>'
               f'<p><b>Как используется в управлении.</b> {use}</p>'
               f'<p><b>Стандартная методика и типовые оговорки.</b> {method}</p>'
               '</details>')
    return (f'<div class="card" id="m-{mid}">'
            f'<h4>{m["name"]} <span class="sub" style="font-weight:400">· {m["abbr"]}</span> '
            f'<span style="font-size:12px;color:{tcolor};border:1px solid {tcolor};'
            f'border-radius:10px;padding:1px 8px;vertical-align:middle">{tname}</span></h4>'
            f'<p>{m["long"]}</p>'
            f'<p class="sub" style="margin:0">Паспорт сбора: CAPEX {m["capex"]} т₽ · '
            f'OPEX {m["opex"]} т₽/мес · TTE ~{m["tte"]} дн</p>'
            f'{det}</div>')


_guide = "".join(
    f'<h3 style="margin:32px 0 6px">{title}</h3>'
    f'<p class="sub" style="margin:0 0 14px">{intro}</p>'
    + "".join(_metric_card(mid) for mid in ids)
    for title, intro, ids in _GROUPS)

_N_DETAILS = len(DETAIL)
_N_FIGS = 20


BODY = f"""
<header><div class="wrap">
  <div class="eyebrow">Аналитика 360 · справочник курса</div>
  <h1>Метрики и качество данных</h1>
  <p class="lead">Полный справочник практической части: по каждой метрике —
     определение, формула расчёта, источник данных в банке, управленческое
     применение и стандартная методика; дерево метрик, экономика данных,
     NPV и паспорт инициативы, интегральная оценка качества данных, правила
     эксперимента. Каждое значение, которое встречается в тренажёрах и
     на занятиях, разобрано здесь до формулы и источника.</p>
  <div class="meta">
    <span class="chip">Метрик в справочнике <b>{len(M)}</b></span>
    <span class="chip">Полных определений <b>{_N_DETAILS}</b></span>
    <span class="chip">Иллюстраций <b>{_N_FIGS}</b></span>
  </div>
</div></header>

<section><div class="wrap">
<div class="toc">
<b>Содержание</b>
<ol>
  <li><a href="#card">Как читать паспорт метрики</a></li>
  <li><a href="#tree">Дерево метрик: опережающие и запаздывающие</a></li>
  <li><a href="#eco">Экономика данных: TTE, TCO и стоимость задержки</a></li>
  <li><a href="#npv">NPV: как считается результат инициативы</a></li>
  <li><a href="#passport">Паспорт инициативы и портфель</a></li>
  <li><a href="#quality">Качество данных и интегральная оценка</a></li>
  <li><a href="#experiment">Эксперимент и накопление данных</a></li>
  <li><a href="#guide">Справочник метрик: полные определения</a></li>
  <li><a href="#src">Источники</a></li>
</ol>
</div>
<p class="sub" style="margin-top:14px">Страница читается двумя способами.
Подряд — как учебник экономики данных: от паспорта метрики к дереву, деньгам
и качеству. По ссылке — как справочник: кнопка «?» на карточке метрики
в тренажёре открывает именно её определение в разделе
<a href="#guide">«Справочник метрик: полные определения»</a>.</p>
</div></section>

<section id="card"><div class="wrap">
<h2><span class="num">1</span>Как читать паспорт метрики</h2>
<p>В курсе слово «паспорт» используется дважды, и это два разных документа.
<b>Паспорт метрики</b> отвечает на вопрос «во что обходится этот показатель»: роль
метрики в дереве, стоимость сбора и срок, за который значению можно верить.
<b>Паспорт инициативы</b> отвечает на вопрос «во что обходится этот проект»:
четыре параметра, из которых строится денежная кривая, — он разобран в разделе
<a href="#passport">«Паспорт инициативы и портфель»</a>. Здесь речь о первом.</p>

<p><b>Роль в дереве.</b>
<span style="color:#20BA72"><b>Опережающая метрика</b></span> показывает, что
произойдёт в будущем, если продолжать действовать как сейчас: она собирается
из первичных событий и меняется раньше результата — по ней управляют.
<span style="color:#2E6BB8"><b>Расчётная метрика</b></span> вычисляется из
других метрик по формуле и наследует их скорость и их дефекты.
<span style="color:#D9822B"><b>Запаздывающая метрика</b></span> констатирует
результат прошлых действий: когда она сдвинулась, влиять уже поздно —
по ней ставят план и отчитываются{ref_metrics("leading-lagging")}.</p>

<p><b>Экономика сбора.</b> Три числа на жёлтом бейдже карточки — это и есть
паспорт сбора метрики.</p>
<div class="scroll"><table>
<tr><th>Параметр</th><th>Полное определение</th><th>Как получить значение</th></tr>
<tr><td><b>CAPEX</b>, т₽</td>
    <td>Единоразовые затраты, чтобы данные вообще появились: доработка договора
        с внешним поставщиком, ключи связи между системами, витрина,
        кодификатор причин, регламент расчёта</td>
    <td>Оценка проекта постройки: работы ИТ и методологии, лицензии,
        доработка договора. Разовая сумма, не повторяется каждый месяц</td></tr>
<tr><td><b>OPEX</b>, т₽/мес</td>
    <td>Периодические затраты на сбор, обработку и поддержание доверия к значению:
        контроль полноты, ручной разбор, сверки между системами, поддержка
        витрины</td>
    <td>Трудозатраты команды в часах × стоимость часа + стоимость
        инфраструктуры и внешних выгрузок за месяц</td></tr>
<tr><td><b>TTE</b>, дни</td>
    <td>Time-to-evidence — время до проверенного значения: сколько ждать, пока
        значению можно верить. Складывается из времени постройки источника,
        накопления нужного объёма наблюдений и горизонта самой метрики</td>
    <td>Срок постройки + срок набора выборки + горизонт метрики. Отток за
        90 дней не узнать быстрее, чем за 90 дней</td></tr>
</table></div>

<p>Из этих трёх чисел собираются две производные величины, на которых
строится вся экономика данных: <b>совокупная стоимость владения</b> метрикой
и <b>время до проверенного решения</b> по всему дереву. Обе разобраны в разделе
<a href="#eco">«Экономика данных: TTE, TCO и стоимость задержки»</a>.</p>

<div class="card acc">
<p><b>Числа в кейсах учебные.</b> Порядок величин типовой для банка, но
в вашем подразделении паспорт каждой метрики заполняется своими значениями —
это часть работы с картой источников, которая собирается в
<a href="trainer_map.html">тренажёре «Карта источников данных»</a> и становится
домашним артефактом A1.</p>
</div>
</div></section>

<section id="tree"><div class="wrap">
<h2><span class="num">2</span>Дерево метрик: опережающие и запаздывающие</h2>
<p>Метрики подразделения — не список, а дерево. Внизу дерева стоят опережающие
сигналы, которые собираются из первичных событий; выше — расчётные уровни,
где сигналы превращаются в показатели продукта или процесса; на вершине —
запаздывающий финансовый итог. Дерево метрик отвечает на вопрос, которым
руководитель начинает любой разбор: «доход упал — где именно вмешиваться».
Ответ всегда лежит ниже той метрики, по которой проблема замечена.</p>

{_slide_fig("s1b2_tree",
            "Дерево метрик розничного продукта. Слева направо: "
            "опережающие сигналы (заявки, одобрение, срок доставки, ошибки "
            "оформления) → расчётные уровни (выдачи, активация, активные клиенты, "
            "отток) → запаздывающий итог (доход, финансовый результат продукта). "
            "Сплошная стрелка — связь «определяет», пунктирная — «предсказывает».")}

<h3 id="tree-links">Две разные связи: «определяет» и «предсказывает»</h3>
<p>В дереве встречаются связи двух типов, и путать их дорого.</p>
<div class="card">
<h4>Связь «определяет»</h4>
<p>Метрика-вход входит в формулу метрики-выхода. Выдачи определяются заявками
и одобрением: <code>выдачи = заявки × одобрение</code>. Такую связь можно
проверить арифметикой: если перемножить входы и получить не то, что показывает
учётная система, значит, где-то потеряны или задвоены записи. Управление по
такой связи предсказуемо: изменение входа даёт расчётное изменение выхода.</p>
</div>
<div class="card">
<h4>Связь «предсказывает»</h4>
<p>Метрика надёжно предвещает другую, не участвуя в её расчёте. Ошибки
оформления не входят в формулу оттока, но рост доли ошибок устойчиво
предшествует росту оттока; падение индекса лояльности предсказывает отток
раньше, чем отток становится виден{ref_metrics("leading-lagging")}. Такая
связь проверяется не арифметикой, а данными: сопоставлением рядов со сдвигом
во времени. И она требует осторожности — совпадение движения двух рядов ещё
не означает, что один вызывает другой; типовые ловушки такого вывода разобраны
в разделе <a href="longread.html#e2">«Общая причина»</a> лонгрида
«Пять ошибок вывода».</p>
</div>

<h3 id="tree-classes">Три класса метрик в дереве</h3>
<p>Метрики продукта принято делить на три класса, и каждое дерево содержит
метрики всех трёх — просто на разных уровнях.</p>
<div class="scroll"><table>
<tr><th>Класс</th><th>Что показывает</th><th>Примеры из справочника</th></tr>
<tr><td><b>Метрики качества опыта</b></td>
    <td>Насколько продукт удобен и полезен клиенту: удовлетворённость,
        лояльность, вовлечённость, удержание</td>
    <td><a href="#m-u_nps">индекс лояльности NPS</a>,
        <a href="#m-u_csat">удовлетворённость CSAT</a>,
        <a href="#m-u_mau">активные клиенты MAU</a>,
        <a href="#m-u_churn">отток</a></td></tr>
<tr><td><b>Метрики управленческого учёта</b></td>
    <td>Насколько экономично управляется продукт: сколько стоит клиент,
        сколько он приносит, во что обходится процесс</td>
    <td><a href="#m-u_cac">стоимость привлечения CAC</a>,
        <a href="#m-u_ltv">ценность клиента LTV</a>,
        <a href="#m-u_aov">средний чек</a>,
        <a href="#m-pc_cost">стоимость обработки заявки</a></td></tr>
<tr><td><b>Инвестиционные метрики</b></td>
    <td>Насколько продукт привлекателен как вложение денег: сколько можно
        заработать и когда вернутся вложения</td>
    <td><a href="#m-u_npv">NPV</a>, <a href="#m-u_roi">ROI</a>,
        <a href="#m-npvi">NPV-кривая инициативы</a>,
        <a href="#m-npvsum">NPV портфеля</a></td></tr>
</table></div>
<p>Практический смысл деления простой. Метрики качества опыта движутся первыми
и стоят дёшево — это кандидаты в опережающие. Метрики управленческого учёта
переводят опыт в деньги. Инвестиционные метрики стоят на вершине и всегда
запаздывают: их считают, чтобы принять решение о вложениях, а не чтобы
управлять неделей.</p>

<h3 id="tree-ensemble">Ансамбль: время решения — свойство всего дерева</h3>
<p>Время до проверенного решения — свойство не отдельной метрики, а всей
композиции, которую руководитель собрал. Расчётный уровень готов не раньше
самого медленного из своих входов, а некоторые сочленения добавляют
собственное время: накопительную сверку между системами, стабилизацию
значения, сезонный цикл. Формально время ансамбля считается по критическому
пути дерева.</p>
{_F("TTE(ансамбль) = max<sub>путь</sub> ( Σ TTE узлов пути + Σ времени сочленений )",
    "критический путь — самая длинная по времени цепочка от первичных данных "
    "до метрики решения")}
<p>Отсюда главное скрытое ограничение конфигураций данных: <b>быстрая метрика
на первом уровне не гарантирует быстрого решения</b>. Флаг активации в CRM
доступен в реальном времени, но меряет выпуск карты, а не операцию, — и любой расчёт на нём требует
накопительной сверки с витриной, из-за которой весь ансамбль оказывается
медленнее, чем на «дорогом» источнике. Это ровно тот случай, который
<a href="trainer_tree.html">тренажёр «Дерево метрик»</a> показывает во втором
уровне розничного кейса: дерево собрано верно при обоих источниках, а
эффективность конфигураций различается в разы.</p>

<div class="card acc">
<p><b>Соберите дерево самостоятельно.</b> В
<a href="trainer_tree.html">тренажёре «Дерево метрик»</a> четыре банковских
кейса — розница, корпоративный блок, кредитный конвейер и портфель инициатив,
каждый в двух уровнях: собрать дерево и выбрать конфигурацию источников.
Замер внизу тренажёра считает TTE ансамбля по критическому пути и совокупную
стоимость владения конфигурацией; кнопка «?» на карточке метрики открывает её
определение из раздела <a href="#guide">«Справочник метрик»</a>.</p>
</div>

<p>Как дерево выводится из вопроса руководителя и почему план ставится по
запаздывающим, а управление идёт по опережающим, разобрано в разделе
<a href="longread_data.html#d6">«Опережающие и запаздывающие: дерево
метрик»</a> лонгрида «Роль данных».</p>
</div></section>

<section id="eco"><div class="wrap">
<h2><span class="num">3</span>Экономика данных: TTE, TCO и стоимость задержки</h2>
<p>Данные не бесплатны, и это не фигура речи: у каждого показателя в управленческом
отчёте есть цена постройки, цена содержания и срок, за который ему начинают
верить. Экономика данных отвечает на вопрос, который на комитете звучит как
«давайте посчитаем ещё и это»: сколько будет стоить «ещё и это» и когда оно
появится.</p>

<h3 id="eco-tte">Time-to-evidence: время до проверенного значения</h3>
<p><b>Time-to-evidence (TTE)</b> — срок от решения «нужна такая метрика» до
момента, когда её значению можно верить настолько, чтобы принять по нему
решение. TTE складывается из трёх слагаемых, и сокращать их деньгами можно
по-разному.</p>
{_F("TTE = T<sub>постройки</sub> + T<sub>набора выборки</sub> + T<sub>горизонта метрики</sub>",
    "деньгами и людьми сжимаются первые два слагаемых; горизонт метрики "
    "не сжимается ничем")}
<p>Срок постройки — это доработка договора, ключи связи, витрина. Срок набора
выборки зависит от притока наблюдений и требуемого объёма. Горизонт метрики —
свойство самой метрики: отток за 90 дней требует 90 дней, полный сезонный
цикл — года. Разбор двух сжимаемых и одной несжимаемой части — в разделе
<a href="#experiment">«Эксперимент и накопление данных»</a>.</p>

<h3 id="eco-tco">Совокупная стоимость владения (Total Cost of Ownership)</h3>
<p><b>Совокупная стоимость владения (Total Cost of Ownership, TCO)</b> — полная
сумма затрат на данные за весь срок владения ими, а не только цена постройки.
В неё входят единоразовые вложения, все периодические расходы на горизонте
и затраты на вывод источника из эксплуатации. Смысл показателя в том, что он
делает сравнимыми варианты с разной структурой затрат: «дорого построить и
дёшево держать» против «почти бесплатно начать и оплачивать ручную обработку
каждый месяц».</p>
{_F("TCO(H) = Σ CAPEX + Σ<sub>t=1..H</sub> OPEX<sub>t</sub> + затраты на вывод из эксплуатации",
    "H — горизонт владения в месяцах; в кейсах курса горизонт равен сроку пилота")}
<p>В упрощённом виде, которым пользуются кейсы курса, периодические расходы
считаются постоянными, а вывод из эксплуатации не учитывается — тогда формула
превращается в ту, что стоит в замере тренажёра:</p>
{_F("TCO = Σ CAPEX + H × Σ OPEX")}
{_more("Что именно входит в каждую часть совокупной стоимости владения",
       "<p><b>Единоразовые вложения (CAPEX).</b> Проектирование и постройка "
       "витрины; доработка систем-источников; настройка ключей связи между "
       "системами; создание кодификаторов и справочников; доработка договора "
       "с внешним поставщиком данных; закупка лицензий; первичная историческая "
       "загрузка и её сверка.</p>"
       "<p><b>Периодические расходы (OPEX).</b> Инфраструктура хранения и "
       "расчёта; сопровождение регламентных загрузок и разбор инцидентов; "
       "контроль полноты и качества; регулярные сверки между системами; ручной "
       "разбор случаев там, где автоматики нет; поддержка справочников и "
       "методики; обучение пользователей витрины.</p>"
       "<p><b>Затраты на вывод из эксплуатации.</b> Перенос истории, архивация, "
       "переключение отчётности на новый источник. В кейсах курса они не "
       "считаются, но в реальном решении о замене источника это ощутимая "
       "часть суммы.</p>"
       "<p><b>Скрытая часть.</b> Отдельно стоит стоимость расхождений между источниками: "
       "часы руководителей, потраченные на выяснение, почему в двух отчётах "
       "разные значения одной метрики. Формально она не попадает ни в одну "
       "статью бюджета, но именно она делает дешёвый источник дорогим — "
       "и именно её убирает зафиксированный master-source.</p>"
       "<p><b>Дисконтированный вариант.</b> Если горизонт владения длинный, "
       "периодические расходы корректно приводить к сегодняшнему дню тем же "
       "способом, что и денежные потоки инициативы: "
       "<code>TCO = Σ CAPEX + Σ OPEX<sub>t</sub> / (1 + r)<sup>t</sup></code>. "
       "На горизонте пилота в несколько месяцев поправка мала, поэтому "
       "в кейсах она опущена.</p>")}
<p>Практический вывод из формулы виден на графике: конфигурация с почти
нулевым входом и ручным трудом сравнивается по совокупной стоимости владения
с «дорогой» витриной за считанные месяцы, а дальше проигрывает ей уже
безнадёжно — и при этом всё это время не даёт следа процесса.</p>
{fig(tco_stack(), "Совокупная стоимость владения двух конфигураций на горизонте владения. Дорогой старт с дешёвой эксплуатацией против дешёвого старта с ручным разбором: точка пересечения — месяц, после которого «дешёвая» конфигурация становится дороже.")}

<h3 id="eco-cod">Стоимость задержки (Cost of Delay) и профили потерь</h3>
<p><b>Стоимость задержки (Cost of Delay)</b> — денежная величина потерь от
того, что решение принято позже, чем могло быть. Это способ выразить влияние
времени на результат: каждая неделя, пока показателю нельзя доверять, — это неделя,
когда решение либо не принимается, либо принимается без оснований. Райнертсен
называет стоимость задержки главной величиной, которую стоит посчитать
в продуктовой работе{ref_metrics("cod")}.</p>
<p>Потери от задержки накапливаются по-разному, и форма накопления меняет
приоритет задачи сильнее, чем её размер. Где-то каждый месяц стоит одинаково;
где-то до контрольной даты потерь нет вовсе, а после неё наступает штраф;
технический долг накапливается незаметно, а затем проявляется скачкообразно.</p>
{fig(cod_profiles_lg(), "Шесть профилей стоимости задержки: по горизонтали — время ожидания, по вертикали — накопленные потери. Форма кривой зависит от типа решения и определяет, что делать первым.")}
<p>Сравнивать варианты принято по стоимости задержки, делённой на
длительность, — этот критерий называется CD3 (Cost of Delay Divided by
Duration); в методологии SAFe тот же принцип носит название WSJF, weighted
shortest job first{ref_metrics("wsjf")}.</p>
{_F("CD3 = стоимость задержки / длительность",
    "чем быстрее и дешевле вариант доводит до проверенного результата, тем он выгоднее")}

<h3 id="eco-e">Критерий курса: одна формула</h3>
<div class="card acc">
<p>В кейсах ценность решения зафиксирована и одинакова для всех конфигураций,
поэтому сравнение сводится к знаменателю CD3 — к тому, во что обходится
доведение решения до проверенного состояния.</p>
{_F("E = 1 / (TTE × TCO)", "«скорость проверки решения на рубль»")}
<p>Здесь <b>TTE</b> — время всего ансамбля по критическому пути собранного
дерева, <b>TCO</b> — совокупная стоимость владения конфигурацией за горизонт
пилота. Эффективность, которую показывает
<a href="trainer_tree.html">тренажёр «Дерево метрик»</a>, — это отношение E
вашей конфигурации к E лучшей конфигурации кейса, выраженное в процентах.
Сто процентов означает, что дешевле и быстрее в этом кейсе собрать нельзя.</p>
</div>
<p>Тот же компромисс удобно видеть на плоскости «время × стоимость», где каждая
метрика занимает собственную точку. Часть конфигураций образует <b>фронт
Парето</b>: улучшить их сразу по обеим осям невозможно, и выбор между ними —
управленческое решение о том, чем платить, деньгами или сроком. Остальные
конфигурации лежат выше и правее фронта: для каждой из них существует
альтернатива, которая одновременно дешевле и быстрее. Отдельно стоит ручной
сбор: низкий вход не компенсирует ежемесячного OPEX, поэтому такие точки
проигрывают сразу по обеим осям.</p>
{fig(tradeoff_scatter_lg(), "Компромисс TTE × TCO на одиннадцати метриках трёх кейсов: по горизонтали — время до проверенного значения, по вертикали — совокупная стоимость владения за три месяца. Сплошная линия — фронт Парето, пунктир — изолиния равной интегральной оценки: точки на ней равноценны, всё, что ниже и левее, — выгоднее. Обведены две конфигурации с наивысшей интегральной оценкой.")}
<p>Наконец, стоит помнить, что цена плохих данных материальна и без всяких
моделей: по оценке Gartner организация теряет на некачественных данных
в среднем 12,9 млн долларов в год{ref_metrics("gartner-dq")}. А актуальность
данных — не удобство, а измеряемая характеристика качества: в модели
ISO/IEC 25012 она входит в число ключевых характеристик наравне с точностью
и полнотой{ref_metrics("iso25012")}.</p>
</div></section>

<section id="npv"><div class="wrap">
<h2><span class="num">4</span>NPV: как считается результат инициативы</h2>
<p>NPV — язык, на котором инвестиционный комитет разговаривает о любой
инициативе. Чтобы читать этот язык, достаточно четырёх понятий, которые
выстраиваются одно из другого: денежный поток, накопленный поток,
дисконтирование и, наконец, сам NPV.</p>

<h3 id="npv-terms">Четыре понятия по порядку</h3>
<div class="card">
<h4>Денежный поток</h4>
<p><b>Денежный поток</b> — совокупность распределённых во времени поступлений
и выплат, которые порождает инициатива. В месячном разрезе это одно число на
месяц: сколько денег за месяц пришло минус сколько ушло. Знак важен: в начале
жизни инициативы поток отрицательный (расходы есть, доходов нет), затем
становится положительным.</p>
</div>
<div class="card">
<h4>Накопленный денежный поток</h4>
<p><b>Денежный поток нарастающим итогом</b> — сумма месячных потоков с начала
проекта до текущего месяца. Именно он отвечает на вопрос «сколько денег мы
уже вложили и вернули»: пока накопленный поток отрицателен, инициатива
находится «в минусе» и требует финансирования.</p>
{_F("Накопленный поток(m) = Σ<sub>t=1..m</sub> CF<sub>t</sub>")}
</div>
<div class="card">
<h4>Дисконтирование и ставка дисконта</h4>
<p><b>Дисконтирование</b> — способ учесть, что деньги со временем
обесцениваются: из-за инфляции, из-за риска и из-за того, что деньги, которые
есть сейчас, можно вложить и получить доход. Коэффициент, которым будущая
сумма приводится к сегодняшнему дню, называется <b>ставкой дисконта</b>: чем
она выше, тем меньше сегодня стоят будущие деньги. Логика бытовая: миллион
через год при ставке 10 % годовых стоит сегодня примерно 909 тысяч рублей,
потому что именно эту сумму достаточно положить на депозит, чтобы через год
получить миллион.</p>
{_F("Приведённая стоимость = Будущая сумма / (1 + r)<sup>t</sup>",
    "r — ставка дисконта за один период, t — номер периода")}
</div>
{fig(discount_bars(), "Механика дисконтирования: одна и та же сумма 100 000 ₽, поступившая в разные месяцы. Светлые столбцы — номинал, как он выглядит в бюджете; тёмные — та же сумма, приведённая к сегодняшнему дню при ставке 1 % в месяц. Через три года приведённая стоимость составляет уже около 70 % номинала.")}
<div class="card">
<h4>NPV — накопленный дисконтированный поток</h4>
<p><b>NPV (Net Present Value, чистая приведённая стоимость)</b> — сумма всех
денежных потоков инициативы, приведённых к сегодняшнему дню, за вычетом
начальных вложений. NPV показывает, сколько денег останется у банка после
того, как он покроет все свои затраты и получит все доходы, с учётом того,
что деньги в разные моменты времени стоят по-разному.</p>
{_F("NPV = Σ<sub>t=1..n</sub> CF<sub>t</sub> / (1 + r)<sup>t</sup> &nbsp;−&nbsp; IC",
    "CF<sub>t</sub> — денежный поток периода t; r — ставка дисконтирования; "
    "n — число периодов; IC — начальные инвестиции")}
<p>Читается результат просто: положительный NPV означает, что инициатива
зарабатывает больше, чем стоит альтернативное вложение тех же денег под
ставку дисконта; отрицательный — что не зарабатывает. Само по себе значение
решения не даёт: решением его делает порог, зафиксированный инвестиционными
правилами банка, — например, «NPV положителен к 36-му месяцу».</p>
</div>

{_more("Как посчитать NPV на практике: месячная ставка, горизонт, примеры",
       "<p><b>Из годовой ставки в месячную.</b> Финансовые модели инициатив "
       "считаются помесячно, а ставка дисконтирования обычно задаётся годовая. "
       "Точный перевод — через корень: "
       "<code>r<sub>мес</sub> = (1 + r<sub>год</sub>)<sup>1/12</sup> − 1</code>. "
       "Для 12 % годовых это 0,949 % в месяц. На практике часто пользуются "
       "упрощением <code>r<sub>мес</sub> = r<sub>год</sub> / 12</code> — "
       "1 % в месяц; расхождение на горизонте трёх лет составляет доли "
       "процента и на решение не влияет. В модели портфеля инициатив, на "
       "которой построены кейсы курса, используется именно упрощение: "
       "10 % годовых дают ставку 0,8333 % в месяц.</p>"
       "<p><b>Горизонт.</b> Горизонт расчёта фиксируется до начала счёта и "
       "одинаков для всех сравниваемых инициатив: 36 месяцев в кейсах курса. "
       "Сравнение NPV, посчитанных на разных горизонтах, бессмысленно — "
       "длинная инициатива всегда «выиграет» просто потому, что ей дали "
       "больше времени.</p>"
       "<p><b>Начальные вложения.</b> Их можно учитывать двумя равноценными "
       "способами: отдельным слагаемым IC или как отрицательный денежный "
       "поток нулевого месяца. Главное — не сделать это дважды.</p>"
       "<p><b>Родственные показатели.</b> "
       "<b>IRR (Internal Rate of Return, внутренняя норма доходности)</b> — "
       "ставка дисконтирования, при которой NPV обращается в ноль; отвечает "
       "на вопрос «какую доходность даёт инициатива». "
       "<b>ROI (Return on Investment)</b> — отношение прибыли к вложениям, "
       "<code>ROI = (доход − затраты) / затраты</code>; стоимость денег во "
       "времени не учитывает и потому годится только для коротких инициатив. "
       "<b>Срок окупаемости</b> — месяц, в котором накопленный поток впервые "
       "пересекает ноль.</p>"
       "<p><b>Учебный пример.</b> Инициатива требует 1,12 млн ₽ к моменту "
       "старта, выходит на положительный месячный поток на шестом месяце "
       "после старта и возвращает вложения на восемнадцатом. При ставке "
       "0,8333 % в месяц и горизонте 36 месяцев её NPV-кривая проходит через "
       "минимум около −1,5 млн ₽ на двенадцатом месяце портфеля, пересекает ноль "
       "на двадцать четвёртом и приходит к горизонту с положительным "
       "результатом. Все четыре числа читаются с одной картинки — она в "
       "следующем разделе.</p>")}

<h3 id="npv-curve">Что читается с кривой NPV</h3>
<p>Кривая накопленного дисконтированного потока отвечает сразу на три вопроса
комитета: сколько денег понадобится и когда потребность максимальна, когда
инициатива вернёт вложенное и сколько она заработает за горизонт.</p>
{fig(npv_curve_lg(), "Кумулятивный денежный поток инициативы: пик вложений (максимальная потребность в финансировании), точка окупаемости (кривая пересекает ноль) и NPV за горизонт. Задержка решения сдвигает всю кривую вправо — позже окупаемость и меньше итог за тот же горизонт.")}
<p>Отсюда же видно, почему время буквально стоит денег: любая задержка сдвигает
кривую вправо целиком. Окупаемость наступает позже, а к концу зафиксированного
горизонта инициатива успевает заработать меньше — при полностью неизменной
экономике самого продукта. Это и есть стоимость задержки из раздела
<a href="#eco-cod">«Стоимость задержки (Cost of Delay) и профили потерь»</a>,
только выраженная не в профиле потерь, а в сдвиге кривой.</p>
<p>Различают две точки, которые часто путают.
<b>Выход на прибыльность</b> — месяц, в котором <i>месячный</i> денежный поток
впервые становится положительным; на накопленной кривой это минимум — точка, ниже
которой она уже не опускается. <b>Окупаемость</b> — месяц, в котором
<i>накопленный</i> поток впервые пересекает ноль, то есть вложенное вернулось
полностью. Между этими двумя точками инициатива уже зарабатывает, но ещё
не рассчиталась.</p>
</div></section>

<section id="passport"><div class="wrap">
<h2><span class="num">5</span>Паспорт инициативы и портфель</h2>
<div class="card acc">
<h4>Определение</h4>
<p><b>Паспорт инициативы</b> — карточка из четырёх параметров, по которым
инициатива превращается в денежную кривую:</p>
<ol>
  <li><b>месяц старта</b> — когда инициатива начинает тратить деньги;</li>
  <li><b>расходы к моменту старта</b> — сколько уже вложено к этому месяцу;</li>
  <li><b>месяц выхода на прибыльность</b> — через сколько месяцев после старта
      месячный денежный поток пересекает ноль;</li>
  <li><b>месяц окупаемости</b> — через сколько месяцев после старта накопленный
      поток пересекает ноль.</li>
</ol>
<p>Смысл паспорта не в точности каждого числа, а в единстве методики.
Когда все инициативы описаны одними и теми же четырьмя параметрами,
посчитанными по одному правилу, их кривые становятся сравнимыми — и их можно
складывать в кривую портфеля. Если же каждый владелец считает «выход на
прибыльность» по-своему, сумма кривых арифметически посчитается, но
экономически не будет значить ничего.</p>
</div>

<h3 id="passport-curve">Как из четырёх чисел получается кривая</h3>
<p>Накопленная прибыль инициативы задаётся кривой, проходящей ровно через три
точки паспорта: в месяц старта она равна минус расходам к старту, в месяц
выхода на прибыльность достигает дна (месячный поток здесь меняет знак,
поэтому накопленная кривая проходит через минимум), а в месяц окупаемости
пересекает ноль. Месячный поток — приращение этой кривой; NPV-кривая — тот же
поток, приведённый к сегодняшнему дню и накопленный.</p>
{fig(passport_curve(), "Одна инициатива: месяц старта 6, расходы к старту 1,12 млн ₽, выход на прибыльность через 6 месяцев, окупаемость через 18. Пунктир — накопленный поток без дисконта, сплошная линия — NPV. Все четыре параметра паспорта читаются прямо с кривой.")}
{_more("Полная выкладка: формула кривой инициативы",
       "<p>Обозначим параметры паспорта: <code>t₀</code> — месяц старта, "
       "<code>C₀</code> — расходы к моменту старта, <code>P</code> — число "
       "месяцев от старта до выхода на прибыльность, <code>O</code> — число "
       "месяцев от старта до окупаемости.</p>"
       "<p>Накопленная прибыль моделируется параболой, потому что этого "
       "достаточно: у параболы ровно три степени свободы, а паспорт задаёт "
       "ровно три условия. Вершина параболы приходится на месяц выхода "
       "на прибыльность <code>t₀ + P</code> — это минимум накопленной кривой. "
       "Один из нулей — месяц окупаемости <code>t₀ + O</code>. Второй ноль "
       "симметричен вершине: <code>t₀ + 2P − O</code>. Значит, кривая имеет "
       "вид</p>"
       + _F("Накопл(m) = a · (m − x₃) · (m − x₂),&nbsp;&nbsp; "
            "x₂ = t₀ + O,&nbsp; x₃ = t₀ + 2P − O")
       + "<p>Масштабный коэффициент <code>a</code> находится из третьего "
       "условия — значения в месяц старта:</p>"
       + _F("a = − C₀ / ( (t₀ − x₃) · (t₀ − x₂) )")
       + "<p>Дальше — обычная механика NPV. Месячный денежный поток есть "
       "приращение накопленной прибыли, "
       "<code>CF(m) = Накопл(m) − Накопл(m−1)</code>; NPV-кривая — накопленная "
       "сумма приведённых потоков:</p>"
       + _F("NPV(m) = Σ<sub>t=1..m</sub> CF(t) / (1 + r)<sup>t</sup>")
       + "<p>Ставка <code>r</code> в модели портфеля равна 0,8333 % в месяц "
       "(10 % годовых, делённые на 12). Проверка модели: на данных финансовой "
       "модели портфеля накопленный итог третьего месяца составляет "
       "−6 138 000 ₽, а NPV того же месяца — −5 987 072 ₽; расчёт сходится "
       "с таблицей до рубля.</p>"
       "<p>Обратите внимание, что до месяца старта кривая тождественно равна "
       "нулю: инициатива, которая ещё не началась, не участвует в потоке "
       "портфеля. Именно поэтому сдвиг месяца старта на два месяца вправо "
       "меняет не только её собственную кривую, но и минимум, окупаемость и NPV "
       "всего портфеля.</p>")}

<h3 id="passport-portfolio">Кривые складываются в портфель</h3>
<p>Портфель — это набор инициатив, и его денежный поток равен сумме потоков
входящих инициатив, месяц к месяцу. Складывать можно только сравнимое,
поэтому единая методика паспорта — не бюрократия, а условие, при котором
арифметика вообще имеет смысл. Когда паспорта единообразны, сумма кривых
отвечает комитету на три вопроса сразу.</p>
{fig(portfolio_curve(), "Четырнадцать инициатив портфеля и их сумма. Тонкие линии — NPV-кривые отдельных инициатив, каждая построена из своего паспорта; толстая линия — кривая портфеля. Минимум суммарной кривой — пик потребности в финансировании, точка пересечения нуля — окупаемость портфеля, значение в конце — NPV за горизонт.")}
<div class="scroll"><table>
<tr><th>Вопрос комитета</th><th>Что читается с суммарной кривой</th></tr>
<tr><td>Сколько денег понадобится и когда?</td>
    <td>Минимум суммарной кривой: его глубина — максимальная потребность
        в финансировании, его месяц — момент, когда эта потребность возникает</td></tr>
<tr><td>Когда портфель выйдет в ноль?</td>
    <td>Первый месяц после минимума, в котором суммарная кривая пересекает нулевую
        линию, — окупаемость портфеля</td></tr>
<tr><td>Сколько заработаем за горизонт?</td>
    <td>Значение суммарной кривой в последнем месяце горизонта — NPV
        портфеля</td></tr>
</table></div>
<p>Отсюда следует главное свойство портфельного управления: от перестановки
инициатив во времени меняются все три ответа. Сдвиг старта одной инициативы
на два месяца вперёд углубляет минимум портфеля, но приближает окупаемость;
сдвиг назад — наоборот. Поэтому решение о составе и порядке стартов
пересчитывается при каждом изменении сроков, а критерием отбора служит
стоимость задержки, делённая на длительность, из раздела
<a href="#eco-cod">«Стоимость задержки (Cost of Delay) и профили потерь»</a>.</p>

<div class="card acc">
<p><b>Соберите портфель самостоятельно.</b> Кейс «Портфель инициатив» в
<a href="trainer_tree.html">тренажёре «Дерево метрик»</a> построен ровно на
этой модели: первый уровень — собрать дерево от источника паспортов к
приоритизации запусков, второй — выбрать, откуда паспорта берутся (витрина
финансовых моделей или заявки менеджеров) и чем контролируется ход портфеля
(план-факт из учёта или статус-отчёты). Определения всех метрик кейса —
в группе <a href="#guide">«Портфель инициатив» справочника метрик</a>.</p>
</div>
</div></section>

<section id="quality"><div class="wrap">
<h2><span class="num">6</span>Качество данных и интегральная оценка</h2>
<p>Качество данных — это не только чистота данных.
Стандарт ISO/IEC 25012 описывает пятнадцать характеристик качества данных, из
которых часть относится к самим данным, а часть — к системе, которая их
хранит{ref_metrics("iso25012")}. Руководителю из них критичны четыре
измерения. Почему это управленческая рамка, а не задача ИТ, разобрано
в разделе <a href="longread_data.html#d4">«Качество данных — это не только
чистота данных»</a> лонгрида «Роль данных».</p>
{_slide_fig("s1b1_quality",
            "Четыре измерения качества данных: чистота и "
            "согласованность, актуальность, прослеживаемость, доступность "
            "и цена сбора.")}
<div class="scroll"><table>
<tr><th>Измерение</th><th>Вопрос руководителя</th><th>Как измеряется</th></tr>
<tr><td><b>Чистота и согласованность</b></td>
    <td>Одинаково ли называется одно и то же во всех системах, нет ли дублей
        и пропусков?</td>
    <td>Доля записей без пропусков в обязательных полях; доля объектов без
        дублей; доля показателей, совпадающих между системами</td></tr>
<tr><td><b>Актуальность</b></td>
    <td>Успевают ли данные за частотой решения? Данные раз в месяц не поддержат
        еженедельное решение</td>
    <td>Доля регламентных обновлений, пришедших в срок; средняя задержка
        данных относительно события</td></tr>
<tr><td><b>Прослеживаемость</b></td>
    <td>Прослеживается ли значение до первичной записи? Показатель без
        источника — не факт, а суждение</td>
    <td>Доля показателей отчёта, для которых описан путь расчёта до первичных
        данных и его можно воспроизвести</td></tr>
<tr><td><b>Доступность и цена сбора</b></td>
    <td>Сколько стоит и сколько длится сбор? Метрика, требующая переделки
        ландшафта, не поможет решению этого квартала</td>
    <td>Паспорт сбора метрики: CAPEX, OPEX и time-to-evidence</td></tr>
</table></div>

<h3 id="dq-index">Интегральная оценка качества данных</h3>
<p><b>Интегральная оценка качества данных</b> — свёртка частных измерений
качества в одно число, по которому источник или витрину можно поставить
в план работ и сравнить с другими. Каждое частное измерение считается как
доля записей (или показателей), прошедших свою проверку; затем измерения
складываются с весами, отражающими важность измерения для решений, которые
на этих данных принимаются.</p>
{_F("Интегральная оценка = Σ<sub>i</sub> w<sub>i</sub> × q<sub>i</sub>,&nbsp;&nbsp; Σ<sub>i</sub> w<sub>i</sub> = 1",
    "q<sub>i</sub> — частная оценка измерения i в долях единицы; "
    "w<sub>i</sub> — вес измерения")}
{fig(dq_index(), "Интегральная оценка качества данных на примере витрины активации: шесть частных измерений со своими весами сворачиваются в одно число. Красным выделены измерения, не дотягивающие до порога 90 % — именно они попадают в план работ.")}
<p>Читается такая оценка вместе с двумя правилами, без которых она превращается
в красивое, но бесполезное число.</p>
<div class="card">
<h4>Правило блокирующих проверок</h4>
<p>Часть проверок критична настолько, что их провал не компенсируется высокими
баллами по остальным измерениям. Если ключ, по которому склеиваются системы,
не уникален — интегральная оценка не имеет смысла, потому что все остальные
измерения посчитаны на неверно склеенных данных. Такие проверки помечаются
как блокирующие: их результат «прошло / не прошло» выносится рядом с
интегральной оценкой, а не растворяется в её весах.</p>
</div>
<div class="card">
<h4>Правило фиксированных весов</h4>
<p>Веса задаются один раз, вместе с владельцем данных, и меняются только через
регламент. Иначе оценка превращается в инструмент подгонки: любую витрину
можно «улучшить» до нужного значения, увеличив вес того измерения, где она
и так хороша. По той же причине история оценок хранится вместе с версией
весов — иначе сравнение кварталов ничего не показывает.</p>
</div>
<p>Практический смысл интегральной оценки — приоритизация. Она не говорит,
можно ли верить конкретному значению: для этого есть паспорт метрики и
прослеживаемость. Она говорит, какому источнику в первую очередь нужны
вложения, и делает разговор о качестве данных на комитете конечным —
вместо обмена впечатлениями появляется одно число, его состав и план
доведения его до порога.</p>

<h3 id="quality-pipeline">Как измерения ломаются на живом процессе</h3>
<p>Все четыре измерения качества видны на одном примере: сам кредитный
конвейер работает штатно, а данные теряются на стыках систем — и руководитель
не видит процесса, принимая решения без оснований.</p>
{_slide_fig("s1b3_pipeline",
            "Конвейер работает, а данные теряются на стыках систем: дубли на входе, "
            "несклеиваемые ключи, нелогируемые статусы, витрина раз в месяц.")}

<h3 id="defects">Пять типовых дефектов данных</h3>
<p>Пять дефектов данных, из-за которых правильная арифметика даёт неверный результат.
На встрече каждый показан отдельным слайдом; здесь — что это, чем измеряется
и что делать.</p>

<div class="card">
<h4>1 · Пропуски</h4>
<p>Поле не заполнено: без адреса не считается срок доставки, без отметки
времени — длительность этапа. Измеряется долей пропусков по каждому ключевому
полю: <code>доля пропусков = записи с пустым полем / все записи × 100 %</code>.
Это первое, что запрашивается у владельца выгрузки. В управленческой
отчётности пропуски не «лечатся средним»: они честно исключаются из расчёта
с указанием доли исключённого — читатель отчёта должен видеть, на какой части
данных сделан вывод. Опасность пропусков в том, что они исключаются из сумм
и средних без какого-либо сообщения об ошибке.</p>
</div>
{_slide_fig("s1b1_def_gaps",
            "Пропуски в выгрузке: незаполненные ячейки исключаются из сумм "
            "и средних без сообщения об ошибке; сначала считается доля пропусков "
            "по каждому полю.")}

<div class="card">
<h4>2 · Дубликаты</h4>
<p>Один объект — несколько записей: заявка, поданная в двух каналах, клиент
с двумя карточками, платёж, загруженный дважды. Сумма и конверсия искажаются
без признаков ошибки и всегда в одну сторону — вверх. Измеряется долей объектов, у которых
больше одной записи по ключу; лечится правилом дедупликации по ключу
«клиент + продукт + период», применённым до всякой аналитики, а не в каждом
отчёте заново. Правило дедупликации — часть определения метрики: два отчёта
с разными правилами дают разные значения при абсолютно одинаковых данных.</p>
</div>
{_slide_fig("s1b1_def_dups",
            "Одна заявка — две записи: дубли завышают поток "
            "и конверсию и не вызывают никакой ошибки при расчёте.")}

<div class="card">
<h4>3 · Неправильные типы</h4>
<p>Число стало текстом («12,4» с запятой вместо точки), дата приехала в трёх
форматах, идентификатор потерял ведущие нули. Сортировки и суммы при этом
работают — но врут: текстовая сортировка ставит «10» перед «9», а даты
в формате «день/месяц» и «месяц/день» дают правдоподобный, но неверный ряд.
Ловится профилированием колонок: по каждому полю смотрят фактический тип,
долю значений, не приводящихся к нему, и диапазон. Чинится один раз на входе
в витрину, а не в каждом отчёте заново.</p>
</div>
{_slide_fig("s1b1_def_types",
            "Число стало текстом: расчёт проходит без ошибки, "
            "а результат неверен.")}

<div class="card">
<h4>4 · Выбросы</h4>
<p>Одна аномальная запись двигает среднее: четырёхдневный сбой в системе
превращается в «процесс замедлился на 74 %». Обнаруживаются сравнением
среднего с медианой и просмотром хвоста распределения (значения выше 90-го
или 99-го перцентиля). Правило курса: выброс — это вопрос «ошибка измерения или
значимое наблюдение», и отвечает на него руководитель, знающий контекст,
а не формула.
Техническая ошибка исключается с описанием причины; реальное редкое событие
остаётся в данных и разбирается отдельно. Рядом с любым средним в отчёте
должны стоять медиана и 90-й перцентиль.</p>
</div>
{_slide_fig("s1b1_def_outliers",
            "Одна сделка смещает среднее: средний срок укладывается в норматив, "
            "а каждая четвёртая заявка идёт вдвое дольше.")}

<div class="card">
<h4>5 · Справочники</h4>
<p>«Москва», «москва» и «МСК» — три разных региона для системы. Любая
группировка по такому полю делит показатель на части, и потери выглядят как
падение. Измеряется числом уникальных значений поля против числа значений
в эталонном справочнике. Лечится одним справочником с назначенным владельцем
и правилом нормализации на входе. Искусственный интеллект здесь заметно
ускоряет работу: по описанию выгрузки GigaChat предлагает план нормализации
и список подозрительных значений, а решение о том, что чему соответствует,
остаётся за владельцем справочника.</p>
</div>
{_slide_fig("s1b1_def_dict",
            "Три имени одного региона: группировка делит "
            "показатель на части, и это выглядит как падение.")}

<div class="card acc">
<p><b>Проверьте качество на своей карте.</b> Шаг «проверка качества» в
<a href="trainer_map.html">тренажёре «Карта источников данных»</a> проходит
ровно по этим измерениям: по каждому источнику фиксируется, где риск дублей,
кто master-source и успевает ли частота обновления за горизонтом решения.</p>
</div>
</div></section>

<section id="experiment"><div class="wrap">
<h2><span class="num">7</span>Эксперимент и накопление данных</h2>
<p>Три правила оберегают решение от ложных выводов: наблюдений должно хватать,
горизонт должен пройти, выборка должна повторять целое. Ниже — каждое
с формулой и с тем, что происходит, если правило нарушить.</p>

<h3 id="exp-volume">Объём: наблюдений должно хватать</h3>
<p>На малых числах оценка неустойчива. На базе из двадцати событий «рост
на 30 %» — это шесть
случаев против четырёх с половиной; такое движение возникает случайно почти
всегда. Прежде чем сравнивать доли, спрашивают про абсолютную базу: сравнение
процентов без базы не значит ничего. Нужный объём считается до эксперимента,
а не после.</p>
<div class="card acc" id="sample-formula">
<h4>Формула объёма выборки</h4>
{_F("n = ( Z × σ / E )²")}
<p>Три параметра, и каждый из них — управленческое решение, а не техническая
настройка.</p>
<ul>
<li><b>Z — уровень доверия.</b> Насколько мы готовы ошибаться. Для стандартных
    95 % <code>Z = 1,96</code>; для 90 % — 1,64; для 99 % — 2,58.</li>
<li><b>σ — разброс величины.</b> Чем «шумнее» метрика, тем больше данных нужно.
    Для долей разброс выражается через саму долю:
    <code>σ² = p(1 − p)</code>, максимум достигается при p = 0,5 — это и есть
    самый «дорогой», консервативный случай.</li>
<li><b>E — допустимая погрешность.</b> Какое отклонение оценки ещё не меняет
    решения. Это половина ширины доверительного интервала: результат
    записывается как «оценка ± E».</li>
</ul>
<p>Отсюда ориентиры, которые звучат на встрече: погрешность 5 процентных
пунктов при 95 % доверия требует около 385 наблюдений, 3 пункта — около
1 067. Ужесточение требований к погрешности вдвое увеличивает необходимый
объём выборки вчетверо: n растёт квадратично.</p>
</div>
{fig(sample_size_sensitivity(), "Квадратичный рост объёма выборки при ужесточении допустимой погрешности (уровень доверия 95 %, доля 0,5). Ужесточение погрешности с 5 % до 2 % удорожает наблюдение более чем вшестеро, до 1 % — в двадцать пять раз.")}
<p>Формула одна для всех кейсов курса, меняются только параметры. В рознице
доля p — это конверсия отклика на предложение, и трафик даёт целевой объём
за считанные дни. В корпоративном блоке p — доля юрлиц, дошедших до
активации, и при сотнях клиентов в месяц набор объёма занимает кварталы.
В портфельном сравнении разброс σ задаёт разброс NPV на клиента, а
погрешность E выбирается такой, чтобы не перепутать инициативы местами.</p>
{_more("Как формула получается и когда ею пользоваться нельзя",
       "<p><b>Откуда берётся формула.</b> Среднее по выборке из n наблюдений "
       "имеет разброс <code>σ/√n</code> — это стандартная ошибка среднего. "
       "Доверительный интервал с уровнем доверия, которому соответствует "
       "множитель Z, имеет полуширину <code>E = Z · σ/√n</code>. Разрешая это "
       "равенство относительно n, получаем <code>n = (Z·σ/E)²</code>. Квадрат "
       "в формуле — прямое следствие того, что точность растёт как корень из "
       "числа наблюдений: чтобы удвоить точность, наблюдений нужно вчетверо "
       "больше.</p>"
       "<p><b>Для долей.</b> Если измеряется доля (конверсия, активация, доля "
       "решений в срок), то <code>σ² = p(1 − p)</code>, где p — ожидаемое "
       "значение доли. Когда ожидаемое значение неизвестно, берут p = 0,5: "
       "это даёт максимальный разброс и, значит, самый безопасный объём.</p>"
       "<p><b>Сравнение двух групп.</b> Формула выше даёт объём для оценки "
       "одной величины. Для A/B-сравнения двух групп нужен объём примерно "
       "вдвое больший на каждую группу, а вместо допустимой погрешности "
       "задаётся минимальный значимый эффект (MDE, minimum detectable "
       "effect) — тот прирост, ради которого стоит внедрять изменение. "
       "Точный расчёт с обеими ошибками — первого и второго рода — делает "
       "<a href='trainer_sample.html'>тренажёр «Расчёт выборки»</a>.</p>"
       "<p><b>Когда формулой пользоваться нельзя.</b> Она предполагает "
       "независимые наблюдения. Если один клиент даёт несколько наблюдений "
       "(несколько заявок, несколько операций), эффективный объём меньше "
       "формального и расчёт занижает нужную выборку. То же происходит при "
       "сильной сезонности внутри периода наблюдения: неделя из середины "
       "месяца не представляет месяц.</p>")}

<h3 id="exp-horizon">Срок: горизонт должен пройти</h3>
<p>Накопительные метрики не ускоряются деньгами. Отток за 90 дней требует
90 дней; полный сезонный цикл — года. Эксперимент, закрытый до окончания
горизонта, меряет нетерпение, а не эффект. Поэтому длительность наблюдения —
часть паспорта метрики (TTE), и ансамбль решения не быстрее самой медленной
из задействованных метрик.</p>
<p>Первые два правила удобно видеть на одной картинке. Пока наблюдений мало,
оценка показателя неустойчива, а доверительный интервал широк — любой «рост»
внутри такого интервала ничего не доказывает. По мере накопления данных
интервал сужается, и вывод становится достоверным только тогда, когда весь коридор
оказывается по одну сторону порога решения.</p>
{fig(ci_funnel_lg(), "Симуляция последовательного наблюдения (та же модель, что на слайде встречи): поток клиентов с истинной конверсией 23 % при пороге решения 20 %. Тёмная линия — бегущая оценка конверсии p̂, светлая полоса — 95 % доверительный интервал, его полуширина и есть погрешность E из формулы объёма выборки. Наблюдение закрыто на n = 869: нижняя граница интервала устойчиво выше порога.")}
<p>На этом графике видны все три буквы формулы объёма выборки. Тёмная линия —
оценка доли <code>p̂</code>; ширина светлой полосы вокруг неё — удвоенная
погрешность <code>E</code>, которая сжимается как <code>1/√n</code> по мере
роста числа наблюдений; выбор уровня доверия 95 % — это множитель
<code>Z = 1,96</code>, задающий, насколько широкой рисуется полоса. Решение
принимается не в момент, когда линия пересекла порог, а в момент, когда порога
не касается уже вся полоса.</p>
<p>Рассчитанный объём — это ещё не срок эксперимента. Наблюдение проходит две
фазы: сначала накапливаются участники до целевого объёма, затем — сами данные,
пока не пройдёт горизонт метрики. Досрочно завершить можно только первую фазу,
и только если участников уже достаточно; горизонт второй фазы не сжимается
ничем.</p>
{fig(accumulation2_lg(), "Две фазы накопления. Модель: приток 40 клиентов в день до целевого объёма n ≈ 970 из формулы выборки, затем горизонт метрики 90 дней. Досрочная остановка набора (GST) сокращает только первую фазу — финиш в день 105 вместо 114; горизонт второй фазы деньгами не ускоряется.")}

<h3 id="exp-sample">Выборка: она должна повторять целое</h3>
<p>Выборка обязана повторять структуру генеральной совокупности по тем
признакам, которые влияют на измеряемую величину. Опрос «дошедших до конца
обслуживания» систематически завышает лояльность: недовольные до опроса
не доходят. Проверка одна и делается до того, как смотреть на результат:
состав выборки сравнивается с составом всей аудитории по ключевым срезам —
каналу, сегменту, региону, давности отношений. Расхождение больше нескольких
процентных пунктов по любому значимому срезу означает, что результат
переносить на всю аудиторию нельзя.</p>
<p>Контргипотеза — часть плана эксперимента: заранее сформулированное условие,
при котором пилот останавливается, даже если целевая метрика выглядит хорошо.
Например, «останавливаемся, если появилось больше трёх случаев фрода» или
«если доля жалоб выросла вдвое». Отслеживается не только целевая метрика,
но и риск-сигналы — иначе эксперимент оптимизирует одно за счёт другого
и это выясняется после внедрения.</p>
<p>Практические поправки, которые экономят кварталы. Если результат прошёл
по самой границе — это значит, что данных нужно больше, а не что «эффект
доказан». Тест не останавливают раньше запланированного объёма, даже когда
промежуточная картина выглядит убедительно. И смотрят не только на
статистическую значимость, но и на размер эффекта: достоверный прирост
в полпроцента может не стоить внедрения.</p>

<div class="card acc">
<p><b>Сколько продлится ваш эксперимент?</b> Обе фазы считает
<a href="trainer_accum.html">тренажёр «Срок эксперимента»</a>: берёте кейс —
розница, кредитный конвейер или портфель — и задаёте тремя ползунками, сколько
участников в день вы можете пропускать в эксперимент, через сколько дней они
активируются и какой горизонт нужен метрике. Доверительный интервал
перестраивается сразу и показывает, какую часть срока сжимает поток, а какую —
не сжимает ничто.</p>
</div>
<div class="card acc">
<p><b>Нужен точный расчёт объёма?</b> В материалах есть
<a href="trainer_sample.html">тренажёр «Расчёт выборки»</a>: задаёте базовую
конверсию, минимальный значимый эффект и дневной трафик — получаете размер
групп и срок накопления данных. Это тот самый расчёт, из которого складывается
TTE экспериментальной метрики в паспорте.</p>
</div>
</div></section>

<section id="guide"><div class="wrap">
<h2><span class="num">8</span>Справочник метрик: полные определения</h2>
<p>Все метрики <a href="trainer_tree.html">тренажёра «Дерево метрик»</a> —
по кейсам, в том же порядке и под теми же названиями, что в тренажёре и на
слайдах. Кнопка «?» на карточке метрики в тренажёре ведёт сюда, на её
описание. У каждой метрики сначала идёт короткое определение и паспорт сбора,
а под расхлопом «Полное определение» — формула расчёта, источник данных
в банке, управленческое применение и стандартная методика с типовыми
оговорками.</p>

<div class="card">
<h4>Сквозные названия и сокращения</h4>
<p>Названия метрик одинаковы во всех артефактах курса — на слайдах, в
тренажёрах и здесь. Ниже — соответствие русских названий общепринятым
в российских банках сокращениям.</p>
<div class="scroll"><table>
<tr><th>Сокращение</th><th>Полное название</th><th>Русское название в курсе</th></tr>
<tr><td><b>TAT</b></td><td>Turnaround Time</td><td>Срок принятия решения</td></tr>
<tr><td><b>STP</b></td><td>Straight-Through Processing</td><td>Доля автоматических решений</td></tr>
<tr><td><b>SLA</b></td><td>Service Level Agreement</td><td>Норматив срока; доля решений в срок</td></tr>
<tr><td><b>NPS</b></td><td>Net Promoter Score</td><td>Индекс лояльности</td></tr>
<tr><td><b>CSAT</b></td><td>Customer Satisfaction Score</td><td>Удовлетворённость</td></tr>
<tr><td><b>CAC</b></td><td>Customer Acquisition Cost</td><td>Стоимость привлечения клиента</td></tr>
<tr><td><b>LTV</b></td><td>Lifetime Value</td><td>Ценность клиента за время жизни</td></tr>
<tr><td><b>ARPU</b></td><td>Average Revenue Per User</td><td>Средний доход на клиента</td></tr>
<tr><td><b>AOV</b></td><td>Average Order Value</td><td>Средний чек</td></tr>
<tr><td><b>MAU / DAU</b></td><td>Monthly / Daily Active Users</td><td>Активные клиенты за месяц / за день</td></tr>
<tr><td><b>Churn / CRR</b></td><td>Churn Rate / Customer Retention Rate</td><td>Отток / удержание</td></tr>
<tr><td><b>ROI</b></td><td>Return on Investment</td><td>Возврат инвестиций</td></tr>
<tr><td><b>NPV / IRR</b></td><td>Net Present Value / Internal Rate of Return</td><td>Чистая приведённая стоимость / внутренняя норма доходности</td></tr>
<tr><td><b>TCO</b></td><td>Total Cost of Ownership</td><td>Совокупная стоимость владения</td></tr>
<tr><td><b>TTE</b></td><td>Time-to-Evidence</td><td>Время до проверенного значения</td></tr>
<tr><td><b>CD3 / WSJF</b></td><td>Cost of Delay Divided by Duration</td><td>Стоимость задержки на длительность</td></tr>
</table></div>
</div>
{_guide}
</div></section>

<section id="src"><div class="wrap">
<h2>Источники</h2>
<p class="sub">Методические утверждения проверены по источникам; цитаты — в
отчёте проверки. Учебные числа CAPEX, OPEX и TTE в кейсах — авторские и на
источники не ссылаются. Определения метрик, классификация метрик продукта,
понятия денежного потока, дисконтирования, NPV, точек прибыльности и
окупаемости, а также модель финансовой модели портфеля инициатив опираются
на книгу Я. Шуваева «Менеджмент цифрового продукта» (пересказ без прямого
цитирования) и на открытые отраслевые источники.</p>
<ol>
{"".join(f'<li id="src-{s["id"]}"><b>{s["ref"]}</b><br>'
         f'<a href="{s["url"]}" target="_blank" rel="noopener">{s["url"]}</a></li>'
         for s in SOURCES_METRICS)}
</ol>
<h3>Куда идти дальше</h3>
<p>Справочник связан с остальными материалами в обе стороны. Из тренажёров
сюда ведут кнопки «?»; отсюда обратно — ссылки в тексте:</p>
<ul>
<li><a href="trainer_tree.html">Тренажёр «Дерево метрик»</a> — собрать дерево
    и сравнить конфигурации источников по формуле эффективности из раздела
    <a href="#eco-e">«Критерий курса: одна формула»</a>.</li>
<li><a href="trainer_map.html">Тренажёр «Карта источников данных»</a> —
    заполнить паспорт метрики своими значениями и пройти проверку качества
    из раздела <a href="#quality">«Качество данных и интегральная оценка»</a>.</li>
<li><a href="trainer_sample.html">Тренажёр «Расчёт выборки»</a> — точный
    расчёт по формуле из раздела
    <a href="#sample-formula">«Формула объёма выборки»</a>.</li>
<li><a href="trainer_accum.html">Тренажёр «Срок эксперимента»</a> — две фазы
    накопления из раздела
    <a href="#exp-horizon">«Срок: горизонт должен пройти»</a>.</li>
<li><a href="longread_data.html">Лонгрид «Роль данных»</a> — категории данных,
    критерии ценности и master-source.</li>
<li><a href="longread.html">Лонгрид «Пять ошибок вывода»</a> — что происходит,
    когда правила этой страницы нарушены.</li>
</ul>
</div></section>

<footer><div class="wrap">
  Аналитика 360 · материалы практической части.<br>
  Справочная страница курса; открывается из тренажёров. Все данные учебные.
</div></footer>
"""
