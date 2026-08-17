# -*- coding: utf-8 -*-
"""Фигуры лонгрида «Разведочный анализ» — из живых данных учебного стенда.

Запускается отдельно от сборки страниц: рисунки сохраняются в `assets/eda_*.svg`,
а `longread_eda.py` просто вставляет их содержимое. Иначе сборка страниц
требовала бы поднятого стенда, а она должна работать всегда.

    ./run.sh up  (в bank-analytics-workshop)
    python3 build/eda_figs.py

Палитра — та же, что у страниц: акцент #20BA72, предупреждение #E4572E.
"""
import os
import pathlib

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "path"      # текст становится кривыми:
matplotlib.rcParams["font.size"] = 11             # шрифта читателя мы не знаем
matplotlib.rcParams["font.family"] = "DejaVu Sans"
import matplotlib.pyplot as plt                                    # noqa: E402
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
        data = [dict(r) for r in cur.fetchall()]
    conn.close()
    return data


def оформить(ax, заголовок, x=None, y=None):
    ax.set_title(заголовок, fontsize=12.5, color=INK, pad=12, fontweight="bold")
    if x:
        ax.set_xlabel(x, fontsize=10.5, color=INK)
    if y:
        ax.set_ylabel(y, fontsize=10.5, color=INK)
    ax.spines[["top", "right"]].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(LINE)
    ax.tick_params(colors=INK, labelsize=10)


def сохранить(fig, имя):
    OUT.mkdir(exist_ok=True)
    путь = OUT / имя
    fig.savefig(путь, format="svg", bbox_inches="tight", transparent=True)
    plt.close(fig)
    print(f"  {путь.name}: {путь.stat().st_size // 1024} КБ")


# ── 1. Распределение длительности: почему среднее обманывает ────────────────
def гистограмма():
    данные = rows("""
        SELECT EXTRACT(EPOCH FROM (left_at - entered_at)) / 3600 AS часы
        FROM raw_stage_events
        WHERE stage = 'Андеррайтинг' AND left_at > entered_at""")
    часы = sorted(float(r["часы"]) for r in данные)
    n = len(часы)
    среднее = sum(часы) / n
    медиана = часы[n // 2]
    p90 = часы[int(n * 0.9)]

    fig, ax = plt.subplots(figsize=(8.4, 3.8), dpi=110)
    ax.hist(часы, bins=45, color=ACC, alpha=.75, edgecolor="white", linewidth=.6)
    # Подписи мер выносим в легенду, а не к линиям: у медианы и среднего
    # значения близкие, и вертикальные надписи налезали друг на друга.
    for значение, подпись, цвет, стиль in (
            (медиана, f"медиана {медиана:.1f} ч".replace(".", ","), DEEP, "-"),
            (среднее, f"среднее {среднее:.1f} ч".replace(".", ","), INK, "--"),
            (p90, f"P90 {p90:.1f} ч".replace(".", ","), WARN, ":")):
        ax.axvline(значение, color=цвет, linestyle=стиль, linewidth=2,
                   label=подпись)
    легенда = ax.legend(frameon=True, fontsize=10.5, loc="upper right",
                        borderpad=.7, labelspacing=.5)
    легенда.get_frame().set_edgecolor(LINE)
    легенда.get_frame().set_facecolor("#ffffff")
    оформить(ax, f"Длительность андеррайтинга: {n} закрытых событий",
             "часы", "число событий")
    сохранить(fig, "eda_hist.svg")
    return dict(медиана=медиана, среднее=среднее, p90=p90, n=n, максимум=часы[-1])


# ── 2. Воронка этапов ──────────────────────────────────────────────────────
def воронка():
    данные = rows("""
        SELECT e.stage AS этап,
               count(DISTINCT e.application_id) AS дошло,
               round(100.0 * count(DISTINCT e.application_id) /
                     (SELECT count(DISTINCT application_id)
                        FROM raw_applications WHERE NOT is_test), 1) AS доля
        FROM raw_stage_events e
        JOIN raw_applications a USING (application_id)
        WHERE NOT a.is_test AND e.left_at IS NOT NULL AND e.left_at > e.entered_at
        GROUP BY e.stage ORDER BY дошло DESC""")
    этапы = [r["этап"] for r in данные][::-1]
    значения = [int(r["дошло"]) for r in данные][::-1]
    доли = [float(r["доля"]) for r in данные][::-1]

    fig, ax = plt.subplots(figsize=(8.4, 3.4), dpi=110)
    ax.barh(этапы, значения, color=[ACC] * len(этапы), height=.62)
    for i, (v, d) in enumerate(zip(значения, доли)):
        ax.text(v + max(значения) * .012, i, f"{v}  ·  {d:.1f} %".replace(".", ","),
                va="center", fontsize=10, color=INK)
    ax.set_xlim(0, max(значения) * 1.22)
    оформить(ax, "Куда доходят заявки", "заявок дошло до этапа")
    ax.grid(axis="x", alpha=.18)
    ax.set_axisbelow(True)
    сохранить(fig, "eda_funnel.svg")
    return данные


# ── 3. Один и тот же этап в разных каналах ─────────────────────────────────
def каналы():
    данные = rows("""
        SELECT a.channel AS канал,
               EXTRACT(EPOCH FROM (e.left_at - e.entered_at)) / 3600 AS часы
        FROM raw_stage_events e
        JOIN raw_applications a USING (application_id)
        WHERE e.stage = 'Андеррайтинг' AND e.left_at > e.entered_at""")
    группы = {}
    for r in данные:
        группы.setdefault(r["канал"], []).append(float(r["часы"]))
    порядок = sorted(группы, key=lambda k: -sorted(группы[k])[len(группы[k]) // 2])

    fig, ax = plt.subplots(figsize=(8.4, 3.6), dpi=110)
    bp = ax.boxplot([группы[k] for k in порядок], vert=False, widths=.55,
                    patch_artist=True, showfliers=False,
                    medianprops=dict(color=WARN, linewidth=2.2),
                    boxprops=dict(facecolor="#d9f0e5", edgecolor=DEEP),
                    whiskerprops=dict(color=DEEP), capprops=dict(color=DEEP))
    ax.set_yticklabels(порядок)
    оформить(ax, "Андеррайтинг по каналам: коробка — половина заявок",
             "часы")
    ax.grid(axis="x", alpha=.18)
    ax.set_axisbelow(True)
    сохранить(fig, "eda_box.svg")
    return {k: sorted(v)[len(v) // 2] for k, v in группы.items()}


# ── 4. Динамика по месяцам ─────────────────────────────────────────────────
def месяцы():
    данные = rows("""
        SELECT to_char(date_trunc('month', a.submitted_at), 'YYYY-MM') AS месяц,
               count(*) AS заявок,
               round(100.0 * count(d.application_id) FILTER (WHERE d.decision = 'Одобрено')
                     / count(*), 1) AS одобрено
        FROM raw_applications a
        LEFT JOIN raw_decisions d USING (application_id)
        WHERE NOT a.is_test
        GROUP BY 1 ORDER BY 1""")
    подписи = [r["месяц"][5:] + "." + r["месяц"][2:4] for r in данные]
    заявок = [int(r["заявок"]) for r in данные]
    одобрено = [float(r["одобрено"]) for r in данные]

    fig, ax = plt.subplots(figsize=(8.4, 3.4), dpi=110)
    ax.plot(подписи, заявок, color=ACC, linewidth=2.6, marker="o", markersize=5)
    оформить(ax, "Заявки и доля одобрений по месяцам", None, "заявок")
    ax.grid(axis="y", alpha=.18)
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(заявок) * 1.25)

    вторая = ax.twinx()
    вторая.plot(подписи, одобрено, color=WARN, linewidth=2, linestyle="--",
                marker="s", markersize=4)
    вторая.set_ylabel("доля одобрений, %", fontsize=10.5, color=WARN)
    вторая.tick_params(colors=WARN, labelsize=10)
    вторая.spines[["top", "left"]].set_visible(False)
    вторая.spines["right"].set_color(LINE)
    вторая.set_ylim(0, 100)
    сохранить(fig, "eda_months.svg")
    return данные


# ── 5. Что нашли проверки данных ───────────────────────────────────────────
def дефекты():
    д = rows("""
        SELECT (SELECT count(*) - count(DISTINCT application_id)
                  FROM raw_applications)                          AS повторы,
               (SELECT count(DISTINCT application_id) FROM raw_applications
                 WHERE is_test OR client_id = 'CL-TEST')          AS тестовые,
               (SELECT count(*) FROM raw_stage_events
                 WHERE left_at < entered_at)                      AS время_назад,
               (SELECT count(*) FROM raw_stage_events
                 WHERE left_at IS NULL)                           AS не_закрыт,
               (SELECT count(*) FROM (SELECT DISTINCT application_id
                                        FROM raw_applications) a
                 LEFT JOIN raw_decisions d USING (application_id)
                WHERE d.application_id IS NULL)                   AS без_решения""")[0]
    подписи = ["повторы строк", "тестовые заявки", "выход раньше входа",
               "этап не закрыт", "заявки без решения"]
    значения = [int(д["повторы"]), int(д["тестовые"]), int(д["время_назад"]),
                int(д["не_закрыт"]), int(д["без_решения"])]
    цвета = [WARN, WARN, WARN, ACC, ACC]      # зелёное — не дефект, а состояние

    fig, ax = plt.subplots(figsize=(8.4, 3.2), dpi=110)
    ax.barh(подписи[::-1], значения[::-1], color=цвета[::-1], height=.6)
    for i, v in enumerate(значения[::-1]):
        ax.text(v + max(значения) * .015, i, str(v), va="center", fontsize=10,
                color=INK, fontweight="bold")
    ax.set_xlim(0, max(значения) * 1.18)
    оформить(ax, "Что нашли четыре проверки до расчётов", "строк или заявок")
    ax.grid(axis="x", alpha=.18)
    ax.set_axisbelow(True)
    сохранить(fig, "eda_defects.svg")
    return dict(zip(подписи, значения))


if __name__ == "__main__":
    print("Фигуры лонгрида «Разведочный анализ»:")
    print("  распределение:", гистограмма())
    print("  воронка:", воронка())
    print("  каналы:", каналы())
    print("  месяцы:", месяцы())
    print("  дефекты:", дефекты())
