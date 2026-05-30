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
    high = sum(1 for r in result.risks if r.severity == "HIGH")
    med  = sum(1 for r in result.risks if r.severity == "MEDIUM")
    low  = sum(1 for r in result.risks if r.severity == "LOW")
    risk_summary = f"🔴×{high} 🟡×{med} 🟢×{low}" if result.risks else "✅ 无风险"
    return (
        f"## X-Reviewer &nbsp; {verdict_e} {verdict_t} &nbsp; `{score}/10`\n\n"
        f"{risk_summary}"
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
    return f"> **{ctype}** `{modules}` — {s.core_change}"


def _risks_section(result: AnalysisResult) -> str:
    if not result.risks:
        return "---\n\n✅ 未发现明显风险。"

    by_sev: dict[str, list[Risk]] = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for r in result.risks:
        by_sev.setdefault(r.severity, []).append(r)

    lines = ["---"]
    for sev in ["HIGH", "MEDIUM", "LOW"]:
        risks = by_sev[sev]
        if not risks:
            continue
        emoji = SEVERITY_EMOJI[sev]
        lines.append(f"\n**{emoji} {sev}（{len(risks)}）**\n")
        for r in risks:
            lines.append(_risk_block(r))

    if result.quick_wins:
        lines.append("\n---\n")
        lines.append("**待处理：** " + " · ".join(result.quick_wins))

    return "\n".join(lines)


def _risk_block(r: Risk) -> str:
    loc = f"`{r.file}:{r.line}`" if r.line else f"`{r.file}`"
    # 合并描述和影响为一句话，去掉AI腔
    detail = r.description
    if r.why_it_matters:
        # 只取第一句，避免啰嗦
        first = r.why_it_matters.split("。")[0].strip().rstrip("，")
        if first and first not in detail:
            detail = f"{detail}（{first}）"
    lines = [f"- {loc} **{r.title}** — {detail}"]
    if r.suggestion_code:
        lines.append(f"\n```suggestion\n{r.suggestion_code}\n```")
    elif r.suggestion:
        lines.append(f"\n  > 修复：{r.suggestion}")
    return "\n".join(lines)


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
        f"*由 X-Reviewer 生成 · "
        f"[👍 有帮助]({up_url}) · [👎 不准确]({down_url})*"
    )


def _skipped_comment(pr: PRData, reason: str) -> str:
    return (
        f"## 🤖 X-Reviewer\n\n"
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

    console.print(f"\n[bold cyan]🤖 X-Reviewer[/bold cyan] — {pr.title}")
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
