"""
评测运行器：将100个用例通过AI分析引擎跑一遍，输出评测结果。

运行方式：
    cd ai-pr-review-assistant
    python -m eval.runner [--limit N] [--category SEC] [--difficulty hard]
"""

import sys, os, json, time, argparse
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

# 把项目根目录加入路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from eval.cases import CASES
from github_client import PRData, PRFile
from analyzer import Analyzer


# ── 构造模拟 PRData ────────────────────────────────────────────────

def make_pr_data(case: dict) -> PRData:
    """将测试用例转换为 PRData 对象送入分析引擎。"""
    code = case["code"]
    filename = case["filename"]
    lines = code.count("\n") + 1

    file = PRFile(
        filename=filename,
        status="added",
        additions=lines,
        deletions=0,
        patch="\n".join(f"+{line}" for line in code.splitlines()),
    )

    return PRData(
        number=0,
        title=f"[EVAL] {case['name']}",
        body=f"评测用例 {case['id']}：{case['description']}",
        author="eval-bot",
        url=f"https://github.com/eval/test/pull/{case['id']}",
        base_branch="main",
        head_branch=f"eval/{case['id']}",
        head_sha="0000000",
        changed_files=1,
        additions=lines,
        deletions=0,
        files=[file],
    )


# ── 单用例评测 ─────────────────────────────────────────────────────

@dataclass
class CaseResult:
    id: str
    name: str
    difficulty: str
    category: str
    expected_high: bool
    actual_verdict: str
    actual_score: int
    actual_high_count: int
    actual_med_count: int
    actual_low_count: int
    keyword_matched: bool
    matched_keywords: list
    passed: bool
    latency_ms: int
    error: str = ""


def evaluate_case(case: dict, analyzer: Analyzer) -> CaseResult:
    pr = make_pr_data(case)
    t0 = time.time()
    error = ""

    try:
        result = analyzer.analyze(pr)
    except Exception as e:
        error = str(e)
        return CaseResult(
            id=case["id"], name=case["name"],
            difficulty=case["difficulty"], category=case["category"],
            expected_high=case["expected_high"],
            actual_verdict="ERROR", actual_score=0,
            actual_high_count=0, actual_med_count=0, actual_low_count=0,
            keyword_matched=False, matched_keywords=[],
            passed=False,
            latency_ms=int((time.time() - t0) * 1000),
            error=error,
        )

    latency_ms = int((time.time() - t0) * 1000)

    high_count = sum(1 for r in result.risks if r.severity == "HIGH")
    med_count  = sum(1 for r in result.risks if r.severity == "MEDIUM")
    low_count  = sum(1 for r in result.risks if r.severity == "LOW")

    # 关键词匹配：在所有风险的 title + description + why_it_matters 中搜索
    all_text = " ".join(
        f"{r.title} {r.description} {r.why_it_matters} {r.suggestion}"
        for r in result.risks
    ).lower()

    matched = [kw for kw in case["expected_keywords"] if kw.lower() in all_text]
    keyword_matched = (
        len(matched) > 0
        if case["expected_keywords"]
        else True  # 无期望关键词（干净代码）默认通过
    )

    # 判断是否通过
    if case["expected_high"]:
        # 预期有HIGH：必须至少有1个HIGH，且关键词匹配
        passed = high_count >= 1 and keyword_matched
    else:
        # 预期无HIGH（干净代码或低风险）：不能有HIGH，允许有MEDIUM/LOW
        passed = high_count == 0

    return CaseResult(
        id=case["id"], name=case["name"],
        difficulty=case["difficulty"], category=case["category"],
        expected_high=case["expected_high"],
        actual_verdict=result.verdict,
        actual_score=result.overall_score,
        actual_high_count=high_count,
        actual_med_count=med_count,
        actual_low_count=low_count,
        keyword_matched=keyword_matched,
        matched_keywords=matched,
        passed=passed,
        latency_ms=latency_ms,
    )


# ── 主运行逻辑 ─────────────────────────────────────────────────────

def run_eval(cases, limit=None, save=True):
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("AI_API_KEY")
    if not api_key:
        print("❌ 缺少 ANTHROPIC_API_KEY，请配置 .env")
        sys.exit(1)

    analyzer = Analyzer(api_key)

    if limit:
        cases = cases[:limit]

    total = len(cases)
    results = []
    passed = 0
    failed_cases = []

    print(f"\n[START] 开始评测：{total} 个用例\n{'─'*60}")

    for i, case in enumerate(cases, 1):
        print(f"[{i:3d}/{total}] {case['id']} — {case['name'][:40]}", end=" ", flush=True)
        r = evaluate_case(case, analyzer)
        results.append(r)

        if r.error:
            print(f"❌ ERROR: {r.error[:50]}")
        elif r.passed:
            passed += 1
            print(f"✅ ({r.latency_ms}ms, score={r.actual_score}, HIGH={r.actual_high_count})")
        else:
            failed_cases.append(r)
            flag = "🔴 漏报" if case["expected_high"] and r.actual_high_count == 0 else "🟡 误报"
            print(f"{flag} ({r.latency_ms}ms, score={r.actual_score}, HIGH={r.actual_high_count})")

    # ── 统计摘要 ──────────────────────────────────────────────────
    print(f"\n{'═'*60}")
    print(f"📊 评测完成\n")

    accuracy = passed / total * 100
    avg_latency = sum(r.latency_ms for r in results) / total

    print(f"总体准确率：{passed}/{total} = {accuracy:.1f}%")
    print(f"平均延迟：{avg_latency:.0f}ms")

    # 按难度统计
    for diff in ["easy", "medium", "hard"]:
        subset = [r for r in results if r.difficulty == diff]
        if subset:
            p = sum(1 for r in subset if r.passed)
            print(f"  {diff:8s}: {p}/{len(subset)} = {p/len(subset)*100:.0f}%")

    # 按类别统计
    print()
    for cat in ["security", "performance", "quality", "clean", "edge"]:
        subset = [r for r in results if r.category == cat]
        if subset:
            p = sum(1 for r in subset if r.passed)
            print(f"  {cat:12s}: {p}/{len(subset)} = {p/len(subset)*100:.0f}%")

    # 误报 & 漏报
    false_positives = [r for r in results if not r.expected_high and r.actual_high_count > 0]
    false_negatives = [r for r in results if r.expected_high and r.actual_high_count == 0]

    print(f"\n🔴 漏报（预期HIGH但未发现）：{len(false_negatives)} 个")
    for r in false_negatives:
        print(f"   {r.id} — {r.name}")

    print(f"\n🟡 误报（预期无HIGH但报了HIGH）：{len(false_positives)} 个")
    for r in false_positives:
        print(f"   {r.id} — {r.name}（actual HIGH={r.actual_high_count}）")

    # ── 保存结果 ──────────────────────────────────────────────────
    if save:
        output_dir = Path(__file__).parent / "results"
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"eval_{timestamp}.json"

        data = {
            "timestamp": timestamp,
            "total": total,
            "passed": passed,
            "accuracy": round(accuracy, 2),
            "avg_latency_ms": round(avg_latency),
            "false_positives": len(false_positives),
            "false_negatives": len(false_negatives),
            "results": [asdict(r) for r in results],
        }
        output_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n💾 结果已保存：{output_file}")

        # 自动写入调优数据库
        try:
            from tuning.db import save_run
            save_run(timestamp, results)
            print(f"📊 已同步到调优数据库（运行 python -m tuning.analyze 查看分析）")
        except Exception as e:
            print(f"[tuning db] 写入跳过：{e}")

    return results


# ── CLI ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI PR Review 评测运行器")
    parser.add_argument("--limit", type=int, help="只跑前N个用例（调试用）")
    parser.add_argument("--category", choices=["security","performance","quality","clean","edge"],
                        help="只跑指定类别")
    parser.add_argument("--difficulty", choices=["easy","medium","hard"],
                        help="只跑指定难度")
    parser.add_argument("--no-save", action="store_true", help="不保存结果文件")
    args = parser.parse_args()

    cases = CASES
    if args.category:
        cases = [c for c in cases if c["category"] == args.category]
    if args.difficulty:
        cases = [c for c in cases if c["difficulty"] == args.difficulty]

    run_eval(cases, limit=args.limit, save=not args.no_save)
