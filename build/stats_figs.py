# -*- coding: utf-8 -*-
"""Фигуры теоретического материала «Связь и причинность».

Два источника данных, и оба честные:
  * квартет Анскомба — опубликованные значения из статьи 1973 года, дословно;
  * всё остальное считается на учебном стенде, как и в остальных материалах.

    ./run.sh up   (в репозитории практики)
    python3 build/stats_figs.py

Рисунки сохраняются в `assets/stat_*.svg` и вставляются в страницу и в деку.
"""
import os
import pathlib

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "path"
matplotlib.rcParams["font.size"] = 11
matplotlib.rcParams["font.family"] = "DejaVu Sans"
import matplotlib.pyplot as plt                                    # noqa: E402
import numpy as np                                                 # noqa: E402
import psycopg2                                                    # noqa: E402
import psycopg2.extras                                             # noqa: E402

ACC, DEEP, WARN, INK, LINE = "#20BA72", "#128a53", "#E4572E", "#2E3641", "#c9d4cd"
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets"


def rows(sql):
    conn = psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=int(os.environ.get("PGPORT", "5433")),
        dbname=os.environ.get("PGDATABASE", "bank_training"),
        user=os.environ.get("PGUSER", "bank_user"),
        password=os.environ.get("PGPASSWORD", "bank_pass"))
    with conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql)
        данные = [dict(r) for r in cur.fetchall()]
    conn.close()
    return данные


def оформить(ax, заголовок, x=None, y=None, размер=12.5):
    ax.set_title(заголовок, fontsize=размер, color=INK, pad=10, fontweight="bold")
    if x:
        ax.set_xlabel(x, fontsize=10.5, color=INK)
    if y:
        ax.set_ylabel(y, fontsize=10.5, color=INK)
    ax.spines[["top", "right"]].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(LINE)
    ax.tick_params(colors=INK, labelsize=10)
    ax.set_axisbelow(True)


def сохранить(fig, имя):
    OUT.mkdir(exist_ok=True)
    путь = OUT / имя
    fig.savefig(путь, format="svg", bbox_inches="tight", transparent=True, dpi=140)
    plt.close(fig)
    print(f"  {путь.name}: {путь.stat().st_size // 1024} КБ")


def _месяцы():
    данные = rows("""
        SELECT to_char(date_trunc('month', a.submitted_at), 'YYYY-MM') AS месяц,
               count(*) AS заявок,
               count(DISTINCT d.application_id) AS выдач
          FROM raw_applications a
          LEFT JOIN raw_disbursements d USING (application_id)
         WHERE NOT a.is_test
         GROUP BY 1 ORDER BY 1""")
    x = np.array([float(r["заявок"]) for r in данные])
    y = np.array([float(r["выдач"]) for r in данные])
    подписи = [r["месяц"] for r in данные]
    return x, y, подписи


def _прямая(x, y):
    k, b = np.polyfit(x, y, 1)
    ŷ = k * x + b
    r = float(np.corrcoef(x, y)[0, 1])
    r2 = 1 - ((y - ŷ) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return k, b, r, r2


# ── 1. Что видно на графике и чего не видно в одном числе ───────────────────
def связь():
    """Заявки и выдачи по месяцам: одна неполная точка меняет и связь, и прямую."""
    x, y, подписи = _месяцы()
    k8, b8, r8, r2_8 = _прямая(x, y)
    k7, b7, r7, r2_7 = _прямая(x[:-1], y[:-1])

    fig, ax = plt.subplots(figsize=(8.4, 4.2), dpi=110)
    ax.scatter(x[:-1], y[:-1], s=64, color=ACC, zorder=3, label="полные месяцы")
    ax.scatter(x[-1:], y[-1:], s=90, color=WARN, zorder=3, marker="D",
               label=f"неполный месяц ({подписи[-1]})")
    сетка = np.linspace(0, x.max() * 1.08, 50)
    ax.plot(сетка, k7 * сетка + b7, color=DEEP, linewidth=2.2,
            label=f"по полным месяцам: R² = {r2_7:.3f}".replace(".", ","))
    ax.plot(сетка, k8 * сетка + b8, color=WARN, linewidth=2, linestyle="--",
            label=f"со всеми точками: R² = {r2_8:.3f}".replace(".", ","))
    легенда = ax.legend(frameon=True, fontsize=10, loc="upper left")
    легенда.get_frame().set_edgecolor(LINE)
    легенда.get_frame().set_facecolor("#ffffff")
    оформить(ax, "Заявки и выдачи по месяцам: одна точка меняет вывод",
             "заявок за месяц", "выдач за месяц")
    ax.grid(alpha=.18)
    сохранить(fig, "stat_relation.svg")
    return dict(r8=r8, r7=r7, k8=k8, k7=k7, r2_8=r2_8, r2_7=r2_7, n=len(x))


# ── 2. Связи нет ────────────────────────────────────────────────────────────
def нет_связи():
    """Сумма заявки и срок андеррайтинга: облако без наклона."""
    данные = rows("""
        SELECT a.amount_requested AS сумма, e.hours AS часы
          FROM v_stage_events_clean e
          JOIN v_applications_clean a USING (application_id)
         WHERE e.stage = 'Андеррайтинг'""")
    x = np.array([float(r["сумма"]) for r in данные]) / 1e6
    y = np.array([float(r["часы"]) for r in данные])
    r = float(np.corrcoef(x, y)[0, 1])

    fig, ax = plt.subplots(figsize=(8.4, 3.8), dpi=110)
    # 2654 точки векторами дают полмегабайта: облако растеризуем,
    # оси и подписи остаются векторными и читаемыми при печати.
    ax.scatter(x, y, s=8, color=ACC, alpha=.28, edgecolors="none",
               rasterized=True)
    k, b = np.polyfit(x, y, 1)
    сетка = np.linspace(x.min(), x.max(), 50)
    ax.plot(сетка, k * сетка + b, color=WARN, linewidth=2,
            label=f"прямая наименьших квадратов: r = {r:.2f}".replace(".", ","))
    легенда = ax.legend(frameon=True, fontsize=10, loc="upper right")
    легенда.get_frame().set_edgecolor(LINE)
    оформить(ax, f"Сумма заявки и срок андеррайтинга: {len(x)} заявок",
             "сумма заявки, млн ₽", "часы")
    ax.grid(alpha=.18)
    сохранить(fig, "stat_norelation.svg")
    return dict(r=r, n=len(x))


# ── 3. Квартет Анскомба ─────────────────────────────────────────────────────
# Значения из статьи: F. J. Anscombe, «Graphs in Statistical Analysis»,
# The American Statistician 27(1), 1973, с. 17–21.
АНСКОМБ = {
    "I":   ([10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5],
            [8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26, 10.84, 4.82, 5.68]),
    "II":  ([10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5],
            [9.14, 8.14, 8.74, 8.77, 9.26, 8.10, 6.13, 3.10, 9.13, 7.26, 4.74]),
    "III": ([10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5],
            [7.46, 6.77, 12.74, 7.11, 7.81, 8.84, 6.08, 5.39, 8.15, 6.42, 5.73]),
    "IV":  ([8, 8, 8, 8, 8, 8, 8, 19, 8, 8, 8],
            [6.58, 5.76, 7.71, 8.84, 8.47, 7.04, 5.25, 12.50, 5.56, 7.91, 6.89]),
}
ПОДПИСИ = {
    "I": "линейная связь",
    "II": "связь есть, но кривая",
    "III": "один выброс тянет прямую",
    "IV": "прямая держится на одной точке",
}


def анскомб():
    fig, оси = plt.subplots(2, 2, figsize=(8.4, 5.2), dpi=110)
    for ось, (имя, (x, y)) in zip(оси.ravel(), АНСКОМБ.items()):
        x, y = np.array(x, float), np.array(y, float)
        k, b = np.polyfit(x, y, 1)
        r = float(np.corrcoef(x, y)[0, 1])
        сетка = np.linspace(2, 20, 20)
        ось.plot(сетка, k * сетка + b, color=WARN, linewidth=1.8, zorder=2)
        ось.scatter(x, y, s=44, color=ACC, zorder=3, edgecolors="white", linewidth=.6)
        ось.set_xlim(2, 20)
        ось.set_ylim(2, 14)
        оформить(ось, f"{имя} · {ПОДПИСИ[имя]}   r = {r:.2f}".replace(".", ","),
                 размер=11)
        ось.grid(alpha=.15)
    fig.suptitle("Одинаковые числа, разные данные: квартет Анскомба",
                 fontsize=13, fontweight="bold", color=INK, y=1.0)
    fig.tight_layout()
    сохранить(fig, "stat_anscombe.svg")
    return {имя: float(np.corrcoef(x, y)[0, 1]) for имя, (x, y) in АНСКОМБ.items()}


# ── 4. Остатки ──────────────────────────────────────────────────────────────
def остатки():
    """Тот же расчёт, но глазами остатков — так проверяют модель."""
    x, y, подписи = _месяцы()
    k, b, r, r2 = _прямая(x, y)
    ост = y - (k * x + b)

    fig, ax = plt.subplots(figsize=(8.4, 3.2), dpi=110)
    цвета = [ACC] * (len(x) - 1) + [WARN]
    ax.bar(range(len(ост)), ост, color=цвета, width=.55)
    ax.axhline(0, color=INK, linewidth=1)
    ax.set_xticks(range(len(подписи)))
    ax.set_xticklabels([п[5:] + "." + п[2:4] for п in подписи])
    оформить(ax, "Остатки: на сколько прямая промахнулась в каждом месяце",
             None, "выдач")
    ax.grid(axis="y", alpha=.18)
    сохранить(fig, "stat_residuals.svg")
    return dict(максимум=float(np.abs(ост).max()))


if __name__ == "__main__":
    print("Фигуры теоретического материала:")
    print("  связь:", связь())
    print("  нет связи:", нет_связи())
    print("  Анскомб:", анскомб())
    print("  остатки:", остатки())
