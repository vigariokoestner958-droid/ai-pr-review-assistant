# 🤖 AI PR Review 助手

> 为 Vibe Coder 设计的 GitHub Pull Request 智能代码审查工具

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)](https://fastapi.tiangolo.com/)
[![Claude](https://img.shields.io/badge/AI-Claude%20Sonnet%204.6-purple)](https://anthropic.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🎬 演示视频

> **📺 B 站演示视频：**（录制完成后补充链接）

---

## 📖 项目简介

本项目是「七牛云 × XEngineer 暑期实训营 2026」竞赛作品，针对**题目三：AI PR Review 助手**开发。

**核心洞察：** Vibe Coder（依赖 Cursor / Copilot / Claude 等 AI 工具编程的开发者）面临的问题不是没有 Review 工具，而是现有工具只告诉你「哪里有问题」，却不告诉你「**为什么是问题 + AI 生成代码的惯性陷阱 + 怎么一键修复**」。

### 与现有工具的差异

| 方案 | 能做什么 | 做不到什么 |
|------|---------|-----------|
| CI/Lint（ESLint、SonarQube）| 格式、静态语法 | 架构风险、业务逻辑、上下文理解 |
| 手动问 ChatGPT | 分析代码片段 | 无项目上下文、无结构、无行号定位 |
| CodeRabbit 等专业工具 | 针对有经验开发者找 bug | 无教育性解释，不解释「为什么」 |
| **本工具** | **告诉你为什么 + AI 惯性陷阱 + 一键修复** | — |

---

## ✨ 核心功能

- 📋 **PR 变更摘要**：自动理解改了什么，核心逻辑一句话说清楚
- 🛡️ **风险分级识别**：HIGH / MEDIUM / LOW 三级，每条附带教育性解释
- ⚡ **一键采纳修复**：GitHub PR 页面直接点击「Apply suggestion」，零摩擦
- 🎓 **AI 陷阱标注**：专门识别 AI 生成代码的高频惯性错误
- 📊 **准确率追踪**：内置 👍/👎 反馈收集，量化「有帮助」率

---

## 📊 实测准确性

> 基于 5 个测试 PR、**20 个预埋漏洞**的验证结果：

| 指标 | 结果 |
|------|------|
| 预埋漏洞检测率 | **20/20 = 100%** |
| 误报数 | **0 个** |
| 额外发现有效问题 | **1 个**（超预期） |
| 干净代码评分 | **8/10 ✅** |
| 漏洞代码评分 | **2–4/10 🚫** |
| 单次分析总耗时 | **~18 秒**（P90） |

测试场景覆盖：命令注入、XSS、SQL 注入、明文密码、N+1 查询、内存泄露、干净代码对照组。

👉 完整报告：[test-report.md](test-report.md)

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
│   FastAPI 后端  │  api.py
└────────┬────────┘
    ┌────┴────┐
    ▼         ▼
GitHub API   AI 分析引擎 (analyzer.py)
Client       │
             ├── Layer 1: claude-haiku-4-5  (~3s)
             │   变更摘要 + 文件重要性排序
             │
             └── Layer 2: claude-sonnet-4-6 (~15s)
                 风险识别 + 教育性解释 + Suggestion 生成
                      │
                      ▼
               结构化 JSON → formatter.py
               ┌──────┴──────┐
               ▼             ▼
         前端动态渲染    GitHub PR 评论发布
                      ▼
               反馈收集 (SQLite)
               /feedback  /stats 准确率看板
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

| 层 | 模型 | 任务 | 延迟 | 成本/次 |
|----|------|------|------|---------|
| Layer 1 | `claude-haiku-4-5-20251001` | 变更摘要、文件重要性排序 | ~3s | ~$0.003 |
| Layer 2 | `claude-sonnet-4-6` | 风险识别、教育性解释、Suggestion 生成 | ~15s | ~$0.015 |

**总成本：$0.02–0.05 / 次**，双层设计在速度与质量之间取得平衡。

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
| **证据锁定** | System Prompt 强制要求「只报告有具体代码证据的问题，不做推测」 |
| **位置锁定** | 每条风险必须包含文件名 + 行号，无法定位则不输出 |
| **噪音过滤** | LOW 以下的风格建议不报告 |
| **反馈回路** | 👎「不准确」触发 Prompt 持续调优 |
| **Vibe Coding 专项** | 针对 AI 代码高频陷阱显式列举（SQL拼接、shell=True、eval、硬编码密钥等）|

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Anthropic API Key（[申请地址](https://console.anthropic.com/)）
- GitHub Personal Access Token（需要 `repo` 权限）

### 安装运行

```bash
# 1. 克隆仓库
git clone https://github.com/vigariokoestner958-droid/ai-pr-review-assistant.git
cd ai-pr-review-assistant

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入以下两个 Key：
# ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
# GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxx

# 4. 启动服务
python -m uvicorn api:app --reload --port 8000

# 5. 打开浏览器
# http://localhost:8000
```

> **获取 GitHub Token：** GitHub → Settings → Developer settings → Personal access tokens (classic) → 勾选 `repo`

### CLI 模式（无需浏览器）

```bash
# 本地分析，仅展示结果
python -X utf8 main.py https://github.com/owner/repo/pull/123

# 分析并自动发布评论到 GitHub PR
python -X utf8 main.py https://github.com/owner/repo/pull/123 --post
```

---

## 🧪 快速体验

用以下测试 PR 立即验证效果（无需自己准备代码）：

| PR | 场景 | 预期评分 | 预期判断 |
|----|------|---------|---------|
| [#1](https://github.com/vigariokoestner958-droid/pr-review-test/pull/1) | 命令注入 + CORS + 弱密码 | ~3/10 | 🚫 拒绝合并 |
| [#2](https://github.com/vigariokoestner958-droid/pr-review-test/pull/2) | XSS + eval + 原型污染 | ~3/10 | 🚫 拒绝合并 |
| [#3](https://github.com/vigariokoestner958-droid/pr-review-test/pull/3) | SQL注入 + 明文密码 + 无权限校验 | ~2/10 | 🚫 拒绝合并 |
| [#4](https://github.com/vigariokoestner958-droid/pr-review-test/pull/4) | N+1查询 + 内存泄露 + 同步阻塞 | ~2/10 | 🚫 拒绝合并 |
| [#5](https://github.com/vigariokoestner958-droid/pr-review-test/pull/5) | 干净代码（对照组）| ~8/10 | ✅ 建议合并 |

---

## 📁 项目结构

```
ai-pr-review-assistant/
├── main.py              # CLI 入口
├── api.py               # FastAPI 后端（/analyze /feedback /stats）
├── analyzer.py          # Claude 双层分析引擎（核心）
├── github_client.py     # GitHub API 封装
├── formatter.py         # 结构化结果 → GitHub Markdown / CLI 输出
├── frontend/
│   └── index.html       # Web 单页应用（TypeGallery 风格）
├── SYSTEM_DESIGN.md     # 系统设计说明（竞赛要求文档）
├── test-report.md       # 5个测试 PR 完整分析报告
├── test_results/        # 详细测试数据
├── requirements.txt
└── .env.example
```

---

## 🔌 API 接口

### `POST /analyze` — 分析 PR

```json
// 请求
{ "pr_url": "https://github.com/owner/repo/pull/123", "post_comment": false }

// 响应关键字段
{
  "verdict": "APPROVE | REQUEST_CHANGES | COMMENT",
  "overall_score": 7,
  "risks": [{ "severity": "HIGH", "file": "auth.py", "line": 45, "title": "...", "why_it_matters": "...", "suggestion_code": "..." }],
  "quick_wins": ["..."],
  "comment_url": "https://github.com/...#issuecomment-xxx"
}
```

### `GET /feedback?pr=URL&vote=up|down` — 收集反馈

### `GET /stats` — 准确率统计看板

### `GET /health` — 健康检查

---

## 📄 系统设计说明

竞赛要求说明「**模型选择、上下文获取方式及未来扩展方向的设计思路**」，完整文档见：

👉 **[SYSTEM_DESIGN.md](SYSTEM_DESIGN.md)**

---

## 🛠️ 技术栈

| 层级 | 技术 | 选择理由 |
|------|------|---------|
| AI 分析 | Anthropic Claude (Haiku + Sonnet) | 代码理解深，指令遵从性强 |
| 后端 | Python + FastAPI | 异步支持，启动快，自动 API 文档 |
| GitHub 集成 | GitHub REST API v3 | 官方支持，Rate Limit 充足 |
| 数据持久化 | SQLite | MVP 阶段零运维成本 |
| 前端 | 原生 HTML/CSS/JS + highlight.js | 无框架，单文件，易部署 |
| 设计系统 | TypeGallery（EB Garamond + Manrope + JetBrains Mono）| 印刷排版质感 |

---

## 📜 知识产权声明

本项目为独立开发，严格遵守七牛云实训营相关规定。代码、文档、设计均为原创。

---

*由 THC 开发 · 七牛云 × XEngineer 暑期实训营 2026*
