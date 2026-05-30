"""
调优数据库

存储每次 eval 运行的详细结果，支持跨运行对比、趋势分析、Prompt 建议生成。

表结构：
  eval_runs     — 每次运行的元数据
  eval_records  — 每个用例在每次运行中的详细结果
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "tuning.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS eval_runs (
            run_id      TEXT PRIMARY KEY,
            total       INTEGER,
            passed      INTEGER,
            accuracy    REAL,
            false_pos   INTEGER,
            false_neg   INTEGER,
            avg_latency INTEGER,
            prompt_version TEXT DEFAULT 'default',
            notes       TEXT DEFAULT '',
            created_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS eval_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id          TEXT NOT NULL,
            case_id         TEXT NOT NULL,
            case_name       TEXT,
            difficulty      TEXT,
            category        TEXT,
            language        TEXT,
            expected_high   INTEGER,
            actual_high     INTEGER,
            actual_med      INTEGER,
            actual_low      INTEGER,
            actual_score    INTEGER,
            actual_verdict  TEXT,
            passed          INTEGER,
            error_type      TEXT,  -- correct/false_positive/false_negative/json_error
            latency_ms      INTEGER,
            error_msg       TEXT DEFAULT '',
            matched_keywords TEXT DEFAULT '',
            created_at      TEXT,
            FOREIGN KEY (run_id) REFERENCES eval_runs(run_id)
        );

        CREATE INDEX IF NOT EXISTS idx_records_case ON eval_records(case_id);
        CREATE INDEX IF NOT EXISTS idx_records_run  ON eval_records(run_id);
        CREATE INDEX IF NOT EXISTS idx_records_type ON eval_records(error_type);
    """)
    conn.commit()
    conn.close()


def save_run(run_id: str, results: list, notes: str = "", prompt_version: str = "default"):
    """将一次完整 eval 的结果写入数据库。results 是 CaseResult dataclass 列表。"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    now = datetime.utcnow().isoformat()

    total  = len(results)
    passed = sum(1 for r in results if r.passed)
    fp     = sum(1 for r in results if not r.expected_high and r.actual_high_count > 0 and not r.error)
    fn     = sum(1 for r in results if r.expected_high and r.actual_high_count == 0 and not r.error)
    avg_lat = int(sum(r.latency_ms for r in results) / total) if total else 0
    accuracy = round(passed / total * 100, 2) if total else 0

    conn.execute("""
        INSERT OR REPLACE INTO eval_runs
        (run_id, total, passed, accuracy, false_pos, false_neg, avg_latency,
         prompt_version, notes, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (run_id, total, passed, accuracy, fp, fn, avg_lat, prompt_version, notes, now))

    for r in results:
        if r.error:
            etype = "json_error"
        elif r.passed:
            etype = "correct"
        elif r.expected_high and r.actual_high_count == 0:
            etype = "false_negative"
        else:
            etype = "false_positive"

        conn.execute("""
            INSERT INTO eval_records
            (run_id, case_id, case_name, difficulty, category, language,
             expected_high, actual_high, actual_med, actual_low,
             actual_score, actual_verdict, passed, error_type,
             latency_ms, error_msg, matched_keywords, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            run_id, r.id, r.name, r.difficulty, r.category, "",
            int(r.expected_high),
            r.actual_high_count, r.actual_med_count, r.actual_low_count,
            r.actual_score, r.actual_verdict,
            int(r.passed), etype,
            r.latency_ms, r.error or "",
            json.dumps(r.matched_keywords, ensure_ascii=False),
            now,
        ))

    conn.commit()
    conn.close()
    return run_id


def load_from_json(json_path: str, notes: str = "", prompt_version: str = "default"):
    """从已有的 eval JSON 结果文件导入数据库（用于历史数据回填）。"""
    from dataclasses import dataclass
    from typing import Optional

    @dataclass
    class FakeResult:
        id: str
        name: str
        difficulty: str
        category: str
        expected_high: bool
        actual_high_count: int
        actual_med_count: int
        actual_low_count: int
        actual_score: int
        actual_verdict: str
        passed: bool
        latency_ms: int
        error: str = ""
        matched_keywords: list = None

        def __post_init__(self):
            if self.matched_keywords is None:
                self.matched_keywords = []

    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    run_id = data["timestamp"]

    results = [
        FakeResult(
            id=r["id"], name=r["name"],
            difficulty=r["difficulty"], category=r["category"],
            expected_high=bool(r["expected_high"]),
            actual_high_count=r["actual_high_count"],
            actual_med_count=r["actual_med_count"],
            actual_low_count=r["actual_low_count"],
            actual_score=r["actual_score"],
            actual_verdict=r["actual_verdict"],
            passed=bool(r["passed"]),
            latency_ms=r["latency_ms"],
            error=r.get("error", ""),
            matched_keywords=r.get("matched_keywords", []),
        )
        for r in data["results"]
    ]

    save_run(run_id, results, notes=notes, prompt_version=prompt_version)
    print(f"[import] {run_id}: {data['passed']}/{data['total']} = {data['accuracy']}%")
    return run_id


def get_runs() -> list[dict]:
    """返回所有运行记录，按时间倒序。"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM eval_runs ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_records(run_id: str = None, error_type: str = None) -> list[dict]:
    """查询详细记录，可按 run_id 或 error_type 过滤。"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    where, params = [], []
    if run_id:
        where.append("run_id = ?"); params.append(run_id)
    if error_type:
        where.append("error_type = ?"); params.append(error_type)
    sql = "SELECT * FROM eval_records"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY run_id DESC, case_id"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    # 一键导入所有已有的 eval JSON 文件
    results_dir = Path(__file__).parent.parent / "eval" / "results"
    for f in sorted(results_dir.glob("eval_*.json")):
        ts = f.stem.replace("eval_", "")
        version = "pre-fix" if ts < "20260530_161000" else "post-fix"
        load_from_json(str(f), prompt_version=version)
    print("全部历史数据导入完成")
