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
            "месяцы": [1, 4, 7, 10], "формат": "%m.%Y", "полотно": (9.6, 8.3)}
# На слайде подписи крупнее: меток по оси времени помещается вдвое меньше,
# и год печатается двумя знаками — иначе подписи наезжают друг на друга.
# Коробка слайда — 912×432, то есть примерно два к одному. Многопанельная
# фигура в пропорциях страницы ужимается по бокам, и половина кадра остаётся
# пустой, поэтому для слайда она собирается широкой.
СЛАЙД = {"base": 15, "title": 0, "label": 15, "legend": 15,
         "месяцы": [1, 7], "формат": "%m.%y", "полотно": (14.4, 6.8)}


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


def _даты(ax, режим, редко=False):
    """Меток по оси времени — не больше, чем помещается при текущем кегле.

    редко=True — для фигур, где ось делится между несколькими панелями:
    там подписи наезжают друг на друга уже при четырёх метках в год.
    """
    import matplotlib.dates as mdates
    месяцы = [1, 7] if редко else режим["месяцы"]
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=месяцы))
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


def слои(ряд):
    """Ряд после снятия каждой сезонности — от самого длинного цикла к самому
    короткому. Тот же порядок, что в тетради практики: годовая, внутримесячная,
    недельная. Возвращает список (подпись, ряд) и сезонные коэффициенты."""
    мес = ряд.resample("MS").mean()
    скользящее = мес.rolling(12, center=True, min_periods=12).mean()
    отношение = (мес / скользящее).dropna()
    к_года = отношение.groupby(отношение.index.month).mean()
    к_года = к_года / к_года.mean()
    без_года = ряд / к_года[ряд.index.month].values

    к_дня = без_года.groupby(без_года.index.day).mean() / без_года.mean()
    без_дня = без_года / к_дня[без_года.index.day].values

    к_недели = без_дня.groupby(без_дня.index.dayofweek).mean() / без_дня.mean()
    без_недели = без_дня / к_недели[без_дня.index.dayofweek].values

    цепочка = [("как есть", ряд),
               ("снята годовая", без_года),
               ("снята внутримесячная", без_дня),
               ("снята недельная", без_недели)]
    return цепочка, {"год": к_года, "день": к_дня, "неделя": к_недели}


def очистить(ряд):
    """Месячный ряд после снятия всех трёх сезонностей."""
    цепочка, _ = слои(ряд)
    return цепочка[-1][1].resample("MS").mean()


ПРИЗНАКИ = ["возраст", "доход_тыс_руб", "средний_остаток_тыс_руб",
            "операций_в_месяц", "доля_цифровых_операций"]


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


СЕГМЕНТЫ = {
    "массовый цифровой": "#1B7FD6",
    "премиальный в отделении": "#E4572E",
    "премиальный цифровой": "#20BA72",
}


def _разбиение():
    """Три сегмента по пяти признакам и их порядок: сначала массовый."""
    клиенты = данные_клиентов()
    X5 = StandardScaler().fit_transform(клиенты[ПРИЗНАКИ])
    метки = KMeans(n_clusters=3, random_state=42, n_init=10).fit_predict(X5)
    клиенты = клиенты.assign(кластер=метки)
    # порядок: массовый (самый молодой), затем премиальные — по доле цифровых
    профиль = клиенты.groupby("кластер")[ПРИЗНАКИ].mean()
    массовый = profile_min = профиль["возраст"].idxmin()
    премиальные = профиль.drop(index=массовый).sort_values("доля_цифровых_операций")
    порядок = [массовый] + list(премиальные.index)
    имена = dict(zip(порядок, СЕГМЕНТЫ))
    клиенты["имя"] = клиенты["кластер"].map(имена)
    return клиенты, профиль


def сверху_и_в_3d(режим, имя, слайд):
    """Одни и те же наблюдения в двух проекциях: сверху и в трёх измерениях.

    Слева — привычный вид «возраст против дохода»: два премиальных сегмента
    лежат друг на друге и выглядят одним облаком. Справа добавлена третья ось —
    доля операций в цифровых каналах, — и облако распадается на два слоя.
    """
    клиенты, _ = _разбиение()
    ширина, высота = режим["полотно"]
    fig = plt.figure(figsize=(ширина, высота * 0.58))
    # правой панели нужно больше места: у трёхмерных осей подписи уходят
    # за пределы своей клетки
    сетка = fig.add_gridspec(1, 2, width_ratios=[1, 1.25], wspace=0.16)
    сверху = fig.add_subplot(сетка[0, 0])
    объём = fig.add_subplot(сетка[0, 1], projection="3d")

    for название, цвет in СЕГМЕНТЫ.items():
        м = клиенты["имя"] == название
        сверху.scatter(клиенты.loc[м, "возраст"], клиенты.loc[м, "доход_тыс_руб"],
                       s=9, alpha=0.35, color=цвет, label=название)
        объём.scatter(клиенты.loc[м, "возраст"], клиенты.loc[м, "доход_тыс_руб"],
                      клиенты.loc[м, "доля_цифровых_операций"],
                      s=6, alpha=0.35, color=цвет, label=название)

    сверху.set_xlabel("возраст, лет", fontsize=режим["label"])
    сверху.set_ylabel("доход, тыс. руб. в месяц", fontsize=режим["label"])
    сверху.spines[["top", "right"]].set_visible(False)
    сверху.grid(alpha=0.25)
    сверху.tick_params(labelsize=режим["base"])
    сверху.set_title("Вид сверху: два облака", fontsize=режим["base"] + 2,
                     fontweight="bold", color=INK, pad=10)

    объём.set_xlabel("возраст", fontsize=режим["label"], labelpad=-4)
    объём.set_ylabel("доход", fontsize=режим["label"], labelpad=-4)
    # подпись вертикальной оси уходит за край кадра, поэтому она перенесена
    # в заголовок панели: у трёхмерных осей место под неё не резервируется
    объём.view_init(elev=16, azim=-58)
    объём.tick_params(labelsize=режим["base"] - 2, pad=-2)
    объём.set_title("Поворот: облаков три", fontsize=режим["base"] + 2,
                    fontweight="bold", color=INK, pad=2)
    # на слайде это пояснение живёт в подзаголовке, внутри кадра оно спорит
    # с легендой за место
    if режим["title"]:
        объём.text2D(0.5, 0.02, "вертикальная ось — доля операций в цифровых каналах",
                     transform=объём.transAxes, ha="center",
                     fontsize=режим["base"], color="#5d6873")

    ручки = [plt.Line2D([], [], marker="o", linestyle="", markersize=9,
                        color=цвет, label=название)
             for название, цвет in СЕГМЕНТЫ.items()]
    # легенда вынесена под кадр: файл сохраняется с bbox_inches="tight",
    # поэтому она попадает в картинку и не спорит с подписью оси
    fig.legend(handles=ручки, loc="upper center", ncol=3, frameon=False,
               fontsize=режим["legend"], bbox_to_anchor=(0.5, 0.055))
    if режим["title"]:
        fig.suptitle("Третий сегмент виден только в третьем измерении",
                     fontsize=режим["title"] + 1, fontweight="bold", color=INK,
                     y=0.995)
    fig.subplots_adjust(left=0.06, right=0.9, top=0.84, bottom=0.17)
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


def каскад(режим, имя, слайд, окно=12):
    """Снятие сезонности сверху вниз: четыре панели с общей осью времени.

    Каждая следующая панель — тот же ряд, из которого убран ещё один цикл;
    сверху самый длинный (годовой), внизу самый короткий (недельный).

    На каждой панели две линии: месячное среднее и прямая тренда по последним
    `окно` месяцам. Тренд считается в одном и том же окне на всех панелях —
    иначе сравнение было бы подтасовкой, — и именно он показывает главное:
    на исходном ряде прямая идёт вверх, после снятия годовой сезонности та же
    прямая в том же окне идёт вниз.

    Масштаб по вертикали общий у всех панелей: иначе выпрямление ряда
    читается как изменение уровня, а не как снятие колебаний.
    """
    ряд = данные_ряда()
    цепочка, _ = слои(ряд)

    все = np.concatenate([с.values for _, с in цепочка])
    низ, верх = все.min(), np.percentile(все, 99.7)
    поле = (верх - низ) * 0.08

    fig, axes = plt.subplots(len(цепочка), 1, sharex=True,
                             figsize=режим["полотно"])
    for i, (ax, (подпись, кусок)) in enumerate(zip(axes, цепочка)):
        последний = i == len(цепочка) - 1
        ax.plot(кусок.index, кусок.values, color="#c2cad3", lw=0.6, alpha=0.65,
                label="день" if i == 0 else None)
        помесячно = кусок.resample("MS").mean()
        ax.plot(помесячно.index, помесячно.values, color="#5d6873", lw=1.8,
                label="месячное среднее" if i == 0 else None)

        хвост = помесячно.tail(окно)
        наклон, сдвиг = np.polyfit(np.arange(окно), хвост.values, 1)
        растёт = наклон > 0
        ax.plot(хвост.index, наклон * np.arange(окно) + сдвиг,
                color=WARN if растёт else ACC, lw=3.4,
                label=f"тренд за {окно} месяцев" if i == 0 else None)
        ax.annotate(f"{наклон:+.1f} млн/мес",
                    xy=(хвост.index[окно // 2], наклон * (окно // 2) + сдвиг),
                    xytext=(0, 26 if растёт else -34), textcoords="offset points",
                    ha="center", fontsize=режим["base"] + 1, fontweight="bold",
                    color=WARN if растёт else ACC)

        ax.set_ylim(низ - поле, верх + поле)
        ax.text(0.008, 0.845, подпись, transform=ax.transAxes,
                fontsize=режим["base"] + 1, fontweight="bold",
                color=INK if последний else "#5d6873")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=0.2)
        ax.tick_params(labelsize=режим["base"])
    _даты(axes[-1], режим, редко=True)
    axes[len(цепочка) // 2].set_ylabel("млн руб. в день", fontsize=режим["label"])
    # легенда общая и вынесена под панели: внутри любой из них она перекрывает
    # либо подпись слоя, либо саму линию тренда
    fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=3,
               fontsize=режим["legend"], frameon=False,
               bbox_to_anchor=(0.5, -0.035))
    if режим["title"]:
        axes[0].set_title("Один и тот же тренд до и после снятия сезонности",
                          fontsize=режим["title"], pad=12, fontweight="bold",
                          color=INK)
    fig.subplots_adjust(hspace=0.14)
    _сохранить(fig, имя, слайд)


def градиент(режим, имя, слайд, месяцев=None):
    """Те же слои, наложенные друг на друга: видно, как ряд сходится к итогу.

    Накладывать дневные ряды бесполезно — недельная пила есть во всех трёх
    промежуточных состояниях, и они сливаются в одно пятно. Поэтому слои
    показаны линиями уровня (месячное среднее): каждая следующая плотнее
    предыдущей, и хорошо видно, как линия распрямляется шаг за шагом.
    Дневной ряд «как есть» остаётся фоном, чтобы был виден масштаб колебаний.
    """
    ряд = данные_ряда()
    цепочка, _ = слои(ряд)
    if месяцев:
        начало = ряд.index[-1] - pd.DateOffset(months=месяцев)
        цепочка = [(подпись, с[с.index >= начало]) for подпись, с in цепочка]

    fig, ax = plt.subplots(figsize=(режим["полотно"][0], режим["полотно"][1] * 0.62))
    фон = цепочка[0][1]
    # фон без подписи в легенде: серая штриховка читается сама, а лишняя
    # строка легенды на слайде отнимает заметную часть кадра
    ax.plot(фон.index, фон.values, color="#9aa5b1", lw=0.5, alpha=0.26)

    прозрачность = np.linspace(0.30, 0.62, len(цепочка) - 1)
    толщина = np.linspace(1.6, 2.4, len(цепочка) - 1)
    коротко = {"как есть": "как есть", "снята годовая": "− годовая",
               "снята внутримесячная": "− внутримесячная"}
    for (подпись, кусок), альфа, лв in zip(цепочка[:-1], прозрачность, толщина):
        уровень = кусок.resample("MS").mean()
        ax.plot(уровень.index, уровень.values, color=BLUE, lw=лв, alpha=альфа,
                label=коротко[подпись])
    итог = цепочка[-1][1].resample("MS").mean()
    ax.plot(итог.index, итог.values, color=ACC, lw=3.2,
            label="− недельная: итог")
    ax.legend(fontsize=режим["legend"], loc="upper left", ncol=4,
              framealpha=0.92, columnspacing=1.1, handlelength=1.6)
    # границы по размаху дневного ряда, а не от нуля: иначе половина кадра пуста
    ax.set_ylim(np.percentile(фон.values, 0.5) * 0.9,
                np.percentile(фон.values, 99.7) * 1.16)
    _даты(ax, режим, редко=True)
    _оформить(ax, режим, y="млн руб. в день",
              заголовок="Каждый снятый цикл распрямляет линию уровня")
    _сохранить(fig, имя, слайд)


def сезонные_коэффициенты(режим, имя, слайд):
    """Три коэффициента в том же порядке, что и панели каскада."""
    _, к = слои(данные_ряда())
    мес_имена = ["янв", "фев", "мар", "апр", "май", "июн",
                 "июл", "авг", "сен", "окт", "ноя", "дек"]
    дни_нед = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 3.6))
    axes[0].bar(мес_имена, к["год"].values, color=ACC)
    axes[0].set_title("Месяц года", fontsize=режим["base"] + 1,
                      fontweight="bold", color=INK)
    axes[1].plot(к["день"].index, к["день"].values, color=ACC, lw=2.4)
    axes[1].set_title("День месяца", fontsize=режим["base"] + 1,
                      fontweight="bold", color=INK)
    axes[2].bar(дни_нед, к["неделя"].values, color=ACC)
    axes[2].set_title("День недели", fontsize=режим["base"] + 1,
                      fontweight="bold", color=INK)
    for ax in axes:
        ax.axhline(1, color=INK, lw=0.9, ls=":")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=0.25)
        ax.tick_params(labelsize=режим["base"])
    axes[0].set_ylabel("коэффициент", fontsize=режим["label"])
    fig.tight_layout()
    _сохранить(fig, имя, слайд)


if __name__ == "__main__":
    if not ПРАКТИКА.exists():
        sys.exit(f"нет репозитория практики {ПРАКТИКА}: он клонируется рядом")
    ДЕКИ.mkdir(parents=True, exist_ok=True)
    print("Фигуры для страниц:")
    кластеры(СТРАНИЦА, "step3_clusters_2d.png", слайд=False)
    сверху_и_в_3d(СТРАНИЦА, "step3_clusters_3d.png", слайд=False)
    тренд_сырой(СТРАНИЦА, "step3_trend_raw.png", слайд=False)
    каскад(СТРАНИЦА, "step3_cascade.png", слайд=False)
    градиент(СТРАНИЦА, "step3_gradient.png", слайд=False)
    сезонные_коэффициенты(СТРАНИЦА, "step3_seasonality.png", слайд=False)
    тренд_очищенный(СТРАНИЦА, "step3_trend_clean.png", слайд=False)
    прогноз(СТРАНИЦА, "step3_forecast.png", слайд=False)
    print("Фигуры для слайдов (без внутреннего заголовка):")
    кластеры(СЛАЙД, "step3_clusters_2d_slide.png", слайд=True)
    сверху_и_в_3d(СЛАЙД, "step3_clusters_3d_slide.png", слайд=True)
    тренд_сырой(СЛАЙД, "step3_trend_raw_slide.png", слайд=True)
    каскад(СЛАЙД, "step3_cascade_slide.png", слайд=True)
    градиент(СЛАЙД, "step3_gradient_slide.png", слайд=True)
    сезонные_коэффициенты(СЛАЙД, "step3_seasonality_slide.png", слайд=True)
    тренд_очищенный(СЛАЙД, "step3_trend_clean_slide.png", слайд=True)
    прогноз(СЛАЙД, "step3_forecast_slide.png", слайд=True)
