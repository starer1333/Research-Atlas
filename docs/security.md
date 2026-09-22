# 安全边界 / 非安全认证

## V3-9 / V3-10 visualization + optional AI (2026-09-22)

V3-9 loads a **version-pinned Apache ECharts 6.1.0** browser bundle from `cdn.jsdelivr.net`. The local server CSP allows scripts only from `self` and that CDN host; `connect-src` remains `self`, so the browser cannot use the chart layer to call arbitrary remote APIs. This adds a third-party CDN supply-chain dependency. If stricter offline operation is required, vendor the pinned ECharts bundle into `workbench/` and restore `script-src 'self'`.

V3-10 AI Research Planner is **off by default** and can only be enabled at server startup with `--enable-ai` plus `ATLAS_AI_BASE_URL`, `ATLAS_AI_API_KEY` and `ATLAS_AI_MODEL`. The API key stays server-side and is never returned by `/api/session`. The browser cannot submit or override the provider endpoint. Configuration rejects non-HTTPS endpoints and localhost/private literal IPs.

The planner receives a compact research snapshot (company context, deterministic findings, current questions, industry-driver prompts, source metadata and allowed evidence/source IDs). Raw documents are not sent by default. Model output is parsed as data, labelled `ai_suggested / not_verified`, and unknown evidence/source IDs are dropped. The planner has no direct path to create or modify verified observations, calculations or final claims; a suggested question is persisted only after an explicit user action.

This does **not** constitute prompt-injection resistance or model-provider security certification. Enabling a third-party AI provider means the compact snapshot is transmitted to that provider under its own privacy/security terms. Provider availability, retention policy and model behavior remain outside Research Atlas's trust boundary.

## V3 optional SEC SourceAdapter (2026-09-22)

V3 adds **opt-in** outbound access to official SEC EDGAR endpoints. It is disabled unless the local server is started with `--enable-sec` and a descriptive `ATLAS_SEC_USER_AGENT` / `--sec-user-agent`. The adapter is hard-limited to `www.sec.gov` and `data.sec.gov`; it does not fetch arbitrary user-supplied URLs. The browser still connects only to the local Research Atlas origin; outbound SEC requests originate from the local Python service.

A Starter Research Pack stores official filing metadata and selected XBRL Company Facts in the local SQLite workspace. Imported observations start as `pending_review`. Multiple candidate facts/restatements are not silently flattened into “truth”: the chosen fact keeps accession, filed date, source taxonomy tag, version count and selection policy.

This is a convenience ingestion layer, not a security or audit certification. SEC availability, rate limits and taxonomy differences can cause incomplete packs.


## V2 更新（2026-09-18）

以下旧章节仅描述 V0.1。V2 的资料摘录、指标、审核、模型/预测/备忘录版本和操作日志保存至项目 `.runtime/workbench/research.sqlite3`。没有浏览器 localStorage、索引数据库或云模型调用。没有读取密钥。导出由本地服务直接写入资料库同级 `exports` 目录，文件名由服务端生成，不接受外部路径；不经过浏览器默认下载目录。

本地服务绑定 127.0.0.1；静态文件采用明确白名单，不允许读取项目根目录、数据库或上游文件。写入同时校验 Host、Origin、随机会话 token、JSON 内容类型与 1MB 请求上限。数据库查询参数化。来源只存为数据，不执行文档、SQL 或生成代码，不主动抓取用户 URL。界面渲染用户文本时转义。V2 当时不允许外部脚本；当前 V3-9 的 CSP 仅额外放行版本固定的 jsDelivr ECharts 脚本，详见上方 V3-9 / V3-10 边界。

已实测：跨来源 POST 被拒绝；请求私有数据库路径返回 404；HTML 注入样本作为普通文本展示；日期截止在后端生效；公司间审核隔离与事务回滚。未做全面渗透测试，不宣称安全认证。没有实现用户身份认证，同机具有访问权限的程序仍属于信任边界。

资料删除：停止本地服务后删除该 SQLite 文件，会删除资料摘录、指标、笔记、版本与操作日志。导出文件、测试数据库及截图不包含在该动作中；没有自动删除功能。未保存的备忘录只在页面内存中。

运行 Python 使用 `-B`；项目临时目录、测试数据库、浏览器专用配置/缓存/崩溃目录都在 D 盘。没有安装软件或修改全局配置。浏览器测试只读取 C 盘既有程序，不使用日常浏览器配置。宿主软件或 Windows 自发日志不在项目可承诺的写入范围。

## V0.1 历史说明

当前页面不调用外部接口，不接收密钥，不持久化浏览器存储；手工笔记与修订只存在会话内存。刷新丢失，显式导出文件由用户选择位置，须选择 D 盘。

页面使用 textContent 展示输入，未执行生成代码。CSP 禁止 connect-src、表单提交及外部内容；还未在实际浏览器验证策略兼容性，不能仅凭策略声明安全。

不主动更改 C 盘文件或安装软件；运行已有 Node 可执行文件只读取其 C 盘位置。临时目录及 Python 缓存配置指向 D 盘，Python 禁止写字节码。未启动浏览器，避免其默认个人配置写入。Windows 或宿主应用的自主日志不属于项目能保证零写入的范围。

当前未实现资料导入、索引、模型服务、认证、代码执行及持久资料库。未来模型调用须先显示发送字段和目的；密钥仅后端；文档只作为数据，无工具权限；查询默认只读。需要提示注入、路径越界、密钥泄漏及删除完整性测试后，才能声称相关安全能力已验证。

删除范围：刷新清空当前笔记和历史，不删除已导出的 Markdown；删除项目也不删除用户另存的导出文件。未来资料、索引、日志需建立明确的关联删除机制。
