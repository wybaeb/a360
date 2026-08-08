# -*- coding: utf-8 -*-
"""SCORM 1.2 пакет с теми же материалами — для загрузки в LMS заказчика.

Отличия от версии на GitHub Pages ровно два:
  1. Страницы не зашифрованы: доступ разграничивает сама LMS, второй пароль
     внутри курса только мешал бы.
  2. Добавлена обвязка SCORM API — курс отмечается пройденным, когда участник
     доходит до конца страницы практики. Без неё LMS покажет «не начат»
     даже у того, кто всё прочитал.

Пакет — один SCO: точка входа index.html, внутри переходы на лонгрид и практику.
Дробить на три SCO незачем — прогресс всё равно один.

Запуск (после build_pages.py):  python3 build/build_scorm.py
"""
import pathlib
import re
import shutil
import zipfile

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
<script>
(function(){
  var api=null, done=false;
  function find(win,depth){
    while(win && depth-->0){ if(win.API) return win.API; win = (win.parent!==win)?win.parent:null; }
    return null;
  }
  api = find(window,10) || (window.opener ? find(window.opener,10) : null);
  if(!api) return;
  try{ api.LMSInitialize(""); }catch(e){ return; }
  function set(k,v){ try{ api.LMSSetValue(k,v); }catch(e){} }
  if(api.LMSGetValue("cmi.core.lesson_status")==="not attempted") set("cmi.core.lesson_status","incomplete");
  function complete(){
    if(done) return; done=true;
    set("cmi.core.lesson_status","completed");
    try{ api.LMSCommit(""); }catch(e){}
  }
  // Курс считается пройденным, когда участник долистал страницу до конца.
  function onScroll(){
    if(window.scrollY + window.innerHeight >= document.body.scrollHeight - 120) complete();
  }
  window.addEventListener("scroll", onScroll, {passive:true});
  onScroll();
  window.addEventListener("beforeunload", function(){
    try{ api.LMSCommit(""); api.LMSFinish(""); }catch(e){}
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
    # соревноваться с ними за загрузку.
    for f in STAGE.glob("*.html"):
        html = f.read_text(encoding="utf-8")
        html = re.sub(r"</body>", API_JS + "</body>", html, count=1)
        f.write_text(html, encoding="utf-8")

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
