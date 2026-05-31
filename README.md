# 🤖 X-Reviewer

> 为 Vibe Coder 设计的 GitHub Pull Request 智能代码审查工具
>
> **"AI 帮你写代码，X-Reviewer 帮你 Review AI 写的代码。"**

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)](https://fastapi.tiangolo.com/)
[![Claude](https://img.shields.io/badge/AI-Claude%20Sonnet%204.6-purple)](https://anthropic.com/)
[![Eval](https://img.shields.io/badge/Eval-100%20cases%20%7C%2081%25%20accuracy-brightgreen)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🎬 演示视频

> **📺 B 站演示视频：** https://www.bilibili.com/video/BV18dVJ6CEx9/

---

## 📖 项目背景与核心洞察

本项目是「七牛云 × XEngineer 暑期实训营 2026」竞赛作品，针对**题目三：AI PR Review 助手**开发。

### 📂 项目文档导览

本项目的完整思路链路是：**策略 → 想法 → 怎么做 → 计划 → 技术 → 商业 → 验证 → 调优闭环**。做产品先想清楚方向和能不能赚钱，再定义问题、落地技术，最后持续验证调优。每个阶段都有对应文档，评委可按需直接跳转。

```
明确市场方向（先看市场，再定产品）
  └─ product-strategy.md          ← 策略：竞品分析、差异化定位、TAM $3.6亿、GTM 冷启动
       ↓
发现痛点，定义产品
  └─ pr-review-prd-final.md       ← 想法：用户画像（Vibe Coder）、四层能力缺口、做什么
       ↓
设计实现方案
  └─ engineering-spec.md          ← 怎么做：架构选型、Prompt 策略、Sprint 拆分
       ↓
规划交付节奏
  └─ roadmap.md                   ← 计划：12周路线图、Epic 优先级、里程碑
       ↓
落地技术细节
  └─ SYSTEM_DESIGN.md             ← 技术：模型选择、上下文获取、误报控制、扩展方向
       ↓
验证商业可行性（能不能赚钱）
  └─ BUSINESS_ANALYSIS.md         ← 商业：LTV/CAC >7x、盈亏平衡仅需5用户、12个月预测
       ↓
系统性评测效果
  └─ eval/EVAL_REPORT.md          ← 验证：100用例、修复前65% → 修复后81%、归因分析
       ↓
数据驱动持续调优
  └─ tuning/analyze.py            ← 闭环：持续性错误识别 + 自动生成 Prompt 修改建议
```

| 阶段 | 文档 | 核心内容 |
|------|------|---------|
| **策略** | [product-strategy.md](product-strategy.md) | 竞品全景分析、差异化定位图、GTM 冷启动策略、PLG 增长飞轮设计 |
| **想法** | [pr-review-prd-final.md](pr-review-prd-final.md) | 用户画像（Vibe Coder）、四层能力缺口、用户故事与验收标准、成功指标 |
| **怎么做** | [engineering-spec.md](engineering-spec.md) | Sprint 计划、技术选型决策、双层模型 Prompt 策略设计 |
| **计划** | [roadmap.md](roadmap.md) | 12周发布路线图：Alpha → Beta → v1.0，12个 Epic 优先级矩阵与里程碑 |
| **技术** | [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) | **（竞赛硬性要求）** 模型选择理由、上下文获取优先级、误报控制机制、未来扩展方向 |
| **商业** | [BUSINESS_ANALYSIS.md](BUSINESS_ANALYSIS.md) | TAM $3.6亿、单次成本 $0.02–0.05、LTV/CAC >7x、**盈亏平衡仅需5个付费用户**、12个月财务预测 |
| **验证** | [eval/EVAL_REPORT.md](eval/EVAL_REPORT.md) | 100用例评测：修复前 65% → 修复后 **81%**，漏报0个，误报18个，完整归因与错误数据集 |
| **调优闭环** | [tuning/analyze.py](tuning/analyze.py) | 自动检测持续性错误、退化/改进对比、生成具体 Prompt 修改建议，跑完 eval 自动写入 |

---

## 💰 商业价值

> **结论：商业上可行，但窗口期有限（12–18个月）。** 详见 [BUSINESS_ANALYSIS.md](BUSINESS_ANALYSIS.md)

### 市场规模

```
全球 GitHub 活跃用户                    ~1亿
├── 使用 AI 辅助编程（2026年）          ~30%  → 3,000万 AI 开发者
└── 符合 Vibe Coder 画像（入门-中级）   ~20%  → 600万 目标用户

TAM = 600万用户 × $60/年 = 3.6亿美元/年
SAM = 3.6亿 × 15%       = 5,400万美元/年（独立开发者+小团队）
SOM = 1,000付费用户 × $9/月 = 108,000美元/年（Year 1）
```

### 单位经济

| 指标 | 数值 | 说明 |
|------|------|------|
| 单次分析成本 | $0.02–0.05 | Haiku+Sonnet双层，实测数据 |
| Pro 定价 | $9/月（100次）| 对比锚点：一杯咖啡换一个月专业 Review |
| 毛利率 | 44%–78% | 用户每月100次，成本约$2–5 |
| **盈亏平衡** | **仅需5个付费用户** | 服务器固定成本$30/月，门槛极低 |
| LTV/CAC | >7x | CAC约$8–15，LTV约$108（12个月留存）|
| Payback Period | 约1个月 | CAC ≤ 1个月ARPU，资金效率极高 |

### 增长飞轮

每次 Bot 评论出现在公开 PR → **零成本品牌曝光** → 新用户访问 → 转化付费 → 更多反馈数据 → 准确率提升 → 更多用户推荐。这是工具类 SaaS 的典型 PLG（产品驱动增长）模型，获客成本趋近于零。

### Go/No-Go 判断

**✅ Go** — 三个核心理由：
1. **市场时机恰好**：Vibe Coding 爆发期，Review 工具生态仍空白
2. **单位经济健康**：LTV/CAC >7x，5个付费用户即回本
3. **技术已验证**：MVP 完成，安全漏洞检测率 83%，真实PR测试准确率 89%

---

### 为什么做这个工具？

2025-2026 年，Vibe Coder 群体爆发式增长——这批开发者依赖 Cursor / Copilot / Claude 生成大量代码，但**缺乏识别 AI 生成代码隐患的经验**。

他们面临四层能力缺口：

| 缺口 | 具体表现 |
|------|---------|
| 不知看什么 | 没有 Review checklist，不知道关注哪里 |
| 看不懂风险 | 能读懂逻辑，识别不出安全/性能/边界问题 |
| 不会表达 | 发现问题也不知道怎么写有建设性的 Review 评论 |
| 缺乏标准 | 没有团队规范，不知道什么是"好代码" |

### 现有工具的不足

| 工具 | 能做什么 | 做不到什么 |
|------|---------|-----------|
| CI/Lint（ESLint、SonarQube）| 格式、静态语法 | 架构风险、业务逻辑、上下文理解 |
| 手动问 ChatGPT | 分析代码片段 | 无项目上下文、无结构、无行号定位 |
| CodeRabbit 等专业工具 | 针对有经验开发者找 bug | **无教育性解释，不告诉你"为什么"** |
| **本工具** | **告诉你为什么 + AI 惯性陷阱 + 一键修复** | — |

---

## ✨ 核心功能

### 📋 PR 变更摘要
自动理解 PR 改了什么，识别变更类型（新功能/重构/bugfix），一句话说清核心改动和影响模块。

### 🛡️ 分级风险识别
**HIGH / MEDIUM / LOW** 三级分类，每条风险包含：
- 精确的文件名 + 行号定位
- 口语化的**教育性解释**（≤3句，解释"为什么是问题"）
- **AI 代码惯性陷阱**标注（专门识别 AI 生成代码的高频错误模式）

### ⚡ 一键采纳修复
在 GitHub PR 页面直接点击「Apply suggestion」采纳 AI 建议的 `suggestion` 代码块，零摩擦修复。

### 📊 准确率追踪
内置 👍/👎 反馈按钮（分析结果页末尾）→ SQLite 持久化 → `/stats-page` 监控看板，量化「有帮助」率，支持告警阈值（P90延迟 / 错误率 / 有帮助率 / 评分异常）。

### 🕐 历史记录
自动保存最近5次分析结果到 localStorage，刷新不丢失，点击即可恢复。

---

## 📊 实测准确性

> 双轨评测：**100个本地结构化用例** + **14个真实 GitHub PR**（含预埋漏洞）

### 整体表现

| 类别 | 修复前 | 修复后 | 变化 |
|------|--------|--------|------|
| **安全漏洞识别** | 83% | **86%** | +3pp |
| **代码质量判断** | 27% | **80%** | **+53pp** |
| **干净代码识别（误报控制）**| 67% | **80%** | **+13pp** |
| 性能问题识别 | 55% | **70%** | +15pp |
| 边界/陷阱用例 | 73% | **87%** | +14pp |
| **本地用例整体** | 65% | **81%** ✅ | **+16pp** |
| **真实 PR 测试** | — | **89%**（9/10新PR，#6-14）| — |

### 本地测试用例覆盖

```
100 个用例 = Security(35) + Performance(20) + Quality(15) + Clean(15) + Edge(15)

难度分布：Easy(48) + Medium(25) + Hard(27)
语言覆盖：Python(89) + JavaScript(8) + TypeScript(2) + Go(1)
预期HIGH用例：46个 / 预期无HIGH用例：54个（含干净代码和边界陷阱）
```

### 真实 PR 测试结果（#6–#14）

| PR | 难度 | 漏洞场景 | 评分 | HIGH | 结果 |
|----|------|---------|------|------|------|
| [#6](https://github.com/vigariokoestner958-droid/pr-review-test/pull/6) | Easy | SQL注入：字符串拼接查询 | 3/10 | 1 | ✅ |
| [#7](https://github.com/vigariokoestner958-droid/pr-review-test/pull/7) | Easy | XSS：innerHTML插入用户内容 | 9/10 | 1 | ✅ |
| [#8](https://github.com/vigariokoestner958-droid/pr-review-test/pull/8) | Easy | 密码明文存储+打印到日志 | 3/10 | 2 | ✅ |
| [#9](https://github.com/vigariokoestner958-droid/pr-review-test/pull/9) | Easy | 管理接口无任何身份验证 | 3/10 | 1 | ✅ |
| [#10](https://github.com/vigariokoestner958-droid/pr-review-test/pull/10) | Medium | N+1查询（循环内逐条查用户）| 6/10 | 0 | ❌ 漏报 |
| [#11](https://github.com/vigariokoestner958-droid/pr-review-test/pull/11) | Medium | TOCTOU竞态+无事务保护 | 3/10 | 2 | ✅ |
| [#12](https://github.com/vigariokoestner958-droid/pr-review-test/pull/12) | Medium | 路径拼接未规范化（路径遍历）| 6/10 | 1 | ✅ |
| [#13](https://github.com/vigariokoestner958-droid/pr-review-test/pull/13) | Hard | JWT alg:none绕过签名验证 | 4/10 | 1 | ✅ |
| [#14](https://github.com/vigariokoestner958-droid/pr-review-test/pull/14) | Hard | pickle反序列化用户输入（RCE）| 3/10 | 2 | ✅ |

> **唯一漏报**：#10 N+1查询被判为 MEDIUM（无 HIGH），未能触发 REQUEST_CHANGES。性能类问题严重度识别仍有改进空间。

### 误报分析与修复

发现的 31 个误报按根因分类后：
- **类型 A（64%）**：严重度过激——AI 将代码质量问题（裸except、魔法数字等）错判为 HIGH → **修复：明确 HIGH/MEDIUM/LOW 定义**
- **类型 B（23%）**：上下文误解——看到安全关键词就报警，无视正确用法 → **修复：加入负面引导规则**
- **类型 C（13%）**：JSON 解析错误——含中文注释时输出格式异常 → **修复：自动重试机制**

详细分析见：[eval/EVAL_REPORT.md](eval/EVAL_REPORT.md)

---

## 🏗️ 系统架构

```
用户输入 PR URL
      │
      ▼
┌─────────────────┐
│   Web Frontend  │  Neumorphism 风格单页应用（历史记录 + 评论预览 + 👍👎 反馈）
│  (index.html)   │
└────────┬────────┘
         │ POST /analyze
         ▼
┌─────────────────┐
│   FastAPI 后端  │  api.py — 自动采集指标、告警
└────────┬────────┘
    ┌────┴────┐
    ▼         ▼
GitHub API   AI 分析引擎 (analyzer.py)
Client       │
             ├── Layer 1: claude-haiku-4-5-20251001 (~3s)
             │   变更摘要 + 文件重要性排序
             │   ↳ JSON解析失败自动重试
             │
             └── Layer 2: claude-sonnet-4-6 (~15s)
                 风险识别 + 教育性解释 + Suggestion 生成
                 ↳ 明确 HIGH/MEDIUM/LOW 定义
                 ↳ 负面引导：好代码不误报
                 ↳ JSON解析失败自动重试
                      │
                      ▼
               结构化 JSON → formatter.py
               ┌──────┴──────┐
               ▼             ▼
         前端动态渲染    GitHub PR 评论发布
                      ▼
           monitoring.py 指标采集
           ├── analyses 表：延迟/评分/风险分布
           ├── /api/metrics JSON 接口
           └── /stats 监控看板（告警+趋势+分布）
```

---

## 🤖 模型选择策略

### 为什么选 Claude？

| 维度 | 说明 |
|------|------|
| **代码语义理解** | Claude Sonnet 在识别安全模式、理解代码上下文方面持续领先 |
| **指令遵从性** | 严格遵守"只报告有证据的问题"的约束，可靠输出结构化 JSON |
| **中文教育性解释** | 口语化中文质量高，适合非技术背景的 Vibe Coder |
| **成本效益** | Haiku+Sonnet 双层架构，每次分析约 $0.02–0.05 |

### 双层模型架构设计

| 层 | 模型 | 职责 | 延迟 | 成本/次 | 选择理由 |
|----|------|------|------|---------|---------|
| Layer 1 | `claude-haiku-4-5-20251001` | 变更摘要 + 文件重要性排序 | ~3s | ~$0.003 | 结构化提取任务，速度优先 |
| Layer 2 | `claude-sonnet-4-6` | 风险识别 + 教育性解释 + Suggestion | ~15s | ~$0.015 | 复杂推理和安全模式识别 |

**降级策略：**
- 单文件 diff 超 50k tokens → 截断并标注"已做部分分析"
- JSON 解析失败 → 自动重试（最多2次）
- PR 超 2000 行 / 100 文件 → 拒绝并返回拆分建议

---

## 📡 上下文获取策略

**上下文优先级（高 → 低）：**

```
① PR Description    ← 开发者意图，最关键信号
② 变更文件 diff    ← 实际代码变更（patch/hunk）
③ 原始文件内容     ← 理解变更前状态（via GitHub Contents API）
④ PR 标题 + Labels ← 补充意图分类
⑤ 现有 Review 评论 ← 避免重复已有建议
```

**为什么不用 RAG / 向量检索（当前版本）：**

PR Review 的核心是"理解这次变更"，而非"理解整个仓库"。直接传入 diff + 原始文件在大多数 PR 场景下已足够。仓库级全局理解是 v2.0 规划项。

---

## 🎯 误报与漏报控制机制

| 机制 | 实现方式 | 解决的问题 |
|------|---------|-----------|
| **严重度定义锁定** | Prompt 明确 HIGH = 可被攻击者利用或导致数据丢失 | 质量问题被过度评为 HIGH |
| **负面引导规则** | 好代码实践（参数化查询、bcrypt、有过期JWT）不报警 | 正确代码被误报 |
| **证据锁定** | 每条风险必须有文件名+行号，无法定位则不输出 | 无根据的推测性告警 |
| **噪音阈值** | LOW 以下风格建议不输出 | 无效噪音干扰开发流程 |
| **JSON 重试** | 解析失败自动重试，附加格式修正提示 | 中文注释导致的解析错误 |
| **反馈回路** | 👎"不准确"记录到 SQLite，支持 Prompt 调优 | 持续准确率下滑 |

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Anthropic API Key（[申请地址](https://console.anthropic.com/)）
- GitHub Personal Access Token（需要 `repo` 权限）

### 三步启动

```bash
# 1. 克隆并安装
git clone https://github.com/vigariokoestner958-droid/ai-pr-review-assistant.git
cd ai-pr-review-assistant
pip install -r requirements.txt

# 2. 配置密钥
cp .env.example .env
# 编辑 .env 填入：
# ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
# GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxx

# 3. 启动服务
python -m uvicorn api:app --reload --port 8001
# 打开 http://localhost:8001
```

> **获取 GitHub Token：** Settings → Developer settings → Personal access tokens (classic) → 勾选 `repo`

### CLI 模式

```bash
# 本地分析（不发布评论）
python -X utf8 main.py https://github.com/owner/repo/pull/123

# 分析并自动发布评论到 GitHub PR
python -X utf8 main.py https://github.com/owner/repo/pull/123 --post
```

---

## 🧪 快速体验（测试 PR 库）

无需准备代码，直接用以下 PR 验证效果：

**原始测试组（#1–#5）**

| PR | 预埋漏洞场景 | 预期评分 | 预期判断 |
|----|------------|---------|---------|
| [#1](https://github.com/vigariokoestner958-droid/pr-review-test/pull/1) | 命令注入 + CORS通配符 + 弱密码生成 | ~3/10 | 🚫 拒绝合并 |
| [#2](https://github.com/vigariokoestner958-droid/pr-review-test/pull/2) | XSS + 危险eval + 原型污染 + token存localStorage | ~3/10 | 🚫 拒绝合并 |
| [#3](https://github.com/vigariokoestner958-droid/pr-review-test/pull/3) | SQL注入 + 明文密码 + 无权限校验（最多漏洞）| ~2/10 | 🚫 拒绝合并 |
| [#4](https://github.com/vigariokoestner958-droid/pr-review-test/pull/4) | N+1查询 + 内存泄露 + 同步阻塞通知 | ~2/10 | 🚫 拒绝合并 |
| [#5](https://github.com/vigariokoestner958-droid/pr-review-test/pull/5) | **干净代码（对照组）** | ~8/10 | ✅ 建议合并 |

**扩展测试组（#6–#14，Easy/Medium/Hard 三难度）**

| PR | 难度 | 漏洞场景 |
|----|------|---------|
| [#6](https://github.com/vigariokoestner958-droid/pr-review-test/pull/6) | Easy | SQL注入：字符串直接拼接查询 |
| [#7](https://github.com/vigariokoestner958-droid/pr-review-test/pull/7) | Easy | XSS：innerHTML插入用户输入 |
| [#8](https://github.com/vigariokoestner958-droid/pr-review-test/pull/8) | Easy | 密码明文存储并打印到日志 |
| [#9](https://github.com/vigariokoestner958-droid/pr-review-test/pull/9) | Easy | 管理删除接口无任何鉴权 |
| [#10](https://github.com/vigariokoestner958-droid/pr-review-test/pull/10) | Medium | N+1查询：循环内逐条查用户 |
| [#11](https://github.com/vigariokoestner958-droid/pr-review-test/pull/11) | Medium | 转账操作无事务保护（竞态条件）|
| [#12](https://github.com/vigariokoestner958-droid/pr-review-test/pull/12) | Medium | 路径拼接未规范化（目录遍历）|
| [#13](https://github.com/vigariokoestner958-droid/pr-review-test/pull/13) | Hard | JWT alg:none攻击绕过签名验证 |
| [#14](https://github.com/vigariokoestner958-droid/pr-review-test/pull/14) | Hard | pickle反序列化用户cookie（RCE）|

---

## 📁 项目结构

```
ai-pr-review-assistant/
│
├── 🐍 核心代码（根目录）
│   ├── main.py              # CLI 入口：python main.py <PR_URL> [--post]
│   ├── api.py               # FastAPI 后端（/analyze /feedback /stats /api/metrics）
│   ├── analyzer.py          # Claude 双层分析引擎（核心 + 重试逻辑）
│   ├── github_client.py     # GitHub API 封装（获取 PR 数据、发布评论）
│   ├── formatter.py         # 结构化结果 → GitHub Markdown / CLI 输出
│   └── monitoring.py        # 指标采集、告警阈值、/stats 看板数据
│
├── 🌐 frontend/             # Web 前端
│   ├── index.html           # 主页（Neumorphism 风格，历史记录 + 评论预览 + 👍👎 反馈）
│   ├── stats.html           # 监控看板（从 /api/metrics 实时拉取数据）
│   └── docs.html            # API 文档页（含接口说明 + Swagger 链接）
│
├── 🧪 eval/                 # 评测框架
│   ├── cases.py             # 100个结构化测试用例（5类 × 4语言）
│   ├── runner.py            # 评测运行器（支持 --category/--difficulty 过滤）
│   ├── report.py            # Markdown 报告生成器
│   ├── EVAL_REPORT.md       # 完整评测报告（基线 vs 修复后对比 + 归因分析）
│   ├── results/             # 自动评测 JSON 结果文件
│   └── results_manual/      # 手工分析测试报告
│
├── 📜 scripts/              # 工具脚本
│   ├── create_test_prs.py   # 批量创建测试 PR（含5类漏洞场景）
│   └── setup_test_repo.py   # 初始化测试仓库
│
├── 📄 说明文档（根目录）
│   ├── README.md
│   ├── SYSTEM_DESIGN.md     # 系统设计（模型/上下文/扩展方向）
│   ├── BUSINESS_ANALYSIS.md # 商业可行性分析
│   ├── test-report.md       # 5个测试 PR 完整分析报告
│   └── roadmap.md / pr-review-prd-final.md / ...
│
└── ⚙️ 配置
    ├── requirements.txt
    └── .env.example
```

---

## 🔌 API 接口文档

### `POST /analyze` — 核心分析接口

```json
// 请求
{
  "pr_url": "https://github.com/owner/repo/pull/123",
  "post_comment": false
}

// 响应
{
  "pr_title": "feat: add auth module",
  "pr_url": "https://github.com/...",
  "verdict": "REQUEST_CHANGES",     // APPROVE | REQUEST_CHANGES | COMMENT
  "overall_score": 3,               // 1–10
  "summary_change_type": "feature", // feature|bugfix|refactor|dependency|other
  "summary_core_change": "新增认证模块，包含JWT签发和密码哈希存储",
  "affected_modules": ["auth.py"],
  "risks": [
    {
      "severity": "HIGH",           // HIGH | MEDIUM | LOW
      "category": "SECURITY",       // SECURITY|PERFORMANCE|CORRECTNESS|ARCHITECTURE|MAINTAINABILITY
      "file": "auth.py",
      "line": 45,
      "title": "明文存储密码",
      "description": "密码直接以明文写入数据库",
      "why_it_matters": "一旦数据库泄露所有密码直接暴露...",
      "ai_trap": "AI常为简化示例跳过密码哈希...",
      "suggestion": "使用bcrypt哈希后存储",
      "suggestion_code": "import bcrypt\nhashed = bcrypt.hashpw(...)"
    }
  ],
  "quick_wins": ["将密码改用bcrypt哈希", "使用参数化查询"],
  "github_comment": "## 🤖 AI PR Review\n...",
  "comment_url": null
}
```

### `POST /feedback` — 用户反馈

```json
{ "pr_url": "https://github.com/...", "vote": "up" }
```
记录👍/👎到 SQLite，实时更新监控看板的有帮助率指标。

### `GET /stats-page` — 监控看板

完整的 HTML 看板（`frontend/stats.html`），实时从 `/api/metrics` 拉取数据：
- KPI 卡片（有帮助率 / 平均延迟 / 错误率 / 平均评分）
- 告警状态（ok / warn / crit 三级）
- 7天每日分析量趋势
- 评分 1-10 分布直方图
- 最近15条分析记录（北京时间）

### `GET /api/metrics?days=7` — 结构化指标 JSON

供外部监控系统（Grafana、Datadog 等）接入，含 `summary` / `alerts` / `daily_trend` / `score_distribution` / `recent`。

### `GET /health` — 健康检查

---

## 📈 监控指标与告警

| 指标 | 告警阈值 | 说明 |
|------|---------|------|
| 有帮助率 | warn < 60% / crit < 40% | 核心准确性指标 |
| P90 延迟 | warn > 30s / crit > 60s | 响应速度 |
| 错误率 | warn > 5% / crit > 15% | 服务稳定性 |
| 平均评分偏高 | warn > 8.5 / crit > 9.5 | AI过于宽松（可能误放安全问题）|
| 平均评分偏低 | warn < 3.0 / crit < 2.0 | AI过于严苛（误报风险）|

---

## 🗺️ 未来扩展方向

### v1.1（1–3 个月）：自动化
- **GitHub App Webhook**：PR 提交自动触发，无需手动输入 URL
- **`@bot re-review` 命令**：修复问题后评论触发重新分析
- **准确率调优循环**：基于👎反馈数据的 Prompt 迭代，目标有帮助率 >75%

### v2.0（3–6 个月）：深度上下文
- **仓库级上下文理解**：tree-sitter 解析 AST + 向量索引，识别跨文件依赖问题
- **团队规范学习**：上传 `.coding-standards.md`，基于规范 Review
- **历史记忆**：记录仓库高频问题，避免重复犯同类错误
- **VS Code 插件**：提 PR 前本地运行，零摩擦防翻车

### v3.0（6–12 个月）：生态
- **Vibe Coding 成长报告**：分析开发者跨 PR 代码模式，生成个人能力提升路线
- **CI/CD 集成**：准确率 >90% 后作为 GitHub Actions 可选阻塞步骤
- **Enterprise**：私有化部署、合规审计、SAML SSO

---

## 🛠️ 技术栈

| 层级 | 技术 | 选择理由 |
|------|------|---------|
| AI 分析 | Anthropic Claude (Haiku + Sonnet) | 代码理解深，指令遵从性强，JSON 输出稳定 |
| 后端 | Python + FastAPI | 异步支持，启动快，自动生成 API 文档 |
| GitHub 集成 | GitHub REST API v3 | 官方支持，Rate Limit 充足（5000 req/hr）|
| 数据持久化 | SQLite | MVP 阶段零运维成本，足够支撑早期用户规模 |
| 前端 | 原生 HTML/CSS/JS | 无框架，单文件，零构建工具，易部署 |
| 代码高亮 | highlight.js（CDN）| 轻量，支持多语言语法高亮 |
| 字体 | Plus Jakarta Sans + DM Sans + JetBrains Mono | Neumorphism 设计系统，柔和立体质感 |

---

## 📄 核心文档索引

| 文档 | 内容 |
|------|------|
| [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) | 模型选择、上下文获取、误报控制、扩展方向（竞赛要求）|
| [BUSINESS_ANALYSIS.md](BUSINESS_ANALYSIS.md) | TAM/SAM/SOM、成本结构、盈亏平衡、12个月财务预测 |
| [eval/EVAL_REPORT.md](eval/EVAL_REPORT.md) | 100用例评测报告、误报归因、修复前后对比 |
| [test-report.md](test-report.md) | 5个测试 PR 的完整手工分析结果 |
| [roadmap.md](roadmap.md) | 12周发布路线图（Alpha → Beta → v1.0）|

---

## 📜 知识产权声明

本项目为独立开发，严格遵守七牛云实训营相关规定。代码、文档、设计均为原创。

---

*由 THC 开发 · 七牛云 × XEngineer 暑期实训营 2026*
