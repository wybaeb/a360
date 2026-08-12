# -*- coding: utf-8 -*-
"""Тренажёр «Срок эксперимента» (T2, задание владельца 12.08).

Интерактивная страница: участник выбирает метрику из кейсов курса и двигает
бегунок «клиентов в эксперименте в день». Тренажёр считает целевой объём
выборки по той же формуле, что разобрана в справочнике (n = (Z·σ/E)²,
Z = 1,96), и раскладывает срок эксперимента на две фазы:

    фаза 1 — набор участников до целевого объёма (n / приток, дней);
    фаза 2 — горизонт метрики (участники набраны, данные ещё копятся).

SVG-таймлайн перестраивается на каждом движении бегунка. Главный урок
показан явно: бегунок сжимает только фазу 1 — горизонт метрики (отток за
90 дней, LTV за полгода) не ускоряется никаким потоком участников.

Визуальная схема двух фаз — та же, что в статичной фигуре accumulation()
из longread_figs.py (лонгрид-справочник, раздел «Эксперимент и накопление»):
здесь она оживлена расчётом. Параметры метрик — учебные, согласованы
с кейсами metrics_data.py: активация 30 дн (m-act), отток 90 дн (m-churn),
конверсия корпоративного блока (m-u_conv), TAT процесса (m-u_tat),
LTV портфеля (m-u_ltv). Наружу страница ничего не отправляет; внешних
зависимостей нет.

Подключение к сборке (build_pages.py) делает оркестратор: модуль экспортирует
BODY / TITLE / CRUMB в том же виде, что trainer_map.
"""

import json
import math

Z = 1.96

NBSP = " "  # узкий неразрывный пробел для тысяч


def _fi(n):
    return f"{n:,}".replace(",", NBSP)


def _n_share(p, e):
    """Объём выборки для доли: n = Z²·p(1−p)/E²."""
    return math.ceil(Z * Z * p * (1 - p) / (e * e))


def _n_sigma(s, e):
    """Объём выборки для средней величины: n = (Z·σ/E)²."""
    return math.ceil((Z * s / e) ** 2)


def _m(id_, tab, name, n, formula, unit_n, horizon, note, link_text, link_href,
       flow_label, fmin, fmax, fstep, fdef):
    return dict(id=id_, tab=tab, name=name, n=n,
                formula=formula + " ≈ " + _fi(n),
                unitN=unit_n, horizon=horizon, note=note,
                linkText=link_text, linkHref=link_href,
                flowLabel=flow_label, fmin=fmin, fmax=fmax, fstep=fstep, fdef=fdef)


METRICS = [
    _m("act", "Розница · активация",
       "Розница: активация за 30 дней",
       _n_share(0.58, 0.03),
       "n = Z²·p(1−p) / E² = 1,96² × 0,58 × 0,42 / 0,03²",
       "клиентов", 30,
       "Доля карт с первой операцией в 30 дней после выдачи — метрика кейса розницы. "
       "Учебные параметры: базовая доля 58 %, допустимая погрешность ±3 п.п. "
       "Горизонт метрики — 30 дней наблюдения за каждым участником.",
       "определение метрики «Активация за 30 дней» — в справочнике",
       "longread_metrics.html#m-act",
       "Клиентов в эксперименте в день", 20, 1000, 20, 100),
    _m("churn", "Розница · отток",
       "Розница: отток за 90 дней",
       _n_share(0.12, 0.02),
       "n = Z²·p(1−p) / E² = 1,96² × 0,12 × 0,88 / 0,02²",
       "клиентов", 90,
       "Доля клиентов без операций за 90 дней. Учебные параметры: базовая доля 12 %, "
       "допустимая погрешность ±2 п.п. Горизонт — 90 дней: отток быстрее не измеряется "
       "по построению.",
       "определение метрики «Отток за 90 дней» — в справочнике",
       "longread_metrics.html#m-churn",
       "Клиентов в эксперименте в день", 20, 1000, 20, 100),
    _m("corp", "Корпоративный блок",
       "Корпоративный блок: конверсия встречи в сделку",
       _n_share(0.25, 0.05),
       "n = Z²·p(1−p) / E² = 1,96² × 0,25 × 0,75 / 0,05²",
       "встреч", 60,
       "Конверсия встречи в сделку в корпоративном блоке. Учебные параметры: базовая "
       "конверсия 25 %, допустимая погрешность ±5 п.п. Поток встреч мал по природе кейса, "
       "а цикл сделки — 60 дней: даже набранные участники дают результат только после "
       "завершения цикла.",
       "определение метрики «Конверсия этапа» — в справочнике",
       "longread_metrics.html#m-u_conv",
       "Встреч с клиентами в день", 1, 30, 1, 6),
    _m("tat", "Внутренние процессы",
       "Внутренние процессы: срок обработки (TAT)",
       _n_sigma(2.0, 0.5),
       "n = (Z·σ / E)² = (1,96 × 2 / 0,5)²",
       "заявок", 14,
       "Средний срок обработки заявки во внутреннем процессе. Учебные параметры: "
       "разброс σ = 2 дня, допустимая погрешность ±0,5 дня. Горизонт наблюдения — "
       "14 дней: заявка должна пройти процесс целиком, включая хвост долгих случаев.",
       "определение метрики «Время процесса» — в справочнике",
       "longread_metrics.html#m-u_tat",
       "Заявок в эксперименте в день", 5, 200, 5, 20),
    _m("ltv", "Портфель · LTV",
       "Портфель: LTV и удержание за 180 дней",
       _n_sigma(40, 4),
       "n = (Z·σ / E)² = (1,96 × 40 / 4)²",
       "клиентов", 180,
       "Ценность клиента и удержание в портфельном управлении. Учебные параметры: "
       "разброс σ = 40 т₽ на клиента, допустимая погрешность ±4 т₽. Горизонт метрики — "
       "180 дней: ценность накапливается полгода, и приток участников этот срок "
       "не сокращает.",
       "определение метрики «Ценность клиента (LTV)» — в справочнике",
       "longread_metrics.html#m-u_ltv",
       "Клиентов в эксперименте в день", 20, 1000, 20, 100),
]

TITLE = "Тренажёр: срок эксперимента · Аналитика 360"
CRUMB = "Тренажёр: срок эксперимента"

_BODY_TMPL = """
<header><div class="wrap">
  <div class="eyebrow">Карпов Курсы × Сбер · Аналитика 360</div>
  <h1>Тренажёр: срок эксперимента</h1>
  <p class="lead">Рассчитанный объём выборки — ещё не срок. Эксперимент живёт
     две фазы: сначала набираются участники до целевого объёма, затем — данные,
     пока не пройдёт горизонт метрики. Выберите метрику кейса и двигайте бегунок
     притока — таймлайн покажет, какая часть срока сжимается, а какая нет.</p>
  <div class="meta">
    <span class="chip">Метрики <b>из кейсов курса</b></span>
    <span class="chip">Формула объёма <b>одна</b></span>
    <span class="chip">Расчёт <b>в вашем браузере</b></span>
  </div>
</div></header>

<section><div class="wrap">
<style>
.exp-tabs{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 14px}
.exp-tab{border:1.5px solid var(--acc);background:#fff;color:var(--acc);border-radius:20px;
  padding:7px 14px;cursor:pointer;font:inherit;font-size:14.5px}
.exp-tab.on{background:var(--acc);color:#fff}
.exp-slider{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin:14px 0 6px}
.exp-slider input[type=range]{flex:1 1 260px;accent-color:var(--acc);height:28px}
.exp-slider .val{font-weight:800;font-size:19px;min-width:64px;text-align:right;
  font-variant-numeric:tabular-nums}
.exp-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0 6px}
.exp-stat{background:var(--surf);border:1px solid var(--line);border-radius:12px;
  padding:12px 14px}
.exp-stat b{display:block;font-size:24px;line-height:1.15;font-variant-numeric:tabular-nums}
.exp-stat span{font-size:13.5px;color:var(--ink3)}
.exp-stat.hot{background:var(--acc-soft);border-color:var(--acc-line)}
.exp-tl{background:var(--surf);border:1px solid var(--line);border-radius:14px;
  padding:16px 14px 8px;margin:14px 0 6px}
.exp-tl svg{width:100%;height:auto;display:block}
.exp-concl{font-size:15px;color:var(--ink2);margin:8px 2px 0}
.exp-fml{font-size:16px}
@media(max-width:700px){.exp-stats{grid-template-columns:repeat(2,1fr)}}
</style>

<h2>Две фазы одного эксперимента</h2>
<p>Целевой объём выборки считается до старта — по формуле из
<a href="longread_metrics.html#sample-formula">раздела «Формула объёма выборки»</a>
справочника. Дальше срок складывается из двух частей: <b>фаза 1</b> — участники
накапливаются до целевого объёма со скоростью притока; <b>фаза 2</b> — участники
набраны, но по каждому ещё должен пройти горизонт метрики. Досрочно завершить
можно только набор — и только когда участников уже достаточно.</p>

<div class="exp-tabs" id="expTabs"></div>
<div class="card acc"><b id="mName"></b><p id="mNote" style="margin:6px 0 0"></p></div>

<div class="exp-slider">
  <span id="flowLab" style="font-weight:700"></span>
  <input type="range" id="flow" min="20" max="1000" step="20" value="100">
  <span class="val" id="flowVal">100</span>
</div>

<div class="exp-stats">
  <div class="exp-stat"><b id="sN"></b><span id="sNu"></span></div>
  <div class="exp-stat"><b id="sP1"></b><span>фаза 1 · набор участников</span></div>
  <div class="exp-stat"><b id="sP2"></b><span>фаза 2 · горизонт метрики</span></div>
  <div class="exp-stat hot"><b id="sTot"></b><span>срок эксперимента</span></div>
</div>

<div class="exp-tl"><div id="tl"></div></div>
<p class="exp-concl" id="concl"></p>

<div class="card">
<h4>Расчёт этого таймлайна</h4>
<p class="exp-fml" style="margin-bottom:8px"><b id="fml"></b> <span id="fmlU"></span></p>
<p style="margin:0" id="fml2" class="sub"></p>
</div>

<div class="card acc">
<h4>Бегунок сжимает только фазу 1</h4>
<p style="margin:0">Приток участников сокращает набор до целевого объёма, но горизонт
второй фазы — свойство самой метрики, а не бюджета: отток за 90 дней требует прожить
90 дней, а LTV за полгода не ускоряется никаким потоком. Эксперимент, закрытый до
горизонта, меряет нетерпение, а не эффект.</p>
</div>

<p>Точный расчёт размера групп под минимальный детектируемый эффект — в
<a href="trainer_sample.html">тренажёре «Расчёт выборки»</a>; из его результата
и складывается фаза 1. Все параметры пресетов учебные.</p>
</div></section>

<section><div class="wrap">
<h2>Источник</h2>
<div class="card">
<h4>Netflix Technology Blog</h4>
<p>Практика, из которой выросла механика тренажёра: каждая функция сервиса
запускается как эксперимент, а срок теста определяется числом участников
и горизонтом метрики, а не желаемой датой отчёта.</p>
<p style="margin:0">
<a href="https://netflixtechblog.com/interpreting-a-b-test-results-false-negatives-and-power-6943995cf3a8"
   target="_blank" rel="noopener">Interpreting A/B test results: false negatives and power</a>
— почему малому эффекту нужно больше участников и почему тест не завершают
раньше запланированного объёма.<br>
<a href="https://netflixtechblog.com/its-all-a-bout-testing-the-netflix-experimentation-platform-4e1ca458c15"
   target="_blank" rel="noopener">It’s All A/Bout Testing: The Netflix Experimentation Platform</a>
— как устроена платформа экспериментов Netflix.</p>
</div>
</div></section>

<footer><div class="wrap">
  Аналитика 360 · практическая часть, Шаги 1–4 · Карпов Курсы для Сбера.<br>
  Параметры метрик учебные; расчёт выполняется в вашем браузере, наружу ничего
  не отправляется.
</div></footer>

<script>
var MS=__METRICS__;
var cur=MS[0];
var flows={};                      // выбранный приток запоминается на метрику
var $=function(id){return document.getElementById(id)};
var NB="\\u202F";
function fi(x){return String(Math.round(x)).replace(/\\B(?=(\\d{3})+(?!\\d))/g,NB)}

function tx(x,y,t,fs,w,f,a,o){
  return '<text x="'+x+'" y="'+y+'" font-size="'+fs+'"'+(w?' font-weight="'+w+'"':'')
    +' fill="'+f+'"'+(a?' text-anchor="'+a+'"':'')+(o?' fill-opacity="'+o+'"':'')+'>'+t+'</text>';
}

function tickStep(total){
  var c=[1,2,5,7,14,30,60,90,180];
  for(var i=0;i<c.length;i++){if(total/c[i]<=13)return c[i]}
  return 360;
}

// SVG-таймлайн двух фаз: зелёная плашка — набор участников, светлая — горизонт
// метрики. Шкала — дни с начала эксперимента; масштаб подстраивается под итог.
function timeline(p1,p2){
  var total=p1+p2,X0=40,X1=896,BY=32,BH=46,AX=116,H=170;
  var sc=(X1-X0)/total,xb=X0+p1*sc;
  var s='<svg viewBox="0 0 920 '+H+'" xmlns="http://www.w3.org/2000/svg" role="img" '
    +'aria-label="Таймлайн эксперимента: фаза набора участников и горизонт метрики" '
    +'style="font-family:var(--font)">';
  s+='<rect x="'+X0+'" y="'+BY+'" width="'+(X1-X0)+'" height="'+BH+'" rx="10" fill="#159A5C" fill-opacity="0.16"/>';
  s+='<rect x="'+X0+'" y="'+BY+'" width="'+Math.max(6,xb-X0).toFixed(1)+'" height="'+BH+'" rx="10" fill="#20BA72"/>';
  s+='<line x1="'+xb.toFixed(1)+'" y1="10" x2="'+xb.toFixed(1)+'" y2="'+AX+'" stroke="#159A5C" stroke-width="1.6" stroke-dasharray="6 5"/>';
  s+='<line x1="'+X1+'" y1="10" x2="'+X1+'" y2="'+AX+'" stroke="#2E3641" stroke-opacity="0.35" stroke-width="1.4" stroke-dasharray="4 5"/>';
  s+=tx(X0,20,'фаза 1 · набор участников — '+fi(p1)+' дн',13.5,'700','#2E3641');
  s+=tx(X1,20,'итог ≈ '+fi(total)+' дн',14,'800','#2E3641','end');
  if(xb-X0>=70)s+=tx(((X0+xb)/2).toFixed(1),BY+BH/2+5,fi(p1)+' дн',14,'700','#ffffff','middle');
  if(X1-xb>=70)s+=tx(((xb+X1)/2).toFixed(1),BY+BH/2+5,fi(p2)+' дн',14,'700','#159A5C','middle');
  var c2=Math.min(Math.max((xb+X1)/2,X0+195),X1-175);
  s+=tx(c2.toFixed(1),BY+BH+22,'фаза 2 · горизонт метрики — '+fi(p2)+' дн',13.5,'700','#159A5C','middle');
  s+='<line x1="'+X0+'" y1="'+AX+'" x2="'+X1+'" y2="'+AX+'" stroke="#2E3641" stroke-opacity="0.3" stroke-width="1.2"/>';
  var st=tickStep(total);
  for(var d=0;d<=total;d+=st){
    var x=X0+d*sc;
    s+='<line x1="'+x.toFixed(1)+'" y1="'+AX+'" x2="'+x.toFixed(1)+'" y2="'+(AX+6)+'" stroke="#2E3641" stroke-opacity="0.3" stroke-width="1.2"/>';
    if(x<X1-26)s+=tx(x.toFixed(1),AX+24,d,12.5,null,'#2E3641','middle',0.6);
  }
  s+=tx(X1,AX+24,fi(total),12.5,'700','#2E3641','middle');
  s+=tx(X1,AX+46,'дни с начала эксперимента →',12.5,null,'#2E3641','end',0.6);
  return s+'</svg>';
}

function renderTabs(){
  $('expTabs').innerHTML=MS.map(function(m){
    return '<button type="button" class="exp-tab'+(m.id===cur.id?' on':'')
      +'" data-m="'+m.id+'">'+m.tab+'</button>';
  }).join('');
}

function select(id){
  cur=MS.filter(function(m){return m.id===id})[0]||MS[0];
  var f=$('flow');
  f.min=cur.fmin;f.max=cur.fmax;f.step=cur.fstep;
  f.value=flows[cur.id]||cur.fdef;
  renderTabs();update();
}

function update(){
  var flow=+$('flow').value;flows[cur.id]=flow;
  var p1=Math.max(1,Math.ceil(cur.n/flow)),p2=cur.horizon,total=p1+p2;
  $('flowLab').textContent=cur.flowLabel;
  $('flowVal').textContent=fi(flow);
  $('mName').textContent=cur.name;
  $('mNote').innerHTML=cur.note+' Подробнее: <a href="'+cur.linkHref+'">'+cur.linkText+'</a>.';
  $('sN').textContent=fi(cur.n);
  $('sNu').textContent='целевой объём, '+cur.unitN;
  $('sP1').textContent=fi(p1)+' дн';
  $('sP2').textContent=fi(p2)+' дн';
  $('sTot').textContent='≈ '+fi(total)+' дн';
  $('tl').innerHTML=timeline(p1,p2);
  $('fml').textContent=cur.formula;
  $('fmlU').textContent=cur.unitN+' (Z = 1,96 — доверие 95\\u202F%)';
  $('fml2').textContent='Фаза 1 = n / приток = '+fi(cur.n)+' / '+fi(flow)+' ≈ '
    +fi(p1)+' дн · фаза 2 = горизонт метрики = '+fi(p2)+' дн · итог ≈ '+fi(total)+' дн.';
  var share=Math.round(100*p2/total);
  $('concl').textContent=(p1<=2
    ? 'Набор уже не узкое место: срок почти целиком — горизонт метрики ('+fi(p2)
      +' дн из '+fi(total)+', '+share+'\\u202F%). Дальше двигать бегунок бесполезно.'
    : 'Фаза 2 — '+fi(p2)+' дн из '+fi(total)+' ('+share+'\\u202F% срока): её не сжимает '
      +'никакой приток — горизонт метрики можно только прожить.');
}

document.addEventListener('click',function(e){
  var b=e.target.closest('.exp-tab');
  if(b)select(b.getAttribute('data-m'));
});
$('flow').addEventListener('input',update);
select(cur.id);
</script>
"""


def body():
    return _BODY_TMPL.replace("__METRICS__", json.dumps(METRICS, ensure_ascii=False))


BODY = body()
