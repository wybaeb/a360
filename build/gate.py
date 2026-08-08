# -*- coding: utf-8 -*-
"""Парольный гейт: страница шифруется на сборке и расшифровывается в браузере.

Схема та же, что уже отработана на практике ВЭБ: PBKDF2-HMAC-SHA256 (200 000
итераций) → AES-256-GCM, всё совместимо с WebCrypto. В репозитории лежит только
шифротекст, ключ не хранится нигде.

После первого верного ввода пароль кладётся в localStorage под общим ключом
a360_pw — поэтому вторая и третья страницы артефактов открываются уже без ввода.
Поддержан и вход по фрагменту #k=<пароль>: фрагмент не уходит на сервер и
стирается из адресной строки до попытки входа.
"""
import base64
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITER = 200_000
STORAGE_KEY = "a360_pw"


def encrypt(plaintext: bytes, password: str):
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt,
                     iterations=ITER).derive(password.encode())
    ct = AESGCM(key).encrypt(iv, plaintext, None)   # ct||tag — как ждёт WebCrypto
    b = base64.b64encode
    return b(salt).decode(), b(iv).decode(), b(ct).decode()


GATE = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive">
<title>{title}</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
 padding:24px;background:linear-gradient(180deg,#e9f3ee,#ffffff);color:#2E3641;
 font-family:'SB Sans Text','Segoe UI',system-ui,-apple-system,Roboto,Arial,sans-serif}}
.card{{background:#fff;border:1px solid rgba(46,54,65,.13);border-radius:20px;
 box-shadow:0 20px 60px rgba(46,54,65,.12);padding:38px 34px;width:min(430px,94vw)}}
.mark{{width:46px;height:46px;border-radius:13px;margin-bottom:20px;
 background:linear-gradient(135deg,#7CD618,#20BA72);display:flex;align-items:center;
 justify-content:center;color:#fff;font-weight:800;font-size:15px;letter-spacing:-.3px}}
.eyebrow{{color:#20BA72;font-weight:800;font-size:11.5px;letter-spacing:.14em;
 text-transform:uppercase;margin-bottom:10px}}
h1{{font-size:24px;font-weight:800;margin:0 0 10px;line-height:1.2}}
p{{color:rgba(46,54,65,.72);font-size:14.5px;margin:0 0 22px;line-height:1.55}}
input{{width:100%;padding:14px 16px;font-size:16px;font-family:inherit;color:#2E3641;
 background:#f4f8f6;border:1.5px solid rgba(46,54,65,.15);border-radius:12px;outline:none}}
input:focus{{border-color:#20BA72;background:#fff}}
button{{margin-top:12px;width:100%;padding:14px;font-size:15px;font-weight:800;
 font-family:inherit;border:0;border-radius:12px;cursor:pointer;background:#20BA72;color:#fff}}
button:hover{{filter:brightness(1.07)}}
.err{{color:#E4572E;font-size:13px;height:18px;margin-top:11px;font-weight:700}}
.foot{{margin-top:20px;padding-top:16px;border-top:1px solid rgba(46,54,65,.11);
 font-size:12.5px;color:rgba(46,54,65,.48);line-height:1.55}}
</style></head>
<body>
<div class="card">
 <div class="mark">360</div>
 <div class="eyebrow">Карпов Курсы × Сбер</div>
 <h1>{heading}</h1>
 <p>{intro}</p>
 <input id="pw" type="password" placeholder="Пароль" autocomplete="current-password" autofocus>
 <button id="go">Открыть</button>
 <div class="err" id="err"></div>
 <div class="foot">Пароль назывался на вводной встрече и напечатан на слайде с QR-кодом.
   После первого ввода он сохраняется в браузере — остальные материалы откроются сами.</div>
</div>
<script>
const DATA={{salt:"{salt}",iv:"{iv}",ct:"{ct}",iter:{iter}}};
const KEY="{storage}";
const dec=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
async function unlock(pw){{
  const km=await crypto.subtle.importKey("raw",new TextEncoder().encode(pw),"PBKDF2",
    false,["deriveKey"]);
  const key=await crypto.subtle.deriveKey(
    {{name:"PBKDF2",salt:dec(DATA.salt),iterations:DATA.iter,hash:"SHA-256"}},
    km,{{name:"AES-GCM",length:256}},false,["decrypt"]);
  const pt=await crypto.subtle.decrypt({{name:"AES-GCM",iv:dec(DATA.iv)}},key,dec(DATA.ct));
  return new TextDecoder().decode(pt);
}}
async function attempt(pw,quiet){{
  try{{const html=await unlock(pw);localStorage.setItem(KEY,pw);
    document.open();document.write(html);document.close();}}
  catch(e){{
    if(quiet){{localStorage.removeItem(KEY);}}
    else{{document.getElementById("err").textContent="Неверный пароль";
      document.getElementById("pw").value="";document.getElementById("pw").focus();}}
  }}
}}
document.getElementById("go").onclick=()=>attempt(document.getElementById("pw").value,false);
document.getElementById("pw").addEventListener("keydown",
  e=>{{if(e.key==="Enter")attempt(e.target.value,false);}});
// Вход по фрагменту #k=<пароль>: фрагмент не уходит в запрос и не попадает в логи
// хостинга, из адресной строки стирается до попытки входа.
const frag=location.hash.match(/^#k=(.+)$/);
if(frag){{try{{history.replaceState(null,"",location.pathname+location.search);}}catch(_e){{}}
  attempt(decodeURIComponent(frag[1]),true);}}
else{{const cached=localStorage.getItem(KEY); if(cached) attempt(cached,true);}}
</script>
</body></html>
"""


def wrap(html: str, password: str, title: str, heading: str, intro: str) -> str:
    salt, iv, ct = encrypt(html.encode("utf-8"), password)
    return GATE.format(title=title, heading=heading, intro=intro,
                       salt=salt, iv=iv, ct=ct, iter=ITER, storage=STORAGE_KEY)
