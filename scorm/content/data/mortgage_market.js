// Аналитика 360 · учебная выгрузка «mortgage_market»
// Подключается тегом <script src="mortgage_market.js"></script>; после этого строки
// доступны как window.DATA — массив объектов с полями: bank, was_bn_rub, now_bn_rub.
// Числа уже числа: parseFloat не нужен. Данные синтетические.
window.DATA = [
{"bank":"Мы","was_bn_rub":142.0,"now_bn_rub":168.0},
{"bank":"Банк А","was_bn_rub":11.5,"now_bn_rub":17.5},
{"bank":"Банк Б","was_bn_rub":6.8,"now_bn_rub":10.9},
{"bank":"Банк В","was_bn_rub":58.0,"now_bn_rub":63.2},
{"bank":"Прочие","was_bn_rub":61.0,"now_bn_rub":58.0}
];
window.DATA_NAME = "mortgage_market";
window.DATA_FIELDS = ["bank", "was_bn_rub", "now_bn_rub"];
