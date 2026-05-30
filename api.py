"""FastAPI backend — serves web UI and exposes POST /analyze."""
import os
import time
import sqlite3
from datetime import datetime, timedelta, timezone
CST = timezone(timedelta(hours=8))
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

load_dotenv()

from monitoring import init_db, record_analysis, get_summary, get_daily_trend, \
    get_score_distribution, get_recent_analyses, check_alerts

init_db()

app = FastAPI(title="X-Reviewer API", version="1.0.0")

DB_PATH = Path(__file__).parent / "feedback.db"


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

    t0 = time.time()
    error_msg = ""
    result = None

    try:
        result = Analyzer(anthropic_key).analyze(pr)
    except Exception as e:
        error_msg = str(e)
        record_analysis(
            pr_url=req.pr_url, pr_title=getattr(pr, "title", ""),
            verdict="ERROR", overall_score=0,
            high_count=0, med_count=0, low_count=0,
            latency_ms=int((time.time() - t0) * 1000),
            error=error_msg,
        )
        raise HTTPException(502, f"AI analysis error: {e}")

    latency_ms = int((time.time() - t0) * 1000)
    high = sum(1 for r in result.risks if r.severity == "HIGH")
    med  = sum(1 for r in result.risks if r.severity == "MEDIUM")
    low  = sum(1 for r in result.risks if r.severity == "LOW")

    record_analysis(
        pr_url=req.pr_url, pr_title=pr.title,
        verdict=result.verdict, overall_score=result.overall_score,
        high_count=high, med_count=med, low_count=low,
        latency_ms=latency_ms, skipped=result.skipped,
    )

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

class FeedbackRequest(BaseModel):
    pr_url: str
    vote: str
    comment: str = ""

@app.post("/feedback")
def feedback(req: FeedbackRequest):
    if req.vote not in ("up", "down"):
        raise HTTPException(400, "vote must be 'up' or 'down'")
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO feedback (pr_url, vote, created_at) VALUES (?, ?, ?)",
        (req.pr_url, req.vote, datetime.now(CST).strftime('%Y-%m-%dT%H:%M:%S')),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "vote": req.vote}

@app.get("/feedback")
def feedback_get(
    pr: str = Query(..., description="GitHub PR URL"),
    vote: str = Query(..., description="up or down"),
):
    if vote not in ("up", "down"):
        raise HTTPException(400, "vote must be 'up' or 'down'")
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO feedback (pr_url, vote, created_at) VALUES (?, ?, ?)",
        (pr, vote, datetime.now(CST).strftime('%Y-%m-%dT%H:%M:%S')),
    )
    conn.commit()
    conn.close()
    emoji = "👍" if vote == "up" else "👎"
    return HTMLResponse(f"""
    <html><head><meta charset="utf-8">
    <style>body{{font-family:sans-serif;text-align:center;padding:60px;background:#F5F0E8;color:#3C1518}}</style>
    </head><body>
    <div style="font-size:48px">{emoji}</div>
    <h2 style="margin-top:16px;font-family:Georgia,serif">{"感谢反馈！" if vote=="up" else "已记录，我们会持续改进"}</h2>
    <p style="color:#8B7E74">你的反馈帮助我们提升 AI 分析准确率</p>
    <p style="margin-top:24px"><a href="{pr}" style="color:#A44A3F">← 返回 PR</a></p>
    </body></html>
    """)


# ── Metrics API (JSON) ────────────────────────────────────────────────────────

@app.get("/api/metrics")
def metrics_api(days: int = Query(7, ge=1, le=90)):
    """返回结构化指标数据，供前端图表或外部监控系统使用。"""
    summary = get_summary(days)
    alerts  = check_alerts(summary)
    trend   = get_daily_trend(days)
    scores  = get_score_distribution()
    recent  = get_recent_analyses(limit=15)
    return JSONResponse({
        "summary": summary,
        "alerts": [
            {"metric": a.metric, "level": a.level,
             "value": a.value, "message": a.message}
            for a in alerts
        ],
        "daily_trend": trend,
        "score_distribution": scores,
        "recent": recent,
    })


# ── Stats dashboard ───────────────────────────────────────────────────────────

@app.get("/stats")
def stats():
    summary = get_summary(days=7)
    alerts  = check_alerts(summary)
    trend   = get_daily_trend(days=14)
    scores  = get_score_distribution()
    recent  = get_recent_analyses(limit=15)

    # ── 反馈统计 ──────────────────────────────────────────────────
    conn = sqlite3.connect(DB_PATH)
    fb = conn.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN vote='up' THEN 1 ELSE 0 END) as up_count
        FROM feedback
    """).fetchone()
    conn.close()
    fb_total = fb[0] or 0
    fb_up    = fb[1] or 0
    helpful_rate = round(fb_up / fb_total * 100) if fb_total else 0
    fb_bar = "█" * (helpful_rate // 10) + "░" * (10 - helpful_rate // 10)

    # ── 告警 HTML ─────────────────────────────────────────────────
    alert_level_map = {"ok": "#3D7A4A", "warn": "#B45309", "crit": "#A44A3F"}
    alert_icon_map  = {"ok": "✓", "warn": "!", "crit": "!!"}
    worst = "ok"
    for a in alerts:
        if a.level == "crit":
            worst = "crit"; break
        if a.level == "warn":
            worst = "warn"

    overall_status_color = alert_level_map[worst]
    overall_status_label = {"ok": "正常", "warn": "警告", "crit": "严重"}[worst]

    alerts_html = ""
    for a in alerts:
        if a.level == "ok":
            continue
        color = alert_level_map[a.level]
        icon  = alert_icon_map[a.level]
        alerts_html += f"""
        <div style="border-left:4px solid {color};padding:10px 14px;margin-bottom:8px;
                    background:{'#FDF8F0' if a.level=='warn' else '#FDF6F5'}">
          <span style="color:{color};font-weight:600">[{a.level.upper()}]</span>
          <span style="margin-left:8px;font-size:14px">{a.message}</span>
        </div>"""
    if not alerts_html:
        alerts_html = '<p style="color:#3D7A4A;font-size:14px">✓ 所有指标正常</p>'

    # ── 趋势迷你图（ASCII）─────────────────────────────────────────
    trend_html = ""
    if trend:
        max_v = max(r["total"] for r in trend) or 1
        for r in trend[-7:]:
            h = max(1, int(r["total"] / max_v * 40))
            bar = "█" * h
            err_note = f' <span style="color:#A44A3F">({r["errors"]}err)</span>' if r.get("errors") else ""
            trend_html += f'<div style="font-size:12px;margin-bottom:4px;font-family:monospace">' \
                          f'{r["day"][-5:]} {bar} {r["total"]}{err_note}</div>'

    # ── 评分分布 ──────────────────────────────────────────────────
    total_scored = sum(scores.values()) or 1
    score_dist_html = ""
    for s, cnt in scores.items():
        pct = int(cnt / total_scored * 100)
        color = "#A44A3F" if s <= 3 else "#B45309" if s <= 6 else "#3D7A4A"
        score_dist_html += f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
          <span style="width:20px;font-size:13px;text-align:right">{s}</span>
          <div style="background:{color};height:14px;width:{max(pct,1)}%;min-width:2px"></div>
          <span style="font-size:12px;color:#8B7E74">{cnt}</span>
        </div>"""

    # ── 最近分析记录 ──────────────────────────────────────────────
    verdict_icon = {"APPROVE": "✅", "REQUEST_CHANGES": "🚫", "COMMENT": "💬", "ERROR": "❌"}
    recent_rows = ""
    for r in recent:
        icon = verdict_icon.get(r["verdict"] or "", "—")
        url  = r["pr_url"]
        short = url.split("github.com/")[-1] if "github.com" in url else url
        err_badge = f'<span style="color:#A44A3F;font-size:11px">{r["error"][:30]}</span>' \
                    if r["error"] else ""
        recent_rows += f"""
        <tr>
          <td style="max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
            <a href="{url}" style="color:#A44A3F;font-size:13px">{short}</a>
          </td>
          <td>{icon}</td>
          <td style="font-size:13px">{r['overall_score'] or '—'}/10</td>
          <td style="font-family:monospace;font-size:12px;color:#8B7E74">
            {r['high_count']}H {r['med_count']}M {r['low_count']}L
          </td>
          <td style="font-size:12px;color:#8B7E74">{r['latency_ms'] or 0}ms</td>
          <td style="font-size:12px;color:#8B7E74">{(r['created_at'] or '')[:16]}</td>
          <td>{err_badge}</td>
        </tr>"""

    total_analyses = summary.get("total", 0)

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>X-Reviewer — 监控看板</title>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;500&family=Manrope:wght@400;500&family=JetBrains+Mono&display=swap" rel="stylesheet">
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Manrope',sans-serif;background:#F5F0E8;color:#3C1518;padding:0}}
  nav{{background:#3C1518;padding:0 48px;height:56px;display:flex;align-items:center;justify-content:space-between}}
  .nav-title{{font-family:'EB Garamond',serif;font-size:20px;color:#F5F0E8}}
  .nav-links a{{color:#F5F0E8;font-size:13px;text-decoration:none;margin-left:24px;opacity:.7}}
  .nav-links a:hover{{opacity:1}}
  main{{max-width:1100px;margin:0 auto;padding:40px 24px}}
  h2{{font-family:'EB Garamond',serif;font-size:22px;color:#3C1518;margin-bottom:16px}}
  .grid{{display:grid;gap:20px}}
  .grid-4{{grid-template-columns:repeat(4,1fr)}}
  .grid-2{{grid-template-columns:repeat(2,1fr)}}
  .card{{background:#fff;border:1px solid #D6CFC4;padding:24px}}
  .card:hover{{border-color:#3C1518}}
  .kpi-num{{font-family:'EB Garamond',serif;font-size:42px;line-height:1;color:#3C1518}}
  .kpi-label{{font-size:12px;font-weight:500;letter-spacing:.06em;text-transform:uppercase;color:#8B7E74;margin-top:4px}}
  .status-badge{{display:inline-block;padding:4px 12px;font-size:12px;font-weight:600;
    color:#F5F0E8;background:{overall_status_color}}}
  .section{{margin-top:32px}}
  table{{width:100%;border-collapse:collapse;font-size:13px}}
  td,th{{padding:8px 12px;border-bottom:1px solid #EDE8DE;text-align:left;vertical-align:middle}}
  th{{font-size:11px;font-weight:500;letter-spacing:.06em;text-transform:uppercase;color:#8B7E74}}
  .mono{{font-family:'JetBrains Mono',monospace;font-size:12px}}
  .refresh{{font-size:12px;color:#8B7E74;cursor:pointer;text-decoration:underline}}
</style>
</head><body>
<nav>
  <span class="nav-title">X-Reviewer — 监控看板</span>
  <div class="nav-links">
    <a href="/">← 返回主页</a>
    <a href="/api/metrics" target="_blank">JSON API</a>
    <span class="refresh" onclick="location.reload()">刷新</span>
  </div>
</nav>
<main>

  <!-- 状态总览 -->
  <div style="display:flex;align-items:center;gap:16px;margin-bottom:28px">
    <h2 style="margin:0">系统状态</h2>
    <span class="status-badge">{overall_status_label}</span>
    <span style="font-size:13px;color:#8B7E74">最近 7 天 · {total_analyses} 次分析</span>
  </div>

  <!-- KPI 卡片 -->
  <div class="grid grid-4">
    <div class="card">
      <div class="kpi-num" style="color:{'#3D7A4A' if helpful_rate>=70 else '#B45309' if helpful_rate>=50 else '#A44A3F'}">{helpful_rate}%</div>
      <div class="kpi-label">有帮助率（目标 >70%）</div>
      <div class="mono" style="margin-top:8px;color:#A44A3F">{fb_bar}</div>
      <div style="font-size:12px;color:#8B7E74;margin-top:4px">👍{fb_up} / 👎{fb_total - fb_up} / 总{fb_total}</div>
    </div>
    <div class="card">
      <div class="kpi-num">{summary.get('avg_latency_ms', 0):,}</div>
      <div class="kpi-label">平均延迟（ms）</div>
      <div style="font-size:12px;color:#8B7E74;margin-top:8px">P90: {summary.get('p90_latency_ms', 0):,}ms</div>
      <div style="font-size:12px;color:#8B7E74">最大: {summary.get('max_latency_ms', 0):,}ms</div>
    </div>
    <div class="card">
      <div class="kpi-num" style="color:{'#3D7A4A' if summary.get('error_rate_pct',0)<5 else '#A44A3F'}">{summary.get('error_rate_pct', 0):.1f}%</div>
      <div class="kpi-label">错误率（目标 <5%）</div>
      <div style="font-size:12px;color:#8B7E74;margin-top:8px">错误次数: {summary.get('error_count', 0)}</div>
      <div style="font-size:12px;color:#8B7E74">跳过次数: {summary.get('skip_count', 0)}</div>
    </div>
    <div class="card">
      <div class="kpi-num">{summary.get('avg_score', 0):.1f}</div>
      <div class="kpi-label">平均质量评分（/10）</div>
      <div style="font-size:12px;color:#8B7E74;margin-top:8px">
        ✅{summary.get('verdict_approve',0)} 建议合并
      </div>
      <div style="font-size:12px;color:#8B7E74">
        🚫{summary.get('verdict_reject',0)} 需修复
        &nbsp;💬{summary.get('verdict_comment',0)} 供参考
      </div>
    </div>
  </div>

  <!-- 告警区 -->
  <div class="section">
    <h2>告警状态</h2>
    <div class="card">{alerts_html}</div>
  </div>

  <!-- 趋势 + 评分分布 -->
  <div class="section grid grid-2">
    <div class="card">
      <h2>每日分析量（最近 7 天）</h2>
      {trend_html if trend_html else '<p style="color:#8B7E74;font-size:14px">暂无数据</p>'}
    </div>
    <div class="card">
      <h2>评分分布</h2>
      {score_dist_html if score_dist_html else '<p style="color:#8B7E74;font-size:14px">暂无数据</p>'}
    </div>
  </div>

  <!-- 风险均值 -->
  <div class="section">
    <h2>平均风险分布（每次分析）</h2>
    <div class="grid grid-4" style="grid-template-columns:repeat(3,1fr)">
      <div class="card" style="text-align:center">
        <div class="kpi-num" style="color:#A44A3F">{summary.get('avg_high', 0):.1f}</div>
        <div class="kpi-label">HIGH / 次</div>
      </div>
      <div class="card" style="text-align:center">
        <div class="kpi-num" style="color:#B45309">{summary.get('avg_med', 0):.1f}</div>
        <div class="kpi-label">MEDIUM / 次</div>
      </div>
      <div class="card" style="text-align:center">
        <div class="kpi-num" style="color:#3D7A4A">{summary.get('avg_low', 0):.1f}</div>
        <div class="kpi-label">LOW / 次</div>
      </div>
    </div>
  </div>

  <!-- 最近分析记录 -->
  <div class="section">
    <h2>最近分析记录</h2>
    <div class="card" style="padding:0;overflow:hidden">
      <table>
        <thead><tr>
          <th>PR</th><th>判断</th><th>评分</th><th>风险</th><th>延迟</th><th>时间</th><th></th>
        </tr></thead>
        <tbody>
          {recent_rows if recent_rows else
           '<tr><td colspan="7" style="color:#8B7E74;text-align:center;padding:24px">暂无数据</td></tr>'}
        </tbody>
      </table>
    </div>
  </div>

  <div style="margin-top:32px;font-size:12px;color:#8B7E74;text-align:center">
    数据每次刷新更新 · JSON API: <a href="/api/metrics" style="color:#A44A3F">/api/metrics</a>
  </div>
</main>
</body></html>""")


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

    @app.get("/stats-page")
    def stats_page():
        return FileResponse(str(frontend_dir / "stats.html"))

    @app.get("/api-docs")
    def api_docs_page():
        return FileResponse(str(frontend_dir / "docs.html"))
