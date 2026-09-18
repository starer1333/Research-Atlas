# 指标与数据契约

## V2 已实现契约

公开历史案例由 `atlas/seed.py` 初始化 SQLite：company、metric、label、value、currency、unit、period、period_type、scope、basis、kind、source_id；来源表包含 disclosed_at、url、locator、excerpt、note、内容摘要哈希；审核状态与操作记录单独保存。

当前仅 NVIDIA 与 Adobe、USD million、合并年度数据，后续 NVIDIA 单季收入为更新案例。GAAP 与 Non-GAAP 使用明确指标区分；导入接口当前只接收 GAAP，避免同名调整值覆盖法定口径。财政年度标签不等于自然年，完整起止日期尚待补齐。

Disclosed：原始披露；Calculated：附计算公式，例如债务合计；Assumed：模型参数。预测模型的输出为 Assumed + Calculated，不能标作披露。现金流量表缺失不转成零；期末应收/存货天数只是余额代理指标，不冒充平均余额周转。

模型快照保存输入值、来源元数据、研究时点、全部参数、五年计算行、情景、敏感性和模型版本。原始记录保留，更新不会覆盖历史快照。

## 以下为 V0.1 模拟案例与目标契约

生产数据目标结构：companyId、segmentId、industry、businessModel、metricId、value、currency、unit、periodStart、periodEnd、periodType、scope、disclosedAt、sourceId、sourceQuote、page、reviewStatus、kind。kind 限 Disclosed / Calculated / Assumed；模拟案例用独立 datasetMode=simulated 隔离，不能假冒 Disclosed。

当前是原型代码内的模拟 fixtures，并非已经实现上述完整契约的存储层。

| 指标 | 定义 | 单位 | 适用边界 |
| --- | --- | --- | --- |
| hardware.units | 年度销量 | 台 | 不等于终端售出量 |
| hardware.price | 每台平均确认收入 | CNY / 台 | 不等于官网标价 |
| software.avgCustomers | 年内平均付费客户 | 个 | 不等于期末客户数 |
| software.annualRevenuePerCustomer | 每平均客户年度确认收入 | CNY / 客户 | 不等于 ARR |
| revenue | 对应行业驱动因素相乘 | CNY 百万元 | 模拟全年合并收入 |
| grossProfit | 收入 × 毛利率 | CNY 百万元 | 不等于营业利润或现金流 |

情景范围是 UI 教学范围，并无真实分布证据。没有同行排名。真实接入须校验指标定义、报告期间、分部、合并范围和币种后再比较。

基期统一 FY2025，模拟可用日期 2026-03-01；日期前不显示数值或情景结果。日期门控采用 ISO 日期，完整日期合法性及财报修订版本管理仍待扩展。
