# -*- coding: utf-8 -*-
"""Сборка страницы «Тренажёр: дерево метрик» (a360/trainer_tree.html).

Исходник конструктора — build/src/metric_tree_trainer.html (копия учебного
конструктора из материалов курса, зафиксирована в репозитории, чтобы сборка
не зависела от внешних каталогов). Скрипт подменяет в нём кейсы, палитру,
тему и достраивает разбор конфигурации.

Что добавляет сборка к исходному конструктору:

  * кейсы двух уровней по трём темам — «соберите дерево» и «конфигурация
    данных» — плюс подключение юрлиц и свободный конструктор;
  * экономика конфигурации источников: TTE по критическому пути построенного дерева
    (расчётные уровни наследуют максимум входов, накопительные сверки в
    сочленениях добавляют время), TCO за горизонт пилота и интегральная
    оценка качества данных конфигурации;
  * разбор неидеальной конфигурации: в чём ограничение именно выбранных
    источников и что заменить, чтобы стало лучше, — с дельтой в днях,
    рублях и пунктах интегральной оценки. Разбор считается из данных
    кейса и справочника метрик, а не пишется текстом под каждый случай.

Метрики берутся из единого справочника build/metrics_data.py — того же,
из которого собирается лонгрид-справочник; кнопки «?» и ссылки в разборе
ведут на якоря #m-<id> этого справочника.

Каждая подмена в исходнике идёт под assert: изменится исходник — сборка
упадёт, а не соберёт страницу без сообщения об ошибке.

Запуск:  python3 build/trainer_tree.py
"""
import itertools
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scorm_engagement
import theme
from metrics_data import M, metric


def theme_font(name):
    """Шрифтовой стек курса из build/theme.py (--font или --mono)."""
    m = re.search(rf"--{name}:\s*([^;]+);", theme.CSS)
    assert m, f"в theme.py не найден шрифтовой стек --{name}"
    return m.group(1).strip()

BUILD = pathlib.Path(__file__).resolve().parent
ROOT = BUILD.parent
SRC = BUILD / "src" / "metric_tree_trainer.html"
# Открытая версия страницы кладётся только в scorm/content: в корень репозитория
# её переносит build_pages.py, зашифровав парольным гейтом (STATIC_PAGES).
# Открытая страница в корне ломает самопроверку гейта — писать туда нельзя.
DST = ROOT / "scorm" / "content" / "trainer_tree.html"


def ms(*ids):
    return [metric(i) for i in ids]


# ═══════════════════════════════════════════════════════════════════════════
# Кейсы
# ═══════════════════════════════════════════════════════════════════════════
# Поля кейса:
#   ideal    — состав лучшей конфигурации (по нему считается эталон);
#   idealEco — контрольные значения TTE и TCO эталона: страница считает их
#              заново из справочника, а эти числа держат расчёт под проверкой;
#   rules    — какие метрики рассчитываются из каких (req — обязательные
#              входы, opt — предсказывающие);
#   quality  — развилки источников: какие варианты закрывают один и тот же
#              вход и какой из них лучший;
#   lags     — накопительные сверки на сочленениях: сколько дней добавляет
#              расчёт метрики target, если её вход взят из источника source.
CASES = [
{
  "id": "retail", "title": "Розница: кредитная карта — соберите дерево",
  "grp": "Розница · кредитная карта", "opt": "Соберите дерево",
  "desc": ("Дерево метрик розничного продукта: от заявок и доставки — к P&L продукта. "
           "Соберите его целиком и соедините все размещённые метрики: изолированная карточка — "
           "несобранные данные. Замер внизу считает срок до решения по критическому пути дерева."),
  "horizon": 3, "decision": "alive",
  "ideal": ["app", "appr", "tat", "err", "iss", "act", "alive", "churn", "rev", "pnl"],
  "idealEco": {"tte": 49, "tco": 986},
  "metrics": ms("app", "appr", "tat", "err", "iss", "act", "alive", "churn", "rev", "pnl"),
  "rules": {
    "iss": {"req": ["app", "appr"], "opt": []},
    "act": {"req": ["tat"], "opt": ["err"]},
    "alive": {"req": ["iss", "act"], "opt": []},
    "churn": {"req": [], "opt": ["err"]},
    "rev": {"req": ["alive", "churn"], "opt": []},
    "pnl": {"req": ["rev"], "opt": []},
  },
  "calc": {
    "iss": {"lbl": "Заявки + Одобрение → Выдачи", "formula": "Выдачи = Заявки × Одобрение",
            "example": "1 000 шт./нед. × 82 % = 820 выдач"},
    "act": {"lbl": "Срок доставки → Активация", "formula": "каждые +2 дня доставки ≈ −4 п.п. активации",
            "example": "TAT 4 дн → активация ≈ 58 %"},
    "alive": {"lbl": "Выдачи + Активация → Активные", "formula": "Активные += Выдачи × Активация",
              "example": "820 × 58 % ≈ +476 активных в неделю"},
    "rev": {"lbl": "Активные − Отток → Доход", "formula": "Доход = Активные × ARPU − потери оттока",
            "example": "476 × 1 200 ₽ ≈ +571 тыс. ₽/мес."},
    "pnl": {"lbl": "Доход → NPV", "formula": "NPV из финансовой модели продукта",
            "example": "порог банка: NPV > 0 к 36-му месяцу"},
  },
},
{
  # Уровень 2 розницы: то же дерево, но активация — развилка источников
  # (витрина DWH против флага CRM). Метрики actA/actB уже в справочнике.
  "id": "retail_data", "title": "Розница: источник активации — выберите источники данных",
  "grp": "Розница · кредитная карта", "opt": "Выберите источники данных",
  "desc": ("Та же розничная воронка, но активацию можно взять из двух источников: "
           "витрина DWH считает первую операцию за 30 дней, флаг CRM отмечает выпуск карты и "
           "доступен в реальном времени. Дерево верно при обоих вариантах, а экономика "
           "конфигураций разная: быстрый флаг требует накопительной сверки на стыке с "
           "расчётом активных клиентов. Соберите дерево — тренажёр сравнит вашу конфигурацию "
           "с лучшей и покажет, что заменить."),
  "horizon": 3, "decision": "alive",
  "ideal": ["app", "appr", "err", "actA", "iss", "alive", "churn", "rev", "pnl"],
  # путь app/appr(7)→iss(7)=14; actA 14 → alive 14+max(14,14)=28;
  # TCO = (20+20+80+60+10+40+40+20+150) + 3×(5+5+20+15+2+10+10+5+30) = 440+306 = 746.
  "idealEco": {"tte": 28, "tco": 746},
  # Подвох сочленения: флаг CRM меряет выпуск, а не операцию — расчёт «Активных»
  # на нём требует накопительной сверки с витриной: +30 дн на ребре actB→alive.
  # Ловушка: alive = 14+max(iss 14, actB 7)+30 = 58 дн; TCO 390+3×107 = 711.
  "lags": [
    {"target": "alive", "source": "actB", "extra": 30},
  ],
  "metrics": ms("app", "appr", "err", "actA", "actB", "iss", "alive", "churn", "rev", "pnl"),
  "rules": {
    "iss": {"req": ["app", "appr"], "opt": []},
    "alive": {"req": ["iss"], "opt": ["actA", "actB"]},
    "churn": {"req": [], "opt": ["err"]},
    "rev": {"req": ["alive", "churn"], "opt": []},
    "pnl": {"req": ["rev"], "opt": []},
  },
  "quality": [
    {"target": "alive", "slot": "Источник активации", "options": ["actA", "actB"], "best": "actA",
     "okNote": ("Активация взята из витрины DWH: считается первая операция за 30 дней, "
                "расчёт прослеживается до транзакций, и витрина закреплена регламентом "
                "как официальный источник.")},
  ],
  "calc": {
    "iss": {"lbl": "Заявки + Одобрение → Выдачи", "formula": "Выдачи = Заявки × Одобрение",
            "example": "1 000 шт./нед. × 82 % = 820 выдач"},
    "alive": {"lbl": "Выдачи + Активация → Активные", "formula": "Активные += Выдачи × Активация",
              "example": "820 × 58 % ≈ +476 активных в неделю"},
    "rev": {"lbl": "Активные − Отток → Доход", "formula": "Доход = Активные × ARPU − потери оттока",
            "example": "476 × 1 200 ₽ ≈ +571 тыс. ₽/мес."},
    "pnl": {"lbl": "Доход → NPV", "formula": "NPV из финансовой модели продукта",
            "example": "порог банка: NPV > 0 к 36-му месяцу"},
  },
},
{
  # Уровень 1 процессной темы: кредитный конвейер, просто собрать дерево.
  "id": "process_basic", "title": "Кредитный конвейер — соберите дерево",
  "grp": "Процесс · кредитный конвейер", "opt": "Соберите дерево",
  "desc": ("Кредитный конвейер глазами руководителя процесса: доля решений без участия "
           "сотрудника и дозапросы документов определяют срок принятия решения по заявке, "
           "а срок — долю решений, уложившихся в норматив; скорость решения задаёт, сколько одобренных клиентов "
           "доходит до выдачи и во сколько обходится обработка заявки. Соберите дерево целиком "
           "и соедините все размещённые метрики."),
  "horizon": 3, "decision": "pc_sla",
  "ideal": ["pc_apps", "pc_stp", "pc_docret", "pc_load", "pc_tat", "pc_sla", "pc_out", "pc_cost"],
  # путь: pc_stp/pc_docret/pc_load(14) → pc_tat 14+14=28 → pc_sla 7+28=35;
  # TCO = (20+30+30+30+60+30+40+60) + 3×(5+8+8+8+15+8+10+15) = 300+231 = 531.
  "idealEco": {"tte": 35, "tco": 531},
  "metrics": ms("pc_apps", "pc_stp", "pc_docret", "pc_load", "pc_tat", "pc_sla", "pc_out", "pc_cost"),
  "rules": {
    "pc_tat": {"req": ["pc_stp", "pc_docret"], "opt": ["pc_load"]},
    "pc_sla": {"req": ["pc_tat"], "opt": []},
    "pc_out": {"req": ["pc_apps", "pc_sla"], "opt": []},
    "pc_cost": {"req": ["pc_out"], "opt": []},
  },
  "calc": {
    "pc_tat": {"lbl": "Автоматизация + Дозапросы → Срок решения (TAT)",
               "formula": "автоматическое решение — минуты; каждый дозапрос ≈ +1,5 дня к сроку",
               "example": "STP 55 % · дозапросы 18 % → медиана TAT ≈ 26 ч"},
    "pc_sla": {"lbl": "Срок решения → Доля решений в срок (SLA)",
               "formula": "SLA = доля заявок с решением в норматив (24 ч)",
               "example": "медиана 26 ч → в норматив укладывается 61 % решений"},
    "pc_out": {"lbl": "Заявки + SLA → Доведённые до выдачи",
               "formula": "дольше решение — больше отвалов: ≈ −7 п.п. доведённых на каждые +24 ч",
               "example": "9 200 заявок/мес × 34 % ≈ 3 130 выдач"},
    "pc_cost": {"lbl": "Доведённые до выдачи → Стоимость обработки",
                "formula": "Стоимость = расходы конвейера / обработанные заявки",
                "example": "18,6 млн ₽ / 3 130 выдач ≈ 5 900 ₽ на выдачу"},
  },
},
{
  # Уровень 2 процессной темы: срок решения существует только при собранном
  # следе процесса — развилка «журнал этапов BPM против ручной выборки досье».
  "id": "process_data", "title": "Кредитный конвейер: след процесса — выберите источники данных",
  "grp": "Процесс · кредитный конвейер", "opt": "Выберите источники данных",
  "desc": ("То же дерево конвейера, но срок принятия решения считается только по "
           "собранному следу процесса — а след можно взять из журнала этапов BPM со сквозным "
           "ключом или ручной выборкой досье. Дерево верно при обоих вариантах; сравните "
           "экономику конфигураций — тренажёр посчитает срок до решения, TCO и интегральную "
           "оценку качества данных и покажет, что заменить."),
  "horizon": 3, "decision": "pc_sla",
  "ideal": ["pc_log", "pc_stp", "pc_docret", "pc_tat", "pc_sla", "pc_out", "pc_cost"],
  # путь: pc_log 21 → pc_tat 14+21=35 → pc_sla 7+35=42;
  # TCO = (150+30+30+60+30+40+60) + 3×(30+8+8+15+8+10+15) = 400+282 = 682.
  # Ловушка (pc_smp 45 дн): pc_tat 59 → pc_sla 66; TCO 265+3×104 = 577.
  "idealEco": {"tte": 42, "tco": 682},
  "metrics": ms("pc_log", "pc_smp", "pc_stp", "pc_docret", "pc_tat", "pc_sla", "pc_out", "pc_cost"),
  "rules": {
    "pc_tat": {"req": [], "opt": ["pc_log", "pc_smp", "pc_stp", "pc_docret"]},
    "pc_sla": {"req": ["pc_tat"], "opt": []},
    "pc_out": {"req": ["pc_sla"], "opt": []},
    "pc_cost": {"req": ["pc_out"], "opt": []},
  },
  "quality": [
    {"target": "pc_tat", "slot": "След процесса", "options": ["pc_log", "pc_smp"], "best": "pc_log",
     "okNote": ("След процесса взят из журнала этапов BPM со сквозным ключом заявки: "
                "разрывы между системами закрыты, время видно по каждому этапу.")},
  ],
  "calc": {
    "pc_tat": {"lbl": "След процесса → Срок решения (TAT)",
               "formula": "TAT = t(решение) − t(подача), по этапам конвейера",
               "example": "медиана 26 ч, 90-й перцентиль 74 ч"},
    "pc_sla": {"lbl": "Срок решения → Доля решений в срок (SLA)",
               "formula": "SLA = доля заявок с решением в норматив (24 ч)",
               "example": "медиана 26 ч → в норматив укладывается 61 % решений"},
    "pc_out": {"lbl": "SLA → Доведённые до выдачи",
               "formula": "дольше решение — больше отвалов: ≈ −7 п.п. доведённых на каждые +24 ч",
               "example": "9 200 заявок/мес × 34 % ≈ 3 130 выдач"},
    "pc_cost": {"lbl": "Доведённые до выдачи → Стоимость обработки",
                "formula": "Стоимость = расходы конвейера / обработанные заявки",
                "example": "18,6 млн ₽ / 3 130 выдач ≈ 5 900 ₽ на выдачу"},
  },
},
{
  "id": "corporate", "title": "Подключение юрлиц — выберите источники данных",
  "grp": "Корпоративный блок · подключение юрлиц", "opt": "Выберите источники данных",
  "desc": ("Дерево проще, но появляется выбор источника: след процесса можно взять "
           "из журнала workflow или собрать ручной выборкой кейсов. Дерево верно при обоих "
           "вариантах, а экономика конфигураций разная: сравните расходы на подключение и "
           "поддержание, время до решения и качество данных — тренажёр покажет, что заменить."),
  "horizon": 3, "decision": "t2a",
  "ideal": ["ts", "rw", "t2a", "actv", "fee"],
  # путь: ts 21 → t2a 21+21=42; TCO = (180+30+60+40+20) + 3×(45+8+15+10+5) = 330+249 = 579.
  # Ловушка (mn 50 дн): t2a 71; TCO 165+3×83 = 414.
  "idealEco": {"tte": 42, "tco": 579},
  "metrics": ms("ts", "mn", "rw", "t2a", "actv", "fee"),
  "rules": {
    "t2a": {"req": [], "opt": ["ts", "mn", "rw"]},
    "actv": {"req": ["t2a"], "opt": []},
    "fee": {"req": ["actv"], "opt": []},
  },
  "quality": [
    {"target": "t2a", "slot": "След процесса", "options": ["ts", "mn"], "best": "ts",
     "okNote": ("След процесса взят из журнала этапов workflow: узкие места видны по этапам, "
                "а не восстанавливаются по памяти сотрудников.")},
  ],
  "calc": {
    "t2a": {"lbl": "След процесса → Время подключения", "formula": "T = t(активация) − t(подача), по этапам",
            "example": "медиана 9 дн, 90-й перцентиль 23 дн"},
    "actv": {"lbl": "Время подключения → Активные", "formula": "короче подключение → меньше отвалов до старта",
             "example": "−5 дн подключения ≈ +6 % дошедших до активации"},
    "fee": {"lbl": "Активные → Комиссионный доход", "formula": "Доход = Активные × средний чек РКО",
            "example": "+120 юрлиц × 4 500 ₽ ≈ +540 тыс. ₽/мес."},
  },
},
{
  # Уровень 1 портфельной темы: та же модель, но без развилок источников —
  # просто собрать цепочку портфельного уровня.
  "id": "portfolio_basic", "title": "Портфель инициатив — соберите дерево",
  "grp": "Портфель инициатив", "opt": "Соберите дерево",
  "desc": ("У каждой инициативы портфеля есть паспорт инициативы — карточка из "
           "четырёх параметров: месяц старта, расходы к старту, месяц выхода на прибыльность "
           "и месяц окупаемости. Витрина финансовых моделей хранит паспорта по единой методике; из "
           "паспорта считается NPV-кривая инициативы, кривые складываются в NPV портфеля, по "
           "сумме выбирается порядок стартов, а план-факт из учёта сверяет модель с фактом. "
           "Соберите цепочку портфельного уровня."),
  "horizon": 3, "decision": "prio",
  "ideal": ["fmv", "npvi", "npvsum", "factp", "prio"],
  # тот же идеал, что у portfolio2: путь fmv→npvi→npvsum→prio = 72 дн, TCO 554 т₽.
  "idealEco": {"tte": 72, "tco": 554},
  "metrics": ms("fmv", "factp", "npvi", "npvsum", "prio"),
  "rules": {
    "npvi": {"req": ["fmv"], "opt": []},
    "npvsum": {"req": ["npvi"], "opt": []},
    "prio": {"req": ["npvsum"], "opt": ["factp"]},
  },
  "calc": {
    "npvi": {"lbl": "Паспорт инициативы → NPV-кривая",
             "formula": ("кривая через три точки: старт (−расходы к старту), "
                         "минимум в месяц прибыльности, пересечение нуля в месяц окупаемости"),
             "example": "старт мес 3 · расходы 1,1 млн ₽ · прибыльность +6 мес · окупаемость +22 мес"},
    "npvsum": {"lbl": "Кривые инициатив → NPV портфеля",
               "formula": "помесячная сумма потоков всех инициатив, дисконт 0,83 %/мес",
               "example": "14 инициатив: минимум −32 млн ₽ (мес 14), ноль — мес 25, NPV(36) ≈ +89 млн ₽"},
    "prio": {"lbl": "NPV портфеля → порядок стартов",
             "formula": "сдвиг месяцев старта → пересчёт дна, окупаемости и доходности портфеля",
             "example": "перестановка двух инициатив меняет все показатели портфеля"},
  },
},
{
  # Паспорт инициативы (месяц старта, расходы к старту, месяцы до прибыльности
  # и окупаемости) → NPV-кривая → сумма потоков → приоритизация запусков.
  "id": "portfolio2", "title": "Портфель: источники паспортов — выберите источники данных",
  "grp": "Портфель инициатив", "opt": "Выберите источники данных",
  "desc": ("Паспорт инициативы (месяц старта, расходы к старту, месяц выхода на "
           "прибыльность и месяц окупаемости) можно взять из витрины финансовых моделей или из заявок "
           "менеджеров, а ход портфеля контролировать план-фактом из учёта или статус-отчётами. "
           "Из паспортов считаются NPV-кривые, кривые складываются в кривую портфеля. Быстрый "
           "источник на первом уровне может стоить недель на стыке с расчётом — соберите "
           "конфигурацию, и тренажёр разберёт, в чём ограничение именно вашего выбора."),
  "horizon": 3, "decision": "prio",
  "ideal": ["fmv", "npvi", "npvsum", "factp", "prio"],
  # путь fmv→npvi→npvsum→prio: 21+14+7+30 = 72 дн (factp→prio: 60 — не критич.);
  # TCO = (150+40+30+90+40) + 3×(25+10+8+15+10) = 350 + 204 = 554 т₽.
  "idealEco": {"tte": 72, "tco": 554},
  # Подвох сочленения: паспорта из заявок менеджеров быстры сами по себе
  # (TTE 10 дн), но посчитаны по разным методикам — перед сложением кривых
  # нужна ручная нормализация: +45 дн на сочленении mreq → NPV-кривая.
  # Анти-конфигурация: 10+45+14+7+30 = 106 дн, TCO 479 т₽.
  # Вторая развилка учит другому: статус-отчёты не стоят на критическом пути
  # (вклад в срок — 3 дн при витрине и ноль при заявках менеджеров), зато вход
  # за 5 т₽ тянет за собой ручное содержание 45 т₽/мес — уже на 3-м месяце,
  # то есть внутри горизонта пилота, «дешёвый» контроль перестаёт быть дешевле
  # план-факта. До правки содержание статус-отчётов стоило 25 т₽/мес, и в паре
  # с заявками менеджеров эталонный источник проигрывал по критерию 13,932
  # против 13,960: подсказка не предлагала правильную замену, а разбор при этом
  # называл статус-отчёты подвохом.
  "lags": [
    {"target": "npvi", "source": "mreq", "extra": 45},
  ],
  "metrics": ms("fmv", "mreq", "factp", "statr", "npvi", "npvsum", "prio"),
  "rules": {
    "npvi": {"req": [], "opt": ["fmv", "mreq"]},
    "npvsum": {"req": ["npvi"], "opt": []},
    "prio": {"req": ["npvsum"], "opt": ["factp", "statr"]},
  },
  "quality": [
    {"target": "npvi", "slot": "Источник паспортов инициатив",
     "options": ["fmv", "mreq"], "best": "fmv",
     "okNote": ("Паспорта инициатив взяты из витрины финансовых моделей: все четыре параметра "
                "посчитаны по одной методике, поэтому кривые складываются без нормализации.")},
    {"target": "prio", "slot": "Контроль хода портфеля",
     "options": ["factp", "statr"], "best": "factp",
     "okNote": ("Ход портфеля контролируется план-фактом из учёта: отклонение кривой от "
                "модели видно в месяц закрытия, а не при пересмотре бюджета.")},
  ],
  "calc": {
    "npvi": {"lbl": "Паспорт инициативы → NPV-кривая",
             "formula": ("кривая через три точки: старт (−расходы к старту), "
                         "минимум в месяц прибыльности, пересечение нуля в месяц окупаемости"),
             "example": "старт мес 3 · расходы 1,1 млн ₽ · прибыльность +6 мес · окупаемость +22 мес"},
    "npvsum": {"lbl": "Кривые инициатив → NPV портфеля",
               "formula": "помесячная сумма потоков всех инициатив, дисконт 0,83 %/мес",
               "example": "14 инициатив: минимум −32 млн ₽ (мес 14), ноль — мес 25, NPV(36) ≈ +89 млн ₽"},
    "prio": {"lbl": "NPV портфеля → порядок стартов",
             "formula": "сдвиг месяцев старта → пересчёт дна, окупаемости и доходности портфеля",
             "example": "перестановка двух инициатив меняет все показатели портфеля"},
  },
},
{
  "id": "universal", "title": "Универсальный конструктор · все метрики",
  "grp": "Свободный режим", "opt": "Все метрики · соберите своё дерево",
  "desc": ("Свободный режим: метрики трёх категорий — инвестиционные, управленческие и качества "
           "опыта. Соберите дерево своего продукта, процесса или портфеля. Единственно верного "
           "ответа нет; живой замер срока до решения и TCO поможет держать конфигурацию реалистичной."),
  "horizon": 3,
  "metrics": ms("u_traffic", "u_conv", "u_tat", "u_err", "u_ops", "u_nps", "u_csat", "u_cac",
                "u_price", "u_iss", "u_mau", "u_churn", "u_aov", "u_ltv", "u_rev", "u_mrr",
                "u_roi", "u_npv"),
},
]


# ═══════════════════════════════════════════════════════════════════════════
# Самопроверка кейсов: эталон и анти-конфигурация считаются здесь ровно так же,
# как их считает страница, и сверяются с числами, записанными в кейсе.
# ═══════════════════════════════════════════════════════════════════════════
def _case(cid):
    return next(c for c in CASES if c["id"] == cid)


def _eval(case, ids, edges=None):
    """TTE до решения, TCO за горизонт и интегральная оценка качества данных
    для конфигурации из метрик ids. Граф строится по правилам кейса — так же,
    как эталонный граф строит страница."""
    mm = {i: metric(i) for i in ids}
    lags = case.get("lags", [])
    if edges is None:
        edges = []
        for tgt, rl in case.get("rules", {}).items():
            if tgt not in ids:
                continue
            for src in list(rl.get("req", [])) + list(rl.get("opt", [])):
                if src in ids:
                    edges.append((src, tgt))
    memo = {}

    def T(mid):
        if mid in memo:
            return memo[mid]
        memo[mid] = 0
        ins = [s for s, t in edges if t == mid]
        mx = max([T(s) for s in ins], default=0)
        extra = sum(L["extra"] for L in lags
                    if L["target"] == mid and L["source"] in ins)
        memo[mid] = mm[mid]["tte"] + mx + extra
        return memo[mid]

    for i in ids:
        T(i)
    dec = case.get("decision")
    tte = memo[dec] if dec in memo else max(memo.values())
    h = case.get("horizon", 3)
    tco = sum(m["capex"] for m in mm.values()) + h * sum(m["opex"] for m in mm.values())
    q = min(m["dqi"] for m in mm.values())
    return tte, tco, q


def _eff(case, ids):
    """Тот же критерий сравнения конфигураций, что считает страница:
    интегральная оценка качества данных, отнесённая к TTE и TCO (CD3)."""
    _t, _co, _q = _eval(case, ids)
    return _q / 100.0 * 1e6 / (_t * _co)


# Запас эталона над ближайшей конфигурацией. Порог не косметический: разбор на
# странице показывает экономический шаг только при выигрыше больше 0,1 %
# (sim.e > cur.e*1.001), а участнику урок должен быть виден числами, а не
# четвёртым знаком. Конфигурация, выигрывающая на доли процента, — не урок,
# а совпадение округлений: такие кейсы сборка не пропускает.
_EFF_MARGIN = 1.05

for _c in CASES:
    if not _c.get("rules"):
        continue
    _tte, _tco, _q = _eval(_c, _c["ideal"])
    assert (_tte, _tco) == (_c["idealEco"]["tte"], _c["idealEco"]["tco"]), (
        f'кейс {_c["id"]}: расчёт эталона {(_tte, _tco)} разошёлся с idealEco {_c["idealEco"]}')
    _c["idealEco"]["q"] = _q
    # Эталон обязан быть лучшим не «при прочих эталонных», а при любых прочих:
    # перебираем все сочетания развилок кейса. Прежняя проверка сравнивала
    # варианты развилки только при эталонных остальных и пропускала случай,
    # когда лучший источник проигрывает в паре с неверным выбором на соседней
    # развилке: участник, выбравший правильный источник, не получал ни
    # подтверждения, ни подсказки — замена отсекалась порогом в разборе.
    _forks = _c.get("quality", [])
    if not _forks:
        continue
    _opts = [o for _g in _forks for o in _g["options"]]
    for _g in _forks:
        assert _g["best"] in _c["ideal"], (
            f'кейс {_c["id"]}, развилка {_g["slot"]}: лучший вариант {_g["best"]} '
            f'не входит в эталон кейса')
    _base = [m for m in _c["ideal"] if m not in _opts]
    _ideal_combo = tuple(_g["best"] for _g in _forks)
    for _combo in itertools.product(*[_g["options"] for _g in _forks]):
        _e = _eff(_c, _base + list(_combo))
        # 1) шаг к эталонному источнику по каждой развилке обязан улучшать
        #    критерий — при любом выборе на соседних развилках;
        for _i, _g in enumerate(_forks):
            if _combo[_i] == _g["best"]:
                continue
            _fix = list(_combo)
            _fix[_i] = _g["best"]
            _ef = _eff(_c, _base + _fix)
            _t, _co, _qq = _eval(_c, _base + list(_combo))
            _tf, _cof, _qf = _eval(_c, _base + _fix)
            assert _e * _EFF_MARGIN < _ef, (
                f'кейс {_c["id"]}, развилка {_g["slot"]}: при выборе '
                f'{_combo} замена {_combo[_i]} на эталонный {_g["best"]} даёт '
                f'{_ef:.4f} (TTE {_tf} дн, TCO {_cof} т₽, качество {_qf}) против '
                f'{_e:.4f} (TTE {_t} дн, TCO {_co} т₽, качество {_qq}) — '
                f'эталонный источник не выигрывает с запасом {_EFF_MARGIN:.2f}, '
                f'и разбор не предложит эту замену')
        # 2) и сам эталон обязан быть максимумом критерия по всем сочетаниям.
        if _combo != _ideal_combo:
            _t, _co, _qq = _eval(_c, _base + list(_combo))
            assert _e * _EFF_MARGIN < _eff(_c, _base + list(_ideal_combo)), (
                f'кейс {_c["id"]}: конфигурация {_combo} даёт {_e:.4f} '
                f'(TTE {_t} дн, TCO {_co} т₽, качество {_qq}) против '
                f'{_eff(_c, _base + list(_ideal_combo)):.4f} у объявленного эталона '
                f'{_ideal_combo} — эталон не выигрывает с запасом {_EFF_MARGIN:.2f}')

# анти-конфигурации, зафиксированные в дизайне кейсов
assert _eval(_case("retail_data"),
             ["app", "appr", "err", "actB", "iss", "alive", "churn", "rev", "pnl"])[:2] == (58, 711)
assert _eval(_case("process_data"),
             ["pc_smp", "pc_stp", "pc_docret", "pc_tat", "pc_sla", "pc_out", "pc_cost"])[:2] == (66, 577)
assert _eval(_case("corporate"), ["mn", "rw", "t2a", "actv", "fee"])[:2] == (71, 414)
assert _eval(_case("portfolio2"),
             ["mreq", "npvi", "npvsum", "statr", "prio"])[:2] == (106, 479)

# Ни одной осиротевшей метрики в справочнике. Метрика, выпавшая из всех кейсов,
# продолжает жить в справочнике отдельной группой и учить участника тому, чего
# в тренажёре нет, — ровно так уцелел кейс «Портфель: сопоставимые продукты»
# после замены на «Портфель инициатив» (метрики dict, adhoc, npvp, cmp, alloc
# удалены 13.08.2026). Проверка ловит следующий такой случай на сборке.
_USED = {m["id"] for _c in CASES for m in _c["metrics"]}
_ORPHAN = sorted(set(M) - _USED)
assert not _ORPHAN, (
    "метрики есть в metrics_data, но не входят ни в один кейс тренажёра: "
    + ", ".join(_ORPHAN) + ". Либо поставьте их в кейс, либо удалите из "
    "справочника — иначе участник получит группу метрик, которой нет в дереве")

# гомогенность терминов: внутренний жаргон в кейсы не просачивается
_all_texts = json.dumps(CASES, ensure_ascii=False)
for _bad in ("паспорта параметров", "паспорт параметров"):
    assert _bad not in _all_texts, f"остался внутренний термин «{_bad}»"


# ═══════════════════════════════════════════════════════════════════════════
# Подмены в исходнике
# ═══════════════════════════════════════════════════════════════════════════
t = SRC.read_text(encoding="utf-8")


def swap(old, new, what):
    global t
    assert old in t, "якорь не найден: " + what
    t = t.replace(old, new, 1)


# ── 0. Шрифты: только системные, без обращений в сеть ──
# Исходник тянул Inter из Google Fonts. В закрытом контуре банка этот запрос
# не проходит: в консоли ошибка, шрифт всё равно откатывается на системный.
# Вдобавок страница была набрана Inter, а остальные страницы курса — семейством
# из build/theme.py, и в одном пакете оказывались две типографики. Стеки берём
# оттуда же: в общей оболочке они системные по тому же соображению.
swap('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
     '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
     '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700'
     '&display=swap" rel="stylesheet">\n', "", "google fonts links")
swap(".calc-example{font-size:12px;color:var(--info);margin-top:6px;padding:6px 10px;"
     "background:rgba(59,130,246,.08);border-radius:6px;"
     "font-family:'SF Mono','Fira Code',monospace;line-height:1.5}",
     ".calc-example{font-size:12px;color:var(--info);margin-top:6px;padding:6px 10px;"
     "background:rgba(59,130,246,.08);border-radius:6px;"
     f"font-family:{theme_font('mono')};line-height:1.5}}",
     "calc-example mono font")

# ── 1. Заголовки ──
swap("<title>Тренажёр: Дерево метрик", "<title>Тренажёр: Дерево метрик · Аналитика 360", "title")
swap('<span class="header-tag">тренажёр</span>',
     '<span class="header-tag">Аналитика 360</span>', "header tag")

# ── 2. Светлая тема в палитре деки ──
i0 = t.find(":root {")
i1 = t.find("}", i0) + 1
assert 0 < i0 < i1, ":root не найден"
t = t[:i0] + """:root {
  --bg:             #f2f7f4;
  --bg-surface:     #ffffff;
  --bg-elevated:    #eef5f1;
  --bg-hover:       #e3efe8;
  --text:           #10281c;
  --text-sec:       rgba(16,40,28,.64);
  --text-muted:     rgba(16,40,28,.38);
  --accent:         #20BA72;
  --accent-hover:   #17a563;
  --color-leading:  #20BA72;
  --color-calc:     #2E6BB8;
  --color-lagging:  #D9822B;
  --bg-leading:     rgba(32,186,114,.10);
  --bg-calc:        rgba(46,107,184,.10);
  --bg-lagging:     rgba(217,130,43,.12);
  --ok:             #0f7a46;
  --warn:           #b07708;
  --err:            #C4453B;
  --info:           #2E6BB8;
  --edge-color:     #5c7268;
  --node-w:         194px;
  --port-r:         7px;
  --radius:         12px;
  --radius-sm:      8px;
  --font:           'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
}""" + t[i1:]

# Семейство курса вместо Inter (см. раздел 0 выше): подмена идёт после
# переписывания :root, поэтому правится уже вставленная строка.
swap("  --font:           'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;",
     f"  --font:           {theme_font('font')};", "font stack")

style_end = t.find("</style>")
head_css = t[:style_end].replace("rgba(255,255,255", "rgba(16,40,28")
t = head_css + t[style_end:]
swap('fill="rgba(255,255,255,.3)"', 'fill="rgba(16,40,28,.3)"', "temp marker")
swap("tmp.setAttribute('stroke','rgba(255,255,255,.3)')",
     "tmp.setAttribute('stroke','rgba(16,40,28,.55)')",
     "temp edge line: белая линия невидима на светлой теме")

# ── 2b. Навигация «← Материалы» ──
swap(".header-brand{display:flex;align-items:baseline;gap:8px}",
     ".header-brand{display:flex;align-items:baseline;gap:8px}\n"
     ".back-link{font-size:12px;font-weight:600;color:var(--accent);text-decoration:none;\n"
     "  white-space:nowrap;border:1px solid rgba(32,186,114,.32);border-radius:8px;padding:3px 9px}\n"
     ".back-link:hover{background:rgba(32,186,114,.10);color:var(--accent-hover)}",
     "back-link css")
swap('<div class="header-brand">',
     '<a class="back-link" href="index.html">&larr; Материалы</a>\n'
     '    <div class="header-brand">', "back-link anchor")

# ── 3. Счётчик связей ──
# Исходный счётчик считал только верные связи и сравнивал их с суммой всех
# правил кейса, включая оба варианта выбора источника. Получалось «7 из 9»
# рядом с вердиктом «есть замечания»: число противоречило вердикту и молчало
# о неверно проведённых связях. Шапку разбора вместе со счётчиком собирает
# заново раздел 8 — за образец берётся число связей правильного дерева кейса,
# а неверно проведённые связи называются отдельным предложением.

# ── 3b. Гомогенные термины в сообщениях: полные названия метрик, а не подписи-единицы ──
swap("msg:`${met(fn.metricId)?.abbr} не влияет на ${met(tn.metricId)?.abbr}`",
     "msg:`«${met(fn.metricId)?.name}» не влияет на «${met(tn.metricId)?.name}»`",
     "invalid edge msg: name вместо abbr")
swap("const mNames=(ri.miss||[]).map(m=>met(m)?.abbr||m).join(', ');",
     "const mNames=(ri.miss||[]).map(m=>met(m)?.name||m).join(', ');",
     "calc miss: name вместо abbr")
swap("'Несвязанные метрики: '+orph.map(n=>met(n.metricId)?.abbr).join(', ')",
     "'Метрики без единой связи: '+orph.map(n=>met(n.metricId)?.name).join(', ')+"
     "'. Соедините их с деревом или уберите с холста.'",
     "orphan list: полное название метрики и фраза вместо перечня сокращений")
swap("m:`${m.abbr} — опережающая, обычно не имеет входящих связей`",
     "m:`«${m.name}» — опережающая, обычно не имеет входящих связей`",
     "sandbox leading-in: name")
swap("m:`${m.abbr} — запаздывающая, обычно не имеет исходящих связей`",
     "m:`«${m.name}» — запаздывающая, обычно не имеет исходящих связей`",
     "sandbox lagging-out: name")
swap("m:`${m.abbr} — ${m.type==='lagging'?'итоговая':'расчётная'} метрика без входящих связей: её не из чего рассчитать`",
     "m:`«${m.name}» — ${m.type==='lagging'?'итоговая':'расчётная'} метрика без входящих связей: её не из чего рассчитать`",
     "sandbox calc-no-in: name")
swap("m:`${m.abbr} — опережающая метрика ни на что не влияет (нет исходящих связей)`",
     "m:`«${m.name}» — опережающая метрика ни на что не влияет (нет исходящих связей)`",
     "sandbox leading-no-out: name")

# ── 3b-2. Обратная связь без языка теории графов и без школьной похвалы ──
# «Цикл», «ациклический граф», «DAG» ничего не говорят руководителю: из
# сообщения не следует, что делать. Заголовок разбора свободного режима и
# заголовок успеха переписаны по той же причине — они не называли ни что
# проверено, ни что дальше.
swap("msgs.push({t:'err',m:'Обнаружен цикл. Дерево метрик должно быть ациклическим графом (DAG)'})",
     "msgs.push({t:'err',m:'Связи замкнулись в круг: метрика в итоге считается сама из себя. "
     "Уберите одну связь в этом круге.'})",
     "сообщение о цикле без DAG")
swap("msgs.push({t:'ok',m:'Граф является корректным DAG (нет циклов)'})",
     "msgs.push({t:'ok',m:'Замкнутых кругов в дереве нет: каждая метрика считается из других'})",
     "сообщение об отсутствии циклов без DAG")
swap('<div class="res-sub">Свободный конструктор — структурная проверка</div>',
     '<div class="res-sub">Что проверено в вашем дереве: замкнутые круги, направление '
     'связей, метрики без связей</div>',
     "подзаголовок разбора свободного режима")
swap('<span class="res-icon pop">&#9989;</span><div><div class="res-title">'
     'Дерево построено правильно!</div>',
     '<span class="res-icon">&#10003;</span><div><div class="res-title">'
     'Дерево собрано верно</div>',
     "заголовок успеха: без восклицательного знака, эмодзи и всплывающей анимации")
swap('<span class="res-icon">&#9888;&#65039;</span><div><div class="res-title">Есть замечания</div>',
     '<span class="res-icon">&#9888;</span><div><div class="res-title">Есть замечания</div>',
     "значок замечаний: текстовый знак вместо эмодзи")

# ── 3c. Селектор кейсов: группировка по темам (optgroup) с пометкой уровня ──
swap("""  CASES.forEach(c=>{
    const o=document.createElement('option');o.value=c.id;o.textContent=c.title;
    cSel.appendChild(o);
  });""",
     """  const ogs={};
  CASES.forEach(c=>{
    let g=ogs[c.grp||''];
    if(!g){
      if(c.grp){g=document.createElement('optgroup');g.label=c.grp;cSel.appendChild(g)}
      else g=cSel;
      ogs[c.grp||'']=g;
    }
    const o=document.createElement('option');o.value=c.id;o.textContent=c.opt||c.title;
    g.appendChild(o);
  });""",
     "optgroup селектора кейсов")

# ── 4. Кейсы ──
i0 = t.find("CASES=[")
assert i0 > 0, "CASES не найден"
i1 = t.find("];", i0)
assert i1 > i0, "конец CASES не найден"
t = t[:i0] + "CASES=" + json.dumps(CASES, ensure_ascii=False) + ";" + t[i1 + 2:]

# ── 5. Карточка палитры: паспорт сбора + интегральная оценка + help ──
swap('d.innerHTML=`<span class="pal-card-dot" style="background:${tColor(m.type)}"></span>'
     '<div><div class="pal-card-name">${m.name}</div><div class="pal-card-abbr">${m.abbr}</div></div>`;',
     'd.innerHTML=`<span class="pal-card-dot" style="background:${tColor(m.type)}"></span>'
     '<div><div class="pal-card-name">${m.name}</div><div class="pal-card-abbr">${m.abbr}</div>'
     '${m.capex!=null?`<div class="q-badge" title="CAPEX + OPEX/мес (тыс. ₽) · время до проверенного сигнала · интегральная оценка качества данных">'
     '${m.capex}+${m.opex}/мес т₽ · ${m.tte} дн · качество ${m.dqi}</div>`:``}</div>'
     '${m.def?`<button class="help-btn" data-mid="${m.id}" type="button" title="Что это за метрика">?</button>`:``}`;',
     "pal card html")

# ── 6. Карточка узла: то же на холсте ──
swap('<div class="node-body"><div class="node-name">${m.name}</div><div class="node-abbr">${m.abbr}</div></div>',
     '<div class="node-body"><div class="node-name">${m.name}</div><div class="node-abbr">${m.abbr}</div>'
     '${m.capex!=null?`<div class="q-badge" title="CAPEX + OPEX/мес (тыс. ₽) · время до проверенного сигнала · интегральная оценка качества данных">'
     '${m.capex}+${m.opex}/мес т₽ · ${m.tte} дн · качество ${m.dqi}</div>`:``}'
     '${m.def?`<button class="help-btn help-btn-node" data-mid="${m.id}" type="button" title="Что это за метрика">?</button>`:``}</div>',
     "node card html")

# ── 7. CSS ──
EXTRA_CSS = """
/* A360: экономика данных, интегральная оценка качества, разбор конфигурации */
.q-badge{font-size:9.5px;color:#7a5c10;background:#fdf3d7;border:1px solid #e3cc8a;
  border-radius:6px;padding:0 5px;margin-top:3px;display:inline-block;line-height:15px}
.help-btn{border:1px solid rgba(16,40,28,.35);background:#fff;color:#33463c;
  opacity:.8;border-radius:50%;width:17px;height:17px;line-height:14px;font-size:10.5px;
  cursor:pointer;flex:none;padding:0;margin-left:auto}
.help-btn:hover{opacity:1;border-color:var(--accent)}
.pal-card{position:relative}
.pal-card .help-btn{position:absolute;top:6px;right:6px}
.help-btn-node{position:absolute;top:4px;right:4px}
/* z-index выше оверлея результатов: «как это считается» открывается прямо из разбора */
.q-modal-back{position:fixed;inset:0;background:rgba(10,30,20,.45);display:none;
  align-items:center;justify-content:center;z-index:120}
.q-modal-back.open{display:flex}
.q-modal{background:#fff;color:#10281c;max-width:490px;width:92%;border-radius:14px;
  padding:20px 22px;box-shadow:0 18px 50px rgba(10,30,20,.35);font-size:13.5px;line-height:1.55;
  max-height:88vh;overflow:auto}
.q-modal h3{margin:0 0 8px;font-size:16px}
.q-modal .q-meta{color:#7a5c10;font-size:12.5px;margin:10px 0}
.q-modal .q-row{display:flex;gap:12px;justify-content:flex-end;align-items:center;margin-top:12px}
.q-modal a{color:#0f7a46;font-weight:600;text-decoration:none}
.q-modal button{border:0;background:#e7efe9;border-radius:8px;padding:7px 14px;cursor:pointer;font:inherit}
.dq-row{display:flex;align-items:center;gap:8px;margin:3px 0;font-size:12.5px}
.dq-row .dq-name{flex:0 0 132px;color:var(--text-sec)}
.dq-row .dq-bar{flex:1;height:9px;border-radius:5px;background:rgba(16,40,28,.09);overflow:hidden}
.dq-row .dq-fill{display:block;height:100%;border-radius:5px;background:#20BA72}
.dq-row .dq-fill.low{background:#D9822B}
.dq-row .dq-val{flex:0 0 104px;text-align:right;white-space:nowrap;
  font-variant-numeric:tabular-nums}
.q-note{border-left:3px solid;padding:9px 11px;border-radius:6px;margin:6px 0;font-size:12.5px;
  line-height:1.5}
.q-note div+div{margin-top:5px}
.q-note.ok{border-color:#0f7a46;background:rgba(32,186,114,.10)}
.q-note.warn{border-color:#b07708;background:rgba(217,166,43,.13)}
.q-note.err{border-color:#C4453B;background:rgba(196,69,59,.10)}
.q-note.info{border-color:#2E6BB8;background:rgba(46,107,184,.09)}
.q-note b{font-variant-numeric:tabular-nums}
.q-link{color:#0f7a46;font-weight:600;text-decoration:none;
  border-bottom:1px solid rgba(15,122,70,.35)}
.q-link:hover{border-bottom-color:#0f7a46}
.eco-badge{font-size:12px;color:var(--text-sec);background:var(--bg-elevated);
  border:1px solid rgba(16,40,28,.14);border-radius:8px;padding:4px 10px;margin-right:10px;
  display:inline-flex;gap:6px;align-items:center;white-space:nowrap}
.eco-badge b{color:var(--text)}
.eco-badge .eco-i{cursor:pointer;border:1px solid rgba(16,40,28,.3);border-radius:50%;
  width:15px;height:15px;line-height:13px;font-size:10px;text-align:center;opacity:.75}
.eco-badge .eco-i:hover{opacity:1;border-color:var(--accent)}
.overlay{background:rgba(10,30,20,.4)}
.results{background:#fff;box-shadow:0 24px 60px rgba(10,30,20,.35)}
/* Следующий шаг — главный элемент разбора: один поступок и объяснение, зачем он */
.next-step{border:1px solid rgba(32,186,114,.38);background:rgba(32,186,114,.09);
  border-radius:10px;padding:14px 16px;margin-bottom:10px}
.next-step.calm{border-color:rgba(46,107,184,.32);background:rgba(46,107,184,.08)}
.ns-t{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;
  color:#0f7a46;margin-bottom:6px}
.next-step.calm .ns-t{color:#2E6BB8}
.ns-do{font-size:14px;font-weight:600;line-height:1.45}
.ns-why{font-size:13px;line-height:1.55;color:var(--text-sec);margin-top:7px}
.ns-why a.q-link{color:#0f7a46}
/* остальные замечания — свёрнуты, чтобы не забивать внимание */
.res-more{margin-top:12px;border-top:1px solid rgba(16,40,28,.10);padding-top:10px}
.res-more>summary{cursor:pointer;font-size:12.5px;font-weight:600;color:var(--text-sec);
  list-style:none;display:flex;align-items:baseline;gap:7px;padding:2px 0}
.res-more>summary::-webkit-details-marker{display:none}
.res-more>summary::before{content:'\\25B8';font-size:10px;color:var(--text-muted)}
.res-more[open]>summary::before{content:'\\25BE'}
.res-more>summary:hover{color:var(--text)}
.res-more-body{margin-top:9px}
.eco-how{color:#0f7a46;font-weight:600;cursor:pointer;white-space:nowrap;
  border-bottom:1px solid rgba(15,122,70,.35)}
.eco-how:hover{border-bottom-color:#0f7a46}
"""
swap("</style>", EXTRA_CSS + "</style>", "css")

# ── 8. Модалка метрики + разбор конфигурации ──
EXTRA_BODY = """
<div class="q-modal-back" id="qModalBack">
  <div class="q-modal">
    <h3 id="qModalTitle"></h3>
    <div id="qModalBody"></div>
    <div id="qModalDq"></div>
    <div class="q-meta" id="qModalMeta"></div>
    <div class="q-row">
      <a id="qModalLink" target="_blank" rel="noopener">Подробнее в справочнике &rarr;</a>
      <button id="qModalClose" type="button">Закрыть</button>
    </div>
  </div>
</div>
<script>
/* ═════════════════════════════════════════════════════════════════════════
   A360: экономика конфигурации источников, интегральная оценка качества данных
   и разбор неидеальной конфигурации.

   Всё, что участник видит в разборе, считается из данных кейса и справочника
   метрик: тексты под конкретный неверный выбор здесь не записаны.
   ═════════════════════════════════════════════════════════════════════════ */
(function(){
  var back=document.getElementById('qModalBack');

  /* ── мелкие помощники разметки ────────────────────────────────────────── */
  function L(mid){var m=met(mid);return {text:'«'+m.name+'»',link:m.link}}
  /* название метрики без ссылки: во фразе «что сделать сейчас» ссылки уводят
     от действия, поэтому там метрики называются простым текстом */
  function N(mid){var m=met(mid);return m?'«'+m.name+'»':mid}
  function put(el,parts){
    parts.forEach(function(p){
      if(p==null)return;
      if(typeof p==='string'){el.appendChild(document.createTextNode(p));return}
      if(p.el){el.appendChild(p.el);return}
      if(p.link){
        var a=document.createElement('a');a.className='q-link';a.href=p.link;
        a.target='_blank';a.rel='noopener';a.textContent=p.text;el.appendChild(a);return;
      }
      var b=document.createElement('b');b.textContent=p.b;el.appendChild(b);
    });
  }
  function note(cls,lines){
    var d=document.createElement('div');d.className='q-note '+cls;
    lines.forEach(function(ln){
      if(!ln)return;
      var r=document.createElement('div');put(r,ln);d.appendChild(r);
    });
    return d;
  }
  function section(title,color){
    var s=document.createElement('div');
    var h=document.createElement('div');h.className='res-section-title';
    if(color)h.style.color=color;
    h.textContent=title;s.appendChild(h);return s;
  }
  /* дни в разборе пишутся одинаково — «58 дн», как на карточках метрик и
     в замере тулбара: так число читается в любом падеже */
  function dn(v){return v+' дн'}
  function signed(v,unit){return (v>0?'+':'−')+Math.abs(v)+' '+unit}

  /* ── модалка метрики: определение, паспорт сбора, качество данных ─────── */
  function openModal(title,body,dqRows,meta,link){
    document.getElementById('qModalTitle').textContent=title;
    var b=document.getElementById('qModalBody');b.textContent=body||'';
    var dqBox=document.getElementById('qModalDq');dqBox.innerHTML='';
    if(dqRows&&dqRows.length){
      var h=document.createElement('div');
      h.style.cssText='margin:12px 0 6px;font-weight:700';
      h.textContent='Интегральная оценка качества данных: '+dqRows.dqi+' из 100';
      dqBox.appendChild(h);
      dqRows.forEach(function(r){
        var row=document.createElement('div');row.className='dq-row';
        var n=document.createElement('span');n.className='dq-name';n.textContent=r[0];
        var bar=document.createElement('span');bar.className='dq-bar';
        var f=document.createElement('span');f.className='dq-fill'+(r[2]<0.9?' low':'');
        f.style.width=Math.round(r[2]*100)+'%';bar.appendChild(f);
        var v=document.createElement('span');v.className='dq-val';
        v.textContent=Math.round(r[2]*100)+' % · вес '+r[1].toFixed(2).replace('.',',');
        row.appendChild(n);row.appendChild(bar);row.appendChild(v);dqBox.appendChild(row);
      });
      var f2=document.createElement('div');
      f2.style.cssText='margin-top:6px;font-size:12px;color:rgba(16,40,28,.62)';
      f2.textContent='Интегральная оценка = Σ (вес × частная оценка); веса заданы регламентом.';
      dqBox.appendChild(f2);
    }
    document.getElementById('qModalMeta').textContent=meta||'';
    var a=document.getElementById('qModalLink');
    if(link){a.style.display='';a.href=link}else{a.style.display='none'}
    back.classList.add('open');
  }
  function openHelp(mid){
    var m=met(mid);if(!m)return;
    var rows=m.dq||[];rows.dqi=m.dqi;
    openModal(m.name+' ('+m.abbr+')',m.def||'',rows,
      m.capex!=null?('Паспорт сбора: CAPEX '+m.capex+' т₽ единоразово · OPEX '+m.opex+
        ' т₽/мес · время до проверенного сигнала (TTE) ~'+m.tte+' дн'):'',m.link);
  }
  var CRIT_TEXT='Конфигурация оценивается по трём величинам. Срок до решения — время до '+
    'проверенного решения по критическому пути дерева: у каждой метрики свой срок сбора, '+
    'расчётные уровни наследуют максимум входов, а накопительные сверки на стыках '+
    'добавляют время. Поэтому быстрая метрика на первом уровне не гарантирует быстрого '+
    'решения — выигрывает цепочка в целом. TCO за горизонт пилота = сумма CAPEX + месяцы × '+
    'сумма OPEX по всем метрикам дерева. Интегральная оценка качества данных — свёртка шести '+
    'частных измерений с весами (методика курса; названия измерений — по ГОСТ Р 71484.2-2024, '+
    'раздел 6); у конфигурации она берётся по самому слабому источнику: '+
    'по правилу блокирующих проверок конфигурация не бывает точнее своего худшего входа. '+
    'Критерий сравнения — принцип Cost of Delay (Д. Райнертсен, The Principles of Product '+
    'Development Flow): задержка решения имеет денежную цену. Конфигурации сравниваются по '+
    'CD3 = Cost of Delay / Duration (он же WSJF в SAFe): при равной ценности решения это '+
    'интегральная оценка, делённая на произведение TTE и TCO, — «скорость проверки '+
    'решения на рубль». Актуальность данных — характеристика качества по ГОСТ Р 71484.2-2024 '+
    '(ИСО/МЭК 5259-2:2024), пункт 6.2.5; цену некачественных данных Gartner оценивает '+
    'в $12,9 млн в год на компанию.';

  ['mousedown','dblclick'].forEach(function(ev){
    document.addEventListener(ev,function(e){
      if(e.target.closest&&(e.target.closest('.help-btn')||e.target.closest('.eco-i')||
        e.target.closest('.eco-how')))e.stopPropagation();
    },true);
  });
  document.addEventListener('click',function(e){
    var b=e.target.closest&&e.target.closest('.help-btn');
    if(b){e.stopPropagation();openHelp(b.dataset.mid);return}
    if(e.target.closest&&(e.target.closest('.eco-i')||e.target.closest('.eco-how'))){
      e.stopPropagation();
      openModal('Как считается эффективность конфигурации',CRIT_TEXT,null,'',
        'longread_metrics.html#eco');return}
    if(e.target===back||e.target.id==='qModalClose')back.classList.remove('open');
  },true);

  /* ═══ расчёт конфигурации ══════════════════════════════════════════════
     Граф строится из холста с модификациями: подмена метрики в узле (ov),
     снятие узла (drop), добавление узла и связей (addNodes / addEdges).
     Один и тот же расчёт обслуживает и текущую конфигурацию, и эталон,
     и симуляцию каждого улучшения — поэтому дельты в разборе всегда сходятся.
     ═══════════════════════════════════════════════════════════════════════ */
  function graphOf(mod){
    mod=mod||{};
    var drop=mod.drop||[],ov=mod.ov||{};
    var nodes=S.nodes.filter(function(n){return drop.indexOf(n.id)<0})
      .map(function(n){return {id:n.id,mid:ov[n.id]||n.metricId}});
    (mod.addNodes||[]).forEach(function(n){nodes.push(n)});
    var ids={};nodes.forEach(function(n){ids[n.id]=1});
    var edges=S.edges.filter(function(e){return ids[e.from]&&ids[e.to]})
      .map(function(e){return {from:e.from,to:e.to}});
    (mod.addEdges||[]).forEach(function(e){if(ids[e.from]&&ids[e.to])edges.push(e)});
    return {nodes:nodes,edges:edges};
  }

  function idealGraph(){
    var c=cas();if(!c||!c.ideal)return null;
    var nodes=c.ideal.map(function(mid){return {id:'i_'+mid,mid:mid}});
    var edges=[];
    for(var tgt in (c.rules||{})){
      if(c.ideal.indexOf(tgt)<0)continue;
      var rl=c.rules[tgt];
      (rl.req||[]).concat(rl.opt||[]).forEach(function(src){
        if(c.ideal.indexOf(src)>=0)edges.push({from:'i_'+src,to:'i_'+tgt});
      });
    }
    return {nodes:nodes,edges:edges};
  }

  function evalGraph(g){
    var c=cas();if(!g||!g.nodes.length)return null;
    var H=c.horizon||3,lags=c.lags||[];
    var byId={};g.nodes.forEach(function(n){byId[n.id]=n});
    var memo={},par={},hits=[];
    function T(nid){
      if(memo[nid]!=null)return memo[nid];
      memo[nid]=0;                                   /* защита от циклов */
      var n=byId[nid],m=n&&met(n.mid),own=(m&&m.tte)||0;
      var ins=g.edges.filter(function(e){return e.to===nid});
      var mx=0,best=null;
      ins.forEach(function(e){var v=T(e.from);if(best===null||v>mx){mx=v;best=e.from}});
      var extra=0;
      lags.forEach(function(Lg){
        if(!n||Lg.target!==n.mid)return;
        var src=ins.filter(function(e){
          var s=byId[e.from];return s&&s.mid===Lg.source});
        if(src.length){extra+=Lg.extra;hits.push({lag:Lg,node:nid,src:src[0].from})}
      });
      par[nid]=best;memo[nid]=own+mx+extra;
      return memo[nid];
    }
    g.nodes.forEach(function(n){T(n.id)});
    var decNode=null;
    if(c.decision)g.nodes.forEach(function(n){if(n.mid===c.decision)decNode=n.id});
    var tte=0;
    if(decNode)tte=memo[decNode];
    else g.nodes.forEach(function(n){tte=Math.max(tte,memo[n.id])});
    var capex=0,opex=0,q=100,weak=null;
    g.nodes.forEach(function(n){
      var m=met(n.mid);if(!m||m.capex==null)return;
      capex+=m.capex;opex+=m.opex;
      if(m.dqi<q){q=m.dqi;weak=n.mid}
    });
    var tco=capex+H*opex;
    /* критический путь до решения: от узла решения вверх по «главному» входу */
    var path=[];
    if(decNode){var p=decNode;while(p){path.unshift(byId[p].mid);p=par[p]}}
    /* конус решения: всё, что влияет на решение */
    var cone={};
    if(decNode){
      var stack=[decNode];
      while(stack.length){
        var cur=stack.pop();if(cone[cur])continue;cone[cur]=1;
        g.edges.forEach(function(e){if(e.to===cur)stack.push(e.from)});
      }
    }
    return {tte:tte,tco:tco,capex:capex,opex:opex,q:q,weak:weak,H:H,path:path,
            byNode:memo,cone:cone,hits:hits,decNode:decNode,
            e:(tte>0&&tco>0)?(q/100)*1e6/(tte*tco):0};
  }

  function effPct(cur,ideal){
    if(!cur||!ideal||!ideal.e)return null;
    return Math.round(100*cur.e/ideal.e);
  }

  /* связи, которые метрика получила бы по правилам кейса */
  function implEdges(nodes,nodeId,mid){
    var c=cas(),out=[],byMid={};
    nodes.forEach(function(n){if(n.id!==nodeId)byMid[n.mid]=n.id});
    var rl=(c.rules||{})[mid];
    if(rl)(rl.req||[]).concat(rl.opt||[]).forEach(function(s){
      if(byMid[s])out.push({from:byMid[s],to:nodeId})});
    for(var tg in (c.rules||{})){
      var r2=c.rules[tg];
      if((r2.req||[]).concat(r2.opt||[]).indexOf(mid)>=0&&byMid[tg])
        out.push({from:nodeId,to:byMid[tg]});
    }
    return out;
  }

  /* месяц, на котором дешёвый вход перестаёт быть дешевле */
  function breakEven(a,b){            /* a — дешёвый на входе, b — дорогой */
    if(a.capex>=b.capex||a.opex<=b.opex)return null;
    return Math.ceil((b.capex-a.capex)/(a.opex-b.opex));
  }
  /* измерение качества, по которому источники расходятся сильнее всего */
  function worstDim(a,b){
    var best=null;
    (a.dq||[]).forEach(function(r,i){
      var rb=(b.dq||[])[i];if(!rb)return;
      var gap=r[1]*(rb[2]-r[2]);
      if(!best||gap>best.gap)best={gap:gap,name:r[0],a:r[2],b:rb[2]};
    });
    return best&&best.gap>0?best:null;
  }
  function pct(v){return Math.round(v*100)+' %'}

  /* Дерево собрано: все связи верны, все метрики дерева на месте и соединены,
     источник на каждом выборе подведён. Лишняя метрика, лежащая на холсте без
     связей, сборке не мешает — она не входит в дерево кейса, о ней разбор
     говорит отдельно. А вот метрика самого дерева без связей — это несобранное
     дерево: её данные в расчёт решения не попадают.
     Пока дерево не собрано, ни срок, ни стоимость, ни качество конфигурации
     ещё ничего не значат: у половины дерева критический путь короче не потому,
     что решение придёт быстрее, а потому, что ветки не проведены. */
  function treeReady(v){
    if(!v||v.sandbox)return true;
    if(v.ok)return true;
    var c=cas(),ideal=(c&&c.ideal)||[];
    return (v.edges||[]).every(function(e){return e.s==='ok'})&&
           (v.metrics||[]).every(function(m){return m.s==='ok'})&&
           (v.qmsgs||[]).every(function(q){return q.t!=='err'})&&
           (v.iso||[]).every(function(m){return ideal.indexOf(m)<0});
  }

  /* ═══ живой замер в тулбаре ═══ */
  var tb=document.querySelector('.toolbar');
  var eb=document.createElement('span');eb.className='eco-badge';eb.style.display='none';
  var tbInfo=document.getElementById('tbInfo');
  tb.insertBefore(eb,tbInfo);
  var _updTb=updTb;
  updTb=function(){
    _updTb();
    var eco=S.nodes.length?evalGraph(graphOf()):null;
    if(!eco){eb.style.display='none';return}
    eb.style.display='';
    if(!treeReady(validate())){
      eb.innerHTML='Срок, стоимость и качество данных замер покажет, '+
        'когда дерево будет собрано'+
        ' <span class="eco-i" title="как это считается">i</span>';
      return;
    }
    eb.innerHTML='Срок до решения <b>'+(eco.tte||'—')+(eco.tte?' дн':'')+'</b> · TCO('+eco.H+
      ' мес) <b>'+eco.tco+' т₽</b> · качество данных <b>'+eco.q+'</b>'+
      ' <span class="eco-i" title="как это считается">i</span>';
  };

  /* ═══ проверка: развилки, изолированные метрики ═══ */
  var _validate=validate;
  validate=function(){
    var r=_validate();
    /* в свободном режиме о метриках без связей уже сказано в самой проверке —
       второй раз теми же словами не повторяем */
    if(r.sandbox)return r;
    var c=cas();r.qmsgs=[];r.forks=[];
    var absentAllowed=[];
    (c.quality||[]).forEach(function(g){
      var tn=nodeByMet(g.target);
      var conn=tn?S.edges.filter(function(e){return e.to===tn.id})
        .map(function(e){var n=S.nodes.find(function(x){return x.id===e.from});return n&&n.metricId})
        .filter(Boolean):[];
      var chosen=g.options.filter(function(o){return conn.indexOf(o)>=0});
      /* невыбранный вариант развилки — не «забытая метрика»: требовать на холст
         оба источника нельзя, об этом говорит отдельное сообщение о развилке */
      g.options.forEach(function(o){if(chosen.indexOf(o)<0)absentAllowed.push(o)});
      if(!tn||!chosen.length){
        /* g кладётся в сообщение, чтобы разбор написал этот выбор словами:
           термина «развилка» участник нигде не встречал */
        r.qmsgs.push({t:'err',g:g,m:'Источник для метрики «'+met(g.target).name+
          '» ещё не выбран: подойдёт '+
          g.options.map(function(o){return '«'+met(o).name+'»'}).join(' или ')+'.'});
      }else{
        r.forks.push({g:g,chosen:chosen});
        if(chosen.length===1&&chosen[0]===g.best)r.qmsgs.push({t:'ok',m:g.okNote});
      }
    });
    r.metrics=r.metrics.filter(function(m){
      return !((m.s==='not_on_canvas'||m.s==='missing')&&absentAllowed.indexOf(m.mid)>=0)});
    r.iso=S.nodes.filter(function(n){
      return !S.edges.some(function(e){return e.from===n.id||e.to===n.id})})
      .map(function(n){return n.metricId});
    var edgesOk=r.edges.every(function(e){return e.s==='ok'});
    var metricsOk=r.metrics.every(function(m){return m.s==='ok'});
    var qOk=r.qmsgs.every(function(q){return q.t!=='err'});
    r.ok=edgesOk&&metricsOk&&qOk&&!r.iso.length;
    return r;
  };

  /* Роль метрики в дереве кейса, сказанная фразой: на что влияет, из чего
     считается и по какому источнику её собирают на выбор. Варианты выбора
     перечисляются отдельно — иначе они читаются как обязательные входы. */
  function connectHint(mid){
    var c=cas(),to=[],req=[],opt=[],forks=[],inFork={};
    function q(x){var m=met(x);return '«'+(m?m.name:x)+'»'}
    function list(a,sep){
      if(a.length<2)return a.join('');
      return a.slice(0,-1).join(', ')+(sep||' и ')+a[a.length-1];
    }
    for(var k in (c.rules||{})){
      var rl=c.rules[k];
      if((rl.req||[]).concat(rl.opt||[]).indexOf(mid)>=0)to.push(q(k));
    }
    (c.quality||[]).forEach(function(g){
      if(g.target!==mid)return;
      forks.push(g);g.options.forEach(function(o){inFork[o]=1});
    });
    var rl2=(c.rules||{})[mid];
    if(rl2){
      req=(rl2.req||[]).filter(function(x){return !inFork[x]}).map(q);
      opt=(rl2.opt||[]).filter(function(x){return !inFork[x]}).map(q);
    }
    var main=[];
    if(to.length)main.push('влияет на '+list(to));
    if(req.length)main.push('рассчитывается из '+list(req));
    else if(opt.length)main.push('учитывает '+list(opt));
    if(req.length&&opt.length)main.push('учитывает '+list(opt));
    var s=list(main,' и ');
    forks.forEach(function(g){
      s+=(s?', а ':'')+g.slot.toLowerCase()+' для неё выбирается из двух: '+
        list(g.options.map(q),' или ');
    });
    return s||'её место — в дереве кейса';
  }

  /* ═══ разбор конфигурации ══════════════════════════════════════════════
     traps — в чём ограничение именно этой конфигурации;
     recs  — что заменить, с выигрышем в днях, рублях и пунктах качества.
     ═══════════════════════════════════════════════════════════════════════ */
  function analyze(r){
    var c=cas();
    var cur=evalGraph(graphOf());
    var ig=idealGraph();
    var ideal=ig?evalGraph(ig):null;
    if(!cur)return null;
    var dec=c.decision&&met(c.decision)?met(c.decision).name:null;
    var traps=[],cands=[],covered={};

    /* — развилки: выбран не лучший источник, либо подключены сразу оба — */
    (r.forks||[]).forEach(function(f){
      var g=f.g,tgtNode=nodeByMet(g.target);
      var bad=f.chosen.filter(function(o){return o!==g.best});
      if(!bad.length)return;
      var bestM=met(g.best);
      bad.forEach(function(o){
        var badM=met(o),n=nodeByMet(o);
        if(f.chosen.indexOf(g.best)>=0){
          /* оба источника развилки подключены разом */
          var wo=n?evalGraph(graphOf({drop:[n.id]})):null;
          var ln=['К метрике ',L(g.target),' подведены сразу оба источника — ',
                  L(g.best),' и ',L(o),'. Один и тот же вход собирается дважды, '+
                  'и второй сбор добавляет ',
                  {b:(cur.tco-(wo?wo.tco:cur.tco))+' т₽'},
                  ' к стоимости владения за ',{b:cur.H+' мес'}];
          /* откуда взялись лишние дни, говорим по факту расчёта: накопительная
             сверка на стыке бывает не у каждого источника, а решение в любом
             случае ждёт более медленную из двух веток */
          var hit0=cur.hits.filter(function(h){return h.lag.source===o})[0];
          if(wo&&wo.tte<cur.tte)ln=ln.concat([' и ещё ',{b:dn(cur.tte-wo.tte)},
            ' к сроку до решения: '+(hit0
              ? 'расчёт на стыке с этим источником требует накопительной сверки, '+
                'и решение ждёт её.'
              : 'решение ждёт более медленный из двух источников.')]);
          else ln.push(', а срок до решения от этого не сокращается.');
          traps.push(ln);
          if(n)cands.push({kind:'drop',node:n.id,mid:o});
          return;
        }
        /* выбран только неудачный источник */
        var line1=['Для метрики ',L(g.target),' вы выбрали источник ',L(o),'.'];
        if(badM.flaw)line1.push(' Его ограничение в том, что '+badM.flaw+'.');
        traps.push(line1);
        var hit=cur.hits.filter(function(h){return h.lag.source===o})[0];
        /* Во что этот выбор обходится по сроку, считаем как разницу между
           конфигурациями — этой и той же с лучшим источником, — а не как
           разницу паспортов источников: собственный срок сбора попадает в срок
           до решения только тогда, когда источник стоит на самой длинной ветке
           дерева. Источник вне критического пути не добавляет решению ни дня. */
        var placed=nodeByMet(g.best),swpMod=null;
        if(n){
          if(placed)swpMod={drop:[n.id],
            addEdges:implEdges(graphOf({drop:[n.id]}).nodes,placed.id,g.best)};
          else{swpMod={ov:{}};swpMod.ov[n.id]=g.best}
        }
        var swp=swpMod?evalGraph(graphOf(swpMod)):null;
        var dT=swp?cur.tte-swp.tte:null;
        function tteTail(){
          if(dT===null)return[];
          if(dT>0)return['По самой длинной ветке дерева решение'+
            (dec?' по метрике «'+dec+'»':'')+' приходит через ',{b:dn(cur.tte)},' — на ',
            {b:dn(dT)},' позже, чем с источником ',L(g.best),', с которым оно приходит через ',
            {b:dn(swp.tte)},'.'];
          if(dT===0)return['На срок до решения этот выбор при этом не влияет: источник '+
            'не стоит на самой длинной ветке дерева, и решение'+
            (dec?' по метрике «'+dec+'»':'')+' приходит через ',{b:dn(cur.tte)},
            ' с любым из двух источников. Разница между ними — в стоимости владения '+
            'и в качестве данных.'];
          return['Решение'+(dec?' по метрике «'+dec+'»':'')+' с ним приходит даже раньше — '+
            'через ',{b:dn(cur.tte)},' против ',{b:dn(swp.tte)},' у источника ',L(g.best),
            '; цена этой скорости — стоимость владения и качество данных.'];
        }
        if(hit){
          traps.push([
            'Сам по себе этот источник быстрее: проверенный сигнал приходит за ',
            {b:dn(badM.tte)},' против ',{b:dn(bestM.tte)},' у источника ',L(g.best),
            '. Но на стыке с метрикой ',L(hit.lag.target),
            ' каждый расчёт требует накопительной сверки, а это ещё ',{b:dn(hit.lag.extra)},
            '. '].concat(tteTail()).concat(
            dT>0?[' Быстрый источник не даёт быстрого решения.']:[]));
        }else if(badM.tte!==bestM.tte||dT){
          traps.push([
            'Проверенную картину он отдаёт за ',{b:dn(badM.tte)},' против ',
            {b:dn(bestM.tte)},' у источника ',L(g.best),'. '].concat(tteTail()).concat(
            (dT>0&&dT<badM.tte-bestM.tte)
              ? [' На срок до решения переносится не вся разница сроков сбора, '+
                 'а только та её часть, которая попадает на самую длинную ветку.']
              : []));
        }
        var be=breakEven(badM,bestM);
        if(be!==null){
          traps.push([
            'На подключении он дешевле на ',{b:(bestM.capex-badM.capex)+' т₽'},
            ', но в обслуживании дороже на ',{b:(badM.opex-bestM.opex)+' т₽/мес'},
            ': экономия исчерпывается на ',{b:be+'-м месяце'},' работы.'
          ]);
        }else if(badM.capex<bestM.capex){
          var save=(bestM.capex-badM.capex)+cur.H*(bestM.opex-badM.opex);
          traps.push([
            'На подключении он дешевле на ',{b:(bestM.capex-badM.capex)+' т₽'},
            (badM.opex===bestM.opex
              ? ', а в обслуживании стоит столько же — '+badM.opex+' т₽/мес'
              : ', и в обслуживании дешевле на '+(bestM.opex-badM.opex)+' т₽/мес'),
            '. Вся экономия — ',{b:save+' т₽'},' за ',{b:cur.H+' мес'},
            ': это и есть цена, за которую покупается задержка решения и '+
            'потеря в качестве данных.'
          ]);
        }
        var wd=worstDim(badM,bestM);
        traps.push([
          'Качество данных этого источника — ',{b:badM.dqi+' из 100'},
          ' против ',{b:bestM.dqi},' у источника ',L(g.best),
          (wd?'; сильнее всего расходится измерение «'+wd.name+'»: '+pct(wd.a)+' против '+
            pct(wd.b):''),'.'
        ]);
        /* Оценка конфигурации идёт по самому слабому источнику, поэтому выигрыш
           от замены упирается в следующее по слабости звено: без этой фразы
           числа читаются как несогласованные — «81 против 95», а замена даёт
           один пункт. */
        if(n){
          var capQ=null,capMid=null;
          graphOf().nodes.forEach(function(nd){
            if(nd.id===n.id)return;
            var m2=met(nd.mid);if(!m2||m2.capex==null)return;
            if(capQ===null||m2.dqi<capQ){capQ=m2.dqi;capMid=nd.mid}
          });
          if(capQ!==null){
            var q0=Math.min(capQ,badM.dqi),q1=Math.min(capQ,bestM.dqi),ln2;
            if(q1>q0){
              ln2=['Качество данных всей конфигурации считается по самому слабому источнику, '+
                   'поэтому замена поднимет его с ',{b:q0+' из 100'},' до ',{b:q1+' из 100'}];
              ln2=ln2.concat(capQ<bestM.dqi
                ? [': выше не пускает ',L(capMid),' со своими ',{b:capQ+' из 100'},
                   ' — насколько поможет замена одного источника, задаёт следующее '+
                   'по слабости звено.']
                : ['.']);
            }else{
              ln2=['Качество данных всей конфигурации считается по самому слабому источнику, '+
                   'и от этой замены оно не изменится: оценку держит ',L(capMid),' со своими ',
                   {b:capQ+' из 100'},' — улучшение одного звена ограничено другим.'];
            }
            traps.push(ln2);
          }
        }
        if(!n)return;
        if(placed){
          /* лучший источник уже на холсте, но не подведён к развилке: менять
             метрику в узле нельзя — иначе он окажется на холсте дважды */
          var left=graphOf({drop:[n.id]}).nodes;
          cands.push({kind:'replace',node:n.id,mid:o,to:g.best,target:g.target,
                      drop:[n.id],edges:implEdges(left,placed.id,g.best)});
        }else{
          cands.push({kind:'swap',node:n.id,mid:o,to:g.best,target:g.target});
        }
        covered[g.best]=1;
      });
    });

    /* — метрики на холсте без единой связи — */
    (r.iso||[]).forEach(function(mid){
      var m=met(mid),n=nodeByMet(mid);
      var own=m.capex+cur.H*m.opex;
      traps.push([
        'Метрика ',L(mid),' лежит на холсте, но не соединена ни с одной другой. '+
        'Её сбор при этом оплачивается — ',{b:own+' т₽'},' за ',{b:cur.H+' мес'},
        ', — а в решение данные не попадают. По дереву кейса она '+connectHint(mid)+'.'
      ]);
      if(n&&!covered[mid]){
        if((c.ideal||[]).indexOf(mid)>=0){
          var eg=implEdges(graphOf().nodes,n.id,mid);
          if(eg.length)cands.push({kind:'link',node:n.id,mid:mid,edges:eg});
        }else cands.push({kind:'drop',node:n.id,mid:mid});
      }
    });

    /* — связанные метрики, которые не влияют на решение и только копят TCO — */
    if(cur.decNode){
      S.nodes.forEach(function(n){
        if((c.ideal||[]).indexOf(n.metricId)>=0)return;
        if(cur.cone[n.id])return;
        if((r.iso||[]).indexOf(n.metricId)>=0)return;
        if(cands.some(function(x){return x.node===n.id}))return;
        var m=met(n.metricId),own=m.capex+cur.H*m.opex;
        traps.push([
          'Метрика ',L(n.metricId),' не влияет на решение'+
          (dec?' по метрике «'+dec+'»':'')+', но добавляет ',{b:own+' т₽'},
          ' к стоимости владения за ',{b:cur.H+' мес'},'.'
        ]);
        cands.push({kind:'drop',node:n.id,mid:n.metricId});
      });
    }

    /* — самое слабое звено по качеству данных — */
    if(cur.weak&&ideal&&cur.q<ideal.q){
      var wm=met(cur.weak);
      var low=(wm.dq||[]).slice().sort(function(a,b){return a[2]-b[2]}).slice(0,2)
        .map(function(x){return x[0].toLowerCase()+' '+pct(x[2])}).join(', ');
      traps.push([
        'Качество данных всей конфигурации — ',{b:cur.q+' из 100'},
        ' против ',{b:ideal.q},' у лучшей сборки кейса. Эту оценку задаёт источник ',
        L(cur.weak),' ('+low+'): собранное дерево не бывает точнее самого слабого '+
        'из своих входов.'
      ]);
    }

    /* — метрики, которых не хватает на холсте: их тоже можно оценить числом.
         Варианты незакрытой развилки сюда не попадают: выбор источника —
         это и есть задание кейса, подсказывать его нельзя — */
    var forkOpts={};
    (c.quality||[]).forEach(function(g){g.options.forEach(function(o){forkOpts[o]=1})});
    var vn=0;
    (r.metrics||[]).forEach(function(mm){
      if(mm.s!=='missing'&&mm.s!=='not_on_canvas')return;
      if(forkOpts[mm.mid])return;
      if(cands.length>4)return;
      var vid='v'+(++vn);
      var nodes=graphOf().nodes.concat([{id:vid,mid:mm.mid}]);
      cands.push({kind:'add',mid:mm.mid,node:vid,
                  addNodes:[{id:vid,mid:mm.mid}],
                  edges:implEdges(nodes,vid,mm.mid)});
    });

    /* — недостающие связи между уже размещёнными метриками — */
    (r.metrics||[]).forEach(function(mm){
      if(mm.s!=='partial'||!(mm.miss||[]).length)return;
      var tn=nodeByMet(mm.mid);if(!tn)return;
      var eg=[];
      mm.miss.forEach(function(s){var sn=nodeByMet(s);if(sn)eg.push({from:sn.id,to:tn.id})});
      if(eg.length)cands.push({kind:'wire',node:tn.id,mid:mm.mid,edges:eg,miss:mm.miss});
    });

    /* — симуляция каждого улучшения на том же расчёте — */
    var recs=[],seen={};
    cands.forEach(function(x){
      /* один и тот же недостающий стык не советуем дважды разными словами */
      var sig=(x.edges||[]).map(function(e){return e.from+'>'+e.to}).sort().join(',');
      if(sig){if(seen[sig])return;seen[sig]=1}
      var mod={};
      if(x.kind==='swap'){mod.ov={};mod.ov[x.node]=x.to}
      else if(x.kind==='drop')mod.drop=[x.node];
      else if(x.kind==='replace'){mod.drop=x.drop;mod.addEdges=x.edges}
      else if(x.kind==='link'||x.kind==='wire')mod.addEdges=x.edges;
      else if(x.kind==='add'){mod.addNodes=x.addNodes;mod.addEdges=x.edges}
      var sim=evalGraph(graphOf(mod));
      if(!sim)return;
      recs.push({x:x,sim:sim});
    });
    /* сначала чиним то, что уже на холсте (связи), потом добираем недостающие
       метрики, и лишь затем — экономические замены, по эффективности */
    var order={link:0,wire:1,add:2,drop:3,swap:3,replace:3};
    recs.sort(function(a,b){
      var d=order[a.x.kind]-order[b.x.kind];
      if(d)return d;
      return b.sim.e-a.sim.e;
    });
    /* экономические шаги показываем только если они действительно улучшают */
    recs=recs.filter(function(rc){
      return order[rc.x.kind]<3||rc.sim.e>cur.e*1.001;
    }).slice(0,2);

    return {cur:cur,ideal:ideal,traps:traps,recs:recs,dec:dec,
            need:ig?ig.edges.length:null,   /* связей в правильном дереве кейса */
            eff:effPct(cur,ideal)};
  }

  /* ═══════════════════════════════════════════════════════════════════════
     Разбор для участника.

     Главный элемент — следующий шаг: одна фраза, что сделать прямо сейчас,
     и одна, почему это улучшит результат. Всё остальное уходит ниже, под
     свёрнутые заголовки, чтобы не забивать внимание. Экономика показывается
     только тогда, когда дерево собрано: у половины дерева три числа ничего
     не значат.
     ═══════════════════════════════════════════════════════════════════════ */

  /* Понятие «одну метрику можно взять из разных источников» объясняется
     в момент первого появления: отдельного термина участник нигде не
     встречал и запоминать его не должен. */
  var CHOICE_INTRO='Одну и ту же метрику иногда можно собрать из разных источников, '+
    'и выбрать нужно ровно один: дерево останется верным при любом выборе, а срок, '+
    'стоимость и качество данных — разными. ';

  function plu(n,f){
    var a=n%10,b=n%100;
    if(a===1&&b!==11)return f[0];
    if(a>=2&&a<=4&&(b<10||b>=20))return f[1];
    return f[2];
  }
  /* роль метрики в дереве кейса словами; null — метрики в дереве нет */
  function roleOf(mid){
    var c=cas(),known=!!(c.rules||{})[mid];
    for(var k in (c.rules||{})){
      var r2=c.rules[k];
      if((r2.req||[]).concat(r2.opt||[]).indexOf(mid)>=0)known=true;
    }
    return known?connectHint(mid):null;
  }
  function edgeEnds(eid){
    var e=S.edges.filter(function(x){return x.id===eid})[0];if(!e)return null;
    var f=S.nodes.filter(function(n){return n.id===e.from})[0];
    var t=S.nodes.filter(function(n){return n.id===e.to})[0];
    return (f&&t)?{from:f.metricId,to:t.metricId}:null;
  }
  /* метрика, с которой разумно начать сборку: верх дерева, не вариант выбора */
  function firstMetric(c){
    var forkOpt={};
    (c.quality||[]).forEach(function(g){g.options.forEach(function(o){forkOpt[o]=1})});
    var ids=(c.ideal||[]).filter(function(m){return !forkOpt[m]});
    var lead=ids.filter(function(m){var mm=met(m);return mm&&mm.type==='leading'})[0];
    return lead||ids[0]||(c.ideal||[])[0];
  }

  /* Что мешает дереву быть собранным — в том порядке, в котором это разумно
     делать: убрать неверную связь, донести метрику, соединить, выбрать
     источник. Первый пункт становится следующим шагом. */
  function structSteps(r){
    var c=cas(),out=[],introUsed=false,covered={};
    function ord(mid){var i=(c.ideal||[]).indexOf(mid);return i<0?99:i}

    (r.edges||[]).forEach(function(e){
      if(e.s!=='invalid')return;
      var p=edgeEnds(e.eid);if(!p)return;
      out.push({sort:[0,ord(p.to)],
        do:['Уберите связь от '+N(p.from)+' к '+N(p.to)+': щёлкните по ней на схеме '+
            'и нажмите клавишу Delete.'],
        why:(c.rules||{})[p.to]
          ? ['Значение метрики ',L(p.to),' не рассчитывается из метрики ',L(p.from),
             ', поэтому такая связь ведёт расчёт по несуществующему правилу. '+
             'На схеме она отмечена красным.']
          : ['Метрика ',L(p.to),' — опережающая: она ни из чего не рассчитывается, '+
             'и входящих связей у неё не бывает. На схеме связь отмечена красным.']});
    });

    (r.metrics||[]).forEach(function(m){
      if(m.s!=='missing'&&m.s!=='not_on_canvas')return;
      var role=roleOf(m.mid);
      out.push({sort:[1,ord(m.mid)],
        do:['Перенесите на холст метрику '+N(m.mid)+' — её карточка лежит на левой панели.'],
        why:['Пока метрики нет на холсте, эту часть дерева не из чего собрать'+
             (role?': по дереву кейса она '+role:'')+'.']});
    });

    (r.metrics||[]).forEach(function(m){
      if(m.s!=='partial')return;
      (m.miss||[]).forEach(function(src){
        if(!nodeByMet(src))return;     /* сначала эту метрику надо поставить на холст */
        covered[src]=1;covered[m.mid]=1;
        out.push({sort:[2,ord(m.mid)],
          do:['Проведите связь от '+N(src)+' к '+N(m.mid)+': потяните от нижнего порта '+
              'карточки '+N(src)+' к верхнему порту карточки '+N(m.mid)+'.'],
          why:['Метрика ',L(m.mid),' рассчитывается из метрики ',L(src),
               ', и пока этой связи нет, расчёт в дереве не замкнут.']});
      });
    });

    (r.qmsgs||[]).forEach(function(q){
      if(q.t!=='err'||!q.g)return;
      var g=q.g,intro=introUsed?'':CHOICE_INTRO;introUsed=true;
      covered[g.target]=1;g.options.forEach(function(o){covered[o]=1});
      out.push({sort:[3,ord(g.target)],
        do:['Подведите к метрике '+N(g.target)+' один из двух источников: '+
            g.options.map(N).join(' или ')+'.'],
        why:[intro+'Здесь такой выбор называется «'+g.slot.toLowerCase()+
             '»; что стоит за каждым источником, описано в справочнике: ',
             L(g.options[0]),' и ',L(g.options[1]),
             '. Разбор покажет, чего этот выбор стоит по сроку, деньгам '+
             'и качеству данных.']});
    });

    (r.iso||[]).forEach(function(mid){
      var n=nodeByMet(mid);if(!n)return;
      var role=roleOf(mid);
      /* метрика лучшей сборки этого кейса — её надо соединить; всё остальное
         (например, невыбранный источник) в дерево не входит: советовать
         «соедините» тут нельзя, иначе один и тот же вход соберётся дважды */
      var need=(c.ideal||[]).indexOf(mid)>=0;
      /* соединять пока не с чем: нужные соседи ещё не на холсте — шаг придёт позже */
      if(need&&!implEdges(graphOf().nodes,n.id,mid).length)return;
      /* про эту метрику уже сказано конкретнее — «проведите связь от … к …» */
      if(covered[mid])return;
      out.push({sort:[4,ord(mid)],
        do:[need?'Соедините метрику '+N(mid)+' с деревом.'
                :'Уберите метрику '+N(mid)+' с холста.'],
        why:need?['По дереву кейса она '+role+', но ни одной связи у неё сейчас нет: '+
                  'данные собираются, а в расчёт решения не попадают.']
                :[(role?'В лучшей сборке этого кейса она не участвует':
                         'В дереве этого кейса она не участвует')+
                  ', а её сбор всё равно оплачивается: данные собираются, '+
                  'а в расчёт решения не попадают.']});
    });

    out.sort(function(a,b){return (a.sort[0]-b.sort[0])||(a.sort[1]-b.sort[1])});
    return out;
  }

  /* Следующий шаг по экономике конфигурации: что заменить и что от этого
     изменится. Числа берутся из той же симуляции, что и раньше. */
  function recStep(rc,a,r){
    var x=rc.x,s=rc.sim,cur=a.cur,d,ph=[];
    if(x.kind==='swap')d='Замените на входе метрики '+N(x.target)+' источник '+
      N(x.mid)+' на '+N(x.to)+'.';
    else if(x.kind==='replace')d='Уберите с холста '+N(x.mid)+' и подведите к метрике '+
      N(x.target)+' уже размещённый источник '+N(x.to)+'.';
    else if(x.kind==='drop')d='Уберите метрику '+N(x.mid)+' с холста.';
    else if(x.kind==='link')d='Соедините метрику '+N(x.mid)+' с деревом.';
    else if(x.kind==='wire')d='Подведите к метрике '+N(x.mid)+' недостающие входы: '+
      x.miss.map(N).join(', ')+'.';
    else d='Разместите метрику '+N(x.mid)+' на холсте и свяжите её по дереву.';
    var dT=s.tte-cur.tte,dC=s.tco-cur.tco,dQ=s.q-cur.q;
    if(dT<0)ph.push(['Решение придёт через ',{b:dn(s.tte)},' вместо ',{b:dn(cur.tte)},'.']);
    else if(dT>0)ph.push(['Срок до решения вырастет с ',{b:dn(cur.tte)},' до ',
      {b:dn(s.tte)},'.']);
    if(dQ>0)ph.push(['Качество данных вырастет с ',{b:cur.q},' до ',{b:s.q+' из 100'},'.']);
    else if(dQ<0)ph.push(['Качество данных снизится с ',{b:cur.q},' до ',
      {b:s.q+' из 100'},'.']);
    if(dC>0)ph.push(['Владение подорожает с ',{b:cur.tco+' т₽'},' до ',{b:s.tco+' т₽'},
      ' за '+cur.H+' мес.']);
    else if(dC<0)ph.push(['Владение подешевеет с ',{b:cur.tco+' т₽'},' до ',
      {b:s.tco+' т₽'},' за '+cur.H+' мес.']);
    if(!ph.length)ph.push(['Срок и стоимость не изменятся: сбор этой метрики уже '+
      'оплачен — изменится то, что её данные наконец попадут в расчёт решения.']);
    var e2=effPct(s,a.ideal);
    if(e2!=null&&a.eff!=null&&r.ok)ph.push(['Эффективность конфигурации '+
      (e2>a.eff?'поднимется':'изменится')+' с ',{b:a.eff+' %'},' до ',{b:e2+' %'},
      ' от лучшей сборки кейса.']);
    var why=[];ph.forEach(function(pp,i){if(i)why.push(' ');why=why.concat(pp)});
    return {do:[d],why:why};
  }

  /* ── блоки разметки разбора ──────────────────────────────────────────── */
  function head(ico,title,sub){
    var h=document.createElement('div');h.className='res-head';
    var i=document.createElement('span');i.className='res-icon';i.innerHTML=ico;
    var box=document.createElement('div');
    var t1=document.createElement('div');t1.className='res-title';t1.textContent=title;
    var t2=document.createElement('div');t2.className='res-sub';t2.textContent=sub;
    box.appendChild(t1);box.appendChild(t2);h.appendChild(i);h.appendChild(box);
    return h;
  }
  function stepBlock(item,title,calm){
    var d=document.createElement('div');d.className='next-step'+(calm?' calm':'');
    var t=document.createElement('div');t.className='ns-t';t.textContent=title;
    var a1=document.createElement('div');a1.className='ns-do';put(a1,item.do);
    var w=document.createElement('div');w.className='ns-why';put(w,item.why);
    d.appendChild(t);d.appendChild(a1);d.appendChild(w);return d;
  }
  function more(title,open){
    var d=document.createElement('details');d.className='res-more';if(open)d.open=true;
    var s=document.createElement('summary');s.textContent=title;d.appendChild(s);
    var b=document.createElement('div');b.className='res-more-body';d.appendChild(b);
    d.body=b;return d;
  }
  function ecoHow(){
    var s=document.createElement('span');s.className='eco-how';
    s.textContent='Как считается эффективность';return s;
  }
  function ecoLines(a){
    var out=[],p=(a.cur.path||[]).filter(function(m){return met(m)});
    var pathTxt=p.length>1?p.map(function(m){return '«'+met(m).name+'»'}).join(' → '):null;
    out.push(['Решение'+(a.dec?' по метрике «'+a.dec+'»':'')+' станет доступно через ',
      {b:dn(a.cur.tte)},' после начала сбора данных: столько занимает самая длинная '+
      'ветка дерева'+(pathTxt?' — '+pathTxt:'')+'. Более короткие ветки ждут её.']);
    out.push(['Владение этими данными обойдётся в ',{b:a.cur.tco+' т₽'},' за '+a.cur.H+
      ' мес: ',{b:a.cur.capex+' т₽'},' единоразово на подключение источников и по ',
      {b:a.cur.opex+' т₽'},' в месяц на их поддержание.']);
    var ql=['Качество данных конфигурации — ',{b:a.cur.q+' из 100'}];
    if(a.cur.weak)ql=ql.concat(['. Эту оценку задаёт источник ',L(a.cur.weak),
      ': собранное дерево не бывает точнее самого слабого из своих входов.']);
    else ql.push('.');
    out.push(ql);
    if(a.eff!=null)out.push(['Эффективность конфигурации — ',{b:a.eff+' %'},
      ' от лучшей сборки этого кейса. Она сравнивает конфигурации по качеству данных, '+
      'отнесённому к сроку и стоимости: чем раньше и дешевле приходит решение при том '+
      'же качестве данных, тем оценка выше. ',{el:ecoHow()}]);
    return out;
  }
  function calcCards(r){
    var c=cas(),box=document.createElement('div');
    Object.keys(c.calc||{}).forEach(function(mid){
      var cl=c.calc[mid],ri=(r.calcs||[]).filter(function(x){return x.mid===mid})[0];
      var d=document.createElement('div');d.className='calc-card';
      var hd=document.createElement('div');hd.className='calc-head';
      var dot=document.createElement('span');
      var lb=document.createElement('span');lb.className='calc-label';lb.textContent=cl.lbl;
      hd.appendChild(dot);hd.appendChild(lb);d.appendChild(hd);
      var fm=document.createElement('div');fm.className='calc-formula';
      fm.textContent=cl.formula;d.appendChild(fm);
      if(ri&&ri.s==='ok'){
        dot.className='calc-dot ok';dot.innerHTML='&#10003;';
        var st1=document.createElement('div');st1.className='calc-formula';
        st1.textContent='В вашем дереве этот расчёт собран.';d.appendChild(st1);
        var ex=document.createElement('div');ex.className='calc-example';
        ex.textContent=cl.example;d.appendChild(ex);
      }else if(ri&&ri.s==='partial'){
        dot.className='calc-dot warn';dot.textContent='!';
        var w=document.createElement('div');w.className='calc-warn';
        w.textContent=(ri.miss||[]).length
          ? 'Чтобы этот расчёт заработал, подведите к метрике '+N(mid)+' ещё '+
            ri.miss.map(N).join(' и ')+'.'
          : 'К метрике '+N(mid)+' подведена лишняя связь: расчёт заработает, когда '+
            'вы её уберёте.';
        d.appendChild(w);
      }else{
        dot.className='calc-dot err';dot.innerHTML='&#10007;';
        var er=document.createElement('div');er.className='calc-err';
        er.textContent='Метрики '+N(mid)+' ещё нет на холсте, поэтому расчёт '+
          'не выполняется.';
        d.appendChild(er);
      }
      box.appendChild(d);
    });
    return box;
  }

  /* ═══ вывод разбора ═══ */
  var _showRes=showRes;
  showRes=function(r){
    _showRes(r);                        /* SCORM, оверлей, подсветка связей */
    if(!r||r.sandbox)return;
    var closeBtn=resP.querySelector('button');
    resP.textContent='';                /* разбор собирается заново, полными фразами */
    var c=cas(),a=analyze(r),steps=structSteps(r);
    var eff=(a&&r.ok)?a.eff:null;
    var st=!S.nodes.length?'empty':(!r.ok?'build':((eff!=null&&eff<100)?'better':'best'));

    /* — счётчик связей: за образец берётся правильное дерево кейса, а неверно
         проведённые связи называются отдельным предложением — */
    var corr=(r.edges||[]).filter(function(e){return e.s==='ok'}).length;
    var wrong=(r.edges||[]).filter(function(e){return e.s==='invalid'}).length;
    var need=a?a.need:null,cnt;
    /* согласование по числу: «проведена 1 связь», но «проведено 2 связи» */
    function corrTxt(k){
      return plu(k,['Верно проведена ','Верно проведено ','Верно проведено '])+k+' '+
        plu(k,['связь','связи','связей']);
    }
    if(need==null)cnt=corrTxt(corr)+'.';
    else if(!corr)cnt='Пока не проведено ни одной из '+need+' '+
      plu(need,['связи','связей','связей'])+' этого дерева.';
    else if(corr<need)cnt=corrTxt(corr)+' из '+need+', нужных в этом дереве.';
    else if(corr===need)cnt=need===1?'Единственная связь этого дерева проведена верно.'
      :('Все '+need+' '+plu(need,['связь','связи','связей'])+' этого дерева проведены верно.');
    else cnt='Все нужные связи проведены, и есть лишние: верных связей '+corr+' при '+
      need+' необходимых.';
    if(wrong)cnt+=' Ещё '+wrong+' '+plu(wrong,['связь','связи','связей'])+' '+
      plu(wrong,['проведена','проведены','проведены'])+' неверно.';

    /* — вердикт — */
    var ttl,sub,ico;
    if(st==='empty'){
      ico='&#8505;';ttl='Дерево ещё не собрано';
      sub='На холсте нет ни одной метрики.';
    }else if(st==='build'){
      ico='&#9888;';
      var k0=steps.length?steps[0].sort[0]:1;
      /* дерево кейса собрано целиком, а на холсте осталась метрика вне дерева:
         это то же состояние, что и «подведены оба источника», — и называется
         оно так же, а не «дерево собрано ещё не полностью» */
      ttl=treeReady(r)
         ?'Дерево собрано верно, но на холсте есть лишнее'
         :(k0===0?(wrong>1?'В дереве есть неверные связи':'В дереве есть неверная связь')
                 :(k0===3?'Осталось выбрать источник данных':'Дерево собрано ещё не полностью'));
      sub=cnt;
    }else if(st==='better'){
      ico='&#10003;';
      var k1=a.recs.length?a.recs[0].x.kind:'';
      ttl=(k1==='swap'||k1==='replace')
        ?'Дерево собрано верно, а источники можно выбрать лучше'
        :(k1==='drop'?'Дерево собрано верно, но на холсте есть лишнее'
                     :'Дерево собрано верно, а конфигурацию можно улучшить');
      sub=cnt+' По сроку, стоимости и качеству данных эта конфигурация даёт '+eff+
        ' % от лучшей сборки кейса.';
    }else{
      ico='&#10003;';ttl='Дерево собрано верно, и конфигурация — лучшая в кейсе';
      sub=cnt;
    }
    resP.appendChild(head(ico,ttl,sub));

    /* — следующий шаг: главный элемент разбора — */
    var item=null,nsTitle='Следующий шаг',calm=false;
    if(st==='empty'){
      var f=firstMetric(c),role=f?roleOf(f):null;
      if(f)item={do:['Перенесите на холст метрику '+N(f)+
                     ' — её карточка лежит на левой панели.'],
                 why:['Дерево собирают сверху вниз: сначала показатели, которые '+
                      'собираются напрямую, затем те, что из них рассчитываются'+
                      (role?'. По дереву кейса '+N(f)+' '+role:'')+'.']};
    }else if(st==='build'){
      item=steps.length?steps[0]:{
        do:['Сверьте дерево с цепочкой расчётов ниже.'],
        why:['В ней отмечено, какой расчёт пока не собран и какой метрики ему '+
             'не хватает.']};
    }else if(st==='better'&&a.recs.length){
      item=recStep(a.recs[0],a,r);
    }else if(st==='best'){
      nsTitle='Результат';calm=true;
      item={do:['Вы собрали набор источников, который даёт решение раньше и дешевле '+
               'остальных при том же качестве данных. Тот же вопрос задайте по своему '+
               'подразделению.'],
            why:a?['Решение приходит через ',{b:dn(a.cur.tte)},', владение стоит ',
                   {b:a.cur.tco+' т₽'},' за '+a.cur.H+' мес, качество данных — ',
                   {b:a.cur.q+' из 100'},'. Быстрее и дешевле при таком качестве данных '+
                   'дерево не собирается: любая замена источника либо удлиняет самую '+
                   'длинную ветку, либо снижает качество данных.']
                 :['Быстрее и дешевле при таком качестве данных дерево не собирается.']};
    }
    if(item)resP.appendChild(stepBlock(item,nsTitle,calm));

    /* — то, что уже выбрано верно: короткая похвала за сборку — */
    var oks=(r.qmsgs||[]).filter(function(q){return q.t==='ok'});
    if(r.ok&&oks.length)oks.forEach(function(q){
      resP.appendChild(note('ok',[['Выбрано верно. '+q.m]]));
    });

    /* — остальное: ниже и свёрнутым — */
    if(st==='build'&&steps.length>1){
      var d1=more('Остальные замечания — '+(steps.length-1)+' '+
        plu(steps.length-1,['пункт','пункта','пунктов']));
      steps.slice(1).forEach(function(s){d1.body.appendChild(note('warn',[s.do,s.why]))});
      resP.appendChild(d1);
    }
    if(r.ok&&a&&a.traps.length){
      var d2=more(st==='best'?'Разбор конфигурации':'Почему эта конфигурация не лучшая');
      d2.body.appendChild(note('warn',a.traps));
      resP.appendChild(d2);
    }
    if(r.ok&&a&&a.recs.length>1){
      var d3=more('Что ещё можно улучшить');
      a.recs.slice(1).forEach(function(rc){
        var it=recStep(rc,a,r);d3.body.appendChild(note('warn',[it.do,it.why]));
      });
      resP.appendChild(d3);
    }
    /* экономика показывается там, где она осмысленна: у собранного дерева */
    if(r.ok&&a){
      var d4=more('Что получилось: срок, стоимость и качество данных');
      d4.body.appendChild(note('info',ecoLines(a)));
      resP.appendChild(d4);
    }
    if(c.calc){
      var d5=more('Цепочка расчётов: по каким формулам считается дерево');
      d5.body.appendChild(calcCards(r));
      resP.appendChild(d5);
    }

    if(closeBtn)resP.appendChild(closeBtn);
  };
})();
</script>
"""
swap("</body>", EXTRA_BODY + "</body>", "body extension")

# ── 9. Узкий экран ──
# Исходный конструктор свёрстан под фиксированную ширину: html,body{overflow:hidden}
# и ни одного медиазапроса. На ширине 390 px содержимое шапки (переключатель кейса
# и легенда) уходило за правый край и не прокручивалось — управление было физически
# недостижимо. Правило: до 1024 px шапка и панель кнопок переносятся по строкам,
# рабочее поле остаётся широким, но прокручивается внутри своего контейнера.
# От 1024 px не применяется ничего из этого блока — десктоп остаётся прежним.
NARROW_CSS = """
/* ── A360: узкий экран ───────────────────────────────────────────────────
   До 1024 px управление переносится по строкам, холст прокручивается внутри
   рабочей области. От 1024 px правила ниже не действуют. */
.narrow-note{display:none}
@media (max-width:1023px){
  #app{height:100vh;height:100dvh}
  .header{flex-wrap:wrap;gap:8px 12px;padding:9px 14px}
  .header-brand{flex:1 1 auto;min-width:0}
  .header-title{font-size:15px}
  .case-select{flex:1 1 100%;width:100%;min-width:0}
  .legend{flex:1 1 100%;margin-left:0;flex-wrap:wrap;gap:6px 14px}
  .case-bar{padding:6px 14px 8px}
  /* палитра остаётся 260 px: у́же карточка метрики наезжает на кнопку «?» */
  .workspace{overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch}
  .canvas-wrap{flex:1 0 auto;min-width:600px}
  .toolbar{flex-wrap:wrap;gap:8px;padding:9px 14px}
  .toolbar .spacer{display:none}
  .toolbar .btn{order:1;flex:1 1 auto;padding:8px 12px}
  .toolbar .eco-badge{order:2;flex:1 1 100%;display:block;margin-right:0;
    white-space:normal;line-height:1.5}
  .toolbar-info{order:3;flex:1 1 100%}
  .results{padding:20px 18px;max-height:88vh}
}
@media (max-width:767px){
  .narrow-note{display:flex;align-items:flex-start;gap:9px;flex-shrink:0;
    padding:9px 14px;font-size:12px;line-height:1.45;color:var(--text-sec);
    background:var(--bg-elevated);border-bottom:1px solid rgba(16,40,28,.06);
    border-left:3px solid var(--warn)}
  .narrow-note-i{flex:none;width:16px;height:16px;margin-top:1px;border-radius:50%;
    background:var(--warn);color:#fff;font-size:11px;font-weight:700;line-height:16px;
    text-align:center}
}
"""
swap("</style>", NARROW_CSS + "</style>", "css узкого экрана")

# ── SCORM: статус «пройдено» по факту работы участника ──
# У этой страницы обвязка SCORM своя (const SCORM в исходнике), поэтому
# build/build_scorm.py в неё ничего не внедряет: второй LMSInitialize по
# SCORM 1.2 — ошибка 101. Условие прохождения при этом должно быть общим для
# курса, и берётся оно из того же модуля, что и у остальных страниц.
#
# Путей к статусу два, и оба честные:
#   * дерево собрано правильно — проверка кейса прошла (SCORM.done() в showRes);
#   * участник работал со страницей — общее условие a360Engagement.
# Второй путь нужен потому, что кейсов несколько и разбор ошибок здесь — тоже
# работа: собирать конструктор полчаса и уйти без зачёта из-за одной неверной
# связи участник не должен. Открытие страницы по-прежнему не даёт ничего,
# кроме статуса «начат».
swap("const SCORM={api:null,",
     scorm_engagement.JS.strip() + "\nconst SCORM={api:null,",
     "общее условие вовлечённости перед обвязкой SCORM")
swap("SCORM.init();\nwindow.addEventListener('beforeunload',()=>SCORM.finish());",
     "SCORM.init();\n"
     "SCORM.start=function(){\n"
     "  if(!this.api)return;\n"
     "  try{\n"
     "    var st=this.api.LMSGetValue('cmi.core.lesson_status');\n"
     "    if(st==='completed'||st==='passed')return;   /* зачёт не снимаем */\n"
     "    if(!st||st==='not attempted')"
     "this.api.LMSSetValue('cmi.core.lesson_status','incomplete');\n"
     "    this.api.LMSCommit('');\n"
     "  }catch(e){}\n"
     "  a360Engagement(function(){SCORM.done()});\n"
     "};\n"
     "SCORM.start();\n"
     "window.addEventListener('beforeunload',()=>SCORM.finish());",
     "статус «начат» при открытии и «пройдено» по работе участника")

swap('  <div class="workspace">',
     '  <div class="narrow-note" id="narrowNote">\n'
     '    <span class="narrow-note-i" aria-hidden="true">i</span>\n'
     '    <span>Конструктор дерева рассчитан на работу за компьютером: карточки метрик '
     'переносятся на холст мышью. С телефона доступны условие кейса, справочник метрик '
     'и разбор конфигурации после проверки.</span>\n'
     '  </div>\n'
     '  <div class="workspace">',
     "плашка узкого экрана")


# Ни одного внешнего адреса на странице: в закрытом контуре банка такой запрос
# не дойдёт, а ссылка на публичный сайт выкидывает участника из LMS.
assert "//fonts.googleapis.com" not in t and "//fonts.gstatic.com" not in t
assert "wybaeb.github.io" not in t


def main():
    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(t, encoding="utf-8")
    print(f"  {DST.relative_to(ROOT)}: {DST.stat().st_size // 1024} КБ "
          f"(в корень переносит build_pages.py, зашифровав)")


if __name__ == "__main__":
    main()
