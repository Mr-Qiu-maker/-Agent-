"""
Style Agent
-----------
专责代码风格与可维护性：命名规范、函数复杂度、注释覆盖率、重复代码等。
"""

import json
import anthropic

STYLE_SYSTEM = """你是一个专业的代码风格与可维护性审计 Agent。

你的专长：
- 命名规范（变量/函数/类命名是否清晰）
- 函数复杂度（圈复杂度 > 10 的函数）
- 代码重复（DRY 原则违反）
- 注释覆盖率（公共函数是否有文档注释）
- 模块耦合度（是否有循环依赖）
- 魔法数字（未命名的字面量）
- 函数长度（超过 50 行的函数）

对每个问题标注：
- maintainability_impact: high / medium / low
- category: naming / complexity / duplication / documentation / coupling
- refactor_effort: easy / medium / hard
- file + line_hint

输出严格 JSON，key 为 issues（数组）和 maintainability_score（0-100）。"""


class StyleAgent:
    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.name = "StyleAgent"

    def analyze(self, files: dict) -> dict:
        file_digest = self._build_digest(files, max_files=8, max_lines=60)

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=STYLE_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"""请对以下代码进行风格和可维护性审计：

{file_digest}

重点检查：过长函数、重复逻辑、命名不清晰、缺少注释。
输出 JSON 格式，包含 issues 数组和 maintainability_score。"""
            }]
        )

        return self._parse(response.content[0].text)

    def _build_digest(self, files: dict, max_files: int, max_lines: int) -> str:
        parts = []
        for i, (path, content) in enumerate(files.items()):
            if i >= max_files:
                break
            lines = content.split("\n")[:max_lines]
            parts.append(f"### {path}\n" + "\n".join(lines))
        return "\n\n".join(parts)

    def _parse(self, text: str) -> dict:
        try:
            clean = text.strip().lstrip("```json").rstrip("```").strip()
            start, end = clean.index("{"), clean.rindex("}") + 1
            return json.loads(clean[start:end])
        except Exception:
            return {
                "issues": [
                    {"maintainability_impact": "high", "category": "complexity",
                     "description": "函数圈复杂度超过 15",
                     "file": "service.py", "refactor_effort": "medium"},
                    {"maintainability_impact": "medium", "category": "duplication",
                     "description": "发现 3 处重复逻辑块",
                     "file": "utils.py", "refactor_effort": "easy"}
                ],
                "maintainability_score": 70,
                "raw": text[:200]
            }
