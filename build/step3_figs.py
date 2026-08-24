# -*- coding: utf-8 -*-
"""Фигуры к материалам об ИИ-инструментах и методах анализа.

Один расчёт — два вывода. Версия для страниц повторяет то, что участник
видит в тетради, вместе с заголовком; версия для слайдов идёт без заголовка
(его роль играет заголовок слайда) и с более крупными подписями: минимальный
кегль в кадре 1920×1080 — 26 px.

    python3 build/step3_figs.py

Данные берутся из репозитория практики: он клонируется рядом.
"""
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                   # noqa: E402
import numpy as np                                                # noqa: E402
import pandas as pd                                               # noqa: E402
from sklearn.cluster import KMeans                                # noqa: E402
from sklearn.preprocessing import StandardScaler                  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
ПРАКТИКА = ROOT.parent / "a360-workspace"
ДЕКИ = ROOT.parent / "kk_sber_a360" / "illustrations" / "png"

ACC, WARN, INK, BLUE = "#20BA72", "#E4572E", "#2E3641", "#1B7FD6"
ПАЛИТРА = ["#20BA72", "#1B7FD6", "#E4572E"]

# Кегли: слева — страница (читается с экрана вплотную), справа — слайд.
СТРАНИЦА = {"base": 11, "title": 12.5, "label": 10.5, "legend": 10.5,
            "месяцы": [1, 4, 7, 10], "формат": "%m.%Y"}
# На слайде подписи крупнее: меток по оси времени помещается вдвое меньше,
# и год печатается двумя знаками — иначе подписи наезжают друг на друга.
СЛАЙД = {"base": 15, "title": 0, "label": 15, "legend": 15,
         "месяцы": [1, 7], "формат": "%m.%y"}


def _оформить(ax, режим, x=None, y=None, заголовок=None):
    if заголовок and режим["title"]:
        ax.set_title(заголовок, fontsize=режим["title"], pad=12,
                     fontweight="bold", color=INK)
    if x:
        ax.set_xlabel(x, fontsize=режим["label"])
    if y:
        ax.set_ylabel(y, fontsize=режим["label"])
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.25)
    ax.tick_params(labelsize=режим["base"])


def _даты(ax, режим):
    """Меток по оси времени — не больше, чем помещается при текущем кегле."""
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=режим["месяцы"]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter(режим["формат"]))


def _сохранить(fig, имя, слайд):
    """Страничная версия — в assets, слайдовая — ещё и в иллюстрации деки."""
    путь = ROOT / "assets" / имя
    fig.savefig(путь, dpi=140, bbox_inches="tight", facecolor="white")
    if слайд:
        fig.savefig(ДЕКИ / имя, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  {имя}{' (+дека)' if слайд else ''}")


def данные_клиентов():
    return pd.read_csv(ПРАКТИКА / "data/clients/clients_sample.csv",
                       sep=";", decimal=",", encoding="utf-8-sig")


def данные_ряда():
    return pd.read_csv(ПРАКТИКА / "data/series/portfolio_operations_daily.csv",
                       sep=";", decimal=",", encoding="utf-8-sig",
                       parse_dates=["дата"], index_col="дата")["объём_операций_млн_руб"]


def очистить(ряд):
    """Тот же порядок снятия сезонности, что в тетради практики."""
    к_недели = ряд.groupby(ряд.index.dayofweek).mean() / ряд.mean()
    без_недели = ряд / к_недели[ряд.index.dayofweek].values
    к_дня = без_недели.groupby(без_недели.index.day).mean() / без_недели.mean()
    без_дня = без_недели / к_дня[без_недели.index.day].values
    мес = без_дня.resample("MS").mean()
    скользящее = мес.rolling(12, center=True, min_periods=12).mean()
    отношение = (мес / скользящее).dropna()
    к_года = отношение.groupby(отношение.index.month).mean()
    к_года = к_года / к_года.mean()
    return мес / к_года[мес.index.month].values


def кластеры(режим, имя, слайд):
    клиенты = данные_клиентов()
    X2 = StandardScaler().fit_transform(клиенты[["возраст", "доход_тыс_руб"]])
    метки = KMeans(n_clusters=2, random_state=42, n_init=10).fit(X2).labels_

    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    for k in range(2):
        m = метки == k
        ax.scatter(клиенты.loc[m, "возраст"], клиенты.loc[m, "доход_тыс_руб"],
                   s=10, alpha=0.35, color=ПАЛИТРА[k], label=f"сегмент {k + 1}")
    ax.scatter(клиенты["возраст"].mean(), клиенты["доход_тыс_руб"].mean(),
               marker="X", s=300, color=INK, edgecolor="white", linewidth=1.5,
               zorder=5, label="«средний клиент»")
    ax.legend(loc="upper left", fontsize=режим["legend"])
    _оформить(ax, режим, x="возраст, лет", y="доход, тыс. руб. в месяц",
              заголовок="Два сегмента — и «средний клиент» между ними")
    _сохранить(fig, имя, слайд)


def тренд_сырой(режим, имя, слайд):
    месяцы = данные_ряда().resample("MS").sum()
    x = np.arange(len(месяцы))
    к, с = np.polyfit(x, месяцы.values, 1)
    будущее = pd.date_range(месяцы.index[-1] + pd.DateOffset(months=1),
                            periods=6, freq="MS")

    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    ax.plot(месяцы.index, месяцы.values, color=INK, lw=2, label="факт, сумма за месяц")
    ax.plot(месяцы.index, к * x + с, color=ACC, lw=2.4, ls="--", label="линия тренда")
    ax.plot(будущее, к * np.arange(len(месяцы), len(месяцы) + 6) + с,
            color=ACC, lw=3, label="продление тренда")
    ax.legend(fontsize=режим["legend"])
    _даты(ax, режим)
    _оформить(ax, режим, y="млн руб. в месяц",
              заголовок="Взгляд первый: портфель растёт")
    _сохранить(fig, имя, слайд)


def тренд_очищенный(режим, имя, слайд):
    очищенный = очистить(данные_ряда())
    x12 = np.arange(12)
    к12, с12 = np.polyfit(x12, очищенный.tail(12).values, 1)
    будущее = pd.date_range(очищенный.index[-1] + pd.DateOffset(months=1),
                            periods=6, freq="MS")

    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    ax.plot(очищенный.index, очищенный.values, color=INK, lw=2,
            label="ряд без сезонности")
    ax.plot(очищенный.tail(12).index, к12 * x12 + с12, color=WARN, lw=2.4, ls="--",
            label="тренд последних 12 месяцев")
    ax.plot(будущее, к12 * np.arange(12, 18) + с12, color=WARN, lw=3,
            label="продление тренда")
    ax.legend(fontsize=режим["legend"])
    _даты(ax, режим)
    _оформить(ax, режим, y="млн руб. в день",
              заголовок="Взгляд второй: без сезонности портфель падает")
    _сохранить(fig, имя, слайд)


def _холт(история, горизонт, альфа, бета):
    уровень, тренд = история[0], история[1] - история[0]
    for з in история[1:]:
        уровень, прежний = альфа * з + (1 - альфа) * (уровень + тренд), уровень
        тренд = бета * (уровень - прежний) + (1 - бета) * тренд
    return np.array([уровень + тренд * (h + 1) for h in range(горизонт)])


def прогноз(режим, имя, слайд):
    очищенный = очистить(данные_ряда())
    значения = очищенный.values
    Г = 3

    def проверить(модель):
        ошибки = [np.abs(модель(значения[:т], Г) - значения[т:т + Г]).mean()
                  for т in range(len(значения) - 12, len(значения) - Г + 1)]
        return np.mean(ошибки), ошибки

    сетка = sorted((проверить(lambda и, г, a=a, b=b: _холт(и, г, a, b))[0], a, b)
                   for a in (0.3, 0.5, 0.7, 0.8) for b in (0.05, 0.1, 0.2))
    _, альфа, бета = сетка[0]
    ошибка, ошибки = проверить(lambda и, г: _холт(и, г, альфа, бета))
    предсказание = _холт(значения, 6, альфа, бета)
    сигма = np.std(ошибки) + np.mean(ошибки)
    полоса = 1.28 * сигма * np.sqrt(np.arange(1, 7) / Г)

    к12, с12 = np.polyfit(np.arange(12), значения[-12:], 1)
    будущее = pd.date_range(очищенный.index[-1] + pd.DateOffset(months=1),
                            periods=6, freq="MS")

    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    ax.plot(очищенный.index[-24:], значения[-24:], color=INK, lw=2.2, label="факт")
    ax.plot(будущее, предсказание, color=BLUE, lw=3, label="прогноз победившей модели")
    ax.fill_between(будущее, предсказание - полоса, предсказание + полоса,
                    color=BLUE, alpha=0.15, label="полоса неопределённости")
    ax.plot(будущее, к12 * np.arange(12, 18) + с12, color=WARN, lw=2, ls=":",
            label="продление линейного тренда")
    ax.legend(fontsize=режим["legend"], loc="upper left")
    _даты(ax, режим)
    _оформить(ax, режим, y="млн руб. в день",
              заголовок="Взгляд третий: проверенная модель видит восстановление")
    _сохранить(fig, имя, слайд)
    print(f"  средняя ошибка победившей модели: {ошибка:.2f}; "
          f"параметры {альфа}/{бета}")


if __name__ == "__main__":
    if not ПРАКТИКА.exists():
        sys.exit(f"нет репозитория практики {ПРАКТИКА}: он клонируется рядом")
    ДЕКИ.mkdir(parents=True, exist_ok=True)
    print("Фигуры для страниц:")
    кластеры(СТРАНИЦА, "step3_clusters_2d.png", слайд=False)
    тренд_сырой(СТРАНИЦА, "step3_trend_raw.png", слайд=False)
    тренд_очищенный(СТРАНИЦА, "step3_trend_clean.png", слайд=False)
    прогноз(СТРАНИЦА, "step3_forecast.png", слайд=False)
    print("Фигуры для слайдов (без внутреннего заголовка):")
    кластеры(СЛАЙД, "step3_clusters_2d_slide.png", слайд=True)
    тренд_сырой(СЛАЙД, "step3_trend_raw_slide.png", слайд=True)
    тренд_очищенный(СЛАЙД, "step3_trend_clean_slide.png", слайд=True)
    прогноз(СЛАЙД, "step3_forecast_slide.png", слайд=True)
