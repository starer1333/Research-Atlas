(function (root) {
  'use strict';
  function scenario(kind, growth, margin) {
    if (!['hardware', 'software'].includes(kind)) throw new Error('未知行业模块');
    if (!Number.isFinite(growth) || growth < -50 || growth > 50) throw new Error('增长假设必须介于 -50% 与 50%');
    if (!Number.isFinite(margin) || margin < 0 || margin > 100) throw new Error('毛利率必须介于 0% 与 100%');
    // Monetary outputs in CNY million; retain full precision until display.
    const base = kind === 'hardware' ? 100000 * 2000 / 1000000 : 2000 * 12000 / 1000000;
    const revenue = base * (1 + growth / 100);
    return {base, revenue, grossProfit: revenue * margin / 100,
      formula: kind === 'hardware' ? '100,000 台 × (1 + 销量增长) × 2,000 元 / 1,000,000' : '2,000 个平均付费客户 × (1 + 客户增长) × 12,000 元年均收入 / 1,000,000'};
  }
  function available(evidence, asOf) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(asOf)) return false;
    return evidence.disclosedAt <= asOf && evidence.periodEnd <= asOf;
  }
  const api = {scenario, available};
  if (typeof module !== 'undefined') module.exports = api;
  else root.AtlasModel = api;
})(typeof window === 'undefined' ? globalThis : window);
