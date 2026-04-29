"""
Tech Debt Auditor — 入口
用法：
  python main.py                    # 使用内置 Demo 代码演示
  python main.py --repo /path/to/repo  # 扫描真实代码库
"""

import argparse
import json
from pathlib import Path

from orchestrator import OrchestratorAgent
from output.report_generator import generate_markdown_report


def main():
    parser = argparse.ArgumentParser(description="多 Agent 代码技术债务审计系统")
    parser.add_argument("--repo", default="./demo_repo", help="代码库路径（默认使用内置 Demo）")
    parser.add_argument("--output", default="./audit_report.md", help="Markdown 报告输出路径")
    parser.add_argument("--json-output", default="./audit_report.json", help="JSON 报告输出路径")
    args = parser.parse_args()

    print("\n" + "="*55)
    print("   Tech Debt Auditor — 多 Agent 代码审计系统")
    print("="*55)
    print(f"  代码库: {args.repo}")
    print(f"  输出:   {args.output}")
    print("="*55 + "\n")

    # 运行 Orchestrator（调度三个子 Agent）
    orchestrator = OrchestratorAgent(repo_path=args.repo)
    report = orchestrator.run()

    # 保存 JSON 原始报告
    Path(args.json_output).write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n[保存] JSON 报告 → {args.json_output}")

    # 生成 Markdown 报告
    md = generate_markdown_report(report, output_path=args.output)
    print(f"[保存] Markdown 报告 → {args.output}\n")

    # 打印简报摘要
    print("="*55)
    print(f"  技术债务等级: {report.get('debt_level', 'N/A')}")
    print(f"  总问题数:     {sum(len(r.get('issues',[])) for r in report.get('agent_results',{}).values())}")
    print("="*55)
    roadmap = report.get("roadmap", [])
    p0 = [x for x in roadmap if x.get("priority") == "P0"]
    if p0:
        print(f"\n🚨 P0 立即修复（{len(p0)} 项）:")
        for item in p0:
            print(f"   · {item.get('issue', '')}")
    print()


if __name__ == "__main__":
    main()
