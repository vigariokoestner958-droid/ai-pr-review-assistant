# 工程化执行文档：AI PR Review 助手 MVP

> 基于 pr-review-prd-final.md · 技术原则：轻量 / 快速出效果 / 容易录制 Demo

---

## 模块一：Sprint Roadmap

### 阶段 0 — 环境准备（今天，30 分钟）
**目标：** 跑通最小闭环验证
- 申请 GitHub Personal Access Token（scopes: `repo`）
- 配置 `.env`（ANTHROPIC_API_KEY + GITHUB_TOKEN）
- 安装依赖：`pip install -r requirements.txt`
- 验证：`python main.py https://github.com/any/public-repo/pull/1`

---

### 🎯 实训营 Demo 冲刺版（Day 1-3）
**核心目标：** PR URL 输入 → AI 分析 → GitHub 自动评论，能录制视频

| User Story | 验收标准 | 交付物 |
|-----------|---------|--------|
| Story 1（自动触发）| 输入 PR URL，10分钟内发布评论 | `main.py` CLI + `api.py` |
| Story 2（变更摘要）| 评论顶部有结构化摘要 | `analyzer.py` Layer 1 |
| Story 3（风险分级）| HIGH/MEDIUM/LOW 标注 + 教育性解释 | `analyzer.py` Layer 2 |
| Story 4（Suggestion）| 评论含可采纳的代码建议块 | `formatter.py` |

**交付物清单：**
```
pr-review/
├── main.py          # CLI：python main.py <PR_URL>
├── api.py           # FastAPI：POST /analyze
├── github_client.py # GitHub API 封装
├── analyzer.py      # Claude 双层分析引擎
├── formatter.py     # GitHub Markdown 格式化
├── .env.example
└── requirements.txt
```

---

### Alpha（Day 4-5）
**目标：** Web UI 接入（Open Design 生成前端）
- Open Design 生成 `frontend/index.html`
- FastAPI 服务 serve 静态文件
- 前端调 `POST /analyze` 展示结果

---

### Beta（Week 2）
**目标：** Story 5（反馈）+ Story 6（重新触发）
- 👍/👎 反馈按钮
- `@bot re-review` 命令解析
- 大型 PR 守卫（>2000行拒绝）

---

## 模块二：核心架构与技术选型

### 交互链路（Demo 冲刺版）

```
用户输入 PR URL
      │
      ▼
main.py / POST /analyze
      │
      ▼
github_client.py
  ├── GET /repos/{owner}/{repo}/pulls/{number}     → PR 元数据
  ├── GET /repos/{owner}/{repo}/pulls/{number}/files → 变更文件+patch
  └── 构建分析上下文
      │
      ▼
analyzer.py
  ├── Layer 1：claude-haiku-4-5（~3s）
  │   └── Prompt: 生成摘要 + 文件重要性排序 → JSON
  └── Layer 2：claude-sonnet-4-6（~15s）
      └── Prompt: 风险扫描 + 教育性解释 + Suggestion → JSON
      │
      ▼
formatter.py
  └── 拼接 GitHub Markdown 评论（摘要卡 + 风险列表 + Suggestion块）
      │
      ▼
github_client.py
  └── POST /repos/{owner}/{repo}/issues/{number}/comments  → 发布评论
      │
      ▼
✅ GitHub PR 页面出现 Bot 评论
```

### 技术栈确认

| 层级 | 选型 | 理由 |
|------|------|------|
| **语言** | Python 3.13 | 已有环境，anthropic SDK 原生支持 |
| **AI SDK** | `anthropic` 官方 SDK | 流式输出、结构化 JSON 模式支持好 |
| **GitHub API** | `requests` 直接调用 | 轻量，不需要 PyGithub 的额外抽象 |
| **CLI** | `click` + `rich` | 彩色输出，demo 好看 |
| **Web 后端** | `FastAPI` + `uvicorn` | 异步、自动文档、启动快 |
| **前端** | Open Design 生成 HTML/CSS | 无需框架，纯静态，容易 demo |
| **数据库** | **无**（MVP 不需要）| 减少环境依赖；反馈功能 Beta 再加 |
| **部署** | `localhost` + `ngrok`（demo 用）| 零成本，够录视频 |

### LLM Prompt 策略

**Layer 1 — Haiku（摘要，速度优先）**
```
System: 你是代码变更分析助手。请简洁分析 PR 的变更内容。
User: [PR 元数据 + diff]
要求: 输出 JSON，包含 summary.what_changed / change_type / core_change / affected_modules
```

**Layer 2 — Sonnet（风险，质量优先）**
```
System: 你是专注 Vibe Coding 场景的代码审查专家。
规则：
1. 只报告有具体代码证据的问题，不做推测
2. 每条风险必须包含文件名+行号
3. HIGH/MEDIUM 风险必须附教育性解释（≤3句，口语化）
4. 标注 AI 生成代码的惯性陷阱（如适用）
5. 提供具体的修复代码（suggestion_code 字段）

User: [PR 上下文]
输出: JSON risks 数组
```

**GitHub Suggestion 格式（formatter.py 生成）**
```markdown
> **[🔴 SECURITY]** `auth.py:45` — JWT Secret 未做存在性校验
>
> **为什么是问题：** 若 `JWT_SECRET` 未配置，jsonwebtoken 会用 `undefined`
> 签名，任何伪造 token 均可通过验证。这是 **AI 生成认证代码的高频陷阱**。

```suggestion
const secret = process.env.JWT_SECRET;
if (!secret) throw new Error('JWT_SECRET is required');
```

---

## 模块三：Week 1 Action Items

### ✅ 今天立刻做（30 分钟）

1. **申请 GitHub Personal Access Token**
   - 路径：GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - 权限勾选：`repo`（含 public_repo + 写评论权限）
   - 复制 token，填入项目 `.env`

2. **配置 `.env` 文件**
   ```
   ANTHROPIC_API_KEY=你的key
   GITHUB_TOKEN=刚申请的token
   ```

3. **安装依赖**
   ```bash
   cd pr-review
   pip install -r requirements.txt
   ```

4. **首次运行验证**
   ```bash
   python main.py https://github.com/任意公开仓库/pull/任意编号
   ```
   预期：终端输出分析结果（不发 GitHub 评论，先 --dry-run 模式）

### 📅 本周剩余（Day 2-5）

5. **验证 GitHub 评论发布**
   ```bash
   python main.py https://github.com/你自己的仓库/pull/1 --post
   ```
   预期：PR 页面出现 Bot 评论

6. **启动 FastAPI 服务**
   ```bash
   uvicorn api:app --reload --port 8000
   # 访问 http://localhost:8000/docs 测试 POST /analyze
   ```

7. **Open Design 生成前端**
   - 向 Open Design 描述 UI 需求（见下方 prompt 模板）
   - 生成 `frontend/index.html`
   - FastAPI serve 静态文件

**Open Design 前端生成 Prompt 模板：**
```
设计一个 AI PR Review 工具的 Web 界面。
主要功能：
- 顶部标题区：「AI PR Review」Logo + 副标题「为 Vibe Coder 设计的代码审查助手」
- 输入区：一个文本框（placeholder: 粘贴 GitHub PR URL，如 https://github.com/owner/repo/pull/123）
  + 一个「开始分析」按钮
- 分析中状态：Loading 动画 + 进度文案（「正在获取代码变更...」「AI 分析中...」）
- 结果展示区（分三个卡片）：
  1. 📋 变更摘要卡（文件数、行数变化、核心改动描述）
  2. ⚠️ 风险列表（RED/YELLOW/GREEN 标签，文件名:行号，风险描述，教育性解释折叠展开）
  3. 💬 评论预览（GitHub Markdown 格式的评论草稿，带复制按钮）
风格：深色主题，代码感，参考 GitHub 界面语言，使用 Tailwind CSS 风格
输出：完整的单文件 HTML（内联 CSS + JS，无需构建工具）
```
