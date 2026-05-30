"""
调优分析引擎

读取 tuning.db 中的历史评测数据，输出：
1. 当前准确率快照
2. 持续出错的用例（跨多次运行都失败）
3. 退化检测（之前通过，现在失败）
4. 错误模式聚类
5. 具体的 Prompt 修改建议

运行：
    python -m tuning.analyze
    python -m tuning.analyze --run 20260530_161851   # 分析指定运行
    python -m tuning.analyze --compare               # 对比最近两次运行
"""

import sys
import argparse
from collections import defaultdict, Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tuning.db import get_runs, get_records, init_db

# ── 提示词建议规则库 ──────────────────────────────────────────────
# 格式：(case_id_prefix, error_type, 建议文字)
SUGGESTION_RULES = [
    # 代码质量误报
    ("QUAL-E-001", "false_positive",
     "裸 except 被持续误报为 HIGH → 在 Prompt LOW 示例中添加：'裸except捕获异常 = LOW，不可直接被外部利用'"),
    ("QUAL-E-002", "false_positive",
     "资源未关闭被误报为 HIGH → 添加 LOW 示例：'文件/连接未关闭 = LOW，稳定性问题而非安全漏洞'"),
    ("QUAL-E-003", "false_positive",
     "可变默认参数被误报 → 添加：'Python 可变默认参数 = LOW，仅影响函数行为，不涉及安全'"),
    ("QUAL-E-005", "false_positive",
     "魔法数字被误报 → 明确：'魔法数字 = LOW，代码可读性问题，无安全影响'"),
    ("QUAL-E-006", "false_positive",
     "输入验证缺失被过度评级 → 区分：'边界输入验证缺失 = MEDIUM；格式校验缺失 = LOW'"),
    ("QUAL-M-001", "false_positive",
     "忘记 await 被误报为 HIGH → 添加：'async/await 遗漏 = MEDIUM，运行时错误而非安全漏洞'"),
    # 干净代码误报
    ("CLEAN-006", "false_positive",
     "规范 JWT 代码被误报 → 在 Prompt 中添加负面引导：'jwt.encode 从 os.environ 读密钥且有 exp 字段 = 安全实现，不报 HIGH'"),
    ("CLEAN-010", "false_positive",
     "规范文件上传被误报 → 添加：'有 ALLOWED_TYPES 白名单 + uuid 文件名 = 安全实现'"),
    ("CLEAN-013", "false_positive",
     "健康检查接口被误报 → 添加：'/health 接口检查数据库连通性 = 运维最佳实践，不报安全问题'"),
    # 安全边界误报
    ("SEC-M-008", "false_positive",
     "GraphQL 内省被误报为 HIGH → 降为 MEDIUM：'内省泄露 schema 是信息泄露，不是直接 RCE'"),
    ("SEC-H-006", "false_positive",
     "子域名劫持被过度评级 → 添加上下文判断：'仅在 CNAME 指向不存在服务时才是 HIGH'"),
    # 性能类漏报
    ("PERF-E-001", "false_negative",
     "N+1 查询被漏报 → 在 Prompt 性能规则中强化：'循环内对每条记录各执行一次 DB 查询 = 典型 N+1，必须报 HIGH'"),
    ("PERF-E-006", "false_negative",
     "无分页接口漏报 → 强化规则：'直接 SELECT * 无 LIMIT 的列表接口 = HIGH，数据量大时可直接导致服务崩溃'"),
    ("PERF-E-010", "false_negative",
     "同步 HTTP 循环漏报 → 添加：'for 循环内 requests.get() = HIGH，串行网络请求会阻塞线程'"),
    ("PERF-M-005", "false_negative",
     "事务内 HTTP 调用漏报 → 添加：'数据库事务内包含外部 HTTP 调用 = HIGH，持有锁等待网络是死锁根源'"),
]


def _latest_two_runs():
    runs = get_runs()
    if len(runs) >= 2:
        return runs[0]["run_id"], runs[1]["run_id"]
    elif runs:
        return runs[0]["run_id"], None
    return None, None


def snapshot(run_id: str = None) -> dict:
    """单次运行快照：按类别/难度统计准确率。"""
    if not run_id:
        runs = get_runs()
        if not runs:
            return {}
        run_id = runs[0]["run_id"]

    records = get_records(run_id=run_id)
    if not records:
        return {}

    total  = len(records)
    passed = sum(1 for r in records if r["passed"])
    fp     = [r for r in records if r["error_type"] == "false_positive"]
    fn     = [r for r in records if r["error_type"] == "false_negative"]
    errors = [r for r in records if r["error_type"] == "json_error"]

    by_cat  = defaultdict(lambda: {"p": 0, "t": 0})
    by_diff = defaultdict(lambda: {"p": 0, "t": 0})
    for r in records:
        by_cat[r["category"]]["t"]  += 1
        by_diff[r["difficulty"]]["t"] += 1
        if r["passed"]:
            by_cat[r["category"]]["p"]  += 1
            by_diff[r["difficulty"]]["p"] += 1

    return {
        "run_id": run_id,
        "total": total, "passed": passed,
        "accuracy": round(passed / total * 100, 1),
        "false_positives": fp,
        "false_negatives": fn,
        "json_errors": errors,
        "by_category": {k: {"pass": v["p"], "total": v["t"],
                             "rate": round(v["p"] / v["t"] * 100)} for k, v in by_cat.items()},
        "by_difficulty": {k: {"pass": v["p"], "total": v["t"],
                               "rate": round(v["p"] / v["t"] * 100)} for k, v in by_diff.items()},
    }


def persistent_errors(min_runs: int = 2) -> list[dict]:
    """返回在至少 min_runs 次运行中都失败的用例（持续性问题）。"""
    records = get_records()
    case_failures = defaultdict(list)
    for r in records:
        if not r["passed"]:
            case_failures[r["case_id"]].append(r)

    result = []
    for case_id, failures in case_failures.items():
        unique_runs = len(set(r["run_id"] for r in failures))
        if unique_runs >= min_runs:
            latest = sorted(failures, key=lambda x: x["run_id"], reverse=True)[0]
            result.append({
                "case_id": case_id,
                "case_name": latest["case_name"],
                "category": latest["category"],
                "difficulty": latest["difficulty"],
                "fail_count": unique_runs,
                "error_type": latest["error_type"],
                "latest_run": latest["run_id"],
            })

    return sorted(result, key=lambda x: -x["fail_count"])


def regressions(new_run: str = None, old_run: str = None) -> list[dict]:
    """检测退化：在 old_run 中通过但在 new_run 中失败的用例。"""
    if not new_run or not old_run:
        new_run, old_run = _latest_two_runs()
    if not new_run or not old_run:
        return []

    new_records = {r["case_id"]: r for r in get_records(run_id=new_run)}
    old_records = {r["case_id"]: r for r in get_records(run_id=old_run)}

    regressions = []
    for case_id, new_r in new_records.items():
        old_r = old_records.get(case_id)
        if old_r and old_r["passed"] and not new_r["passed"]:
            regressions.append({
                "case_id": case_id,
                "case_name": new_r["case_name"],
                "category": new_r["category"],
                "old_run": old_run,
                "new_run": new_run,
                "error_type": new_r["error_type"],
            })
    return regressions


def improvements(new_run: str = None, old_run: str = None) -> list[dict]:
    """检测改进：在 old_run 中失败但在 new_run 中通过的用例。"""
    if not new_run or not old_run:
        new_run, old_run = _latest_two_runs()
    if not new_run or not old_run:
        return []

    new_records = {r["case_id"]: r for r in get_records(run_id=new_run)}
    old_records = {r["case_id"]: r for r in get_records(run_id=old_run)}

    improvements = []
    for case_id, new_r in new_records.items():
        old_r = old_records.get(case_id)
        if old_r and not old_r["passed"] and new_r["passed"]:
            improvements.append({
                "case_id": case_id,
                "case_name": new_r["case_name"],
                "category": new_r["category"],
                "old_error_type": old_r["error_type"],
            })
    return improvements


def prompt_suggestions(run_id: str = None) -> list[str]:
    """基于持续性错误和规则库，生成具体的 Prompt 修改建议。"""
    persistent = persistent_errors(min_runs=1)
    persistent_ids = {e["case_id"]: e for e in persistent}

    suggestions = []
    for case_prefix, etype, suggestion in SUGGESTION_RULES:
        if case_prefix in persistent_ids:
            e = persistent_ids[case_prefix]
            if e["error_type"] == etype:
                fail_label = f"（已失败 {e['fail_count']} 次）" if e["fail_count"] > 1 else ""
                suggestions.append(f"[{case_prefix}]{fail_label} {suggestion}")

    # 自动归纳规律：同类别误报超过3个时给出通用建议
    if run_id:
        fp_records = [r for r in get_records(run_id=run_id)
                      if r["error_type"] == "false_positive"]
        cat_fp = Counter(r["category"] for r in fp_records)
        for cat, cnt in cat_fp.most_common():
            if cnt >= 3 and not any(cat.lower() in s.lower() for s in suggestions):
                suggestions.append(
                    f"[通用] {cat} 类别有 {cnt} 个误报，建议在 Prompt 中增加该类别的 LOW/MEDIUM 示例"
                )

    return suggestions


def print_report(run_id: str = None, compare: bool = False):
    """打印完整分析报告到终端。"""
    runs = get_runs()
    if not runs:
        print("数据库为空，请先运行 eval 或导入历史数据")
        return

    if not run_id:
        run_id = runs[0]["run_id"]

    snap = snapshot(run_id)
    bar = "█" * int(snap["accuracy"] / 10) + "░" * (10 - int(snap["accuracy"] / 10))

    print(f"\n{'='*60}")
    print(f"  AI PR Review 调优分析报告")
    print(f"  运行：{run_id}")
    print(f"{'='*60}\n")

    # 总体准确率
    print(f"[总体准确率]  {snap['accuracy']}%  {bar}")
    print(f"  通过: {snap['passed']}/{snap['total']}  "
          f"误报: {len(snap['false_positives'])}  "
          f"漏报: {len(snap['false_negatives'])}  "
          f"解析错误: {len(snap['json_errors'])}\n")

    # 按类别
    print("[按类别]")
    cat_order = ["security", "performance", "quality", "clean", "edge"]
    for cat in cat_order:
        v = snap["by_category"].get(cat, {"pass": 0, "total": 0, "rate": 0})
        bar_c = "█" * (v["rate"] // 10) + "░" * (10 - v["rate"] // 10)
        status = "✓" if v["rate"] >= 70 else "!"
        print(f"  {status} {cat:12s}  {v['pass']:2d}/{v['total']:2d}  {v['rate']:3d}%  {bar_c}")

    # 按难度
    print("\n[按难度]")
    for diff in ["easy", "medium", "hard"]:
        v = snap["by_difficulty"].get(diff, {"pass": 0, "total": 0, "rate": 0})
        print(f"  {diff:8s}  {v['pass']:2d}/{v['total']:2d}  {v['rate']:3d}%")

    # 持续性错误
    persistent = persistent_errors(min_runs=2)
    if persistent:
        print(f"\n[持续性错误] （出现在 >=2 次运行中）")
        for e in persistent[:10]:
            print(f"  [{e['fail_count']}次] {e['case_id']}  {e['case_name'][:35]}  "
                  f"({e['category']}, {e['error_type']})")

    # 退化/改进
    if compare and len(runs) >= 2:
        new_run, old_run = runs[0]["run_id"], runs[1]["run_id"]
        reg = regressions(new_run, old_run)
        imp = improvements(new_run, old_run)
        print(f"\n[退化检测]  {old_run[:15]} → {new_run[:15]}")
        if reg:
            for r in reg:
                print(f"  ↓ {r['case_id']}  {r['case_name'][:35]}  ({r['error_type']})")
        else:
            print("  无退化")
        print(f"\n[改进]")
        if imp:
            for r in imp:
                print(f"  ↑ {r['case_id']}  {r['case_name'][:35]}")
        else:
            print("  无新改进")

    # Prompt 建议
    suggestions = prompt_suggestions(run_id)
    if suggestions:
        print(f"\n[Prompt 修改建议]  ({len(suggestions)} 条)")
        for i, s in enumerate(suggestions, 1):
            print(f"  {i}. {s}")
    else:
        print("\n[Prompt 修改建议]  暂无明显改进点")

    print(f"\n{'='*60}")
    print("  运行历史")
    print(f"{'='*60}")
    for r in runs[:5]:
        trend = ""
        print(f"  {r['run_id'][:15]}  {r['accuracy']:5.1f}%  "
              f"FP:{r['false_pos']:2d} FN:{r['false_neg']:2d}  "
              f"[{r['prompt_version']}] {r['notes']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI PR Review 调优分析")
    parser.add_argument("--run",     type=str, help="分析指定运行 ID")
    parser.add_argument("--compare", action="store_true", help="对比最近两次运行")
    args = parser.parse_args()
    print_report(run_id=args.run, compare=args.compare)
