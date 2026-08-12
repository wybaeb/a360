# -*- coding: utf-8 -*-
"""Тренажёр «Срок эксперимента» (T2; правка владельца 12.08 — ACCUM-v2).

Претензия прошлого круга: «меняется только горизонтальная шкала, сама имитация
графика накопления достоверности не меняется». Здесь модель переделана так,
что от ползунков меняется САМА ГЕОМЕТРИЯ ВОРОНКИ, а не подписи оси.

Модель (та же нотация, что на слайдах A2/A3 деки Шага 1 — fig_accum2.py и
fig_ci_real.py: n, Z = 1,96, σ, E — допустимая погрешность, она же полуширина
коридора, порог решения):

  1. целевой объём считается до старта — n = (Z·σ/E)² (для долей
     n = Z²·p(1−p)/E²): это та же формула, что в справочнике;
  2. кандидат i попадает в выборку на день i / C, где C — пропускная
     способность (участников в день), и активируется — то есть фактически
     попадает в бакет — на день  a_i = i / C + L · ℓ_i,  где L — лаг
     активации (бегунок), ℓ_i — индивидуальный множитель с медианой 1
     (логнормальный, зафиксирован); набор закрывается, когда активировались
     n участников, поэтому  n(t) = #{ i : a_i ≤ t },  n(t) ≤ n;
  3. полуширина коридора считается из ФАКТИЧЕСКОГО n(t):
     h(t) = Z·σ / √n(t)  — она равна ровно E в тот день, когда n(t) = n;
  4. эффект проявляется за горизонт наблюдения H (бегунок): зрелость
     участника m_i(t) = clip((t − a_i)/H, 0, 1), а бегущая оценка
     x̄(t) = среднее наблюдений по тем, кто уже в бакете, где наблюдение
     участника равно порогу плюс Δ·m_i(t) плюс его собственный разброс;
  5. решение принято (зелёный), когда одновременно h(t) ≤ E и граница
     коридора устойчиво, до конца окна, лежит по одну сторону порога.

Важное следствие пункта 5, из-за которого горизонт H НЕЛЬЗЯ называть
слагаемым срока. После закрытия набора полуширина коридора равна ровно E,
поэтому граница уходит за порог в тот день, когда накопленный эффект
перерастает E, — а это, если эффект на полном горизонте больше E, наступает
заметно раньше, чем у последнего участника пройдут все H дней. В прогоне по
трём пресетам и крайним положениям всех ползунков (21 состояние) день решения
всегда меньше «день закрытия набора + H», а средняя зрелость участников в день
решения — 0,50–0,73, ни разу не 1. Горизонт — это скорость, с которой эффект
проявляется у каждого участника, то есть условие зрелости данных, а не
слагаемое календаря. Поэтому во всех подписях вторая фаза называется
ожиданием, пока эффект перерастёт погрешность E, а не «ожиданием горизонта».

Отсюда честно получаются все четыре угла из разбора владельца:
  медленная метрика + узкий вход — воронка сужается медленно, её узкая часть
      далеко, и после набора эффект ещё долго добирается до E;
  медленная метрика + широкий вход — воронка закрывается в первые дни,
      дальше почти плоский коридор шириной ±E до самого решения;
  быстрая метрика + узкий вход — срок разгоняется именно набором;
  быстрая метрика + широкий вход — результат почти сразу.

Детерминированность сохранена: склонности участников (u, z), множители лага и
дневные сдвиги генерируются один раз на кейс из фиксированного зерна, причём
наблюдения раздаются по РАНГУ активации — поэтому ряд наблюдений один и тот же,
ползунки меняют только скорость набора и сроки. Ряды нормированы (среднее 0,
s.d. 1 для величин; равномерная сетка в случайном порядке для долей), поэтому
оценка сходится к истине, а не к случайному смещению.

Светофор трёх состояний сохранён: красный — коридор шире E; жёлтый — объём
набран, коридор сузился до ±E, но порог внутри; зелёный — коридор устойчиво по
одну сторону порога.

Пресеты — по одному на тему из разбора владельца: розница (новый карточный
продукт, узкий вход по пропускной способности контакт-центра, период
активации, траты меряем полгода), процессный бизнес (срок решения в кредитном
конвейере: вход широкий, метрика быстрая), управление портфелем (редкое
событие, узкий вход, длинный горизонт).

Подключение к сборке (build_pages.py) делает оркестратор: модуль экспортирует
BODY / TITLE / CRUMB в том же виде, что trainer_map.
"""

import json
import math

Z = 1.96

NBSP = " "  # узкий неразрывный пробел для тысяч


def _fi(n):
    return f"{n:,}".replace(",", NBSP)


def _n_share(p, e):
    """Объём выборки для доли: n = Z²·p(1−p)/E²."""
    return math.ceil(Z * Z * p * (1 - p) / (e * e))


def _n_mean(s, e):
    """Объём выборки для средней величины: n = (Z·σ/E)²."""
    return math.ceil((Z * s / e) ** 2)


def _sl(label, unit, hint, lo, hi, step, dflt):
    return dict(label=label, unit=unit, hint=hint, min=lo, max=hi,
                step=step, val=dflt)


# ── Кейсы-пресеты: по одному на тему ────────────────────────────────────────
# sim.kind — 'mean' (средняя величина) или 'share' (доля);
# sim.thr  — порог решения (текущий уровень метрики);
# sim.delta — эффект на полном горизонте (знак = направление);
# sim.sigma — σ планирования (для долей √(p(1−p)));
# sim.E    — допустимая погрешность = целевая полуширина коридора;
# sim.good — с какой стороны порога гипотеза считается подтверждённой;
# sim.shock — амплитуда общего дневного сдвига (сезонность), в единицах метрики.
CASES = [
    dict(
        id="retail",
        tab="Розница · новая карта",
        name="Розница: новый карточный продукт — средние траты по карте",
        n=_n_mean(12.0, 0.9),
        formula="n = (Z·σ / E)² = (1,96 × 12 / 0,9)²",
        unitN="клиентов",
        note=(
            "Пилот нового карточного продукта. Карту выдают ровно столько клиентов "
            "в день, сколько переваривает контакт-центр на новой функции, — это "
            "<b>пропускная способность</b>. Клиент попадает в бакет не в день выдачи, "
            "а когда совершит первую операцию: это <b>лаг активации</b>. Дальше меряем "
            "средние траты по карте, и на то, чтобы они вышли на свой уровень, уходит "
            "около полугода — это <b>горизонт наблюдения</b>. Порог решения — 18,0 т₽ "
            "в месяц, средние траты по действующей карте; новая карта должна дать больше."
        ),
        links=[
            ("определение метрики «Средний чек» — в справочнике",
             "longread_metrics.html#m-u_aov"),
            ("условие активации — метрика «Активация за 30 дн.»",
             "longread_metrics.html#m-act"),
        ],
        sim=dict(kind="mean", thr=18.0, delta=1.5, sigma=12.0, E=0.9,
                 good="above", shock=0.09, scale=1, dec=1,
                 unitY="средние траты по карте, т₽ в месяц",
                 sigmaTxt="σ = 12 т₽ (разброс трат одного клиента)",
                 ETxt="E = 0,9 т₽", thrTxt="порог 18,0 т₽"),
        sliders=dict(
            cap=_sl("Пропускная способность", "клиентов в день",
                    "Сколько клиентов в день контакт-центр проводит через пилот "
                    "новой карты.", 5, 200, 5, 15),
            lag=_sl("Лаг активации", "дней",
                    "Через сколько дней после выдачи клиент делает первую операцию "
                    "и попадает в бакет.", 0, 45, 1, 14),
            hor=_sl("Горизонт наблюдения", "дней",
                    "Сколько времени по клиенту должно пройти, чтобы траты вышли "
                    "на свой уровень.", 30, 270, 10, 180),
        ),
    ),
    dict(
        id="proc",
        tab="Процессный бизнес · конвейер",
        name="Процессный бизнес: срок принятия решения в кредитном конвейере",
        n=_n_mean(9.5, 1.4),
        formula="n = (Z·σ / E)² = (1,96 × 9,5 / 1,4)²",
        unitN="заявок",
        note=(
            "Пилот нового маршрута согласования в кредитном конвейере. Вход широкий: "
            "заявки идут потоком, и <b>пропускная способность</b> измеряется сотнями "
            "в день. <b>Лаг активации</b> короткий — заявка попадает в эксперимент "
            "после автопроверки, на следующий день. Метрика быстрая: <b>горизонт "
            "наблюдения</b> — те несколько дней, за которые заявка проходит конвейер "
            "целиком, включая хвост долгих случаев. Порог решения — 26 часов, текущий "
            "срок; новый маршрут должен уложиться быстрее."
        ),
        links=[
            ("определение метрики «Срок принятия решения (TAT)» — в справочнике",
             "longread_metrics.html#m-pc_tat"),
            ("норматив — метрика «Доля решений в срок (SLA)»",
             "longread_metrics.html#m-pc_sla"),
        ],
        sim=dict(kind="mean", thr=26.0, delta=-2.8, sigma=9.5, E=1.4,
                 good="below", shock=0.14, scale=1, dec=1,
                 unitY="срок принятия решения, часов",
                 sigmaTxt="σ = 9,5 ч (разброс срока одной заявки)",
                 ETxt="E = 1,4 ч", thrTxt="порог 26,0 ч"),
        sliders=dict(
            cap=_sl("Пропускная способность", "заявок в день",
                    "Сколько заявок в день пускаем по новому маршруту.",
                    20, 600, 10, 250),
            lag=_sl("Лаг активации", "дней",
                    "Через сколько дней после подачи заявка проходит автопроверку "
                    "и попадает в эксперимент.", 0, 10, 1, 1),
            hor=_sl("Горизонт наблюдения", "дней",
                    "За сколько дней заявка проходит конвейер целиком — только тогда "
                    "её срок известен.", 1, 30, 1, 7),
        ),
    ),
    dict(
        id="portf",
        tab="Управление портфелем · редкое событие",
        name="Управление портфелем: редкое событие в премиальном сегменте",
        n=_n_share(0.06, 0.02),
        formula="n = Z²·p(1−p) / E² = 1,96² × 0,06 × 0,94 / 0,02²",
        unitN="клиентов",
        note=(
            "Новая сервисная модель в премиальном сегменте портфеля. Событие редкое: "
            "закрытие основного счёта случается у 6 % клиентов сегмента. Вход узкий по "
            "природе кейса — под условие пилота в день подходит несколько клиентов, "
            "это <b>пропускная способность</b>. <b>Лаг активации</b> длинный: клиент "
            "попадает в бакет только после планового контакта с менеджером. "
            "<b>Горизонт наблюдения</b> — полгода: редкое событие иначе просто не "
            "успевает случиться. Порог решения — 6 %, текущий уровень; новая модель "
            "должна опустить его ниже."
        ),
        links=[
            ("определение метрики «Отток» — в справочнике",
             "longread_metrics.html#m-u_churn"),
            ("сопоставимость определений в портфеле — метрика «Словарь определений»",
             "longread_metrics.html#m-dict"),
        ],
        sim=dict(kind="share", thr=0.06, delta=-0.033,
                 sigma=math.sqrt(0.06 * 0.94), E=0.02,
                 good="below", shock=0.002, scale=100, dec=1,
                 unitY="доля клиентов с событием, %",
                 sigmaTxt="σ = √(0,06 × 0,94) ≈ 0,24 (разброс наблюдения «событие / нет»)",
                 ETxt="E = 2 п.п.", thrTxt="порог 6,0 %"),
        sliders=dict(
            cap=_sl("Пропускная способность", "клиентов в день",
                    "Сколько клиентов сегмента в день подходит под условие пилота.",
                    2, 40, 1, 6),
            lag=_sl("Лаг активации", "дней",
                    "Через сколько дней после отбора клиент проходит плановый контакт "
                    "и попадает в бакет.", 0, 90, 5, 45),
            hor=_sl("Горизонт наблюдения", "дней",
                    "Сколько времени по клиенту должно пройти, чтобы редкое событие "
                    "успело случиться.", 60, 365, 5, 180),
        ),
    ),
]

for _c in CASES:
    _c["formula"] = _c["formula"] + " ≈ " + _fi(_c["n"])

TITLE = "Тренажёр: срок эксперимента · Аналитика 360"
CRUMB = "Тренажёр: срок эксперимента"

_BODY_TMPL = """
<header><div class="wrap">
  <div class="eyebrow">Аналитика 360</div>
  <h1>Тренажёр: срок эксперимента</h1>
  <p class="lead">Рассчитанный объём выборки — ещё не срок. Здесь эксперимент
     проживается вживую: участники входят в бакет по мере активации,
     доверительный интервал (в тренажёре он показан как коридор 95 % доверия)
     сужается ровно так, как растёт фактическое число наблюдений, и в какой-то
     день индикатор переключается на зелёный. Три ползунка — пропускная
     способность, лаг активации, горизонт наблюдения — меняют не подписи оси,
     а саму форму воронки и день решения.</p>
  <div class="meta">
    <span class="chip">Кейсы <b>розницы, процесса и портфеля</b></span>
    <span class="chip">Формула объёма <b>n = (Z·σ/E)²</b></span>
    <span class="chip">Расчёт <b>в вашем браузере</b></span>
  </div>
</div></header>

<section><div class="wrap">
<style>
.exp-tabs{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 14px}
.exp-tab{border:1.5px solid var(--acc);background:#fff;color:var(--acc);border-radius:20px;
  padding:7px 14px;cursor:pointer;font:inherit;font-size:14.5px}
.exp-tab.on{background:var(--acc);color:#fff}
.exp-knobs{background:var(--surf);border:1px solid var(--line);border-radius:14px;
  padding:6px 16px 14px;margin:14px 0 6px}
.exp-knob{display:grid;grid-template-columns:230px 1fr 150px;gap:6px 16px;align-items:center;
  padding:12px 0;border-bottom:1px solid var(--line)}
.exp-knob:last-child{border-bottom:0}
.exp-knob .kn{font-weight:700;font-size:15.5px}
.exp-knob .kh{grid-column:1/-1;margin:0;font-size:13.5px;color:var(--ink3);
  padding-top:2px}
.exp-knob input[type=range]{width:100%;accent-color:var(--acc);height:28px}
.exp-knob .val{font-weight:800;font-size:19px;text-align:right;
  font-variant-numeric:tabular-nums;line-height:1.15}
.exp-knob .val small{display:block;font-size:12.5px;font-weight:600;color:var(--ink3)}
.exp-corners{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:12px 0 4px;
  font-size:13.5px;color:var(--ink3)}
.exp-corner{border:1px solid var(--line);background:#fff;color:var(--ink2);border-radius:16px;
  padding:5px 12px;cursor:pointer;font:inherit;font-size:13.5px}
.exp-corner:hover{border-color:var(--acc);color:var(--acc)}
.exp-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0 6px}
.exp-stat{background:var(--surf);border:1px solid var(--line);border-radius:12px;
  padding:12px 14px}
.exp-stat b{display:block;font-size:24px;line-height:1.15;font-variant-numeric:tabular-nums}
.exp-stat span{font-size:13.5px;color:var(--ink3)}
.exp-stat.hot{background:var(--acc-soft);border-color:var(--acc-line)}
.exp-tl{background:var(--surf);border:1px solid var(--line);border-radius:14px;
  padding:16px 14px 8px;margin:14px 0 6px}
.exp-tl svg{width:100%;height:auto;display:block}
.exp-light{display:flex;gap:14px;align-items:center;border:1px solid var(--line);
  border-radius:14px;padding:12px 16px;margin:14px 0 6px;background:var(--surf)}
.exp-light.st-red{background:rgba(196,69,59,.07);border-color:rgba(196,69,59,.3)}
.exp-light.st-yellow{background:rgba(217,164,0,.09);border-color:rgba(217,164,0,.35)}
.exp-light.st-green{background:var(--acc-soft);border-color:var(--acc-line)}
.exp-lamps{display:flex;flex-direction:column;gap:5px;flex:0 0 auto}
.exp-lamp{width:15px;height:15px;border-radius:50%;opacity:.18}
.exp-lamp.r{background:#C4453B}.exp-lamp.y{background:#D9A400}.exp-lamp.g{background:#20BA72}
.exp-lamp.on{opacity:1;box-shadow:0 0 0 3px rgba(46,54,65,.08)}
.exp-light p{margin:0;font-size:15px}
.exp-leg{display:flex;gap:8px 22px;flex-wrap:wrap;margin:10px 2px 0;font-size:13.5px;
  color:var(--ink2)}
.exp-leg span{display:inline-flex;align-items:center;gap:7px}
.exp-leg i{display:inline-block;width:22px;height:0;border-top:3px solid;border-radius:2px}
.exp-leg .band{width:22px;height:12px;border:0;border-radius:3px;
  background:rgba(32,186,114,.22)}
.exp-concl{font-size:15px;color:var(--ink2);margin:8px 2px 0}
.exp-fml{font-size:16px}
@media(max-width:820px){.exp-knob{grid-template-columns:1fr 96px}
  .exp-knob input[type=range]{grid-column:1/-1;order:3}}
@media(max-width:700px){.exp-stats{grid-template-columns:repeat(2,1fr)}}
</style>

<h2>Живая симуляция накопления</h2>
<p>Целевой объём выборки считается до старта — по формуле
<b>n = (Z·σ/E)²</b> из <a href="longread_metrics.html#sample-formula">раздела
«Формула объёма выборки»</a> справочника. Каждая буква видна на графике:
<b>n</b> — сколько наблюдений накоплено (это <b>n(t)</b>: участники, которые уже
активировались и попали в бакет), <b>Z</b> — уровень доверия (Z = 1,96 для
95 %), <b>σ</b> — разброс наблюдений, <b>E</b> — допустимая погрешность, то есть
целевая полуширина коридора. Коридор в каждый день равен <b>x̄ ± Z·σ/√n(t)</b>
и сжимается до ±E ровно тогда, когда n(t) достигает (Z·σ/E)².</p>

<div class="exp-tabs" id="expTabs"></div>
<div class="card acc"><b id="mName"></b><p id="mNote" style="margin:6px 0 0"></p>
  <p id="mLinks" class="sub" style="margin:8px 0 0"></p></div>

<div class="exp-knobs" id="knobs"></div>

<div class="exp-corners">
  <span>Четыре угла из разбора:</span>
  <button type="button" class="exp-corner" data-corner="sn">медленная метрика + узкий вход</button>
  <button type="button" class="exp-corner" data-corner="sw">медленная метрика + широкий вход</button>
  <button type="button" class="exp-corner" data-corner="fn">быстрая метрика + узкий вход</button>
  <button type="button" class="exp-corner" data-corner="fw">быстрая метрика + широкий вход</button>
  <button type="button" class="exp-corner" data-corner="reset">вернуть пресет кейса</button>
</div>

<div class="exp-light" id="light">
  <span class="exp-lamps">
    <span class="exp-lamp r" id="lampR"></span>
    <span class="exp-lamp y" id="lampY"></span>
    <span class="exp-lamp g" id="lampG"></span>
  </span>
  <p id="lightTxt"></p>
</div>

<div class="exp-tl">
  <div id="sim"></div>
  <div class="exp-leg">
    <span><i style="border-color:#159A5C"></i>бегущая оценка метрики x̄ по n(t) наблюдениям</span>
    <span><i class="band"></i>коридор 95 % доверия: x̄ ± Z·σ/√n(t) (Z = 1,96)</span>
    <span><i style="border-color:#C4453B;border-top-style:dashed"></i>порог принятия решения</span>
    <span><b style="color:#159A5C">⇕ E</b> — допустимая погрешность (полуширина коридора), <span id="legE"></span></span>
  </div>
  <p class="exp-concl" id="legS"></p>
</div>

<h4 style="margin-top:20px">Откуда берётся форма воронки: n(t) и две фазы</h4>
<p style="margin:6px 0 0">Ширина коридора — это не рисунок, а
<b>Z·σ/√n(t)</b>. Значит, форму воронки задаёт нижний график: как быстро
участники набираются в бакет. Пропускная способность — наклон этой кривой,
лаг активации — её сдвиг вправо (первые дни бакет пуст), горизонт наблюдения
на набор не влияет вовсе: он двигает только момент, когда метрика проявилась.</p>
<div class="exp-tl"><div id="tl"></div></div>
<p class="exp-concl" id="concl"></p>

<div class="exp-stats">
  <div class="exp-stat"><b id="sN"></b><span id="sNu"></span></div>
  <div class="exp-stat"><b id="sF"></b><span>набор закрыт · коридор сузился до ±E</span></div>
  <div class="exp-stat"><b id="sH"></b><span>горизонт метрики по каждому участнику</span></div>
  <div class="exp-stat hot"><b id="sD"></b><span>решение · зелёный сигнал</span></div>
</div>

<div class="card">
<h4>Расчёт под этим графиком</h4>
<p class="exp-fml" style="margin-bottom:8px"><b id="fml"></b> <span id="fmlU"></span></p>
<p style="margin:0 0 8px" id="fml2" class="sub"></p>
<p style="margin:0" class="sub" id="fml3"></p>
</div>

<div class="card acc">
<h4>Что означают буквы формулы n = (Z·σ/E)²</h4>
<p style="margin:0"><b>n</b> — объём выборки: сколько наблюдений нужно накопить;
<b>n(t)</b> — сколько их уже накоплено к дню t.
<b>Z</b> — множитель уровня доверия: для 95 % доверия Z = 1,96.
<b>σ</b> — разброс отдельных наблюдений: чем разнороднее клиенты, тем шире
коридор при том же n. <b>E</b> — допустимая погрешность: полуширина коридора,
с которой согласны жить при принятии решения. На графике коридор равен
x̄ ± Z·σ/√n(t) и сжимается до ±E ровно в тот момент, когда n(t) достигает
(Z·σ/E)².</p>
</div>

<div class="card acc">
<h4>Что делает каждый ползунок</h4>
<p style="margin:0 0 8px"><b>Пропускная способность</b> — сколько участников
в день вы физически можете провести через эксперимент. Это наклон кривой n(t),
а значит скорость, с которой сужается воронка. Контакт-центр переваривает
15 клиентов в день на новой функции — воронка будет сужаться неделями.</p>
<p style="margin:0 0 8px"><b>Лаг активации</b> — через сколько дней после
попадания в выборку участник совершает действие и фактически попадает в бакет.
Пока лаг не прошёл, бакет пуст: воронка не начинает сужаться вовсе, весь
график просто сдвигается вправо.</p>
<p style="margin:0 0 8px"><b>Горизонт наблюдения</b> — сколько времени должно
пройти по участнику, чтобы метрика проявилась. На ширину коридора он не влияет
никак — он задаёт темп, с которым оценка отходит от порога, то есть день
решения. Именно поэтому при широком входе воронка закрывается за два-три дня,
а решение всё равно ждёт, пока эффект проявится.</p>
<p style="margin:0"><b>Горизонт — не слагаемое срока.</b> Складывать «набор
плюс горизонт» неверно: после закрытия набора коридор равен ровно ±E, и его
граница уходит за порог в тот день, когда накопленный эффект перерос E, — а
это наступает раньше, чем последний участник проживёт все свои дни горизонта.
Горизонт — условие зрелости данных и темп проявления эффекта, а не отрезок
календаря, который надо переждать целиком. Проверить легко: сравните день
решения с суммой «набор закрыт + горизонт» в любом положении ползунков.</p>
</div>

<div class="card">
<h4>Четыре угла разбора — что происходит с формой</h4>
<p style="margin:0 0 8px"><b>Медленная метрика + узкий вход.</b> Долго-долго
набираем участников, воронка сужается медленно, её узкая часть далеко справа —
и только потом эффект добирается до E. Самый дорогой случай. Зато к концу
набора первые участники уже почти дозрели, поэтому вторая фаза короткая.</p>
<p style="margin:0 0 8px"><b>Медленная метрика + широкий вход.</b> Воронка
резко сужается в первые дни и дальше идёт почти плоским коридором шириной ±E.
Объём набран давно, а решения нет: срок целиком определяется тем, как медленно
эффект проявляется у каждого участника.</p>
<p style="margin:0 0 8px"><b>Быстрая метрика + узкий вход.</b> Горизонт короткий,
эффект успевает проявиться прямо по ходу набора, и срок разгоняется именно
набором: день решения почти совпадает с днём, когда воронка сузилась до ±E.</p>
<p style="margin:0"><b>Быстрая метрика + широкий вход.</b> Результат почти
сразу: воронка закрывается в первые часы, горизонт короткий, решение —
на первой неделе.</p>
</div>

<details class="more"><summary>Как устроена симуляция и почему ряд наблюдений не меняется</summary>
<p>Наблюдения случайны, но ряд у каждого кейса зафиксирован: генератор
стартует с одного и того же начального состояния, зависящего от кейса, а
наблюдения раздаются участникам по рангу активации — первый активировавшийся
получает первое наблюдение ряда, второй — второе. Поэтому перемещение ползунков
не меняет удачу: тот же поток наблюдений проживается быстрее или медленнее.
Ряд дополнительно нормирован (среднее 0 и единичный разброс для величин,
равномерная сетка в случайном порядке для долей), поэтому оценка сходится
к истинному значению, а не к случайному смещению. Индивидуальный лаг
активации разбросан вокруг заданного значения (логнормально, медиана равна
положению ползунка): участники активируются не строго в один день. Набор
закрывается, когда активировались n участников. Общий дневной сдвиг
(сезонность операций) задан на календарь и не зависит от положения ползунков.</p>
<p>Как определяется день решения. После закрытия набора коридор перестаёт
сужаться: его полуширина равна ровно E. Значит, граница коридора уходит за
порог ровно в тот день, когда накопленный по всей выборке эффект перерастает
E. Пока участники дозревают, эффект виден лишь частично: у участника он
проявляется за горизонт H, поэтому эффект растёт постепенно и достигает
полной величины только после того, как последний участник проживёт свои H
дней. Если эффект на полном горизонте больше E, порог перейдён раньше — днём
решения управляет соотношение «эффект против E», а не календарная сумма
«набор + горизонт». Если же эффект меньше E, решения не будет вовсе, сколько
ни ждать: тогда нужна меньшая погрешность E, то есть больший объём выборки.</p>
</details>

<p style="margin-top:16px">Точный расчёт размера групп под минимальный
детектируемый эффект — в <a href="trainer_sample.html">тренажёре «Расчёт
выборки»</a>; из его результата и берётся целевой объём n. Все параметры
пресетов учебные.</p>
</div></section>

<section><div class="wrap">
<h2>Источник</h2>
<div class="card">
<h4>Netflix Technology Blog</h4>
<p>Практика, из которой выросла механика тренажёра: каждая функция сервиса
запускается как эксперимент, а срок теста определяется числом участников
и горизонтом метрики, а не желаемой датой отчёта.</p>
<p style="margin:0">
<a href="https://netflixtechblog.com/interpreting-a-b-test-results-false-negatives-and-power-6943995cf3a8"
   target="_blank" rel="noopener">Interpreting A/B test results: false negatives and power</a>
— почему малому эффекту нужно больше участников и почему тест не завершают
раньше запланированного объёма.<br>
<a href="https://netflixtechblog.com/its-all-a-bout-testing-the-netflix-experimentation-platform-4e1ca458c15"
   target="_blank" rel="noopener">It’s All A/Bout Testing: The Netflix Experimentation Platform</a>
— как устроена платформа экспериментов Netflix.</p>
</div>
</div></section>

<footer><div class="wrap">
  Аналитика 360 · материалы практической части.<br>
  Параметры кейсов учебные; расчёт выполняется в вашем браузере, наружу ничего
  не отправляется.
</div></footer>

<script>
var CS=__CASES__;
var Zc=1.96;
var cur=CS[0];
var pos={};                        // положение ползунков запоминается на кейс
var $=function(id){return document.getElementById(id)};
var NB="\\u202F";
function fi(x){return String(Math.round(x)).replace(/\\B(?=(\\d{3})+(?!\\d))/g,NB)}
function fv(v,c){return (v*c.sim.scale).toFixed(c.sim.dec).replace('.',',')}
function fd(x){return (Math.round(x*10)/10).toString().replace('.',',')}
// сроки: до 20 дней — с десятыми, дальше целые дни (планируют всё равно в днях)
function fday(x){return x<20?fd(x):fi(x)}

function tx(x,y,t,fs,w,f,a,o){
  return '<text x="'+x+'" y="'+y+'" font-size="'+fs+'"'+(w?' font-weight="'+w+'"':'')
    +' fill="'+f+'"'+(a?' text-anchor="'+a+'"':'')+(o?' fill-opacity="'+o+'"':'')+'>'+t+'</text>';
}
// подпись на белой подложке: не сливается с коридором и зонами светофора
function plate(x,y,t,fs,w,col,a,X0,X1){
  var wd=t.length*fs*0.6+14,x0;
  if(a==='end')x0=x-wd+7;else if(a==='middle')x0=x-wd/2;else x0=x-7;
  if(X0!=null){if(x0<X0+2)x0=X0+2;if(x0+wd>X1-2)x0=X1-2-wd;}
  var xt=(a==='end')?x0+wd-7:(a==='middle')?x0+wd/2:x0+7;
  return '<rect x="'+x0.toFixed(1)+'" y="'+(y-fs-2).toFixed(1)+'" width="'+wd.toFixed(1)
    +'" height="'+(fs+8).toFixed(1)+'" rx="6" fill="#ffffff" fill-opacity="0.9"/>'
    +tx(xt.toFixed(1),y,t,fs,w,col,a);
}
function tickStep(total){
  var c=[0.5,1,2,5,7,10,14,20,30,60,90,120,180,360];
  for(var i=0;i<c.length;i++){if(total/c[i]<=12)return c[i]}
  return 720;
}
var LADDER=[3,5,7,10,14,20,30,45,60,90,120,150,200,250,300,400,500,650,800,1000,1300,1600,2000,2600];
function niceCeil(v){for(var i=0;i<LADDER.length;i++){if(LADDER[i]>=v)return LADDER[i]}return v}

// ── Детерминированный ряд наблюдений: фиксирован на кейс ────────────────────
function seedOf(s){var h=5381;s=s+'a360';for(var i=0;i<s.length;i++)h=((h<<5)+h+s.charCodeAt(i))>>>0;return h}
function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;
  var t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;
  return ((t^t>>>14)>>>0)/4294967296}}
function gauss(rnd){var u=0,v=0;while(u===0)u=rnd();while(v===0)v=rnd();
  return Math.sqrt(-2*Math.log(u))*Math.cos(2*Math.PI*v)}

var drawCache={};
function draws(c){
  if(drawCache[c.id])return drawCache[c.id];
  var rnd=mulberry32(seedOf(c.id)),N=c.n,M=N+Math.ceil(0.6*N)+40,i;
  // склонности участников раздаются по РАНГУ активации — ряд наблюдений один
  var u=new Float64Array(N),z=new Float64Array(N),uu=new Float64Array(N);
  for(i=0;i<N;i++)u[i]=rnd();
  var ord=[];for(i=0;i<N;i++)ord.push(i);
  ord.sort(function(a,b){return u[a]-u[b]});
  for(i=0;i<N;i++)uu[ord[i]]=(i+0.5)/N;          // равномерная сетка в случайном порядке
  var s1=0,s2=0;
  for(i=0;i<N;i++){z[i]=gauss(rnd);s1+=z[i]}
  s1/=N;for(i=0;i<N;i++){z[i]-=s1;s2+=z[i]*z[i]}
  s2=Math.sqrt(s2/N)||1;for(i=0;i<N;i++)z[i]/=s2; // среднее 0, s.d. 1
  var lg=new Float64Array(M);                     // множитель лага, медиана 1
  for(i=0;i<M;i++)lg[i]=Math.exp(0.45*gauss(rnd)-0.101);
  var sh=new Float64Array(3000);                  // общий дневной сдвиг
  for(i=0;i<3000;i++)sh[i]=gauss(rnd);
  var o={u:uu,z:z,lg:lg,sh:sh,M:M};drawCache[c.id]=o;return o;
}
function upperBound(A,t,len){var lo=0,hi=len;while(lo<hi){var m=(lo+hi)>>1;
  if(A[m]<=t)lo=m+1;else hi=m}return lo}
// вертикальный размах поля: чтобы «горло» воронки входило в кадр, а полоса ±E
// оставалась хорошо различимой
function spanOf(s){return Math.max(6.4*s.E,Math.abs(s.delta)+4.2*s.E)}
// с какого n коридор целиком входит в кадр — с него и начинаем рисовать воронку
function nMinOf(s){return Math.max(8,Math.ceil(Math.pow(Zc*s.sigma/(0.55*spanOf(s)),2)))}

// ── Симуляция: n(t) из пропускной способности и лага, коридор Z·σ/√n(t) ─────
var simCache={};
function simulate(c,cap,lag,H){
  var key=c.id+'|'+cap+'|'+lag+'|'+H;
  if(simCache[key])return simCache[key];
  var D=draws(c),N=c.n,s=c.sim,i;
  var a=new Float64Array(D.M);
  for(i=0;i<D.M;i++)a[i]=(i+1)/cap+lag*D.lg[i];
  a.sort();                                   // первые N активаций = набранная выборка
  var tFill=a[N-1],tStart=a[0];
  var tEnd=tFill+H*1.15+Math.max(3,0.06*(tFill+H));
  var G=400,MINN=nMinOf(s);
  var t=new Float64Array(G+1),est=new Float64Array(G+1),half=new Float64Array(G+1),
      nn=new Int32Array(G+1),ok=new Uint8Array(G+1),vis=new Uint8Array(G+1);
  for(var j=0;j<=G;j++){
    var ti=tEnd*j/G,n=upperBound(a,ti,N);
    t[j]=ti;nn[j]=n;
    if(n<MINN)continue;
    // общий дневной сдвиг: задан на календарь, между днями сглажен
    var d0=Math.floor(ti)%3000,fr=ti-Math.floor(ti);
    var ct=s.shock*(D.sh[d0]*(1-fr)+D.sh[(d0+1)%3000]*fr),e,m;
    if(s.kind==='share'){
      var cnt=0;
      for(i=0;i<n;i++){m=(ti-a[i])/H;if(m>1)m=1;else if(m<0)m=0;
        if(D.u[i]<s.thr+s.delta*m+ct)cnt++}
      e=cnt/n;
    }else{
      var sm=0,sz=0;
      for(i=0;i<n;i++){m=(ti-a[i])/H;if(m>1)m=1;else if(m<0)m=0;sm+=m;sz+=D.z[i]}
      e=s.thr+s.delta*(sm/n)+s.sigma*(sz/n)+ct;
    }
    var h=Zc*s.sigma/Math.sqrt(n);
    est[j]=e;half[j]=h;vis[j]=1;
    ok[j]=(h<=s.E*1.000001&&(s.good==='above'?(e-h>s.thr):(e+h<s.thr)))?1:0;
  }
  var stop=-1;
  for(j=G;j>=0;j--){if(ok[j])stop=j;else break}
  var o={t:t,est:est,half:half,n:nn,vis:vis,G:G,tFill:tFill,tStart:tStart,tEnd:tEnd,
         tDec:stop>=0?t[stop]:null,iDec:stop,reached:stop>=0};
  o.tAxis=Math.min(tEnd,niceCeil((o.reached?o.tDec:tFill)*1.22));
  simCache[key]=o;return o;
}

// ── Главный график: коридор из n(t), порог, светофорные зоны ────────────────
function chart(c,r){
  var s=c.sim,X0=64,X1=884,Y0=34,Y1=298,HT=372,TA=r.tAxis;
  var span=spanOf(s);
  var mid=s.thr+s.delta/2,yLo=mid-span/2;
  if(s.kind==='share'&&yLo<0)yLo=0;
  var yHi=yLo+span;
  var xx=function(t){return X0+(t/TA)*(X1-X0)};
  var yy=function(v){return Y1-(v-yLo)/(yHi-yLo)*(Y1-Y0)};
  var o='<svg viewBox="0 0 920 '+HT+'" xmlns="http://www.w3.org/2000/svg" role="img" '
    +'aria-label="Накопление достоверности: бегущая оценка метрики, коридор 95 % доверия '
    +'шириной Z·σ/√n(t), порог решения и зоны индикатора решения" style="font-family:var(--font)">';
  o+='<clipPath id="simClip"><rect x="'+X0+'" y="'+Y0+'" width="'+(X1-X0)+'" height="'+(Y1-Y0)+'"/></clipPath>';
  var xF=Math.min(xx(r.tFill),X1),xD=r.reached?Math.min(xx(r.tDec),X1):X1;
  var caps='';
  var zone=function(xa,xb,fill,lab,col){
    if(xb-xa<0.6)return '';
    if(xb-xa>=lab.length*7.2+18)
      caps+=plate(((xa+xb)/2).toFixed(1),Y0+16,lab,12,'700',col,'middle',X0,X1);
    return '<rect x="'+xa.toFixed(1)+'" y="'+Y0+'" width="'+(xb-xa).toFixed(1)+'" height="'
      +(Y1-Y0)+'" fill="'+fill+'"/>';
  };
  o+=zone(X0,xF,'rgba(196,69,59,0.06)','красный · коридор шире E','#C4453B');
  o+=zone(xF,xD,'rgba(217,164,0,0.11)','жёлтый · объём набран, порог внутри','#8a6d00');
  o+=zone(xD,X1,'rgba(32,186,114,0.09)','зелёный · решение принято','#159A5C');
  // коридор и бегущая оценка
  var up=[],lo=[],ce=[];
  for(var i=0;i<=r.G;i++){
    if(r.t[i]>TA)break;
    if(!r.vis[i])continue;
    var x=xx(r.t[i]).toFixed(1);
    up.push(x+','+yy(r.est[i]+r.half[i]).toFixed(1));
    lo.push(x+','+yy(r.est[i]-r.half[i]).toFixed(1));
    ce.push(x+','+yy(r.est[i]).toFixed(1));
  }
  o+='<g clip-path="url(#simClip)">';
  if(up.length>1){
    o+='<polygon points="'+up.join(' ')+' '+lo.slice().reverse().join(' ')+'" fill="#20BA72" fill-opacity="0.15"/>';
    o+='<polyline points="'+up.join(' ')+'" fill="none" stroke="#20BA72" stroke-width="1.7"/>';
    o+='<polyline points="'+lo.join(' ')+'" fill="none" stroke="#20BA72" stroke-width="1.7"/>';
    o+='<polyline points="'+ce.join(' ')+'" fill="none" stroke="#159A5C" stroke-width="2.6"/>';
  }
  o+='</g>'+caps;
  // порог решения
  var yT=yy(s.thr);
  o+='<line x1="'+X0+'" y1="'+yT.toFixed(1)+'" x2="'+X1+'" y2="'+yT.toFixed(1)
    +'" stroke="#C4453B" stroke-width="2" stroke-dasharray="7 5"/>';
  o+=plate(X1-4,yT+(s.good==='above'?17:-7),'порог решения — '+fv(s.thr,c),12.5,'800','#C4453B','end',X0,X1);
  // вертикали: набор закрыт и день решения
  o+='<line x1="'+xF.toFixed(1)+'" y1="'+Y0+'" x2="'+xF.toFixed(1)+'" y2="'+Y1
    +'" stroke="#2E3641" stroke-opacity="0.5" stroke-width="1.6" stroke-dasharray="5 4"/>';
  if(r.reached&&xD<X1-1)
    o+='<line x1="'+xD.toFixed(1)+'" y1="'+Y0+'" x2="'+xD.toFixed(1)+'" y2="'+Y1
      +'" stroke="#159A5C" stroke-width="2" stroke-dasharray="3 4"/>';
  // подписи вертикалей — в свободной половине поля (там, где нет кривой)
  var yA=(s.good==='above')?Y1-38:Y0+40,yB=(s.good==='above')?Y1-14:Y0+62;
  o+=plate(xF+7,yA,'набор закрыт: n = (Z·σ/E)² = '+fi(c.n)+' · день '+fday(r.tFill),12,'700','#2E3641',null,X0,X1);
  if(r.reached)
    o+=plate(xD+7,yB,'решение: '+fday(r.tDec)+'-й день',12.5,'800','#159A5C',null,X0,X1);
  // скобка E в момент, когда коридор сузился до допустимой погрешности
  var iF=0;while(iF<r.G&&(r.t[iF]<r.tFill||!r.vis[iF]))iF++;
  if(r.vis[iF]){
    var ya=yy(r.est[iF]),yb=yy(r.est[iF]+r.half[iF]),xb=Math.min(xF+11,X1-30);
    o+='<line x1="'+xb.toFixed(1)+'" y1="'+ya.toFixed(1)+'" x2="'+xb.toFixed(1)+'" y2="'+yb.toFixed(1)+'" stroke="#159A5C" stroke-width="2"/>';
    o+='<line x1="'+(xb-4).toFixed(1)+'" y1="'+ya.toFixed(1)+'" x2="'+(xb+4).toFixed(1)+'" y2="'+ya.toFixed(1)+'" stroke="#159A5C" stroke-width="2"/>';
    o+='<line x1="'+(xb-4).toFixed(1)+'" y1="'+yb.toFixed(1)+'" x2="'+(xb+4).toFixed(1)+'" y2="'+yb.toFixed(1)+'" stroke="#159A5C" stroke-width="2"/>';
    o+=tx((xb+7).toFixed(1),((ya+yb)/2+4).toFixed(1),'E',13,'800','#159A5C');
  }
  // оси
  o+='<line x1="'+X0+'" y1="'+Y0+'" x2="'+X0+'" y2="'+Y1+'" stroke="#2E3641" stroke-opacity="0.3" stroke-width="1.2"/>';
  o+='<line x1="'+X0+'" y1="'+Y1+'" x2="'+X1+'" y2="'+Y1+'" stroke="#2E3641" stroke-opacity="0.3" stroke-width="1.2"/>';
  for(var k=0;k<=4;k++){
    var v=yLo+(yHi-yLo)*k/4,y=yy(v);
    o+='<line x1="'+(X0-5)+'" y1="'+y.toFixed(1)+'" x2="'+X0+'" y2="'+y.toFixed(1)+'" stroke="#2E3641" stroke-opacity="0.3" stroke-width="1.2"/>';
    o+=tx(X0-9,y+4,fv(v,c),11.5,null,'#2E3641','end',0.65);
  }
  o+=tx(X0-8,Y0-13,s.unitY+' — бегущая оценка x̄',12,null,'#2E3641',null,0.65);
  var st=tickStep(TA);
  for(var d=0;d<=TA+1e-9;d+=st){
    var xd=xx(d);
    o+='<line x1="'+xd.toFixed(1)+'" y1="'+Y1+'" x2="'+xd.toFixed(1)+'" y2="'+(Y1+6)+'" stroke="#2E3641" stroke-opacity="0.3" stroke-width="1.2"/>';
    o+=tx(xd.toFixed(1),Y1+21,fd(d),12,null,'#2E3641','middle',0.6);
  }
  o+=tx(X0,Y1+44,'коридор: x̄ ± Z·σ/√n(t) · Z = 1,96 (доверие 95'+NB+'%) · '+s.ETxt,12.5,null,'#2E3641',null,0.65);
  o+=tx(X1,Y1+44,'дни с начала эксперимента →',12.5,null,'#2E3641','end',0.65);
  return o+'</svg>';
}

// ── Нижний график: n(t) и две фазы на той же оси дней ──────────────────────
function accum(c,r,cap,lag,H){
  var X0=64,X1=884,Y0=24,Y1=112,BY=128,BH=26,AX=166,HT=214,TA=r.tAxis,N=c.n;
  var xx=function(t){return X0+(t/TA)*(X1-X0)};
  var yy=function(v){return Y1-(v/N)*(Y1-Y0)};
  var o='<svg viewBox="0 0 920 '+HT+'" xmlns="http://www.w3.org/2000/svg" role="img" '
    +'aria-label="Кривая набора n(t): участники, попавшие в бакет, и две фазы эксперимента" '
    +'style="font-family:var(--font)">';
  // кривая набора
  var pts=[X0.toFixed(1)+','+Y1.toFixed(1)];
  for(var i=0;i<=r.G;i++){
    if(r.t[i]>TA)break;
    pts.push(xx(r.t[i]).toFixed(1)+','+yy(r.n[i]).toFixed(1));
  }
  if(r.tFill<=TA)pts.push(X1.toFixed(1)+','+yy(N).toFixed(1));
  var last=pts[pts.length-1].split(',');
  o+='<polygon points="'+pts.join(' ')+' '+last[0]+','+Y1.toFixed(1)+'" fill="#20BA72" fill-opacity="0.18"/>';
  o+='<polyline points="'+pts.join(' ')+'" fill="none" stroke="#159A5C" stroke-width="2.4"/>';
  // целевой объём
  o+='<line x1="'+X0+'" y1="'+yy(N).toFixed(1)+'" x2="'+X1+'" y2="'+yy(N).toFixed(1)
    +'" stroke="#2E3641" stroke-opacity="0.4" stroke-width="1.4" stroke-dasharray="5 5"/>';
  o+=plate(X1-4,yy(N)-7,'n = '+fi(N)+' — целевой объём',12,'700','#2E3641','end',X0,X1);
  // лаг активации: бакет пуст
  var xS=Math.min(xx(r.tStart),X1);
  if(xS-X0>4){
    o+='<rect x="'+X0+'" y="'+Y0+'" width="'+(xS-X0).toFixed(1)+'" height="'+(Y1-Y0)
      +'" fill="#2E3641" fill-opacity="0.05"/>';
    if(xS-X0>=118)o+=tx(((X0+xS)/2).toFixed(1),Y1-8,'лаг: бакет пуст',11.5,'700','#2E3641','middle',0.6);
  }
  o+=tx(X0-8,Y0-9,'n(t) — участников уже в бакете',12,null,'#2E3641',null,0.65);
  o+='<line x1="'+X0+'" y1="'+Y0+'" x2="'+X0+'" y2="'+Y1+'" stroke="#2E3641" stroke-opacity="0.3" stroke-width="1.2"/>';
  o+='<line x1="'+X0+'" y1="'+Y1+'" x2="'+X1+'" y2="'+Y1+'" stroke="#2E3641" stroke-opacity="0.3" stroke-width="1.2"/>';
  // полоса фаз
  var xF=Math.min(xx(r.tFill),X1),xD=r.reached?Math.min(xx(r.tDec),X1):X1;
  o+='<rect x="'+X0+'" y="'+BY+'" width="'+(X1-X0)+'" height="'+BH+'" rx="8" fill="#159A5C" fill-opacity="0.1"/>';
  o+='<rect x="'+X0+'" y="'+BY+'" width="'+Math.max(3,xF-X0).toFixed(1)+'" height="'+BH+'" rx="8" fill="#20BA72"/>';
  if(xD-xF>3)o+='<rect x="'+xF.toFixed(1)+'" y="'+BY+'" width="'+(xD-xF).toFixed(1)+'" height="'+BH+'" fill="#D9A400" fill-opacity="0.5"/>';
  var yL=BY+BH/2+5;
  var l1='фаза 1 · набор и активация — '+fday(r.tFill)+' дн';
  var l2='фаза 2 · эффект перерастает E (горизонт '+fi(H)+' дн) — '+(r.reached?fday(r.tDec-r.tFill):'—')+' дн';
  var w1=l1.length*7.2+14,w2=l2.length*7.2+14;
  var in1=(xF-X0>=w1),in2=(xD-xF>=w2);
  if(in1)o+=tx(((X0+xF)/2).toFixed(1),yL,l1,12,'700','#ffffff','middle');
  else o+=plate(X0+4,yL,l1,12,'700','#159A5C',null,X0,X1);
  // подпись фазы 2 не должна наехать на выносную подпись фазы 1
  if(in2&&(in1||(xF+xD)/2-w2/2>X0+8+w1))o+=tx(((xF+xD)/2).toFixed(1),yL,l2,12,'700','#6b5400','middle');
  else o+=plate(X1-4,yL,l2,12,'700','#6b5400','end',X0,X1);
  // ось дней
  o+='<line x1="'+X0+'" y1="'+AX+'" x2="'+X1+'" y2="'+AX+'" stroke="#2E3641" stroke-opacity="0.3" stroke-width="1.2"/>';
  var st=tickStep(TA);
  for(var d=0;d<=TA+1e-9;d+=st){
    var x=xx(d);
    o+='<line x1="'+x.toFixed(1)+'" y1="'+AX+'" x2="'+x.toFixed(1)+'" y2="'+(AX+6)+'" stroke="#2E3641" stroke-opacity="0.3" stroke-width="1.2"/>';
    o+=tx(x.toFixed(1),AX+21,fd(d),12,null,'#2E3641','middle',0.6);
  }
  o+=tx(X0,AX+42,'наклон = '+fi(cap)+NB+'/'+NB+'день · сдвиг вправо = лаг '+fi(lag)+' дн',
    12.5,null,'#2E3641',null,0.65);
  o+=tx(X1,AX+42,'дни с начала эксперимента →',12.5,null,'#2E3641','end',0.65);
  return o+'</svg>';
}

function renderTabs(){
  $('expTabs').innerHTML=CS.map(function(c){
    return '<button type="button" class="exp-tab'+(c.id===cur.id?' on':'')
      +'" data-c="'+c.id+'">'+c.tab+'</button>';
  }).join('');
}
var KEYS=['cap','lag','hor'];
function renderKnobs(){
  $('knobs').innerHTML=KEYS.map(function(k){
    var s=cur.sliders[k],v=pos[cur.id][k];
    return '<div class="exp-knob"><span class="kn">'+s.label+'</span>'
      +'<input type="range" id="k_'+k+'" min="'+s.min+'" max="'+s.max+'" step="'+s.step+'" value="'+v+'">'
      +'<span class="val" id="v_'+k+'">'+fi(v)+'<small>'+s.unit+'</small></span>'
      +'<p class="kh">'+s.hint+'</p></div>';
  }).join('');
  KEYS.forEach(function(k){$('k_'+k).addEventListener('input',function(){
    pos[cur.id][k]=+this.value;update()})});
}
function preset(c){return {cap:c.sliders.cap.val,lag:c.sliders.lag.val,hor:c.sliders.hor.val}}

function select(id){
  cur=CS.filter(function(c){return c.id===id})[0]||CS[0];
  if(!pos[cur.id])pos[cur.id]=preset(cur);
  renderTabs();renderKnobs();update();
}
function corner(kind){
  var s=cur.sliders,p=pos[cur.id];
  if(kind==='reset'){pos[cur.id]=preset(cur)}
  else{
    p.cap=(kind==='sn'||kind==='fn')?s.cap.min:s.cap.max;
    p.hor=(kind==='sn'||kind==='sw')?s.hor.max:s.hor.min;
    p.lag=s.lag.val;
  }
  renderKnobs();update();
}

function setLight(state,txt){
  var box=$('light');
  box.className='exp-light st-'+state;
  ['R','Y','G'].forEach(function(ch){
    var on=(state==='red'&&ch==='R')||(state==='yellow'&&ch==='Y')||(state==='green'&&ch==='G');
    $('lamp'+ch).className='exp-lamp '+ch.toLowerCase()+(on?' on':'');
  });
  $('lightTxt').innerHTML=txt;
}

function update(){
  var p=pos[cur.id],c=cur,s=c.sim;
  var r=simulate(c,p.cap,p.lag,p.hor);
  KEYS.forEach(function(k){
    var el=$('v_'+k);if(el)el.innerHTML=fi(p[k])+'<small>'+c.sliders[k].unit+'</small>';
  });
  $('mName').textContent=c.name;
  $('mNote').innerHTML=c.note;
  $('mLinks').innerHTML='Подробнее: '+c.links.map(function(l){
    return '<a href="'+l[1]+'">'+l[0]+'</a>'}).join(' · ')+'.';
  $('sim').innerHTML=chart(c,r);
  $('tl').innerHTML=accum(c,r,p.cap,p.lag,p.hor);
  $('sN').textContent=fi(c.n);
  $('sNu').textContent='целевой объём n, '+c.unitN;
  $('sF').textContent=fday(r.tFill)+' дн';
  $('sH').textContent=fi(p.hor)+' дн';
  $('sD').textContent=r.reached?('≈ '+fday(r.tDec)+'-й день'):'не достигнут';
  var verdict=(s.good==='above')===(s.delta>0)?'гипотеза подтверждена':'гипотеза опровергнута';
  if(r.reached){
    setLight('green','<b>Зелёный с ≈ '+fday(r.tDec)+'-го дня: '+verdict+'</b> — коридор устойчиво '
      +(s.delta>0?'выше':'ниже')+' порога ('+s.thrTxt+'). До этого: красный до '+fday(r.tFill)
      +'-го дня, пока коридор шире E; затем жёлтый '+fday(r.tDec-r.tFill)
      +' дн — объём n набран, коридор сузился до ±'+s.ETxt.replace('E = ','')
      +', но порог оставался внутри него.');
  }else{
    setLight('yellow','<b>Жёлтый:</b> объём n набран на '+fday(r.tFill)+'-й день, коридор сузился '
      +'до ±E, но в окне наблюдения порог остаётся внутри коридора — решение не принято.');
  }
  $('legE').textContent=s.ETxt+' · '+s.sigmaTxt;
  $('legS').textContent='Светофор: красный — коридор шире E, данных мало; жёлтый — объём n '
    +'набран, коридор сузился до ±E, но порог внутри; зелёный — коридор устойчиво по одну '
    +'сторону порога, гипотеза подтверждена или опровергнута.';
  $('fml').textContent=c.formula;
  $('fmlU').textContent=c.unitN+' (Z = 1,96 — доверие 95\\u202F%)';
  $('fml2').textContent='Набор: n(t) = сколько участников уже активировалось. При '
    +fi(p.cap)+' '+c.sliders.cap.unit+' и лаге '+fi(p.lag)+' дн объём n = '+fi(c.n)
    +' набран на '+fday(r.tFill)+'-й день — тогда полуширина коридора Z·σ/√n(t) равна ровно E.';
  $('fml3').textContent=r.reached
    ? ('Решение: ' +fday(r.tDec)+'-й день. Из них '+fday(r.tFill)+' дн — набор и активация, '
       +fday(r.tDec-r.tFill)+' дн — пока накопленный эффект не перерос погрешность E. Горизонт ('
       +fi(p.hor)+' дн по каждому участнику) в срок не складывается: у последнего вошедшего он '
       +'заканчивается только на '+fday(r.tFill+p.hor)+'-й день.')
    : 'В окне наблюдения решение не принято: эффект меньше допустимой погрешности E.';
  var wait=r.reached?(r.tDec-r.tFill):0,tot=r.reached?r.tDec:r.tFill;
  var share=tot>0?Math.round(100*wait/tot):0;
  $('concl').textContent=!r.reached
    ? 'Решение в окне не принято — измените ползунками горизонт наблюдения и пропускную способность.'
    : (share>=60
      ? 'Набор уже не узкое место: '+share+'\\u202F% срока — ожидание, пока эффект перерастёт '
        +'погрешность E ('+fday(wait)+' дн из '+fday(tot)+'). Дальше расширять вход бесполезно: '
        +'темп второй фазы задаёт сама метрика — как быстро эффект проявляется у участника.'
      : (share<=15
        ? 'Срок держит набор: '+fday(r.tFill)+' дн из '+fday(tot)+' уходит на то, чтобы участники '
          +'просто попали в бакет. Здесь помогает пропускная способность и сокращение лага активации.'
        : 'Срок делится примерно поровну: '+fday(r.tFill)+' дн — набор и активация, '+fday(wait)
          +' дн — пока эффект перерастает погрешность E. Ползунок пропускной способности сжимает '
          +'только первую часть.'));
}

document.addEventListener('click',function(e){
  var b=e.target.closest('.exp-tab');
  if(b){select(b.getAttribute('data-c'));return}
  var k=e.target.closest('.exp-corner');
  if(k)corner(k.getAttribute('data-corner'));
});
select(cur.id);
</script>
"""


def body():
    return _BODY_TMPL.replace("__CASES__", json.dumps(CASES, ensure_ascii=False))


BODY = body()
