# -*- coding: utf-8 -*-
"""Тренажёр практического занятия «Проект по варианту» (a360/trainer_practice.html).

Участник выбирает вариант (три направления × три варианта), получает каркас
проекта, собирает конфигурацию дерева метрик — по одному источнику на каждый
вход с оценкой скорости, цены и интегрального качества, — скачивает файлы
выбранных источников, получает промпт на мини-инструмент расчёта параметров
(несколько CSV на вход), затем промпт на мини-инструмент финансовой модели
(NPV, окупаемость, SVG), загружает SVG обратно и получает презентацию проекта
с кнопкой «Скачать HTML».

Ядро (промпты, экономика конфигурации, финмодель) — build/src/practice_core.js;
варианты и файлы — build/practice_variants.py → build/src/practice_variants.json
и practice_data/<вариант>/*.csv (копируются в scorm/content и остаются в корне
как открытые данные). Подключение: build_pages.py, PAGES → trainer_practice.BODY.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
CORE = (HERE / "src" / "practice_core.js").read_text(encoding="utf-8")
VARIANTS = json.loads((HERE / "src" / "practice_variants.json").read_text(encoding="utf-8"))
TOOL_TPL = (HERE / "src" / "practice_tool_template.html").read_text(encoding="utf-8")
FIN_TPL = (HERE / "src" / "practice_fin_template.html").read_text(encoding="utf-8")


def _samples():
    """Первые четыре строки каждого файла — для примеров в промпте."""
    out = {}
    for v in VARIANTS:
        for inp in v["inputs"]:
            for s in inp["sources"]:
                txt = (ROOT / "practice_data" / v["id"] / s["file"]).read_text(encoding="utf-8")
                out[v["id"] + "/" + s["file"]] = "\n".join(txt.splitlines()[:4]) + "\n"
    return out


CSS = """
<style>
.pr .dirs{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 10px}
.pr .dirs button,.pr .vars button{background:var(--surf);border:1px solid var(--line);border-radius:10px;
  padding:8px 14px;font:inherit;font-size:15px;color:var(--ink);cursor:pointer}
.pr .dirs button.on,.pr .vars button.on{background:var(--acc);border-color:var(--acc);color:#fff;font-weight:700}
.pr .vars{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}
.pr .stepper{display:flex;flex-wrap:wrap;gap:6px;margin:18px 0 22px}
.pr .stepper button{flex:1 1 120px;background:var(--surf);border:1px solid var(--line);border-radius:10px;
  padding:7px 8px;font:inherit;font-size:13px;color:var(--ink2);cursor:pointer;text-align:left;line-height:1.25}
.pr .stepper button b{display:block;font-size:12px;color:var(--ink3)}
.pr .stepper button.ok{border-color:var(--acc-line);background:var(--acc-soft);color:var(--ink)}
.pr .stepper button.ok b{color:#128a53}
.pr .stepper button.cur{border-color:var(--acc);box-shadow:inset 0 0 0 1px var(--acc);color:var(--ink)}
.pr .step{display:none}.pr .step.on{display:block}
.pr .sthead{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin:0 0 4px}
.pr .sthead h3{margin:0;font-size:22px}
.pr .snum{color:var(--acc);font-weight:800;font-size:13px;letter-spacing:.1em;text-transform:uppercase}
.pr .part{border:1px solid var(--line);border-radius:14px;padding:14px 18px;margin:0 0 12px;background:#fff}
.pr .part h4{margin:0 0 8px;color:var(--ink);font-size:15px}
.pr .part h4 .n{display:inline-block;width:22px;height:22px;border-radius:50%;background:var(--acc);color:#fff;
  text-align:center;line-height:22px;font-size:12.5px;margin-right:8px}
.pr .links{font-size:14px;color:var(--ink3);margin:0 0 12px}.pr .links a{margin-right:10px;white-space:nowrap}
.pr .hint{font-size:13.5px;color:var(--ink3);margin:0 0 8px}
.pr .grid{display:grid;grid-template-columns:1fr 1fr;gap:10px 18px}
@media(max-width:720px){.pr .grid{grid-template-columns:1fr}}
.pr .fld{margin:0 0 8px}.pr .fld label{display:block;font-size:13px;color:var(--ink3);margin:0 0 3px}
.pr .fld input,.pr .fld textarea{width:100%;box-sizing:border-box;font:inherit;font-size:15px;padding:7px 10px;
  border:1px solid var(--line);border-radius:8px;background:#fff;color:var(--ink)}
.pr .fld textarea{min-height:56px;resize:vertical;line-height:1.45}
.pr .btn{border:0;border-radius:9px;background:var(--acc);color:#fff;padding:8px 16px;cursor:pointer;font:inherit;font-size:14.5px;font-weight:700}
.pr .btn.sec{background:var(--surf);color:var(--ink);border:1px solid var(--line);font-weight:600}
.pr .nav{display:flex;justify-content:space-between;gap:10px;margin:6px 0 0}
.pr .msg{font-size:13.5px;color:var(--ink3);margin:8px 0 0}.pr .msg.ok{color:#128a53;font-weight:600}.pr .msg.warn{color:var(--warn);font-weight:600}
.pr .frame{display:grid;grid-template-columns:150px 1fr;gap:10px 16px;font-size:15.5px;line-height:1.5}
.pr .frame dt{font-weight:800;color:var(--acc);font-size:12.5px;text-transform:uppercase;letter-spacing:.05em;padding-top:3px}
.pr .frame dd{margin:0;padding-bottom:8px;border-bottom:1px solid var(--line)}
.pr .frame dd:last-child{border-bottom:0}
.pr .phv{background:rgba(32,186,114,.18);color:#8ee7b8;border-radius:3px;padding:0 2px}
.pr .frame textarea{width:100%;box-sizing:border-box;font:inherit;font-size:14.5px;padding:6px 9px;border:1px solid var(--line);border-radius:8px;min-height:44px;resize:vertical;line-height:1.4}
.pr .src{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:6px 0 14px}
@media(max-width:720px){.pr .src{grid-template-columns:1fr}}
.pr .src label{display:block;border:1.5px solid var(--line);border-radius:12px;padding:10px 12px;cursor:pointer;background:#fff;font-size:14px}
.pr .src label.on{border-color:var(--acc);background:var(--acc-soft)}
.pr .src label b{display:block;font-size:14.5px;margin:0 0 3px}
.pr .src .meta{font-size:12.5px;color:var(--ink3)}
.pr .src input{margin-right:6px}
.pr .kpi{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:10px 0}
@media(max-width:720px){.pr .kpi{grid-template-columns:1fr}}
.pr .kpi>div{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 12px}
.pr .kpi .l{font-size:12.5px;color:var(--ink3)}.pr .kpi .v{font-size:22px;font-weight:800;margin-top:3px}.pr .kpi .s{font-size:12.5px;color:var(--ink3);margin-top:2px}
.pr .vis{background:var(--surf);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:10px 0 0}
.pr .vis svg{width:100%;height:auto;display:block}
.pr .files a.f{display:inline-block;margin:0 10px 8px 0;padding:7px 12px;border:1px solid var(--acc-line);border-radius:999px;background:var(--acc-soft);font-size:14px;border-bottom-width:1px}
.pr .pctl{border:1px solid var(--line);border-radius:12px;overflow:hidden;margin:6px 0 6px;background:#20262e}
.pr .pctl-head{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;padding:8px 10px;background:#20262e}
.pr .b-cp{border:0;border-radius:8px;background:var(--acc);color:#fff;padding:7px 14px;cursor:pointer;font:inherit;font-size:13.5px}
.pr .b-cp.done{background:#0f7a46}
.pr .pctl pre{margin:0;padding:14px 16px;background:#20262e;color:#e7edf3;border-radius:0;font:13px/1.65 var(--mono);white-space:pre-wrap;word-break:break-word;max-height:380px;overflow:auto}
.pr .pstate{font-size:12.5px;color:#aeb9c6;padding:8px 16px 10px;background:#20262e;margin:0;border-top:1px solid #313a46}
.pr .ctrl{font-size:14px;background:var(--surf);border:1px dashed var(--line);border-radius:10px;padding:8px 12px;margin:8px 0 0}
.pr .slides{background:#20262e;border-radius:14px;padding:14px}
.pr .slide{aspect-ratio:16/9;background:#fff;border-radius:8px;padding:4% 5%;display:flex;flex-direction:column;gap:2%;overflow:hidden;color:#2E3641}
.pr .slide .h{font-size:clamp(15px,2.4vw,24px);font-weight:800;line-height:1.15;border-bottom:3px solid #20BA72;padding-bottom:1.5%}
.pr .slide .b{font-size:clamp(11px,1.45vw,15px);line-height:1.4;overflow:hidden}
.pr .slide .b p{margin:0 0 .6em}
.pr .slide .b table{font-size:.95em}
.pr .slide svg{max-height:60%;width:auto;max-width:100%;margin:0 auto}
.pr .slnav{display:flex;justify-content:space-between;align-items:center;gap:10px;margin:10px 0 0;color:#aeb9c6;font-size:13.5px}
.pr .slnav button{border:0;border-radius:8px;background:#3a4453;color:#fff;padding:6px 14px;cursor:pointer;font:inherit}
.pr .svgbox svg{max-width:100%;height:auto}
.pr table.sm{font-size:14px}.pr table.sm td{white-space:normal}
.pr #tree [data-pick],.pr #tree [data-info]{cursor:pointer}
.pr #tree [data-pick]:hover rect{filter:brightness(0.97)}
.pr .modal{position:fixed;inset:0;background:rgba(46,54,65,.45);display:none;align-items:center;justify-content:center;z-index:50;padding:20px}
.pr .modal.on{display:flex}
.pr .mbox{background:#fff;border-radius:16px;max-width:760px;width:100%;max-height:88vh;overflow:auto;padding:22px 26px;position:relative;box-shadow:0 20px 60px rgba(0,0,0,.25)}
.pr .mbox h3{margin:0 40px 6px 0;font-size:20px}
.pr .mbox .meta{color:var(--ink3);font-size:13.5px;margin:0 0 12px}
.pr .mclose{position:absolute;top:12px;right:12px;border:0;background:var(--surf);border-radius:50%;width:34px;height:34px;font-size:20px;cursor:pointer;color:var(--ink2)}
.pr .mbox table{font-size:13.5px;margin:6px 0 10px}.pr .mbox td,.pr .mbox th{white-space:nowrap;padding:5px 9px}
.pr .mbox .calc{background:var(--surf);border-radius:10px;padding:8px 12px;font-size:14px;margin:0 0 10px}
</style>
"""


def _пром(n):
    return (f'<div class="pctl"><div class="pctl-head"><span style="color:#aeb9c6;font-size:13px">Промпт собран из вашей конфигурации; зелёным — подставленные значения</span>'
            f'<button class="b-cp" type="button" data-copy="{n}">Копировать промпт</button></div>'
            f'<pre id="pv{n}"></pre><p class="pstate" id="ps{n}"></p></div>')


def _нав(n, последний=False):
    prev = f'<button class="btn sec" type="button" data-go="{n-1}">← Шаг {n-1}</button>' if n > 1 else '<span></span>'
    nxt = (f'<button class="btn" type="button" data-go="{n+1}">Дальше: шаг {n+1} →</button>' if not последний
           else '<button class="btn" type="button" id="bDownload">Скачать презентацию (HTML)</button>')
    return f'<div class="nav">{prev}{nxt}</div>'


HTML = f"""
<header><div class="wrap">
  <div class="eyebrow">Практическое занятие</div>
  <h1>Проект по варианту: от каркаса до презентации</h1>
  <p class="lead">Работа по вариантам: направления — продукт, процесс, бизнес-инициатива.
     По варианту: описание проекта по каркасу, конфигурация дерева метрик с оценкой срока и стоимости
     данных, мини-инструмент расчёта параметров на выгрузках, мини-инструмент финансовой модели
     с графиком, заключение и презентация проекта. Оба инструмента создаёт ассистент по промптам
     из тренажёра.</p>
  <div class="meta">
    <span class="chip">Нужен: <b>ассистент в браузере</b></span>
    <span class="chip">Итог: <b>презентация проекта одним файлом</b></span>
  </div>
</div></header>

<section><div class="wrap pr">
<div class="card acc">
<h4>Как проходить</h4>
<ol style="margin:0;padding-left:22px">
<li><b>Выберите вариант</b> — направление и номер. Каркас проекта по варианту заполнен, его можно уточнить.</li>
<li><b>Соберите конфигурацию</b> дерева: для каждого входа итоговой метрики выберите источник данных.
    Страница показывает срок первого значения, стоимость и интегральную оценку конфигурации.</li>
<li><b>Скачайте файлы</b> выбранных источников и скопируйте промпт. Ассистент возвращает код HTML-файла: сохраните его
    через Блокнот с расширением .html, откройте в браузере и перетащите в него файлы — инструмент посчитает входы
    и параметры проекта. Контрольные значения для проверки — в тренажёре.</li>
<li><b>Финансовая модель:</b> второй промпт с параметрами — ассистент возвращает код второго инструмента; сохраните,
    откройте: окупаемость, NPV, график SVG с кнопкой сохранения. Загрузите SVG сюда.</li>
<li><b>Заключение</b> пишет ассистент по результатам; <b>презентация</b> собирается из всего сделанного
    и скачивается одним HTML-файлом.</li>
</ol>
<p class="sub" style="margin:10px 0 0">Введённое сохраняется в браузере отдельно для каждого варианта. Как сохранить ответ ассистента файлом
и открыть его — в материале <a href="guide_mini.html">«Мини-инструменты»</a>. Если инструмент не собрался с первого раза,
сообщение об ошибке из браузера отправляется ассистенту; контрольные значения в тренажёре позволяют идти дальше.</p>
</div>

<h3>Вариант</h3>
<div class="dirs" id="dirs"></div>
<div class="vars" id="vars"></div>
<p class="hint" id="varNote"></p>

<div class="stepper" id="stepper"></div>

<!-- ─── Шаг 1 ─────────────────────────────────────────────────────────── -->
<div class="step" id="st1">
<div class="sthead"><span class="snum">Шаг 1</span><h3>Каркас проекта</h3></div>
<p class="sub">Семь элементов каркаса: проблема → метрика → данные → инструмент → анализ → вывод → эффект,
и изменение, которое проверяет проект. Это условие варианта: прочитайте его, чтобы понимать задачу, над которой идёт работа
на следующих шагах.</p>
<p class="links" id="links1">Из курса: <a href="longread_project.html">Каркас проекта</a>
<a href="longread_project.html#problema">Формулировка проблемы</a></p>
<div class="part"><h4><span class="n">1</span>Описание проекта по каркасу</h4>
<dl class="frame" id="frame"></dl>
</div>
{_нав(1)}
</div>

<!-- ─── Шаг 2 ─────────────────────────────────────────────────────────── -->
<div class="step" id="st2">
<div class="sthead"><span class="snum">Шаг 2</span><h3>Дерево метрик и конфигурация источников</h3></div>
<p class="sub">Итоговая метрика эффекта считается из входов; каждый вход можно получить из двух источников
с разной скоростью и ценой. Срок первого значения метрики определяется самым медленным входом,
стоимость складывается, интегральная оценка учитывает и то, и другое.</p>
<p class="links">Из курса: <a href="trainer_tree.html">Тренажёр «Дерево метрик»</a>
<a href="longread_metrics.html#eco">Экономика данных: срок и стоимость</a>
<a href="longread_metrics.html#tree">Опережающие и запаздывающие</a>
<a href="trainer_map.html">Карта источников</a></p>
<div class="part"><h4><span class="n">1</span>Дерево: щелчок по источнику выбирает его, значок «?» открывает описание</h4><div class="vis" id="tree"></div>
<p class="hint" style="margin:8px 0 0">Сплошная рамка — выбранный источник, пунктир — запасной. В описании источника: срок, стоимость, файл, расчёт входа и структура данных.</p></div>
<div class="part"><h4><span class="n">2</span>Оценка конфигурации</h4>
<div class="kpi">
<div><div class="l">Срок первого значения метрики</div><div class="v" id="k-tte"></div><div class="s" id="k-tte-s"></div></div>
<div><div class="l">Стоимость данных за пилот</div><div class="v" id="k-cost"></div><div class="s" id="k-cost-s"></div></div>
<div><div class="l">Интегральная оценка</div><div class="v" id="k-score"></div><div class="s" id="k-score-s"></div></div>
</div>
<p class="hint" id="ecoNote"></p>
</div>
{_нав(2)}
</div>

<!-- ─── Шаг 3 ─────────────────────────────────────────────────────────── -->
<div class="step" id="st3">
<div class="sthead"><span class="snum">Шаг 3</span><h3>Мини-инструмент расчёта параметров</h3></div>
<p class="sub">Мини-инструмент создаёт ассистент по промпту ниже: HTML-файл, который принимает несколько CSV
перетаскиванием, считает входы дерева по формулам и три параметра финансовой модели, рисует график. Промпт собран
из вашей конфигурации; тот же промпт с другими файлами и формулами даёт другой инструмент. Расчёт выполняется
в браузере, данные никуда не отправляются.</p>
<p class="links">Из курса: <a href="guide_mini.html">Мини-инструменты: как создать и открыть</a>
<a href="case_report.html">Мини-инструменты корреляций и трендов</a></p>
<div class="part"><h4><span class="n">1</span>Скачайте файлы выбранных источников</h4>
<p class="hint">Имена файлов должны остаться такими же: инструмент распознаёт файл по имени.</p>
<div class="files" id="files"></div>
</div>
<div class="part"><h4><span class="n">2</span>Промпт на мини-инструмент</h4>{_пром(3)}
<p class="hint" style="margin-top:8px">Вставьте промпт в новый чат ассистента. Ответ — код HTML-файла.</p></div>
<div class="part"><h4><span class="n">3</span>Сохраните и откройте инструмент</h4>
<ol style="margin:0 0 6px;padding-left:22px;font-size:15px">
<li>Скопируйте ответ ассистента целиком, откройте Блокнот, вставьте, сохраните как <b>инструмент.html</b>
(тип файла «Все файлы», кодировка UTF-8).</li>
<li>Откройте сохранённый файл двойным щелчком — он откроется в браузере.</li>
<li>Перетащите в него скачанные CSV-файлы или выберите их по ссылке в окне инструмента.</li>
<li>Инструмент покажет входы, три параметра, итоговую метрику и график. Строку параметров скопируйте в поле ниже.</li>
</ol>
<p class="hint">Если браузер показал ошибку или инструмент ничего не посчитал — скопируйте текст ошибки ассистенту с просьбой исправить
и вернуть файл целиком. Подробнее: <a href="guide_mini.html">«Мини-инструменты: как создать и открыть»</a>.</p>
<p class="hint">Не получилось с двух попыток — <button class="btn sec" type="button" id="bToolRef">скачать запасной инструмент</button>,
собранный по этому же промпту: он считает то же самое, и занятие продолжается.</p>
</div>
<div class="part"><h4><span class="n">4</span>Параметры из инструмента</h4>
<p class="hint">Скопируйте строку параметров из инструмента и вставьте сюда — или впишите числа вручную.</p>
<div class="fld"><label>Строка параметров</label><input data-bind="paramsLine" placeholder="delta=…; volume=…; price=…"></div>
<div class="grid">
<div class="fld"><label id="l-delta">Изменение показателя</label><input data-bind="delta"></div>
<div class="fld"><label id="l-volume">Объём</label><input data-bind="volume"></div>
<div class="fld"><label id="l-price">Стоимость единицы</label><input data-bind="price"></div>
</div>
<div class="ctrl" id="ctrl3"></div>
</div>
{_нав(3)}
</div>

<!-- ─── Шаг 4 ─────────────────────────────────────────────────────────── -->
<div class="step" id="st4">
<div class="sthead"><span class="snum">Шаг 4</span><h3>Мини-инструмент финансовой модели</h3></div>
<p class="sub">Второй мини-инструмент создаёт ассистент по промпту с параметрами и условиями: поля, поток эффекта по месяцам,
окупаемость, NPV, таблица и график SVG с кнопкой сохранения. Формулы потока — те же, что в материале «Финансовая модель проекта».</p>
<details class="more"><summary>Как считается финансовая модель</summary>
<p><b>Эффект в месяц</b> = изменение показателя × объём × стоимость единицы. Изменение показателя берётся
из гипотезы проекта, объём — из данных, стоимость единицы — из финансовой модели продукта. Всё, что не подтверждено
данными, — допущение.</p>
<p><b>Поток по месяцам.</b> Эффект выходит на полный уровень за несколько месяцев и сохраняется заданный срок.
Для когорт единицы эффекта появляются каждый месяц и приносят доход, пока сохраняются; для уровня эффект действует
как постоянный поток. Из дохода месяца вычитаются ежемесячные затраты; в нулевом месяце — единовременные затраты,
включая стоимость сбора данных.</p>
<p><b>Окупаемость</b> — первый месяц, в котором накопленный поток становится неотрицательным.
<b>NPV</b> — сумма потоков, приведённых к сегодняшнему дню по ставке дисконтирования: месячная ставка
равна (1 + годовая)<sup>1/12</sup> − 1, поток месяца t делится на (1 + месячная)<sup>t</sup>. Проект принимается,
если NPV за горизонт положителен, а окупаемость укладывается в срок сохранения эффекта.</p>
<p><b>Доход за первый год</b> — сумма дохода за первые двенадцать месяцев без вычета затрат.</p>
</details>
<div class="part"><h4><span class="n">1</span>Что получено на предыдущих шагах</h4>
<div id="from34"></div>
</div>
<div class="part"><h4><span class="n">2</span>Условия финансовой модели</h4>
<div class="grid">
<div class="fld"><label>Стоимость сбора данных за пилот, руб. (из шага 2, входит в единовременные затраты)</label><input data-bind="fin.datacost"></div>
<div class="fld"><label>Единовременные затраты на изменение, руб.</label><input data-bind="fin.capex"></div>
<div class="fld"><label>Выход на полный уровень, мес.</label><input data-bind="fin.ramp"></div>
<div class="fld"><label>Срок сохранения эффекта, мес.</label><input data-bind="fin.keep"></div>
<div class="fld"><label>Ежемесячные затраты, руб.</label><input data-bind="fin.opex"></div>
<div class="fld"><label>Горизонт, мес.</label><input data-bind="fin.horizon"></div>
<div class="fld"><label>Ставка дисконтирования, доля в год</label><input data-bind="fin.rate"></div>
</div>
</div>
<div class="part"><h4><span class="n">3</span>Промпт на инструмент финансовой модели</h4>{_пром(4)}</div>
<div class="part"><h4><span class="n">4</span>Сохраните и откройте инструмент</h4>
<p style="margin:0 0 6px;font-size:15px">Ответ ассистента сохраните через Блокнот как <b>финмодель.html</b> и откройте. Параметры шага 3
и условия уже подставлены; при необходимости измените их и нажмите «Рассчитать». Кнопка «Сохранить SVG» сохраняет график
файлом npv.svg — загрузите его ниже.</p>
<p class="hint">Не получилось с двух попыток — <button class="btn sec" type="button" id="bFinRef">скачать запасной инструмент</button>,
собранный по этому же промпту.</p>
</div>
<div class="part"><h4><span class="n">5</span>Результат инструмента</h4>
<div class="grid">
<div class="fld"><label>Окупаемость, месяц</label><input data-bind="res.payback"></div>
<div class="fld"><label>NPV за горизонт, руб.</label><input data-bind="res.npv"></div>
<div class="fld"><label>Доход за первый год, руб.</label><input data-bind="res.year1"></div>
</div>
<div class="ctrl" id="ctrl4"></div>
<div class="fld" style="margin-top:10px"><label>График из инструмента (файл .svg, сохранённый кнопкой «Сохранить SVG»)</label>
<input type="file" id="svgFile" accept=".svg,image/svg+xml"></div>
<div class="svgbox" id="svgBox"></div>
</div>
{_нав(4)}
</div>

<!-- ─── Шаг 5 ─────────────────────────────────────────────────────────── -->
<div class="step" id="st5">
<div class="sthead"><span class="snum">Шаг 5</span><h3>Заключение и презентация проекта</h3></div>
<p class="sub">Заключение по проекту пишет ассистент по всем результатам: конфигурация источников, параметры из инструмента,
финансовая модель. Затем слайды по структуре презентации проекта: проблема и метрики, дерево и данные,
параметры, финансовая модель с графиком, заключение. Слайды листаются здесь и скачиваются одним HTML-файлом.</p>
<p class="links">Из курса: <a href="longread_project.html#prezentaciya">Структура презентации проекта</a></p>
<div class="part"><h4><span class="n">1</span>Промпт на заключение</h4>{_пром(5)}
<p class="hint" style="margin-top:8px">Промпт содержит все результаты шагов 2–4. Ответ ассистента вставьте ниже.</p></div>
<div class="part"><h4><span class="n">2</span>Ответ ассистента</h4>
<textarea class="fld" data-bind="concl" style="width:100%;min-height:110px;font:inherit;font-size:14.5px;padding:9px 11px;border:1px solid var(--line);border-radius:10px" placeholder="Вставьте ответ целиком"></textarea>
<div style="margin-top:8px"><button class="btn" type="button" id="bConcl">Разобрать ответ</button><span class="msg" id="conclMsg" style="display:inline-block;margin:0 0 0 12px"></span></div>
<div class="grid" style="margin-top:10px">
<div class="fld"><label>Вывод</label><textarea data-bind="c.conclusion"></textarea></div>
<div class="fld"><label>Эффект для бизнеса</label><textarea data-bind="c.effect"></textarea></div>
<div class="fld"><label>Первое действие</label><textarea data-bind="c.action"></textarea></div>
<div class="fld"><label>Когда пересматриваем</label><textarea data-bind="c.review"></textarea></div>
</div>
</div>
<div class="part"><h4><span class="n">3</span>Слайды презентации</h4>
<div class="slides"><div class="slide" id="slide"></div>
<div class="slnav"><button type="button" id="slPrev">← Назад</button><span id="slPos"></span><button type="button" id="slNext">Вперёд →</button></div></div>
<p class="msg" id="dlMsg"></p>
</div>
{_нав(5, True)}
</div>

<div class="modal" id="modal"><div class="mbox"><button class="mclose" type="button" id="mclose" aria-label="Закрыть">×</button><div id="mbody"></div></div></div>
</div></section>

<footer><div class="wrap">
  Аналитика 360 · материалы практической части. Выгрузки вариантов синтетические. Расчёты и файлы
  остаются в вашем браузере.
</div></footer>
"""

UI = r"""
<script>
(function(){
var C=window.PracticeCore, VARS=__VARIANTS__, SAMPLES=__SAMPLES__, TOOL_TPL=__TOOL_TPL__, FIN_TPL=__FIN_TPL__;
var $=function(id){return document.getElementById(id)};
var esc=function(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')};
var DIRS=['продукт','процесс','бизнес-инициатива'];
var FRAME=[['problem','Проблема'],['metric','Метрика'],['data','Данные'],['tool','Инструмент'],['analysis','Анализ'],['conclusion','Вывод'],['effect','Эффект']];
var STEPS=['Каркас проекта','Дерево и источники','Мини-инструмент параметров','Финансовая модель','Презентация'];
var cur=null, st=null, dir=DIRS[0], ptext={}, slideNo=0;

function V(){return VARS.filter(function(v){return v.id===cur})[0]}
function key(){return 'a360_practice_'+cur}
function startChosen(v){var best=null;function go(i,ch){if(i===v.inputs.length){var sc=C.economy(v,ch).score;if(sc<100&&(best===null||Math.abs(sc-45)<Math.abs(best.sc-45)))best={sc:sc,ch:JSON.parse(JSON.stringify(ch))};return}
  v.inputs[i].sources.forEach(function(src){ch[v.inputs[i].id]=src.id;go(i+1,ch)})}go(0,{});return best?best.ch:{}}
function blank(v){var s={step:1,frame:{},action:v.frame.action,chosen:{},paramsLine:'',delta:'',volume:'',price:'',code3:'',code4:'',concl:'',c:{conclusion:'',effect:'',action:'',review:''},fin:JSON.parse(JSON.stringify(v.fin)),res:{payback:'',npv:'',year1:''},svg:''};
  FRAME.forEach(function(f){s.frame[f[0]]=v.frame[f[0]]});s.chosen=startChosen(v);s.fin.datacost=C.economy(v,s.chosen).cost;return s}
function load(id){cur=id;var v=V(),s=null;try{var raw=localStorage.getItem(key());if(raw)s=JSON.parse(raw)}catch(e){}
  st=s||blank(v);var b=blank(v);for(var k in b)if(st[k]===undefined)st[k]=b[k];dir=v.direction}
function save(){try{localStorage.setItem(key(),JSON.stringify(st))}catch(e){}}
function get(path){var p=path.split('.'),o=st;for(var i=0;i<p.length;i++){if(o==null)return '';o=o[p[i]]}return o==null?'':o}
function set(path,v){var p=path.split('.'),o=st;for(var i=0;i<p.length-1;i++){if(!o[p[i]])o[p[i]]={};o=o[p[i]]}o[p[p.length-1]]=v}
function params(){return {delta:C.num(st.delta),volume:C.num(st.volume),price:C.num(st.price)}}
function npvArgs(){var f=finP();return {delta:f.delta,volume:f.volume,price:f.price,fin:{kind:f.kind,ramp:f.ramp,keep:f.keep,capex:f.capex,datacost:f.datacost,opex:f.opex,horizon:f.horizon,rate:f.rate}}}
function paramsOk(){var p=params();return !isNaN(p.delta)&&!isNaN(p.volume)&&!isNaN(p.price)}
function finP(){var f=st.fin,p=params();return {kind:V().fin.kind,delta:p.delta||0,volume:p.volume||0,price:p.price||0,ramp:C.num(f.ramp)||0,keep:C.num(f.keep)||0,capex:(C.num(f.capex)||0)+(C.num(f.datacost)||0),datacost:C.num(f.datacost)||0,opex:C.num(f.opex)||0,horizon:Math.max(1,Math.round(C.num(f.horizon)||24)),rate:C.num(f.rate)||0}}
function done(n){switch(n){case 1:return true;case 2:return true;case 3:return paramsOk();case 4:return !!(st.svg||C.clean(st.res.npv));case 5:return !!(st.svg&&C.clean(st.c.conclusion))}return false}

// ── выбор варианта ───────────────────────────────────────────────────────
function renderPicker(){
  var d=$('dirs');d.innerHTML='';DIRS.forEach(function(x){var b=document.createElement('button');b.type='button';b.textContent=x.charAt(0).toUpperCase()+x.slice(1);b.className=x===dir?'on':'';
    b.onclick=function(){dir=x;var first=VARS.filter(function(v){return v.direction===x})[0];save();load(first.id);renderAll()};d.appendChild(b)});
  var vv=$('vars');vv.innerHTML='';VARS.filter(function(v){return v.direction===dir}).forEach(function(v,i){var b=document.createElement('button');b.type='button';b.textContent='Вариант '+(i+1)+' · '+v.title;b.className=v.id===cur?'on':'';
    b.onclick=function(){save();load(v.id);renderAll()};vv.appendChild(b)});
  var v=V();$('varNote').textContent='Направление «'+v.direction+'». Итоговая метрика варианта: '+v.metric.name+' ('+v.metric.unit+'). Входов дерева: '+v.inputs.length+', у каждого два источника.';
}
function renderStepper(){var s=$('stepper');s.innerHTML='';STEPS.forEach(function(name,i){var n=i+1,b=document.createElement('button');b.type='button';b.className=(done(n)?'ok ':'')+(n===st.step?'cur':'');b.innerHTML='<b>'+(done(n)?'✓ ':'')+'Шаг '+n+'</b>'+esc(name);b.onclick=function(){go(n)};s.appendChild(b)})}
function go(n){st.step=n;save();for(var i=1;i<=5;i++)$('st'+i).className='step'+(i===n?' on':'');renderStep(n);renderStepper();
  var top=$('stepper').getBoundingClientRect().top+window.pageYOffset-12;if(Math.abs(window.pageYOffset-top)>40)window.scrollTo(0,top)}

// ── поля ─────────────────────────────────────────────────────────────────
function fillInputs(scope){Array.prototype.forEach.call((scope||document).querySelectorAll('[data-bind]'),function(el){var v=get(el.dataset.bind);if(String(el.value)!==String(v))el.value=v})}
document.addEventListener('input',function(e){var el=e.target;if(!el.dataset||!el.dataset.bind)return;set(el.dataset.bind,el.value);
  if(el.dataset.bind==='paramsLine'){var pp=C.parseParams(el.value);if(pp){st.delta=String(pp.delta);st.volume=String(pp.volume);st.price=String(pp.price);fillInputs($('st3'))}}
  if(el.dataset.bind.indexOf('frame.')===0||el.dataset.bind==='action'){}
  save();afterChange(el.dataset.bind)});
function afterChange(bind){
  if(bind==='delta'||bind==='volume'||bind==='price'||bind==='paramsLine'){renderCtrl3();renderPrompt(4);renderCtrl4()}

  if(bind.indexOf('fin.')===0){renderPrompt(4);renderCtrl4()}
  if(bind.indexOf('c.')===0){renderSlide()}
  renderStepper();
}

// ── шаг 1 ────────────────────────────────────────────────────────────────
function renderFrame(){var v=V(),h='';FRAME.forEach(function(f){h+='<dt>'+f[1]+'</dt><dd>'+esc(st.frame[f[0]])+'</dd>'});h+='<dt>Что меняем</dt><dd>'+esc(st.action)+'</dd>';$('frame').innerHTML=h;
  $('links1').innerHTML='Из курса: <a href="longread_project.html">Каркас проекта</a> <a href="longread_project.html#problema">Формулировка проблемы</a> '+v.links.filter(function(l){return !/longread_finmodel|longread_effect|trainer_effect/.test(l[0])}).map(function(l){return '<a href="'+esc(l[0])+'">'+esc(l[1])+'</a>'}).join(' ')}

// ── шаг 2: дерево и источники ────────────────────────────────────────────
function tx(x,y,t,fs,w,f,a,o){return '<text x="'+x+'" y="'+y+'" font-size="'+fs+'"'+(w?' font-weight="'+w+'"':'')+' fill="'+f+'"'+(a?' text-anchor="'+a+'"':'')+(o?' fill-opacity="'+o+'"':'')+'>'+esc(t)+'</text>'}
function wrap(t,n,max){var w=String(t).split(' '),out=[],c='';w.forEach(function(x){if((c+' '+x).trim().length>n&&c){out.push(c.trim());c=x}else c+=' '+x});if(c.trim())out.push(c.trim());return out.slice(0,max||3)}
function badge(x,y){return '<g data-info="1"><circle cx="'+x+'" cy="'+y+'" r="9" fill="#fff" stroke="#128a53" stroke-width="1.5"/><text x="'+x+'" y="'+(y+4)+'" font-size="12" font-weight="800" fill="#128a53" text-anchor="middle">?</text></g>'}
function box(x,y,w,h,t,sub,fill,stroke,dash,fs){fs=fs||13;var o='<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="10" fill="'+fill+'" stroke="'+stroke+'" stroke-width="2"'+(dash?' stroke-dasharray="6 4"':'')+'/>';
  // текст центрируется по вертикали в части ячейки над строкой подписи
  var lh=fs*1.22,lines=wrap(t,Math.floor((w-40)/(fs*0.56)),4),subH=sub?16:0,avail=h-subH,block=lines.length*lh;
  var y0=y+(avail-block)/2+lh*0.8;
  lines.forEach(function(l,i){o+=tx(x+w/2,(y0+i*lh).toFixed(1),l,fs,'700','#2E3641','middle')});
  if(sub)o+=tx(x+w/2,y+h-7,sub,10.5,null,'#2E3641','middle',0.7);return o}
function treeSvg(v,chosen,forSlide){
  var W=960,H=346,s=[],n=v.inputs.length,colW=W/n;
  s.push('<svg viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg" role="img" font-family="'+(forSlide?'system-ui,Segoe UI,Roboto,Arial,sans-serif':'inherit')+'">');
  var g=function(attrs,inner){return forSlide?inner:'<g '+attrs+'>'+inner+'</g>'};
  s.push(g('data-kind="metric"',box(W/2-230,16,460,64,v.metric.name,v.metric.unit+' · '+v.metric.formula,'#e4ecf9','#1b5fa8',false,14)+(forSlide?'':badge(W/2+230-14,30))));
  v.inputs.forEach(function(inp,i){var cx=colW*i+colW/2,bw=Math.min(240,colW-24);
    s.push('<line x1="'+(W/2)+'" y1="80" x2="'+cx+'" y2="118" stroke="#1b5fa8" stroke-width="2" stroke-opacity="0.7"/>');
    s.push(g('data-kind="input" data-inp="'+esc(inp.id)+'"',box(cx-bw/2,118,bw,58,inp.name,inp.unit,'#e3f2ea','#20BA72',false,12.5)+(forSlide?'':badge(cx+bw/2-14,132))));
    inp.sources.forEach(function(src,j){var on=chosen[inp.id]===src.id,sw=bw/2-6,sx=cx-bw/2+j*(sw+12);
      s.push('<line x1="'+cx+'" y1="176" x2="'+(sx+sw/2)+'" y2="222" stroke="'+(on?'#20BA72':'#2E3641')+'" stroke-width="'+(on?2.5:1)+'" stroke-opacity="'+(on?0.9:0.3)+'"/>');
      s.push(g('data-kind="source" data-inp="'+esc(inp.id)+'" data-src="'+esc(src.id)+'" data-pick="1"',box(sx,222,sw,98,src.name,src.days+' дн. · '+(src.cost?C.fi(src.cost)+' руб.':'0 руб.'),on?'#fff':'#f4f8f6',on?'#20BA72':'#c9d3cd',!on,11)+(forSlide?'':badge(sx+sw-12,234))));
      if(on)s.push(tx(sx+sw/2,334,'выбран',10.5,'700','#128a53','middle'));
    });
  });
  s.push('</svg>');return s.join('');
}
function renderTree(){$('tree').innerHTML=treeSvg(V(),st.chosen,false)}
function pick(inpId,srcId){st.chosen[inpId]=srcId;st.fin.datacost=C.economy(V(),st.chosen).cost;save();renderTree();renderEco();renderFiles();renderPrompt(3);renderCtrl3()}
function sampleTable(file){var t=SAMPLES[cur+'/'+file]||'';var lines=t.split(/\r?\n/).filter(Boolean);if(!lines.length)return '';
  var h='<div class="scroll"><table><thead><tr>'+lines[0].split(';').map(function(c){return '<th>'+esc(c)+'</th>'}).join('')+'</tr></thead><tbody>';
  lines.slice(1).forEach(function(l){h+='<tr>'+l.split(';').map(function(c){return '<td>'+esc(c)+'</td>'}).join('')+'</tr>'});return h+'<tr><td colspan="9" style="color:var(--ink3)">… и далее по строкам файла</td></tr></tbody></table></div>'}
function openModal(kind,inpId,srcId){var v=V(),h='';
  if(kind==='metric'){h='<h3>'+esc(v.metric.name)+'</h3><p class="meta">Итоговая метрика эффекта · '+esc(v.metric.unit)+'</p><div class="calc">'+esc(v.metric.formula)+' — эффект в месяц; из него финансовая модель разворачивает поток по месяцам.</div>';
    h+='<p><b>Параметры финансовой модели, которые считает мини-инструмент:</b></p><table><tr><th>Параметр</th><th>Единица</th><th>Формула из входов</th></tr>';
    ['delta','volume','price'].forEach(function(k){var p=v.params[k];h+='<tr><td>'+esc(p.name)+' ('+k+')</td><td>'+esc(p.unit)+'</td><td style="white-space:normal">'+esc(p.formula)+(p.note?' — '+esc(p.note):'')+'</td></tr>'});h+='</table>';
    h+='<p class="hint">Входы дерева: '+v.inputs.map(function(i){return i.name+' ('+i.id+')'}).join('; ')+'.</p>';}
  else{var inp=v.inputs.filter(function(i){return i.id===inpId})[0];
    if(kind==='input'){h='<h3>'+esc(inp.name)+'</h3><p class="meta">Вход дерева '+esc(inp.id)+' · '+esc(inp.unit)+'</p><p>Значение входа можно получить из двух источников; выбор источника задаёт срок первого проверенного значения метрики и стоимость данных.</p>';
      inp.sources.forEach(function(sr){var on=st.chosen[inp.id]===sr.id;h+='<div class="calc"><b>'+esc(sr.name)+'</b>'+(on?' <span style="color:#128a53;font-weight:700">— выбран</span>':'')+'<br><span style="color:var(--ink3);font-size:13px">'+sr.days+' дн. · '+(sr.cost?C.fi(sr.cost)+' руб.':'без затрат')+' · файл '+esc(sr.file)+'</span><br>Расчёт: '+esc(sr.calc)+'</div>'})}
    else{var sr=inp.sources.filter(function(x){return x.id===srcId})[0],on=st.chosen[inp.id]===sr.id;
      h='<h3>'+esc(sr.name)+'</h3><p class="meta">Источник входа «'+esc(inp.name)+'» ('+esc(inp.id)+', '+esc(inp.unit)+') · срок первого значения '+sr.days+' дн. · стоимость за пилот '+(sr.cost?C.fi(sr.cost)+' руб.':'без затрат')+' · файл '+esc(sr.file)+'</p>';
      h+='<div class="calc"><b>Расчёт входа:</b> '+esc(sr.calc)+'</div><p style="margin:0 0 4px"><b>Структура данных</b> — шапка и первые строки файла:</p>'+sampleTable(sr.file);
      h+='<p style="margin-top:12px">'+(on?'<span style="color:#128a53;font-weight:700">Этот источник выбран.</span>':'<button class="btn" type="button" data-modal-pick="'+esc(inp.id)+'|'+esc(sr.id)+'">Выбрать этот источник</button>')+'</p>';}}
  $('mbody').innerHTML=h;$('modal').className='modal on'}
function closeModal(){$('modal').className='modal'}
$('tree').addEventListener('click',function(e){var b=e.target.closest('[data-info]');var gEl=e.target.closest('[data-kind]');if(!gEl)return;
  if(b){openModal(gEl.dataset.kind,gEl.dataset.inp,gEl.dataset.src);return}
  if(gEl.dataset.pick)pick(gEl.dataset.inp,gEl.dataset.src)});
$('modal').addEventListener('click',function(e){var b=e.target.closest('[data-modal-pick]');if(b){var x=b.dataset.modalPick.split('|');pick(x[0],x[1]);closeModal();return}if(e.target===$('modal')||e.target.id==='mclose')closeModal()});
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeModal()});
function renderSrcs(){var v=V(),h='';v.inputs.forEach(function(inp){h+='<p style="margin:8px 0 4px"><b>'+esc(inp.name)+'</b> <span class="hint" style="display:inline">('+esc(inp.unit)+')</span></p><div class="src">';
    inp.sources.forEach(function(s){var on=st.chosen[inp.id]===s.id;h+='<label class="'+(on?'on':'')+'"><input type="radio" name="src-'+inp.id+'" value="'+esc(s.id)+'"'+(on?' checked':'')+'><b>'+esc(s.name)+'</b><span class="meta">срок первого значения: '+s.days+' дн. · стоимость за пилот: '+(s.cost?C.fi(s.cost)+' руб.':'без затрат')+' · файл '+esc(s.file)+'</span><div style="margin-top:4px;font-size:13px">Расчёт: '+esc(s.calc)+'</div></label>'});h+='</div>'});
  $('srcs').innerHTML=h;
  Array.prototype.forEach.call($('srcs').querySelectorAll('input[type=radio]'),function(r){r.onchange=function(){st.chosen[r.name.slice(4)]=r.value;save();renderSrcs();renderTree();renderEco();renderFiles();renderPrompt(3);renderCtrl3()}})}
function renderEco(){var v=V(),e=C.economy(v,st.chosen);
  $('k-tte').textContent=e.tte+' дн.';$('k-tte-s').textContent='лучшая конфигурация: '+e.bestTte+' дн., худшая: '+e.worstTte;
  $('k-cost').textContent=e.cost?C.money(e.cost):'0 руб.';$('k-cost-s').textContent='от '+C.money(e.bestCost).replace('0 руб.','0 руб.')+' до '+C.money(e.worstCost);
  $('k-score').textContent=e.score+' из 100';$('k-score-s').textContent=e.score>=85?'быстро и недорого':e.score>=60?'приемлемо: один из входов медленный или платный':'дорого или долго: пересмотрите источники';
  var slow=e.rows.slice().sort(function(a,b){return b.source.days-a.source.days})[0];
  $('ecoNote').textContent='Срок задаёт самый медленный вход — «'+slow.input.name+'» ('+slow.source.name+', '+slow.source.days+' дн.). Интегральная оценка: 100 баллов минус штраф за дни и рубли относительно худшей конфигурации варианта. Выгрузки по месяцам из витрин бесплатны и быстры; детальные выгрузки, опросы и сверки дают то же значение, но позже и дороже — их выбирают, когда витрины нет.'}

// ── шаг 3 ────────────────────────────────────────────────────────────────
function chosenRows(){return C.economy(V(),st.chosen).rows}
function filesObj(){var o={};chosenRows().forEach(function(r){o[r.source.file]={text:SAMPLES[cur+'/'+r.source.file]||''}});return o}
function fileLink(name,label){return '<a class="f" href="practice_data/'+encodeURIComponent(cur)+'/'+encodeURIComponent(name)+'" download="'+esc(name)+'">⬇ '+esc(label||name)+'</a>'}
function renderFiles(){var h='';chosenRows().forEach(function(r){h+=fileLink(r.source.file)});$('files').innerHTML=h+'<p class="hint" style="margin-top:4px">'+chosenRows().length+' файла данных; разделитель — точка с запятой, десятичный знак — запятая.</p>'}
// ── сборка мини-инструментов одним файлом ────────────────────────────────
function moduleCode(txt,fn){var c=String(txt||'');var m=c.match(/```(?:javascript|js)?\s*([\s\S]*?)```/i);if(m)c=m[1];c=c.trim();
  if(c&&c.indexOf('window.'+fn)<0){if(new RegExp('function\\s+'+fn+'\\s*\\(').test(c))c+='\nwindow.'+fn+' = '+fn+';';}
  return c.replace(/<\/script/gi,'<\\/script')}
function codeState(n){var fn=n===3?'computeInputs':'effectFlows',c=moduleCode(get('code'+n),fn),el=$('code'+n+'msg');
  if(!C.clean(get('code'+n))){el.textContent='Код ещё не вставлен: инструмент можно скачать и так — он покажет контрольный расчёт, а расчёт ассистента добавите позже.';el.className='msg';return c}
  if(c.indexOf('window.'+fn)<0){el.textContent='В ответе не найдена функция '+fn+'. Проверьте, что вставлен ответ целиком; попросите ассистента вернуть файл с объявлением window.'+fn+'. Инструмент всё равно соберётся с контрольным расчётом.';el.className='msg warn';return c}
  el.textContent='Функция '+fn+' найдена — инструмент готов к сборке.';el.className='msg ok';return c}
function toolMeta(){var v=V(),files=[],inputs=[],ref={};v.inputs.forEach(function(i){i.sources.forEach(function(s){files.push({file:s.file,input:i.name,id:i.id});ref[s.file]=s.ref});inputs.push({id:i.id,name:i.name,unit:i.unit,file:i.sources.map(function(s){return s.file}).join(' / ')})});
  return {title:v.title,metric:v.metric,params:v.params,inputs:inputs,files:files,ref:ref}}
function finMeta(){var v=V(),f=st.fin,p=params();return {title:v.title,kind:v.fin.kind,defaults:{delta:paramsOk()?p.delta:'',volume:paramsOk()?p.volume:'',price:paramsOk()?p.price:'',ramp:f.ramp,keep:f.keep,capex:f.capex,opex:f.opex,horizon:f.horizon,rate:f.rate},units:{delta:v.params.delta.unit,volume:v.params.volume.unit,price:v.params.price.unit}}}
function assemble(n){var tpl=n===3?TOOL_TPL:FIN_TPL,meta=n===3?toolMeta():finMeta(),code=moduleCode(get('code'+n),n===3?'computeInputs':'effectFlows');
  return tpl.split('__TITLE__').join(esc(V().title)).split('__META__').join(JSON.stringify(meta).replace(/<\//g,'<\\/')).split('__MODULE__').join(code)}
function downloadHtml(html,name){var a=document.createElement('a');var blob=new Blob([html],{type:'text/html;charset=utf-8'});a.href=URL.createObjectURL(blob);a.download=name;document.body.appendChild(a);a.click();document.body.removeChild(a)}
window.__assemble=assemble;
window.__reference=function(n){return n===3?C.toolReference(V(),st.chosen,filesObj()):C.npvReference(V(),npvArgs())};
function highlight(text,values){var vals=values.map(function(v){return String(v==null?'':v).trim()}).filter(function(v){return v.length>=2});
  vals=vals.filter(function(v,i){return vals.indexOf(v)===i}).sort(function(a,b){return b.length-a.length});
  if(!vals.length)return esc(text);
  var re=new RegExp(vals.map(function(v){return v.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}).join('|'),'g');
  var out='',last=0,m;while((m=re.exec(text))){out+=esc(text.slice(last,m.index))+'<span class="phv">'+esc(m[0])+'</span>';last=m.index+m[0].length;if(!m[0].length)re.lastIndex++}
  return out+esc(text.slice(last))}
function promptValues(n){var v=V(),vals=[v.title],rows=chosenRows(),p=params(),f=finP();
  if(n===3){rows.forEach(function(r){vals.push(r.source.file,r.input.name,r.input.unit,r.source.calc,r.input.id);var sm=SAMPLES[cur+'/'+r.source.file]||'';sm.split(/\r?\n/).filter(Boolean).forEach(function(l){vals.push(l.replace(/^\uFEFF/,''))})});
    ['delta','volume','price'].forEach(function(k){vals.push(v.params[k].formula,v.params[k].unit,v.params[k].name,v.params[k].note)});vals.push(v.metric.name,v.metric.unit,v.metric.formula)}
  if(n===4){[p.delta,p.volume,p.price,f.ramp,f.keep,f.capex,f.opex,f.horizon,f.rate,f.datacost].forEach(function(x){vals.push(String(x),C.fmtv(x),C.fi(x))});vals.push(v.params.delta.unit,v.params.volume.unit,v.params.price.unit,C.money(p.delta*p.volume*p.price).replace(/\.$/,''))}
  if(n===5){var c=conclCtx(),e=c.eco;vals.push(c.frame.problem,c.action,v.metric.name,v.metric.unit,v.metric.formula);e.rows.forEach(function(r){vals.push(r.input.name,r.input.id,r.source.name,String(r.source.days),C.fi(r.source.cost),C.fmtv(c.inputs[r.input.id]),r.input.unit.replace(/\.$/,''))});
    vals.push(String(e.tte),C.fi(e.cost),String(e.score),String(e.bestTte),C.fi(e.bestCost),C.fmtv(p.delta),C.fmtv(p.volume),C.fmtv(p.price),v.params.delta.unit,v.params.delta.note,v.params.volume.unit,v.params.price.unit,String(c.fin.ramp),String(c.fin.keep),C.fi(c.fin.capex),C.fi(c.fin.datacost),C.fi(c.fin.opex),String(c.fin.horizon),C.fr(c.fin.rate*100,1),C.money(c.res.year1).replace(/\.$/,''),c.res.payback===null?'не достигается в горизонте':'месяц '+c.res.payback,C.money(c.res.npv).replace(/\.$/,''))}
  return vals}
function renderPrompt(n){var pv=$('pv'+n);if(!pv)return;var txt;
  if(n===3){txt=C.toolPrompt(V(),st.chosen,filesObj());$('ps3').textContent='Промпт собран для файлов '+chosenRows().map(function(r){return r.source.file}).join(', ')+' и содержит основу инструмента. Если в ассистенте есть выбор модели — выбирайте самую сильную.'}
  else if(n===4){var p=params();if(!paramsOk()){txt='';$('ps4').textContent='Сначала введите параметры на шаге 3.'}else{var r=C.npvPrompt(V(),npvArgs());txt=r.text;$('ps4').textContent='Параметры шага 3, стоимость данных шага 2 и условия подставлены в основу инструмента. Контрольные значения расчёта — под полями результата.'}}
  else{if(!paramsOk()){txt='';$('ps5').textContent='Сначала введите параметры на шаге 3.'}else{txt=C.conclusionPrompt(V(),conclCtx());$('ps5').textContent='В промпт подставлены конфигурация источников, значения входов, параметры и результат финансовой модели.'}}
  ptext[n]=txt;pv.innerHTML=txt?highlight(txt,promptValues(n)):''}
function renderCtrl3(){var v=V(),rows=chosenRows(),exp={};rows.forEach(function(r){exp[r.input.id]=r.source.expect});
  var keys=Object.keys(exp),delta=v.params.delta.formula,vol=v.params.volume.formula,pr=v.params.price.formula;
  var expDelta=evalFormula(delta,exp),expVol=evalFormula(vol,exp),expPrice=evalFormula(pr,exp);
  $('l-delta').textContent='Изменение показателя ('+v.params.delta.unit+')';$('l-volume').textContent='Объём ('+v.params.volume.unit+')';$('l-price').textContent='Стоимость единицы ('+v.params.price.unit+')';
  var p=params(),chk='';
  if(paramsOk()){var ok=near(p.delta,expDelta,0.05)&&near(p.price,expPrice,0.03)&&near(p.volume,expVol,0.01);chk=ok?' <b style="color:#128a53">Совпадает с контрольным расчётом.</b>':' <b style="color:var(--warn)">Отличается от контрольного расчёта — проверьте файлы и формулы инструмента.</b>'}
  $('ctrl3').innerHTML='<b>Контрольные значения для проверки инструмента</b> (страница считает их по тем же файлам): '+keys.map(function(k){return k+' = '+C.fmtv(exp[k])}).join('; ')+' → delta = '+C.fmtv(Math.round(expDelta*100)/100)+', volume = '+C.fmtv(expVol)+', price = '+C.fmtv(Math.round(expPrice*100)/100)+'.'+chk+' Если инструмент не собрался — введите контрольные значения и продолжайте.'}
function near(a,b,rel){return Math.abs(a-b)<=Math.abs(b)*rel+1e-9}
function evalFormula(f,vals){var s=String(f);Object.keys(vals).forEach(function(k){s=s.replace(new RegExp('\\b'+k+'\\b','g'),'('+vals[k]+')')});s=s.replace(/×/g,'*').replace(/÷/g,'/');if(!/^[\d\s().*\/+\-]+$/.test(s))return NaN;try{return Function('return ('+s+')')()}catch(e){return NaN}}

// ── шаг 4 ────────────────────────────────────────────────────────────────
function renderFrom34(){var v=V(),e=C.economy(v,st.chosen),p=params(),ok=paramsOk();
  var h='<div class="kpi"><div><div class="l">Метрика эффекта из шага 3</div><div class="v">'+(ok?C.money(p.delta*p.volume*p.price):'—')+'</div><div class="s">'+esc(v.metric.name)+', в месяц'+(v.fin.kind==='cohort'?' на когорту':'')+'</div></div>'+
    '<div><div class="l">Параметры из шага 3</div><div class="v" style="font-size:16px">'+(ok?C.fmtv(p.delta)+' × '+C.fmtv(p.volume)+' × '+C.fmtv(p.price):'—')+'</div><div class="s">изменение показателя × объём × стоимость единицы</div></div>'+
    '<div><div class="l">Данные из шага 2</div><div class="v">'+(e.cost?C.money(e.cost):'0 руб.')+'</div><div class="s">стоимость сбора за пилот; первое значение через '+e.tte+' дн.; оценка '+e.score+' из 100</div></div></div>'+
    '<p class="hint" style="margin:0">Поток эффекта считается от метрики шага 3, а стоимость сбора данных из шага 2 входит в единовременные затраты: чем дешевле и быстрее конфигурация источников, тем раньше окупается проект.</p>';
  $('from34').innerHTML=h}
function renderCtrl4(){if(!paramsOk()){$('ctrl4').innerHTML='<b>Контрольные значения</b> появятся после ввода параметров.';return}
  var r=C.totals(finP());var have=C.num(st.res.npv),chk='';
  if(!isNaN(have))chk=near(have,r.npv,0.03)?' <b style="color:#128a53">NPV совпадает с контрольным расчётом.</b>':' <b style="color:var(--warn)">NPV отличается от контрольного — проверьте формулу когорт и дисконтирование в инструменте.</b>';
  $('ctrl4').innerHTML='<b>Контрольные значения</b> (расчёт страницы, единовременные затраты '+C.money(finP().capex)+' с учётом данных): окупаемость — '+(r.payback===null?'не достигается':'месяц '+r.payback)+'; NPV за '+r.horizon+' мес. — '+C.money(r.npv)+'; доход за первый год — '+C.money(r.year1).replace(/\.$/,'')+'.'+chk+' Если инструмент не собрался — введите контрольные значения.'}
function sanitizeSvg(t){var s=String(t||'');var i=s.indexOf('<svg');if(i<0)return '';s=s.slice(i);var j=s.lastIndexOf('</svg>');if(j>0)s=s.slice(0,j+6);
  s=s.replace(/<script[\s\S]*?<\/script>/gi,'').replace(/\son\w+="[^"]*"/gi,'').replace(/\son\w+='[^']*'/gi,'').replace(/<foreignObject[\s\S]*?<\/foreignObject>/gi,'');
  if(!/xmlns=/.test(s.slice(0,200)))s=s.replace('<svg','<svg xmlns="http://www.w3.org/2000/svg"');return s}
function renderSvg(){$('svgBox').innerHTML=st.svg?'<div class="vis">'+st.svg+'<p class="hint" style="margin:8px 0 0">График загружен и попадёт на слайд финансовой модели.</p></div>':'<p class="hint">После загрузки график появится здесь.</p>'}
$('svgFile').addEventListener('change',function(){var f=this.files&&this.files[0];if(!f)return;var rd=new FileReader();rd.onload=function(){st.svg=sanitizeSvg(rd.result);if(!st.svg)alert('В файле не найден элемент svg');save();renderSvg();renderStepper()};rd.readAsText(f)});

// ── шаг 5: заключение и презентация ─────────────────────────────────────
function conclCtx(){var v=V(),e=C.economy(v,st.chosen),inputs={};e.rows.forEach(function(r){inputs[r.input.id]=r.source.expect});
  var f=st.fin,fp=finP(),r=C.totals(fp);var res={payback:C.clean(st.res.payback)?C.num(st.res.payback):r.payback,npv:C.clean(st.res.npv)?C.num(st.res.npv):r.npv,year1:C.clean(st.res.year1)?C.num(st.res.year1):r.year1};
  if(C.clean(st.res.payback)&&/не/.test(st.res.payback))res.payback=null;
  return {frame:st.frame,action:st.action,eco:e,inputs:inputs,params:params(),fin:{ramp:C.num(f.ramp),keep:C.num(f.keep),capex:(C.num(f.capex)||0)+(C.num(f.datacost)||0),datacost:C.num(f.datacost)||0,opex:C.num(f.opex),horizon:C.num(f.horizon),rate:C.num(f.rate)},res:res}}
function parseConcl(){var r=C.parseConclusion(st.concl),m=$('conclMsg');['conclusion','effect','action','review'].forEach(function(k){if(r.fields[k]!==undefined)st.c[k]=r.fields[k]});save();fillInputs($('st5'));
  m.textContent=r.found?'Разобрано: '+r.found+' из '+r.total+(r.found<r.total?' — остальное впишите вручную':''):'Не удалось разобрать: вставьте ответ целиком или заполните поля вручную';m.className='msg '+(r.found?'ok':'warn');renderSlide();renderStepper()}
function slides(){var v=V(),e=C.economy(v,st.chosen),p=params(),f=st.frame,r=paramsOk()?C.totals(finP()):null,S=[];
  S.push({h:v.title,b:'<p><b>Направление:</b> '+esc(v.direction)+'</p><p><b>Проблема.</b> '+esc(f.problem)+'</p><p><b>Что меняем.</b> '+esc(st.action)+'</p>'});
  S.push({h:'Метрики и данные',b:'<p><b>Метрика.</b> '+esc(f.metric)+'</p><p><b>Данные.</b> '+esc(f.data)+'</p><p><b>Инструмент.</b> '+esc(f.tool)+'</p>'});
  S.push({h:'Дерево метрик и конфигурация источников',b:treeSvg(v,st.chosen,true)+'<p style="margin-top:.4em"><b>Срок первого значения:</b> '+e.tte+' дн. · <b>Стоимость данных за пилот:</b> '+(e.cost?C.money(e.cost):'0 руб.')+' · <b>Интегральная оценка:</b> '+e.score+' из 100</p>'});
  var tb='<table><tr><th>Вход</th><th>Источник</th><th>Значение</th></tr>';e.rows.forEach(function(x){tb+='<tr><td>'+esc(x.input.name)+'</td><td>'+esc(x.source.name)+'</td><td>'+C.fmtv(x.source.expect)+' '+esc(x.input.unit)+'</td></tr>'});tb+='</table>';
  S.push({h:'Анализ: параметры эффекта по выгрузкам',b:tb+'<p style="margin-top:.5em"><b>Изменение показателя:</b> '+(paramsOk()?C.fmtv(p.delta):'—')+' '+esc(v.params.delta.unit)+' · <b>Объём:</b> '+(paramsOk()?C.fmtv(p.volume):'—')+' · <b>Стоимость единицы:</b> '+(paramsOk()?C.fmtv(p.price):'—')+' '+esc(v.params.price.unit)+'</p><p>'+esc(f.analysis)+'</p>'});
  var fin='<p><b>Формула:</b> '+(paramsOk()?C.fmtv(p.delta)+' × '+C.fmtv(p.volume)+' × '+C.fmtv(p.price)+' = '+C.money(p.delta*p.volume*p.price)+' в месяц на полном уровне':'—')+'</p>'+
    '<p><b>Окупаемость:</b> '+(C.clean(st.res.payback)||(r?(r.payback===null?'не достигается':'месяц '+r.payback):'—'))+' · <b>NPV за '+st.fin.horizon+' мес.:</b> '+(C.clean(st.res.npv)?C.money(C.num(st.res.npv)):(r?C.money(r.npv):'—'))+' · <b>Доход за первый год:</b> '+(C.clean(st.res.year1)?C.money(C.num(st.res.year1)):(r?C.money(r.year1):'—'))+'</p>'+
    '<p>Затраты: единовременно '+C.money((C.num(st.fin.capex)||0)+(C.num(st.fin.datacost)||0))+' (в том числе сбор данных '+C.money(C.num(st.fin.datacost)||0)+'), ежемесячно '+C.money(C.num(st.fin.opex)||0)+'; выход на уровень '+st.fin.ramp+' мес., срок сохранения '+st.fin.keep+' мес., ставка '+C.fr((C.num(st.fin.rate)||0)*100,1)+' %.</p>';
  S.push({h:'Финансовая модель: эффект для бизнеса',b:(st.svg||'')+fin});
  var c=st.c||{};S.push({h:'Заключение и следующий шаг',b:'<p><b>Вывод.</b> '+esc(C.or(c.conclusion,'— заключение ассистента ещё не вставлено (шаг 5)'))+'</p><p><b>Эффект для бизнеса.</b> '+esc(C.or(c.effect,'—'))+'</p><p><b>Первое действие.</b> '+esc(C.or(c.action,'—'))+'</p><p><b>Когда пересматриваем.</b> '+esc(C.or(c.review,'—'))+'</p>'});
  return S}
function renderSlide(){var S=slides();if(slideNo<0)slideNo=0;if(slideNo>=S.length)slideNo=S.length-1;var s=S[slideNo];
  $('slide').innerHTML='<div class="h">'+esc(s.h)+'</div><div class="b">'+s.b+'</div>';$('slPos').textContent='Слайд '+(slideNo+1)+' из '+S.length}
$('slPrev').onclick=function(){slideNo--;renderSlide()};$('slNext').onclick=function(){slideNo++;renderSlide()};
function deckHtml(){var S=slides(),v=V();
  var css='body{margin:0;background:#20262e;font-family:system-ui,"Segoe UI",Roboto,Arial,sans-serif;color:#2E3641}.wrap{max-width:1100px;margin:0 auto;padding:20px}.slide{display:none;aspect-ratio:16/9;background:#fff;border-radius:10px;padding:4% 5%;box-sizing:border-box;flex-direction:column;gap:2%;overflow:hidden}.slide.on{display:flex}.h{font-size:clamp(16px,2.6vw,30px);font-weight:800;line-height:1.15;border-bottom:3px solid #20BA72;padding-bottom:1.5%}.b{font-size:clamp(12px,1.55vw,18px);line-height:1.4;overflow:hidden}.b p{margin:0 0 .6em}.b table{border-collapse:collapse;width:100%;font-size:.95em}.b td,.b th{border-bottom:1px solid #e6ecf1;padding:4px 8px;text-align:left}.b svg{max-height:62%;width:auto;max-width:100%;display:block;margin:0 auto}nav{display:flex;justify-content:space-between;align-items:center;color:#aeb9c6;font-size:14px;margin-top:12px}nav button{border:0;border-radius:8px;background:#3a4453;color:#fff;padding:8px 16px;cursor:pointer;font:inherit}@media print{body{background:#fff}.slide{display:flex;page-break-after:always;border:1px solid #ddd;margin:0 0 10px}nav{display:none}}';
  var js='var i=0,s=document.querySelectorAll(".slide");function show(k){i=Math.max(0,Math.min(s.length-1,k));for(var j=0;j<s.length;j++)s[j].className="slide"+(j===i?" on":"");document.getElementById("pos").textContent="Слайд "+(i+1)+" из "+s.length}document.getElementById("p").onclick=function(){show(i-1)};document.getElementById("n").onclick=function(){show(i+1)};document.addEventListener("keydown",function(e){if(e.key==="ArrowRight"||e.key===" ")show(i+1);if(e.key==="ArrowLeft")show(i-1)});show(0);';
  var h='<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+esc(v.title)+' · проект</title><style>'+css+'</style></head><body><div class="wrap">';
  S.forEach(function(s){h+='<section class="slide"><div class="h">'+esc(s.h)+'</div><div class="b">'+s.b+'</div></section>'});
  h+='<nav><button id="p" type="button">← Назад</button><span id="pos"></span><button id="n" type="button">Вперёд →</button></nav></div><script>'+js+'<\/script></body></html>';return h}
$('bDownload').onclick=function(){var html=deckHtml(),a=document.createElement('a');var blob=new Blob([html],{type:'text/html;charset=utf-8'});a.href=URL.createObjectURL(blob);a.download='проект_'+cur+'.html';document.body.appendChild(a);a.click();document.body.removeChild(a);
  $('dlMsg').textContent='Файл презентации сохранён. Если загрузка заблокирована, откройте меню браузера «Сохранить страницу» на этом шаге или обратитесь к куратору.';$('dlMsg').className='msg ok'};

// ── сборка ───────────────────────────────────────────────────────────────
function copyText(txt,btn,lbl){function done(){btn.textContent='Скопировано';btn.classList.add('done');setTimeout(function(){btn.classList.remove('done');btn.textContent=lbl},1800)}
  function fb(){var a=document.createElement('textarea');a.value=txt;a.style.position='fixed';a.style.opacity=0;document.body.appendChild(a);a.select();try{document.execCommand('copy');done()}catch(_e){btn.textContent='Выделите вручную'}document.body.removeChild(a)}
  if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(txt).then(done,fb)}else{fb()}}
document.addEventListener('click',function(e){var t=e.target.closest('button');if(!t)return;
  if(t.dataset.go){go(+t.dataset.go);return}
  if(t.dataset.copy){e.stopImmediatePropagation();copyText(ptext[+t.dataset.copy]||'',t,'Копировать промпт');return}
  if(t.id==='bConcl'){parseConcl();return}
  if(t.id==='bToolRef'){downloadHtml(C.toolReference(V(),st.chosen,filesObj()),'инструмент_'+cur+'.html');return}
  if(t.id==='bFinRef'){if(!paramsOk()){alert('Сначала введите параметры на шаге 3');return}downloadHtml(C.npvReference(V(),npvArgs()),'финмодель_'+cur+'.html');return}
});
function renderStep(n){fillInputs($('st'+n));
  switch(n){case 1:renderFrame();break;case 2:renderTree();renderEco();break;case 3:renderFiles();renderPrompt(3);renderCtrl3();break;case 4:renderFrom34();renderPrompt(4);renderCtrl4();renderSvg();break;case 5:renderPrompt(5);slideNo=0;renderSlide();break}}
function renderAll(){fillInputs(document);renderPicker();renderStepper();go(st.step||1)}
var first=null;try{first=localStorage.getItem('a360_practice_last')}catch(e){}
load(first&&VARS.some(function(v){return v.id===first})?first:VARS[0].id);
var _save=save;save=function(){_save();try{localStorage.setItem('a360_practice_last',cur)}catch(e){}};
renderAll();
})();
</script>
"""


def _json(o):
    return json.dumps(o, ensure_ascii=False).replace("</", "<\\/")


BODY = (CSS + HTML + "<script>\n" + CORE.replace("</", "<\\/") + "\n</script>"
        + UI.replace("__VARIANTS__", _json(VARIANTS)).replace("__SAMPLES__", _json(_samples()))
        .replace("__TOOL_TPL__", _json(TOOL_TPL)).replace("__FIN_TPL__", _json(FIN_TPL)))
