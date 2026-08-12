// Проверка страницы тренажёра карты в headless-Chrome: открытая копия из
// scorm/content и зашифрованная копия из корня (после инцидента с коллизией
// имён за гейтом обе проверяются всегда), плюс совместимость со старым
// черновиком в localStorage — структура эталонов менялась.
//
//   NODE_PATH=<путь к node_modules с puppeteer-core> node build/check_map_page.cjs
// Пароль гейта берётся из файла, путь к нему — в A360_PW_FILE; корень репозитория
// можно переопределить через A360_ROOT.
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const R = process.env.A360_ROOT || '/root/work/sessions/max--76387277381017/a360/';
const pw = fs.readFileSync(process.env.A360_PW_FILE, 'utf8').trim();

// Черновик старой структуры: 4 метрики, «Средний остаток», старый ключ пресета,
// плюс лишнее поле cl и меньшее число колонок в строке источника.
const OLD_DRAFT = JSON.stringify({
  q: 'Старый вопрос из прошлого черновика',
  metrics: [['Средний остаток на счетах', 'запаздывающая', '₽ млн', 'ежемесячно']],
  sources: [['АБС', 'счета, обороты']],
  quality: [['определения', 'старое расхождение']],
  master: { ind: 'Доля активных счетов', a: 'АБС', av: '71 %', b: 'Витрина', bv: '63 %', choice: 'Витрина', proto: 'старый протокол' },
  actions: [['Сверить определение активного счёта', 'методолог', 'две недели']],
  cl: [0, 2]
});

async function open(b, file, gated, seed) {
  const p = await b.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push('pageerror: ' + String(e).slice(0, 160)));
  p.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text().slice(0, 160)); });
  await p.goto('file://' + R + file, { waitUntil: 'networkidle0' });
  await p.evaluate(() => localStorage.clear());
  if (seed) await p.evaluate(s => { localStorage.setItem('a360_dmz_own', s.d); localStorage.setItem('a360_dmz_preset', s.k); }, seed);
  await p.goto('file://' + R + file, { waitUntil: 'networkidle0' });
  if (gated) {
    await p.type('#pw', pw);
    await p.click('#go');
    await new Promise(r => setTimeout(r, 1600));
  }
  return { p, errs };
}

(async () => {
  const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  let bad = 0;
  const say = (ok, t, x) => { if (!ok) bad++; console.log((ok ? 'ок      ' : 'СЛОМАНО ') + t + (x ? '  ' + x : '')); };

  for (const [file, gated] of [['scorm/content/trainer_map.html', false], ['trainer_map.html', true]]) {
    const label = gated ? 'за паролем' : 'открытая  ';
    const { p, errs } = await open(b, file, gated);

    const base = await p.evaluate(() => ({
      gate: !!document.getElementById('pw'),
      presets: document.querySelectorAll('#epSel option[value]:not([value=""])').length,
      groups: document.querySelectorAll('#epSel optgroup').length,
      prompt: (document.getElementById('dmzPview') || {}).textContent || ''
    }));
    say(!base.gate, label + ' · страница открылась');
    say(base.presets === 18, label + ' · эталонов в списке: ' + base.presets);
    say(base.groups === 4, label + ' · групп в списке: ' + base.groups);
    say(/Границы разбора/.test(base.prompt) && /\[строки таблицы метрик\]/.test(base.prompt),
      label + ' · промпт-шаблон собран');

    // выбор эталона заполняет форму
    const filled = await p.evaluate(async () => {
      const s = document.getElementById('epSel');
      s.value = 'rko';
      s.dispatchEvent(new Event('change', { bubbles: true }));
      await new Promise(r => setTimeout(r, 250));
      return {
        q: document.getElementById('fQ').value,
        metrics: document.querySelectorAll('[data-t="metrics"][data-j="0"]').length,
        sources: document.querySelectorAll('[data-t="sources"][data-j="0"]').length,
        actions: document.querySelectorAll('[data-t="actions"][data-j="0"]').length,
        badge: document.getElementById('epBadge').textContent,
        prompt: document.getElementById('dmzPview').textContent,
        state: document.getElementById('pState').textContent
      };
    });
    say(/юрлиц/.test(filled.q), label + ' · вопрос эталона подставлен');
    say(filled.metrics === 6 && filled.sources === 4 && filled.actions === 3,
      label + ' · строки формы: метрик ' + filled.metrics + ', источников ' + filled.sources + ', действий ' + filled.actions);
    say(filled.badge === 'Продукты', label + ' · бейдж группы: ' + filled.badge);
    say(/Доля счетов без оборота на 60-й день/.test(filled.prompt) && /Границы разбора/.test(filled.prompt),
      label + ' · промпт заполнен картой');
    say(/Все 6 блоков карты подставлены/.test(filled.state), label + ' · статус: ' + filled.state.slice(0, 60));

    // тумблер и копирование
    const copy = await p.evaluate(async () => {
      let copied = null;
      navigator.clipboard.writeText = t => { copied = t; return Promise.resolve(); };
      document.getElementById('swTpl').click();
      const tpl = document.getElementById('dmzPview').textContent;
      document.getElementById('bCopyMode').click();
      await new Promise(r => setTimeout(r, 200));
      const lbl = document.getElementById('bCopyMode').textContent;
      document.getElementById('swFill').click();
      return { tpl: tpl, copied: copied, lbl: lbl, fill: document.getElementById('dmzPview').textContent };
    });
    say(/\[строки таблицы источников\]/.test(copy.tpl), label + ' · тумблер «Шаблон»');
    say(copy.copied && copy.copied.length > 1500 && /Границы разбора/.test(copy.copied),
      label + ' · копирование промпта (' + (copy.copied || '').length + ' симв.)');
    say(copy.lbl === 'Скопировано', label + ' · кнопка подтвердила копирование');

    // экспорт в Markdown
    const exp = await p.evaluate(async () => {
      let md = null, name = null;
      navigator.clipboard.writeText = t => { md = t; return Promise.resolve(); };
      const oldCreate = URL.createObjectURL;
      URL.createObjectURL = b => { window.__blob = b; return 'blob:test'; };
      const oldClick = HTMLAnchorElement.prototype.click;
      HTMLAnchorElement.prototype.click = function () { name = this.download; };
      document.getElementById('bExport').click();
      await new Promise(r => setTimeout(r, 300));
      HTMLAnchorElement.prototype.click = oldClick;
      URL.createObjectURL = oldCreate;
      return { md: md, name: name, msg: document.getElementById('expMsg').textContent };
    });
    say(exp.name === 'A1_карта_источников.md', label + ' · имя файла экспорта: ' + exp.name);
    say(exp.md && /## 6. Действия/.test(exp.md) && /Отток клиентов РКО/.test(exp.md),
      label + ' · markdown экспорта (' + ((exp.md || '').length) + ' симв.)');

    say(errs.length === 0, label + ' · ошибок консоли: ' + errs.length, errs[0] || '');
    await p.close();
  }

  // старый черновик не должен ломать страницу
  {
    const { p, errs } = await open(b, 'scorm/content/trainer_map.html', false,
      { d: OLD_DRAFT, k: 'rko' });
    const st = await p.evaluate(() => ({
      q: document.getElementById('fQ').value,
      metrics: document.querySelectorAll('[data-t="metrics"][data-j="0"]').length,
      srcCells: document.querySelectorAll('[data-t="sources"]').length,
      sel: document.getElementById('epSel').value,
      prompt: (document.getElementById('dmzPview').textContent || '').length,
      checked: document.querySelectorAll('[data-cl]:checked').length
    }));
    say(/Старый вопрос/.test(st.q), 'старый черновик · вопрос сохранён');
    say(st.metrics === 1 && st.srcCells > 0, 'старый черновик · форма отрисована (метрик ' + st.metrics + ')');
    say(st.sel === 'rko', 'старый черновик · выбранный эталон помнится');
    say(st.prompt > 500, 'старый черновик · промпт собрался (' + st.prompt + ' симв.)');
    say(st.checked === 2, 'старый черновик · чек-лист восстановлен: ' + st.checked);
    say(errs.length === 0, 'старый черновик · ошибок консоли: ' + errs.length, errs[0] || '');

    // и замена старого черновика эталоном тоже не падает
    const after = await p.evaluate(async () => {
      window.confirm = () => true;
      const s = document.getElementById('epSel');
      s.value = 'churn';
      s.dispatchEvent(new Event('change', { bubbles: true }));
      await new Promise(r => setTimeout(r, 250));
      return { q: document.getElementById('fQ').value, m: document.querySelectorAll('[data-t="metrics"][data-j="0"]').length };
    });
    say(/90 дней/.test(after.q) && after.m === 5, 'старый черновик · заменяется эталоном (метрик ' + after.m + ')');
    say(errs.length === 0, 'старый черновик · ошибок после замены: ' + errs.length, errs[0] || '');
    await p.close();
  }

  console.log(bad ? ('ПРОВЕРОК ПРОВАЛЕНО: ' + bad) : 'все проверки тренажёра карты пройдены');
  await b.close();
  process.exit(bad ? 1 : 0);
})();
