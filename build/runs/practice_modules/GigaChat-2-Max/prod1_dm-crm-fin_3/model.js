window.effectFlows = function (p) {
  var rows = [], cum = 0, cumDisc = 0;
  var m = Math.pow(1 + p.rate, 1/12) - 1;       // месячная ставка из годовой p.rate
  var full = p.delta * p.volume;                // delta × volume

  function rampShare(t) {
    return Math.min(t / p.ramp, 1);
  }

  for (var t = 0; t <= p.horizon; t++) {
    var units = 0, income = 0, cost = (t === 0) ? p.capex : p.opex;
    if (t >= 1) {
      for (var k = Math.max(1, t - p.keep + 1); k <= t; k++) {
        units += full * rampShare(k);
      }
      income = units * p.price;
    }
    var cf = income - cost;
    cum += cf;
    var disc = cf / Math.pow(1 + m, t);         // cf / (1 + m)^t
    cumDisc += disc;
    rows.push({ t: t, income: income, cost: cost, cf: cf, cum: cum, cum_disc: cumDisc });
  }
  return rows;
};