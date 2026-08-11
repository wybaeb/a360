# -*- coding: utf-8 -*-
"""Тренажёр «Карта источников данных» (Шаг 1, T1_3).

Конструктор карты по маршруту вопрос → метрики → источники → качество →
master-source → действия. Три пресета — кейсы встречи (Продукт / Процесс /
Бизнес), у каждого встроенный эталон (переключатель «Эталон» — для показа
ведущим и самопроверки). Четвёртая вкладка — пустая карта своего
подразделения: это и есть домашний артефакт A1, кнопка экспорта собирает
его в Markdown по структуре template_data_source_map.md.

Эталоны здесь — те же, что в sber-a360-materials (example_filled_map.md,
example_filled_process.md, example_master_source.md): тренажёр их показывает,
репозиторий остаётся канонической копией. Промпты — дословно из
prompts_step1.md. Черновик участника живёт в localStorage браузера,
наружу ничего не отправляется.
"""
import json

TRUST = ["доверяю", "проверяю", "не доверяю"]
MTYPES = ["опережающая", "запаздывающая"]
ASPECTS = ["частота", "полнота", "дубли", "разрозненность", "пробелы",
           "определения", "справочники", "выбросы"]

PROMPT1 = """Ты — аналитик данных банка. Помоги руководителю подразделения составить карту источников данных.

Контекст: подразделение отвечает за [продукт / процесс], ключевое управленческое решение, которое я принимаю регулярно, — [решение].
Показатели, которыми я управляю: [список из 5–10 показателей].

Для каждого показателя предложи:
1) вероятные источники данных в банке (класс системы, а не конкретное название);
2) кто обычно является владельцем таких данных;
3) типичную частоту обновления;
4) типовые проблемы качества именно этого показателя;
5) 2–3 вопроса, которые стоит задать владельцу данных перед тем, как строить на этом решение.

Ответ — таблицей. В конце отдельно перечисли показатели, для которых источник обычно отсутствует и данные существуют только в чьей-то голове или в личном файле."""

PROMPT2 = """Ты — аналитик данных банка, специализируешься на процессной аналитике.

Вот мой процесс, как я его описываю словами: [4–8 предложений своими словами].

Сделай следующее:
1) разложи процесс на шаги и для каждого укажи, какой цифровой след он обычно оставляет и в системе какого класса;
2) отметь, где типично возникают четыре разрыва данных: дубли, разрозненность (нет сквозного ключа), пробелы (шаг не логируется), недостаточная частота обновления;
3) скажи, какие из этих разрывов мешают посчитать сквозное время процесса одной цифрой;
4) предложи, какой идентификатор мог бы стать сквозным ключом.

Ответ — таблицей по шагам плюс отдельный короткий список «что мешает посчитать сквозное время»."""

PROMPT3 = """Ты — методолог управленческой отчётности в банке.

Показатель: [название]. Он приходит ко мне из разных источников с разными значениями:
- источник A: [описание, как считает], значение [X]
- источник B: [описание, как считает], значение [Y]

1) Перечисли вероятные причины расхождения: разный период, разный момент признания, разные фильтры, разные справочники, разное определение самого показателя.
2) По каждой причине скажи, как её проверить за один запрос.
3) Предложи критерии выбора master-source и порекомендуй источник, обосновав выбор.
4) Сформулируй одно предложение для протокола, фиксирующее договорённость об источнике."""

PRESETS = {
    "product": {
        "name": "Кейс 1 · Продукт",
        "legend": ("Вы — руководитель продукта «Кредитная карта». Активация падает, план "
                   "не выполняется. Карта строится под решение: вкладываться в доставку, "
                   "в коммуникацию или в упрощение оформления. Уровень — один продукт."),
        "labels": {"src": "Источник / система", "gives": "Что даёт"},
        "checks": ["вычеркните источники, которые не назовёте у себя поимённо",
                   "показатели «данные только в голове» — начало списка дыр",
                   "два источника у показателя — кандидат в спор о цифрах"],
        "prompt": PROMPT1,
        "etalon": {
            "q": "Почему падает конверсия в активацию кредитной карты?",
            "metrics": [
                ["Активация за 30 дней", "опережающая", "% от выдач", "еженедельно"],
                ["Срок доставки (TAT)", "опережающая", "дни", "еженедельно"],
                ["Отказы на выпуске", "опережающая", "% заявок", "еженедельно"],
                ["Доход по продукту", "запаздывающая", "₽/мес.", "ежемесячно"]],
            "sources": [
                ["CRM", "заявка, канал, статусы до решения", "владелец CRM", "онлайн", "доверяю"],
                ["Витрина «Карточные продукты», DWH", "выдачи, активации, доход",
                 "владелец витрины", "раз в сутки", "доверяю"],
                ["Курьерская служба (подрядчик)", "статусы доставки",
                 "менеджер договора", "по запросу", "проверяю"],
                ["Навигатор BI", "сводный дашборд продукта", "владелец дашборда",
                 "раз в сутки", "доверяю"]],
            "quality": [
                ["полнота", "3 % заявок без корректного адреса — срок доставки по ним не считается"],
                ["дубли", "заявка из приложения и с сайта — две записи об одном клиенте"],
                ["определения", "в CRM «активация» = выпуск карты, в витрине = первая операция — источник спора о цифрах"]],
            "master": {
                "ind": "Активация кредитных карт",
                "a": "CRM: активация = выпуск карты", "av": "61 %",
                "b": "Витрина «Карточные продукты» DWH: активация = первая операция в 30 дней", "bv": "58 %",
                "choice": "Витрина «Карточные продукты» в DWH",
                "proto": ("Показатель активации кредитных карт для управленческой отчётности "
                          "берётся из витрины «Карточные продукты» DWH (активация — первая "
                          "операция в течение 30 дней с выдачи); показатель CRM используется "
                          "только для операционного контроля выпуска.")},
            "actions": [
                ["Сверить определение активации в CRM и в витрине, зафиксировать письменно",
                 "владелец витрины", "неделя"],
                ["Запросить регулярную выгрузку статусов курьерской службы вместо «по запросу»",
                 "менеджер договора", "две недели"],
                ["Починить 3 % заявок без адреса — найти шаг, где теряется поле",
                 "владелец процесса", "месяц"]],
        },
    },
    "process": {
        "name": "Кейс 2 · Процесс",
        "legend": ("Кредитный конвейер: подача → скоринг → андеррайтинг → оформление → выдача. "
                   "Задача — данные процесса, а не его оптимизация. Проверочный вопрос: "
                   "сквозное время одной цифрой — сегодня, без ручной сборки."),
        "labels": {"src": "Шаг → система", "gives": "Цифровой след"},
        "checks": ["предложения оптимизировать процесс — не задача Шага 1, игнорируйте",
                   "сквозное время обычно не считается по одной причине: нет общего ключа",
                   "шаг без цифрового следа — главный кандидат в «серую зону»"],
        "prompt": PROMPT2,
        "etalon": {
            "q": "Где конвейер теряет время — и можем ли мы доказать это цифрой?",
            "metrics": [
                ["Сквозное время заявки (подача → выдача)", "запаздывающая", "часы", "еженедельно"],
                ["Время на этапе", "опережающая", "часы", "ежедневно"],
                ["Доля возвратов на доработку", "опережающая", "% заявок", "ежедневно"],
                ["Операций на сотрудника (андеррайтинг)", "опережающая", "шт./день", "ежедневно"]],
            "sources": [
                ["Подача → CRM", "заявка, канал, отметка времени", "владелец CRM", "онлайн", "доверяю"],
                ["Скоринг → скоринговая система", "решение, скорбалл, запрос в БКИ",
                 "владелец модели", "онлайн", "доверяю"],
                ["Андеррайтинг → личный реестр Excel", "решение и комментарий, времени нет",
                 "руководитель группы", "вручную, раз в день", "не доверяю"],
                ["Оформление → CRM + отделение", "статус документов", "владелец CRM", "онлайн", "доверяю"],
                ["Выдача → АБС", "договор, транзакция выдачи", "владелец АБС", "онлайн", "доверяю"]],
            "quality": [
                ["дубли", "заявка из приложения, досозданная оператором, живёт двумя записями"],
                ["разрозненность", "у CRM номер заявки, у АБС номер договора — общего ключа нет, путь заявки не склеивается"],
                ["пробелы", "андеррайтинг в личном Excel: время входа и выхода заявки не логируется"],
                ["частота", "реестр обновляется раз в день вручную — к обеду картина очереди неверна"]],
            "master": {
                "ind": "Сквозное время заявки",
                "a": "Ручная сборка из Excel-реестра: без отметок времени", "av": "не считается",
                "b": "Журнал статусов конвейера (CRM + скоринг) после введения сквозного ключа", "bv": "время этапов",
                "choice": "Журнал статусов конвейера — после договорённости о сквозном ID заявки",
                "proto": ("Временем этапов конвейера считается журнал статусов CRM и скоринга "
                          "по сквозному ID заявки; личный реестр андеррайтинга источником "
                          "времени не является.")},
            "actions": [
                ["Договориться о сквозном ID заявки и его передаче в АБС",
                 "владельцы CRM, скоринга, АБС", "две недели"],
                ["Перевести реестр андеррайтинга в систему со статусами и временем",
                 "руководитель группы + владелец CRM", "месяц"],
                ["Включить дедупликацию заявок по клиенту и продукту на входе",
                 "владелец CRM", "месяц"]],
        },
    },
    "business": {
        "name": "Кейс 3 · Бизнес",
        "legend": ("На комитет приходят две цифры активации: CRM — 61 %, витрина DWH — 58 %. "
                   "Полчаса совещания уходит на спор о цифрах. Задача — выбрать master-source "
                   "и сформулировать одно предложение для протокола. Уровни: продукт и портфель."),
        "labels": {"src": "Источник / система", "gives": "Как считает"},
        "checks": ["проверку начинайте с определения показателя, а не с выгрузок",
                   "источник без живого владельца не может быть официальным",
                   "фразу для протокола доведите до одного предложения, понятного не вашей команде"],
        "prompt": PROMPT3,
        "etalon": {
            "q": "Почему у одного показателя на совещании две разные цифры — и какая из них правда для решения?",
            "metrics": [
                ["Активация кредитных карт", "запаздывающая", "% выдач", "еженедельно"]],
            "sources": [
                ["CRM", "активация = выпуск карты → 61 %", "владелец CRM", "онлайн", "проверяю"],
                ["Витрина «Карточные продукты», DWH", "активация = первая операция в 30 дней → 58 %",
                 "владелец витрины", "раз в сутки", "доверяю"]],
            "quality": [
                ["определения", "источники считают разные события; период, фильтры и справочники совпадают"],
                ["полнота", "3 п.п. разницы — карты, выпущенные, но ни разу не использованные"]],
            "master": {
                "ind": "Активация кредитных карт",
                "a": "CRM: активация = выпуск карты", "av": "61 %",
                "b": "Витрина «Карточные продукты» DWH: активация = первая операция в 30 дней", "bv": "58 %",
                "choice": "Витрина «Карточные продукты» в DWH: по смыслу решения, прослеживается до транзакций, есть владелец и регламент",
                "proto": ("Показатель активации кредитных карт для управленческой отчётности "
                          "берётся из витрины «Карточные продукты» DWH (активация — первая "
                          "операция в течение 30 дней с выдачи); показатель CRM используется "
                          "только для операционного контроля выпуска.")},
            "actions": [
                ["Зафиксировать выбор master-source в протоколе комитета", "руководитель", "эта неделя"],
                ["Сверить определение активации по всем продуктам портфеля", "методолог отчётности", "месяц"],
                ["Убрать CRM-цифру из отчёта комитета, оставить в операционном контуре", "владелец отчёта", "две недели"]],
        },
    },
    "own": {
        "name": "Моё подразделение · A1",
        "legend": ("Домашний артефакт A1: карта источников своего подразделения, 1–2 страницы, "
                   "срок — до Шага 2 (20 августа). Встреча начинается с разбора принесённых карт. "
                   "Заполняйте по тому же маршруту; эталоны — во вкладках кейсов. "
                   "В публичный GigaChat закрытые данные и внутренние имена систем не отправляем."),
        "labels": {"src": "Источник / система", "gives": "Что даёт"},
        "checks": ["есть показатели всех трёх контекстов (продукт / процесс / бизнес)",
                   "у каждого показателя назван конкретный источник и владелец",
                   "отмечена хотя бы одна «дыра» и хотя бы один конфликт источников",
                   "для конфликтующих показателей выбран master-source с обоснованием",
                   "карта заканчивается тремя действиями, а не таблицей"],
        "prompt": PROMPT1,
        "etalon": None,
    },
}


def body():
    presets_json = json.dumps(PRESETS, ensure_ascii=False)
    return """
<header><div class="wrap">
  <div class="eyebrow">Карпов Курсы × Сбер · Аналитика 360 · Шаг 1</div>
  <h1>Тренажёр: карта источников данных</h1>
  <p class="lead">Конструктор карты по маршруту встречи: вопрос → метрики → источники →
     проверка качества → master-source → действия. Три кейса с эталонами и четвёртая
     вкладка — карта вашего подразделения, которая экспортируется в артефакт A1.</p>
  <div class="meta">
    <span class="chip">Кейсы <b>3 + свой</b></span>
    <span class="chip">Эталоны <b>внутри</b></span>
    <span class="chip">Черновик <b>в вашем браузере</b></span>
  </div>
</div></header>

<section><div class="wrap">
<style>
.dmz-tabs{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 14px}
.dmz-tab{border:1.5px solid var(--acc);background:#fff;color:var(--acc);border-radius:20px;
  padding:7px 14px;cursor:pointer;font:inherit;font-size:14.5px}
.dmz-tab.on{background:var(--acc);color:#fff}
.dmz-mode{display:flex;gap:8px;align-items:center;margin:0 0 12px}
.dmz-mode button{border:1.5px solid #8B5CD6;background:#fff;color:#6b41ad;border-radius:8px;
  padding:6px 12px;cursor:pointer;font:inherit;font-size:14px}
.dmz-mode button.on{background:#8B5CD6;color:#fff}
.dmz h3{margin:20px 0 6px}
.dmz .hint{font-size:13.5px;opacity:.72;margin:0 0 8px}
.dmz table{width:100%;border-collapse:collapse;font-size:14px}
.dmz th,.dmz td{border:1px solid #d8d8d8;padding:5px 7px;text-align:left;vertical-align:top}
.dmz th{background:#f2f6f4;font-weight:600}
.dmz input[type=text],.dmz textarea,.dmz select{width:100%;border:1px solid #c9c9c9;
  border-radius:6px;padding:5px 7px;font:inherit;font-size:14px;box-sizing:border-box;background:#fff}
.dmz textarea{min-height:52px;resize:vertical}
.dmz .addrow{margin:6px 0 0;border:1px dashed #9a9a9a;background:#fff;border-radius:8px;
  padding:4px 12px;cursor:pointer;font:inherit;font-size:13.5px}
.dmz .del{border:0;background:none;color:#c33;cursor:pointer;font-size:15px;padding:0 4px}
.dmz .btns{display:flex;gap:10px;flex-wrap:wrap;margin:22px 0 4px}
.dmz .btns button{border:0;border-radius:9px;padding:9px 16px;cursor:pointer;font:inherit;font-size:14.5px}
.dmz .b-exp{background:#0f7a46;color:#fff}
.dmz .b-clr{background:#eee;color:#333}
.dmz .etview table{background:#faf7ff}
.dmz .etview .kvline{margin:4px 0}
.dmz .badge-et{display:inline-block;background:#8B5CD6;color:#fff;border-radius:6px;
  padding:2px 8px;font-size:12.5px;margin-left:8px;vertical-align:middle}
.dmz .cl label{display:block;margin:4px 0;font-size:14.5px}
.dmz .okmsg{color:#0f7a46;font-size:13.5px;margin-left:8px}
</style>

<div class="dmz">
  <div class="dmz-tabs" id="dmzTabs"></div>
  <div class="card acc"><p id="dmzLegend" style="margin:0"></p></div>
  <div class="dmz-mode" id="dmzMode">
    <button id="mMy" class="on" type="button">Моя карта</button>
    <button id="mEt" type="button">Эталон</button>
    <span class="hint" id="mHint"></span>
  </div>
  <div id="dmzForm"></div>
  <div id="dmzEt" class="etview" style="display:none"></div>

  <h3>Промпт для GigaChat</h3>
  <p class="hint">Квадратные скобки — ваши подстановки. Ассистент не знает вашего ландшафта:
  его польза — структура и вопросы владельцу данных, а не факты. Закрытые данные банка
  в публичный GigaChat не отправляем.</p>
  <div class="prompt"><button class="copy" type="button">Копировать</button><pre id="dmzPrompt"></pre></div>
  <div id="dmzChecks" class="card"></div>

  <h3>Чек-лист самопроверки</h3>
  <div class="cl" id="dmzCl"></div>

  <div class="btns">
    <button class="b-exp" id="bExport" type="button">Экспорт карты в Markdown</button>
    <button class="b-clr" id="bClear" type="button">Очистить кейс</button>
    <span class="okmsg" id="expMsg"></span>
  </div>
  <p class="sub">Экспортированный файл — ваш артефакт A1 (для вкладки «Моё подразделение»)
  или конспект кейса. Канонические эталоны и шаблоны — в
  <a href="https://github.com/wybaeb/sber-a360-materials/tree/master/step1_data_landscape">репозитории материалов</a>.</p>
</div>

<script>
var PRESETS=__PRESETS__;
var CL7=["Есть показатели всех трёх контекстов (продукт / процесс / бизнес)",
 "У каждого показателя назван конкретный источник и владелец",
 "Для 2–3 показателей построено дерево метрик (см. шаблон дерева)",
 "Хотя бы одна связь помечена как «предсказывает», а не «определяет»",
 "Отмечена хотя бы одна «дыра» и хотя бы один конфликт источников",
 "Для конфликтов выбран master-source и сформулировано обоснование",
 "Карта заканчивается тремя действиями, а не таблицей"];
var cur="product",mode="my";
var $=function(id){return document.getElementById(id)};

function key(){return "a360_dmz_"+cur}
function blank(){return {q:"",metrics:[["","опережающая","",""]],
  sources:[["","","","",""]],quality:[["определения",""]],
  master:{ind:"",a:"",av:"",b:"",bv:"",choice:"",proto:""},
  actions:[["","",""]],cl:[]}}
function load(){try{var s=localStorage.getItem(key());return s?JSON.parse(s):blank()}catch(e){return blank()}}
function save(d){try{localStorage.setItem(key(),JSON.stringify(d))}catch(e){}}

function esc(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}

function rowsTable(id,heads,rows,builders){
  var h="<table><tr>"+heads.map(function(x){return "<th>"+esc(x)+"</th>"}).join("")+"<th></th></tr>";
  rows.forEach(function(r,i){
    h+="<tr>"+builders.map(function(b,j){return "<td>"+b(r[j],i,j)+"</td>"}).join("");
    h+='<td><button class="del" type="button" data-t="'+id+'" data-i="'+i+'" title="удалить">×</button></td></tr>';
  });
  h+="</table>";
  h+='<button class="addrow" type="button" data-add="'+id+'">+ строка</button>';
  return h;
}
function inp(t,i,j){return function(v){return '<input type="text" data-t="'+t+'" data-i="'+i+'" data-j="'+j+'" value="'+esc(v)+'">'}}
function sel(t,opts){return function(v,i,j){
  return '<select data-t="'+t+'" data-i="'+i+'" data-j="'+j+'">'+opts.map(function(o){
    return '<option'+(o===v?" selected":"")+'>'+esc(o)+"</option>"}).join("")+"</select>"}}

function renderForm(){
  var p=PRESETS[cur],d=load(),L=p.labels;
  function cells(t,n,selIdx,selOpts){
    var out=[];for(var j=0;j<n;j++){out.push(j===selIdx?sel(t,selOpts):(function(jj){
      return function(v,i){return inp(t,i,jj)(v)}})(j));}
    return out;}
  var h="";
  h+="<h3>1 · Управленческий вопрос</h3><p class='hint'>Решение, ради которого строится карта, — не «про данные вообще».</p>";
  h+='<textarea id="fQ">'+esc(d.q)+"</textarea>";
  h+="<h3>2 · Метрики</h3><p class='hint'>5–10 показателей, после которых что-то меняется. Опережающие предсказывают, запаздывающие констатируют.</p>";
  h+=rowsTable("metrics",["Метрика","Тип","Единица","Частота наблюдения"],d.metrics,cells("metrics",4,1,__MTYPES__));
  h+="<h3>3 · Источники</h3>";
  h+=rowsTable("sources",[L.src,L.gives,"Владелец","Обновление","Доверие"],d.sources,cells("sources",5,4,__TRUST__));
  h+="<h3>4 · Проверка качества</h3><p class='hint'>Что нашли: дыры, дубли, расхождения определений.</p>";
  h+=rowsTable("quality",["Аспект","Что нашли"],d.quality,[sel("quality",__ASPECTS__),function(v,i){return inp("quality",i,1)(v)}]);
  h+="<h3>5 · Master-source</h3><p class='hint'>Показатель со «спором о цифрах»: два источника, выбор, фраза для протокола.</p>";
  h+='<table><tr><th style="width:28%">Показатель</th><td><input type="text" data-m="ind" value="'+esc(d.master.ind)+'"></td></tr>'
   +'<tr><th>Источник A: как считает</th><td><input type="text" data-m="a" value="'+esc(d.master.a)+'"></td></tr>'
   +'<tr><th>Значение A</th><td><input type="text" data-m="av" value="'+esc(d.master.av)+'"></td></tr>'
   +'<tr><th>Источник B: как считает</th><td><input type="text" data-m="b" value="'+esc(d.master.b)+'"></td></tr>'
   +'<tr><th>Значение B</th><td><input type="text" data-m="bv" value="'+esc(d.master.bv)+'"></td></tr>'
   +'<tr><th>Выбор master-source и почему</th><td><input type="text" data-m="choice" value="'+esc(d.master.choice)+'"></td></tr>'
   +'<tr><th>Фраза для протокола</th><td><textarea data-m="proto">'+esc(d.master.proto)+"</textarea></td></tr></table>";
  h+="<h3>6 · Действия</h3><p class='hint'>То, ради чего строилась карта: что сверить, у кого запросить доступ, что починить.</p>";
  h+=rowsTable("actions",["Что","Кому","Срок"],d.actions,cells("actions",3,-1,null));
  $("dmzForm").innerHTML=h;
}

function renderEt(){
  var p=PRESETS[cur],e=p.etalon;
  if(!e){$("dmzEt").innerHTML="";return}
  function tbl(heads,rows){return '<div class="scroll"><table><tr>'+heads.map(function(x){return "<th>"+esc(x)+"</th>"}).join("")+"</tr>"
    +rows.map(function(r){return "<tr>"+r.map(function(c){return "<td>"+esc(c)+"</td>"}).join("")+"</tr>"}).join("")+"</table></div>"}
  var L=p.labels,h="";
  h+='<h3>1 · Вопрос <span class="badge-et">эталон</span></h3><p>'+esc(e.q)+"</p>";
  h+="<h3>2 · Метрики</h3>"+tbl(["Метрика","Тип","Единица","Частота"],e.metrics);
  h+="<h3>3 · Источники</h3>"+tbl([L.src,L.gives,"Владелец","Обновление","Доверие"],e.sources);
  h+="<h3>4 · Проверка качества</h3>"+tbl(["Аспект","Что нашли"],e.quality);
  h+="<h3>5 · Master-source</h3><div class='card'>"
   +"<p class='kvline'><b>Показатель:</b> "+esc(e.master.ind)+"</p>"
   +"<p class='kvline'><b>A:</b> "+esc(e.master.a)+" → "+esc(e.master.av)+"</p>"
   +"<p class='kvline'><b>B:</b> "+esc(e.master.b)+" → "+esc(e.master.bv)+"</p>"
   +"<p class='kvline'><b>Выбор:</b> "+esc(e.master.choice)+"</p>"
   +"<p class='kvline'><b>Протокол:</b> «"+esc(e.master.proto)+"»</p></div>";
  h+="<h3>6 · Действия</h3>"+tbl(["Что","Кому","Срок"],e.actions);
  $("dmzEt").innerHTML=h;
}

function renderMeta(){
  var p=PRESETS[cur],d=load();
  $("dmzLegend").textContent=p.legend;
  $("dmzPrompt").textContent=p.prompt;
  $("dmzChecks").innerHTML="<b>Что проверить в ответе GigaChat:</b><ul style='margin:6px 0 0'>"
    +p.checks.map(function(c){return "<li>"+esc(c)+"</li>"}).join("")+"</ul>";
  $("dmzCl").innerHTML=CL7.map(function(c,i){
    return '<label><input type="checkbox" data-cl="'+i+'"'+(d.cl&&d.cl.indexOf(i)>=0?" checked":"")+"> "+esc(c)+"</label>"}).join("");
  var hasEt=!!p.etalon;
  $("mEt").style.display=hasEt?"":"none";
  $("mHint").textContent=hasEt?"«Эталон» — разбор со встречи; ваш черновик при просмотре не теряется.":"У своего кейса эталона нет — сверяйтесь с кейсами 1–3.";
  if(!hasEt&&mode==="et"){mode="my"}
  $("mMy").className=mode==="my"?"on":"";$("mEt").className=mode==="et"?"on":"";
  $("dmzForm").style.display=mode==="my"?"":"none";
  $("dmzEt").style.display=mode==="et"?"":"none";
}

function renderTabs(){
  $("dmzTabs").innerHTML=Object.keys(PRESETS).map(function(k){
    return '<button class="dmz-tab'+(k===cur?" on":"")+'" type="button" data-case="'+k+'">'+esc(PRESETS[k].name)+"</button>"}).join("");
}

function renderAll(){renderTabs();renderMeta();renderForm();renderEt()}

function collect(){
  var d=load();d.q=$("fQ")?$("fQ").value:d.q;
  ["metrics","sources","quality","actions"].forEach(function(t){
    var m={};document.querySelectorAll('[data-t="'+t+'"]').forEach(function(el){
      if(el.tagName==="BUTTON")return;
      var i=+el.dataset.i,j=+el.dataset.j;(m[i]=m[i]||[])[j]=el.value;});
    var rows=Object.keys(m).sort(function(a,b){return a-b}).map(function(i){return m[i]});
    if(rows.length)d[t]=rows;});
  document.querySelectorAll("[data-m]").forEach(function(el){d.master[el.dataset.m]=el.value});
  d.cl=[];document.querySelectorAll("[data-cl]").forEach(function(el){if(el.checked)d.cl.push(+el.dataset.cl)});
  return d;
}

document.addEventListener("input",function(e){
  if(e.target.closest(".dmz"))save(collect());
});
document.addEventListener("change",function(e){
  if(e.target.closest(".dmz"))save(collect());
});
document.addEventListener("click",function(e){
  var t=e.target;
  if(t.dataset&&t.dataset.case){save(collect());cur=t.dataset.case;mode="my";renderAll();return}
  if(t.id==="mMy"||t.id==="mEt"){save(collect());mode=t.id==="mEt"?"et":"my";renderMeta();return}
  if(t.dataset&&t.dataset.add){var d=collect();
    d[t.dataset.add].push(t.dataset.add==="quality"?["определения",""]:
      t.dataset.add==="metrics"?["","опережающая","",""]:
      t.dataset.add==="actions"?["","",""]:["","","","",""]);
    save(d);renderForm();return}
  if(t.classList&&t.classList.contains("del")){var d2=collect();
    d2[t.dataset.t].splice(+t.dataset.i,1);
    if(!d2[t.dataset.t].length)d2[t.dataset.t]=t.dataset.t==="quality"?[["определения",""]]:
      t.dataset.t==="metrics"?[["","опережающая","",""]]:
      t.dataset.t==="actions"?[["","",""]]:[["","","","",""]];
    save(d2);renderForm();return}
  if(t.id==="bClear"){if(confirm("Стереть черновик этого кейса?")){localStorage.removeItem(key());renderAll()}return}
  if(t.id==="bExport"){exportMd();return}
});

function exportMd(){
  var d=collect();save(d);var p=PRESETS[cur],L=p.labels;
  function row(r){return "| "+r.map(function(c){return String(c||"—").replace(/\\|/g,"/")}).join(" | ")+" |"}
  var m=["# Карта источников данных — "+p.name,"",
    "> вопрос → метрика → категории данных → источники → проверка качества → master-source → действия","",
    "## 1. Вопрос","",d.q||"—","","## 2. Метрики","",
    row(["Метрика","Тип","Единица","Частота"]),"|---|---|---|---|"]
    .concat(d.metrics.map(row))
    .concat(["","## 3. Источники","",row([L.src,L.gives,"Владелец","Обновление","Доверие"]),"|---|---|---|---|---|"])
    .concat(d.sources.map(row))
    .concat(["","## 4. Проверка качества",""])
    .concat(d.quality.map(function(r){return "- **"+(r[0]||"—")+":** "+(r[1]||"—")}))
    .concat(["","## 5. Master-source","",
      "- Показатель: "+(d.master.ind||"—"),
      "- Источник A: "+(d.master.a||"—")+" → "+(d.master.av||"—"),
      "- Источник B: "+(d.master.b||"—")+" → "+(d.master.bv||"—"),
      "- Выбор: "+(d.master.choice||"—"),
      "- Протокол: «"+(d.master.proto||"—")+"»","",
      "## 6. Действия","",row(["Что","Кому","Срок"]),"|---|---|---|"])
    .concat(d.actions.map(row)).join("\\n")+"\\n";
  var a=document.createElement("a");
  a.href=URL.createObjectURL(new Blob([m],{type:"text/markdown"}));
  a.download="A1_карта_источников_"+cur+".md";a.click();
  if(navigator.clipboard&&window.isSecureContext)navigator.clipboard.writeText(m);
  $("expMsg").textContent="Файл скачан и скопирован в буфер";
  setTimeout(function(){$("expMsg").textContent=""},2600);
}

renderAll();
</script>
</div></section>

<footer><div class="wrap">
  Аналитика 360 · Шаг 1 · тренажёр карты источников. Черновики хранятся только в вашем
  браузере; все данные в кейсах синтетические.
</div></footer>
""".replace("__PRESETS__", presets_json)\
   .replace("__MTYPES__", json.dumps(MTYPES, ensure_ascii=False))\
   .replace("__TRUST__", json.dumps(TRUST, ensure_ascii=False))\
   .replace("__ASPECTS__", json.dumps(ASPECTS, ensure_ascii=False))


BODY = body()
