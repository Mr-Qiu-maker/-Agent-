"""
Tech Debt Auditor — Orchestrator Agent
---------------------------------------
主控 Agent，负责任务拆解、调度三个子 Agent、汇总报告。
流程：接收代码库路径 → 并行调度子 Agent → 收集结果 → 长链推理生成最终报告
"""

import json
import time
from pathlib import Path
from datetime import datetime

import anthropic

from agents.security_agent import SecurityAgent
from agents.performance_agent import PerformanceAgent
from agents.style_agent import StyleAgent
from tools.file_tools import collect_source_files, read_file_content

client = anthropic.Anthropic()

ORCHESTRATOR_SYSTEM = """你是一个代码质量审计系统的主控 Agent（Orchestrator）。

你的职责：
1. 接收三个子 Agent（安全、性能、风格）的分析结果
2. 进行跨维度的关联推理：
   - 安全漏洞是否因性能优化妥协导致？
   - 风格混乱是否暗示团队协作问题？
   - 哪些问题需要立即修复，哪些可延迟？
3. 评估整体技术债务等级（S / A / B / C / D）
4. 生成优先级排序的修复 Roadmap

推理时请展示你的思考链：先列出关键观察，再推导结论，最后给出行动建议。
输出必须是合法 JSON，不含任何 markdown 标记。"""


class OrchestratorAgent:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.agent_results = {}
        self.conversation_history = []

    def _log(self, agent: str, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [{agent:12s}] {msg}")

    def run(self) -> dict:
        self._log("ORCHESTRATOR", f"开始审计: {self.repo_path}")

        # Step 1: 收集源文件
        files = collect_source_files(self.repo_path)
        self._log("ORCHESTRATOR", f"发现 {len(files)} 个源文件，准备分发给子 Agent")

        # Step 2: 启动三个子 Agent（顺序执行，模拟调度）
        sub_agents = [
            ("security",    SecurityAgent(client)),
            ("performance", PerformanceAgent(client)),
            ("style",       StyleAgent(client)),
        ]

        for name, agent in sub_agents:
            self._log(name.upper(), "开始分析...")
            result = agent.analyze(files)
            self.agent_results[name] = result
            self._log(name.upper(), f"完成，发现 {len(result.get('issues', []))} 个问题")
            time.sleep(0.5)  # 模拟网络延迟

        # Step 3: Orchestrator 进行长链推理汇总
        self._log("ORCHESTRATOR", "所有子 Agent 完成，开始跨维度关联推理...")
        final_report = self._synthesize()

        self._log("ORCHESTRATOR", f"审计完成 — 技术债务等级: {final_report.get('debt_level', 'N/A')}")
        return final_report

    def _synthesize(self) -> dict:
        """
        长链推理阶段：Orchestrator 进行多轮对话，
        逐步从「观察」推导到「结论」再到「行动」。
        """
        summary_payload = json.dumps(self.agent_results, ensure_ascii=False, indent=2)

        # 第一轮：观察与关联
        self.conversation_history.append({
            "role": "user",
            "content": f"""以下是三个子 Agent 的分析结果：

{summary_payload}

请先进行「观察阶段」：
- 列出每个维度最严重的 3 个问题
- 找出跨维度的关联模式（如：某个模块同时有安全+性能问题）
- 识别哪些问题可能有共同根因

以 JSON 格式输出你的观察，key 为 observations。"""
        })

        obs_response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=ORCHESTRATOR_SYSTEM,
            messages=self.conversation_history,
        )
        obs_text = obs_response.content[0].text
        self._log("ORCHESTRATOR", "第一轮推理完成（观察阶段）")
        self.conversation_history.append({"role": "assistant", "content": obs_text})

        # 第二轮：评级与 Roadmap
        self.conversation_history.append({
            "role": "user",
            "content": """基于你的观察，现在进行「决策阶段」：
1. 评定整体技术债务等级（S=危急 / A=严重 / B=中等 / C=轻微 / D=良好）
2. 生成按优先级排序的修复 Roadmap（P0 立即修 / P1 本周内 / P2 本月内）
3. 估算每个修复项的工作量（小时）

输出完整 JSON，包含：debt_level, reasoning, roadmap（数组，每项含 priority/issue/effort_hours/owner_hint）, overall_summary"""
        })

        final_response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=ORCHESTRATOR_SYSTEM,
            messages=self.conversation_history,
        )
        final_text = final_response.content[0].text
        self._log("ORCHESTRATOR", "第二轮推理完成（决策阶段）")

        # 解析最终 JSON
        try:
            clean = final_text.strip().lstrip("```json").rstrip("```").strip()
            start, end = clean.index("{"), clean.rindex("}") + 1
            report = json.loads(clean[start:end])
        except Exception:
            report = {"raw": final_text, "debt_level": "B", "overall_summary": final_text[:300]}

        # 注入子 Agent 原始数据
        report["agent_results"] = self.agent_results
        report["session_id"] = self.session_id
        report["scanned_at"] = datetime.now().isoformat()
        return report
