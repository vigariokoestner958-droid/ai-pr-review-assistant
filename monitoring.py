"""
评估与监控模块

负责：
1. 记录每次 /analyze 调用的指标到 SQLite
2. 查询聚合数据（趋势、分布、告警状态）
3. 定义告警阈值，判断各指标是否异常

表结构：
  analyses  — 每次分析的指标记录
  feedback  — 用户 👍/👎 反馈（原有）
"""

import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

CST = timezone(timedelta(hours=8))   # 北京时间 UTC+8

def _now_cst() -> str:
    return datetime.now(CST).strftime('%Y-%m-%dT%H:%M:%S')

def _since_cst(days: int) -> str:
    return (datetime.now(CST) - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%S')
from dataclasses import dataclass
from typing import Optional

DB_PATH = Path(__file__).parent / "feedback.db"

# ── 告警阈值 ──────────────────────────────────────────────────────
THRESHOLDS = {
    # 延迟
    "latency_p90_ms":        {"warn": 30_000, "crit": 60_000},
    # 错误率（最近100次中的比例）
    "error_rate_pct":        {"warn": 5.0,    "crit": 15.0},
    # 有帮助率（越高越好，低于阈值告警）
    "helpful_rate_pct":      {"warn": 60.0,   "crit": 40.0},   # 低于此值告警
    # 误报率（HIGH风险被👎的比例）
    "false_positive_pct":    {"warn": 20.0,   "crit": 35.0},
    # 平均评分异常（低于此值说明模型过于严苛）
    "avg_score_low":         {"warn": 3.0,    "crit": 2.0},
    # 平均评分异常（高于此值说明模型过于宽松）
    "avg_score_high":        {"warn": 8.5,    "crit": 9.5},
    # 每日分析量骤降（低于历史均值的百分比）
    "daily_volume_drop_pct": {"warn": 50.0,   "crit": 80.0},
}


# ── 初始化数据库 ──────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            pr_url        TEXT NOT NULL,
            pr_title      TEXT,
            verdict       TEXT,
            overall_score INTEGER,
            high_count    INTEGER DEFAULT 0,
            med_count     INTEGER DEFAULT 0,
            low_count     INTEGER DEFAULT 0,
            latency_ms    INTEGER,
            skipped       INTEGER DEFAULT 0,
            error         TEXT DEFAULT '',
            created_at    TEXT NOT NULL
        )
    """)
    # feedback 表原有，确保字段完整
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


# ── 写入指标 ──────────────────────────────────────────────────────

def record_analysis(
    pr_url: str,
    pr_title: str,
    verdict: str,
    overall_score: int,
    high_count: int,
    med_count: int,
    low_count: int,
    latency_ms: int,
    skipped: bool = False,
    error: str = "",
):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO analyses
           (pr_url, pr_title, verdict, overall_score,
            high_count, med_count, low_count, latency_ms,
            skipped, error, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            pr_url, pr_title, verdict, overall_score,
            high_count, med_count, low_count, latency_ms,
            int(skipped), error,
            _now_cst(),
        ),
    )
    conn.commit()
    conn.close()


# ── 查询聚合 ──────────────────────────────────────────────────────

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_summary(days: int = 7) -> dict:
    """返回最近N天的汇总指标。"""
    since = _since_cst(days)
    conn = _conn()

    total_row = conn.execute(
        "SELECT COUNT(*) as n FROM analyses WHERE created_at >= ?", (since,)
    ).fetchone()
    total = total_row["n"] or 0

    if total == 0:
        conn.close()
        return {"total": 0, "days": days}

    stats = conn.execute("""
        SELECT
            AVG(latency_ms)    as avg_latency,
            MAX(latency_ms)    as max_latency,
            AVG(overall_score) as avg_score,
            SUM(CASE WHEN error != '' THEN 1 ELSE 0 END) as error_count,
            SUM(CASE WHEN skipped = 1 THEN 1 ELSE 0 END) as skip_count,
            SUM(CASE WHEN verdict = 'APPROVE' THEN 1 ELSE 0 END) as approve_count,
            SUM(CASE WHEN verdict = 'REQUEST_CHANGES' THEN 1 ELSE 0 END) as reject_count,
            SUM(CASE WHEN verdict = 'COMMENT' THEN 1 ELSE 0 END) as comment_count,
            AVG(high_count) as avg_high,
            AVG(med_count)  as avg_med,
            AVG(low_count)  as avg_low
        FROM analyses WHERE created_at >= ?
    """, (since,)).fetchone()

    # 反馈数据
    fb = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN vote='up' THEN 1 ELSE 0 END) as up_count
        FROM feedback WHERE created_at >= ?
    """, (since,)).fetchone()

    # P90 延迟
    latencies = [
        r[0] for r in conn.execute(
            "SELECT latency_ms FROM analyses WHERE created_at >= ? AND error = '' ORDER BY latency_ms",
            (since,)
        ).fetchall()
    ]
    p90 = latencies[int(len(latencies) * 0.9)] if latencies else 0

    conn.close()

    fb_total = fb["total"] or 0
    fb_up    = fb["up_count"] or 0
    helpful_rate = round(fb_up / fb_total * 100, 1) if fb_total > 0 else None
    error_count  = stats["error_count"] or 0
    error_rate   = round(error_count / total * 100, 1)

    return {
        "days": days,
        "total": total,
        "error_count": error_count,
        "error_rate_pct": error_rate,
        "skip_count": stats["skip_count"] or 0,
        "avg_latency_ms": round(stats["avg_latency"] or 0),
        "max_latency_ms": stats["max_latency"] or 0,
        "p90_latency_ms": p90,
        "avg_score": round(stats["avg_score"] or 0, 1),
        "verdict_approve": stats["approve_count"] or 0,
        "verdict_reject":  stats["reject_count"] or 0,
        "verdict_comment": stats["comment_count"] or 0,
        "avg_high": round(stats["avg_high"] or 0, 1),
        "avg_med":  round(stats["avg_med"] or 0, 1),
        "avg_low":  round(stats["avg_low"] or 0, 1),
        "feedback_total": fb_total,
        "feedback_up":    fb_up,
        "helpful_rate_pct": helpful_rate,
    }


def get_daily_trend(days: int = 14) -> list[dict]:
    """返回最近N天每天的分析量和平均延迟。"""
    conn = _conn()
    rows = conn.execute("""
        SELECT
            substr(created_at, 1, 10) as day,
            COUNT(*) as total,
            SUM(CASE WHEN error != '' THEN 1 ELSE 0 END) as errors,
            AVG(latency_ms) as avg_latency,
            AVG(overall_score) as avg_score
        FROM analyses
        WHERE created_at >= ?
        GROUP BY day
        ORDER BY day
    """, (_since_cst(days),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_score_distribution() -> dict:
    """返回评分 1-10 的分布。"""
    conn = _conn()
    rows = conn.execute("""
        SELECT overall_score, COUNT(*) as cnt
        FROM analyses
        WHERE error = '' AND skipped = 0
        GROUP BY overall_score
        ORDER BY overall_score
    """).fetchall()
    conn.close()
    dist = {i: 0 for i in range(1, 11)}
    for r in rows:
        if r[0]:
            dist[r[0]] = r[1]
    return dist


def get_recent_analyses(limit: int = 20) -> list[dict]:
    """返回最近N条分析记录。"""
    conn = _conn()
    rows = conn.execute("""
        SELECT pr_url, pr_title, verdict, overall_score,
               high_count, med_count, low_count, latency_ms,
               error, created_at
        FROM analyses
        ORDER BY id DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── 告警判断 ──────────────────────────────────────────────────────

@dataclass
class Alert:
    metric: str
    level: str      # "ok" / "warn" / "crit"
    value: float
    threshold: float
    message: str


def check_alerts(summary: dict) -> list[Alert]:
    """根据当前指标和阈值生成告警列表。"""
    alerts = []

    def _check(metric: str, value, higher_is_worse: bool = True):
        if value is None:
            return
        t = THRESHOLDS.get(metric)
        if not t:
            return
        if higher_is_worse:
            if value >= t["crit"]:
                lvl = "crit"
            elif value >= t["warn"]:
                lvl = "warn"
            else:
                lvl = "ok"
        else:
            # 越低越危险（如 helpful_rate）
            if value <= t["crit"]:
                lvl = "crit"
            elif value <= t["warn"]:
                lvl = "warn"
            else:
                lvl = "ok"
        threshold = t["crit"] if lvl == "crit" else t["warn"]
        alerts.append(Alert(metric=metric, level=lvl, value=value,
                            threshold=threshold, message=_alert_msg(metric, lvl, value)))

    _check("latency_p90_ms",     summary.get("p90_latency_ms", 0))
    _check("error_rate_pct",     summary.get("error_rate_pct", 0))
    _check("helpful_rate_pct",   summary.get("helpful_rate_pct", 100), higher_is_worse=False)
    _check("avg_score_low",      summary.get("avg_score", 5), higher_is_worse=False)
    _check("avg_score_high",     summary.get("avg_score", 5))

    return alerts


def _alert_msg(metric: str, level: str, value: float) -> str:
    msgs = {
        "latency_p90_ms":    f"P90 延迟 {value:.0f}ms，响应速度{'严重' if level=='crit' else ''}过慢",
        "error_rate_pct":    f"错误率 {value:.1f}%，{'严重' if level=='crit' else ''}偏高，请排查日志",
        "helpful_rate_pct":  f"有帮助率 {value:.1f}%，{'严重' if level=='crit' else ''}低于目标 70%",
        "avg_score_low":     f"平均评分 {value:.1f}，AI 可能{'严重' if level=='crit' else ''}过于严苛",
        "avg_score_high":    f"平均评分 {value:.1f}，AI 可能{'严重' if level=='crit' else ''}过于宽松（误报风险）",
    }
    return msgs.get(metric, f"{metric} = {value}")
