"""
File Tools
----------
收集源文件、读取内容的工具函数，供各 Agent 调用。
"""

from pathlib import Path

SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".rb", ".php"}

IGNORE_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "coverage"
}


def collect_source_files(repo_path: Path, max_files: int = 30) -> dict:
    """
    遍历代码库，收集所有源文件内容。
    返回 {相对路径: 文件内容} 的字典。
    """
    files = {}
    repo_path = Path(repo_path)

    if not repo_path.exists():
        # 如果路径不存在，生成示例代码用于演示
        return _generate_demo_files()

    for file_path in sorted(repo_path.rglob("*")):
        if len(files) >= max_files:
            break
        if not file_path.is_file():
            continue
        if any(part in IGNORE_DIRS for part in file_path.parts):
            continue
        if file_path.suffix not in SUPPORTED_EXTENSIONS:
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            rel_path = str(file_path.relative_to(repo_path))
            files[rel_path] = content
        except Exception:
            continue

    return files if files else _generate_demo_files()


def read_file_content(file_path: str) -> str:
    try:
        return Path(file_path).read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return f"// Error reading file: {e}"


def _generate_demo_files() -> dict:
    """生成包含典型技术债务的示例代码，用于演示。"""
    return {
        "api/user_service.py": '''
import sqlite3
import hashlib

SECRET_KEY = "hardcoded_secret_12345"   # CWE-798: 硬编码凭证
DB_PATH = "app.db"

def get_user(username):
    conn = sqlite3.connect(DB_PATH)
    # CWE-89: SQL 注入漏洞
    query = f"SELECT * FROM users WHERE username = \'{username}\'"
    result = conn.execute(query).fetchall()
    conn.close()
    return result

def update_all_users():
    users = get_all_users()  # 全量加载
    for user in users:       # N+1: 循环内逐条查询
        orders = get_orders_by_user(user["id"])
        send_email(user["email"], orders)

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    return conn.execute("SELECT * FROM users").fetchall()

def get_orders_by_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    return conn.execute(f"SELECT * FROM orders WHERE user_id={user_id}").fetchall()

def process_data(data, flag1, flag2, flag3, mode, threshold, retry):
    # 圈复杂度极高的函数
    result = []
    for item in data:
        if flag1:
            if flag2:
                if mode == "a":
                    if item > threshold:
                        result.append(item * 2)
                    else:
                        result.append(item)
                elif mode == "b":
                    for i in range(retry):
                        result.append(item + i)
            elif flag3:
                result.append(item - 1)
        else:
            result.append(0)
    return result
''',
        "api/payment.py": '''
import requests

STRIPE_SECRET = "sk_live_abc123xyz"   # 硬编码 Stripe 密钥

def charge_card(amount, card_token, user_input):
    # 未验证 user_input，直接拼接
    url = "https://api.stripe.com/v1/charges"
    payload = f"amount={amount}&source={card_token}&description={user_input}"
    resp = requests.post(url, data=payload, auth=(STRIPE_SECRET, ""))
    return resp.json()

def refund(charge_id):
    # 重复逻辑（与 charge_card 相似）
    url = "https://api.stripe.com/v1/refunds"
    payload = f"charge={charge_id}"
    resp = requests.post(url, data=payload, auth=(STRIPE_SECRET, ""))
    return resp.json()
''',
        "utils/helpers.py": '''
def calculate(x, y, z, w, v):
    # 魔法数字
    if x > 9999:
        return x * 0.15 + 88
    elif y < 100:
        return y / 3.14159 * z
    else:
        a = x + y + z + w + v
        b = a * 0.07
        c = b + 500
        d = c - 200
        return d

# 重复代码：与 api/payment.py 中相同逻辑
def send_request(url, data):
    import requests
    resp = requests.post(url, data=data)
    return resp.json()
''',
        "models/order.py": '''
from datetime import datetime

class Order:
    def __init__(self, id, user_id, items, status, created_at, updated_at,
                 shipping_addr, billing_addr, discount_code, tax_rate,
                 notes, metadata):
        self.id = id
        self.user_id = user_id
        self.items = items
        self.status = status

    def to_dict(self):
        # 未缓存，每次调用都重新序列化大对象
        return {
            "id": self.id,
            "user": get_user(self.user_id),        # 每次 to_dict 触发 DB 查询
            "items": [i.to_dict() for i in self.items],
        }
'''
    }
