# -*- coding: utf-8 -*-
"""Страница «Установка и настройка стенда».

Короткая версия того, что подробно расписано в репозитории практики: путь
с нуля до открытой тетради, отдельно — что нужно, чтобы поднять материалы
в JupyterHub банка. Полные тексты живут в репозитории и обновляются вместе
с кодом, поэтому здесь на них ссылки, а не копии.
"""

РЕПО = "https://github.com/wybaeb/bank-analytics-workshop"
УСТАНОВКА = f"{РЕПО}/blob/master/2.4_установка_стенда/2.4.1_установка.md"
JHUB = f"{РЕПО}/blob/master/2.4_установка_стенда/2.4.2_jupyterhub.md"

BODY = f"""
<header><div class="wrap">
  <div class="eyebrow">Материалы практики</div>
  <h1>Установка и настройка стенда</h1>
  <p class="lead">Три кейса практики работают на одном стенде: база с данными
     банка и система дашбордов. Поднимается локально одной командой, данные
     синтетические, ключи наружу не уходят. На чистой машине —
     10–15 минут, почти всё это время скачиваются образы.</p>
  <div class="meta">
    <span class="chip">Нужен <b>Docker</b></span>
    <span class="chip">Нужен <b>Python 3.10+</b></span>
    <span class="chip">Ключ ассистента — <b>для двух кейсов из трёх</b></span>
  </div>
</div></header>

<section><div class="wrap">
<h2><span class="num">1</span>Локально: пять шагов</h2>

<ol class="steps">
<li><b>Забрать папку практики.</b>
<pre><code>git clone {РЕПО}.git
cd bank-analytics-workshop</code></pre></li>

<li><b>Поставить библиотеки.</b>
<pre><code>pip install -r requirements.txt</code></pre>
<p class="sub" style="margin:8px 0 0">Пять штук: тетради, драйвер базы, pandas,
графики и клиент ассистента.</p></li>

<li><b>Заполнить <code>.env</code>.</b>
<pre><code>cp .env.example .env</code></pre>
<p>Вписать <code>GIGACHAT_AUTH_KEY</code> — строку авторизации из личного
кабинета GigaChat, и выбрать область ключа: <code>GIGACHAT_API_PERS</code>
для личного, <code>GIGACHAT_API_CORP</code> для корпоративного. Если под рукой
другой ассистент с OpenAI-совместимым интерфейсом — заполняются
<code>AI_PROVIDER_URL</code> и <code>AI_PROVIDER_TOKEN</code>, тетради
работают одинаково через оба пути.</p>
<p>Файл <code>.env</code> в репозиторий не попадает — ключ остаётся у вас.</p></li>

<li><b>Поднять стенд.</b>
<pre><code>./run.sh up</code></pre>
<p>Через минуту-две поднимутся база на порту 5433 и система дашбордов
на <code>localhost:3000</code>. Оба сервиса слушают только вашу машину,
учебные пароли лежат в <code>.env.example</code>.</p></li>

<li><b>Проверить, что всё сошлось.</b>
<pre><code>python3 tools/check_env.py</code></pre>
<p>Скрипт печатает библиотеки, переменные окружения, подключение к базе
с числом строк по таблицам, получение токена ассистента и доступность
дашбордов. <b>Значения ключей и паролей он не печатает</b> — только «задана,
длина N», поэтому вывод можно приложить к вопросу в поддержку.</p></li>
</ol>

<div class="card acc">
<h4>Как выглядит успех</h4>
<pre style="margin:0"><code>База данных
  ✓ localhost:5433/bank_training — PostgreSQL 16
  ✓ raw_applications: 3672 строк
  ✓ raw_stage_events: 14203 строк
  ✓ initiative_passport: 10 строк

Ассистент
  ✓ GigaChat: токен получен, модель GigaChat-2-Max

Итог
  ✓ всё на месте: можно открывать любую тетрадь практики</code></pre>
</div>

<p>Совпали числа строк — значит, данные загрузились правильно, и все числа
в материалах у вас воспроизведутся. Полный текст со всеми вариантами —
в <a href="{УСТАНОВКА}">документе установки</a>.</p>
</div></section>

<section><div class="wrap">
<h2><span class="num">2</span>В JupyterHub банка</h2>

<p>Тетради устроены просто: обычные ядра Python, расширений хаба не требуют.
Чтобы они заработали в корпоративном контуре, должны сойтись три вещи.</p>

<h3>Библиотеки в образе ядра</h3>
<p>Python 3.10 или новее и пять библиотек из <code>requirements.txt</code>:
<code>jupyter</code>, <code>psycopg2-binary</code>, <code>pandas</code>,
<code>matplotlib</code>, <code>requests</code>. Ставятся в образ или
командой <code>pip install --user -r requirements.txt</code>.</p>

<h3>Сетевые доступы и сертификаты</h3>
<div class="scroll">
<table>
<thead><tr><th>Куда</th><th>Зачем</th></tr></thead>
<tbody>
<tr><td>ваш сервер СУБД</td><td>все тетради с SQL</td></tr>
<tr><td><code>ngw.devices.sberbank.ru:9443</code></td><td>получение токена ассистента</td></tr>
<tr><td><code>gigachat.devices.sberbank.ru:443</code></td><td>запросы к модели</td></tr>
<tr><td>ваш BI</td><td>кейс с дашбордами</td></tr>
</tbody>
</table>
</div>
<p>Сертификат ассистента подписан НУЦ Минцифры: цепочку кладут в образ
и включают проверку переменной <code>GIGACHAT_VERIFY=1</code> либо указывают
файл в <code>GIGACHAT_CA_BUNDLE</code>. Без этого обращение к модели идёт
без проверки подлинности сервера — на учебной машине допустимо,
в корпоративном контуре нет.</p>

<h3>Переменные окружения</h3>
<p>Тетради не знают ничего, кроме имён переменных: сменить учебную базу
на рабочую — значит поменять значения, а не код.</p>
<div class="scroll">
<table>
<thead><tr><th>Переменная</th><th>Что задаёт</th></tr></thead>
<tbody>
<tr><td><code>GIGACHAT_AUTH_KEY</code>, <code>GIGACHAT_SCOPE</code></td>
    <td>ключ ассистента и область его действия</td></tr>
<tr><td><code>GIGACHAT_VERIFY</code> или <code>GIGACHAT_CA_BUNDLE</code></td>
    <td>проверка сертификата</td></tr>
<tr><td><code>PGHOST</code>, <code>PGPORT</code>, <code>PGDATABASE</code></td>
    <td>адрес рабочей базы</td></tr>
<tr><td><code>PGUSER</code>, <code>PGPASSWORD</code></td>
    <td>учётная запись — сервисная, только на чтение</td></tr>
</tbody>
</table>
</div>

<p>Задаются они администратором хаба — всем сразу через
<code>c.Spawner.environment</code>, в Kubernetes через
<code>singleuser.extraEnv</code> со ссылкой на Secret, персонально через
<code>pre_spawn_hook</code>. Секреты приходят из вашей секретницы, а не лежат
в конфигурационном файле. Все четыре способа с примерами —
в <a href="{JHUB}">инструкции по JupyterHub</a>.</p>

<div class="card warn">
<h4>Пароль базы константой в тетради</h4>
<p>Самый распространённый способ — и самый неудачный: пароль остаётся
в файле тетради вместе с выводом, уезжает в систему контроля версий,
на общий диск и в скриншот на созвоне. Замена — одна строка:</p>
<pre style="margin:0"><code>import os
conn = psycopg2.connect(
    host=os.environ["PGHOST"], dbname=os.environ["PGDATABASE"],
    user=os.environ["PGUSER"], password=os.environ["PGPASSWORD"])</code></pre>
<p style="margin:12px 0 0">Если переменных нет, а подключиться нужно сейчас —
<code>getpass.getpass()</code> спросит пароль в диалоге, и он не сохранится
в файле.</p>
</div>
</div></section>

<section><div class="wrap">
<h2><span class="num">3</span>Если что-то не поднялось</h2>
<div class="scroll">
<table>
<thead><tr><th>Симптом</th><th>Обычная причина</th><th>Что сделать</th></tr></thead>
<tbody>
<tr><td><code>port is already allocated</code></td><td>порт 5433 или 3000 занят</td>
    <td>поменять порт в <code>docker-compose.yml</code> и в <code>.env</code></td></tr>
<tr><td>дашборды не открываются пару минут</td><td>первый запуск</td>
    <td>подождать, <code>./run.sh status</code> покажет <code>healthy</code></td></tr>
<tr><td>в таблицах ноль строк</td><td>том остался от прерванной сборки</td>
    <td><code>./run.sh reset</code></td></tr>
<tr><td>токен ассистента не получен</td><td>нет выхода наружу, нет сертификатов
    или ключ другой области</td><td>проверить доступы и
    <code>GIGACHAT_SCOPE</code></td></tr>
<tr><td><code>ModuleNotFoundError</code> в тетради</td><td>тетрадь запущена
    другим интерпретатором</td><td>выбрать ядро того Python, где ставили
    библиотеки</td></tr>
<tr><td>агент отвечает текстом «Tool use: …»</td><td>провайдер не поддерживает
    вызов инструментов или ядро держит старую версию модуля</td>
    <td><b>Restart Kernel</b> и <b>Run All</b>; проверить, что провайдер умеет
    <code>tools</code></td></tr>
</tbody>
</table>
</div>

<div class="card">
<h4>Правило работы с данными</h4>
<p>Все наборы в стенде синтетические. В промпты ассистента идут только учебные
и обезличенные данные: реальные клиентские выгрузки во внешние сервисы
не отправляются. Это правило не про учебный стенд — оно про привычку,
которая остаётся после практики.</p>
</div>

<p class="sub">Дальше: <a href="case_cards.html">кейс карточного бизнеса</a>,
<a href="case_pipeline.html">кейс кредитного конвейера</a>,
<a href="case_portfolio.html">кейс портфеля инициатив</a>.</p>
</div></section>

<footer><div class="wrap">
  Аналитика 360 · материалы практической части.<br>
  Учебные пароли действуют только на вашей машине.
</div></footer>
"""
