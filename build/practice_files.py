# -*- coding: utf-8 -*-
"""Страница «Папка практики: скачать без git» и зеркало папки в downloads/.

Зачем. В корпоративной сети github.com закрыт, а страницы материалов
(github.io) открываются. Шаг «git clone» инструкции установки на такой машине
не проходит — участник остаётся без тетрадей и выгрузок. Поэтому та же папка
практики лежит здесь файл за файлом: копия отслеживаемых файлов репозитория
bank-analytics-workshop в downloads/practice/ плюс архив целиком. Страница
перечисляет файлы по папкам, говорит, что нужно для какого кейса, и как
положить файлы в JupyterHub.

Источник — соседний рабочий каталог репозитория практики (a360-workspace):
берём только то, что отслеживает git, — без .env, кэшей и графиков.
Зеркало пересобирается на каждой сборке страниц, поэтому расходиться с
репозиторием ему негде.
"""
import html
import pathlib
import re
import shutil
import subprocess
import sys
import urllib.parse
import zipfile

import markdown
import nbformat
from nbconvert import HTMLExporter

import theme

ROOT = pathlib.Path(__file__).resolve().parent.parent
WS = ROOT.parent / "a360-workspace"
OUT = ROOT / "downloads" / "practice"
ZIP = ROOT / "downloads" / "practice.zip"
KITS = ROOT / "downloads" / "kits"
VIEW = ROOT / "practice"
РЕПО = "https://github.com/wybaeb/bank-analytics-workshop"
ИМЯ_ПАПКИ = "bank-analytics-workshop"

# Что лежит в папках — тем же порядком и теми же номерами, что на странице
# материалов. Общие папки — в конце.
ПАПКИ = [
    ("2.2_разведочный_анализ", "Разведочный анализ",
     "тетрадь: семь этапов работы с незнакомой выгрузкой"),
    ("2.3_памятка_sql_и_pandas", "Памятка SQL и pandas",
     "тетрадь-справочник: 21 операция двумя способами со сверкой"),
    ("2.4_установка_стенда", "Установка стенда",
     "полные тексты инструкций: локально и в JupyterHub"),
    ("2.5_кейс_карточный_бизнес", "Кейс: карточный бизнес",
     "выгрузка, промпты и эталонные скрипты для таблиц"),
    ("2.6_кейс_кредитный_конвейер", "Кейс: кредитный конвейер",
     "тетрадь: SQL от первого запроса до панели в BI"),
    ("2.7_кейс_отчёт_агента", "Кейс: отчёт агента",
     "тетрадь: вопрос словами — отчёт с графиками"),
    ("2.8_кейс_дашборд_агентом", "Кейс: дашборд агентом",
     "тетрадь: описание абзацем — постоянная панель в BI"),
    ("3.2_кейс_gigachat_отчёт", "Кейс: страница анализа от ассистента",
     "промпты и готовые мини-инструменты, открываются в браузере"),
    ("3.3_кейс_кластеризация", "Кейс: сегментация клиентов",
     "промпт, ответ ассистента, тетрадь, трёхмерный график"),
    ("3.4_кейс_анализ_отклонений", "Кейс: анализ отклонений",
     "промпт, ответ ассистента, тетрадь"),
    ("4.1_каркас_проекта", "Каркас проекта",
     "шаблоны презентации проекта и письма команде, примеры каркасов"),
    ("4.4_финмодель_эффекта", "Финансовая модель эффекта",
     "тетрадь: множители из выгрузки, поток, окупаемость, NPV"),
    ("data", "Выгрузки",
     "учебные наборы данных для всех кейсов и генераторы"),
    ("tools", "Общие модули",
     "подключение к базе, сверка SQL и pandas, клиент ассистента, агенты"),
    ("sql", "База стенда",
     "схема, загрузка и дамп учебной базы"),
    ("", "Корень папки",
     "инструкции, список библиотек, запуск стенда"),
]

# Какие файлы нужны для какого кейса и нужен ли стенд. Стенд — база данных
# и BI; без него работают кейсы, которые читают выгрузку из файла.
КЕЙСЫ = [
    ("2.2 · Разведочный анализ", "папка 2.2 и папка tools", "база данных"),
    ("2.3 · Памятка SQL и pandas", "папка 2.3 и папка tools", "база данных"),
    ("2.5 · Карточный бизнес", "только папка 2.5", "не нужен"),
    ("2.6 · Кредитный конвейер", "папка 2.6 и папка tools", "база данных и BI"),
    ("2.7 · Отчёт агента", "папка 2.7 и папка tools", "база данных и ключ ассистента"),
    ("2.8 · Дашборд агентом", "папка 2.8 и папка tools", "база, BI и ключ ассистента"),
    ("3.2 · Страница анализа от ассистента",
     "папка 3.2 и файл data/product/savings_monthly.csv", "не нужен"),
    ("3.3 · Сегментация клиентов",
     "папка 3.3 и файл data/clients/clients_sample.csv", "не нужен"),
    ("3.4 · Анализ отклонений",
     "папка 3.4 и файл data/series/portfolio_operations_daily.csv", "не нужен"),
    ("4.1 · Каркас проекта", "только папка 4.1", "не нужен"),
    ("4.4 · Финансовая модель эффекта",
     "папка 4.4 и файл data/product/savings_monthly.csv", "не нужен"),
]

# Комплект «всё для кейса»: папка кейса плюс ровно то, что ей нужно, —
# общие модули для тетрадей с базой, один файл выгрузки для тетрадей без неё.
ОБЩИЕ = ["tools/*.py", "requirements.txt"]
КОМПЛЕКТЫ = {
    "2.2_разведочный_анализ": ОБЩИЕ,
    "2.3_памятка_sql_и_pandas": ОБЩИЕ,
    "2.4_установка_стенда": ["requirements.txt", ".env.example",
                             "docker-compose.yml", "run.sh", "sql/**/*",
                             "tools/*.py", "_STAND.md"],
    "2.5_кейс_карточный_бизнес": [],
    "2.6_кейс_кредитный_конвейер": ОБЩИЕ,
    "2.7_кейс_отчёт_агента": ОБЩИЕ,
    "2.8_кейс_дашборд_агентом": ОБЩИЕ,
    "3.2_кейс_gigachat_отчёт": ["data/product/savings_monthly.csv"],
    "3.3_кейс_кластеризация": ["data/clients/clients_sample.csv"],
    "3.4_кейс_анализ_отклонений": ["data/series/portfolio_operations_daily.csv"],
    "4.1_каркас_проекта": [],
    "4.4_финмодель_эффекта": ["data/product/savings_monthly.csv"],
}

# Как что открывать: расширение → подсказка.
ЧЕМ_ОТКРЫТЬ = {
    ".ipynb": "тетрадь — загрузить в JupyterHub или открыть в VS Code",
    ".md": "текст — открывается любым редактором",
    ".html": "мини-инструмент — открыть в браузере двойным щелчком",
    ".csv": "выгрузка — таблица или тетрадь",
    ".xlsx": "выгрузка для Excel",
    ".txt": "промпт — скопировать в ассистент",
    ".py": "модуль Python — положить рядом с тетрадью, как в структуре папок",
    ".gs": "эталонный скрипт Google Таблиц",
    ".bas": "эталонный макрос Excel",
    ".sql": "запросы к базе стенда",
    ".sh": "сценарий запуска стенда",
    ".yml": "описание стенда для Docker",
    ".png": "изображение",
    ".json": "данные",
    ".js": "проверка скрипта",
    ".example": "образец файла настроек: переименовать в .env",
}


def _файлы():
    """Отслеживаемые git файлы репозитория практики, кроме служебных."""
    if not (WS / ".git").exists():
        sys.exit(f"нет рабочего каталога репозитория практики: {WS}")
    out = subprocess.run(["git", "-c", "core.quotepath=off", "ls-files"],
                         cwd=WS, capture_output=True, text=True, check=True).stdout
    return [pathlib.PurePosixPath(l) for l in out.splitlines()
            if l and l != ".gitignore"]


def sync():
    """Пересобрать зеркало и архив. Возвращает список (путь, размер)."""
    файлы = _файлы()
    if OUT.exists():
        shutil.rmtree(OUT)
    for f in файлы:
        src = WS / f
        dst = OUT / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files_sorted(файлы):
            z.write(WS / f, f"{ИМЯ_ПАПКИ}/{f}")
    _комплекты(файлы)
    _просмотр(файлы)
    return [(f, (WS / f).stat().st_size) for f in files_sorted(файлы)]


def _подходит(f, маски):
    return any(f.match(м) or (м.endswith("/**/*") and str(f).startswith(м[:-4]))
               for м in маски)


def _комплекты(файлы):
    """Архив на каждый кейс: папка кейса плюс её зависимости, со структурой."""
    if KITS.exists():
        shutil.rmtree(KITS)
    KITS.mkdir(parents=True)
    for папка, маски in КОМПЛЕКТЫ.items():
        состав = [f for f in files_sorted(файлы)
                  if f.parts[0] == папка or _подходит(f, маски)]
        with zipfile.ZipFile(KITS / f"{папка}.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for f in состав:
                z.write(WS / f, f"{ИМЯ_ПАПКИ}/{f}")


def размер_комплекта(папка):
    k = KITS / f"{папка}.zip"
    return k.stat().st_size if k.exists() else 0


# ---- читаемые копии: README и инструкции страницами, тетради через nbconvert

_MD = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"])


def _вверх(path):
    """Префикс до корня сайта из practice/<путь>.html."""
    return "../" * len(path.parts)


def _перевести_ссылку(href, path, файлы_набор):
    """Относительная ссылка внутри md → адрес на сайте."""
    if re.match(r"^[a-z]+:|^#|^mailto:", href):
        return href
    цель = pathlib.PurePosixPath(urllib.parse.unquote(href.split("#")[0]))
    якорь = ("#" + href.split("#", 1)[1]) if "#" in href else ""
    полный = pathlib.PurePosixPath(*[ч for ч in (path.parent / цель).parts if ч != "."])
    # убираем «..»
    части = []
    for ч in полный.parts:
        if ч == "..":
            if части:
                части.pop()
        else:
            части.append(ч)
    полный = pathlib.PurePosixPath(*части) if части else pathlib.PurePosixPath("")
    верх = _вверх(path)
    if str(полный) in ("", ".") or полный.parts and полный not in файлы_набор and \
            any(str(f).startswith(str(полный) + "/") for f in файлы_набор):
        якорь_папки = f"#p-{urllib.parse.quote(полный.parts[0])}" if полный.parts else ""
        return f"{верх}practice_files.html{якорь_папки}"
    if полный in файлы_набор:
        q = "/".join(urllib.parse.quote(ч) for ч in полный.parts)
        if полный.suffix in (".md", ".ipynb"):
            return f"{верх}practice/{q}.html{якорь}"
        return f"{верх}downloads/practice/{q}"
    return href


def _шапка(path, заголовок, подпись):
    верх = _вверх(path)
    q = "/".join(urllib.parse.quote(ч) for ч in path.parts)
    return (f'<nav class="crumbs" aria-label="Навигация"><div class="wrap">'
            f'<a href="{верх}index.html">Материалы</a><span class="sep">▸</span>'
            f'<a href="{верх}practice_files.html">Папка практики</a>'
            f'<span class="sep">▸</span><span class="here">{html.escape(path.name)}</span>'
            f'</div></nav>\n<header><div class="wrap">'
            f'<div class="eyebrow">{подпись}</div><h1>{заголовок}</h1>'
            f'<div class="meta">'
            f'<a class="chip" href="{верх}downloads/practice/{q}" download="{html.escape(path.name)}">'
            f'Скачать <b>{html.escape(path.name)}</b></a>'
            f'<a class="chip" href="{РЕПО}/blob/master/{q}">На <b>GitHub</b></a>'
            f'</div></div></header>')


def _страница_md(path, файлы_набор):
    текст = (WS / path).read_text(encoding="utf-8")
    m = re.match(r"\s*#\s+(.+)", текст)
    заголовок = html.escape(m.group(1).strip()) if m else html.escape(path.name)
    if m:
        текст = текст[m.end():]
    _MD.reset()
    тело = _MD.convert(текст)
    тело = re.sub(r'(href|src)="([^"]*)"',
                  lambda mm: f'{mm.group(1)}="{_перевести_ссылку(mm.group(2), path, файлы_набор)}"',
                  тело)
    import repolink
    тело = repolink.переписать(тело, prefix=_вверх(path))
    body = (_шапка(path, заголовок, f"Репозиторий практики · <code>{html.escape(str(path.parent))}</code>"
                   if str(path.parent) != "." else "Репозиторий практики")
            + f'<section><div class="wrap md">{тело}</div></section>'
            + '<footer><div class="wrap">Аналитика 360 · копия файла из репозитория практики.</div></footer>')
    return theme.SHELL.format(title=f"{заголовок} · Аналитика 360", css=theme.CSS, body=body)


def _страница_ipynb(path):
    nb = nbformat.read(str(WS / path), as_version=4)
    exp = HTMLExporter(template_name="lab")
    exp.exclude_input_prompt = True
    exp.exclude_output_prompt = True
    тело, _ = exp.from_notebook_node(nb)
    верх = _вверх(path)
    q = "/".join(urllib.parse.quote(ч) for ч in path.parts)
    полоса = (f'<div style="font-family:system-ui,sans-serif;font-size:14px;padding:10px 18px;'
              f'background:#eaf6ef;border-bottom:1px solid #bfe3cf;display:flex;gap:18px;'
              f'flex-wrap:wrap;align-items:center">'
              f'<a href="{верх}index.html" style="color:#128a53;font-weight:700">Материалы</a>'
              f'<a href="{верх}practice_files.html" style="color:#128a53;font-weight:700">Папка практики</a>'
              f'<span style="color:#555">Тетрадь <b>{html.escape(path.name)}</b> — просмотр с результатами</span>'
              f'<a href="{верх}downloads/practice/{q}" download="{html.escape(path.name)}" '
              f'style="color:#fff;background:#20BA72;padding:6px 14px;border-radius:999px;'
              f'font-weight:700;text-decoration:none">Скачать .ipynb</a>'
              f'<a href="{РЕПО}/blob/master/{q}" style="color:#128a53">На GitHub</a></div>')
    тело = тело.replace("<body", "<body data-a360", 1)
    i = тело.find(">", тело.find("<body")) + 1
    return тело[:i] + полоса + тело[i:]


def _просмотр(файлы):
    """practice/<путь>.html для каждого md и ipynb."""
    if VIEW.exists():
        shutil.rmtree(VIEW)
    набор = set(файлы)
    for f in файлы:
        if f.suffix not in (".md", ".ipynb"):
            continue
        dst = VIEW / (str(f) + ".html")
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(_страница_md(f, набор) if f.suffix == ".md" else _страница_ipynb(f),
                       encoding="utf-8")


def просмотр_url(path):
    return f"practice/{'/'.join(urllib.parse.quote(ч) for ч in path.parts)}.html" \
        if path.suffix in (".md", ".ipynb") else None


def files_sorted(файлы):
    return sorted(файлы, key=lambda p: (str(p.parent) != ".", str(p)))


def _размер(n):
    if n < 1024:
        return f"{n} Б"
    if n < 1024 * 1024:
        return f"{n / 1024:.0f} КБ"
    return f"{n / 1024 / 1024:.1f} МБ".replace(".", ",")


def _строка(path, size):
    имя = html.escape(path.name)
    href = "downloads/practice/" + "/".join(html.escape(p) for p in path.parts)
    подсказка = ЧЕМ_ОТКРЫТЬ.get(path.suffix, "")
    v = просмотр_url(path)
    if v:
        подсказка += f' <a class="mir" href="{v}">на сайте</a>'
    elif path.suffix == ".html":
        подсказка += f' <a class="mir" href="{href}">открыть</a>'
    return (f'<tr><td><a href="{href}" download="{имя}">{имя}</a></td>'
            f'<td>{подсказка}</td>'
            f'<td style="white-space:nowrap;text-align:right">{_размер(size)}</td></tr>')


def _таблица(строки):
    return ('<div class="scroll"><table>'
            '<thead><tr><th>Файл</th><th>Что это</th><th>Размер</th></tr></thead>'
            '<tbody>' + "".join(строки) + '</tbody></table></div>')


def _раздел_папок(файлы):
    по_папкам = {}
    for f, size in файлы:
        верх = f.parts[0] if len(f.parts) > 1 else ""
        по_папкам.setdefault(верх, []).append((f, size))
    куски = []
    for ключ, заг, что in ПАПКИ:
        строки = по_папкам.pop(ключ, [])
        if not строки:
            continue
        путь = f"<code>{html.escape(ключ)}/</code> · " if ключ else ""
        к = размер_комплекта(ключ) if ключ else 0
        комплект = (f' <a class="mir" href="downloads/kits/{urllib.parse.quote(ключ)}.zip" '
                    f'download="{html.escape(ключ)}.zip">всё для кейса · {_размер(к)}</a>'
                    if к else "")
        куски.append(f'<h3 id="p-{html.escape(ключ) or "root"}">{заг}</h3>'
                     f'<p class="sub" style="margin-bottom:10px">{путь}{что}. '
                     f'{len(строки)} файл{_окончание(len(строки))}.{комплект}</p>'
                     + _таблица(_строка(f, s) for f, s in строки))
    for ключ in sorted(по_папкам):   # папки, не описанные выше, — не теряем
        строки = по_папкам[ключ]
        куски.append(f'<h3>{html.escape(ключ)}</h3>'
                     + _таблица(_строка(f, s) for f, s in строки))
    return "".join(куски)


def _окончание(n):
    if n % 10 == 1 and n % 100 != 11:
        return ""
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return "а"
    return "ов"


def body(файлы):
    всего = sum(s for _, s in файлы)
    архив = ZIP.stat().st_size
    def _комплект(к):
        ключ = next((п for п, *_ in ПАПКИ if п.startswith(к.split(" ")[0] + "_")), "")
        r = размер_комплекта(ключ) if ключ else 0
        return (f'<a class="mir" href="downloads/kits/{urllib.parse.quote(ключ)}.zip" '
                f'download="{html.escape(ключ)}.zip">скачать · {_размер(r)}</a>' if r else "")
    кейсы = "".join(f"<tr><td>{к}</td><td>{ф}</td><td>{_комплект(к)}</td><td>{с}</td></tr>"
                    for к, ф, с in КЕЙСЫ)
    оглавление = " · ".join(
        f'<a href="#p-{html.escape(к) or "root"}">{html.escape(к) or "корень"}</a>'
        for к, *_ in ПАПКИ)
    return f"""
<header><div class="wrap">
  <div class="eyebrow">Материалы практики</div>
  <h1>Папка практики: скачать без git</h1>
  <p class="lead">Та же папка, что в репозитории практики, — файл за файлом.
     Для машин, где git и сайт репозитория недоступны: скачайте архив целиком
     или нужные файлы по отдельности и положите их в одну папку с той же
     структурой — в JupyterHub, VS Code или просто на диск.</p>
  <div class="meta">
    <span class="chip">Файлов: <b>{len(файлы)}</b></span>
    <span class="chip">Всего: <b>{_размер(всего)}</b></span>
    <span class="chip">Комплектов на кейс: <b>{len(КОМПЛЕКТЫ)}</b></span>
  </div>
</div></header>

<section><div class="wrap">
<h2><span class="num">1</span>Три способа забрать папку</h2>

<ol class="steps">
<li><b>Комплект на кейс.</b>
<p>Архив «всё для кейса»: папка кейса и ровно те файлы данных и общих
модулей, которые ей нужны, со структурой папок. Ссылки — в таблице ниже
и у каждой папки в списке. Распакуйте — и кейс готов к запуску.</p></li>

<li><b>По одному файлу.</b>
<p>Ниже список всех файлов по папкам. Щелчок по имени сохраняет файл;
плашка «на сайте» открывает README или тетрадь для чтения прямо здесь.
Сохраняйте структуру: тетради ищут общие модули в <code>tools/</code>
и выгрузки в <code>data/</code> на уровень выше себя, поэтому папка кейса,
<code>tools/</code> и <code>data/</code> должны лежать рядом в одной
родительской папке.</p></li>

<li><b>Через git</b> — на машине, где он есть и репозиторий доступен:
<pre><code>git clone {РЕПО}.git</code></pre></li>
</ol>
<p class="sub">Все варианты работы без репозитория, включая JupyterHub
и кейсы без стенда, — на странице <a href="nogit.html">«Если не открывается
GitHub»</a>.</p>

<div class="card acc">
<h4>Что нужно для какого кейса</h4>
<p>Стенд — это база данных и система дашбордов из инструкции установки.
Кейсы, которые читают выгрузку из файла, работают без него: достаточно
папки кейса и одного файла из <code>data/</code>.</p>
<div class="scroll">
<table>
<thead><tr><th>Кейс</th><th>Что нужно</th><th>Комплект</th><th>Стенд</th></tr></thead>
<tbody>{кейсы}</tbody>
</table>
</div>
</div>
</div></section>

<section><div class="wrap">
<h2><span class="num">2</span>Как положить в JupyterHub</h2>
<ol>
<li>В файловой панели хаба создайте папку <code>{ИМЯ_ПАПКИ}</code>.</li>
<li>Внутри неё — папки с теми же именами, что здесь: папку кейса,
<code>tools/</code> и <code>data/</code> с вложенными папками.</li>
<li>Кнопкой <b>Upload</b> загрузите файлы в каждую из папок. Тетрадь
открывается двойным щелчком; вверху — <b>Restart Kernel</b> →
<b>Run All</b>.</li>
<li>Для тетрадей с базой нужны переменные окружения подключения —
их задаёт администратор хаба, см. второй раздел
<a href="setup.html">инструкции установки</a>.</li>
</ol>
<p class="sub">Файл <code>.env.example</code> — образец настроек для локального
стенда; в хабе он не нужен.</p>
</div></section>

<section><div class="wrap">
<h2><span class="num">3</span>Все файлы по папкам</h2>
<p class="sub">{оглавление}</p>
{_раздел_папок(файлы)}

<h3>Вся папка целиком</h3>
<p>Нужна только тем, кто разворачивает стенд у себя: <a href="downloads/practice.zip"
download="{ИМЯ_ПАПКИ}.zip">скачать {ИМЯ_ПАПКИ}.zip · {_размер(архив)}</a>.
Распакуйте — получится папка <code>{ИМЯ_ПАПКИ}</code> со всей структурой;
дальше по <a href="setup.html">инструкции установки</a> со второго шага.</p>
</div></section>

<footer><div class="wrap">
  Аналитика 360 · материалы практической части.<br>
  Данные синтетические, сгенерированы для обучения.
</div></footer>
"""


ФАЙЛЫ = sync()
BODY = body(ФАЙЛЫ)

if __name__ == "__main__":
    print(f"зеркало: {len(ФАЙЛЫ)} файлов, архив {_размер(ZIP.stat().st_size)}")
