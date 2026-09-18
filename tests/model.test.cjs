const {test}=require('node:test');
const assert=require('node:assert/strict');
const {scenario,available}=require('../model.js');
test('硬件销量价格模型正确，保持计算精度',()=>{const r=scenario('hardware',10,35);assert.ok(Math.abs(r.revenue-220)<1e-10);assert.ok(Math.abs(r.grossProfit-77)<1e-10);});
test('订阅软件用平均客户而非硬件销量模型',()=>{const r=scenario('software',25,75);assert.equal(r.revenue,30);assert.equal(r.grossProfit,22.5);});
test('拒绝非有限数、未知模块和超范围假设',()=>{for(const g of [NaN,Infinity,-51,51])assert.throws(()=>scenario('hardware',g,35));assert.throws(()=>scenario('bank',10,35));assert.throws(()=>scenario('software',10,101));});
test('研究日期早于披露日期不可使用数据，包括已结束的期间',()=>{const e={disclosedAt:'2026-03-01',periodEnd:'2025-12-31'};assert.equal(available(e,'2026-02-28'),false);assert.equal(available(e,'2026-03-01'),true);assert.equal(available(e,''),false);});
