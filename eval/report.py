"""
评测报告生成器：读取 eval/results/ 下的 JSON 结果，生成 Markdown 报告。

运行方式：
    python -m eval.report                    # 读最新结果
    python -m eval.report results/eval_xxx.json  # 读指定文件
"""

import json, sys
from pathlib import Path
from datetime import datetime


def load_latest():
    results_dir = Path(__file__).parent / "results"
    files = sorted(results_dir.glob("eval_*.json"))
    if not files:
        print("❌ 没有找到评测结果，请先运行 python -m eval.runner")
        sys.exit(1)
    return json.loads(files[-1].read_text(encoding="utf-8")), files[-1].name


def generate_report(data: dict, source_file: str) -> str:
    results = data["results"]
    ts = data["timestamp"]
    total = data["total"]
    passed = data["passed"]
    accuracy = data["accuracy"]
    avg_latency = data["avg_latency_ms"]
    fp = data["false_positives"]
    fn = data["false_negatives"]

    # 按类别和难度聚合
    def group_stats(key):
        groups = {}
        for r in results:
            k = r[key]
            if k not in groups:
                groups[k] = {"total": 0, "passed": 0}
            groups[k]["total"] += 1
            if r["passed"]:
                groups[k]["passed"] += 1
        return groups

    by_diff = group_stats("difficulty")
    by_cat  = group_stats("category")

    score_bar = "█" * int(accuracy / 10) + "░" * (10 - int(accuracy / 10))

    lines = [
        f"# AI PR Review 评测报告",
        f"",
        f"**生成时间：** {ts}  ",
        f"**数据来源：** `{source_file}`",
        f"",
        f"---",
        f"",
        f"## 总体结果",
        f"",
        f"| 指标 | 值 |",
        f"|------|-----|",
        f"| 总体准确率 | **{accuracy}%** `{score_bar}` |",
        f"| 通过 / 总计 | {passed} / {total} |",
        f"| 平均延迟 | {avg_latency}ms |",
        f"| 漏报数（预期HIGH未发现）| 🔴 {fn} |",
        f"| 误报数（预期无HIGH却报了）| 🟡 {fp} |",
        f"",
        f"---",
        f"",
        f"## 按难度分布",
        f"",
        f"| 难度 | 通过 | 总计 | 准确率 |",
        f"|------|------|------|--------|",
    ]

    for diff in ["easy", "medium", "hard"]:
        s = by_diff.get(diff, {"total": 0, "passed": 0})
        rate = s["passed"] / s["total"] * 100 if s["total"] else 0
        lines.append(f"| {diff} | {s['passed']} | {s['total']} | {rate:.0f}% |")

    lines += [
        f"",
        f"## 按类别分布",
        f"",
        f"| 类别 | 通过 | 总计 | 准确率 |",
        f"|------|------|------|--------|",
    ]

    cat_labels = {
        "security": "安全漏洞",
        "performance": "性能问题",
        "quality": "代码质量",
        "clean": "干净代码（误报测试）",
        "edge": "边界/陷阱用例",
    }
    for cat, label in cat_labels.items():
        s = by_cat.get(cat, {"total": 0, "passed": 0})
        rate = s["passed"] / s["total"] * 100 if s["total"] else 0
        lines.append(f"| {label} | {s['passed']} | {s['total']} | {rate:.0f}% |")

    # 失败用例列表
    failed = [r for r in results if not r["passed"] and not r["error"]]
    errors = [r for r in results if r["error"]]

    lines += [
        f"",
        f"---",
        f"",
        f"## 漏报用例（{fn} 个）",
        f"",
        f"> 预期发现 HIGH 风险，但 AI 未报告",
        f"",
    ]

    fn_cases = [r for r in results if r["expected_high"] and r["actual_high_count"] == 0 and not r["error"]]
    if fn_cases:
        lines.append("| ID | 名称 | 难度 | 实际评分 |")
        lines.append("|-----|------|------|---------|")
        for r in fn_cases:
            lines.append(f"| {r['id']} | {r['name']} | {r['difficulty']} | {r['actual_score']}/10 |")
    else:
        lines.append("*无漏报* ✅")

    lines += [
        f"",
        f"## 误报用例（{fp} 个）",
        f"",
        f"> 预期无 HIGH 风险，但 AI 报告了 HIGH",
        f"",
    ]

    fp_cases = [r for r in results if not r["expected_high"] and r["actual_high_count"] > 0]
    if fp_cases:
        lines.append("| ID | 名称 | 难度 | 误报HIGH数 |")
        lines.append("|-----|------|------|-----------|")
        for r in fp_cases:
            lines.append(f"| {r['id']} | {r['name']} | {r['difficulty']} | {r['actual_high_count']} |")
    else:
        lines.append("*无误报* ✅")

    # 详细结果
    lines += [
        f"",
        f"---",
        f"",
        f"## 完整结果列表",
        f"",
        f"| ID | 名称 | 难度 | 类别 | 结果 | 评分 | H/M/L | 延迟 |",
        f"|----|------|------|------|------|------|-------|------|",
    ]

    for r in results:
        if r["error"]:
            status = "💥 ERROR"
        elif r["passed"]:
            status = "✅"
        else:
            if r["expected_high"] and r["actual_high_count"] == 0:
                status = "🔴 漏报"
            else:
                status = "🟡 误报"

        hml = f"{r['actual_high_count']}/{r['actual_med_count']}/{r['actual_low_count']}"
        lines.append(
            f"| {r['id']} | {r['name'][:25]} | {r['difficulty']} | {r['category']} "
            f"| {status} | {r['actual_score']}/10 | {hml} | {r['latency_ms']}ms |"
        )

    lines += [
        f"",
        f"---",
        f"",
        f"*由 AI PR Review 评测框架生成 · {ts}*",
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        f = Path(sys.argv[1])
        data = json.loads(f.read_text(encoding="utf-8"))
        source = f.name
    else:
        data, source = load_latest()

    report = generate_report(data, source)

    output_dir = Path(__file__).parent / "results"
    ts = data["timestamp"]
    out_file = output_dir / f"report_{ts}.md"
    out_file.write_text(report, encoding="utf-8")

    print(report)
    print(f"\n💾 报告已保存：{out_file}")
