"""Dual-layer AI analysis engine — OpenAI-compatible (works with any proxy)."""
import json
import os
from dataclasses import dataclass, field
from typing import Optional
from openai import OpenAI
from github_client import PRData, PRFile

# Models — PackyAPI 通常支持这两个 Claude 模型名称，如不行可改为 gpt-4o
FAST_MODEL = os.getenv("FAST_MODEL", "claude-haiku-4-5-20251001")
DEEP_MODEL = os.getenv("DEEP_MODEL", "claude-sonnet-4-6")

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_DIFF_CHARS   = 80_000   # ~20k tokens, safe for Sonnet
MAX_PR_FILES     = 100
MAX_PR_LINES     = 2000


# ── Result models ─────────────────────────────────────────────────────────────

@dataclass
class Risk:
    severity: str          # HIGH | MEDIUM | LOW
    category: str          # SECURITY | PERFORMANCE | CORRECTNESS | ARCHITECTURE | MAINTAINABILITY
    file: str
    line: Optional[int]
    title: str
    description: str
    why_it_matters: str
    ai_trap: Optional[str]
    suggestion: str
    suggestion_code: Optional[str]


@dataclass
class Summary:
    what_changed: str
    change_type: str
    core_change: str
    affected_modules: list[str]


@dataclass
class AnalysisResult:
    summary: Summary
    risks: list[Risk]
    verdict: str           # APPROVE | REQUEST_CHANGES | COMMENT
    overall_score: int     # 1–10
    quick_wins: list[str]
    skipped: bool = False
    skip_reason: str = ""


# ── Context builder ───────────────────────────────────────────────────────────

def _build_context(pr: PRData) -> tuple[str, bool, str]:
    """Returns (context_text, skipped, reason)."""
    total_lines = pr.additions + pr.deletions
    if pr.changed_files > MAX_PR_FILES:
        return "", True, f"PR 包含 {pr.changed_files} 个文件，超过限制（{MAX_PR_FILES}）。建议拆分 PR。"
    if total_lines > MAX_PR_LINES:
        return "", True, f"PR 变更行数 {total_lines} 超过限制（{MAX_PR_LINES}）。建议拆分为更小的 PR。"

    parts = [
        f"## PR 信息",
        f"标题：{pr.title}",
        f"描述：{pr.body or '（无描述）'}",
        f"作者：{pr.author}",
        f"分支：{pr.base_branch} ← {pr.head_branch}",
        f"变更：{pr.changed_files} 个文件，+{pr.additions}/-{pr.deletions} 行",
        "",
        "## 代码变更",
    ]

    diff_chars = 0
    for f in pr.files:
        if not f.patch:
            continue
        file_header = f"\n### {f.filename} ({f.status}, +{f.additions}/-{f.deletions})\n"
        patch_block = f"```diff\n{f.patch}\n```\n"
        chunk = file_header + patch_block
        if diff_chars + len(chunk) > MAX_DIFF_CHARS:
            parts.append(f"\n### （其余文件因超出长度限制已省略）")
            break
        parts.append(chunk)
        diff_chars += len(chunk)

    return "\n".join(parts), False, ""


# ── Prompts ───────────────────────────────────────────────────────────────────

_SUMMARY_SYSTEM = """\
你是代码变更分析助手。请简洁分析 PR 的变更内容，输出 JSON 格式。
不要解释，直接输出合法 JSON。"""

_SUMMARY_USER = """\
{context}

请输出以下 JSON（不要有其他文字）：
{{
  "what_changed": "一句话描述改了什么",
  "change_type": "feature|bugfix|refactor|dependency|other",
  "core_change": "核心变更的技术描述（1-2句）",
  "affected_modules": ["模块1", "模块2"]
}}"""

_RISK_SYSTEM = """\
你是专注 Vibe Coding 场景的代码审查专家。你的读者是刚开始学编程、依赖 AI 写代码的新手，
所以你的语言必须通俗易懂，像朋友解释一样，不要堆砌专业术语。

【语言要求——必须遵守】
- 用大白话写，避免直接甩出专业词汇（如"SQL注入"、"XSS"、"竞态条件"）而不解释
- 如果必须用技术词，立刻用一句话解释它是什么意思
- 描述危害时，说清楚"如果不修复，会发生什么具体的坏事"，而不是抽象的"存在安全风险"
- 修复建议要具体，告诉用户"把第X行改成这样"，而不是"应当使用参数化查询"
- 语气友好，像在帮朋友 review 代码，不要像在写安全报告

【语言示例】
  不好的写法："存在SQL注入漏洞，攻击者可利用此漏洞执行任意SQL语句。"
  好的写法："这里直接把用户输入拼进了数据库查询，黑客可以输入特殊字符来偷走你数据库里所有的数据，甚至删库。"

  不好的写法："存在XSS跨站脚本攻击风险。"
  好的写法："用户输入的内容直接显示在页面上，没有过滤，别人可以在你的网站上注入恶意代码，劫持其他用户的账号。"

  不好的写法："建议使用bcrypt进行密码哈希处理。"
  好的写法："密码直接存成明文了，数据库一旦泄露，所有用户的密码都会暴露。改用 bcrypt 加密存储，就算数据库被盗也没人能看到真实密码。"

【严重度定义——必须严格遵守】
HIGH   = 可被外部攻击者直接利用 OR 导致数据丢失/服务崩溃的缺陷。
         典型例子：SQL注入、XSS、命令注入、硬编码密钥、明文存储密码、
                   未授权访问、可被重放的身份验证缺陷、
                   N+1查询且无分页（大数据量下会拖垮数据库导致服务崩溃）。
MEDIUM = 存在真实风险但需要特定条件，或影响范围有限。
         典型例子：内存泄漏、竞态条件、弱随机数用于安全场景。
         注意：N+1查询若同时缺少分页限制（无 LIMIT/paginate），数据量大时可拖垮服务，应评为 HIGH。
LOW    = 代码质量/可维护性问题，无直接安全或稳定性影响。
         典型例子：裸except、资源未关闭、魔法数字、print调试、可变默认参数、
                   缺少输入格式校验（非安全边界）、浮点数比较、未处理Promise。

【判断原则】
- 如果一段代码没有直接暴露给外部攻击者，不能评为 HIGH
- 代码风格问题、可读性问题、优化建议 → 最高 LOW
- 看到好的代码实践（参数化查询、bcrypt哈希、有过期的JWT）→ 不要误报

规则：
1. 只报告有具体代码证据的问题，不做推测性建议
2. 每条风险必须有文件名和行号（如无法确定行号，写 null）
3. HIGH/MEDIUM 风险必须附教育性解释（≤3句，用大白话，解释"为什么危险"和"会发生什么"）
4. 如果该问题是 AI 生成代码的惯性陷阱，在 ai_trap 字段注明（也用大白话）
5. suggestion_code 提供可直接替换的修复代码（如无，写 null）
6. 不要制造"噪音"：LOW 以下的风格建议不要报告
7. 直接输出合法 JSON，不要解释"""

_RISK_USER = """\
{context}

请输出以下 JSON（不要有其他文字）：
{{
  "risks": [
    {{
      "severity": "HIGH|MEDIUM|LOW",
      "category": "SECURITY|PERFORMANCE|CORRECTNESS|ARCHITECTURE|MAINTAINABILITY",
      "file": "filename.py",
      "line": 45,
      "title": "简短标题（≤15字）",
      "description": "问题描述（1句）",
      "why_it_matters": "为什么是问题——教育性解释（≤3句，口语化）",
      "ai_trap": "AI 生成代码的常见陷阱说明，或 null",
      "suggestion": "修复建议（1句）",
      "suggestion_code": "可直接替换的修复代码，或 null"
    }}
  ],
  "verdict": "APPROVE|REQUEST_CHANGES|COMMENT",
  "overall_score": 7,
  "quick_wins": ["可立即做的小改进1", "可立即做的小改进2"]
}}"""


# ── Main analyzer ─────────────────────────────────────────────────────────────

class Analyzer:
    def __init__(self, api_key: str):
        base_url = os.getenv("AI_BASE_URL")   # e.g. https://api.packyapi.com/v1
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def analyze(self, pr: PRData) -> AnalysisResult:
        context, skipped, reason = _build_context(pr)
        if skipped:
            return AnalysisResult(
                summary=Summary("", "", "", []),
                risks=[], verdict="COMMENT", overall_score=0,
                quick_wins=[], skipped=True, skip_reason=reason,
            )

        summary = self._layer1_summary(context)
        risks_data = self._layer2_risks(context)

        return AnalysisResult(
            summary=summary,
            risks=risks_data["risks"],
            verdict=risks_data["verdict"],
            overall_score=risks_data["overall_score"],
            quick_wins=risks_data["quick_wins"],
        )

    def _call(self, model: str, system: str, user: str, max_tokens: int = 4096) -> str:
        resp = self.client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
        )
        return resp.choices[0].message.content.strip()

    def _layer1_summary(self, context: str) -> Summary:
        """Fast summary — Layer 1. Retries once on JSON parse failure."""
        for attempt in range(2):
            raw = self._call(FAST_MODEL, _SUMMARY_SYSTEM,
                             _SUMMARY_USER.format(context=context), max_tokens=512)
            try:
                d = json.loads(_strip_code_fence(raw))
                break
            except json.JSONDecodeError:
                if attempt == 1:
                    raise
        return Summary(
            what_changed=d.get("what_changed", ""),
            change_type=d.get("change_type", "other"),
            core_change=d.get("core_change", ""),
            affected_modules=d.get("affected_modules", []),
        )

    def _layer2_risks(self, context: str) -> dict:
        """Deep risk analysis — Layer 2. Retries once on JSON parse failure."""
        for attempt in range(2):
            raw = self._call(DEEP_MODEL, _RISK_SYSTEM,
                             _RISK_USER.format(context=context), max_tokens=4096)
            try:
                d = json.loads(_strip_code_fence(raw))
                break
            except json.JSONDecodeError:
                if attempt == 1:
                    raise
                # 第一次失败：加一条提示重新生成
                context = context + "\n\n[注意：上次输出的JSON格式有误，请重新输出合法JSON，不要包含任何注释或特殊字符]"

        risks = [
            Risk(
                severity=r.get("severity", "LOW"),
                category=r.get("category", "MAINTAINABILITY"),
                file=r.get("file", "unknown"),
                line=r.get("line"),
                title=r.get("title", ""),
                description=r.get("description", ""),
                why_it_matters=r.get("why_it_matters", ""),
                ai_trap=r.get("ai_trap"),
                suggestion=r.get("suggestion", ""),
                suggestion_code=r.get("suggestion_code"),
            )
            for r in d.get("risks", [])
        ]
        return {
            "risks": risks,
            "verdict": d.get("verdict", "COMMENT"),
            "overall_score": d.get("overall_score", 5),
            "quick_wins": d.get("quick_wins", []),
        }


def _strip_code_fence(text: str) -> str:
    """Remove ```json ... ``` wrappers if present."""
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return text.strip()
