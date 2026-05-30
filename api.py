"""FastAPI backend — serves web UI and exposes POST /analyze."""
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="AI PR Review API", version="1.0.0")

# ── Feedback DB ───────────────────────────────────────────────────────────────

DB_PATH = Path(__file__).parent / "feedback.db"

def _init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            pr_url    TEXT NOT NULL,
            vote      TEXT NOT NULL CHECK(vote IN ('up','down')),
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

_init_db()


# ── Request / Response schemas ────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    pr_url: str
    post_comment: bool = False


class RiskOut(BaseModel):
    severity: str
    category: str
    file: str
    line: int | None
    title: str
    description: str
    why_it_matters: str
    ai_trap: str | None
    suggestion: str
    suggestion_code: str | None


class AnalyzeResponse(BaseModel):
    pr_title: str
    pr_url: str
    summary_what_changed: str
    summary_change_type: str
    summary_core_change: str
    affected_modules: list[str]
    risks: list[RiskOut]
    verdict: str
    overall_score: int
    quick_wins: list[str]
    skipped: bool
    skip_reason: str
    github_comment: str
    comment_url: str | None


# ── Analyze endpoint ──────────────────────────────────────────────────────────

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    github_token  = os.getenv("GITHUB_TOKEN")

    if not anthropic_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY not configured")
    if not github_token:
        raise HTTPException(500, "GITHUB_TOKEN not configured")

    from github_client import GitHubClient
    from analyzer import Analyzer
    from formatter import to_github_comment

    gh = GitHubClient(github_token)
    try:
        owner, repo, number = gh.parse_pr_url(req.pr_url)
    except ValueError as e:
        raise HTTPException(400, str(e))

    try:
        pr = gh.get_pr(owner, repo, number)
    except Exception as e:
        raise HTTPException(502, f"GitHub API error: {e}")

    try:
        result = Analyzer(anthropic_key).analyze(pr)
    except Exception as e:
        raise HTTPException(502, f"AI analysis error: {e}")

    comment_body = to_github_comment(pr, result)
    comment_url = None

    if req.post_comment and not result.skipped:
        try:
            comment_url = gh.post_comment(owner, repo, number, comment_body)
        except Exception as e:
            raise HTTPException(502, f"Failed to post GitHub comment: {e}")

    return AnalyzeResponse(
        pr_title=pr.title,
        pr_url=pr.url,
        summary_what_changed=result.summary.what_changed,
        summary_change_type=result.summary.change_type,
        summary_core_change=result.summary.core_change,
        affected_modules=result.summary.affected_modules,
        risks=[RiskOut(
            severity=r.severity, category=r.category, file=r.file, line=r.line,
            title=r.title, description=r.description, why_it_matters=r.why_it_matters,
            ai_trap=r.ai_trap, suggestion=r.suggestion, suggestion_code=r.suggestion_code,
        ) for r in result.risks],
        verdict=result.verdict,
        overall_score=result.overall_score,
        quick_wins=result.quick_wins,
        skipped=result.skipped,
        skip_reason=result.skip_reason,
        github_comment=comment_body,
        comment_url=comment_url,
    )


# ── Feedback endpoint ─────────────────────────────────────────────────────────

@app.get("/feedback")
def feedback(
    pr: str = Query(..., description="GitHub PR URL"),
    vote: str = Query(..., description="up or down"),
):
    if vote not in ("up", "down"):
        raise HTTPException(400, "vote must be 'up' or 'down'")
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO feedback (pr_url, vote, created_at) VALUES (?, ?, ?)",
        (pr, vote, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    emoji = "👍" if vote == "up" else "👎"
    return HTMLResponse(f"""
    <html><head><meta charset="utf-8">
    <style>body{{font-family:sans-serif;text-align:center;padding:60px;background:#0d1117;color:#e6edf3}}</style>
    </head><body>
    <div style="font-size:48px">{emoji}</div>
    <h2 style="margin-top:16px">{"感谢反馈！" if vote=="up" else "已记录，我们会持续改进"}</h2>
    <p style="color:#8b949e">你的反馈帮助我们提升 AI 分析准确率</p>
    <p style="margin-top:24px"><a href="{pr}" style="color:#58a6ff">← 返回 PR</a></p>
    </body></html>
    """)


# ── Stats endpoint ─────────────────────────────────────────────────────────────

@app.get("/stats")
def stats():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN vote='up' THEN 1 ELSE 0 END) as up_count,
            SUM(CASE WHEN vote='down' THEN 1 ELSE 0 END) as down_count
        FROM feedback
    """).fetchone()
    recent = conn.execute(
        "SELECT pr_url, vote, created_at FROM feedback ORDER BY id DESC LIMIT 20"
    ).fetchall()
    conn.close()

    total, up, down = rows
    up = up or 0
    down = down or 0
    rate = round(up / total * 100) if total else 0

    rows_html = "".join(
        f"<tr><td style='max-width:400px;overflow:hidden;text-overflow:ellipsis'>"
        f"<a href='{r[0]}' style='color:#58a6ff'>{r[0]}</a></td>"
        f"<td>{'👍' if r[1]=='up' else '👎'}</td>"
        f"<td style='color:#8b949e'>{r[2][:19]}</td></tr>"
        for r in recent
    )
    bar_filled = int(rate / 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    return HTMLResponse(f"""
    <html><head><meta charset="utf-8">
    <style>
      body{{font-family:sans-serif;background:#0d1117;color:#e6edf3;padding:40px;max-width:800px;margin:0 auto}}
      h1{{font-size:20px;margin-bottom:24px}} .card{{background:#161b22;border:1px solid #30363d;
      border-radius:8px;padding:20px;margin-bottom:20px}} .big{{font-size:48px;font-weight:700;color:#3fb950}}
      table{{width:100%;border-collapse:collapse;font-size:13px}}
      td{{padding:8px 12px;border-bottom:1px solid #21262d;vertical-align:top}}
    </style></head><body>
    <h1>📊 AI PR Review — 准确率统计</h1>
    <div class="card">
      <div class="big">{rate}%</div>
      <div style="font-family:monospace;margin:8px 0;color:#58a6ff">{bar}</div>
      <div style="color:#8b949e">有帮助率（目标 >70%）</div>
      <div style="margin-top:16px;display:flex;gap:32px">
        <div>👍 有帮助 <strong>{up}</strong></div>
        <div>👎 不准确 <strong>{down}</strong></div>
        <div>总计 <strong>{total}</strong></div>
      </div>
    </div>
    <div class="card">
      <div style="font-size:14px;margin-bottom:12px;color:#8b949e">最近 20 条反馈</div>
      <table><tr style="color:#8b949e"><td>PR</td><td>反馈</td><td>时间</td></tr>
      {rows_html if rows_html else "<tr><td colspan='3' style='color:#8b949e'>暂无数据</td></tr>"}
      </table>
    </div>
    </body></html>
    """)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Serve frontend ────────────────────────────────────────────────────────────

frontend_dir = Path(__file__).parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def root():
        return FileResponse(str(frontend_dir / "index.html"))
