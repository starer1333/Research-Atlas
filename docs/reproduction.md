# 上游复现记录 / 2026-09-18

来源：https://github.com/AI4Finance-Foundation/FinRobot

固定 commit：`6d6ccd32c1b8b1904dc656cf06897438aba3daec`。浅克隆下载至 `upstream/FinRobot`，不纳入本项目 Git。

本次重新核验 README：V1 finrobot_equity 开源；V2 源码尚未开源。不能以主 README 中其他版本的介绍证明 V1 的能力。

模块文档：https://github.com/AI4Finance-Foundation/FinRobot/blob/6d6ccd32c1b8b1904dc656cf06897438aba3daec/finrobot_equity/README.md

根目录 LICENSE 为 Apache-2.0，NOTICE 原样保留在下载目录。目前没有复制上游代码到产品；后续若复用须保留适用许可证、NOTICE、版权及改动声明。Dexter、WrenAI、OpenBB 尚未下载或集成。

## 数据流检查

`generate_financial_analysis.py` → FMP 数据获取 → 财务指标与三年预测 → 同业比较 → 模型文本 → CSV / JSON / TXT。

`create_equity_report.py` → 加载前述输出 → 补充市场数据 → 图表 → HTML → 可选 PDF。文档中的报告重生成路径仍可能调用外部服务，不等于离线渲染。

依赖声明采用较宽版本区间，并非完整 lockfile。Python 运行环境实际为 3.12.9。现有环境检测：pandas、numpy、requests 可找到；agents、openai、matplotlib 不可找到。

## 原版执行尝试

输入：NVDA / NVIDIA Corporation；同业 AMD、INTC；启用文本生成；输出指定 D 盘项目 `.runtime/reproduction/NVDA`。

原版入口执行在导入阶段失败：`ModuleNotFoundError: No module named 'yfinance'`。具体堆栈、退出码、耗时见 `upstream-run.txt`。

没有财务结果或生成报告；没有 API 调用及费用。没有购买服务，没有读取其他项目密钥。FMP 与模型密钥尚未由用户为本项目提供。尚未安装完整依赖或完成真实研究路径。此失败不能用于评价模型准确率。

## 样例质量核对

固定源码内 `finrobot_equity/core/output/NVDA_Equity_Research_Report.html`：

- 第 253、262 行将 FY2026 215.9 billion 收入描述为 consensus estimates。
- 第 281 行同时显示 `Revenue (2026A)` 与 `$215.94B`。
- 因此确认**同一报告口径冲突**；不是确认哪一个数值与真实公告一致。
- 自动核对脚本：`python -B scripts/audit_upstream.py`。脚本只检查这个固定样本，不是通用报告准确率评估。
- 根因尚未定位。下一步需追踪预测数据字段、期间状态传递和摘要模板；不得直接归因于 LLM。

官方在线样例：https://ai4finance-foundation.github.io/FinRobot/finrobot_equity/core/output/NVDA_Equity_Research_Report.html

## 下一步复现

在 D 盘专用虚拟环境固定依赖，明确隔离缓存及配置目录；配置本项目获授权的 API 密钥后再运行完整路径。安装与执行前检查潜在 C 盘写入；绝不直接运行上游自动部署脚本。费用上限与外部发送字段需另行确认。
