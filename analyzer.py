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
你是专注 Vibe Coding 场景的代码审查专家。

规则：
1. 只报告有具体代码证据的问题，不做推测性建议
2. 每条风险必须有文件名和行号（如无法确定行号，写 null）
3. HIGH/MEDIUM 风险必须附教育性解释（≤3句，口语化，解释"为什么"）
4. 如果该问题是 AI 生成代码的惯性陷阱，在 ai_trap 字段注明
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
        """Fast summary — Layer 1."""
        raw = self._call(FAST_MODEL, _SUMMARY_SYSTEM,
                         _SUMMARY_USER.format(context=context), max_tokens=512)
        d = json.loads(_strip_code_fence(raw))
        return Summary(
            what_changed=d.get("what_changed", ""),
            change_type=d.get("change_type", "other"),
            core_change=d.get("core_change", ""),
            affected_modules=d.get("affected_modules", []),
        )

    def _layer2_risks(self, context: str) -> dict:
        """Deep risk analysis — Layer 2."""
        raw = self._call(DEEP_MODEL, _RISK_SYSTEM,
                         _RISK_USER.format(context=context), max_tokens=4096)
        d = json.loads(_strip_code_fence(raw))

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
