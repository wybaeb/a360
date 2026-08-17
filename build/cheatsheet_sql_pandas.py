# -*- coding: utf-8 -*-
"""Страница-памятка «Одна операция — два способа: SQL и pandas».

Источник правды один — список пар в репозитории практики
(`tools/nbbuild/pairs_sql_pandas.py`). Из него же собирается тетрадь, где обе
записи выполняются и сверяются. Здесь тот же список, только читаемый без
запуска: страницу можно открыть с телефона в дороге.

Если репозиторий практики лежит не рядом, сборка падает — молча выложенная
памятка, разошедшаяся с тетрадью, хуже упавшей сборки.
"""
import html
import importlib.util
import pathlib

_ПУТЬ = (pathlib.Path(__file__).resolve().parent.parent.parent /
         "a360-workspace" / "tools" / "nbbuild" / "pairs_sql_pandas.py")

if not _ПУТЬ.exists():
    raise FileNotFoundError(
        f"нет источника пар {_ПУТЬ}: страница памятки собирается из того же "
        f"файла, что и тетрадь практики — склонируйте bank-analytics-workshop "
        f"рядом с этим репозиторием")

_спец = importlib.util.spec_from_file_location("pairs_sql_pandas", _ПУТЬ)
_модуль = importlib.util.module_from_spec(_спец)
_спец.loader.exec_module(_модуль)
PAIRS, ПРАВИЛО, ВСТУПЛЕНИЕ = _модуль.PAIRS, _модуль.ПРАВИЛО, _модуль.ВСТУПЛЕНИЕ

ТЕТРАДЬ = ("https://github.com/wybaeb/bank-analytics-workshop/blob/master/"
           "2.3_памятка_sql_и_pandas/2.3.1_памятка_sql_и_pandas.ipynb")

# Разделы: пары идут в том же порядке, что в тетради, но с заголовками —
# иначе двадцать одна операция подряд читается как список без структуры.
РАЗДЕЛЫ = [
    ("osmotr", "Осмотр", (1, 3), "Что вообще лежит в выгрузке"),
    ("otbor", "Отбор и категории", (4, 6), "Сузить данные до нужного среза"),
    ("chistka", "Чистка", (7, 10), "Пропуски, повторы и типы"),
    ("agregaty", "Агрегация", (11, 13), "Свернуть строки в показатели"),
    ("forma", "Соединение и форма", (14, 17), "Собрать из нескольких таблиц"),
    ("statistika", "Статистика и окна", (18, 21), "Медианы, корзины, ранги, выбросы"),
]

CSS = """
<style>
/* Колонка страницы рассчитана на текст, а здесь рядом стоят два блока кода:
   в 860 пикселях каждый получает по 40 символов, и запрос ломается посреди
   строки. Разделы с парами — и только они — шире. */
section.wide .wrap{max-width:1180px}
.pair{border:1px solid var(--line);border-radius:14px;margin:0 0 22px;overflow:hidden}
.pair>h3{margin:0;padding:14px 18px;background:var(--surf);font-size:17px;
  border-bottom:1px solid var(--line)}
.pair>h3 .n{color:var(--acc);font-variant-numeric:tabular-nums;margin-right:.5em}
.pair .why{margin:0;padding:14px 18px 0;color:var(--ink2);font-size:15.5px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:0;padding:14px 18px 4px;
  align-items:stretch}
.two>div{min-width:0;display:flex;flex-direction:column}
.two .lab{font:700 11.5px var(--font);letter-spacing:.1em;text-transform:uppercase;
  color:var(--ink3);margin:0 0 6px}
/* Памятку читают, а не только копируют: длинную строку переносим, иначе
   правый край запроса просто не виден, а горизонтальную прокрутку внутри
   узкой колонки никто не ищет. */
.two pre{margin:0;border-radius:10px;font-size:12px;line-height:1.55;flex:1;
  white-space:pre-wrap;overflow-wrap:anywhere;overflow-x:visible}
.two>div:first-child pre{border-top-right-radius:0;border-bottom-right-radius:0}
.two>div:last-child pre{border-top-left-radius:0;border-bottom-left-radius:0;
  border-left:1px solid rgba(255,255,255,.16)}
.pair .note{margin:0;padding:12px 18px 16px;color:var(--ink2);font-size:15px}
.pair .note b{color:var(--ink)}
@media(max-width:720px){
  .two{grid-template-columns:1fr;gap:10px}
  .two pre{border-radius:10px!important;border-left:0!important}
}
</style>
"""


def _код(текст):
    return f"<pre><code>{html.escape(текст)}</code></pre>"


def _заметка(текст):
    """Заметка автора пары: `код` в обратных кавычках — в <code>."""
    куски = текст.split("`")
    собрано = []
    for i, кусок in enumerate(куски):
        экранировано = html.escape(кусок)
        собрано.append(f"<code>{экранировано}</code>" if i % 2 else экранировано)
    return "".join(собрано)


def _пара(p):
    return (
        f'<div class="pair" id="op{p["n"]}">'
        f'<h3><span class="n">{p["n"]}</span>{html.escape(p["title"])}</h3>'
        f'<p class="why">{html.escape(p["why"])}</p>'
        f'<div class="two">'
        f'<div><p class="lab">SQL</p>{_код(p["sql"])}</div>'
        f'<div><p class="lab">pandas</p>{_код(p["pd"])}</div>'
        f'</div>'
        f'<p class="note">{_заметка(p["note"])}</p>'
        f'</div>')


def _раздел(ключ, имя, границы, подзаголовок):
    первый, последний = границы
    пары = [p for p in PAIRS if первый <= p["n"] <= последний]
    номер = [r[0] for r in РАЗДЕЛЫ].index(ключ) + 1
    return (f'<section class="wide" id="{ключ}"><div class="wrap">'
            f'<h2><span class="num">{номер}</span>{имя}</h2>'
            f'<p class="sub">{подзаголовок}</p>'
            + "".join(_пара(p) for p in пары) +
            "</div></section>")


_МД = ПРАВИЛО.replace("**отбор, соединение и агрегация —\nзапросом; доводка, "
                      "форма таблицы и график — в pandas.**",
                      "<b>отбор, соединение и агрегация — запросом; доводка, "
                      "форма таблицы и график — в pandas.</b>")
_МД = _МД.replace("`SELECT *`", "<code>SELECT *</code>").replace("\n", " ")

BODY = f"""{CSS}
<header><div class="wrap">
  <div class="eyebrow">Материалы практики</div>
  <h1>Одна операция — два способа: SQL и pandas</h1>
  <p class="lead">{ВСТУПЛЕНИЕ.replace(chr(10), ' ')}</p>
  <div class="meta">
    <span class="chip">Операций <b>{len(PAIRS)}</b></span>
    <span class="chip">Данные <b>синтетические</b></span>
    <span class="chip">Проверено <b>сверкой результатов</b></span>
  </div>
</div></header>

<section><div class="wrap">
<p>{_МД}</p>

<div class="toc">
<ol>
{''.join(f'<li><a href="#{к}">{и}</a> — {п.lower()}</li>'
         for к, и, _, п in РАЗДЕЛЫ)}
</ol>
</div>

<p class="sub">Всё то же самое, но выполняемое, — в тетради
<a href="{ТЕТРАДЬ}">«Памятка SQL ↔ pandas»</a>: там каждая пара считается
на вашей базе, и под ячейкой появляется отметка о совпадении результатов.
Разведочный анализ, ради которого эти операции и нужны, разобран
в <a href="longread_eda.html">отдельном лонгриде</a>.</p>
</div></section>

{''.join(_раздел(*р) for р in РАЗДЕЛЫ)}

<section><div class="wrap">
<h2>Что выбрать</h2>
<div class="card acc">
<ul>
  <li><b>Данных много, ответ маленький</b> — считает база. Отбор, соединение
      и агрегация по миллионам строк живут в запросе.</li>
  <li><b>Данных уже мало, нужна форма</b> — работает pandas: доводка таблицы,
      производные колонки, подготовка к графику.</li>
  <li><b>Правило, которым пользуются все</b> — представление в базе, а не
      ячейка в чужой тетради: так оно живёт в одном месте и не расходится
      между отчётами.</li>
</ul>
</div>
<p>Числа при этом совпадают до последнего знака — в этом и смысл сверки
в тетради. Выбор между SQL и pandas — не про правильность, а про место
вычисления и объём данных.</p>
</div></section>

<footer><div class="wrap">
  Аналитика 360 · материалы практической части.<br>
  Все примеры выполняются на учебном стенде, данные синтетические.
</div></footer>
"""
