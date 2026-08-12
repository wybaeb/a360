# -*- coding: utf-8 -*-
"""Общая графика лонгридов A360: инлайновые SVG в стиле деки Шага 1.

Единый источник иллюстраций для longread_*.py — те же цвета и конструкции,
что на слайдах (build_review_step1_r3.py), чтобы участник видел одну и ту же
картинку на встрече и в тексте. Все фигуры — <figure class="fig"> с подписью;
CSS для .fig добавляет theme.py.

Использование:
    from longread_figs import fig, npv_curve, ci_funnel, accumulation, ...
    BODY = f"... {fig(npv_curve(), 'Кумулятивный поток: три ответа на одной кривой')} ..."
"""
import math

FONT = "Inter, Arial, sans-serif"
DARK = "#2E3641"
ACC = "#20BA72"
DEEP = "#159A5C"
WARN = "#C4453B"


def _txt(x, y, s, size=13, weight=None, fill=DARK, op=None, anchor=None):
    a = [f'x="{x}"', f'y="{y}"', f'font-size="{size}"', f'fill="{fill}"']
    if weight:
        a.append(f'font-weight="{weight}"')
    if op is not None:
        a.append(f'fill-opacity="{op}"')
    if anchor:
        a.append(f'text-anchor="{anchor}"')
    return '<text %s>%s</text>' % (' '.join(a), s)


def _plate(x, y, w, h, fill="#ffffff", rx=10, stroke=None, bar=0):
    out = []
    if bar:
        out.append(f'<rect x="{x}" y="{y}" width="{bar}" height="{h}" rx="2" fill="{ACC}"/>')
    st = f' stroke="{stroke}" stroke-width="1.5"' if stroke else f' stroke="{ACC}" stroke-opacity="0.25"'
    out.append(f'<rect x="{x + (bar and bar + 4)}" y="{y}" width="{w - (bar and bar + 4)}" height="{h}" rx="{rx}" fill="{fill}"{st}/>')
    return ''.join(out)


def _poly(pts, stroke, w=2.5, dash=None, op=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    o = f' stroke-opacity="{op}"' if op else ''
    p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    return (f'<polyline points="{p}" fill="none" stroke="{stroke}" stroke-width="{w}"{d}{o} '
            f'stroke-linejoin="round" stroke-linecap="round"/>')


def _svg(h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 {h}" width="100%" '
            f'style="font-family:{FONT};display:block">{body}</svg>')


def _axes(x0, y0, x1, y1):
    return (f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{DARK}" stroke-opacity="0.35" stroke-width="1.5"/>'
            f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="{DARK}" stroke-opacity="0.35" stroke-width="1.5"/>')


def fig(svg, caption):
    """Обёртка иллюстрации: белая карточка + подпись."""
    return (f'<figure class="fig">{svg}'
            f'<figcaption>{caption}</figcaption></figure>')


# ── NPV: кумулятивный поток ─────────────────────────────────────────────────
def npv_curve():
    s = []
    X0, Y0, X1, Y1 = 60, 30, 880, 330
    ZERO = Y1 - 90
    s.append(_axes(X0, Y0, X1, Y1))
    s.append(f'<line x1="{X0}" y1="{ZERO}" x2="{X1 - 10}" y2="{ZERO}" stroke="{DARK}" '
             f'stroke-opacity="0.3" stroke-width="1.2" stroke-dasharray="4 4"/>')
    s.append(_txt(X1, Y1 + 22, "месяцы →", 12, None, DARK, op=0.6, anchor="end"))
    s.append(_txt(X0 - 8, Y0 - 10, "накопленный поток, приведённый к сегодняшнему дню", 12, None, DARK, op=0.6))
    cum = lambda m: 0.1829 * m * m - 2.093 * m + 0.89
    gx = lambda m: X0 + 24 + m / 24 * (X1 - X0 - 60)
    gy = lambda v: ZERO - v * 3.6
    s.append(_poly([(gx(m), gy(cum(m))) for m in [i / 2 for i in range(49)]], DEEP, 2.8))
    mmin = 2.093 / (2 * 0.1829)
    s.append(f'<circle cx="{gx(mmin):.0f}" cy="{gy(cum(mmin)):.0f}" r="6" fill="{WARN}"/>')
    s.append(_txt(gx(mmin), gy(cum(mmin)) + 24, "пик вложений", 12, "700", WARN, anchor="middle"))
    s.append(f'<line x1="{gx(11):.0f}" y1="{Y0 + 8}" x2="{gx(11):.0f}" y2="{Y1}" stroke="{DEEP}" stroke-width="1.6" stroke-dasharray="6 5"/>')
    s.append(f'<circle cx="{gx(11):.0f}" cy="{ZERO}" r="6" fill="{DEEP}"/>')
    s.append(_txt(gx(11) + 10, Y0 + 26, "окупаемость: поток вышел в ноль", 12, "700", DEEP))
    s.append(f'<circle cx="{gx(24):.0f}" cy="{gy(cum(24)):.0f}" r="7" fill="{DEEP}"/>')
    s.append(_txt(gx(24) - 12, gy(cum(24)) + 4, "NPV за горизонт", 12.5, "800", DEEP, anchor="end"))
    return _svg(360, ''.join(s))


# ── Доверительный интервал и порог решения ──────────────────────────────────
def ci_funnel():
    s = []
    X0, Y0, X1, Y1 = 60, 26, 880, 330
    MID, THR = 178, 250
    s.append(_axes(X0, Y0, X1, Y1))
    s.append(_txt(X1, Y1 + 22, "наблюдений накоплено →", 12, None, DARK, op=0.6, anchor="end"))
    wob = lambda x: (11 * math.sin((x - X0) / 46) + 6 * math.sin((x - X0) / 15 + 1.7)) \
        * (0.45 + 0.55 * math.exp(-(x - X0) / 420))
    half = lambda x: 14 + 100 * math.exp(-(x - X0 - 40) / 240)
    xs = [X0 + 40 + i * 8 for i in range(int((X1 - 30 - X0 - 40) / 8) + 1)]
    up = [(x, MID + wob(x) - half(x)) for x in xs]
    lo = [(x, MID + wob(x) + half(x)) for x in xs]
    est = [(x, MID + wob(x)) for x in xs]
    area = ' '.join(f'{x:.1f},{y:.1f}' for x, y in up) + ' ' + \
           ' '.join(f'{x:.1f},{y:.1f}' for x, y in reversed(lo))
    s.append(f'<polygon points="{area}" fill="{ACC}" fill-opacity="0.14"/>')
    s.append(_poly(up, ACC, 1.8))
    s.append(_poly(lo, ACC, 1.8))
    s.append(_poly(est, DEEP, 2.6))
    s.append(f'<line x1="{X0 + 20}" y1="{THR}" x2="{X1 - 20}" y2="{THR}" stroke="{WARN}" '
             f'stroke-width="2" stroke-dasharray="7 5"/>')
    s.append(_txt(X1 - 24, THR + 20, "порог решения", 12.5, "800", WARN, anchor="end"))
    xc = None
    for x, y in reversed(lo):
        if y >= THR:
            xc = x + 8
            break
    s.append(f'<line x1="{xc:.0f}" y1="{Y0 + 6}" x2="{xc:.0f}" y2="{Y1}" stroke="{DEEP}" '
             f'stroke-width="2" stroke-dasharray="3 4"/>')
    s.append(_txt(min(xc + 10, X1 - 300), Y0 + 18, "вывод достоверен: нижняя граница выше порога", 12, "700", DEEP))
    s.append(_txt(X1 - 24, MID - 46, "доверительный интервал", 11.5, "700", ACC, anchor="end"))
    s.append(_txt(X1 - 24, MID - 6, "оценка метрики", 12, "700", DEEP, anchor="end"))
    return _svg(360, ''.join(s))


# ── Накопление: две фазы, GST/FSS ───────────────────────────────────────────
def accumulation():
    s = []
    X0, Y0, X1, Y1 = 60, 30, 880, 290
    s.append(_axes(X0, Y0, X1, Y1))
    s.append(_txt(X1, Y1 + 20, "время эксперимента →", 12, None, DARK, op=0.6, anchor="end"))
    s.append(_txt(X0 - 8, Y0 - 12, "накоплено наблюдений", 12, None, DARK, op=0.6))
    pts = []
    for i in range(81):
        t = i / 80
        v = 1 / (1 + math.exp(-(t - 0.42) * 7.5))
        pts.append((X0 + t * (X1 - X0 - 20), Y1 - v * (Y1 - Y0 - 26)))
    s.append(_poly(pts, DEEP, 2.6))
    xg, xf = X0 + 0.52 * (X1 - X0 - 20), X0 + 0.86 * (X1 - X0 - 20)
    for x, name in ((xg, "GST"), (xf, "FSS")):
        s.append(f'<line x1="{x:.0f}" y1="{Y0 + 6}" x2="{x:.0f}" y2="{Y1}" stroke="{DEEP}" '
                 f'stroke-width="1.6" stroke-dasharray="6 5"/>')
        s.append(_txt(x, Y0, name, 13, "800", DEEP, anchor="middle"))
    s.append(_txt(xg - 14, 120, "участников достаточно —", 11.5, "700", DARK, anchor="end"))
    s.append(_txt(xg - 14, 137, "можно завершить досрочно", 11.5, None, DARK, op=0.75, anchor="end"))
    s.append(_txt(xf - 14, 190, "плановое завершение —", 11.5, "700", DARK, anchor="end"))
    s.append(_txt(xf - 14, 207, "фиксированная выборка набрана", 11.5, None, DARK, op=0.75, anchor="end"))
    s.append(f'<rect x="{X0}" y="{Y1 + 30}" width="{(xg - X0):.0f}" height="24" rx="7" fill="{ACC}" fill-opacity="0.75"/>')
    s.append(f'<rect x="{xg + 3:.0f}" y="{Y1 + 30}" width="{(X1 - 20 - xg - 3):.0f}" height="24" rx="7" fill="{DEEP}" fill-opacity="0.3"/>')
    s.append(_txt(X0 + 10, Y1 + 47, "фаза 1 · накапливаются клиенты", 12, "700", "#ffffff"))
    s.append(_txt(xg + 13, Y1 + 47, "фаза 2 · накапливаются данные (горизонт метрики)", 12, "700", DEEP))
    return _svg(360, ''.join(s))


# ── Компромисс TTE × TCO ────────────────────────────────────────────────────
def tradeoff_scatter():
    s = []
    X0, Y0, X1, Y1 = 60, 26, 880, 330
    s.append(_axes(X0, Y0, X1, Y1))
    s.append(_txt(X1, Y1 + 22, "TTE, дней →", 12, None, DARK, op=0.6, anchor="end"))
    s.append(_txt(X0 - 8, Y0 - 8, "TCO, т₽", 12, None, DARK, op=0.6))
    px = lambda t: X0 + 40 + t / 90 * (X1 - X0 - 90)
    py = lambda c: Y1 - 20 - c / 800 * (Y1 - Y0 - 50)
    K = 105 * 14
    iso = [(px(t), py(min(780, K / t))) for t in [2.2, 3, 4, 5.5, 7.5, 10, 14, 20, 30, 45, 65, 88]]
    s.append(_poly(iso, DARK, 1.6, dash="5 5", op=0.45))
    PTS = [("Готовый отчёт подрядчика", 5, 700, DEEP), ("Витрина DWH", 14, 105, DEEP),
           ("Флаг CRM + сверки", 67, 70, DEEP), ("Ручная выгрузка", 55, 420, WARN)]
    s.append(_poly([(px(5), py(700)), (px(14), py(105)), (px(67), py(70))], DEEP, 2, op=0.5))
    for name, t, c, col in PTS:
        s.append(f'<circle cx="{px(t):.0f}" cy="{py(c):.0f}" r="7" fill="{col}" fill-opacity="0.9"/>')
    s.append(_txt(px(5) + 12, py(700) - 4, "Готовый отчёт подрядчика: быстро, но дорого", 12, "700", DEEP))
    s.append(_txt(px(55), py(420) - 14, "Ручная выгрузка: за фронтом, проигрывает всегда", 12, "700", WARN, anchor="middle"))
    s.append(_txt(px(14) - 10, py(105) - 14, "Витрина DWH: лучшая интегральная оценка", 12, "700", DEEP, anchor="end"))
    s.append(_txt(px(67), py(70) + 26, "Флаг CRM: дёшево, но решение ждёт", 12, "700", DEEP, anchor="middle"))
    return _svg(360, ''.join(s))


# ── Профили Cost of Delay ───────────────────────────────────────────────────
def cod_profiles():
    s = []
    W, H, GX, GY = 280, 120, 20, 46
    PROF = [
        ("Линейный", "каждый месяц — одинаковая потеря", lambda t: t),
        ("Фиксированный срок", "до даты потерь нет, после — штраф", lambda t: 0.06 if t < 0.55 else 0.95),
        ("Делать сейчас", "штраф уже накапливается и растёт", lambda t: 0.35 + 0.6 * t),
        ("Логарифмический", "основные потери — в начале", lambda t: math.log1p(t * 12) / math.log1p(12)),
        ("Незаметный", "технический долг: потери долго не видны", lambda t: (math.exp(2.6 * t) - 1) / (math.exp(2.6) - 1)),
        ("Разовая стоимость", "единовременная потеря", lambda t: 0.82),
    ]
    for i, (name, sub, f) in enumerate(PROF):
        cx, cy = 10 + (i % 3) * (W + GX), 8 + (i // 3) * (H + GY + 30)
        s.append(_plate(cx, cy, W, H + 34, "#fbfdfc"))
        s.append(_txt(cx + 14, cy + 22, name, 13, "700"))
        x0, y0, x1, y1 = cx + 14, cy + 32, cx + W - 14, cy + H - 4
        s.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{DARK}" stroke-opacity="0.25" stroke-width="1.2"/>')
        s.append(_poly([(x0 + t * (x1 - x0), y1 - 4 - f(t) * (y1 - y0 - 8))
                        for t in [j / 36 for j in range(37)]], DEEP, 2.2))
        s.append(_txt(cx + 14, cy + H + 22, sub, 11, None, DARK, op=0.7))
    return _svg(2 * (120 + 46 + 30) + 10, ''.join(s))


# ── Матрица категорий данных (2×2 из деки, упрощённая) ──────────────────────
def categories_matrix():
    s = []
    CELLS = [
        (70, 20, "Структурированные · внутренние", "витрины, CRM, транзакции, статусы",
         "здесь принимаются решения", True),
        (480, 20, "Структурированные · внешние", "рынок, бюро, партнёрские фиды",
         "база сравнения и бенчмарки", False),
        (70, 170, "Тексты и речь · внутренние", "звонки, обращения, договоры",
         "ИИ читает целиком — новый источник", False),
        (480, 170, "Тексты · внешние", "отзывы, соцсети, СМИ",
         "ранние сигналы рынка", False),
    ]
    s.append(_txt(460, 14, "структурированные ← → текстовые", 12, "700", DARK, op=0.55, anchor="middle"))
    for x, y, t, sub, note, accent in CELLS:
        s.append(_plate(x, y, 370, 130, "#eaf7f0" if accent else "#ffffff"))
        s.append(_txt(x + 18, y + 30, t, 14.5, "800", DEEP if accent else DARK))
        s.append(_txt(x + 18, y + 56, sub, 12.5, None, DARK, op=0.8))
        s.append(_txt(x + 18, y + 82, note, 12.5, "700", DEEP if accent else DARK))
    s.append(_txt(24, 165, "внутр.", 12, "700", DARK, op=0.55))
    s.append(_txt(20, 185, "↕", 14, "700", DARK, op=0.55))
    s.append(_txt(14, 205, "внешние", 12, "700", DARK, op=0.55))
    s.append(_plate(70, 316, 780, 54, "#eef5f1", rx=10, bar=4))
    s.append(_txt(96, 338, "Решения принимаются по левому верхнему квадранту —", 13.5, "700"))
    s.append(_txt(96, 358, "а причина происходящего почти всегда лежит в остальных трёх.", 13, None, DARK, op=0.8))
    return _svg(390, ''.join(s))
