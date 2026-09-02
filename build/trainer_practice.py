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
.pr .frame{display:grid;grid-template-columns:150px 1fr;gap:6px 14px;font-size:15px}
.pr .frame dt{font-weight:800;color:var(--ink2);font-size:12.5px;text-transform:uppercase;letter-spacing:.05em;padding-top:8px}
.pr .frame dd{margin:0}
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
</style>
"""


def _пром(n):
    return (f'<div class="pctl"><div class="pctl-head"><span style="color:#aeb9c6;font-size:13px">Промпт собран из вашей конфигурации</span>'
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
  <p class="lead">Три направления — продукт, процесс, бизнес-инициатива — по три варианта в каждом.
     По своему варианту участник проходит каркас проекта, собирает конфигурацию дерева метрик
     с оценкой скорости и цены данных, получает от ассистента мини-инструмент расчёта параметров
     на нескольких выгрузках, затем мини-инструмент финансовой модели с графиком, и собирает
     презентацию проекта.</p>
  <div class="meta">
    <span class="chip">Вариантов: <b>9</b></span>
    <span class="chip">Шагов: <b>5</b></span>
    <span class="chip">Нужен: <b>ассистент в браузере</b></span>
    <span class="chip">Итог: <b>презентация проекта</b></span>
  </div>
</div></header>

<section><div class="wrap pr">
<div class="card acc">
<h4>Как проходить</h4>
<ol style="margin:0;padding-left:22px">
<li><b>Выберите вариант</b> — направление и номер. Каркас проекта по варианту заполнен, его можно уточнить.</li>
<li><b>Соберите конфигурацию</b> дерева: для каждого входа итоговой метрики выберите источник данных.
    Страница показывает срок первого значения, стоимость и интегральную оценку конфигурации.</li>
<li><b>Скачайте каркас мини-инструмента и файлы</b> выбранных источников в одну папку, скопируйте промпт. Ассистент
    возвращает файл расчёта: сохраните его рядом с каркасом как rasschet.js, откройте каркас, выберите файлы — инструмент
    посчитает параметры проекта и сверит расчёт ассистента с контрольным.</li>
<li><b>Финансовая модель:</b> второй каркас и второй промпт с параметрами — ассистент возвращает файл расчёта потока
    model.js; каркас показывает окупаемость, NPV и график SVG с кнопкой сохранения. Загрузите SVG сюда.</li>
<li><b>Презентация</b> собирается из всего сделанного: слайды листаются здесь и скачиваются одним HTML-файлом.</li>
</ol>
<p class="sub" style="margin:10px 0 0">Введённое сохраняется в браузере отдельно для каждого варианта. Как сохранить ответ
ассистента файлом — в материале <a href="guide_mini.html">«Мини-инструменты»</a>. Если файл расчёта не собрался,
каркас показывает контрольный расчёт, и занятие продолжается.</p>
</div>

<h3>Вариант</h3>
<div class="dirs" id="dirs"></div>
<div class="vars" id="vars"></div>
<p class="hint" id="varNote"></p>

<div class="stepper" id="stepper"></div>

<!-- ─── Шаг 1 ─────────────────────────────────────────────────────────── -->
<div class="step" id="st1">
<div class="sthead"><span class="snum">Шаг 1</span><h3>Каркас проекта</h3></div>
<p class="sub">Семь элементов каркаса: проблема → метрика → данные → инструмент → анализ → вывод → эффект.
По варианту они заполнены; уточните формулировки языком своего подразделения — проблема должна содержать
показатель с числом, источник и то, что меняем.</p>
<p class="links" id="links1">Из курса: <a href="longread_project.html">Каркас проекта</a>
<a href="longread_project.html#problema">Формулировка проблемы</a> <a href="longread_effect.html">Повторение основ</a></p>
<div class="part"><h4><span class="n">1</span>Элементы каркаса</h4>
<dl class="frame" id="frame"></dl>
</div>
<div class="part"><h4><span class="n">2</span>Что меняем</h4>
<div class="fld"><label>Изменение, которое проверяет проект</label><textarea data-bind="action"></textarea></div>
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
<div class="part"><h4><span class="n">1</span>Дерево</h4><div class="vis" id="tree"></div></div>
<div class="part"><h4><span class="n">2</span>Источники по входам</h4><div id="srcs"></div></div>
<div class="part"><h4><span class="n">3</span>Оценка конфигурации</h4>
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
<p class="sub">Мини-инструмент состоит из готового каркаса и файла расчёта. Каркас читает несколько CSV одной кнопкой,
считает три параметра финансовой модели и рисует график; файл расчёта <b>rasschet.js</b> по формулам дерева пишет ассистент
по промпту ниже. Расчёт выполняется в браузере, данные никуда не отправляются.</p>
<p class="links">Из курса: <a href="guide_mini.html">Мини-инструменты: как создать и открыть</a>
<a href="case_report.html">Мини-инструменты корреляций и трендов</a>
<a href="longread_finmodel.html#formula">Формула эффекта</a></p>
<div class="part"><h4><span class="n">1</span>Скачайте каркас и файлы выбранных источников</h4>
<p class="hint">Всё — в одну папку. Имена файлов должны остаться такими же: каркас распознаёт файл по имени.</p>
<div class="files" id="files"></div>
</div>
<div class="part"><h4><span class="n">2</span>Промпт на файл расчёта</h4>{_пром(3)}
<p class="hint" style="margin-top:8px">Вставьте промпт в новый чат ассистента. Ответ (только код) сохраните в ту же папку файлом
<b>rasschet.js</b>, откройте каркас <b>инструмент_параметров.html</b> в браузере и выберите скачанные CSV одной кнопкой. Если каркас
сообщает об ошибке — скопируйте его сообщение ассистенту и замените файл расчёта.</p></div>
<div class="part"><h4><span class="n">3</span>Параметры из инструмента</h4>
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
<p class="sub">Каркас финансовой модели показывает поля параметров и условий, таблицу потока по месяцам, окупаемость, NPV
и график SVG с кнопкой сохранения; файл расчёта потока <b>model.js</b> по формулам финансовой модели пишет ассистент.</p>
<p class="links">Из курса: <a href="longread_finmodel.html#potok">Поток эффекта во времени</a>
<a href="longread_finmodel.html#npv">NPV и правило принятия</a>
<a href="trainer_effect.html">Тренажёр «Финансовая модель эффекта»</a></p>
<div class="part"><h4><span class="n">1</span>Условия финансовой модели</h4>
<div class="grid">
<div class="fld"><label>Выход на полный уровень, мес.</label><input data-bind="fin.ramp"></div>
<div class="fld"><label>Срок сохранения эффекта, мес.</label><input data-bind="fin.keep"></div>
<div class="fld"><label>Единовременные затраты, руб.</label><input data-bind="fin.capex"></div>
<div class="fld"><label>Ежемесячные затраты, руб.</label><input data-bind="fin.opex"></div>
<div class="fld"><label>Горизонт, мес.</label><input data-bind="fin.horizon"></div>
<div class="fld"><label>Ставка дисконтирования, доля в год</label><input data-bind="fin.rate"></div>
</div>
</div>
<div class="part"><h4><span class="n">2</span>Каркас и промпт на файл расчёта</h4>
<div class="files" id="files4"></div>{_пром(4)}
<p class="hint" style="margin-top:8px">Ответ сохраните рядом с каркасом файлом <b>model.js</b>, откройте <b>финмодель.html</b>,
введите параметры из шага 3 и нажмите «Рассчитать». Кнопка «Сохранить SVG» сохраняет график файлом npv.svg — загрузите его ниже.</p></div>
<div class="part"><h4><span class="n">3</span>Результат инструмента</h4>
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
<div class="sthead"><span class="snum">Шаг 5</span><h3>Презентация проекта</h3></div>
<p class="sub">Шесть слайдов по структуре презентации проекта: проблема и метрики, дерево и данные, инструмент
и параметры, финансовая модель с графиком, вывод и следующий шаг. Слайды листаются здесь и скачиваются
одним HTML-файлом, который открывается в любом браузере без интернета.</p>
<p class="links">Из курса: <a href="longread_project.html#prezentaciya">Структура презентации проекта</a>
<a href="longread_project.html#pismo">Письмо команде</a></p>
<div class="part"><h4><span class="n">1</span>Слайды</h4>
<div class="slides"><div class="slide" id="slide"></div>
<div class="slnav"><button type="button" id="slPrev">← Назад</button><span id="slPos"></span><button type="button" id="slNext">Вперёд →</button></div></div>
<p class="msg" id="dlMsg"></p>
</div>
{_нав(5, True)}
</div>

</div></section>

<footer><div class="wrap">
  Аналитика 360 · материалы практической части. Выгрузки вариантов синтетические. Расчёты и файлы
  остаются в вашем браузере.
</div></footer>
"""

UI = r"""
<script>
(function(){
var C=window.PracticeCore, VARS=__VARIANTS__, SAMPLES=__SAMPLES__;
var $=function(id){return document.getElementById(id)};
var esc=function(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')};
var DIRS=['продукт','процесс','бизнес-инициатива'];
var FRAME=[['problem','Проблема'],['metric','Метрика'],['data','Данные'],['tool','Инструмент'],['analysis','Анализ'],['conclusion','Вывод'],['effect','Эффект']];
var STEPS=['Каркас проекта','Дерево и источники','Мини-инструмент параметров','Финансовая модель','Презентация'];
var cur=null, st=null, dir=DIRS[0], ptext={}, slideNo=0;

function V(){return VARS.filter(function(v){return v.id===cur})[0]}
function key(){return 'a360_practice_'+cur}
function blank(v){var s={step:1,frame:{},action:v.frame.action,chosen:{},paramsLine:'',delta:'',volume:'',price:'',fin:JSON.parse(JSON.stringify(v.fin)),res:{payback:'',npv:'',year1:''},svg:''};
  FRAME.forEach(function(f){s.frame[f[0]]=v.frame[f[0]]});v.inputs.forEach(function(i){s.chosen[i.id]=i.sources[0].id});return s}
function load(id){cur=id;var v=V(),s=null;try{var raw=localStorage.getItem(key());if(raw)s=JSON.parse(raw)}catch(e){}
  st=s||blank(v);var b=blank(v);for(var k in b)if(st[k]===undefined)st[k]=b[k];dir=v.direction}
function save(){try{localStorage.setItem(key(),JSON.stringify(st))}catch(e){}}
function get(path){var p=path.split('.'),o=st;for(var i=0;i<p.length;i++){if(o==null)return '';o=o[p[i]]}return o==null?'':o}
function set(path,v){var p=path.split('.'),o=st;for(var i=0;i<p.length-1;i++){if(!o[p[i]])o[p[i]]={};o=o[p[i]]}o[p[p.length-1]]=v}
function params(){return {delta:C.num(st.delta),volume:C.num(st.volume),price:C.num(st.price)}}
function paramsOk(){var p=params();return !isNaN(p.delta)&&!isNaN(p.volume)&&!isNaN(p.price)}
function finP(){var f=st.fin,p=params();return {kind:V().fin.kind,delta:p.delta||0,volume:p.volume||0,price:p.price||0,ramp:C.num(f.ramp)||0,keep:C.num(f.keep)||0,capex:C.num(f.capex)||0,opex:C.num(f.opex)||0,horizon:Math.max(1,Math.round(C.num(f.horizon)||24)),rate:C.num(f.rate)||0}}
function done(n){switch(n){case 1:return true;case 2:return true;case 3:return paramsOk();case 4:return !!(st.svg||C.clean(st.res.npv));case 5:return !!st.svg}return false}

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
  renderStepper();
}

// ── шаг 1 ────────────────────────────────────────────────────────────────
function renderFrame(){var v=V(),h='';FRAME.forEach(function(f){h+='<dt>'+f[1]+'</dt><dd><textarea data-bind="frame.'+f[0]+'"></textarea></dd>'});$('frame').innerHTML=h;fillInputs($('st1'));
  $('links1').innerHTML='Из курса: <a href="longread_project.html">Каркас проекта</a> <a href="longread_project.html#problema">Формулировка проблемы</a> '+v.links.map(function(l){return '<a href="'+esc(l[0])+'">'+esc(l[1])+'</a>'}).join(' ')}

// ── шаг 2: дерево и источники ────────────────────────────────────────────
function tx(x,y,t,fs,w,f,a,o){return '<text x="'+x+'" y="'+y+'" font-size="'+fs+'"'+(w?' font-weight="'+w+'"':'')+' fill="'+f+'"'+(a?' text-anchor="'+a+'"':'')+(o?' fill-opacity="'+o+'"':'')+'>'+esc(t)+'</text>'}
function wrap(t,n){var w=String(t).split(' '),out=[],c='';w.forEach(function(x){if((c+' '+x).trim().length>n){out.push(c.trim());c=x}else c+=' '+x});if(c.trim())out.push(c.trim());return out.slice(0,3)}
function box(x,y,w,h,t,sub,fill,stroke,dash,fs){var o='<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="10" fill="'+fill+'" stroke="'+stroke+'" stroke-width="2"'+(dash?' stroke-dasharray="6 4"':'')+'/>';
  var lines=wrap(t,Math.floor(w/((fs||13)*0.58)));lines.forEach(function(l,i){o+=tx(x+w/2,y+20+i*15-(lines.length-1)*7,l,fs||13,'700','#2E3641','middle')});
  if(sub)o+=tx(x+w/2,y+h-9,sub,10.5,null,'#2E3641','middle',0.7);return o}
function treeSvg(v,chosen,forSlide){
  var W=960,H=330,s=[],n=v.inputs.length,colW=W/n;
  s.push('<svg viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg" role="img" font-family="'+(forSlide?'system-ui,Segoe UI,Roboto,Arial,sans-serif':'inherit')+'">');
  s.push(box(W/2-190,16,380,64,v.metric.name,v.metric.unit+' · '+v.metric.formula,'#e4ecf9','#1b5fa8',false,14));
  v.inputs.forEach(function(inp,i){var cx=colW*i+colW/2,bw=Math.min(240,colW-24);
    s.push('<line x1="'+(W/2)+'" y1="80" x2="'+cx+'" y2="118" stroke="#1b5fa8" stroke-width="2" stroke-opacity="0.7"/>');
    s.push(box(cx-bw/2,118,bw,58,inp.name,inp.unit,'#e3f2ea','#20BA72',false,12.5));
    inp.sources.forEach(function(src,j){var on=chosen[inp.id]===src.id,sw=bw/2-6,sx=cx-bw/2+j*(sw+12);
      s.push('<line x1="'+cx+'" y1="176" x2="'+(sx+sw/2)+'" y2="222" stroke="'+(on?'#20BA72':'#2E3641')+'" stroke-width="'+(on?2.5:1)+'" stroke-opacity="'+(on?0.9:0.3)+'"/>');
      s.push(box(sx,222,sw,84,src.name,src.days+' дн. · '+(src.cost?C.fi(src.cost)+' руб.':'0 руб.'),on?'#fff':'#f4f8f6',on?'#20BA72':'#c9d3cd',!on,11));
      if(on)s.push(tx(sx+sw/2,318,'выбран',10.5,'700','#128a53','middle'));
    });
  });
  s.push('</svg>');return s.join('');
}
function renderTree(){$('tree').innerHTML=treeSvg(V(),st.chosen,false)}
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
function renderFiles(){var h=fileLink('инструмент_параметров.html','инструмент_параметров.html — каркас');chosenRows().forEach(function(r){h+=fileLink(r.source.file)});$('files').innerHTML=h+'<p class="hint" style="margin-top:4px">Каркас и '+chosenRows().length+' файла данных; разделитель — точка с запятой, десятичный знак — запятая.</p>';
  var f4=$('files4');if(f4)f4.innerHTML=fileLink('финмодель.html','финмодель.html — каркас финансовой модели')}
function renderPrompt(n){var pv=$('pv'+n);if(!pv)return;var txt;
  if(n===3){txt=C.calcPrompt(V(),st.chosen,filesObj());$('ps3').textContent='Промпт учитывает выбранные источники: '+chosenRows().map(function(r){return r.source.file}).join(', ')+'. Если в ассистенте есть выбор модели — выбирайте самую сильную.'}
  else{var p=params();if(!paramsOk()){txt='';$('ps4').textContent='Сначала введите параметры на шаге 3.'}else{var r=C.modelPrompt(V(),p);txt=r.text;$('ps4').textContent='Формулы потока — те же, что в материале «Финансовая модель проекта». Контрольные значения расчёта — под полями результата.'}}
  ptext[n]=txt;pv.textContent=txt}
function renderCtrl3(){var v=V(),rows=chosenRows(),exp={};rows.forEach(function(r){exp[r.input.id]=r.source.expect});
  var keys=Object.keys(exp),delta=v.params.delta.formula,vol=v.params.volume.formula,pr=v.params.price.formula;
  var expDelta=evalFormula(delta,exp),expVol=evalFormula(vol,exp),expPrice=evalFormula(pr,exp);
  $('l-delta').textContent='Изменение показателя ('+v.params.delta.unit+')';$('l-volume').textContent='Объём ('+v.params.volume.unit+')';$('l-price').textContent='Стоимость единицы ('+v.params.price.unit+')';
  var p=params(),chk='';
  if(paramsOk()){var ok=near(p.delta,expDelta,0.05)&&near(p.price,expPrice,0.03)&&near(p.volume,expVol,0.01);chk=ok?' <b style="color:#128a53">Совпадает с контрольным расчётом.</b>':' <b style="color:var(--warn)">Отличается от контрольного расчёта — проверьте файлы и формулы инструмента.</b>'}
  $('ctrl3').innerHTML='<b>Контрольные значения</b> (страница считает их по тем же файлам): '+keys.map(function(k){return k+' = '+C.fmtv(exp[k])}).join('; ')+' → delta = '+C.fmtv(Math.round(expDelta*100)/100)+', volume = '+C.fmtv(expVol)+', price = '+C.fmtv(Math.round(expPrice*100)/100)+'.'+chk+' Если инструмент не собрался — введите контрольные значения и продолжайте.'}
function near(a,b,rel){return Math.abs(a-b)<=Math.abs(b)*rel+1e-9}
function evalFormula(f,vals){var s=String(f);Object.keys(vals).forEach(function(k){s=s.replace(new RegExp('\\b'+k+'\\b','g'),'('+vals[k]+')')});s=s.replace(/×/g,'*').replace(/÷/g,'/');if(!/^[\d\s().*\/+\-]+$/.test(s))return NaN;try{return Function('return ('+s+')')()}catch(e){return NaN}}

// ── шаг 4 ────────────────────────────────────────────────────────────────
function renderCtrl4(){if(!paramsOk()){$('ctrl4').innerHTML='<b>Контрольные значения</b> появятся после ввода параметров.';return}
  var r=C.totals(finP());var have=C.num(st.res.npv),chk='';
  if(!isNaN(have))chk=near(have,r.npv,0.03)?' <b style="color:#128a53">NPV совпадает с контрольным расчётом.</b>':' <b style="color:var(--warn)">NPV отличается от контрольного — проверьте формулу когорт и дисконтирование в инструменте.</b>';
  $('ctrl4').innerHTML='<b>Контрольные значения</b> (расчёт страницы): окупаемость — '+(r.payback===null?'не достигается':'месяц '+r.payback)+'; NPV за '+r.horizon+' мес. — '+C.money(r.npv)+'; доход за первый год — '+C.money(r.year1).replace(/\.$/,'')+'.'+chk+' Если инструмент не собрался — введите контрольные значения.'}
function sanitizeSvg(t){var s=String(t||'');var i=s.indexOf('<svg');if(i<0)return '';s=s.slice(i);var j=s.lastIndexOf('</svg>');if(j>0)s=s.slice(0,j+6);
  s=s.replace(/<script[\s\S]*?<\/script>/gi,'').replace(/\son\w+="[^"]*"/gi,'').replace(/\son\w+='[^']*'/gi,'').replace(/<foreignObject[\s\S]*?<\/foreignObject>/gi,'');
  if(!/xmlns=/.test(s.slice(0,200)))s=s.replace('<svg','<svg xmlns="http://www.w3.org/2000/svg"');return s}
function renderSvg(){$('svgBox').innerHTML=st.svg?'<div class="vis">'+st.svg+'<p class="hint" style="margin:8px 0 0">График загружен и попадёт на слайд финансовой модели.</p></div>':'<p class="hint">После загрузки график появится здесь.</p>'}
$('svgFile').addEventListener('change',function(){var f=this.files&&this.files[0];if(!f)return;var rd=new FileReader();rd.onload=function(){st.svg=sanitizeSvg(rd.result);if(!st.svg)alert('В файле не найден элемент svg');save();renderSvg();renderStepper()};rd.readAsText(f)});

// ── шаг 5: презентация ───────────────────────────────────────────────────
function slides(){var v=V(),e=C.economy(v,st.chosen),p=params(),f=st.frame,r=paramsOk()?C.totals(finP()):null,S=[];
  S.push({h:v.title,b:'<p><b>Направление:</b> '+esc(v.direction)+'</p><p><b>Проблема.</b> '+esc(f.problem)+'</p><p><b>Что меняем.</b> '+esc(st.action)+'</p>'});
  S.push({h:'Метрики и данные',b:'<p><b>Метрика.</b> '+esc(f.metric)+'</p><p><b>Данные.</b> '+esc(f.data)+'</p><p><b>Инструмент.</b> '+esc(f.tool)+'</p>'});
  S.push({h:'Дерево метрик и конфигурация источников',b:treeSvg(v,st.chosen,true)+'<p style="margin-top:.4em"><b>Срок первого значения:</b> '+e.tte+' дн. · <b>Стоимость данных за пилот:</b> '+(e.cost?C.money(e.cost):'0 руб.')+' · <b>Интегральная оценка:</b> '+e.score+' из 100</p>'});
  var tb='<table><tr><th>Вход</th><th>Источник</th><th>Значение</th></tr>';e.rows.forEach(function(x){tb+='<tr><td>'+esc(x.input.name)+'</td><td>'+esc(x.source.name)+'</td><td>'+C.fmtv(x.source.expect)+' '+esc(x.input.unit)+'</td></tr>'});tb+='</table>';
  S.push({h:'Анализ: параметры эффекта по выгрузкам',b:tb+'<p style="margin-top:.5em"><b>Изменение показателя:</b> '+(paramsOk()?C.fmtv(p.delta):'—')+' '+esc(v.params.delta.unit)+' · <b>Объём:</b> '+(paramsOk()?C.fmtv(p.volume):'—')+' · <b>Стоимость единицы:</b> '+(paramsOk()?C.fmtv(p.price):'—')+' '+esc(v.params.price.unit)+'</p><p>'+esc(f.analysis)+'</p>'});
  var fin='<p><b>Формула:</b> '+(paramsOk()?C.fmtv(p.delta)+' × '+C.fmtv(p.volume)+' × '+C.fmtv(p.price)+' = '+C.money(p.delta*p.volume*p.price)+' в месяц на полном уровне':'—')+'</p>'+
    '<p><b>Окупаемость:</b> '+(C.clean(st.res.payback)||(r?(r.payback===null?'не достигается':'месяц '+r.payback):'—'))+' · <b>NPV за '+st.fin.horizon+' мес.:</b> '+(C.clean(st.res.npv)?C.money(C.num(st.res.npv)):(r?C.money(r.npv):'—'))+' · <b>Доход за первый год:</b> '+(C.clean(st.res.year1)?C.money(C.num(st.res.year1)):(r?C.money(r.year1):'—'))+'</p>'+
    '<p>Затраты: единовременно '+C.money(C.num(st.fin.capex)||0)+', ежемесячно '+C.money(C.num(st.fin.opex)||0)+'; выход на уровень '+st.fin.ramp+' мес., срок сохранения '+st.fin.keep+' мес., ставка '+C.fr((C.num(st.fin.rate)||0)*100,1)+' %.</p>';
  S.push({h:'Финансовая модель: эффект для бизнеса',b:(st.svg||'')+fin});
  S.push({h:'Вывод и следующий шаг',b:'<p><b>Вывод.</b> '+esc(f.conclusion)+'</p><p><b>Эффект.</b> '+esc(f.effect)+'</p><p><b>Первое действие.</b> '+esc(st.action)+' — первая сверка метрики по полной выгрузке через '+e.tte+' дн. после старта; условие пересмотра: значение параметра «изменение показателя» ниже пессимистичного.</p>'});
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
  if(t.dataset.copy){e.stopImmediatePropagation();copyText(ptext[+t.dataset.copy]||'',t,'Копировать промпт');return}});
function renderStep(n){fillInputs($('st'+n));
  switch(n){case 1:renderFrame();break;case 2:renderTree();renderSrcs();renderEco();break;case 3:renderFiles();renderPrompt(3);renderCtrl3();break;case 4:renderFiles();renderPrompt(4);renderCtrl4();renderSvg();break;case 5:slideNo=0;renderSlide();break}}
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
        + UI.replace("__VARIANTS__", _json(VARIANTS)).replace("__SAMPLES__", _json(_samples())))
