# Research Atlas｜公司与产业研究工作台

面向有财务基础的初级研究者。把证据、经营假设、计算与研究修订连接起来。

**实施原则：借鉴核心思路与选择性复用代码，开发自己的需求 demo；不以完整复现 FinRobot 为前置条件。** 对拟复用模块做针对性验证，保留来源、许可证及改动记录。

## V2 本地研究工作台 / 当前开发版

七个工作区：研究总览、财务诊断、市场与论点、预测实验室、证据与审核、预测检验、研究备忘录。

使用 NVIDIA / Adobe 的历史公开披露验证硬件平台与软件两种业务结构。支持利润变化分解、五年经营与现金流预测、三情景、DCF 敏感性、参数影响排序、来源审核、模型快照、后续资料更新、预测事后检验与备忘录版本。数据和记录持久保存至本地 SQLite。

**无 API 密钥、无运行依赖安装。需要 Python 3.10+。** Windows 本机已有 `D:\python\python.exe` 时，在项目目录运行：

```powershell
.\start-workbench.ps1
```

或直接运行 `D:\python\python.exe -B serve_atlas.py`。浏览器访问 **http://127.0.0.1:8766**。其他机器可用已有 Python 执行 `python -B serve_atlas.py`；请先将项目、临时目录放在允许的磁盘。当前用户约定仅写 D 盘。

本地版是浏览器网页，不需要桌面应用安装包。服务仅监听本机，页面与资料库随服务启动可用；不要将本地 HTTP 服务直接公开。记录位于 `.runtime/workbench/research.sqlite3`，退出再启动仍保留。备忘录需要点击保存；研究包直接写入 `.runtime/workbench/exports/`，不经过浏览器默认下载目录。

新视觉从维米尔与霍普的明暗、暖冷组织汲取思路，采用深油绿、亚麻白和黄铜细节；不是画作图片拼贴。新版视觉尚待用户验收。

[完整逻辑、商业理念与验证记录](docs/v2-logic-and-validation.md) · [本轮设计契约](docs/v2-design-contract.md) · [安全边界](docs/security.md)

**诚实边界：** 当前未连接外部 AI；没有 PDF 自动抽取、完整三表或同行市场数据库。历史资料由 AI 辅助录入，全部初始标为待用户审核。历史预测训练不代表当时就做出的前瞻判断。默认预测参数是练习假设，结果不是目标价或投资建议。

## 在线演示 / 早期 V0.1

[打开 Research Atlas 演示工作台](https://research-atlas-starer1333.judy40202.chatgpt.site)

公开可访问，无需下载或 API 密钥。当前为虚构模拟原型，不是真实公司研究报告。

## 保留的 V0.1 网页与离线交互原型

直接打开 `index.html`，无需安装、密钥或联网。也可在本目录运行 `python -B -m http.server 8765 --bind 127.0.0.1`，浏览器访问 http://127.0.0.1:8765 。服务方式仅适用于本地开发，不要将项目根目录服务器暴露到公网（根目录含上游及开发文件）。

硬件销量价格模型、订阅软件客户模型是两种**虚构模拟案例**，不代表真实公司业绩。支持数字溯源、假设调整、提交修订、研究日期过滤、笔记和 Markdown 导出。会话数据只在内存，刷新即重置；导出用于显式保存。不使用浏览器持久存储，以避免主动向 C 盘浏览器配置目录写入。

## 交付路线

推荐以网页产品为主，GitHub 保存代码与证据记录。公开仓库 https://github.com/starer1333/Research-Atlas 的线上模拟演示已发布；V2 先在本地检验交互和资料库。多用户云服务需要单独设计认证、隔离和备份，不能把本机数据库直接放到静态托管站。

上游 FinRobot 已下载并固定版本；原版完整研究路径尚未复现成功，详见 `docs/reproduction.md`。此原型不是 FinRobot 运行结果，也没有复用其计算代码。

## 验证

`python -B tests/test_workbench.py`：V2 财务计算、日期约束、持久化、导入契约、预测检验，16 项测试。

`node scripts/qa-workbench.cjs`：V2 真实浏览器操作链与基础安全验证。开发机使用已有 Playwright/Chrome；可通过 `ATLAS_PLAYWRIGHT`、`ATLAS_CHROME`、`ATLAS_PYTHON` 覆盖路径。数据库、浏览器配置、缓存、下载、截图都位于 D 盘 `.runtime/workbench-qa`，不会污染用户资料库。

`python -B scripts/probe_upstream.py`：原始上游模块的合成边界样本，需已有 pandas/numpy 和固定源码；不连接 API。

`node --test tests/model.test.cjs`：行业计算、输入边界、期间与披露日期过滤。

`python -B scripts/audit_upstream.py`：核验固定版本示例中的年度标签冲突。源码需位于 upstream/FinRobot。

## 文件

- `serve_atlas.py`、`atlas/`：V2 本地 API、资料库、指标与确定性计算
- `workbench/`：V2 七工作区网页
- `start-workbench.ps1`：D 盘启动脚本

- `index.html`、`style.css`、`app.js`：网页工作台
- `model.js`：确定性计算与日期约束
- `docs/`：问题定义、复现、设计、安全、评估、协作和面试材料
- `upstream/`：本地原始参考，已排除 Git 提交

所有项目写入限定 D 盘。不要运行上游自动安装脚本。后续安装必须指定 D 盘虚拟环境、下载缓存、临时目录及工具配置；不修改全局配置。
