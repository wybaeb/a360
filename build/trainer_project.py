# -*- coding: utf-8 -*-
"""Тренажёр «Сквозная практика: проект от проблемы до эффекта»
(a360/trainer_project.html).

Девять шагов по каркасу проекта. На каждом шаге участник заполняет поля,
получает готовый промпт (шаблон или заполненный), копирует его в ассистента,
вставляет ответ обратно — страница разбирает ответ в поля следующего шага
и рисует результат: график показателя, дерево метрик, таблицу данных,
связь показателей, поток эффекта, слайд, письмо. Итог — файл проекта
в Markdown: каркас, слайд «Эффект для бизнеса», письмо команде.

Разделение труда: ассистент формулирует и выбирает (проблема, метрики,
план по данным, вывод, допущения, тексты), страница считает (связь, тренд,
поток эффекта, окупаемость, NPV, чувствительность). Так каждый шаг проходит
на базовой веб-модели ассистента, которая не читает файлы и ненадёжна
в арифметике.

Ядро (промпты, разбор ответов, расчёты) — build/src/project_core.js: тот же
файл использует прогон цепочки через API build/check_project_chain.cjs.
Заготовки трёх кейсов — build/src/project_presets.json (build/project_data.py).
Подключение: build_pages.py, PAGES → trainer_project.BODY.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
CORE = (HERE / "src" / "project_core.js").read_text(encoding="utf-8")
PRESETS = json.loads((HERE / "src" / "project_presets.json").read_text(encoding="utf-8"))

CSS = """
<style>
.pj .tabs{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}
.pj .tabs button{background:var(--surf);border:1px solid var(--line);border-radius:10px;
  padding:8px 14px;font:inherit;font-size:15px;color:var(--ink);cursor:pointer}
.pj .tabs button.on{background:var(--acc);border-color:var(--acc);color:#fff;font-weight:700}
.pj .frame{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:0 0 6px}
@media(max-width:720px){.pj .frame{grid-template-columns:1fr 1fr}}
.pj .frame>div{background:var(--surf);border:1px solid var(--line);border-radius:12px;padding:9px 12px;
  min-height:74px;cursor:pointer;font-size:13.5px;line-height:1.35}
.pj .frame>div.ok{background:var(--acc-soft);border-color:var(--acc-line)}
.pj .frame>div.cur{outline:2px solid var(--acc)}
.pj .frame .l{font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);font-weight:800;margin-bottom:3px}
.pj .frame .t{color:var(--ink2);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.pj .frame>div.ok .t{color:var(--ink)}
.pj .stepper{display:flex;flex-wrap:wrap;gap:6px;margin:18px 0 22px}
.pj .stepper button{flex:1 1 90px;background:var(--surf);border:1px solid var(--line);border-radius:10px;
  padding:7px 8px;font:inherit;font-size:13px;color:var(--ink2);cursor:pointer;text-align:left;line-height:1.25}
.pj .stepper button b{display:block;font-size:12px;color:var(--ink3)}
.pj .stepper button.ok{border-color:var(--acc-line);background:var(--acc-soft);color:var(--ink)}
.pj .stepper button.ok b{color:#128a53}
.pj .stepper button.cur{border-color:var(--acc);box-shadow:inset 0 0 0 1px var(--acc);color:var(--ink)}
.pj .step{display:none}
.pj .step.on{display:block}
.pj .sthead{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin:0 0 4px}
.pj .sthead h3{margin:0;font-size:22px}
.pj .snum{color:var(--acc);font-weight:800;font-size:13px;letter-spacing:.1em;text-transform:uppercase}
.pj .sst{font-size:12.5px;font-weight:700;border-radius:999px;padding:2px 10px;background:var(--elev);color:var(--ink3)}
.pj .sst.ok{background:var(--acc-soft);color:#128a53}
.pj .part{border:1px solid var(--line);border-radius:14px;padding:14px 18px;margin:0 0 12px;background:#fff}
.pj .part h4{margin:0 0 8px;color:var(--ink);font-size:15px}
.pj .part h4 .n{display:inline-block;width:22px;height:22px;border-radius:50%;background:var(--acc);color:#fff;
  text-align:center;line-height:22px;font-size:12.5px;margin-right:8px}
.pj .grid{display:grid;grid-template-columns:1fr 1fr;gap:10px 18px}
@media(max-width:720px){.pj .grid{grid-template-columns:1fr}}
.pj .fld{margin:0 0 8px}
.pj .fld label{display:block;font-size:13px;color:var(--ink3);margin:0 0 3px}
.pj .fld input,.pj .fld select,.pj .fld textarea{width:100%;box-sizing:border-box;font:inherit;font-size:15px;
  padding:7px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;color:var(--ink)}
.pj .fld textarea{min-height:64px;resize:vertical;line-height:1.45}
.pj .fld .u{font-size:12.5px;color:var(--ink3);margin-top:2px}
.pj textarea.resp{width:100%;box-sizing:border-box;font:inherit;font-size:14.5px;min-height:120px;
  padding:9px 11px;border:1px solid var(--line);border-radius:10px;resize:vertical;line-height:1.45}
.pj .btn{border:0;border-radius:9px;background:var(--acc);color:#fff;padding:8px 16px;cursor:pointer;
  font:inherit;font-size:14.5px;font-weight:700}
.pj .btn.sec{background:var(--surf);color:var(--ink);border:1px solid var(--line);font-weight:600}
.pj .btn:disabled{opacity:.45;cursor:default}
.pj .msg{font-size:13.5px;color:var(--ink3);margin:8px 0 0}
.pj .msg.ok{color:#128a53;font-weight:600}
.pj .msg.warn{color:var(--warn);font-weight:600}
.pj .nav{display:flex;justify-content:space-between;gap:10px;margin:6px 0 0}
.pj .pctl{border:1px solid var(--line);border-radius:12px;overflow:hidden;margin:6px 0 6px;background:#20262e}
.pj .pctl-head{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;
  padding:8px 10px;background:#20262e}
.pj .psw{display:flex;border:1.5px solid #4a5462;border-radius:8px;overflow:hidden}
.pj .psw button{border:0;background:transparent;color:#aeb9c6;padding:6px 13px;cursor:pointer;font:inherit;font-size:13.5px}
.pj .psw button.on{background:var(--acc);color:#fff}
.pj .b-cp{border:0;border-radius:8px;background:var(--acc);color:#fff;padding:7px 14px;cursor:pointer;font:inherit;font-size:13.5px}
.pj .b-cp.done{background:#0f7a46}
.pj .pctl pre{margin:0;padding:14px 16px;background:#20262e;color:#e7edf3;border-radius:0;
  font:13px/1.65 var(--mono);white-space:pre-wrap;word-break:break-word;max-height:360px;overflow:auto}
.pj .phx{background:#ffedaa;color:#8a1c4a;border-radius:3px;padding:0 3px;font-weight:600}
.pj .phv{background:rgba(32,186,114,.18);color:#8ee7b8;border-radius:3px;padding:0 2px}
.pj .pstate{font-size:12.5px;color:#aeb9c6;padding:8px 16px 10px;background:#20262e;margin:0;border-top:1px solid #313a46}
.pj .vis{background:var(--surf);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:10px 0 0}
.pj .vis svg{width:100%;height:auto;display:block}
.pj .vis .cap{font-size:13.5px;color:var(--ink3);margin:8px 0 0}
.pj .kpi{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:10px 0}
@media(max-width:720px){.pj .kpi{grid-template-columns:1fr 1fr}}
.pj .kpi>div{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 12px}
.pj .kpi .l{font-size:12.5px;color:var(--ink3)}
.pj .kpi .v{font-size:20px;font-weight:800;margin-top:3px;line-height:1.15}
.pj .kpi .v.neg{color:var(--warn)}
.pj .kpi .s{font-size:12.5px;color:var(--ink3);margin-top:2px}
.pj .rows{display:grid;grid-template-columns:130px 1fr;gap:6px 12px;font-size:15px;margin:0}
.pj .rows dt{font-weight:800;color:var(--ink2);font-size:13px;text-transform:uppercase;letter-spacing:.04em;padding-top:3px}
.pj .rows dd{margin:0}
.pj .rows dd.fact{border-left:3px solid #1b5fa8;padding-left:10px}
.pj .rows dd.interp{border-left:3px solid #b05c1c;padding-left:10px}
.pj .rows dd.hyp{border-left:3px solid var(--acc);padding-left:10px}
.pj .rows dd.refute{border-left:3px solid var(--warn);padding-left:10px}
.pj .chip-st{display:inline-block;font-size:12px;font-weight:700;border-radius:999px;padding:1px 9px}
.pj .st-есть{background:#e3f2ea;color:#0f7a46}
.pj .st-частично{background:#fdeee3;color:#b05c1c}
.pj .st-нет{background:rgba(228,87,46,.12);color:var(--warn)}
.pj table.sm{font-size:14px}
.pj table.sm td{white-space:nowrap}
.pj #mtab td,.pj #dtab td{white-space:normal}
.pj table.sm input{width:82px;font:inherit;font-size:14px;padding:4px 6px;border:1px solid var(--line);border-radius:6px}
.pj .flip{color:var(--warn);font-weight:700}
.pj .keep{color:#0f7a46;font-weight:700}
.pj .slide{aspect-ratio:16/9;background:#fff;border:1px solid var(--line);border-radius:12px;padding:5% 6%;
  display:flex;flex-direction:column;gap:2.2%;box-shadow:0 8px 24px rgba(46,54,65,.08)}
.pj .slide .h{font-size:clamp(16px,2.6vw,26px);font-weight:800;line-height:1.15;color:var(--ink);border-bottom:3px solid var(--acc);padding-bottom:2%}
.pj .slide .r{display:grid;grid-template-columns:110px 1fr;gap:10px;font-size:clamp(11px,1.5vw,15.5px);line-height:1.35}
.pj .slide .r b{color:var(--acc);text-transform:uppercase;font-size:.78em;letter-spacing:.06em;padding-top:.2em}
.pj .letter{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px 22px;font-size:15.5px}
.pj .letter p{margin:0 0 12px}
.pj .letter b{color:var(--ink)}
.pj .ff{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 14px;font-size:15.5px;overflow-x:auto}
.pj .ff b{color:#0f7a46}
.pj .links{font-size:14px;color:var(--ink3);margin:0 0 12px}
.pj .links a{margin-right:10px;white-space:nowrap}
.pj .hint{font-size:13.5px;color:var(--ink3);margin:0 0 8px}
.pj details.raw{margin:8px 0 0;font-size:13.5px}
.pj details.raw summary{cursor:pointer;color:var(--ink3)}
.pj details.raw table{font-size:13px;margin-top:6px}
.pj details.raw td,.pj details.raw th{padding:4px 8px;white-space:nowrap}
</style>
"""


def _пром(n):
    return (f'<div class="pctl"><div class="pctl-head">'
            f'<div class="psw" role="group" aria-label="Режим промпта">'
            f'<button type="button" data-sw="tpl" data-n="{n}">Шаблон</button>'
            f'<button type="button" class="on" data-sw="fill" data-n="{n}">Заполненный</button></div>'
            f'<button class="b-cp" type="button" data-copy="{n}">Копировать заполненный промпт</button></div>'
            f'<pre id="pv{n}"></pre><p class="pstate" id="ps{n}"></p></div>')


def _ответ(n, подсказка):
    return (f'<div class="part"><h4><span class="n">3</span>Ответ ассистента</h4>'
            f'<p class="hint">{подсказка}</p>'
            f'<textarea class="resp" id="resp{n}" data-bind="s{n}.resp" placeholder="Вставьте ответ ассистента целиком"></textarea>'
            f'<div style="margin-top:8px"><button class="btn" type="button" data-parse="{n}">Разобрать ответ</button>'
            f'<span class="msg" id="pm{n}" style="display:inline-block;margin:0 0 0 12px"></span></div></div>')


def _нав(n):
    prev = f'<button class="btn sec" type="button" data-go="{n-1}">← Шаг {n-1}</button>' if n > 1 else '<span></span>'
    nxt = (f'<button class="btn" type="button" data-go="{n+1}">Дальше: шаг {n+1} →</button>' if n < 9
           else '<button class="btn" type="button" id="bExport">Скачать проект (Markdown)</button>')
    return f'<div class="nav">{prev}{nxt}</div>'


def _поле(bind, метка, тип="input", подпись="", attrs=""):
    if тип == "textarea":
        ctl = f'<textarea data-bind="{bind}" {attrs}></textarea>'
    elif тип == "select":
        ctl = f'<select data-bind="{bind}" {attrs}></select>'
    else:
        ctl = f'<input data-bind="{bind}" {attrs}>'
    u = f'<div class="u">{подпись}</div>' if подпись else ""
    return f'<div class="fld"><label>{метка}</label>{ctl}{u}</div>'


HTML = f"""
<header><div class="wrap">
  <div class="eyebrow">Тренажёр · сквозная практика</div>
  <h1>Проект от проблемы до эффекта</h1>
  <p class="lead">Девять коротких шагов по каркасу проекта: проблема, метрики, данные,
     анализ, вывод, финансовая модель, слайд «Эффект для бизнеса» и письмо команде.
     На каждом шаге страница собирает промпт из ваших полей, ассистент отвечает,
     ответ вставляется обратно — и результат переходит на следующий шаг сам.
     Все расчёты выполняет страница, ассистент только формулирует и выбирает.</p>
  <div class="meta">
    <span class="chip">Шагов: <b>9</b></span>
    <span class="chip">Время: <b>45–60 минут</b></span>
    <span class="chip">Нужен: <b>ассистент в браузере</b></span>
    <span class="chip">Итог: <b>каркас, слайд, письмо</b></span>
  </div>
</div></header>

<section><div class="wrap pj">
<div class="card acc">
<h4>Как проходить</h4>
<ol style="margin:0;padding-left:22px">
<li><b>Заполните поля</b> шага. В кейсах курса они уже заполнены — исправляйте, что хотите.</li>
<li><b>Скопируйте заполненный промпт</b> кнопкой и вставьте в новый чат ассистента.
    Если в ассистенте есть выбор модели — выбирайте самую сильную из доступных.</li>
<li><b>Вставьте ответ</b> ассистента целиком в поле «Ответ ассистента» и нажмите «Разобрать ответ».
    Поля результата заполнятся сами; их можно править вручную.</li>
<li><b>Проверьте результат</b> на графике или в таблице и переходите дальше. Заполненный каркас
    вверху растёт с каждым шагом.</li>
</ol>
<p class="sub" style="margin:10px 0 0">Всё введённое сохраняется в вашем браузере отдельно для каждого кейса.
Если ответ не разобрался — впишите результат в поля вручную: разбор нужен для удобства, а не для проверки.</p>
</div>

<h3>Кейс</h3>
<div class="tabs" id="tabs"></div>
<p class="hint" id="caseNote"></p>

<h3>Каркас проекта</h3>
<div class="frame" id="frame"></div>
<p class="hint">Семь элементов каркаса и письмо. Ячейка заполняется, когда пройден её шаг; нажатие открывает шаг.</p>

<div class="stepper" id="stepper"></div>

<!-- ─── Шаг 1 ─────────────────────────────────────────────────────────── -->
<div class="step" id="st1">
<div class="sthead"><span class="snum">Шаг 1</span><h3>Объект изменений и проблема</h3><span class="sst" id="ss1"></span></div>
<p class="sub">Объект — то, что можно изменить своим решением: продукт, процесс или инициатива.
Проблема сформулирована, если в ней есть показатель с числом, источник, целевой уровень и то, что меняем.</p>
<p class="links">Из курса: <a href="longread_project.html">Каркас проекта</a>
<a href="longread_project.html#problema">Формулировка проблемы</a>
<a href="longread_effect.html">Повторение основ</a></p>
<div class="part"><h4><span class="n">1</span>Заполните</h4>
<div class="grid">
{_поле("s1.axis", "Ось объекта", "select")}
{_поле("s1.object", "Объект изменений", attrs='placeholder="например: накопительный счёт для физических лиц"')}
</div>
{_поле("s1.observation", "Что вы наблюдаете — одной фразой", "textarea")}
{_поле("s1.action_in", "Что вы предполагаете изменить", attrs='placeholder="одно действие, которое в силах объекта изменений"')}
<div class="grid">
{_поле("s1.source", "Откуда данные", attrs='placeholder="витрина, выгрузка, отчёт"')}
{_поле("s1.focus", "Показатель, который беспокоит", "select")}
</div>
<div id="tblBox">{_поле("s1.tableText", "Небольшая таблица данных", "textarea", "Первая строка — названия столбцов, первый столбец — месяц или срез; разделитель — точка с запятой или табуляция (вставка из Excel). До 40 строк.", 'style="min-height:110px;font-family:var(--mono);font-size:13px"')}</div>
<details class="raw" id="tblView"><summary>Показать таблицу данных</summary><div class="scroll" id="tblHtml"></div></details>
<div class="vis" id="v1"></div>
</div>
<div class="part"><h4><span class="n">2</span>Промпт для ассистента</h4>{_пром(1)}</div>
{_ответ(1, "Ожидается пять строк: Проблема, Показатель, Источник, Целевое значение, Что меняем.")}
<div class="part"><h4><span class="n">4</span>Результат: проблема</h4>
{_поле("s1.problem", "Проблема", "textarea")}
<div class="grid">
{_поле("s1.metric", "Показатель")}
{_поле("s1.source2", "Источник")}
{_поле("s1.target", "Целевое значение")}
{_поле("s1.action", "Что меняем")}
</div>
<p class="hint" id="chk1"></p>
</div>
{_нав(1)}
</div>

<!-- ─── Шаг 2 ─────────────────────────────────────────────────────────── -->
<div class="step" id="st2">
<div class="sthead"><span class="snum">Шаг 2</span><h3>Метрики: результат и драйверы</h3><span class="sst" id="ss2"></span></div>
<p class="sub">Результат — запаздывающая метрика, по которой судят об итоге. Драйверы — опережающие:
наблюдаются раньше и на них действует изменение. Контрольная метрика не должна ухудшиться.</p>
<p class="links">Из курса: <a href="trainer_tree.html">Тренажёр «Дерево метрик»</a>
<a href="longread_metrics.html#tree">Опережающие и запаздывающие</a>
<a href="longread_project.html#metriki">Ключевые метрики проекта</a></p>
<div class="part"><h4><span class="n">1</span>Заполните</h4>
<p class="hint">Проблема и изменение берутся из шага 1. Показатели таблицы подставляются сами.</p>
{_поле("s2.other", "Другие показатели, которые подразделение может наблюдать", "textarea", "через точку с запятой; сюда попадают опережающие метрики, которых нет в таблице")}
</div>
<div class="part"><h4><span class="n">2</span>Промпт для ассистента</h4>{_пром(2)}</div>
{_ответ(2, "Ожидается четыре строки: Результат, Драйвер 1, Драйвер 2, Контрольная — поля через вертикальную черту.")}
<div class="part"><h4><span class="n">4</span>Результат: дерево метрик</h4>
<div class="scroll"><table class="sm"><thead><tr><th>Роль</th><th>Метрика</th><th>Единица</th><th>Частота</th><th>Пояснение</th></tr></thead>
<tbody id="mtab"></tbody></table></div>
<div class="vis" id="v2"></div>
</div>
{_нав(2)}
</div>

<!-- ─── Шаг 3 ─────────────────────────────────────────────────────────── -->
<div class="step" id="st3">
<div class="sthead"><span class="snum">Шаг 3</span><h3>Данные: что есть, чего нет</h3><span class="sst" id="ss3"></span></div>
<p class="sub">План по данным: для каждой метрики — собирается ли она сейчас, из какого источника,
как получить первое проверенное значение и через сколько. То, чего нет, помечается: это будущее допущение.</p>
<p class="links">Из курса: <a href="trainer_map.html">Тренажёр «Карта источников»</a>
<a href="longread_data.html">Роль данных</a>
<a href="longread_metrics.html#eco">Экономика данных</a></p>
<div class="part"><h4><span class="n">1</span>Заполните</h4>
{_поле("s3.sources", "Источники, которые есть у подразделения", "textarea", "система, что даёт, как часто обновляется; через точку с запятой")}
</div>
<div class="part"><h4><span class="n">2</span>Промпт для ассистента</h4>{_пром(3)}</div>
{_ответ(3, "Ожидается по одной строке на метрику: метрика | есть / частично / нет | источник | как получить | срок.")}
<div class="part"><h4><span class="n">4</span>Результат: план по данным</h4>
<div class="scroll"><table class="sm"><thead><tr><th>Метрика</th><th>Статус</th><th>Источник</th><th>Как получить</th><th>Срок</th></tr></thead>
<tbody id="dtab"></tbody></table></div>
<p class="hint" id="dmiss"></p>
</div>
{_нав(3)}
</div>

<!-- ─── Шаг 4 ─────────────────────────────────────────────────────────── -->
<div class="step" id="st4">
<div class="sthead"><span class="snum">Шаг 4</span><h3>Анализ на данных</h3><span class="sst" id="ss4"></span></div>
<p class="sub">Этот шаг без ассистента: расчёт выполняет страница. Связь двух показателей — коэффициент
корреляции и линия регрессии; динамика одного показателя — тренд и сравнение с тем же месяцем прошлого года.
Итог шага — текст с числами, который уходит ассистенту на следующем шаге.</p>
<p class="links">Из курса: <a href="theory_stats.html">Связь и причинность</a>
<a href="case_report.html">Мини-инструменты корреляций и трендов</a>
<a href="longread_math.html">Математические основы</a>
<a href="case_deviations.html">Анализ отклонений</a></p>
<div class="part"><h4><span class="n">1</span>Выберите расчёт</h4>
<div class="grid">
{_поле("s4.mode", "Вид анализа", "select")}
{_поле("s4.y", "Показатель результата", "select")}
</div>
<div id="xBox">{_поле("s4.x", "Показатель-драйвер (по горизонтали)", "select")}</div>
<div class="vis" id="v4"></div>
</div>
<div class="part"><h4><span class="n">2</span>Результат анализа</h4>
{_поле("s4.text", "Что показал расчёт (уходит ассистенту на шаге 5; можно дополнить)", "textarea", attrs='style="min-height:96px"')}
{_поле("s4.tool", "Инструмент, которым расчёт повторяется на следующей выгрузке", attrs='placeholder="мини-инструмент корреляций / таблица / тетрадь"')}
</div>
{_нав(4)}
</div>

<!-- ─── Шаг 5 ─────────────────────────────────────────────────────────── -->
<div class="step" id="st5">
<div class="sthead"><span class="snum">Шаг 5</span><h3>Вывод: факт, интерпретация, гипотеза</h3><span class="sst" id="ss5"></span></div>
<p class="sub">Факт — то, что показали числа. Интерпретация — возможное объяснение, помеченное как предположение.
Гипотеза — проверяемое утверждение «если …, то … изменится на … за …»; из неё берётся изменение показателя для финансовой модели.</p>
<p class="links">Из курса: <a href="longread.html">Ошибки вывода</a>
<a href="theory_stats.html">Связь и причинность</a>
<a href="longread_project.html#vyvod">Вывод в каркасе проекта</a></p>
<div class="part"><h4><span class="n">1</span>Проверьте вход</h4>
<p class="hint">Проблема и изменение — из шага 1, результат анализа — из шага 4. Менять здесь ничего не нужно.</p>
<p id="in5" style="font-size:14.5px;margin:0"></p>
</div>
<div class="part"><h4><span class="n">2</span>Промпт для ассистента</h4>{_пром(5)}</div>
{_ответ(5, "Ожидается четыре строки: Факт, Интерпретация, Гипотеза, Что опровергнет.")}
<div class="part"><h4><span class="n">4</span>Результат: вывод</h4>
{_поле("s5.fact", "Факт", "textarea", attrs='style="min-height:48px"')}
{_поле("s5.interp", "Интерпретация", "textarea", attrs='style="min-height:48px"')}
{_поле("s5.hyp", "Гипотеза", "textarea", attrs='style="min-height:48px"')}
{_поле("s5.refute", "Что опровергнет гипотезу", "textarea", attrs='style="min-height:48px"')}
<div class="vis" id="v5"></div>
</div>
{_нав(5)}
</div>

<!-- ─── Шаг 6 ─────────────────────────────────────────────────────────── -->
<div class="step" id="st6">
<div class="sthead"><span class="snum">Шаг 6</span><h3>Множители эффекта и допущения</h3><span class="sst" id="ss6"></span></div>
<p class="sub">Эффект в месяц = изменение показателя × объём × стоимость единицы. Изменение берётся
из гипотезы, объём — из данных, стоимость — из финансовой модели. Всё, что не подтверждено данными, — допущение
с пессимистичным и оптимистичным значением: их задаёт ассистент, а проверяет шаг 7.</p>
<p class="links">Из курса: <a href="longread_finmodel.html#formula">Формула эффекта</a>
<a href="longread_finmodel.html#dopushcheniya">Данные и допущения</a>
<a href="longread_effect.html">Повторение основ: примеры</a></p>
<div class="part"><h4><span class="n">1</span>Заполните множители</h4>
<div class="grid">
{_поле("s6.delta", "Изменение показателя в месяц")}
{_поле("s6.udelta", "Единица изменения", attrs='placeholder="предотвращённых закрытий в месяц"')}
{_поле("s6.volume", "Объём")}
{_поле("s6.uvolume", "Единица объёма", attrs='placeholder="единиц, к которым применяется изменение"')}
{_поле("s6.price", "Стоимость единицы, руб. в месяц")}
{_поле("s6.uprice", "Как получена стоимость", attrs='placeholder="остаток × маржа ÷ 12"')}
{_поле("s6.keep", "Срок сохранения эффекта, мес.")}
{_поле("s6.kind", "Тип эффекта", "select")}
</div>
<div class="grid">
{_поле("s6.sdelta", "Откуда изменение", attrs='placeholder="гипотеза (допущение)"')}
{_поле("s6.svolume", "Откуда объём", attrs='placeholder="данные выгрузки"')}
{_поле("s6.sprice", "Откуда стоимость", attrs='placeholder="допущение по тарифу"')}
{_поле("s6.skeep", "Откуда срок сохранения", attrs='placeholder="допущение"')}
</div>
<div class="ff" id="v6f"></div>
</div>
<div class="part"><h4><span class="n">2</span>Промпт для ассистента</h4>{_пром(6)}</div>
{_ответ(6, "Ожидается четыре строки: Изменение показателя, Объём, Стоимость единицы, Срок сохранения — базовое | пессимистичное | оптимистичное | данные или допущение | обоснование.")}
<div class="part"><h4><span class="n">4</span>Результат: допущения</h4>
<div class="scroll"><table class="sm"><thead><tr><th>Множитель</th><th>Базовое</th><th>Пессимистичное</th><th>Оптимистичное</th><th>Природа</th><th>Обоснование</th></tr></thead>
<tbody id="atab"></tbody></table></div>
<p class="hint">Значения затрат в чувствительность добавляются на шаге 7. Числа можно править прямо в таблице.</p>
</div>
{_нав(6)}
</div>

<!-- ─── Шаг 7 ─────────────────────────────────────────────────────────── -->
<div class="step" id="st7">
<div class="sthead"><span class="snum">Шаг 7</span><h3>Поток эффекта, окупаемость и чувствительность</h3><span class="sst" id="ss7"></span></div>
<p class="sub">Расчёт страницы: эффект разворачивается по месяцам с выходом на уровень и сроком сохранения,
затраты вычитаются, поток дисконтируется по ставке. Каждое допущение по очереди ставится в пессимистичное
и оптимистичное значение — видно, какое из них меняет вывод.</p>
<p class="links">Из курса: <a href="trainer_effect.html">Тренажёр «Финансовая модель эффекта»</a>
<a href="longread_finmodel.html#potok">Поток эффекта во времени</a>
<a href="longread_finmodel.html#npv">NPV и правило принятия</a>
<a href="longread_finmodel.html#chuvstvitelnost">Проверка чувствительности</a></p>
<div class="part"><h4><span class="n">1</span>Затраты и горизонт</h4>
<div class="grid">
{_поле("s7.ramp", "Выход на полный уровень, мес.")}
{_поле("s7.horizon", "Горизонт расчёта, мес.")}
{_поле("s7.capex", "Единовременные затраты, руб.")}
{_поле("s7.opex", "Ежемесячные затраты, руб.")}
{_поле("s7.rate", "Ставка дисконтирования, % годовых")}
</div>
<div class="grid">
{_поле("s7.capex_p", "Затраты единовременные: пессимистично / оптимистично", attrs='placeholder="900000 / 450000"')}
{_поле("s7.opex_p", "Затраты ежемесячные: пессимистично / оптимистично", attrs='placeholder="80000 / 35000"')}
</div>
</div>
<div class="part"><h4><span class="n">2</span>Результат: поток и окупаемость</h4>
<div class="kpi">
<div><div class="l">Эффект в месяц</div><div class="v" id="k-full"></div><div class="s" id="k-full-s"></div></div>
<div><div class="l">Доход за первый год</div><div class="v" id="k-y1"></div><div class="s" id="k-y1-s"></div></div>
<div><div class="l">Окупаемость</div><div class="v" id="k-pb"></div><div class="s" id="k-pb-s"></div></div>
<div><div class="l">NPV за горизонт</div><div class="v" id="k-npv"></div><div class="s" id="k-npv-s"></div></div>
</div>
<div class="vis" id="v7"></div>
<p id="verdict7" style="font-weight:700;margin:10px 0 0"></p>
</div>
<div class="part"><h4><span class="n">3</span>Чувствительность</h4>
<div class="scroll"><table class="sm"><thead><tr><th>Допущение</th><th>Базовое</th><th>Пессимистичное</th><th>NPV</th><th>Оптимистичное</th><th>NPV</th><th>Вывод</th></tr></thead>
<tbody id="stab"></tbody></table></div>
<div class="vis" id="v7t"></div>
<p id="sens7" style="font-size:14.5px;margin:10px 0 0"></p>
{_поле("s7.text", "Текст расчёта (уходит ассистенту на шаге 8)", "textarea", attrs='style="min-height:96px;margin-top:10px"')}
</div>
{_нав(7)}
</div>

<!-- ─── Шаг 8 ─────────────────────────────────────────────────────────── -->
<div class="step" id="st8">
<div class="sthead"><span class="snum">Шаг 8</span><h3>Слайд «Эффект для бизнеса»</h3><span class="sst" id="ss8"></span></div>
<p class="sub">Один слайд, который читается без ведущего: предмет в заголовке, формула с числами,
результат, главное допущение и первое действие. Числа — только из расчёта шага 7.</p>
<p class="links">Из курса: <a href="longread_project.html#prezentaciya">Структура презентации проекта</a>
<a href="longread_finmodel.html#oshibki">Типичные ошибки финансовой модели</a></p>
<div class="part"><h4><span class="n">1</span>Проверьте вход</h4>
<p class="hint">Проблема — из шага 1, гипотеза — из шага 5, расчёт — из шага 7.</p>
<p id="in8" style="font-size:14.5px;margin:0"></p>
</div>
<div class="part"><h4><span class="n">2</span>Промпт для ассистента</h4>{_пром(8)}</div>
{_ответ(8, "Ожидается пять строк: Заголовок, Формула, Результат, Риск, Действие.")}
<div class="part"><h4><span class="n">4</span>Результат: слайд</h4>
{_поле("s8.title", "Заголовок")}
{_поле("s8.formula", "Формула", "textarea", attrs='style="min-height:44px"')}
{_поле("s8.result", "Результат", "textarea", attrs='style="min-height:44px"')}
{_поле("s8.risk", "Риск", "textarea", attrs='style="min-height:44px"')}
{_поле("s8.action", "Действие", "textarea", attrs='style="min-height:44px"')}
<div class="slide" id="v8"></div>
<p class="hint" style="margin-top:8px">Текст слайда переносится в любой редактор презентаций: заголовок и четыре строки.</p>
</div>
{_нав(8)}
</div>

<!-- ─── Шаг 9 ─────────────────────────────────────────────────────────── -->
<div class="step" id="st9">
<div class="sthead"><span class="snum">Шаг 9</span><h3>Письмо команде</h3><span class="sst" id="ss9"></span></div>
<p class="sub">Итоговый артефакт: пять абзацев с решениями — что меняем и почему, по какому показателю судим,
какие данные начинаем собирать, первое действие, когда пересматриваем. Расчёт остаётся в презентации.</p>
<p class="links">Из курса: <a href="longread_project.html#pismo">Письмо команде: структура и пример</a>
<a href="practice/4.1_каркас_проекта/4.1.2_шаблон_письма_команде.md.html">Шаблон письма</a></p>
<div class="part"><h4><span class="n">1</span>Проверьте вход</h4>
<p class="hint">Всё собрано с предыдущих шагов; данные, которых нет, — из шага 3.</p>
<p id="in9" style="font-size:14.5px;margin:0"></p>
</div>
<div class="part"><h4><span class="n">2</span>Промпт для ассистента</h4>{_пром(9)}</div>
{_ответ(9, "Ожидается пять абзацев, каждый начинается с названия раздела и двоеточия.")}
<div class="part"><h4><span class="n">4</span>Результат: письмо</h4>
<div class="letter" id="v9"></div>
<div style="margin-top:10px;display:flex;gap:10px;flex-wrap:wrap">
<button class="btn sec" type="button" id="bCopyLetter">Копировать письмо</button>
<button class="btn sec" type="button" id="bCopyMd">Копировать весь проект</button>
<button class="btn sec" type="button" id="bClear">Очистить кейс</button>
<span class="msg" id="expMsg"></span></div>
</div>
{_нав(9)}
</div>

</div></section>

<footer><div class="wrap">
  Аналитика 360 · материалы практической части. Расчёты выполняются в вашем браузере,
  данные никуда не отправляются. Введённое сохраняется в браузере отдельно для каждого кейса.
</div></footer>
"""

UI = r"""
<script>
(function(){
var C=window.ProjectCore, P=__PRESETS__;
var $=function(id){return document.getElementById(id)};
var esc=function(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')};
var cur='savings', st=null, pmode={};
var AXES=['продукт','процесс','бизнес-инициатива'];
var ROLE={result:'Результат',d1:'Драйвер 1',d2:'Драйвер 2',control:'Контрольная'};
var ANAME={delta:'Изменение показателя',volume:'Объём',price:'Стоимость единицы',keep:'Срок сохранения',capex:'Единовременные затраты',opex:'Ежемесячные затраты'};
var STEPS=['Объект и проблема','Метрики','Данные','Анализ','Вывод','Множители','Поток эффекта','Слайд','Письмо'];

// ── состояние ────────────────────────────────────────────────────────────
function blank(){return {step:1,
  s1:{axis:'продукт',object:'',observation:'',action_in:'',source:'',focus:'',tableText:'',resp:'',problem:'',metric:'',source2:'',target:'',action:''},
  s2:{other:'',resp:'',metrics:{}},
  s3:{sources:'',resp:'',rows:[]},
  s4:{mode:'pair',x:'',y:'',text:'',tool:''},
  s5:{resp:'',fact:'',interp:'',hyp:'',refute:''},
  s6:{delta:'',udelta:'',volume:'',uvolume:'',price:'',uprice:'',keep:'',kind:'cohort',sdelta:'',svolume:'',sprice:'',skeep:'',resp:'',ass:{}},
  s7:{ramp:3,horizon:24,capex:0,opex:0,rate:15,capex_p:'',opex_p:'',text:''},
  s8:{resp:'',title:'',formula:'',result:'',risk:'',action:''},
  s9:{resp:'',p1:'',p2:'',p3:'',p4:'',p5:''}}}
function fromPreset(id){
  var s=blank(); if(id==='custom')return s;
  var p=P[id];
  s.s1.axis=p.axis;s.s1.object=p.object;s.s1.observation=p.observation;s.s1.action_in=p.action;s.s1.source=p.source;s.s1.focus=p.focus;
  s.s1.tableText=C.tableText(p.table);
  s.s2.other=p.other_metrics;s.s3.sources=p.sources;
  s.s4.mode=p.analysis.mode;s.s4.x=p.analysis.x||'';s.s4.y=p.analysis.y;
  s.s4.tool=p.analysis.mode==='pair'?'мини-инструмент корреляций на месячной выгрузке':'мини-инструмент трендов на месячной выгрузке';
  var f=p.fin;
  s.s6.delta=f.delta;s.s6.udelta=f.delta_unit;s.s6.volume=f.volume;s.s6.uvolume=f.volume_unit;s.s6.price=f.price;s.s6.uprice=f.price_unit;
  s.s6.keep=f.keep;s.s6.kind=f.kind;s.s6.sdelta='гипотеза проекта (допущение)';s.s6.svolume='данные выгрузки';s.s6.sprice='допущение по тарифу';s.s6.skeep='допущение';
  s.s7.ramp=f.ramp;s.s7.horizon=f.horizon;s.s7.capex=f.capex;s.s7.opex=f.opex;s.s7.rate=Math.round(f.rate*1000)/10;
  var ap={};f.assumptions.forEach(function(a){ap[a.key]=a});
  if(ap.capex)s.s7.capex_p=ap.capex.pess+' / '+ap.capex.opt;
  if(ap.opex)s.s7.opex_p=ap.opex.pess+' / '+ap.opex.opt;
  return s;
}
function key(){return 'a360_project_'+cur}
function load(id){cur=id;var s=null;try{var raw=localStorage.getItem(key());if(raw)s=JSON.parse(raw)}catch(e){}
  st=s||fromPreset(id);
  // новые поля после обновления страницы
  var b=fromPreset(id);['s1','s2','s3','s4','s5','s6','s7','s8','s9'].forEach(function(k){if(!st[k])st[k]=b[k];for(var f in b[k])if(st[k][f]===undefined)st[k][f]=b[k][f]});
  if(!st.step)st.step=1;}
function save(){try{localStorage.setItem(key(),JSON.stringify(st))}catch(e){}}
function get(path){var p=path.split('.'),o=st;for(var i=0;i<p.length;i++){if(o==null)return '';o=o[p[i]]}return o==null?'':o}
function set(path,v){var p=path.split('.'),o=st;for(var i=0;i<p.length-1;i++){if(!o[p[i]])o[p[i]]={};o=o[p[i]]}o[p[p.length-1]]=v}
function table(){return C.parseTable(st.s1.tableText)}

// ── готовность шагов ──────────────────────────────────────────────────────
function done(n){
  switch(n){
    case 1:return !!(C.clean(st.s1.problem)&&C.clean(st.s1.action));
    case 2:return !!(st.s2.metrics.result&&st.s2.metrics.result.name);
    case 3:return (st.s3.rows||[]).length>0;
    case 4:return !!C.clean(st.s4.text);
    case 5:return !!C.clean(st.s5.hyp);
    case 6:return Object.keys(st.s6.ass||{}).some(function(k){var a=st.s6.ass[k];return a&&a.pess!==null&&a.opt!==null&&!isNaN(a.pess)&&!isNaN(a.opt)});
    case 7:return !!C.clean(st.s7.text)&&done(6);
    case 8:return !!C.clean(st.s8.title);
    case 9:return !!C.clean(st.s9.p1);
  }return false;
}

// ── общие элементы: кейс, каркас, шаги ────────────────────────────────────
function renderTabs(){
  var t=$('tabs');t.innerHTML='';
  var ids=Object.keys(P).concat(['custom']);
  ids.forEach(function(id){var b=document.createElement('button');b.type='button';b.dataset.id=id;
    b.textContent=id==='custom'?'Свой проект':P[id].tab;b.className=id===cur?'on':'';
    b.onclick=function(){save();load(id);renderAll()};t.appendChild(b)});
  $('caseNote').textContent=cur==='custom'
    ?'Свой проект: заполните поля шага 1 и вставьте небольшую таблицу данных — из выгрузки, отчёта или вручную. Ключевые числа удобно взять из своей карты источников и заготовки «Повторения основ».'
    :'Кейс курса: поля заполнены, таблица — учебная выгрузка папки практики, свёрнутая до '+P[cur].table.rows.length+' строк. '+P[cur].fin_note;
}
function frameText(i){
  var m=st.s2.metrics;
  switch(i){
    case 0:return st.s1.problem;
    case 1:return m.result&&m.result.name?('результат: '+m.result.name+(m.d1&&m.d1.name?'; драйверы: '+m.d1.name+(m.d2&&m.d2.name?', '+m.d2.name:''):'')):'';
    case 2:return (st.s3.rows||[]).length?st.s3.rows.map(function(r){return r.metric+' — '+r.status}).join('; '):'';
    case 3:return st.s4.tool;
    case 4:return st.s4.text;
    case 5:return st.s5.hyp?('гипотеза: '+st.s5.hyp):'';
    case 6:return st.s8.result||st.s7.text;
    case 7:return st.s9.p1;
  }return '';
}
var FRAME=[['Проблема',1],['Метрика',2],['Данные',3],['Инструмент',4],['Анализ',4],['Вывод',5],['Эффект',7],['Письмо',9]];
function renderFrame(){
  var f=$('frame');f.innerHTML='';
  FRAME.forEach(function(x,i){var d=document.createElement('div');var t=frameText(i);
    d.className=(t?'ok':'')+(x[1]===st.step?' cur':'');
    d.innerHTML='<div class="l">'+x[0]+'</div><div class="t">'+(t?esc(t):'шаг '+x[1])+'</div>';
    d.onclick=function(){go(x[1])};f.appendChild(d)});
}
function renderStepper(){
  var s=$('stepper');s.innerHTML='';
  STEPS.forEach(function(name,i){var n=i+1,b=document.createElement('button');b.type='button';
    b.className=(done(n)?'ok ':'')+(n===st.step?'cur':'');
    b.innerHTML='<b>'+(done(n)?'✓ ':'')+'Шаг '+n+'</b>'+esc(name);b.onclick=function(){go(n)};s.appendChild(b)});
  for(var n=1;n<=9;n++){var e=$('ss'+n);if(e){e.textContent=done(n)?'готово':'не пройден';e.className='sst'+(done(n)?' ok':'')}}
}
function go(n){st.step=n;save();
  for(var i=1;i<=9;i++){var e=$('st'+i);e.className='step'+(i===n?' on':'')}
  renderStep(n);renderFrame();renderStepper();
  var top=$('stepper').getBoundingClientRect().top+window.pageYOffset-12;
  if(Math.abs(window.pageYOffset-top)>40)window.scrollTo(0,top);
}

// ── поля ↔ состояние ─────────────────────────────────────────────────────
function fillInputs(scope){
  var els=(scope||document).querySelectorAll('[data-bind]');
  Array.prototype.forEach.call(els,function(el){var v=get(el.dataset.bind);
    if(el.tagName==='SELECT'){if(String(v)!==el.value)el.value=String(v)}else if(String(el.value)!==String(v))el.value=v});
}
function options(sel,list,val){sel.innerHTML=list.map(function(o){var v=typeof o==='string'?o:o[0],l=typeof o==='string'?o:o[1];
  return '<option value="'+esc(v)+'"'+(String(v)===String(val)?' selected':'')+'>'+esc(l)+'</option>'}).join('')}
document.addEventListener('input',function(e){var el=e.target;if(!el.dataset||!el.dataset.bind)return;
  set(el.dataset.bind,el.value);save();
  var n=+el.dataset.bind.charAt(1);
  if(el.dataset.bind==='s6.'+'ass')return;
  onChange(n,el.dataset.bind);
});
document.addEventListener('change',function(e){var el=e.target;if(!el.dataset||!el.dataset.bind||el.tagName!=='SELECT')return;
  set(el.dataset.bind,el.value);save();onChange(+el.dataset.bind.charAt(1),el.dataset.bind)});
function onChange(n,bind){
  if(bind==='s1.tableText'||bind==='s1.focus'){renderTableView();renderV1()}
  if(n===1){renderPrompt(1);renderFrame();renderStepper();renderChk1();if(bind==='s1.action_in'&&!C.clean(st.s1.action)){st.s1.action=st.s1.action_in;save();fillInputs($('st1'))}}
  if(n===2){renderPrompt(2)}
  if(n===3){renderPrompt(3)}
  if(n===4){if(bind!=='s4.text'&&bind!=='s4.tool')computeAnalysis();renderFrame();renderStepper()}
  if(n===5){renderV5();renderFrame();renderStepper()}
  if(n===6){renderV6f();renderPrompt(6)}
  if(n===7){renderS7()}
  if(n===8){renderV8();renderFrame();renderStepper()}
  if(n===9){renderV9();renderFrame();renderStepper()}
  if(bind.indexOf('resp')<0&&n!==1&&n!==4)renderStepper();
}

// ── промпты ──────────────────────────────────────────────────────────────
function metricsLines(){var m=st.s2.metrics;return ['result','d1','d2','control'].filter(function(k){return m[k]&&m[k].name})
  .map(function(k){return '- '+m[k].name+' ('+C.or(m[k].unit,'—')+', '+C.or(m[k].freq,'—')+') — '+ROLE[k].replace(/ \d$/,'').toLowerCase()}).join('\n')}
function missingText(){return (st.s3.rows||[]).filter(function(r){return r.status!=='есть'}).map(function(r){return r.metric+' ('+r.status+': '+r.source+')'}).join('; ')||'нет'}
function promptVals(n){
  var t=table(),m=st.s2.metrics;
  switch(n){
    case 1:return {axis:st.s1.axis,object:st.s1.object,observation:st.s1.observation,action_in:st.s1.action_in,source:st.s1.source,table:t?C.tableText(t):'',focus:st.s1.focus,facts:facts1(t)};
    case 2:return {problem:st.s1.problem,action:st.s1.action,columns:t?C.numericCols(t).join(', '):'',other:st.s2.other};
    case 3:return {metrics:metricsLines(),sources:st.s3.sources,columns:t?C.numericCols(t).join(', '):''};
    case 5:var an=currentAnalysis();return {problem:st.s1.problem,action:st.s1.action,analysis:st.s4.text,n:an?String(an.n):(t?String(t.rows.length):'')};
    case 6:return {problem:st.s1.problem,hyp:st.s5.hyp,
      fdelta:C.fmtv(C.num(st.s6.delta)),udelta:st.s6.udelta,sdelta:st.s6.sdelta,
      fvolume:C.fmtv(C.num(st.s6.volume)),uvolume:st.s6.uvolume,svolume:st.s6.svolume,
      fprice:C.fmtv(C.num(st.s6.price)),uprice:st.s6.uprice,sprice:st.s6.sprice,
      fkeep:C.fmtv(C.num(st.s6.keep)),skeep:st.s6.skeep};
    case 8:return {problem:st.s1.problem,hyp:st.s5.hyp,effect:st.s7.text};
    case 9:return {problem:st.s1.problem,action:st.s1.action,result:m.result?m.result.name:'',target:st.s1.target,
      control:m.control?m.control.name:'',missing:missingText(),hyp:st.s5.hyp,refute:st.s5.refute,
      seffect:st.s8.result,risk:st.s8.risk,first:st.s8.action};
  }return {};
}
function facts1(t){return C.facts1(t,st.s1.focus)}
var ptext={};
function renderPrompt(n){
  var pv=$('pv'+n);if(!pv)return;
  var segs=C.PROMPTS['s'+n],vals=promptVals(n),mode=pmode[n]||'fill';
  var r=C.fillPrompt(segs,vals,mode);ptext[n]=r.text;
  pv.innerHTML=r.parts.map(function(p){return p.t!==undefined?esc(p.t):p.ph!==undefined?'<span class="phx">'+esc(p.ph)+'</span>':'<span class="phv">'+esc(p.v)+'</span>'}).join('');
  var keys=C.promptKeys(segs),n0=keys.filter(function(k){return C.clean(vals[k])!==''}).length;
  $('ps'+n).textContent=mode==='tpl'?'Показан шаблон: жёлтые выражения в [скобках] заменяются вашими данными.'
    :(n0===keys.length?'Все '+keys.length+' полей подставлены — промпт готов для ассистента.'
      :'Подставлено '+n0+' из '+keys.length+' полей; незаполненные скопируются шаблонными выражениями в [скобках]'+(n0<keys.length&&n>1?' — вернитесь к предыдущим шагам':'')+'.');
  var b=document.querySelector('[data-copy="'+n+'"]');if(b&&!b.classList.contains('done'))b.textContent=mode==='tpl'?'Копировать шаблон':'Копировать заполненный промпт';
}
function copyText(txt,btn,lbl){
  function done(){btn.textContent='Скопировано';btn.classList.add('done');setTimeout(function(){btn.classList.remove('done');btn.textContent=lbl},1800)}
  function fb(){var a=document.createElement('textarea');a.value=txt;a.style.position='fixed';a.style.opacity=0;document.body.appendChild(a);a.select();
    try{document.execCommand('copy');done()}catch(_e){btn.textContent='Выделите вручную'}document.body.removeChild(a)}
  if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(txt).then(done,fb)}else{fb()}
}

// ── разбор ответов ───────────────────────────────────────────────────────
function parse(n){
  var txt=$('resp'+n).value,msg=$('pm'+n),r;
  function ok(f,t){msg.textContent='Разобрано: '+f+' из '+t+(f<t?' — остальное впишите вручную':'');msg.className='msg '+(f?'ok':'warn');if(!f)msg.textContent='Не удалось разобрать: проверьте, что вставлен ответ целиком, или заполните поля вручную'}
  switch(n){
    case 1:r=C.parseS1(txt);var f=r.fields;if(f.problem!==undefined)st.s1.problem=f.problem;if(f.metric)st.s1.metric=f.metric;if(f.source)st.s1.source2=f.source;if(f.target)st.s1.target=f.target;if(f.action)st.s1.action=f.action;ok(r.found,r.total);fillInputs($('st1'));renderChk1();break;
    case 2:r=C.parseS2(txt);if(r.found){st.s2.metrics=r.metrics}ok(r.found,r.total);renderMtab();renderV2();break;
    case 3:r=C.parseS3(txt);if(r.found){st.s3.rows=r.rows}msg.textContent=r.found?'Разобрано строк: '+r.found:'Не удалось разобрать: нужны строки с полями через вертикальную черту';msg.className='msg '+(r.found?'ok':'warn');renderDtab();break;
    case 5:r=C.parseS5(txt);['fact','interp','hyp','refute'].forEach(function(k){if(r.fields[k]!==undefined)st.s5[k]=r.fields[k]});ok(r.found,r.total);fillInputs($('st5'));renderV5();break;
    case 6:r=C.parseS6(txt);if(r.found){var a=st.s6.ass||{};Object.keys(r.ass).forEach(function(k){a[k]=r.ass[k]});st.s6.ass=a}ok(r.found,r.total);renderAtab();break;
    case 8:r=C.parseS8(txt);['title','formula','result','risk','action'].forEach(function(k){if(r.fields[k]!==undefined)st.s8[k]=r.fields[k]});ok(r.found,r.total);fillInputs($('st8'));renderV8();break;
    case 9:r=C.parseS9(txt);['p1','p2','p3','p4','p5'].forEach(function(k){if(r.fields[k]!==undefined)st.s9[k]=r.fields[k]});ok(r.found,r.total);renderV9();break;
  }
  save();renderFrame();renderStepper();
  if(n===1)renderPrompt(2);if(n===2)renderPrompt(3);if(n===5)renderPrompt(6);if(n===6)renderS7();if(n===8)renderPrompt(9);
}

// ── графики ──────────────────────────────────────────────────────────────
function tx(x,y,t,fs,w,f,a,o){return '<text x="'+x+'" y="'+y+'" font-size="'+fs+'"'+(w?' font-weight="'+w+'"':'')+' fill="'+f+'"'+(a?' text-anchor="'+a+'"':'')+(o?' fill-opacity="'+o+'"':'')+'>'+esc(t)+'</text>'}
function seriesChart(lab,y,name,fit){
  var W=960,H=300,L=70,R=24,T=20,B=48,pw=W-L-R,ph=H-T-B,n=y.length,s=[];
  var mx=Math.max.apply(null,y),mn=Math.min.apply(null,y);if(mx===mn){mx+=1;mn-=1}
  var pad=(mx-mn)*0.1;var top=mx+pad,bot=Math.max(0,mn-pad);if(mn<0)bot=mn-pad;
  var X=function(i){return L+(n>1?pw*i/(n-1):pw/2)},Y=function(v){return T+ph*(top-v)/(top-bot)};
  s.push('<svg viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg" role="img" font-family="inherit">');
  var step=C.niceStep((top-bot)/5);
  for(var v=Math.ceil(bot/step)*step;v<=top;v+=step){s.push('<line x1="'+L+'" x2="'+(W-R)+'" y1="'+Y(v).toFixed(1)+'" y2="'+Y(v).toFixed(1)+'" stroke="#2E3641" stroke-opacity="0.1"/>');s.push(tx(L-8,Y(v)+4,C.fmtv(Math.round(v*100)/100),12,null,'#2E3641','end',0.7))}
  if(n<=12){var bw=pw/n*0.6;y.forEach(function(v,i){var x=X(i)-bw/2;s.push('<rect x="'+x.toFixed(1)+'" y="'+Y(v).toFixed(1)+'" width="'+bw.toFixed(1)+'" height="'+(Y(bot)-Y(v)).toFixed(1)+'" rx="4" fill="#20BA72" fill-opacity="0.65"/>');s.push(tx(X(i),Y(v)-6,C.fmtv(v),12,'700','#2E3641','middle'))})}
  else{var d='';y.forEach(function(v,i){d+=(i?'L':'M')+X(i).toFixed(1)+' '+Y(v).toFixed(1)+' '});s.push('<path d="'+d+'" fill="none" stroke="#159A5C" stroke-width="3"/>');
    y.forEach(function(v,i){s.push('<circle cx="'+X(i).toFixed(1)+'" cy="'+Y(v).toFixed(1)+'" r="3.2" fill="#159A5C"/>')})}
  if(fit&&n>2){s.push('<line x1="'+X(0)+'" x2="'+X(n-1)+'" y1="'+Y(fit.a).toFixed(1)+'" y2="'+Y(fit.a+fit.b*(n-1)).toFixed(1)+'" stroke="#D2564A" stroke-width="2" stroke-dasharray="6 5"/>')}
  var every=Math.max(1,Math.ceil(n/12));lab.forEach(function(l,i){if(i%every===0&&(n-1-i>=every/2||i===n-1)||i===n-1)s.push(tx(X(i),H-B+18,l,11.5,null,'#2E3641','middle',0.75))});
  s.push(tx(L,H-8,name,12.5,'700','#2E3641'));
  s.push('</svg>');return s.join('');
}
function scatterChart(an){
  var W=960,H=340,L=70,R=24,T=20,B=52,pw=W-L-R,ph=H-T-B,s=[];
  var xs=an.xs,ys=an.ys;var mxx=Math.max.apply(null,xs),mnx=Math.min.apply(null,xs),mxy=Math.max.apply(null,ys),mny=Math.min.apply(null,ys);
  if(mxx===mnx){mxx+=1;mnx-=1}if(mxy===mny){mxy+=1;mny-=1}
  var px=(mxx-mnx)*0.08,py=(mxy-mny)*0.12;mxx+=px;mnx-=px;mxy+=py;mny-=py;
  var X=function(v){return L+pw*(v-mnx)/(mxx-mnx)},Y=function(v){return T+ph*(mxy-v)/(mxy-mny)};
  s.push('<svg viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg" role="img" font-family="inherit">');
  var sy=C.niceStep((mxy-mny)/5);for(var v=Math.ceil(mny/sy)*sy;v<=mxy;v+=sy){s.push('<line x1="'+L+'" x2="'+(W-R)+'" y1="'+Y(v).toFixed(1)+'" y2="'+Y(v).toFixed(1)+'" stroke="#2E3641" stroke-opacity="0.1"/>');s.push(tx(L-8,Y(v)+4,C.fmtv(Math.round(v*100)/100),12,null,'#2E3641','end',0.7))}
  var sx=C.niceStep((mxx-mnx)/6);for(var u=Math.ceil(mnx/sx)*sx;u<=mxx;u+=sx){s.push(tx(X(u),H-B+18,C.fmtv(Math.round(u*100)/100),12,null,'#2E3641','middle',0.7))}
  var f=an.fit;s.push('<line x1="'+X(mnx).toFixed(1)+'" x2="'+X(mxx).toFixed(1)+'" y1="'+Y(f.a+f.b*mnx).toFixed(1)+'" y2="'+Y(f.a+f.b*mxx).toFixed(1)+'" stroke="#D2564A" stroke-width="2" stroke-dasharray="6 5"/>');
  xs.forEach(function(x,i){s.push('<circle cx="'+X(x).toFixed(1)+'" cy="'+Y(ys[i]).toFixed(1)+'" r="5" fill="#159A5C" fill-opacity="0.8"/>')});
  s.push(tx(W-R,H-B+38,an.x,12.5,'700','#2E3641','end'));s.push(tx(L,14,an.y,12.5,'700','#2E3641'));
  s.push(tx(W-R,T+16,'r = '+C.fr(an.r,2)+' · '+an.strength,14,'800',Math.abs(an.r)>=0.7?'#0f7a46':'#2E3641','end'));
  s.push('</svg>');return s.join('');
}
function yoyChart(yoy){
  if(!yoy.length)return '';
  var W=960,H=170,L=70,R=24,T=16,B=40,pw=W-L-R,ph=H-T-B,n=yoy.length,s=[];
  var mx=0;yoy.forEach(function(r){mx=Math.max(mx,Math.abs(r.d))});if(!mx)mx=0.1;mx*=1.15;
  var X=function(i){return L+pw*(i+0.5)/n},Y=function(v){return T+ph*(mx-v)/(2*mx)};
  s.push('<svg viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg" role="img" font-family="inherit">');
  s.push('<line x1="'+L+'" x2="'+(W-R)+'" y1="'+Y(0).toFixed(1)+'" y2="'+Y(0).toFixed(1)+'" stroke="#2E3641" stroke-opacity="0.45"/>');
  var bw=pw/n*0.6;yoy.forEach(function(r,i){var y0=Y(Math.max(0,r.d)),h=Math.abs(Y(0)-Y(r.d));
    s.push('<rect x="'+(X(i)-bw/2).toFixed(1)+'" y="'+y0.toFixed(1)+'" width="'+bw.toFixed(1)+'" height="'+h.toFixed(1)+'" rx="3" fill="'+(r.d<0?'#D2564A':'#20BA72')+'" fill-opacity="0.7"/>');
    if(i%Math.max(1,Math.ceil(n/12))===0||i===n-1)s.push(tx(X(i),H-B+16,r.label,11,null,'#2E3641','middle',0.75))});
  s.push(tx(L,H-6,'изменение к тому же месяцу прошлого года, %',12,'700','#2E3641'));
  s.push(tx(L-8,Y(mx)+4,'+'+C.fr(mx*100,0)+' %',11,null,'#2E3641','end',0.7));s.push(tx(L-8,Y(-mx)+4,'−'+C.fr(mx*100,0)+' %',11,null,'#2E3641','end',0.7));
  s.push('</svg>');return s.join('');
}
function flowChart(res){
  var rows=res.rows,W=960,H=320,L=78,R=48,T=18,B=44,pw=W-L-R,ph=H-T-B;
  var mx=0,mn=0;rows.forEach(function(r){mx=Math.max(mx,r.cum,r.income);mn=Math.min(mn,r.cum,-r.cost)});
  if(mx===mn){mx=1;mn=-1}var pad=(mx-mn)*0.08;mx+=pad;mn-=pad;
  var y=function(v){return T+ph*(mx-v)/(mx-mn)},x=function(t){return L+pw*t/res.horizon};
  var bw=Math.max(3,pw/(res.horizon+1)*0.34),s=[];
  s.push('<svg viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg" role="img" font-family="inherit">');
  var step=C.niceStep((mx-mn)/5);
  for(var v=Math.ceil(mn/step)*step;v<=mx;v+=step){s.push('<line x1="'+L+'" x2="'+(W-R)+'" y1="'+y(v).toFixed(1)+'" y2="'+y(v).toFixed(1)+'" stroke="#2E3641" stroke-opacity="'+(Math.abs(v)<1e-9?0.45:0.10)+'"/>');s.push(tx(L-8,y(v)+4,C.money(v).replace(' руб.',''),12,null,'#2E3641','end',0.7))}
  rows.forEach(function(r){var cx=x(r.t);
    if(r.income>0)s.push('<rect x="'+(cx-bw).toFixed(1)+'" y="'+y(r.income).toFixed(1)+'" width="'+bw.toFixed(1)+'" height="'+(y(0)-y(r.income)).toFixed(1)+'" fill="#20BA72" fill-opacity="0.55"/>');
    if(r.cost>0)s.push('<rect x="'+cx.toFixed(1)+'" y="'+y(0).toFixed(1)+'" width="'+bw.toFixed(1)+'" height="'+(y(-r.cost)-y(0)).toFixed(1)+'" fill="#2E3641" fill-opacity="0.35"/>')});
  var d='';rows.forEach(function(r,i){d+=(i?'L':'M')+x(r.t).toFixed(1)+' '+y(r.cum).toFixed(1)+' '});s.push('<path d="'+d+'" fill="none" stroke="#159A5C" stroke-width="3"/>');
  var dd='';rows.forEach(function(r,i){dd+=(i?'L':'M')+x(r.t).toFixed(1)+' '+y(r.cum_disc).toFixed(1)+' '});s.push('<path d="'+dd+'" fill="none" stroke="#159A5C" stroke-width="2" stroke-dasharray="6 5" stroke-opacity="0.8"/>');
  if(res.payback!==null){var px=x(res.payback);s.push('<line x1="'+px.toFixed(1)+'" x2="'+px.toFixed(1)+'" y1="'+T+'" y2="'+(T+ph)+'" stroke="#D2564A" stroke-width="1.5" stroke-dasharray="4 4"/>');s.push(tx(px+6,T+14,'окупаемость: месяц '+res.payback,13,'700','#D2564A'))}
  var ms=res.horizon>24?6:3;for(var t=0;t<=res.horizon;t+=ms)s.push(tx(x(t),H-B+18,String(t),12,null,'#2E3641','middle',0.7));
  s.push(tx(W-R+12,H-B+18,'мес.',12,null,'#2E3641','start',0.5));
  var ly=H-8;s.push('<rect x="'+L+'" y="'+(ly-10)+'" width="12" height="10" fill="#20BA72" fill-opacity="0.55"/>'+tx(L+18,ly,'доход в месяц',12.5,null,'#2E3641',null,0.8));
  s.push('<rect x="'+(L+130)+'" y="'+(ly-10)+'" width="12" height="10" fill="#2E3641" fill-opacity="0.35"/>'+tx(L+148,ly,'затраты',12.5,null,'#2E3641',null,0.8));
  s.push('<line x1="'+(L+230)+'" x2="'+(L+256)+'" y1="'+(ly-5)+'" y2="'+(ly-5)+'" stroke="#159A5C" stroke-width="3"/>'+tx(L+262,ly,'накопленный поток',12.5,null,'#2E3641',null,0.8));
  s.push('<line x1="'+(L+400)+'" x2="'+(L+426)+'" y1="'+(ly-5)+'" y2="'+(ly-5)+'" stroke="#159A5C" stroke-width="2" stroke-dasharray="6 5"/>'+tx(L+432,ly,'то же с дисконтированием (NPV на конце)',12.5,null,'#2E3641',null,0.8));
  s.push('</svg>');return s.join('');
}
function tornadoChart(sens,base){
  if(!sens.length)return '';
  var W=960,rowH=34,L=300,R=190,T=26,H=T+rowH*sens.length+14,pw=W-L-R,s=[];
  var mx=0;sens.forEach(function(r){mx=Math.max(mx,Math.abs(r.npv_pess-base),Math.abs(r.npv_opt-base))});if(mx===0)mx=1;
  var x0=L+pw/2,sc=(pw/2-8)/mx;
  s.push('<svg viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg" role="img" font-family="inherit">');
  s.push(tx(x0,16,'NPV при базовых значениях: '+C.money(base),12.5,'700','#2E3641','middle'));
  s.push('<line x1="'+x0+'" x2="'+x0+'" y1="'+T+'" y2="'+(H-10)+'" stroke="#2E3641" stroke-opacity="0.45"/>');
  sens.forEach(function(r,i){var y=T+i*rowH+6,h=rowH-12,dp=r.npv_pess-base,dop=r.npv_opt-base;
    s.push(tx(L-12,y+h/2+4,r.name,13.5,null,'#2E3641','end'));
    var xp=x0+Math.min(0,dp)*sc,wp=Math.abs(dp)*sc;s.push('<rect x="'+xp.toFixed(1)+'" y="'+y+'" width="'+wp.toFixed(1)+'" height="'+h+'" rx="4" fill="'+(r.flips?'#D2564A':'#2E3641')+'" fill-opacity="'+(r.flips?0.8:0.35)+'"/>');
    var xo=x0+Math.min(0,dop)*sc,wo=Math.abs(dop)*sc;s.push('<rect x="'+xo.toFixed(1)+'" y="'+y+'" width="'+wo.toFixed(1)+'" height="'+h+'" rx="4" fill="#20BA72" fill-opacity="0.6"/>');
    var xr=Math.max(xo+wo,xp+wp,x0)+8;s.push(tx(xr,y+h/2+4,C.money(r.npv_pess).replace(' руб.','')+' → '+C.money(r.npv_opt).replace(' руб.',''),11.5,null,'#2E3641','start',0.75))});
  s.push('</svg>');return s.join('');
}
function treeSvg(m){
  var W=960,H=250,s=[];
  var res=m.result&&m.result.name?m.result.name:'результат',d1=m.d1&&m.d1.name?m.d1.name:'драйвер 1',d2=m.d2&&m.d2.name?m.d2.name:'драйвер 2',ctl=m.control&&m.control.name?m.control.name:'';
  function box(x,y,w,h,t,sub,fill,stroke,dash){var o='<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="12" fill="'+fill+'" stroke="'+stroke+'" stroke-width="2"'+(dash?' stroke-dasharray="7 5"':'')+'/>';
    var lines=wrap(t,Math.floor(w/8.2));lines.forEach(function(l,i){o+=tx(x+w/2,y+26+i*17-(lines.length-1)*8,l,14,'700','#2E3641','middle')});
    if(sub)o+=tx(x+w/2,y+h-12,sub,11.5,null,'#2E3641','middle',0.65);return o}
  function wrap(t,n){var w=String(t).split(' '),out=[],cur='';w.forEach(function(x){if((cur+' '+x).trim().length>n){out.push(cur.trim());cur=x}else cur+=' '+x});if(cur.trim())out.push(cur.trim());return out.slice(0,3)}
  s.push('<svg viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg" role="img" font-family="inherit">');
  s.push('<defs><marker id="arrP" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0L10 5L0 10z" fill="#128a53"/></marker></defs>');
  s.push(box(40,40,260,76,d1,'опережающая · '+(m.d1&&m.d1.freq?m.d1.freq:''),'#e3f2ea','#20BA72'));
  s.push(box(40,150,260,76,d2,'опережающая · '+(m.d2&&m.d2.freq?m.d2.freq:''),'#e3f2ea','#20BA72'));
  s.push(box(400,95,260,80,res,'запаздывающая · '+(m.result&&m.result.freq?m.result.freq:''),'#e4ecf9','#1b5fa8'));
  s.push('<path d="M300 78 C 350 78, 350 135, 400 135" fill="none" stroke="#128a53" stroke-width="2.5" marker-end="url(#arrP)"/>');
  s.push('<path d="M300 188 C 350 188, 350 135, 400 135" fill="none" stroke="#128a53" stroke-width="2.5" marker-end="url(#arrP)"/>');
  s.push(tx(350,60,'предсказывает',11.5,null,'#128a53','middle'));
  if(ctl)s.push(box(700,95,230,80,ctl,'контрольная: не должна ухудшиться','#fff','#b05c1c',true));
  s.push('</svg>');return s.join('');
}

// ── шаг 1 ────────────────────────────────────────────────────────────────
function renderTableView(){
  var t=table(),box=$('tblHtml');
  if(!t){box.innerHTML='<p class="hint">Таблица не распознана: первая строка — названия столбцов, разделитель — точка с запятой или табуляция.</p>';return}
  var h='<table class="sm"><thead><tr>'+t.cols.map(function(c){return '<th>'+esc(c)+'</th>'}).join('')+'</tr></thead><tbody>';
  t.rows.forEach(function(r){h+='<tr>'+r.map(function(c){return '<td>'+esc(c)+'</td>'}).join('')+'</tr>'});
  box.innerHTML=h+'</tbody></table>';
  var sel=document.querySelector('[data-bind="s1.focus"]'),cols=C.numericCols(t);
  if(cols.indexOf(st.s1.focus)<0){st.s1.focus=cols[0]||'';save()}
  options(sel,cols,st.s1.focus);
}
function renderV1(){
  var t=table(),v=$('v1');
  if(!t||!st.s1.focus){v.innerHTML='<p class="hint" style="margin:0">График показателя появится, когда есть таблица и выбран показатель.</p>';return}
  var y=C.column(t,st.s1.focus),lab=C.labels(t),idx=[];for(var i=0;i<y.length;i++)idx.push(i);
  v.innerHTML=seriesChart(lab,y,st.s1.focus,y.length>6?C.linfit(idx,y):null)+'<p class="cap">'+esc(st.s1.focus)+': '+
    (C.isMonthly(t)?'по месяцам, пунктир — линия тренда':'по срезам таблицы')+'. Значения от '+C.fmtv(Math.min.apply(null,y))+' до '+C.fmtv(Math.max.apply(null,y))+'.</p>';
}
function renderChk1(){
  var p=st.s1.problem||'',ok=[];
  ok.push(/\d/.test(p)?'✓ число':'✗ число');ok.push(C.clean(st.s1.source2||st.s1.source)?'✓ источник':'✗ источник');
  ok.push(C.clean(st.s1.target)?'✓ целевой уровень':'✗ целевой уровень');ok.push(C.clean(st.s1.action)?'✓ что меняем':'✗ что меняем');
  $('chk1').textContent='Четыре условия проблемы: '+ok.join(' · ');
}

// ── шаг 2 ────────────────────────────────────────────────────────────────
function renderMtab(){
  var tb=$('mtab'),m=st.s2.metrics||{};tb.innerHTML='';
  ['result','d1','d2','control'].forEach(function(k){var x=m[k]||{name:'',unit:'',freq:'',note:''};
    var tr=document.createElement('tr');
    tr.innerHTML='<td><b>'+ROLE[k]+'</b></td>'+['name','unit','freq','note'].map(function(f){return '<td><input data-m="'+k+'" data-f="'+f+'" value="'+esc(x[f]||'')+'" style="width:'+(f==='name'?170:f==='note'?220:100)+'px"></td>'}).join('');
    tb.appendChild(tr)});
  Array.prototype.forEach.call(tb.querySelectorAll('input'),function(inp){inp.oninput=function(){
    if(!st.s2.metrics[inp.dataset.m])st.s2.metrics[inp.dataset.m]={name:'',unit:'',freq:'',note:''};
    st.s2.metrics[inp.dataset.m][inp.dataset.f]=inp.value;save();renderV2();renderFrame();renderStepper();renderPrompt(3)}});
}
function renderV2(){var m=st.s2.metrics||{};$('v2').innerHTML=(m.result&&m.result.name)?treeSvg(m)+'<p class="cap">Дерево проекта: драйверы предсказывают результат; контрольная метрика наблюдается рядом. Полное дерево с источниками собирается в тренажёре «Дерево метрик».</p>':'<p class="hint" style="margin:0">Дерево появится после разбора ответа или заполнения таблицы.</p>'}

// ── шаг 3 ────────────────────────────────────────────────────────────────
function renderDtab(){
  var tb=$('dtab'),rows=st.s3.rows||[];tb.innerHTML='';
  if(!rows.length){tb.innerHTML='<tr><td colspan="5" class="hint">План появится после разбора ответа.</td></tr>';$('dmiss').textContent='';return}
  rows.forEach(function(r,i){var tr=document.createElement('tr');
    tr.innerHTML='<td>'+esc(r.metric)+'</td><td><span class="chip-st st-'+esc(r.status)+'">'+esc(r.status)+'</span></td><td>'+esc(r.source)+'</td><td>'+esc(r.how)+'</td><td>'+esc(r.term)+'</td>';tb.appendChild(tr)});
  var miss=rows.filter(function(r){return r.status!=='есть'});
  $('dmiss').textContent=miss.length?'Чего нет или есть частично: '+miss.map(function(r){return r.metric}).join(', ')+'. Это допущения проекта — они попадут в письмо команде как данные, которые начинаем собирать.':'Все метрики закрыты источниками.';
}

// ── шаг 4 ────────────────────────────────────────────────────────────────
function currentAnalysis(){var t=table();if(!t)return null;
  return st.s4.mode==='pair'?C.analysisPair(t,st.s4.x,st.s4.y):C.analysisTrend(t,st.s4.y)}
function renderS4(){
  var t=table(),cols=t?C.numericCols(t):[];
  options(document.querySelector('[data-bind="s4.mode"]'),[['pair','Связь двух показателей'],['trend','Динамика одного показателя']],st.s4.mode);
  if(cols.indexOf(st.s4.y)<0)st.s4.y=st.s1.metric&&cols.indexOf(st.s1.metric)>=0?st.s1.metric:(st.s1.focus||cols[0]||'');
  if(cols.indexOf(st.s4.x)<0)st.s4.x=cols.filter(function(c){return c!==st.s4.y})[0]||'';
  options(document.querySelector('[data-bind="s4.y"]'),cols,st.s4.y);options(document.querySelector('[data-bind="s4.x"]'),cols,st.s4.x);
  $('xBox').style.display=st.s4.mode==='pair'?'':'none';
  computeAnalysis(true);
}
function computeAnalysis(keepText){
  var an=currentAnalysis(),v=$('v4');
  $('xBox').style.display=st.s4.mode==='pair'?'':'none';
  if(!an){v.innerHTML='<p class="hint" style="margin:0">Для расчёта нужна таблица шага 1 хотя бы из трёх строк с числами.</p>';return}
  if(an.mode==='pair')v.innerHTML=scatterChart(an)+'<p class="cap">Каждая точка — строка таблицы; пунктир — линия регрессии. Коэффициент показывает согласованность изменений, а не причину.</p>';
  else v.innerHTML=seriesChart(an.labels,an.ys,an.y,an.fit)+(an.yoy.length?yoyChart(an.yoy):'')+'<p class="cap">Линия — показатель по периодам, пунктир — тренд'+(an.yoy.length?'; столбики — отклонение от того же месяца прошлого года: так сезонность не принимается за спад или рост':'')+'.</p>';
  if(!(keepText&&C.clean(st.s4.text))){st.s4.text=an.text;save();fillInputs($('st4'))}
  renderFrame();renderStepper();
}

// ── шаг 5 ────────────────────────────────────────────────────────────────
function renderV5(){var s=st.s5,v=$('v5');
  if(!C.clean(s.fact)&&!C.clean(s.hyp)){v.innerHTML='<p class="hint" style="margin:0">Вывод появится после разбора ответа.</p>';return}
  v.innerHTML='<dl class="rows"><dt>Факт</dt><dd class="fact">'+esc(s.fact)+'</dd><dt>Интерпретация</dt><dd class="interp">'+esc(s.interp)+'</dd><dt>Гипотеза</dt><dd class="hyp">'+esc(s.hyp)+'</dd><dt>Опровергнет</dt><dd class="refute">'+esc(s.refute)+'</dd></dl>'}
function renderIn5(){$('in5').innerHTML='<b>Проблема:</b> '+esc(C.or(st.s1.problem,'— не заполнена (шаг 1)'))+'<br><b>Что меняем:</b> '+esc(C.or(st.s1.action,'— (шаг 1)'))+'<br><b>Результат анализа:</b> '+esc(C.or(st.s4.text,'— (шаг 4)'))}

// ── шаг 6 ────────────────────────────────────────────────────────────────
function renderV6f(){var d=C.num(st.s6.delta),v=C.num(st.s6.volume),p=C.num(st.s6.price);
  var ok=!isNaN(d)&&!isNaN(v)&&!isNaN(p);
  $('v6f').innerHTML='<b>Эффект в месяц</b> = '+C.fmtv(d)+' <span style="color:var(--ink3)">('+esc(C.or(st.s6.udelta,'изменение'))+')</span> × '+C.fmtv(v)+' <span style="color:var(--ink3)">('+esc(C.or(st.s6.uvolume,'объём'))+')</span> × '+C.fmtv(p)+' <span style="color:var(--ink3)">руб.</span> = <b>'+(ok?C.money(d*v*p):'—')+'</b>'+(st.s6.kind==='cohort'?' на каждую месячную когорту':' в месяц на полном уровне')}
function renderAtab(){
  var tb=$('atab'),a=st.s6.ass||{};tb.innerHTML='';
  var base={delta:C.num(st.s6.delta),volume:C.num(st.s6.volume),price:C.num(st.s6.price),keep:C.num(st.s6.keep)};
  ['delta','volume','price','keep'].forEach(function(k){var x=a[k]||{pess:null,opt:null,kind:'',why:''};
    var tr=document.createElement('tr');
    tr.innerHTML='<td><b>'+ANAME[k]+'</b></td><td>'+C.fmtv(base[k])+'</td><td><input data-a="'+k+'" data-f="pess" value="'+(x.pess===null||x.pess===undefined?'':esc(C.fmtv(x.pess)))+'"></td><td><input data-a="'+k+'" data-f="opt" value="'+(x.opt===null||x.opt===undefined?'':esc(C.fmtv(x.opt)))+'"></td><td>'+esc(x.kind||'')+'</td><td style="white-space:normal;min-width:200px">'+esc(x.why||'')+'</td>';
    tb.appendChild(tr)});
  Array.prototype.forEach.call(tb.querySelectorAll('input'),function(inp){inp.oninput=function(){
    if(!st.s6.ass)st.s6.ass={};if(!st.s6.ass[inp.dataset.a])st.s6.ass[inp.dataset.a]={pess:null,opt:null,kind:'',why:''};
    st.s6.ass[inp.dataset.a][inp.dataset.f]=C.firstNum(inp.value);save();renderStepper();renderFrame();renderS7()}});
}

// ── шаг 7 ────────────────────────────────────────────────────────────────
function params7(){return {kind:st.s6.kind||'cohort',delta:C.num(st.s6.delta)||0,volume:C.num(st.s6.volume)||0,price:C.num(st.s6.price)||0,
  ramp:C.num(st.s7.ramp)||0,keep:C.num(st.s6.keep)||0,capex:C.num(st.s7.capex)||0,opex:C.num(st.s7.opex)||0,horizon:Math.max(1,Math.round(C.num(st.s7.horizon)||24)),rate:(C.num(st.s7.rate)||0)/100}}
function pair(s){var m=String(s||'').split('/');return m.length===2?[C.firstNum(m[0]),C.firstNum(m[1])]:[null,null]}
function assumptions7(){var out=[],a=st.s6.ass||{};
  ['delta','volume','price','keep'].forEach(function(k){var x=a[k];if(x&&x.pess!==null&&x.opt!==null&&!isNaN(x.pess)&&!isNaN(x.opt))out.push({key:k,name:ANAME[k],pess:x.pess,opt:x.opt})});
  var c=pair(st.s7.capex_p);if(c[0]!==null&&c[1]!==null)out.push({key:'capex',name:ANAME.capex,pess:c[0],opt:c[1]});
  var o=pair(st.s7.opex_p);if(o[0]!==null&&o[1]!==null)out.push({key:'opex',name:ANAME.opex,pess:o[0],opt:o[1]});
  return out}
function renderS7(){
  var p=params7(),res=C.totals(p),sens=C.sensitivity(p,assumptions7());
  $('k-full').textContent=C.money(res.full_month)+' в мес.';$('k-full-s').textContent=p.kind==='cohort'?'одна месячная когорта на полном уровне':'на полном уровне';
  $('k-y1').textContent=C.money(res.year1);$('k-y1-s').textContent='затраты за год: '+C.money(p.capex+12*p.opex);
  $('k-pb').textContent=res.payback===null?'нет':res.payback+' мес.';$('k-pb-s').textContent=res.payback===null?'в горизонте '+res.horizon+' мес. не окупается':(res.payback_disc===null?'с дисконтированием — за горизонтом':'с дисконтированием — '+res.payback_disc+' мес.');
  var kn=$('k-npv');kn.textContent=C.money(res.npv);kn.className='v'+(res.npv<0?' neg':'');$('k-npv-s').textContent='за '+res.horizon+' мес. при ставке '+C.fr(p.rate*100,1)+' %';
  $('v7').innerHTML=flowChart(res);
  var vd=$('verdict7');if(res.npv>=0){vd.style.color='';vd.textContent='Вывод при базовых значениях: проект окупается'+(res.payback!==null?' за '+res.payback+' мес.':'')+', NPV за горизонт положительный.'}
  else{vd.style.color='var(--warn)';vd.textContent='Вывод при базовых значениях: NPV за горизонт отрицательный — проект не окупается в выбранном горизонте.'}
  var tb=$('stab');tb.innerHTML='';
  if(!sens.length)tb.innerHTML='<tr><td colspan="7" class="hint">Пессимистичные и оптимистичные значения задаются на шаге 6 (множители) и выше (затраты).</td></tr>';
  sens.forEach(function(r){var tr=document.createElement('tr');tr.innerHTML='<td>'+r.name+'</td><td>'+C.fmtv(r.base)+'</td><td>'+C.fmtv(r.pess)+'</td><td>'+C.money(r.npv_pess)+'</td><td>'+C.fmtv(r.opt)+'</td><td>'+C.money(r.npv_opt)+'</td><td>'+(r.flips?'<span class="flip">меняется</span>':'<span class="keep">сохраняется</span>')+'</td>';tb.appendChild(tr)});
  $('v7t').innerHTML=sens.length?tornadoChart(sens,res.npv)+'<p class="cap">Торнадо: длина полосы — насколько NPV уходит от базового при пессимистичном (слева, серый или красный) и оптимистичном (зелёный) значении допущения. Красная полоса — вывод меняется.</p>':'';
  var crit=sens.filter(function(r){return r.flips});
  $('sens7').textContent=!sens.length?'':crit.length?'Вывод меняется при пессимистичном значении: '+crit.map(function(r){return r.name.toLowerCase()+' ('+C.fmtv(r.pess)+')'}).join('; ')+'. Это допущение подтверждается данными в первую очередь — оно и станет строкой «Риск» слайда.':'Ни одно допущение по отдельности не меняет вывод. Самое влиятельное — '+sens[0].name.toLowerCase()+': разброс NPV '+C.money(sens[0].span).replace(' руб.','')+' руб.';
  st.s7.text=C.effectText(p,{delta:st.s6.udelta,volume:st.s6.uvolume,price:st.s6.uprice},res,sens);save();
  fillInputs($('st7'));renderPrompt(8);renderFrame();renderStepper();
}

// ── шаг 8 и 9 ────────────────────────────────────────────────────────────
function renderIn8(){$('in8').innerHTML='<b>Проблема:</b> '+esc(C.or(st.s1.problem,'— (шаг 1)'))+'<br><b>Гипотеза:</b> '+esc(C.or(st.s5.hyp,'— (шаг 5)'))+'<br><b>Расчёт:</b> '+esc(C.or(st.s7.text,'— (шаг 7)'))}
function renderV8(){var s=st.s8;
  $('v8').innerHTML='<div class="h">'+esc(C.or(s.title,'Заголовок слайда'))+'</div>'+
    [['Формула',s.formula],['Результат',s.result],['Риск',s.risk],['Действие',s.action]].map(function(x){return '<div class="r"><b>'+x[0]+'</b><span>'+esc(C.or(x[1],'—'))+'</span></div>'}).join('')}
function renderIn9(){var v=promptVals(9);$('in9').innerHTML=[['Метрика результата',v.result],['Целевое значение',v.target],['Контрольная',v.control],['Данных нет',v.missing],['Гипотеза',v.hyp],['Эффект',v.seffect],['Риск',v.risk],['Первое действие',v.first]].map(function(x){return '<b>'+x[0]+':</b> '+esc(C.or(x[1],'—'))}).join('<br>')}
function letterText(){var s=st.s9;return [['Что меняем и почему',s.p1],['По какому показателю судим',s.p2],['Какие данные начинаем собирать',s.p3],['Первое действие',s.p4],['Когда пересматриваем',s.p5]]}
function renderV9(){var L=letterText(),v=$('v9');
  if(!C.clean(st.s9.p1)){v.innerHTML='<p class="hint" style="margin:0">Письмо появится после разбора ответа.</p>';return}
  v.innerHTML=L.map(function(x){return '<p><b>'+x[0]+'.</b> '+esc(C.or(x[1],'—')).replace(/\n/g,'<br>')+'</p>'}).join('')}

// ── сборка шага ──────────────────────────────────────────────────────────
function renderStep(n){
  fillInputs($('st'+n));
  switch(n){
    case 1:options(document.querySelector('[data-bind="s1.axis"]'),AXES,st.s1.axis);renderTableView();renderV1();renderPrompt(1);renderChk1();break;
    case 2:renderPrompt(2);renderMtab();renderV2();break;
    case 3:renderPrompt(3);renderDtab();break;
    case 4:renderS4();break;
    case 5:renderIn5();renderPrompt(5);renderV5();break;
    case 6:options(document.querySelector('[data-bind="s6.kind"]'),[['cohort','когорты: единицы эффекта накапливаются каждый месяц'],['level','уровень: постоянный поток после выхода на уровень']],st.s6.kind);renderV6f();renderPrompt(6);renderAtab();break;
    case 7:renderS7();break;
    case 8:renderIn8();renderPrompt(8);renderV8();break;
    case 9:renderIn9();renderPrompt(9);renderV9();break;
  }
}
function renderAll(){fillInputs(document);renderTabs();renderFrame();renderStepper();go(st.step||1)}

// ── события ──────────────────────────────────────────────────────────────
document.addEventListener('click',function(e){var t=e.target.closest('button');if(!t)return;
  if(t.dataset.go){go(+t.dataset.go);return}
  if(t.dataset.parse){parse(+t.dataset.parse);return}
  if(t.dataset.sw){var n=+t.dataset.n;pmode[n]=t.dataset.sw;var head=t.parentNode;Array.prototype.forEach.call(head.children,function(c){c.className=c.dataset.sw===pmode[n]?'on':''});renderPrompt(n);return}
  if(t.dataset.copy){e.stopImmediatePropagation();var k=+t.dataset.copy;copyText(ptext[k]||'',t,(pmode[k]||'fill')==='tpl'?'Копировать шаблон':'Копировать заполненный промпт');return}
  if(t.id==='bCopyLetter'){copyText(letterText().map(function(x){return x[0]+'. '+C.or(x[1],'—')}).join('\n\n'),t,'Копировать письмо');return}
  if(t.id==='bCopyMd'){copyText(C.projectMarkdown(st),t,'Копировать весь проект');return}
  if(t.id==='bExport'){var md=C.projectMarkdown(st),a=document.createElement('a');
    a.href='data:text/markdown;charset=utf-8,'+encodeURIComponent(md);a.download='проект_'+(cur==='custom'?'свой':cur)+'.md';document.body.appendChild(a);a.click();document.body.removeChild(a);
    $('expMsg').textContent='Файл проекта сохранён. Если загрузка заблокирована — кнопка «Копировать весь проект».';return}
  if(t.id==='bClear'){if(confirm('Стереть всё введённое в этом кейсе?')){try{localStorage.removeItem(key())}catch(_e){}load(cur);st.step=1;renderAll()}return}
});
load(cur);renderAll();
})();
</script>
"""


def _пресеты_js():
    return json.dumps(PRESETS, ensure_ascii=False).replace("</", "<\\/")


BODY = (CSS + HTML + "<script>\n" + CORE.replace("</", "<\\/") + "\n</script>"
        + UI.replace("__PRESETS__", _пресеты_js()))
