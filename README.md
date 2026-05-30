# 🤖 AI PR Review 助手

> 为 Vibe Coder 设计的 GitHub Pull Request 智能代码审查工具

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)](https://fastapi.tiangolo.com/)
[![Claude](https://img.shields.io/badge/AI-Claude%20Sonnet%204.6-purple)](https://anthropic.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📖 项目简介

本项目是「七牛云 × XEngineer 暑期实训营」竞赛作品，针对题目三「AI PR Review 助手」开发。

**核心洞察：** Vibe Coder（依赖 Cursor / Copilot / Claude 等 AI 工具编程的开发者）面临的问题不是没有 Review 工具，而是现有工具只告诉你「哪里有问题」，却不告诉你「**为什么是问题 + AI 生成代码的惯性陷阱 + 怎么一键修复**」。

**本工具做到了：**

- 📋 **变更摘要**：自动理解 PR 改了什么，核心逻辑一句话说清楚
- 🛡️ **风险识别**：HIGH / MEDIUM / LOW 三级分类，每条风险附带教育性解释
- ⚡ **一键修复**：在 GitHub PR 页面直接采纳 AI 建议的 `suggestion` 代码块，无需手动复制
- 🎓 **AI 陷阱标注**：专门识别 AI 生成代码的高频惯性错误（如 `shell=True`、f-string 拼 SQL、`eval()`、明文密码等）
- 📊 **准确率追踪**：内置反馈收集系统，量化「有帮助」率，持续调优

---

## 🖥️ 界面预览

Web 界面采用 TypeGallery 设计系统：奶油底色、衬线标题（EB Garamond）、零圆角，印刷排版质感。

| 功能 | 说明 |
|------|------|
| 输入 PR 链接 | 粘贴任意 GitHub PR 地址，回车或点击按钮触发 |
| 三步加载动画 | 获取数据 → Layer 1 摘要 → Layer 2 深度扫描 |
| 判断横幅 | ✅ 建议合并 / 🚫 请修复后合并 / 💬 供参考，含评分条 |
| 风险卡片 | 点击展开，HIGH 默认展开，含代码高亮修复建议 |
| 准确率统计 | 访问 `/stats` 查看内部看板 |

---

## 🏗️ 系统架构

```
用户输入 PR URL
      │
      ▼
┌─────────────────┐
│   Web Frontend  │  TypeGallery 风格单页应用
│  (index.html)   │
└────────┬────────┘
         │ POST /analyze
         ▼
┌─────────────────┐
│   FastAPI       │  api.py — 后端服务
│   后端服务      │
└────────┬────────┘
    ┌────┴────┐
    ▼         ▼
GitHub API   AI 分析引擎 (analyzer.py)
Client       │
(github_     ├── Layer 1: claude-haiku-4-5  (~3s)
 client.py)  │   变更摘要 + 文件重要性排序
             │
             └── Layer 2: claude-sonnet-4-6 (~15s)
                 风险识别 + 教育性解释 + Suggestion 生成
                      │
                      ▼
               结构化 JSON → formatter.py
               GitHub Markdown 评论 + Web 展示
                      │
               ┌──────┴──────┐
               ▼             ▼
         前端动态渲染    GitHub PR 评论发布

                      ▼
               反馈收集 (SQLite)
               GET /feedback?vote=up/down
               GET /stats 准确率看板
```

---

## 🤖 模型选择策略

### 为什么选 Claude？

| 维度 | 说明 |
|------|------|
| **代码语义理解** | Claude Sonnet 在识别安全模式、理解代码上下文方面表现优秀 |
| **指令遵从性** | 严格遵守「只报告有证据的问题」的约束，误报率低 |
| **结构化输出** | JSON 格式稳定，解析失败率极低 |
| **中文教育性解释** | 口语化中文输出质量高，适合 Vibe Coder 受众 |

### 双层模型架构

| 层 | 模型 | 任务 | 延迟 | 成本 |
|----|------|------|------|------|
| Layer 1 | `claude-haiku-4-5-20251001` | 变更摘要、文件重要性排序 | ~3s | ~$0.003 |
| Layer 2 | `claude-sonnet-4-6` | 风险识别、教育性解释、Suggestion 生成 | ~15s | ~$0.015 |

**总成本：$0.02–0.05 / 次 PR 分析**

---

## 📡 上下文获取策略

**上下文优先级（高 → 低）：**

1. **PR Description**：开发者意图，最关键的信号
2. **核心变更文件 diff**：实际代码变更（patch/hunk）
3. **原始文件内容**：理解变更前的状态，通过 GitHub Contents API 获取
4. **PR 标题 + Labels**：补充意图分类
5. **现有 Review 评论**：避免重复已有建议

**PR 规模守卫：**
- 超过 **2000 行 diff** 或 **100 个文件** → 拒绝分析，返回拆分建议
- 单文件超过 **50k tokens** → 截断并标注「已做部分分析」

---

## 🎯 误报与漏报控制

| 机制 | 实现方式 |
|------|---------|
| **证据锁定** | System Prompt 强制要求「只报告有具体代码证据的问题，不做推测性建议」 |
| **位置锁定** | 每条风险必须包含文件名 + 行号，无法定位则不输出 |
| **噪音过滤** | LOW 以下的风格建议不报告，避免打扰开发者心流 |
| **反馈回路** | 👎「不准确」标记触发 Prompt 持续调优 |
| **Vibe Coding 专项** | 针对 AI 代码高频陷阱（SQL拼接、shell=True、eval、硬编码密钥等）显式列举 |

### 实测准确性（基于 5 个测试 PR，20 个预埋漏洞）

| 指标 | 结果 |
|------|------|
| 预埋漏洞检测率 | **20/20 = 100%** |
| 误报数 | **0 个** |
| 额外发现有效问题 | **1 个**（超预期发现） |
| 干净代码评分 | **8/10 ✅** |
| 漏洞代码评分 | **2–4/10 🚫** |

详见 [`test-report.md`](test-report.md)

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/vigariokoestner958-droid/ai-pr-review-assistant.git
cd ai-pr-review-assistant
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`：

```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx   # Anthropic API Key
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxx            # GitHub Personal Access Token（需要 repo 权限）
```

> **获取 GitHub Token：** GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → 勾选 `repo`

### 4. 启动 Web 服务

```bash
python -m uvicorn api:app --reload --port 8000
```

打开浏览器访问：**http://localhost:8000**

### 5. 或使用 CLI 模式

```bash
# 仅本地分析（dry-run）
python -X utf8 main.py https://github.com/owner/repo/pull/123

# 分析并发布评论到 GitHub PR
python -X utf8 main.py https://github.com/owner/repo/pull/123 --post
```

---

## 📁 项目结构

```
ai-pr-review-assistant/
├── main.py              # CLI 入口：python main.py <PR_URL> [--post]
├── api.py               # FastAPI 后端：POST /analyze, GET /feedback, GET /stats
├── analyzer.py          # Claude 双层分析引擎（核心）
├── github_client.py     # GitHub API 封装（获取 PR 数据、发布评论）
├── formatter.py         # 结构化结果 → GitHub Markdown / CLI 输出
├── frontend/
│   └── index.html       # Web 单页应用（TypeGallery 风格）
├── SYSTEM_DESIGN.md     # 系统设计说明（模型选择/上下文获取/扩展方向）
├── test-report.md       # 5个测试 PR 的完整分析报告
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔌 API 文档

### `POST /analyze`

分析指定 GitHub PR。

**请求体：**
```json
{
  "pr_url": "https://github.com/owner/repo/pull/123",
  "post_comment": false
}
```

**响应字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `pr_title` | string | PR 标题 |
| `verdict` | string | `APPROVE` / `REQUEST_CHANGES` / `COMMENT` |
| `overall_score` | int | 质量评分 1–10 |
| `risks` | array | 风险列表，每项含 severity / file / line / title / why_it_matters / suggestion_code |
| `quick_wins` | array | 可立即改进的建议列表 |
| `github_comment` | string | 完整的 GitHub Markdown 评论内容 |
| `comment_url` | string \| null | 发布后的评论链接（post_comment=true 时） |

### `GET /feedback`

收集用户反馈，用于准确率追踪。

```
GET /feedback?pr=https://github.com/...&vote=up
GET /feedback?pr=https://github.com/...&vote=down
```

### `GET /stats`

内部准确率统计看板，展示有帮助率和最近反馈记录。

### `GET /health`

服务健康检查：`{"status": "ok"}`

---

## 🧪 测试用 PR

以下是用于验证系统效果的测试仓库，包含 5 个预设场景：

| PR | 场景 | 预期评分 | 预期判断 |
|----|------|---------|---------|
| [#1](https://github.com/vigariokoestner958-droid/pr-review-test/pull/1) | 命令注入 + CORS + 弱密码 | ~3/10 | 🚫 拒绝合并 |
| [#2](https://github.com/vigariokoestner958-droid/pr-review-test/pull/2) | XSS + eval + 原型污染 | ~3/10 | 🚫 拒绝合并 |
| [#3](https://github.com/vigariokoestner958-droid/pr-review-test/pull/3) | SQL注入 + 明文密码 + 无权限校验 | ~2/10 | 🚫 拒绝合并 |
| [#4](https://github.com/vigariokoestner958-droid/pr-review-test/pull/4) | N+1查询 + 内存泄露 + 同步阻塞 | ~2/10 | 🚫 拒绝合并 |
| [#5](https://github.com/vigariokoestner958-droid/pr-review-test/pull/5) | 干净代码（对照组）| ~8/10 | ✅ 建议合并 |

---

## 🗺️ 未来扩展方向

### v1.1（1–3 个月）
- **GitHub App Webhook**：PR 提交时自动触发，无需手动输入 URL
- **`@bot re-review` 命令**：修复问题后评论触发重新分析
- **准确率调优循环**：基于反馈数据持续优化 Prompt，目标有帮助率 > 70%

### v2.0（3–6 个月）
- **仓库级上下文理解**：索引整个仓库，识别跨文件依赖问题
- **团队规范学习**：上传 `.coding-standards.md`，基于团队规范 Review
- **VS Code 插件**：提 PR 前本地运行，零摩擦防翻车

### v3.0（6–12 个月）
- **Vibe Coding 成长报告**：分析开发者跨 PR 的代码模式，生成个人能力提升路线
- **CI/CD 集成**：准确率达标后，作为 GitHub Actions 可选阻塞步骤
- **Enterprise**：私有化部署、合规审计、SAML SSO

详见 [`SYSTEM_DESIGN.md`](SYSTEM_DESIGN.md) 和 [`roadmap.md`](roadmap.md)

---

## 🛠️ 技术栈

| 层级 | 技术 | 选择理由 |
|------|------|---------|
| AI 分析 | Anthropic Claude (Haiku + Sonnet) | 代码理解深度强，指令遵从性好 |
| 后端 | Python + FastAPI | 异步支持，启动快，自动文档 |
| GitHub 集成 | GitHub REST API v3 | 官方支持，Rate Limit 充足 |
| 数据持久化 | SQLite（反馈数据）| MVP 阶段零运维成本 |
| 前端 | 原生 HTML/CSS/JS | 无框架，单文件，易部署 |
| 代码高亮 | highlight.js | 轻量，支持多语言 |
| 字体 | EB Garamond + Manrope + JetBrains Mono | TypeGallery 设计系统 |

---

## 📄 系统设计说明

竞赛题目要求说明「模型选择、上下文获取方式及未来扩展方向的设计思路」，详见：

👉 **[SYSTEM_DESIGN.md](SYSTEM_DESIGN.md)**

---

## 📊 测试报告

5 个场景、20 个预埋漏洞的完整验证报告，含每条风险的检测情况和评分合理性分析：

👉 **[test-report.md](test-report.md)**

---

## 📜 知识产权声明

本项目为独立开发，严格遵守七牛云实训营相关规定。代码、文档、设计均为原创。

---

*由 THC 开发 · 七牛云 × XEngineer 暑期实训营 2026*
