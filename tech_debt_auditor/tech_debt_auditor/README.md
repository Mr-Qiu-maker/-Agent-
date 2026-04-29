# Tech Debt Auditor — 多 Agent 代码技术债务审计系统

## 系统架构

```
OrchestratorAgent（主控）
├── SecurityAgent    → 安全漏洞扫描（SQL注入、硬编码密钥、XSS）
├── PerformanceAgent → 性能瓶颈识别（N+1查询、缓存缺失、内存泄漏）
└── StyleAgent       → 可维护性审计（圈复杂度、重复代码、命名规范）
         ↓
  长链推理（两轮对话）
  → 观察阶段：跨维度关联分析
  → 决策阶段：评级 + 优先级 Roadmap
         ↓
  结构化报告（JSON + Markdown）
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置 API Key
export ANTHROPIC_API_KEY="your-key-here"

# 3. 运行（使用内置 Demo 代码）
python main.py

# 4. 扫描你的真实代码库
python main.py --repo /path/to/your/repo --output report.md
```

## 输出文件

- `audit_report.md`  — 可读的 Markdown 报告
- `audit_report.json` — 完整 JSON 数据（含各 Agent 原始结果）

## Agent 说明

| Agent | 职责 | 关键检测项 |
|-------|------|-----------|
| SecurityAgent | 安全漏洞 | SQL注入、硬编码密钥、CWE-89/798 |
| PerformanceAgent | 性能瓶颈 | N+1查询、缓存缺失、同步阻塞 |
| StyleAgent | 代码风格 | 圈复杂度、重复代码、魔法数字 |
| OrchestratorAgent | 调度+综合 | 关联推理、评级、Roadmap生成 |

## 项目结构

```
tech_debt_auditor/
├── main.py                  # 入口
├── orchestrator.py          # 主控 Agent（长链推理）
├── requirements.txt
├── agents/
│   ├── security_agent.py    # 安全子 Agent
│   ├── performance_agent.py # 性能子 Agent
│   └── style_agent.py       # 风格子 Agent
├── tools/
│   └── file_tools.py        # 文件读取工具
└── output/
    └── report_generator.py  # Markdown 报告生成
```
