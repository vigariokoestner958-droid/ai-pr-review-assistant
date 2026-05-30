"""Format analysis results for GitHub comments and CLI output."""
import os
from analyzer import AnalysisResult, Risk
from github_client import PRData

SEVERITY_EMOJI = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
VERDICT_EMOJI  = {"APPROVE": "✅", "REQUEST_CHANGES": "🚫", "COMMENT": "💬"}
VERDICT_TEXT   = {
    "APPROVE": "建议合并",
    "REQUEST_CHANGES": "请修复后再合并",
    "COMMENT": "供参考，最终由你决定",
}


# ── GitHub Markdown comment ───────────────────────────────────────────────────

def to_github_comment(pr: PRData, result: AnalysisResult) -> str:
    if result.skipped:
        return _skipped_comment(pr, result.skip_reason)

    parts = [
        _header(pr, result),
        _summary_section(result),
        _risks_section(result),
        _footer(result, pr.url),
    ]
    return "\n\n".join(p for p in parts if p)


def _header(pr: PRData, result: AnalysisResult) -> str:
    verdict_e = VERDICT_EMOJI[result.verdict]
    verdict_t = VERDICT_TEXT[result.verdict]
    score = result.overall_score
    score_bar = "█" * score + "░" * (10 - score)
    return (
        f"## 🤖 AI PR Review\n\n"
        f"**{verdict_e} {verdict_t}** &nbsp;|&nbsp; "
        f"质量评分：`{score_bar}` {score}/10\n\n"
        f"---"
    )


def _summary_section(result: AnalysisResult) -> str:
    s = result.summary
    if not s.what_changed:
        return ""
    modules = "、".join(s.affected_modules) if s.affected_modules else "—"
    change_type_map = {
        "feature": "新功能", "bugfix": "Bug 修复",
        "refactor": "重构", "dependency": "依赖升级", "other": "其他",
    }
    ctype = change_type_map.get(s.change_type, s.change_type)
    return (
        f"### 📋 变更摘要\n\n"
        f"| 维度 | 内容 |\n"
        f"|------|------|\n"
        f"| 变更类型 | {ctype} |\n"
        f"| 核心改动 | {s.core_change} |\n"
        f"| 影响模块 | {modules} |\n"
        f"| 一句话 | {s.what_changed} |"
    )


def _risks_section(result: AnalysisResult) -> str:
    if not result.risks:
        return "### ✅ 风险扫描\n\n未发现明显风险，代码看起来不错！"

    # Group by severity
    by_sev: dict[str, list[Risk]] = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for r in result.risks:
        by_sev.setdefault(r.severity, []).append(r)

    lines = ["### ⚠️ 风险评估\n"]
    for sev in ["HIGH", "MEDIUM", "LOW"]:
        risks = by_sev[sev]
        if not risks:
            continue
        emoji = SEVERITY_EMOJI[sev]
        lines.append(f"#### {emoji} {sev}（{len(risks)} 项）\n")
        for r in risks:
            lines.append(_risk_block(r))

    if result.quick_wins:
        lines.append("### 💡 快速改进\n")
        for qw in result.quick_wins:
            lines.append(f"- {qw}")

    return "\n".join(lines)


def _risk_block(r: Risk) -> str:
    loc = f"`{r.file}`" + (f":{r.line}" if r.line else "")
    parts = [
        f"**[{r.category}]** {loc} — {r.title}\n",
        f"{r.description}\n",
    ]
    if r.why_it_matters:
        parts.append(f"> 📚 **为什么是问题：** {r.why_it_matters}\n")
    if r.ai_trap:
        parts.append(f"> ⚡ **AI 代码陷阱：** {r.ai_trap}\n")
    if r.suggestion_code:
        parts.append(f"```suggestion\n{r.suggestion_code}\n```\n")
    elif r.suggestion:
        parts.append(f"💡 **修复建议：** {r.suggestion}\n")
    parts.append("---")
    return "\n".join(parts)


FEEDBACK_BASE_URL = os.getenv("FEEDBACK_BASE_URL", "http://localhost:8000")


def _footer(result: AnalysisResult, pr_url: str = "") -> str:
    high_count = sum(1 for r in result.risks if r.severity == "HIGH")
    med_count  = sum(1 for r in result.risks if r.severity == "MEDIUM")
    low_count  = sum(1 for r in result.risks if r.severity == "LOW")
    from urllib.parse import quote
    encoded = quote(pr_url, safe="")
    up_url   = f"{FEEDBACK_BASE_URL}/feedback?pr={encoded}&vote=up"
    down_url = f"{FEEDBACK_BASE_URL}/feedback?pr={encoded}&vote=down"
    return (
        f"<details><summary>📊 统计</summary>\n\n"
        f"🔴 HIGH: {high_count} &nbsp; 🟡 MEDIUM: {med_count} &nbsp; 🟢 LOW: {low_count}\n\n"
        f"</details>\n\n"
        f"*由 AI PR Review 助手生成 · "
        f"[👍 有帮助]({up_url}) · [👎 不准确]({down_url})*"
    )


def _skipped_comment(pr: PRData, reason: str) -> str:
    return (
        f"## 🤖 AI PR Review\n\n"
        f"⚠️ **无法分析此 PR**\n\n"
        f"{reason}\n\n"
        f"**建议：** 将此 PR 拆分为多个更小的 PR（每个聚焦一个功能点），"
        f"这也符合 Vibe Coding 「小步快跑」的最佳实践。"
    )


# ── CLI rich output ───────────────────────────────────────────────────────────

def print_cli(pr: PRData, result: AnalysisResult):
    """Print a rich summary to the terminal."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich import box
        console = Console()
    except ImportError:
        print(to_github_comment(pr, result))
        return

    console.print(f"\n[bold cyan]🤖 AI PR Review[/bold cyan] — {pr.title}")
    console.print(f"[dim]{pr.url}[/dim]\n")

    if result.skipped:
        console.print(Panel(result.skip_reason, title="⚠️ 跳过分析", border_style="yellow"))
        return

    # Summary
    s = result.summary
    if s.what_changed:
        t = Table(box=box.SIMPLE, show_header=False)
        t.add_column(style="dim")
        t.add_column()
        t.add_row("变更类型", s.change_type)
        t.add_row("核心改动", s.core_change)
        t.add_row("影响模块", "、".join(s.affected_modules) or "—")
        console.print(Panel(t, title="📋 变更摘要", border_style="blue"))

    # Risks
    if not result.risks:
        console.print(Panel("✅ 未发现明显风险", border_style="green"))
    else:
        sev_color = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}
        for r in result.risks:
            color = sev_color.get(r.severity, "white")
            loc = f"{r.file}:{r.line}" if r.line else r.file
            body = f"[dim]{loc}[/dim]\n{r.description}"
            if r.why_it_matters:
                body += f"\n[dim italic]{r.why_it_matters}[/dim italic]"
            console.print(Panel(
                body,
                title=f"[{color}]{SEVERITY_EMOJI[r.severity]} {r.severity}[/{color}] {r.title}",
                border_style=color,
            ))

    # Verdict
    verdict_color = {"APPROVE": "green", "REQUEST_CHANGES": "red", "COMMENT": "yellow"}
    color = verdict_color.get(result.verdict, "white")
    console.print(
        f"\n[{color} bold]{VERDICT_EMOJI[result.verdict]} {VERDICT_TEXT[result.verdict]}[/{color} bold] "
        f"[dim]（质量评分 {result.overall_score}/10）[/dim]\n"
    )
