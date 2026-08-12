# -*- coding: utf-8 -*-
"""Проверка теории лонгрида по источникам — единственное место, где живут цитаты.

Отсюда собирается и список источников в конце лонгрида, и отчёт о проверке для
заказчика (build_report.py). Поэтому утверждение в тексте и цитата в отчёте не
могут разойтись: у них общий идентификатор.

Поля записи:
    claim  — утверждение лонгрида ровно в той формулировке, в какой оно проверялось
    quote  — дословная цитата источника (язык оригинала)
    ref    — библиографическая ссылка
    url    — где проверено
    status — «подтверждено» либо «подтверждено с оговоркой» + сама оговорка
"""

CHECKED = "2026-08-08"

SOURCES = [
    dict(
        id="mad",
        claim="Выбросы в коротком ряду ищут не по среднему и стандартному отклонению, "
              "а по медиане и медианному абсолютному отклонению (MAD): модифицированная "
              "z-оценка 0,6745·(x − медиана)/MAD, порог по модулю 3,5.",
        quote="M_i = 0.6745(x_i − x̃)/MAD … Iglewicz and Hoaglin recommend that modified "
              "Z-scores with an absolute value of greater than 3.5 be labeled as potential outliers.",
        ref="NIST/SEMATECH e-Handbook of Statistical Methods, §1.3.5.17 «Detection of Outliers» "
            "(со ссылкой на Iglewicz B., Hoaglin D. «How to Detect and Handle Outliers», ASQC, 1993)",
        url="https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm",
        status="подтверждено",
    ),
    dict(
        id="mad-const",
        claim="Константа 0,6745 в модифицированной z-оценке — это обратная величина к 1,4826, "
              "множителю, который приводит MAD к масштабу стандартного отклонения "
              "для нормального распределения.",
        quote="MAD_n = 1.4826 med{|x_i − med_j x_j|} … 1.4826 = 1/Φ⁻¹(0.75) — множитель "
              "фишеровской состоятельности, приводящий MAD к σ нормального закона.",
        ref="Rousseeuw P. J., Croux C. «Alternatives to the Median Absolute Deviation», "
            "Journal of the American Statistical Association, 1993, 88(424), с. 1273–1283, "
            "DOI 10.1080/01621459.1993.10476408",
        url="https://www.tandfonline.com/doi/abs/10.1080/01621459.1993.10476408",
        status="подтверждено. В лонгриде константа не выводится, а называется — "
               "проверялось только само значение и его смысл",
    ),
    dict(
        id="median",
        claim="Среднее сдвигается редкими экстремальными значениями и асимметрией "
              "распределения, медиана — нет.",
        quote="For skewed distributions, the mean and median are not the same. The mean will "
              "be pulled in the direction of the skewness. … Extreme values in the tails "
              "distort the mean. However, these extreme values do not distort the median since "
              "the median is based on ranks.",
        ref="NIST/SEMATECH e-Handbook of Statistical Methods, §1.3.5.1 «Measures of Location»",
        url="https://www.itl.nist.gov/div898/handbook/eda/section3/eda351.htm",
        status="подтверждено",
    ),
    dict(
        id="percentile",
        claim="Норматив на срок процесса надо задавать по перцентилю, а не по среднему: "
              "среднее прячет хвост, в котором и сидит клиентский опыт.",
        quote="A simple average can obscure these tail latencies, as well as changes in them. … "
              "Using percentiles for indicators allows you to consider the shape of the "
              "distribution and its differing attributes.",
        ref="Beyer B., Jones C., Petoff J., Murphy N. R. «Site Reliability Engineering», "
            "O’Reilly / Google, 2016, гл. 4 «Service Level Objectives»",
        url="https://sre.google/sre-book/service-level-objectives/",
        status="подтверждено. Источник — инженерная практика уровней сервиса; перенос "
               "на срок рассмотрения заявки сделан по аналогии и в лонгриде назван "
               "именно как аналогия",
    ),
    dict(
        id="confounding",
        claim="Совместный рост двух показателей может целиком объясняться третьим, общим для "
              "них фактором; такая связь называется ложной, а сам фактор — конфаундером.",
        quote="Confounding arises when the exposure and the outcome of interest share a common "
              "cause. … A confounder is a variable that is responsible for confounding; "
              "typically, such a variable is a cause of the outcome that is associated with "
              "exposure but not affected by exposure.",
        ref="Statistical Methods in Cancer Research Volume V: Bias Assessment in Case–Control "
            "and Cohort Studies for Hazard Identification (IARC), гл. «Confounding: a routine "
            "concern in the interpretation of epidemiological studies», NCBI Bookshelf",
        url="https://www.ncbi.nlm.nih.gov/books/NBK612871/",
        status="подтверждено. Термин пришёл из эпидемиологии; в лонгриде он применён "
               "к бизнес-показателям и это оговорено",
    ),
    dict(
        id="partial",
        claim="Связь двух показателей при зафиксированном третьем считается частной "
              "корреляцией: r(xy·z) = (r_xy − r_xz·r_yz) / √((1 − r_xz²)(1 − r_yz²)).",
        quote="ρ_xy·z = (ρ_xy − ρ_xz·ρ_yz) / √((1 − ρ_xz²)(1 − ρ_yz²)) … partial correlation "
              "measures the degree of association between two random variables, with the effect "
              "of a set of controlling random variables removed.",
        ref="Wikipedia, «Partial correlation» (формула первого порядка); та же формула "
            "приводится в учебных курсах статистики, например VassarStats, гл. 3a",
        url="https://en.wikipedia.org/wiki/Partial_correlation",
        status="подтверждено с оговоркой: формула стандартная и совпадает во всех проверенных "
               "источниках, но энциклопедическая ссылка — не первоисточник. Числовая "
               "проверка сделана независимо: на нашем датасете формула даёт 0,07, столько "
               "же даёт pingouin.partial_corr",
    ),
    dict(
        id="decomposition",
        claim="Дневной ряд раскладывается на тренд, сезонные профили и остаток; сезонные "
              "профили оцениваются по отношению ряда к скользящему среднему.",
        quote="A classical multiplicative decomposition is similar, except that the subtractions "
              "are replaced by divisions. … To estimate the seasonal component for each season, "
              "simply average the detrended values for that season.",
        ref="Hyndman R. J., Athanasopoulos G. «Forecasting: Principles and Practice» (3rd ed.), "
            "§3.4 «Classical decomposition»",
        url="https://otexts.com/fpp3/classical-decomposition.html",
        status="подтверждено с оговоркой: сами авторы не рекомендуют классическую "
               "декомпозицию для рабочих задач («it is not recommended, as there are now "
               "several much better methods») и предлагают STL. В лонгриде это сказано: "
               "классическая схема показана как объяснение механики, для работы назван STL",
    ),
    dict(
        id="stl",
        claim="Для рабочего снятия сезонности берут STL — он устойчив к выбросам и позволяет "
              "сезонности меняться со временем.",
        quote="STL is a versatile and robust method for decomposing time series. … The seasonal "
              "component is allowed to change over time … It can be robust to outliers … so that "
              "occasional unusual observations will not affect the estimates of the trend-cycle "
              "and seasonal components.",
        ref="Hyndman R. J., Athanasopoulos G. «Forecasting: Principles and Practice» (3rd ed.), "
            "§3.6 «STL decomposition»",
        url="https://otexts.com/fpp3/stl.html",
        status="подтверждено",
    ),
    dict(
        id="base-effect",
        claim="Большой процент прироста при малой базе сравнения не означает большого прироста "
              "по существу; это эффект базы, и официальная статистика отдельно "
              "предупреждает о нём.",
        quote="Beware base effects … the impact of the corresponding «base» or period of the "
              "previous year on current growth estimates … yet the UK economy (under this "
              "hypothetical example) would remain well below pre-pandemic levels.",
        ref="Office for National Statistics (Великобритания), блог национальной статистики, "
            "«Beware base effects», 19.05.2021",
        url="https://blog.ons.gov.uk/2021/05/19/beware-base-effects/",
        status="подтверждено",
    ),
    dict(
        id="giga-files",
        claim="Веб-версия GigaChat принимает вложения только в форматах DOCX, PDF и TXT — "
              "CSV и XLSX к ней приложить нельзя.",
        quote="В GigaChat доступен анализ прикреплённого файла формата DOCX, PDF и TXT.",
        ref="Справка GigaChat, «Работа с документами в GigaChat»",
        url="https://giga.chat/help/articles/work-with-docs",
        status="подтверждено. Это ограничение веба; у API набор форматов шире "
               "(txt, doc, docx, pdf, epub, ppt, pptx, xlsx)",
    ),
    dict(
        id="giga-api-files",
        claim="У GigaChat API список поддерживаемых форматов шире, чем у веб-версии, "
              "и есть ограничение 40 Мб на текстовый файл.",
        quote="Максимальный размер одного текстового файла в запросе — 40 Мб. … "
              "Поддерживаемые форматы текстовых документов: txt, doc, docx, pdf, epub, "
              "ppt, pptx, xlsx.",
        ref="Sber Developers, документация GigaChat API, «Обработка файлов»",
        url="https://developers.sber.ru/docs/ru/gigachat/guides/working-with-files",
        status="подтверждено",
    ),
]

BY_ID = {s["id"]: s for s in SOURCES}
NUM = {s["id"]: i + 1 for i, s in enumerate(SOURCES)}


def ref(sid):
    """Ссылка-сноска в тексте лонгрида."""
    return (f'<a href="#src-{sid}" class="fn">[{NUM[sid]}]</a>')


# ── Лонгрид «Роль данных: категории и критерии ценности» ────────────────────
# Отдельный список с собственной нумерацией: страницы независимые, и сноска
# [2] на каждой из них должна вести на второй пункт её собственного списка.

CHECKED_DATA = "2026-08-11"

SOURCES_DATA = [
    dict(
        id="gost-dq",
        claim="Русские названия характеристик качества данных даются по действующему "
              "национальному стандарту: раздел 6 ГОСТ Р 71484.2-2024 описывает основную "
              "модель из пятнадцати характеристик тремя группами — внутренне присущие "
              "(аккуратность, наполненность, согласованность, достоверность, "
              "актуальность), внутренне присущие и системно-зависимые (доступность, "
              "соответствие, эффективность, точность, прослеживаемость, понятность) "
              "и системно-зависимые (готовность, переносимость, восстанавливаемость); "
              "релевантность и репрезентативность стоят отдельно, в дополнительных "
              "характеристиках качества данных (6.5).",
        quote="Аккуратность — степень, в которой элементы данных имеют корректные значения "
              "данных или корректные метки данных. … Наполненность — степень, в которой "
              "данные имеют значения … для всех предполагаемых атрибутов и экземпляров "
              "сущностей. … Согласованность — … когерентность с другими данными "
              "и отсутствие противоречий. … Актуальность — степень, в которой данные "
              "являются надлежащего возраста относительно использования данных. … "
              "Прослеживаемость — в какой степени данные обладают атрибутами, "
              "позволяющими отслеживать доступ и любые внесённые в них изменения.",
        ref="ГОСТ Р 71484.2-2024 (ИСО/МЭК 5259-2:2024) «Искусственный интеллект. "
            "Качество данных для аналитики и машинного обучения. Часть 2. Показатели "
            "качества данных», раздел 6. Утверждён приказом Росстандарта от 28.10.2024 "
            "№ 1551-ст, введён в действие 01.01.2025",
        url="https://protect.gost.ru/",
        status="подтверждено. Реквизиты и статус документа сверены по реестру "
               "Росстандарта, названия характеристик и определения — по тексту раздела 6. "
               "Оговорки, важные для материалов: конфиденциальность в перечне названа, "
               "но собственного пункта и определения в разделе 6 не имеет — на пункт "
               "мы не ссылаемся; «точность» в стандарте занята под precision (6.3.4), "
               "поэтому привычное «данные корректны» — это аккуратность (6.2.1); "
               "дополнительные характеристики 6.5 в основную модель не подмешиваются "
               "(иначе получилось бы 23 характеристики вместо 15)",
    ),
    dict(
        id="iso25012",
        claim="Первоисточник самой модели — международный стандарт ISO/IEC 25012:2008: "
              "пятнадцать характеристик качества данных, разделённых на внутренне "
              "присущие (inherent) и системно-зависимые.",
        quote="The model defines 15 data quality characteristics … Inherent: Accuracy, "
              "Completeness, Consistency, Credibility, Currentness — quality properties "
              "that can be assessed from the data itself.",
        ref="ISO/IEC 25012:2008 «Data quality model»; проверено по своду "
            "arc42 Quality Model, раздел «ISO/IEC 25012 — Data Quality Model»",
        url="https://quality.arc42.org/standards/iso-iec-25012",
        status="подтверждено с оговоркой: текст самого стандарта платный, состав "
               "характеристик проверен по независимому своду. Отдельная оговорка "
               "о названии: документа «ГОСТ Р ИСО/МЭК 25012» не существует — в реестре "
               "Росстандарта его нет, официального русского текста у ISO/IEC 25012 тоже "
               "нет, поэтому русские названия характеристик от него взяться не могут. "
               "В материалах ISO/IEC 25012 называется только как первоисточник модели, "
               "а термины даются по ГОСТ Р 71484.2-2024, раздел 6",
    ),
    dict(
        id="moe",
        claim="При 95-процентном уровне доверия погрешность оценки доли составляет "
              "примерно 0,98/√n: около 400 наблюдений дают ±5 %, около 1 100 — ±3 %.",
        quote="MOE₉₅(0.5) = z₀.₉₅ σₚ̄ ≈ z₀.₉₅ √(σ²ₚ/n) = 1.96 √(.25/n) = 0.98/√n",
        ref="Wikipedia, «Margin of error» (формула максимальной погрешности доли "
            "при p = 0,5)",
        url="https://en.wikipedia.org/wiki/Margin_of_error",
        status="подтверждено с оговоркой: энциклопедическая ссылка — не первоисточник, "
               "но формула стандартная и сверена расчётом: 0,98/√400 = 4,9 %, "
               "0,98/√1067 = 3,0 %. Ориентиры лонгрида «около 400 → ±5 %, "
               "около 1 100 → ±3 %» совпадают с расчётом",
    ),
    dict(
        id="leading-lagging",
        claim="Метрики результата — запаздывающие индикаторы, драйверы — опережающие; "
              "рабочая система показателей требует и тех и других: без результатов "
              "не видно, достигнута ли цель, без драйверов — работает ли способ "
              "её достижения.",
        quote="Performance drivers (leading indicators) and outcomes (lagging indicators). "
              "… An effective balanced scorecard needs a combination of both performance "
              "drivers and outcome measures. Without outcome measures such as "
              "profitability, market share, or customer satisfaction, among others, "
              "a scorecard does not provide an indication of how well the organization "
              "is performing. Without performance drivers … you don't have an indication "
              "of whether your strategy is working.",
        ref="Kaplan R. S., Norton D. P. «The Balanced Scorecard: Translating Strategy "
            "into Action», HBS Press, 1996; цитируется по изложению теории в документации "
            "Oracle PeopleSoft Scorecard, раздел «Balanced Scorecard Theory»",
        url="https://docs.oracle.com/cd/E41507_01/epm91pbr3/eng/epm/pbsc/task_BalancedScorecardTheory-991810.html",
        status="подтверждено с оговоркой: проверка сделана по вторичному источнику — "
               "вендорской документации, прямо ссылающейся на книгу Каплана и Нортона; "
               "первоисточник платный. Управленческое правило «план по запаздывающим, "
               "управление по опережающим» — авторская формулировка программы, "
               "источнику не приписывается",
    ),
    dict(
        id="ssot",
        claim="Единый источник правды — практика, при которой каждый элемент данных "
              "ведётся (mastered) ровно в одном месте; она защищает от расхождения копий.",
        quote="Single source of truth (SSOT) architecture … is the practice of structuring "
              "information models and associated data schemas such that every data element "
              "is mastered (or edited) in only one place … easier prevention of mistaken "
              "inconsistencies (such as a duplicate value/copy somewhere being forgotten).",
        ref="Wikipedia, «Single source of truth»",
        url="https://en.wikipedia.org/wiki/Single_source_of_truth",
        status="подтверждено с оговоркой: энциклопедическая ссылка — не первоисточник. "
               "В лонгриде термин применён к управленческой договорённости о master-source "
               "(а не к архитектуре систем), и это в тексте оговорено",
    ),
]

BY_ID_DATA = {s["id"]: s for s in SOURCES_DATA}
NUM_DATA = {s["id"]: i + 1 for i, s in enumerate(SOURCES_DATA)}


def ref_data(sid):
    """Сноска для лонгрида «Роль данных» — нумерация его собственного списка."""
    return (f'<a href="#src-{sid}" class="fn">[{NUM_DATA[sid]}]</a>')


# ── Лонгрид-справочник «Метрики и качество данных» ──────────────────────────
# Собственная нумерация; стандарт качества данных (ГОСТ и его международный
# первоисточник) и опережающие/запаздывающие переиспользуются из списка
# «Роль данных» — те же записи, чтобы цитата и статус не разошлись.

CHECKED_METRICS = "2026-08-11"

SOURCES_METRICS = [
    dict(
        id="cod",
        claim="Стоимость задержки (Cost of Delay) — денежное выражение влияния времени "
              "на результат; Райнертсен называет её главной величиной, которую стоит "
              "квантифицировать в разработке продукта.",
        quote="A way of communicating the impact of time on the outcomes we hope to achieve. … "
              "If you only quantify one thing, quantify the Cost of Delay.",
        ref="Reinertsen D. «The Principles of Product Development Flow», Celeritas, 2009; "
            "Wikipedia, «Cost of delay»",
        url="https://en.wikipedia.org/wiki/Cost_of_delay",
        status="подтверждено",
    ),
    dict(
        id="wsjf",
        claim="Варианты сравниваются по стоимости задержки, делённой на длительность: "
              "CD3 (Cost of Delay Divided by Duration), в SAFe тот же принцип называется WSJF.",
        quote="WSJF is estimated as the relative cost of delay divided by the relative "
              "job duration.",
        ref="Scaled Agile Framework, «WSJF — Weighted Shortest Job First»",
        url="https://framework.scaledagile.com/wsjf",
        status="подтверждено",
    ),
    dict(
        id="gartner-dq",
        claim="Плохое качество данных стоит организации в среднем 12,9 млн долларов в год "
              "(оценка Gartner).",
        quote="Every year, poor data quality costs organizations an average $12.9 million.",
        ref="Gartner, «How to Improve Your Data Quality», Smarter with Gartner, 14.07.2021",
        url="https://www.gartner.com/smarterwithgartner/how-to-improve-your-data-quality",
        status="подтверждено",
    ),
]

SOURCES_METRICS = SOURCES_METRICS + [BY_ID_DATA["gost-dq"], BY_ID_DATA["iso25012"],
                                     BY_ID_DATA["leading-lagging"]]

BY_ID_METRICS = {s["id"]: s for s in SOURCES_METRICS}
NUM_METRICS = {s["id"]: i + 1 for i, s in enumerate(SOURCES_METRICS)}


def ref_metrics(sid):
    """Сноска для справочника метрик — нумерация его собственного списка."""
    return (f'<a href="#src-{sid}" class="fn">[{NUM_METRICS[sid]}]</a>')


# ── Лонгрид «Инструменты анализа» (предчтение к Шагу 2) ─────────────────────

CHECKED_TOOLS = "2026-08-11"

SOURCES_TOOLS = [
    dict(
        id="eda",
        claim="Разведочный анализ данных (EDA) — подход к анализу, использующий "
              "преимущественно графические техники, чтобы максимально раскрыть "
              "структуру набора данных до построения моделей.",
        quote="Exploratory Data Analysis (EDA) is an approach/philosophy for data "
              "analysis that employs a variety of techniques (mostly graphical) to "
              "maximize insight into a data set.",
        ref="NIST/SEMATECH e-Handbook of Statistical Methods, §1.1.1 «What is EDA?»",
        url="https://www.itl.nist.gov/div898/handbook/eda/section1/eda11.htm",
        status="подтверждено",
    ),
    dict(
        id="histogram",
        claim="Гистограмма — базовый инструмент: она графически сводит распределение "
              "одномерного набора данных и показывает форму, которую среднее прячет.",
        quote="The purpose of a histogram is to graphically summarize the distribution "
              "of a univariate data set.",
        ref="NIST/SEMATECH e-Handbook of Statistical Methods, §1.3.3.14 «Histogram»",
        url="https://www.itl.nist.gov/div898/handbook/eda/section3/histogra.htm",
        status="подтверждено",
    ),
    dict(
        id="pandas",
        claim="Pandas — открытая библиотека анализа и обработки данных для Python, "
              "стандарт де-факто для табличных данных.",
        quote="pandas is a fast, powerful, flexible and easy to use open source data "
              "analysis and manipulation tool, built on top of the Python programming "
              "language.",
        ref="pandas.pydata.org — официальный сайт проекта",
        url="https://pandas.pydata.org/",
        status="подтверждено",
    ),
]

SOURCES_TOOLS = SOURCES_TOOLS + [BY_ID["median"], BY_ID["percentile"]]

BY_ID_TOOLS = {s["id"]: s for s in SOURCES_TOOLS}
NUM_TOOLS = {s["id"]: i + 1 for i, s in enumerate(SOURCES_TOOLS)}


def ref_tools(sid):
    """Сноска для лонгрида «Инструменты анализа»."""
    return (f'<a href="#src-{sid}" class="fn">[{NUM_TOOLS[sid]}]</a>')
