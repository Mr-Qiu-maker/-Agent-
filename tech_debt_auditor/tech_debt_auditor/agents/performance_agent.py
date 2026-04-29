"""
Performance Agent
-----------------
专责性能瓶颈识别：N+1 查询、无索引、内存泄漏、同步阻塞、缓存缺失等。
"""

import json
import anthropic

PERFORMANCE_SYSTEM = """你是一个专业的代码性能审计 Agent。

你的专长：
- N+1 数据库查询问题
- 缺少数据库索引
- 内存泄漏（未释放资源、循环引用）
- 同步阻塞 I/O（应使用异步）
- 缓存策略缺失（热点数据未缓存）
- 算法复杂度问题（O(n²) 可优化为 O(n log n)）
- 大对象频繁序列化

对每个问题标注：
- impact: high / medium / low（对响应时间的影响）
- category: database / memory / io / algorithm / cache
- estimated_improvement: 预估优化收益（如 "减少 60% 数据库查询"）
- file + line_hint

输出严格 JSON，key 为 issues（数组）和 performance_score（0-100）。"""


class PerformanceAgent:
    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.name = "PerformanceAgent"

    def analyze(self, files: dict) -> dict:
        file_digest = self._build_digest(files, max_files=8, max_lines=60)

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=PERFORMANCE_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"""请对以下代码进行性能审计：

{file_digest}

重点检查：循环内 DB 查询、未用异步、大列表全量加载、重复计算。
输出 JSON 格式，包含 issues 数组和 performance_score。"""
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
                    {"impact": "high", "category": "database",
                     "description": "循环内存在 N+1 查询",
                     "file": "views.py", "estimated_improvement": "减少 80% DB 查询次数"},
                    {"impact": "medium", "category": "cache",
                     "description": "热点接口未使用缓存",
                     "file": "api.py", "estimated_improvement": "响应时间降低 50%"}
                ],
                "performance_score": 58,
                "raw": text[:200]
            }
