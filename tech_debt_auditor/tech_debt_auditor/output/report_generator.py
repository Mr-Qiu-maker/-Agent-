"""
Report Generator
----------------
将 Orchestrator 的 JSON 报告渲染为可读的 Markdown 报告。
"""

from datetime import datetime
from pathlib import Path


DEBT_LEVEL_DESC = {
    "S": "🔴 危急 — 存在严重安全漏洞或系统性崩溃风险，需立即停工修复",
    "A": "🟠 严重 — 多个高危问题并存，建议本周内专项处理",
    "B": "🟡 中等 — 技术债务积累明显，需纳入下一个 Sprint 计划",
    "C": "🟢 轻微 — 代码质量尚可，存在少量可优化项",
    "D": "✅ 良好 — 代码健康，保持当前工程规范即可",
}

PRIORITY_EMOJI = {"P0": "🚨", "P1": "⚠️", "P2": "📌"}


def generate_markdown_report(report: dict, output_path: str = None) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    debt_level = report.get("debt_level", "B")
    debt_desc = DEBT_LEVEL_DESC.get(debt_level, "未知等级")

    lines = [
        "# 代码技术债务审计报告",
        f"\n> 生成时间：{now}  |  Session: `{report.get('session_id', 'N/A')}`\n",
        f"## 技术债务等级：{debt_level}",
        f"\n{debt_desc}\n",
    ]

    # 总结
    summary = report.get("overall_summary", report.get("summary", ""))
    if summary:
        lines += ["## 执行摘要", f"\n{summary}\n"]

    # 推理过程
    reasoning = report.get("reasoning", "")
    if reasoning:
        lines += ["## Orchestrator 推理链", f"\n{reasoning}\n"]

    # 各 Agent 得分
    agent_results = report.get("agent_results", {})
    if agent_results:
        lines.append("## 各维度评分\n")
        lines.append("| 维度 | 评分 | 问题数 |")
        lines.append("|------|------|--------|")
        score_map = {
            "security": ("安全性", "security_score"),
            "performance": ("性能", "performance_score"),
            "style": ("可维护性", "maintainability_score"),
        }
        for key, (label, score_key) in score_map.items():
            if key in agent_results:
                r = agent_results[key]
                score = r.get(score_key, "N/A")
                count = len(r.get("issues", []))
                lines.append(f"| {label} | {score}/100 | {count} 个 |")
        lines.append("")

    # Roadmap
    roadmap = report.get("roadmap", [])
    if roadmap:
        lines.append("## 修复 Roadmap\n")
        for item in roadmap:
            p = item.get("priority", "P2")
            emoji = PRIORITY_EMOJI.get(p, "📌")
            issue = item.get("issue", "未知问题")
            effort = item.get("effort_hours", "?")
            owner = item.get("owner_hint", "")
            lines.append(f"### {emoji} [{p}] {issue}")
            lines.append(f"- 预估工作量：{effort} 小时")
            if owner:
                lines.append(f"- 建议负责人：{owner}")
            lines.append("")

    # 各 Agent 详细问题列表
    for key, (label, _) in {
        "security": ("安全漏洞详情", "security_score"),
        "performance": ("性能问题详情", "performance_score"),
        "style": ("风格问题详情", "maintainability_score"),
    }.items():
        if key not in agent_results:
            continue
        issues = agent_results[key].get("issues", [])
        if not issues:
            continue
        lines.append(f"## {label}\n")
        for issue in issues:
            desc = issue.get("description", str(issue))
            sev = issue.get("severity") or issue.get("impact") or issue.get("maintainability_impact", "")
            file_ = issue.get("file", "")
            fix = issue.get("fix_suggestion") or issue.get("estimated_improvement") or issue.get("refactor_effort", "")
            lines.append(f"- **{desc}**")
            if sev:
                lines.append(f"  - 严重程度：`{sev}`")
            if file_:
                lines.append(f"  - 文件：`{file_}`")
            if fix:
                lines.append(f"  - 建议：{fix}")
        lines.append("")

    content = "\n".join(lines)

    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")

    return content
