# GitHub Pages 演示

本次新增独立静态演示 `pages/`，不替换完整本地工作台，也不更新旧 Sites 网站。演示不是完整工作台的全部功能；未接入任何云端模型。

## 已包含

- NVIDIA、AMD、Intel、Adobe 四个公开历史案例，资料截止 2025-03-01。源披露摘录待人工审核，不是实时金融数据。
- 财务看板、来源查看、报表勾稽、三个半导体企业的描述性比较；Adobe 暂无同业样例。
- 硬件量价模型、软件留存和收入确认模型；确定性浏览器计算，明确标记假设。
- 六种会话内配色，完整版代码 ZIP 下载及启动文档入口。

新建任意公司、导入资料、保存研究、审核与修改历史请使用本地版。静态演示不模拟保存成功，不读取用户 SQLite，不上传笔记、审计记录或 API 密钥。浏览器只请求本站 HTML、CSS、JS 与公开样例 JSON；点击原始证据链接时才访问来源网站。

## 生成与测试

在项目根目录运行 `python -B scripts/build_pages.py`，从全新临时数据库导出白名单字段。临时目录位于项目 `.runtime/pages-build`；不读取 `.runtime/workbench`。

`node scripts/qa-pages.cjs` 在 `/Research-Atlas/` 子路径测试。脚本当前使用本机既有 Python、Node、Chrome 和 Playwright 路径；换电脑需调整路径。所有浏览器资料和缓存位于 D 盘项目 `.runtime/pages-qa`。

2026-09-22 实测：四公司默认情景共 280 个数值与 Python Decimal 模型比对，绝对误差不超过 0.0051（USD million）；覆盖公司切换、来源抽屉、假设调整、配色切换及 1280/390 宽度四视图。无页面脚本错误，无站外请求。该测试不构成所有参数组合的财务正确性证明，也不是源数据准确率。

## 发布

将 `pages/` 内的文件作为 `gh-pages` 分支根目录，包含 `.nojekyll`。仓库 Settings → Pages → Source 选择 Deploy from a branch → `gh-pages` → `/(root)` → Save。

预期网址：https://starer1333.github.io/Research-Atlas/ 。只有开启 Pages 且 GitHub 构建成功后才能访问，不以代码上传成功代替部署成功。

官方设置说明：https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

## 原创与限制

静态导出与 UI 由 AI 实现，经营公式改写自本项目 Python 确定性模型，未直接复制 FinRobot 的模型代码。用户尚未逐项人工审核。公开样例、公式、来源可检查；不得将这些测试表述为投资预测表现或企业内部分析经历。
