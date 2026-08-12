# -*- coding: utf-8 -*-
"""SCORM 1.2 пакет с теми же материалами — для загрузки в LMS заказчика.

Отличия от версии на GitHub Pages ровно два:
  1. Страницы не зашифрованы: доступ разграничивает сама LMS, второй пароль
     внутри курса только мешал бы.
  2. Добавлена обвязка SCORM API — курс отмечается пройденным, когда участник
     поработал со страницей. Без неё LMS покажет «не начат» даже у того, кто
     всё прочитал.

Пакет — один SCO: точка входа index.html, внутри переходы на лонгрид и практику.
Дробить на три SCO незачем — прогресс всё равно один.

Когда ставится «пройдено». Открытие страницы статуса не даёт: при загрузке
курс переводится в «начат» (incomplete), а «пройдено» ставится по факту работы
участника — настоящее событие, 45 секунд осмысленного времени и признак
прохождения (прокрутка лонгрида до 90% высоты либо десяток действий на
одноэкранном тренажёре). Само условие и почему оно такое — в докстринге
build/scorm_engagement.py; здесь оно только подключается к LMS.

Обвязка внедряется не во все страницы: у тренажёра дерева метрик она своя,
и вторая поверх неё вызвала бы LMSInitialize дважды — по SCORM 1.2 это
ошибка 101 (already initialized), после которой LMS вправе игнорировать всё
остальное. Страницы с собственной обвязкой пропускаются, условие прохождения
у них то же самое — из общего модуля.

Запуск (после build_pages.py):  python3 build/build_scorm.py
"""
import pathlib
import re
import shutil
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scorm_engagement  # noqa: E402  — общее условие «участник работал»

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "scorm" / "content"
STAGE = ROOT / "scorm" / "package"
DIST = ROOT / "dist"
ZIP = DIST / "a360_step0_scorm12.zip"

IDENT = "KK.SBER.A360.STEP0"
TITLE = "Аналитика 360 · практическая часть: предчтение и практика в GigaChat"

# Обвязка ищет API по спецификации SCORM 1.2: сначала вверх по window.parent,
# потом в opener. Если API не найден (страницу открыли просто в браузере),
# всё молча работает как обычный сайт — это нужно, чтобы те же файлы годились
# и для LMS, и для раздачи ссылкой.
API_JS = """
<script>""" + scorm_engagement.JS + """
(function(){
  var api=null;
  function find(win,depth){
    while(win && depth-->0){ if(win.API) return win.API; win = (win.parent!==win)?win.parent:null; }
    return null;
  }
  api = find(window,10) || (window.opener ? find(window.opener,10) : null);
  if(!api) return;
  try{ api.LMSInitialize(""); }catch(e){ return; }
  function get(k){ try{ return api.LMSGetValue(k); }catch(e){ return ""; } }
  function set(k,v){ try{ api.LMSSetValue(k,v); }catch(e){} }

  // Закрытие сеанса вешается сразу после LMSInitialize и до всех выходов из
  // функции: сеанс, открытый и не закрытый, LMS считает зависшим.
  window.addEventListener("beforeunload", function(){
    try{ api.LMSCommit(""); api.LMSFinish(""); }catch(e){}
  });

  // Открытие страницы — это «начат», не «пройдено». Уже проставленный статус
  // не трогаем: пересдач у курса нет, снимать зачёт при повторном заходе
  // нельзя.
  var st = get("cmi.core.lesson_status");
  if(st==="completed" || st==="passed") return;
  if(st==="not attempted" || st==="") set("cmi.core.lesson_status","incomplete");
  try{ api.LMSCommit(""); }catch(e){}

  // «Пройдено» ставится, когда участник поработал со страницей: условие и его
  // пороги — в build/scorm_engagement.py.
  window.a360Engagement(function(){
    set("cmi.core.lesson_status","completed");
    try{ api.LMSCommit(""); }catch(e){}
  });
})();
</script>
"""

MANIFEST = """<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="{ident}" version="1.2"
  xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
  xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2 imscp_rootv1p1p2.xsd
                      http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations default="ORG">
    <organization identifier="ORG">
      <title>{title}</title>
      <item identifier="ITEM1" identifierref="RES1" isvisible="true">
        <title>{title}</title>
        <adlcp:masteryscore/>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="RES1" type="webcontent" adlcp:scormtype="sco" href="index.html">
{files}
    </resource>
  </resources>
</manifest>
"""


def main():
    if not SRC.exists():
        raise SystemExit("нет scorm/content — сначала запустите build_pages.py")
    if STAGE.exists():
        shutil.rmtree(STAGE)
    shutil.copytree(SRC, STAGE)

    # Обвязка вставляется перед </body> — после наших скриптов, чтобы не
    # соревноваться с ними за загрузку. Страницы со своей обвязкой (тренажёр
    # дерева метрик) пропускаются: два LMSInitialize подряд — ошибка 101.
    own = []
    for f in sorted(STAGE.glob("*.html")):
        html = f.read_text(encoding="utf-8")
        if re.search(r"LMSInitialize\s*\(", html):   # именно вызов, не упоминание
            own.append(f.name)
            continue
        html = re.sub(r"</body>", API_JS + "</body>", html, count=1)
        f.write_text(html, encoding="utf-8")
    if own:
        print("  своя обвязка SCORM, наша не внедряется: " + ", ".join(own))

    files = sorted(p.relative_to(STAGE).as_posix() for p in STAGE.rglob("*") if p.is_file())
    (STAGE / "imsmanifest.xml").write_text(
        MANIFEST.format(ident=IDENT, title=TITLE,
                        files="\n".join(f'      <file href="{f}"/>' for f in files)),
        encoding="utf-8")

    DIST.mkdir(exist_ok=True)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(STAGE.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(STAGE).as_posix())

    print(f"  {ZIP.relative_to(ROOT)} · {ZIP.stat().st_size // 1024} КБ · "
          f"{len(files) + 1} файлов, один SCO")


if __name__ == "__main__":
    main()
