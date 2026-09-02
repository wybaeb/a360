# -*- coding: utf-8 -*-
"""Ссылки на репозиторий практики: к каждой — путь внутри сайта.

В корпоративной сети github.com закрыт, страницы на github.io открываются.
Любая ссылка на файл репозитория в материалах должна иметь пару: тот же
файл на сайте — для чтения (README и тетради собраны страницами в practice/)
и для скачивания (копия в downloads/practice/). Пару дописывает
переписать(html): она находит все <a href="https://github.com/…/bank-analytics-workshop…">
и добавляет к ним плашки «на сайте» и «скачать». Генераторы страниц ссылки
на репозиторий пишут как раньше — пара появляется на сборке у всех сразу.
"""
import html
import pathlib
import re
import urllib.parse

РЕПО = "https://github.com/wybaeb/bank-analytics-workshop"
ROOT = pathlib.Path(__file__).resolve().parent.parent
ЗЕРКАЛО = ROOT / "downloads" / "practice"
ПРОСМОТР = ROOT / "practice"
КОМПЛЕКТЫ = ROOT / "downloads" / "kits"

_ССЫЛКА = re.compile(
    r'<a\s+href="' + re.escape(РЕПО) + r'(?P<хвост>[^"]*)"(?P<атр>[^>]*)>(?P<текст>.*?)</a>',
    re.S)


def путь_из_url(url_или_хвост):
    """'/blob/master/2.4_…/2.4.1_установка.md' → PurePosixPath; '' для корня."""
    хвост = url_или_хвост.replace(РЕПО, "", 1)
    хвост = urllib.parse.unquote(хвост).strip("/")
    for префикс in ("blob/master", "raw/master", "tree/master"):
        if хвост == префикс:
            return pathlib.PurePosixPath("")
        if хвост.startswith(префикс + "/"):
            return pathlib.PurePosixPath(хвост[len(префикс) + 1:])
    if хвост in ("", ".git"):
        return pathlib.PurePosixPath("")
    return None   # что-то другое (issues, commits) — не трогаем


def _q(p):
    return "/".join(urllib.parse.quote(ч) for ч in p.parts)


def просмотр(path):
    """Относительный (от корня сайта) адрес читаемой копии или None."""
    if path == pathlib.PurePosixPath(""):
        return "practice_files.html"
    if (ЗЕРКАЛО / path).is_dir():
        return f"practice_files.html#p-{urllib.parse.quote(path.parts[0])}"
    if path.suffix in (".md", ".ipynb") and (ПРОСМОТР / (str(path) + ".html")).exists():
        return f"practice/{_q(path)}.html"
    if path.suffix == ".html" and (ЗЕРКАЛО / path).exists():
        return f"downloads/practice/{_q(path)}"
    return None


def скачать(path):
    """Относительный адрес копии для скачивания или None."""
    if path == pathlib.PurePosixPath(""):
        return None
    if (ЗЕРКАЛО / path).is_dir():
        k = КОМПЛЕКТЫ / (path.parts[0] + ".zip")
        return f"downloads/kits/{urllib.parse.quote(k.name)}" if k.exists() else None
    if (ЗЕРКАЛО / path).exists():
        return f"downloads/practice/{_q(path)}"
    return None


def плашки(path, prefix=""):
    """HTML плашек «на сайте» / «скачать» для пути репозитория."""
    out = []
    v = просмотр(path)
    if v:
        out.append(f'<a class="mir" href="{prefix}{v}">на сайте</a>')
    d = скачать(path)
    if d:
        имя = html.escape(path.name) if path.name else ""
        подпись = "комплект" if (ЗЕРКАЛО / path).is_dir() else "скачать"
        out.append(f'<a class="mir" href="{prefix}{d}" download="{имя}">{подпись}</a>')
    return "".join(out)


def переписать(html_текст, prefix=""):
    """Дописать плашки ко всем ссылкам на репозиторий в готовом HTML."""
    def _зам(m):
        path = путь_из_url(m.group("хвост"))
        if path is None:
            return m.group(0)
        return m.group(0) + плашки(path, prefix)
    return _ССЫЛКА.sub(_зам, html_текст)


def сколько_без_пары(html_текст):
    """Ссылки на репозиторий, у которых не нашлось копии на сайте."""
    плохие = []
    for m in _ССЫЛКА.finditer(html_текст):
        path = путь_из_url(m.group("хвост"))
        if path is None or not (просмотр(path) or скачать(path)):
            плохие.append(m.group("хвост"))
    return плохие
