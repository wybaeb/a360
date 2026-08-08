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
