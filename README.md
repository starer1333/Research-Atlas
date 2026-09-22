# Research Atlas V3｜Guided Company Research Workbench

**Current development branch:** `feature/research-workbench-v3`  
**V3 UI preview:** https://starer1333.github.io/Research-Atlas/v3/  
**V3-6 Business UI preview:** https://starer1333.github.io/Research-Atlas/v3/?view=business  
**Draft PR:** https://github.com/starer1333/Research-Atlas/pull/1

Research Atlas V3 is a financial-first guided company research workbench. The user-facing flow stays small — **Research / Evidence / Analysis / Report** — while the backend keeps explicit financial semantics, provenance, comparability and revision logic.

## V3 status

### Implemented now

- Four-page V3 information architecture and 60-second Company View.
- Deterministic Financial Diagnostics and guided research questions.
- Evidence Drawer with period / basis / scope / disclosure / review state.
- Comparative Reasoning gate before peer metrics.
- Question-first Scenario entry and Research Memory.
- **V3 Semantic Contract** in `atlas/semantic.py`:
  `Company → Metric → Observation → Document → Segment → Product → Driver → ResearchQuestion → Claim → Revision`.
- Validated semantic projection exposed in every V3 state response.
- **SourceAdapter contract** in `atlas/sources/`.
- **Direct official SEC EDGAR adapter** for company resolution, filing discovery and XBRL Company Facts.
- **Automatic Starter Research Pack** for a new U.S. ticker when SEC access is explicitly enabled.
- **V3-6 filing-text semantics**: deterministic 10-K Item 1 Business extraction plus explicit Segment / Product / Platform / Service candidates, all source-linked and `pending_review`.
- The public GitHub Pages V3-6 preview shows the Business/Segment/Product interaction and Semantic Contract layout. Because GitHub Pages is static, live SEC requests only run in the local V3 backend with `--enable-sec`.
- Existing V2 deterministic backend and SQLite research history remain available; the previous V2 UI is still at `/v2`.

### Not implemented yet

- Full semantic extraction of Customer / Competitor / pricing / strategy and note-level segment disclosures. V3-6 currently handles Item 1 Business plus explicit Segment/Product list candidates only.
- Docling/PDF intake pipeline.
- External LLM/RAG.
- Complete Semiconductor / SaaS / Consumer / Automotive / Bank driver modules.
- ECharts production visualization layer.
- Multi-user/cloud authentication.

## Runtime path

```
Ticker
↓
SourceAdapter
↓
SEC EDGAR (official endpoints)
↓
10-K Item 1 Business parser
↓
Automatic Starter Research Pack
↓
V3 Semantic Contract
↓
Deterministic diagnostics
↓
60-second Company View
↓
Question → Evidence → Compare → Scenario → Claim → Revision
```

## Local start

Default mode remains local-only:

```powershell
python -B serve_atlas.py
```

To allow a user to type a **new U.S. ticker** and build a Starter Research Pack from SEC EDGAR:

```powershell
$env:ATLAS_SEC_USER_AGENT="ResearchAtlas your-email@example.com"
python -B serve_atlas.py --enable-sec
```

SEC ingestion is opt-in, uses only fixed `sec.gov` endpoints, and imports observations as **pending review**. See [V3 SourceAdapter](docs/v3-source-adapters.md), [V3 Semantic Contract](docs/v3-semantic-contract.md), [V3 product contract](docs/v3-product-contract.md), and [security boundary](docs/security.md).

---

# Research Atlas｜公司与产业研究工作台

面向有财务基础的初级研究者。把证据、经营假设、计算与研究修订连接起来。

**浏览器演示：** 静态版本位于 `pages/`，支持四家公司、财务表格、来源、勾稽、竞品比较与经营情景。[演示范围与 GitHub Pages 发布说明](docs/github-pages.md)。[下载完整本地版](https://github.com/starer1333/Research-Atlas/archive/refs/heads/feature/research-workbench-v3.zip)。网页版不包含资料导入与持久保存；请使用下方本地启动说明体验完整流程。

**实施原则：借鉴核心思路与选择性复用代码，开发自己的需求 demo；不以完整复现 FinRobot 为前置条件。** 对拟复用模块做针对性验证，保留来源、许可证及改动记录。

## V2.2 本地研究工作台 / 当前开发版

新增：研究任务台、硬件量价与订阅留存两类经营驱动模型、不可覆盖的模型与判断修订、逐指标竞品可比性、候选提取与人工审核。预置 NVIDIA、AMD、Intel、Adobe 历史案例。勾稽结果区分独立披露值一致与衍生数据计算自洽，审核状态单独保存。

[V2.2 交付范围、测试与案例复现](docs/v22-release.md)。新增模型是经营假设实验，不是完整三表预测；提取支持本地规则及外部候选 JSON 导入，尚未调用外部模型 API。

十二个研究工作区：研究任务台、研究看板、财务数据表、勾稽与质量、竞品对比、市场与论点、经营驱动模型、预测实验室、提取与审核、证据与审核、预测检验、研究备忘录；另有配色实验室。

预置 NVIDIA / AMD / Adobe 的历史公开披露，支持新建任意公司档案、从 Excel 粘贴指标、预览勾稽后导入。按公司币种、会计准则、合并范围和财政期间检查可比性。支持共同比表、损益与现金勾稽、五年经营与现金流预测、三情景、DCF 敏感性、来源审核、模型快照、预测检验与备忘录版本。数据和记录保存至本地 SQLite。

**无 API 密钥、无运行依赖安装。需要 Python 3.10+。** Windows 本机已有 `D:\python\python.exe` 时，在项目目录运行：

```powershell
.\start-workbench.ps1
```

或直接运行 `D:\python\python.exe -B serve_atlas.py`。浏览器访问 **http://127.0.0.1:8766**。其他机器可用已有 Python 执行 `python -B serve_atlas.py`；请先将项目、临时目录放在允许的磁盘。当前用户约定仅写 D 盘。

本地版是浏览器网页，不需要桌面应用安装包。服务仅监听本机，页面与资料库随服务启动可用；不要将本地 HTTP 服务直接公开。记录位于 `.runtime/workbench/research.sqlite3`，退出再启动仍保留。备忘录需要点击保存；研究包直接写入 `.runtime/workbench/exports/`，不经过浏览器默认下载目录。

配色由用户决定：打开 http://127.0.0.1:8766/#palette ，可预览六套色卡，点击“保存我的选择”才持久保存。此前油绿配色仅保留为未选择时的默认状态；不代表用户认可。

[V2.1 多公司、勾稽、可比性与实测记录](docs/v21-multicompany-and-validation.md) · [V2 初始逻辑与验证记录](docs/v2-logic-and-validation.md) · [安全边界](docs/security.md)

**诚实边界：** 任意公司支持建档与手动导入，并非自动获取任意公司的完整资料。当前未连接外部 AI；没有 PDF 自动抽取、完整三表预测或全市场数据库。金融机构禁用一般企业 FCFF；其他新增行业目前使用基础财务口径，专属经营模型尚未完成。历史资料由 AI 辅助录入，初始待用户审核。历史预测训练不代表前瞻成绩；默认参数是练习假设。

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

`python -B tests/test_research.py`：新增 18 项测试，覆盖经营传导、版本修订、衍生核验、指标可比性和提取审核。

`node scripts/qa-research.cjs`：研究任务、硬件与订阅模型、模型修订、竞争判断、候选审核导入与刷新保留。测试目录 `.runtime/research-qa`，不写入用户资料库。

`python -B scripts/build_research_case.py`：生成独立 AMD 历史练习及 Adobe 模型扩展验证，资料库与完整导出在 `.runtime/research-case/`。管理层指引复盘不代表用户独立预测；示例不写入日常资料库。

`python -B tests/test_workbench.py`：财务计算、日期约束、持久化、导入契约、预测检验、多公司、可比性与勾稽，28 项测试。

`node scripts/qa-workspace.cjs`：新建公司 → 粘贴 → 预览 → 导入 → 模型，以及竞品、配色保存；十个页面在 1280 / 390 宽度验证。独立数据与截图位于 D 盘 `.runtime/workspace-qa`。

`node scripts/qa-workbench.cjs`：V2 真实浏览器操作链与基础安全验证。开发机使用已有 Playwright/Chrome；可通过 `ATLAS_PLAYWRIGHT`、`ATLAS_CHROME`、`ATLAS_PYTHON` 覆盖路径。数据库、浏览器配置、缓存、下载、截图都位于 D 盘 `.runtime/workbench-qa`，不会污染用户资料库。

`python -B scripts/probe_upstream.py`：原始上游模块的合成边界样本，需已有 pandas/numpy 和固定源码；不连接 API。

`node --test tests/model.test.cjs`：行业计算、输入边界、期间与披露日期过滤。

`python -B scripts/audit_upstream.py`：核验固定版本示例中的年度标签冲突。源码需位于 upstream/FinRobot。

## 文件

- `serve_atlas.py`、`atlas/`：V2 本地 API、资料库、指标与确定性计算
- `workbench/`：研究工作区、表格看板与配色实验室
- `start-workbench.ps1`：D 盘启动脚本

- `index.html`、`style.css`、`app.js`：网页工作台
- `model.js`：确定性计算与日期约束
- `docs/`：问题定义、复现、设计、安全、评估、协作和面试材料
- `upstream/`：本地原始参考，已排除 Git 提交

所有项目写入限定 D 盘。不要运行上游自动安装脚本。后续安装必须指定 D 盘虚拟环境、下载缓存、临时目录及工具配置；不修改全局配置。
