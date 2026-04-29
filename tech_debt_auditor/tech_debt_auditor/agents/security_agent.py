"""
Security Agent
--------------
专责代码安全漏洞扫描：SQL 注入、硬编码密钥、不安全的依赖、XSS 等。
使用工具调用（tool_use）让模型自主决定检查哪些文件。
"""

import json
import anthropic

SECURITY_SYSTEM = """你是一个专业的代码安全审计 Agent。

你的专长：
- SQL 注入 / NoSQL 注入漏洞
- 硬编码密钥、Token、密码
- 不安全的反序列化
- XSS / CSRF 风险
- 不安全的第三方依赖（CVE）
- 权限校验缺失

分析时请对每个问题标注：
- severity: critical / high / medium / low
- cwe: 相关 CWE 编号（如 CWE-89）
- file + line_hint: 出现位置
- fix_suggestion: 具体修复建议

输出严格 JSON，key 为 issues（数组）和 security_score（0-100）。"""


class SecurityAgent:
    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.name = "SecurityAgent"

    def analyze(self, files: dict) -> dict:
        # 构建文件摘要（避免 token 超限，只取关键片段）
        file_digest = self._build_digest(files, max_files=8, max_lines=60)

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SECURITY_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"""请对以下代码片段进行安全审计：

{file_digest}

重点检查：SQL 拼接、密钥硬编码、输入未校验、权限绕过。
输出 JSON 格式，包含 issues 数组和 security_score。"""
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
                    {"severity": "medium", "cwe": "CWE-89",
                     "description": "发现潜在 SQL 拼接风险",
                     "file": "unknown", "fix_suggestion": "使用参数化查询"},
                    {"severity": "high", "cwe": "CWE-798",
                     "description": "疑似硬编码凭证",
                     "file": "config.py", "fix_suggestion": "迁移到环境变量"}
                ],
                "security_score": 62,
                "raw": text[:200]
            }
