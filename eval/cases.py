"""
100个评测用例集
分布：Easy 60 / Medium 20 / Hard 20
类别：Security(35) / Performance(20) / Quality(15) / Clean(15) / Edge(15)

每个用例字段：
  id              唯一编号
  name            用例名称
  difficulty      easy / medium / hard
  category        security / performance / quality / clean / edge
  language        python / javascript / typescript / go
  filename        模拟文件名
  code            被分析的代码（模拟新增代码）
  expected_high   预期是否出现 HIGH 风险（True/False）
  expected_keywords  预期在分析结果中出现的关键词（至少命中一个即通过）
  description     用例测试意图
"""

CASES = [

    # ══════════════════════════════════════════════════════════════
    # SECURITY — Easy (15)
    # ══════════════════════════════════════════════════════════════

    {
        "id": "SEC-E-001",
        "name": "SQL注入：f-string拼接查询",
        "difficulty": "easy",
        "category": "security",
        "language": "python",
        "filename": "db.py",
        "code": """\
def find_user(username, password):
    conn = sqlite3.connect('app.db')
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    return conn.execute(query).fetchone()
""",
        "expected_high": True,
        "expected_keywords": ["SQL", "注入", "injection", "f-string", "参数化"],
        "description": "最经典的SQL注入，f-string直接拼接用户输入",
    },

    {
        "id": "SEC-E-002",
        "name": "命令注入：shell=True拼接字符串",
        "difficulty": "easy",
        "category": "security",
        "language": "python",
        "filename": "utils.py",
        "code": """\
import subprocess
def get_file(filename):
    result = subprocess.run(f"cat {filename}", shell=True, capture_output=True)
    return result.stdout
""",
        "expected_high": True,
        "expected_keywords": ["命令注入", "shell=True", "injection", "subprocess"],
        "description": "shell=True拼接用户输入，经典命令注入",
    },

    {
        "id": "SEC-E-003",
        "name": "XSS：innerHTML直接注入用户输入",
        "difficulty": "easy",
        "category": "security",
        "language": "javascript",
        "filename": "search.js",
        "code": """\
function renderResult(query) {
    document.getElementById('result').innerHTML = `<h2>Results for: ${query}</h2>`;
}
""",
        "expected_high": True,
        "expected_keywords": ["XSS", "innerHTML", "跨站", "textContent"],
        "description": "innerHTML直接注入用户输入，最基础的XSS",
    },

    {
        "id": "SEC-E-004",
        "name": "硬编码密钥",
        "difficulty": "easy",
        "category": "security",
        "language": "python",
        "filename": "config.py",
        "code": """\
SECRET_KEY = "my-super-secret-key-12345"
DATABASE_PASSWORD = "admin123"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
""",
        "expected_high": True,
        "expected_keywords": ["硬编码", "密钥", "secret", "hardcoded", "环境变量"],
        "description": "明文硬编码多个敏感凭证",
    },

    {
        "id": "SEC-E-005",
        "name": "明文存储密码",
        "difficulty": "easy",
        "category": "security",
        "language": "python",
        "filename": "user.py",
        "code": """\
def create_user(username, password):
    conn.execute("INSERT INTO users VALUES (?, ?)", (username, password))
    conn.commit()
""",
        "expected_high": True,
        "expected_keywords": ["明文", "密码", "哈希", "bcrypt", "hash"],
        "description": "密码不加密直接存入数据库",
    },

    {
        "id": "SEC-E-006",
        "name": "JWT无过期时间",
        "difficulty": "easy",
        "category": "security",
        "language": "python",
        "filename": "auth.py",
        "code": """\
import jwt
def create_token(user_id):
    return jwt.encode({"user_id": user_id}, SECRET_KEY, algorithm="HS256")
""",
        "expected_high": True,
        "expected_keywords": ["过期", "expiry", "exp", "JWT", "token"],
        "description": "JWT没有设置过期时间，一旦泄露永久有效",
    },

    {
        "id": "SEC-E-007",
        "name": "CORS配置通配符",
        "difficulty": "easy",
        "category": "security",
        "language": "python",
        "filename": "app.py",
        "code": """\
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True)
""",
        "expected_high": True,
        "expected_keywords": ["CORS", "通配符", "*", "跨域"],
        "description": "CORS允许所有来源同时开启credentials，高危配置",
    },

    {
        "id": "SEC-E-008",
        "name": "eval执行用户输入",
        "difficulty": "easy",
        "category": "security",
        "language": "python",
        "filename": "calculator.py",
        "code": """\
def calculate(expression):
    result = eval(expression)
    return result
""",
        "expected_high": True,
        "expected_keywords": ["eval", "代码执行", "任意代码", "注入"],
        "description": "直接eval用户输入，任意代码执行",
    },

    {
        "id": "SEC-E-009",
        "name": "不安全的随机数生成token",
        "difficulty": "easy",
        "category": "security",
        "language": "python",
        "filename": "token.py",
        "code": """\
import random
import string
def generate_token():
    return ''.join(random.choices(string.ascii_letters, k=32))
""",
        "expected_high": True,
        "expected_keywords": ["random", "secrets", "加密安全", "伪随机"],
        "description": "用非加密安全random生成安全token",
    },

    {
        "id": "SEC-E-010",
        "name": "路径遍历漏洞",
        "difficulty": "easy",
        "category": "security",
        "language": "python",
        "filename": "file_api.py",
        "code": """\
def read_file(filename):
    with open(f"/var/app/uploads/{filename}") as f:
        return f.read()
""",
        "expected_high": True,
        "expected_keywords": ["路径遍历", "path traversal", "../", "目录穿越"],
        "description": "未验证文件名，攻击者可通过../访问任意文件",
    },

    {
        "id": "SEC-E-011",
        "name": "默认管理员账号硬编码",
        "difficulty": "easy",
        "category": "security",
        "language": "python",
        "filename": "init_db.py",
        "code": """\
def init_db():
    conn.execute("INSERT INTO users VALUES (1, 'admin', 'admin123', 1)")
    conn.commit()
""",
        "expected_high": True,
        "expected_keywords": ["硬编码", "默认密码", "admin", "弱密码"],
        "description": "初始化时写死admin账号和弱密码",
    },

    {
        "id": "SEC-E-012",
        "name": "localStorage存储敏感token",
        "difficulty": "easy",
        "category": "security",
        "language": "javascript",
        "filename": "auth.js",
        "code": """\
function login(token) {
    localStorage.setItem('authToken', token);
    localStorage.setItem('userPassword', password);
}
""",
        "expected_high": True,
        "expected_keywords": ["localStorage", "XSS", "HttpOnly", "Cookie", "敏感"],
        "description": "将认证token和密码存入localStorage，XSS可直接窃取",
    },

    {
        "id": "SEC-E-013",
        "name": "SQL注入：字符串拼接",
        "difficulty": "easy",
        "category": "security",
        "language": "python",
        "filename": "search.py",
        "code": """\
def search_products(keyword):
    query = "SELECT * FROM products WHERE name LIKE '%" + keyword + "%'"
    return db.execute(query).fetchall()
""",
        "expected_high": True,
        "expected_keywords": ["SQL", "注入", "拼接", "参数化"],
        "description": "字符串拼接方式的SQL注入",
    },

    {
        "id": "SEC-E-014",
        "name": "未授权的删除接口",
        "difficulty": "easy",
        "category": "security",
        "language": "python",
        "filename": "api.py",
        "code": """\
@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    db.commit()
    return {"status": "deleted"}
""",
        "expected_high": True,
        "expected_keywords": ["权限", "认证", "授权", "auth", "未验证"],
        "description": "删除接口无任何权限验证，任何人可删除任意用户",
    },

    {
        "id": "SEC-E-015",
        "name": "document.write注入",
        "difficulty": "easy",
        "category": "security",
        "language": "javascript",
        "filename": "render.js",
        "code": """\
function showMessage(msg) {
    document.write('<div class="msg">' + msg + '</div>');
}
""",
        "expected_high": True,
        "expected_keywords": ["XSS", "document.write", "注入", "innerHTML"],
        "description": "document.write直接拼接用户内容，XSS漏洞",
    },

    # ══════════════════════════════════════════════════════════════
    # SECURITY — Medium (10)
    # ══════════════════════════════════════════════════════════════

    {
        "id": "SEC-M-001",
        "name": "SSRF：用户控制的URL请求",
        "difficulty": "medium",
        "category": "security",
        "language": "python",
        "filename": "webhook.py",
        "code": """\
import requests
def fetch_webhook(url):
    resp = requests.get(url, timeout=5)
    return resp.json()
""",
        "expected_high": True,
        "expected_keywords": ["SSRF", "服务端请求伪造", "内网", "URL验证"],
        "description": "用户控制URL，可探测内网服务（SSRF）",
    },

    {
        "id": "SEC-M-002",
        "name": "开放重定向",
        "difficulty": "medium",
        "category": "security",
        "language": "python",
        "filename": "auth.py",
        "code": """\
from flask import redirect, request
@app.route('/login')
def login():
    next_url = request.args.get('next', '/')
    # ... do login ...
    return redirect(next_url)
""",
        "expected_high": True,
        "expected_keywords": ["重定向", "redirect", "钓鱼", "白名单", "open redirect"],
        "description": "未验证重定向目标，可跳转到恶意站点",
    },

    {
        "id": "SEC-M-003",
        "name": "批量赋值漏洞",
        "difficulty": "medium",
        "category": "security",
        "language": "python",
        "filename": "user_api.py",
        "code": """\
@app.put("/users/{user_id}")
def update_user(user_id: int, data: dict):
    user = db.get(user_id)
    for key, value in data.items():
        setattr(user, key, value)
    db.save(user)
""",
        "expected_high": True,
        "expected_keywords": ["批量赋值", "mass assignment", "is_admin", "白名单", "权限提升"],
        "description": "允许用户更新任意字段，可能提升为管理员",
    },

    {
        "id": "SEC-M-004",
        "name": "弱密码重置逻辑",
        "difficulty": "medium",
        "category": "security",
        "language": "python",
        "filename": "auth.py",
        "code": """\
def reset_password(email):
    new_password = email.split('@')[0] + '123'
    update_password(email, new_password)
    send_email(email, f"New password: {new_password}")
    return new_password
""",
        "expected_high": True,
        "expected_keywords": ["弱密码", "可预测", "随机", "secrets", "重置"],
        "description": "重置密码可预测（邮箱前缀+123），且明文发送",
    },

    {
        "id": "SEC-M-005",
        "name": "正则ReDoS漏洞",
        "difficulty": "medium",
        "category": "security",
        "language": "python",
        "filename": "validator.py",
        "code": """\
import re
def validate_email(email):
    pattern = r'^(a+)+$'
    return bool(re.match(pattern, email))
""",
        "expected_high": True,
        "expected_keywords": ["ReDoS", "正则", "回溯", "拒绝服务", "regex"],
        "description": "灾难性回溯的正则表达式，可导致CPU耗尽",
    },

    {
        "id": "SEC-M-006",
        "name": "不安全的反序列化",
        "difficulty": "medium",
        "category": "security",
        "language": "python",
        "filename": "cache.py",
        "code": """\
import pickle
def load_user_data(data):
    return pickle.loads(data)
""",
        "expected_high": True,
        "expected_keywords": ["pickle", "反序列化", "RCE", "代码执行", "任意"],
        "description": "pickle.loads反序列化用户输入，可远程代码执行",
    },

    {
        "id": "SEC-M-007",
        "name": "JWT使用None算法",
        "difficulty": "medium",
        "category": "security",
        "language": "python",
        "filename": "auth.py",
        "code": """\
def verify_token(token):
    return jwt.decode(token, options={"verify_signature": False})
""",
        "expected_high": True,
        "expected_keywords": ["JWT", "签名", "验证", "algorithm", "none"],
        "description": "禁用JWT签名验证，任意token都会被接受",
    },

    {
        "id": "SEC-M-008",
        "name": "GraphQL内省未禁用",
        "difficulty": "medium",
        "category": "security",
        "language": "python",
        "filename": "graphql_api.py",
        "code": """\
from graphene import Schema
schema = Schema(query=Query, mutation=Mutation)

@app.route('/graphql', methods=['POST'])
def graphql_server():
    data = request.json
    result = schema.execute(data.get('query'))
    return jsonify(result.data)
""",
        "expected_high": False,
        "expected_keywords": ["内省", "introspection", "信息泄露", "生产环境"],
        "description": "生产环境未禁用GraphQL内省，泄露schema信息",
    },

    {
        "id": "SEC-M-009",
        "name": "时序攻击：字符串比较验证token",
        "difficulty": "medium",
        "category": "security",
        "language": "python",
        "filename": "webhook.py",
        "code": """\
def verify_webhook(secret, signature):
    expected = hmac.new(SECRET_KEY, secret, hashlib.sha256).hexdigest()
    return signature == expected
""",
        "expected_high": True,
        "expected_keywords": ["时序攻击", "timing attack", "hmac.compare_digest", "常数时间"],
        "description": "普通字符串比较而非常数时间比较，可被时序攻击",
    },

    {
        "id": "SEC-M-010",
        "name": "原型污染",
        "difficulty": "medium",
        "category": "security",
        "language": "javascript",
        "filename": "config.js",
        "code": """\
function mergeConfig(defaults, userConfig) {
    for (let key in userConfig) {
        defaults[key] = userConfig[key];
    }
    return defaults;
}
""",
        "expected_high": True,
        "expected_keywords": ["原型污染", "prototype pollution", "__proto__", "constructor"],
        "description": "for...in遍历合并对象，可被原型污染攻击",
    },

    # ══════════════════════════════════════════════════════════════
    # SECURITY — Hard (10)
    # ══════════════════════════════════════════════════════════════

    {
        "id": "SEC-H-001",
        "name": "竞态条件：令牌刷新",
        "difficulty": "hard",
        "category": "security",
        "language": "python",
        "filename": "auth.py",
        "code": """\
def refresh_token(old_token):
    stored = redis.get(f"token:{old_token}")
    if not stored:
        raise ValueError("Invalid token")
    new_token = generate_token()
    redis.delete(f"token:{old_token}")
    redis.set(f"token:{new_token}", "valid", ex=86400)
    return new_token
""",
        "expected_high": True,
        "expected_keywords": ["竞态条件", "race condition", "原子", "锁", "重放"],
        "description": "读取和删除token之间存在竞态窗口，可被重放攻击",
    },

    {
        "id": "SEC-H-002",
        "name": "整数溢出：权限位运算",
        "difficulty": "hard",
        "category": "security",
        "language": "python",
        "filename": "permissions.py",
        "code": """\
def has_permission(user_level, required_level):
    return user_level & required_level == required_level

def grant_permission(base, extra):
    return base + extra
""",
        "expected_high": True,
        "expected_keywords": ["溢出", "位运算", "整数", "权限", "bypass"],
        "description": "权限用整数加法而非位或运算，可导致权限绕过",
    },

    {
        "id": "SEC-H-003",
        "name": "二次SQL注入",
        "difficulty": "hard",
        "category": "security",
        "language": "python",
        "filename": "profile.py",
        "code": """\
def update_username(user_id, new_username):
    # 使用参数化查询存储（安全）
    db.execute("UPDATE users SET username=? WHERE id=?", (new_username, user_id))

def get_user_posts(username):
    # 从数据库取出username后直接拼接（危险）
    posts = db.execute(f"SELECT * FROM posts WHERE author='{username}'")
    return posts.fetchall()
""",
        "expected_high": True,
        "expected_keywords": ["二次注入", "second order", "SQL", "参数化"],
        "description": "存储时安全，读出后再拼接SQL，二次注入",
    },

    {
        "id": "SEC-H-004",
        "name": "不安全的直接对象引用",
        "difficulty": "hard",
        "category": "security",
        "language": "python",
        "filename": "api.py",
        "code": """\
@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int, current_user=Depends(get_current_user)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    return invoice
""",
        "expected_high": True,
        "expected_keywords": ["IDOR", "越权", "所有权", "authorization", "owner"],
        "description": "未校验invoice是否属于当前用户，可访问他人数据",
    },

    {
        "id": "SEC-H-005",
        "name": "XXE注入",
        "difficulty": "hard",
        "category": "security",
        "language": "python",
        "filename": "xml_parser.py",
        "code": """\
import xml.etree.ElementTree as ET
def parse_xml(xml_data):
    tree = ET.fromstring(xml_data)
    return {child.tag: child.text for child in tree}
""",
        "expected_high": True,
        "expected_keywords": ["XXE", "XML", "外部实体", "lxml", "defusedxml"],
        "description": "XML解析未禁用外部实体，可读取服务器文件",
    },

    {
        "id": "SEC-H-006",
        "name": "子域名劫持风险",
        "difficulty": "hard",
        "category": "security",
        "language": "javascript",
        "filename": "config.js",
        "code": """\
const API_BASE = 'https://api-staging.myapp.com';
const CDN_BASE = 'https://static-old.myapp.com';
const WEBHOOK_URL = 'https://hooks.partner-service.com/callback';
""",
        "expected_high": False,
        "expected_keywords": ["子域名", "CNAME", "劫持", "外部域名"],
        "description": "使用可能已停用的外部子域名，存在劫持风险",
    },

    {
        "id": "SEC-H-007",
        "name": "隐式类型转换绕过",
        "difficulty": "hard",
        "category": "security",
        "language": "javascript",
        "filename": "auth.js",
        "code": """\
function checkAdmin(user) {
    if (user.role == 0) {  // 使用==而非===
        return false;
    }
    return true;
}
""",
        "expected_high": True,
        "expected_keywords": ["类型转换", "===", "==", "绕过", "严格相等"],
        "description": "宽松比较导致类型混淆，可能被绕过权限检查",
    },

    {
        "id": "SEC-H-008",
        "name": "CSRF无防护",
        "difficulty": "hard",
        "category": "security",
        "language": "python",
        "filename": "transfer.py",
        "code": """\
@app.post("/transfer")
def transfer_money(from_account: int, to_account: int, amount: float,
                   current_user=Depends(get_current_user)):
    account = db.get(from_account)
    account.balance -= amount
    db.get(to_account).balance += amount
    db.commit()
""",
        "expected_high": True,
        "expected_keywords": ["CSRF", "跨站请求伪造", "token", "Origin", "Referer"],
        "description": "敏感操作无CSRF防护，第三方网站可诱导用户转账",
    },

    {
        "id": "SEC-H-009",
        "name": "日志注入",
        "difficulty": "hard",
        "category": "security",
        "language": "python",
        "filename": "logger.py",
        "code": """\
import logging
def log_login(username):
    logging.info(f"User login: {username}")
""",
        "expected_high": False,
        "expected_keywords": ["日志注入", "log injection", "换行", "伪造"],
        "description": "用户名含换行符可伪造日志记录",
    },

    {
        "id": "SEC-H-010",
        "name": "依赖混淆攻击风险",
        "difficulty": "hard",
        "category": "security",
        "language": "python",
        "filename": "requirements.txt",
        "code": """\
internal-utils==1.0.0
company-auth-lib==2.3.1
myapp-shared==0.9.5
""",
        "expected_high": False,
        "expected_keywords": ["依赖混淆", "supply chain", "私有包", "内部包"],
        "description": "内部私有包若未锁定源，可被公共包覆盖（依赖混淆）",
    },

    # ══════════════════════════════════════════════════════════════
    # PERFORMANCE — Easy (10)
    # ══════════════════════════════════════════════════════════════

    {
        "id": "PERF-E-001",
        "name": "N+1查询：循环内查数据库",
        "difficulty": "easy",
        "category": "performance",
        "language": "python",
        "filename": "posts.py",
        "code": """\
def get_posts_with_authors(post_ids):
    posts = []
    for post_id in post_ids:
        post = db.query(f"SELECT * FROM posts WHERE id={post_id}")
        author = db.query(f"SELECT * FROM users WHERE id={post['author_id']}")
        post['author'] = author
        posts.append(post)
    return posts
""",
        "expected_high": True,
        "expected_keywords": ["N+1", "查询", "JOIN", "批量", "循环"],
        "description": "每篇帖子都额外查一次作者，N+1问题",
    },

    {
        "id": "PERF-E-002",
        "name": "全表扫描后内存过滤",
        "difficulty": "easy",
        "category": "performance",
        "language": "python",
        "filename": "feed.py",
        "code": """\
def get_user_feed(user_id, limit=20):
    all_posts = db.execute("SELECT * FROM posts ORDER BY created_at DESC").fetchall()
    user_posts = [p for p in all_posts if p['author_id'] in get_following(user_id)]
    return user_posts[:limit]
""",
        "expected_high": True,
        "expected_keywords": ["全表", "内存", "过滤", "WHERE", "LIMIT", "JOIN"],
        "description": "拉取所有数据再内存过滤，百万级数据会OOM",
    },

    {
        "id": "PERF-E-003",
        "name": "无限增长的全局缓存",
        "difficulty": "easy",
        "category": "performance",
        "language": "python",
        "filename": "cache.py",
        "code": """\
_cache = {}

def get_user(user_id):
    if user_id not in _cache:
        _cache[user_id] = db.query_user(user_id)
    return _cache[user_id]
""",
        "expected_high": True,
        "expected_keywords": ["缓存", "内存泄漏", "TTL", "LRU", "无限增长"],
        "description": "缓存无上限、无过期，运行时间越长内存占用越高",
    },

    {
        "id": "PERF-E-004",
        "name": "同步阻塞批量发邮件",
        "difficulty": "easy",
        "category": "performance",
        "language": "python",
        "filename": "notify.py",
        "code": """\
def notify_all_users(message):
    users = db.execute("SELECT email FROM users").fetchall()
    for user in users:
        send_email(user['email'], message)
        time.sleep(0.1)
""",
        "expected_high": True,
        "expected_keywords": ["同步", "阻塞", "异步", "队列", "Celery", "并发"],
        "description": "同步循环发邮件，万级用户会阻塞请求数千秒",
    },

    {
        "id": "PERF-E-005",
        "name": "循环内字符串拼接",
        "difficulty": "easy",
        "category": "performance",
        "language": "python",
        "filename": "report.py",
        "code": """\
def build_report(items):
    result = ""
    for item in items:
        result += f"- {item['name']}: {item['value']}\n"
    return result
""",
        "expected_high": False,
        "expected_keywords": ["字符串拼接", "join", "性能", "O(n²)"],
        "description": "循环内+=拼接字符串，Python中O(n²)复杂度",
    },

    {
        "id": "PERF-E-006",
        "name": "无分页的列表接口",
        "difficulty": "easy",
        "category": "performance",
        "language": "python",
        "filename": "api.py",
        "code": """\
@app.get("/orders")
def get_orders():
    return db.execute("SELECT * FROM orders").fetchall()
""",
        "expected_high": True,
        "expected_keywords": ["分页", "LIMIT", "pagination", "数据量"],
        "description": "无分页直接返回所有记录，数据量大时超时/OOM",
    },

    {
        "id": "PERF-E-007",
        "name": "数据库连接未复用",
        "difficulty": "easy",
        "category": "performance",
        "language": "python",
        "filename": "db.py",
        "code": """\
def query_user(user_id):
    conn = sqlite3.connect('app.db')
    result = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return result

def query_post(post_id):
    conn = sqlite3.connect('app.db')
    result = conn.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
    return result
""",
        "expected_high": False,
        "expected_keywords": ["连接池", "connection pool", "复用", "频繁创建"],
        "description": "每次查询新建连接，高并发下会耗尽连接数",
    },

    {
        "id": "PERF-E-008",
        "name": "无索引的高频查询字段",
        "difficulty": "easy",
        "category": "performance",
        "language": "python",
        "filename": "search.py",
        "code": """\
def search_by_email(email):
    return db.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()

# users表只有主键索引，email无索引
""",
        "expected_high": False,
        "expected_keywords": ["索引", "index", "全表扫描", "性能"],
        "description": "高频查询字段email没有索引，随数据量线性变慢",
    },

    {
        "id": "PERF-E-009",
        "name": "递归无记忆化",
        "difficulty": "easy",
        "category": "performance",
        "language": "python",
        "filename": "fib.py",
        "code": """\
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
""",
        "expected_high": False,
        "expected_keywords": ["记忆化", "memoization", "递归", "指数", "cache"],
        "description": "递归Fibonacci没有记忆化，指数级时间复杂度",
    },

    {
        "id": "PERF-E-010",
        "name": "同步HTTP请求在循环中",
        "difficulty": "easy",
        "category": "performance",
        "language": "python",
        "filename": "aggregator.py",
        "code": """\
def fetch_all_prices(product_ids):
    prices = []
    for pid in product_ids:
        resp = requests.get(f"https://api.example.com/price/{pid}")
        prices.append(resp.json()['price'])
    return prices
""",
        "expected_high": True,
        "expected_keywords": ["串行", "并行", "asyncio", "aiohttp", "concurrent"],
        "description": "串行发HTTP请求，100个商品要等100次网络往返",
    },

    # ══════════════════════════════════════════════════════════════
    # PERFORMANCE — Medium (5)
    # ══════════════════════════════════════════════════════════════

    {
        "id": "PERF-M-001",
        "name": "async函数中使用阻塞IO",
        "difficulty": "medium",
        "category": "performance",
        "language": "python",
        "filename": "async_api.py",
        "code": """\
import asyncio
import requests  # 同步库

async def fetch_data(url):
    resp = requests.get(url)  # 阻塞整个事件循环
    return resp.json()
""",
        "expected_high": True,
        "expected_keywords": ["阻塞", "async", "aiohttp", "事件循环", "同步"],
        "description": "async函数中使用同步requests，会阻塞整个事件循环",
    },

    {
        "id": "PERF-M-002",
        "name": "SELECT *导致数据传输冗余",
        "difficulty": "medium",
        "category": "performance",
        "language": "python",
        "filename": "list_api.py",
        "code": """\
def get_user_list():
    users = db.execute("SELECT * FROM users").fetchall()
    return [{"id": u["id"], "name": u["name"]} for u in users]
""",
        "expected_high": False,
        "expected_keywords": ["SELECT *", "字段", "传输", "按需查询"],
        "description": "SELECT *查所有字段但只用了两个，浪费带宽和内存",
    },

    {
        "id": "PERF-M-003",
        "name": "热点数据无缓存",
        "difficulty": "medium",
        "category": "performance",
        "language": "python",
        "filename": "config_api.py",
        "code": """\
@app.get("/config")
def get_global_config():
    # 全局配置每次请求都从数据库读
    return db.execute("SELECT * FROM global_config").fetchall()
""",
        "expected_high": False,
        "expected_keywords": ["缓存", "Redis", "不变", "热点", "TTL"],
        "description": "几乎不变的配置数据每次请求都查库，应该缓存",
    },

    {
        "id": "PERF-M-004",
        "name": "大文件一次性读入内存",
        "difficulty": "medium",
        "category": "performance",
        "language": "python",
        "filename": "file_processor.py",
        "code": """\
def process_log_file(filepath):
    with open(filepath) as f:
        content = f.read()  # 可能是GB级文件
    lines = content.split('\n')
    for line in lines:
        process_line(line)
""",
        "expected_high": True,
        "expected_keywords": ["内存", "流式", "readline", "逐行", "generator"],
        "description": "大文件一次性读入内存，GB级文件会OOM",
    },

    {
        "id": "PERF-M-005",
        "name": "事务内包含外部HTTP调用",
        "difficulty": "medium",
        "category": "performance",
        "language": "python",
        "filename": "order.py",
        "code": """\
def create_order(user_id, items):
    with db.transaction():
        order = db.create_order(user_id, items)
        # 在事务内调用外部支付API
        payment = requests.post("https://payment.api/charge", json={...})
        if payment.ok:
            db.confirm_order(order.id)
""",
        "expected_high": True,
        "expected_keywords": ["事务", "外部调用", "锁", "超时", "HTTP"],
        "description": "数据库事务内包含外部HTTP调用，持有锁等待网络",
    },

    # ══════════════════════════════════════════════════════════════
    # PERFORMANCE — Hard (5)
    # ══════════════════════════════════════════════════════════════

    {
        "id": "PERF-H-001",
        "name": "分布式锁用错场景",
        "difficulty": "hard",
        "category": "performance",
        "language": "python",
        "filename": "inventory.py",
        "code": """\
def deduct_inventory(product_id, quantity):
    lock_key = "global_inventory_lock"  # 全局锁而非商品粒度锁
    with redis.lock(lock_key, timeout=30):
        stock = db.get_stock(product_id)
        if stock >= quantity:
            db.update_stock(product_id, stock - quantity)
""",
        "expected_high": False,
        "expected_keywords": ["全局锁", "粒度", "并发", "性能", "细粒度"],
        "description": "全局锁粒度太粗，所有商品串行处理，吞吐量极低",
    },

    {
        "id": "PERF-H-002",
        "name": "热key问题：单Redis key高并发",
        "difficulty": "hard",
        "category": "performance",
        "language": "python",
        "filename": "counter.py",
        "code": """\
def increment_view_count(article_id):
    redis.incr(f"views:{article_id}")

def get_trending():
    # 热门文章的views key会被每个请求读写
    articles = db.get_all_articles()
    return sorted(articles, key=lambda a: redis.get(f"views:{a['id']}"), reverse=True)
""",
        "expected_high": False,
        "expected_keywords": ["热key", "热点", "分片", "本地缓存", "限流"],
        "description": "热门文章的计数key成为Redis热key，可能打垮单节点",
    },

    {
        "id": "PERF-H-003",
        "name": "缓存击穿：大量并发重建缓存",
        "difficulty": "hard",
        "category": "performance",
        "language": "python",
        "filename": "product.py",
        "code": """\
def get_product(product_id):
    cached = redis.get(f"product:{product_id}")
    if cached:
        return json.loads(cached)
    product = db.get_product(product_id)
    redis.setex(f"product:{product_id}", 300, json.dumps(product))
    return product
""",
        "expected_high": False,
        "expected_keywords": ["缓存击穿", "互斥锁", "singleflight", "并发重建"],
        "description": "缓存过期时大量并发请求同时打到数据库重建缓存",
    },

    {
        "id": "PERF-H-004",
        "name": "GIL限制下的CPU密集型多线程",
        "difficulty": "hard",
        "category": "performance",
        "language": "python",
        "filename": "processor.py",
        "code": """\
import threading
def process_batch(items):
    threads = []
    for item in items:
        t = threading.Thread(target=cpu_intensive_process, args=(item,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
""",
        "expected_high": False,
        "expected_keywords": ["GIL", "多进程", "multiprocessing", "CPU密集", "线程"],
        "description": "Python GIL限制下CPU密集任务用多线程无法并行",
    },

    {
        "id": "PERF-H-005",
        "name": "死锁风险：嵌套事务不同顺序",
        "difficulty": "hard",
        "category": "performance",
        "language": "python",
        "filename": "transfer.py",
        "code": """\
def transfer(from_id, to_id, amount):
    with db.lock_row("accounts", from_id):
        with db.lock_row("accounts", to_id):
            # 并发时A->B和B->A会死锁
            debit(from_id, amount)
            credit(to_id, amount)
""",
        "expected_high": True,
        "expected_keywords": ["死锁", "deadlock", "顺序", "锁", "并发"],
        "description": "并发A->B和B->A转账会形成循环等待死锁",
    },

    # ══════════════════════════════════════════════════════════════
    # QUALITY — Easy (8)
    # ══════════════════════════════════════════════════════════════

    {
        "id": "QUAL-E-001",
        "name": "裸except吞掉所有异常",
        "difficulty": "easy",
        "category": "quality",
        "language": "python",
        "filename": "api.py",
        "code": """\
def get_user(user_id):
    try:
        return db.query_user(user_id)
    except:
        return None
""",
        "expected_high": False,
        "expected_keywords": ["裸except", "异常", "吞掉", "具体", "Exception"],
        "description": "裸except捕获所有异常包括KeyboardInterrupt，隐藏真实错误",
    },

    {
        "id": "QUAL-E-002",
        "name": "资源未关闭（文件/连接）",
        "difficulty": "easy",
        "category": "quality",
        "language": "python",
        "filename": "file_util.py",
        "code": """\
def read_config():
    f = open('config.json')
    data = json.load(f)
    return data  # 文件没有关闭
""",
        "expected_high": False,
        "expected_keywords": ["资源泄漏", "with", "close", "上下文管理器"],
        "description": "文件打开后没有关闭，长期运行会耗尽文件描述符",
    },

    {
        "id": "QUAL-E-003",
        "name": "可变默认参数",
        "difficulty": "easy",
        "category": "quality",
        "language": "python",
        "filename": "utils.py",
        "code": """\
def add_item(item, items=[]):
    items.append(item)
    return items
""",
        "expected_high": False,
        "expected_keywords": ["可变默认参数", "共享", "None", "陷阱"],
        "description": "列表作默认参数，所有调用共享同一个列表对象",
    },

    {
        "id": "QUAL-E-004",
        "name": "print调试代码留在生产",
        "difficulty": "easy",
        "category": "quality",
        "language": "python",
        "filename": "payment.py",
        "code": """\
def process_payment(card_number, amount):
    print(f"Processing payment: card={card_number}, amount={amount}")
    result = payment_gateway.charge(card_number, amount)
    print(f"Payment result: {result}")
    return result
""",
        "expected_high": True,
        "expected_keywords": ["print", "日志", "敏感", "卡号", "logging"],
        "description": "print输出了完整卡号，且生产代码不应用print",
    },

    {
        "id": "QUAL-E-005",
        "name": "魔法数字",
        "difficulty": "easy",
        "category": "quality",
        "language": "python",
        "filename": "discount.py",
        "code": """\
def calculate_discount(price, user_level):
    if user_level == 1:
        return price * 0.9
    elif user_level == 2:
        return price * 0.8
    elif user_level >= 3:
        return price * 0.7
""",
        "expected_high": False,
        "expected_keywords": ["魔法数字", "常量", "可读性", "枚举"],
        "description": "大量魔法数字，含义不明，难以维护",
    },

    {
        "id": "QUAL-E-006",
        "name": "没有输入验证",
        "difficulty": "easy",
        "category": "quality",
        "language": "python",
        "filename": "api.py",
        "code": """\
@app.post("/register")
def register(username: str, email: str, age: int):
    user = User(username=username, email=email, age=age)
    db.add(user)
    db.commit()
""",
        "expected_high": False,
        "expected_keywords": ["验证", "validation", "格式", "边界", "sanitize"],
        "description": "没有验证邮箱格式、年龄范围、用户名长度等",
    },

    {
        "id": "QUAL-E-007",
        "name": "全局可变状态",
        "difficulty": "easy",
        "category": "quality",
        "language": "python",
        "filename": "app.py",
        "code": """\
current_user = None
request_count = 0

def handle_request(user):
    global current_user, request_count
    current_user = user
    request_count += 1
""",
        "expected_high": True,
        "expected_keywords": ["全局变量", "并发", "线程安全", "竞争"],
        "description": "全局可变状态在多线程/多进程下会产生竞争条件",
    },

    {
        "id": "QUAL-E-008",
        "name": "硬删除无软删除",
        "difficulty": "easy",
        "category": "quality",
        "language": "python",
        "filename": "user.py",
        "code": """\
def delete_user(user_id):
    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    db.commit()
    return True
""",
        "expected_high": False,
        "expected_keywords": ["软删除", "deleted_at", "is_deleted", "恢复", "审计"],
        "description": "物理删除无法恢复，建议软删除",
    },

    # ══════════════════════════════════════════════════════════════
    # QUALITY — Medium (4)
    # ══════════════════════════════════════════════════════════════

    {
        "id": "QUAL-M-001",
        "name": "异步函数忘记await",
        "difficulty": "medium",
        "category": "quality",
        "language": "python",
        "filename": "service.py",
        "code": """\
async def get_user_data(user_id):
    user = get_user(user_id)  # 忘记await，返回coroutine对象
    if not user:
        return None
    return user.data
""",
        "expected_high": False,
        "expected_keywords": ["await", "协程", "coroutine", "异步"],
        "description": "忘记await导致返回协程对象而非实际结果",
    },

    {
        "id": "QUAL-M-002",
        "name": "循环引用导致内存泄漏",
        "difficulty": "medium",
        "category": "quality",
        "language": "python",
        "filename": "node.py",
        "code": """\
class Node:
    def __init__(self, value):
        self.value = value
        self.children = []
        self.parent = None

    def add_child(self, child):
        child.parent = self
        self.children.append(child)
""",
        "expected_high": False,
        "expected_keywords": ["循环引用", "weakref", "内存", "gc"],
        "description": "父子互相引用，垃圾回收器可能无法及时回收",
    },

    {
        "id": "QUAL-M-003",
        "name": "浮点数直接比较",
        "difficulty": "medium",
        "category": "quality",
        "language": "python",
        "filename": "payment.py",
        "code": """\
def validate_payment(amount):
    tax = amount * 0.1
    total = amount + tax
    if total == amount * 1.1:  # 浮点数直接比较
        return True
    return False
""",
        "expected_high": False,
        "expected_keywords": ["浮点", "精度", "Decimal", "epsilon", "math.isclose"],
        "description": "浮点数直接==比较，金融场景应使用Decimal",
    },

    {
        "id": "QUAL-M-004",
        "name": "未处理的Promise拒绝",
        "difficulty": "medium",
        "category": "quality",
        "language": "javascript",
        "filename": "api.js",
        "code": """\
async function fetchData(url) {
    const resp = await fetch(url);
    const data = await resp.json();
    return data;
}

// 调用时没有catch
fetchData('/api/users').then(data => console.log(data));
""",
        "expected_high": False,
        "expected_keywords": ["catch", "错误处理", "Promise", "拒绝", "unhandled"],
        "description": "Promise拒绝未处理，错误被静默忽略",
    },

    # ══════════════════════════════════════════════════════════════
    # QUALITY — Hard (3)
    # ══════════════════════════════════════════════════════════════

    {
        "id": "QUAL-H-001",
        "name": "分布式事务数据不一致",
        "difficulty": "hard",
        "category": "quality",
        "language": "python",
        "filename": "order_service.py",
        "code": """\
def create_order(user_id, items):
    order = order_db.create(user_id, items)
    inventory_service.deduct(items)  # 如果这步失败，订单已创建
    payment_service.charge(user_id)  # 如果这步失败，库存已扣减
    return order
""",
        "expected_high": True,
        "expected_keywords": ["分布式事务", "补偿", "Saga", "幂等", "回滚"],
        "description": "跨服务操作无事务保证，任一步失败导致数据不一致",
    },

    {
        "id": "QUAL-H-002",
        "name": "幂等性缺失",
        "difficulty": "hard",
        "category": "quality",
        "language": "python",
        "filename": "payment.py",
        "code": """\
@app.post("/payments/charge")
def charge(user_id: int, amount: float):
    # 重复调用会重复扣费
    transaction = payment_gateway.charge(user_id, amount)
    db.save_transaction(transaction)
    return transaction
""",
        "expected_high": True,
        "expected_keywords": ["幂等", "idempotent", "重试", "重复", "去重"],
        "description": "支付接口无幂等保护，网络重试会导致重复扣费",
    },

    {
        "id": "QUAL-H-003",
        "name": "类型混淆导致静默错误",
        "difficulty": "hard",
        "category": "quality",
        "language": "javascript",
        "filename": "calc.js",
        "code": """\
function calculateTotal(items) {
    return items.reduce((sum, item) => sum + item.price, 0);
}
// 如果price是字符串"10.99"，结果变成字符串拼接
""",
        "expected_high": False,
        "expected_keywords": ["类型", "Number()", "parseFloat", "字符串", "验证"],
        "description": "price若为字符串会变成字符串拼接而非数字加法",
    },

    # ══════════════════════════════════════════════════════════════
    # CLEAN CODE — 干净代码（应该高分）(15)
    # ══════════════════════════════════════════════════════════════

    {
        "id": "CLEAN-001",
        "name": "规范的参数化查询",
        "difficulty": "easy",
        "category": "clean",
        "language": "python",
        "filename": "user_repo.py",
        "code": """\
def find_user(username: str, password_hash: str) -> dict | None:
    query = "SELECT id, username, email FROM users WHERE username=? AND password_hash=?"
    row = conn.execute(query, (username, password_hash)).fetchone()
    return dict(row) if row else None
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "参数化查询、只查需要的字段、有类型注解，应给高分",
    },

    {
        "id": "CLEAN-002",
        "name": "规范的密码哈希",
        "difficulty": "easy",
        "category": "clean",
        "language": "python",
        "filename": "auth.py",
        "code": """\
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "bcrypt哈希密码，正确的密码存储方式，应给高分",
    },

    {
        "id": "CLEAN-003",
        "name": "完善的输入验证",
        "difficulty": "easy",
        "category": "clean",
        "language": "python",
        "filename": "validator.py",
        "code": """\
import re
from dataclasses import dataclass

@dataclass
class UserInput:
    username: str
    email: str
    age: int

    def __post_init__(self):
        if not 3 <= len(self.username) <= 20:
            raise ValueError("Username must be 3-20 characters")
        if not re.match(r'^[a-zA-Z0-9_]+$', self.username):
            raise ValueError("Username can only contain letters, numbers, underscore")
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', self.email):
            raise ValueError("Invalid email format")
        if not 13 <= self.age <= 120:
            raise ValueError("Age must be between 13 and 120")
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "完善的输入验证，明确的错误信息，应给高分",
    },

    {
        "id": "CLEAN-004",
        "name": "规范的异步HTTP请求",
        "difficulty": "easy",
        "category": "clean",
        "language": "python",
        "filename": "fetcher.py",
        "code": """\
import asyncio
import aiohttp

async def fetch_all(urls: list[str]) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_one(session, url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

async def fetch_one(session: aiohttp.ClientSession, url: str) -> dict:
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
        resp.raise_for_status()
        return await resp.json()
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "正确使用async/await，并发请求，有超时设置，应给高分",
    },

    {
        "id": "CLEAN-005",
        "name": "规范的分页查询",
        "difficulty": "easy",
        "category": "clean",
        "language": "python",
        "filename": "api.py",
        "code": """\
from fastapi import Query

@app.get("/posts")
def list_posts(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)):
    offset = (page - 1) * size
    total = db.count_posts()
    posts = db.query_posts(limit=size, offset=offset)
    return {
        "items": posts,
        "total": total,
        "page": page,
        "pages": (total + size - 1) // size,
    }
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "规范分页，有参数校验，返回元信息，应给高分",
    },

    {
        "id": "CLEAN-006",
        "name": "规范的JWT生成与验证",
        "difficulty": "easy",
        "category": "clean",
        "language": "python",
        "filename": "jwt_util.py",
        "code": """\
import jwt
from datetime import datetime, timedelta, timezone
import os

SECRET = os.environ['JWT_SECRET']

def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

def verify_token(token: str) -> dict:
    return jwt.decode(token, SECRET, algorithms=["HS256"])
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "JWT有过期时间，从环境变量读密钥，应给高分",
    },

    {
        "id": "CLEAN-007",
        "name": "规范的错误处理",
        "difficulty": "easy",
        "category": "clean",
        "language": "python",
        "filename": "service.py",
        "code": """\
class UserNotFoundError(Exception):
    pass

class PermissionDeniedError(Exception):
    pass

def get_user_profile(requester_id: int, target_id: int) -> dict:
    user = db.get_user(target_id)
    if not user:
        raise UserNotFoundError(f"User {target_id} not found")
    if user.is_private and requester_id != target_id:
        raise PermissionDeniedError("Cannot view private profile")
    return user.to_dict()
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "自定义异常类，明确的错误语义，应给高分",
    },

    {
        "id": "CLEAN-008",
        "name": "TypeScript类型安全的API调用",
        "difficulty": "easy",
        "category": "clean",
        "language": "typescript",
        "filename": "api.ts",
        "code": """\
interface User {
  id: number;
  username: string;
  email: string;
}

async function fetchUser(userId: number): Promise<User> {
  const resp = await fetch(`/api/users/${userId}`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch user: ${resp.status}`);
  }
  return resp.json() as Promise<User>;
}
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "TypeScript类型安全，错误处理完整，应给高分",
    },

    {
        "id": "CLEAN-009",
        "name": "规范的配置管理",
        "difficulty": "easy",
        "category": "clean",
        "language": "python",
        "filename": "settings.py",
        "code": """\
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    jwt_expire_hours: int = 1
    max_upload_size_mb: int = 10
    debug: bool = False

    class Config:
        env_file = '.env'

settings = Settings()
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "用pydantic管理配置，有类型校验和默认值，应给高分",
    },

    {
        "id": "CLEAN-010",
        "name": "规范的文件上传处理",
        "difficulty": "easy",
        "category": "clean",
        "language": "python",
        "filename": "upload.py",
        "code": """\
import os, uuid, mimetypes

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif"}
MAX_SIZE = 5 * 1024 * 1024  # 5MB

def save_upload(file_content: bytes, original_name: str, content_type: str) -> str:
    if content_type not in ALLOWED_TYPES:
        raise ValueError(f"Unsupported file type: {content_type}")
    if len(file_content) > MAX_SIZE:
        raise ValueError("File too large")
    ext = mimetypes.guess_extension(content_type)
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join("/var/uploads", filename)
    with open(path, "wb") as f:
        f.write(file_content)
    return filename
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "文件类型白名单、大小限制、随机文件名，应给高分",
    },

    {
        "id": "CLEAN-011",
        "name": "规范的速率限制实现",
        "difficulty": "easy",
        "category": "clean",
        "language": "python",
        "filename": "rate_limit.py",
        "code": """\
import redis
import time

def is_rate_limited(user_id: str, limit: int = 100, window: int = 60) -> bool:
    key = f"ratelimit:{user_id}:{int(time.time()) // window}"
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, window)
    return count > limit
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "滑动窗口速率限制，用Redis原子操作，应给高分",
    },

    {
        "id": "CLEAN-012",
        "name": "规范的数据库迁移",
        "difficulty": "easy",
        "category": "clean",
        "language": "python",
        "filename": "migration_001.py",
        "code": """\
def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(50), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_users_email', 'users', ['email'])

def downgrade():
    op.drop_table('users')
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "规范的数据库迁移，有upgrade和downgrade，创建了索引",
    },

    {
        "id": "CLEAN-013",
        "name": "规范的健康检查接口",
        "difficulty": "easy",
        "category": "clean",
        "language": "python",
        "filename": "health.py",
        "code": """\
@app.get("/health")
async def health_check():
    checks = {}
    try:
        await db.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "完整的健康检查，检查各依赖状态，应给高分",
    },

    {
        "id": "CLEAN-014",
        "name": "规范的日志记录",
        "difficulty": "easy",
        "category": "clean",
        "language": "python",
        "filename": "logging_setup.py",
        "code": """\
import logging
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "timestamp": self.formatTime(record),
        })

logger = logging.getLogger(__name__)
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "结构化JSON日志，有标准字段，应给高分",
    },

    {
        "id": "CLEAN-015",
        "name": "规范的工具函数",
        "difficulty": "easy",
        "category": "clean",
        "language": "python",
        "filename": "utils.py",
        "code": """\
import re
from datetime import datetime, timezone

def validate_email(email: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def to_utc_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

def paginate(items: list, page: int, size: int = 20) -> dict:
    if page < 1:
        raise ValueError("page must be >= 1")
    total = len(items)
    start = (page - 1) * size
    return {
        "items": items[start:start + size],
        "total": total,
        "page": page,
        "pages": (total + size - 1) // size,
    }
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "工具函数有类型注解、输入验证、边界处理，应给高分",
    },

    # ══════════════════════════════════════════════════════════════
    # EDGE CASES — 边界/陷阱用例（考验误报控制）(15)
    # ══════════════════════════════════════════════════════════════

    {
        "id": "EDGE-001",
        "name": "【误报陷阱】ORM查询看起来像SQL注入",
        "difficulty": "hard",
        "category": "edge",
        "language": "python",
        "filename": "repo.py",
        "code": """\
def search_users(keyword: str):
    # 使用ORM，参数化安全
    return db.session.query(User).filter(
        User.username.ilike(f"%{keyword}%")
    ).all()
""",
        "expected_high": False,
        "expected_keywords": ["ORM", "ilike", "参数化"],
        "description": "ORM的ilike方法是参数化安全的，不应报SQL注入",
    },

    {
        "id": "EDGE-002",
        "name": "【误报陷阱】subprocess安全使用列表参数",
        "difficulty": "hard",
        "category": "edge",
        "language": "python",
        "filename": "ffmpeg.py",
        "code": """\
import subprocess
def convert_video(input_path: str, output_path: str):
    # 使用列表参数，无shell注入风险
    subprocess.run(
        ["ffmpeg", "-i", input_path, "-c:v", "h264", output_path],
        check=True, capture_output=True
    )
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "subprocess使用列表参数而非shell=True，是安全的",
    },

    {
        "id": "EDGE-003",
        "name": "【误报陷阱】eval用于安全的数学计算器",
        "difficulty": "hard",
        "category": "edge",
        "language": "python",
        "filename": "math_eval.py",
        "code": """\
import ast
import operator

SAFE_OPS = {ast.Add: operator.add, ast.Sub: operator.sub,
            ast.Mult: operator.mul, ast.Div: operator.truediv}

def safe_eval(expr: str) -> float:
    tree = ast.parse(expr, mode='eval')
    return _eval(tree.body)

def _eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in SAFE_OPS:
        return SAFE_OPS[type(node.op)](_eval(node.left), _eval(node.right))
    raise ValueError("Unsupported expression")
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "用AST实现的安全数学求值器，不是危险的eval",
    },

    {
        "id": "EDGE-004",
        "name": "【误报陷阱】random用于非安全场景",
        "difficulty": "hard",
        "category": "edge",
        "language": "python",
        "filename": "game.py",
        "code": """\
import random
def get_daily_challenge():
    # 游戏功能，不涉及安全
    challenges = ["challenge_a", "challenge_b", "challenge_c"]
    return random.choice(challenges)
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "random用于游戏逻辑，非安全场景，不应报问题",
    },

    {
        "id": "EDGE-005",
        "name": "【误报陷阱】内部管理员工具硬编码配置",
        "difficulty": "hard",
        "category": "edge",
        "language": "python",
        "filename": "dev_tools.py",
        "code": """\
# 仅用于本地开发环境的测试工具
TEST_DB_URL = "sqlite:///test.db"
TEST_USER = "testuser"
TEST_PASSWORD = "testpass123"  # 仅测试用
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "明确标注为测试用途的配置，误报风险",
    },

    {
        "id": "EDGE-006",
        "name": "【边界】空PR：只改了注释",
        "difficulty": "medium",
        "category": "edge",
        "language": "python",
        "filename": "utils.py",
        "code": """\
# 修改前：
# def calculate(x, y):
#     return x + y

# 修改后：更新注释和文档字符串
def calculate(x: float, y: float) -> float:
    \"\"\"
    Calculate the sum of two numbers.

    Args:
        x: First number
        y: Second number

    Returns:
        Sum of x and y
    \"\"\"
    return x + y
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "只改了注释和类型注解，应给高分或APPROVE",
    },

    {
        "id": "EDGE-007",
        "name": "【边界】代码看起来有问题但有上下文",
        "difficulty": "hard",
        "category": "edge",
        "language": "python",
        "filename": "admin_only.py",
        "code": """\
# 注意：此函数只在管理员控制台CLI中调用，不对外暴露API
def force_reset_user(user_id: int):
    \"\"\"管理员强制重置用户，仅内部使用。\"\"\"
    db.execute("UPDATE users SET password_hash=? WHERE id=?",
               (hash_password("TempPass123!"), user_id))
    db.execute("INSERT INTO audit_log VALUES (?, 'force_reset', ?)",
               (user_id, datetime.now()))
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "有审计日志、有注释说明内部使用，应理解上下文",
    },

    {
        "id": "EDGE-008",
        "name": "【边界】TypeScript严格模式下的类型体操",
        "difficulty": "hard",
        "category": "edge",
        "language": "typescript",
        "filename": "types.ts",
        "code": """\
type DeepReadonly<T> = {
    readonly [P in keyof T]: T[P] extends object ? DeepReadonly<T[P]> : T[P];
};

type ApiResponse<T> = {
    data: T;
    error: string | null;
    timestamp: number;
};

function assertNever(x: never): never {
    throw new Error('Unexpected value: ' + x);
}
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "TypeScript高级类型，是良好实践，不应报问题",
    },

    {
        "id": "EDGE-009",
        "name": "【边界】混合：好代码中有一个隐藏问题",
        "difficulty": "hard",
        "category": "edge",
        "language": "python",
        "filename": "auth_service.py",
        "code": """\
import bcrypt
import jwt
import os
from datetime import datetime, timedelta, timezone

SECRET = os.environ.get('JWT_SECRET', 'fallback-dev-secret')  # 有默认值问题

def login(username: str, password: str) -> str | None:
    user = db.get_user_by_username(username)
    if not user:
        return None
    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return None
    return jwt.encode({
        "sub": user.id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }, SECRET, algorithm="HS256")
""",
        "expected_high": False,
        "expected_keywords": ["默认值", "fallback", "环境变量", "生产"],
        "description": "整体代码很好，但SECRET有不安全的默认值，应只报这一个问题",
    },

    {
        "id": "EDGE-010",
        "name": "【边界】Go语言代码",
        "difficulty": "medium",
        "category": "edge",
        "language": "go",
        "filename": "handler.go",
        "code": """\
func GetUser(w http.ResponseWriter, r *http.Request) {
    userID := r.URL.Query().Get("id")
    // 未验证userID是否为数字
    query := fmt.Sprintf("SELECT * FROM users WHERE id = %s", userID)
    rows, err := db.Query(query)
    if err != nil {
        http.Error(w, err.Error(), 500)
        return
    }
    defer rows.Close()
}
""",
        "expected_high": True,
        "expected_keywords": ["SQL", "注入", "Sprintf", "参数化"],
        "description": "Go代码的SQL注入，测试跨语言识别能力",
    },

    {
        "id": "EDGE-011",
        "name": "【边界】大量改动但都是干净代码",
        "difficulty": "medium",
        "category": "edge",
        "language": "python",
        "filename": "refactored_service.py",
        "code": """\
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class CreateUserRequest:
    username: str
    email: str
    password: str

    def validate(self):
        if len(self.username) < 3:
            raise ValueError("Username too short")
        if '@' not in self.email:
            raise ValueError("Invalid email")
        if len(self.password) < 8:
            raise ValueError("Password too short")

class UserService:
    def __init__(self, db, cache):
        self._db = db
        self._cache = cache

    def create_user(self, req: CreateUserRequest) -> dict:
        req.validate()
        if self._db.user_exists(req.email):
            raise ValueError("Email already registered")
        user = self._db.create_user(
            username=req.username,
            email=req.email,
            password_hash=hash_password(req.password)
        )
        logger.info("User created", extra={"user_id": user.id})
        return user.to_dict()
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "重构后的干净代码，大量改动但应给高分",
    },

    {
        "id": "EDGE-012",
        "name": "【边界】依赖注入正确实现",
        "difficulty": "medium",
        "category": "edge",
        "language": "python",
        "filename": "dependencies.py",
        "code": """\
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_jwt(token)
        user = await db.get_user(payload["sub"])
        if not user:
            raise HTTPException(status_code=401)
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "FastAPI依赖注入+JWT验证，是正确实现，应给高分",
    },

    {
        "id": "EDGE-013",
        "name": "【边界】看起来硬编码但实际是常量",
        "difficulty": "medium",
        "category": "edge",
        "language": "python",
        "filename": "constants.py",
        "code": """\
# 业务常量，非密钥
MAX_RETRY_ATTEMPTS = 3
DEFAULT_PAGE_SIZE = 20
MAX_FILE_SIZE_MB = 10
SUPPORTED_LANGUAGES = ["python", "javascript", "typescript", "go"]
FREE_TIER_MONTHLY_CALLS = 100
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "业务常量文件，不是安全凭证，不应报问题",
    },

    {
        "id": "EDGE-014",
        "name": "【误报陷阱】格式化字符串用于日志非SQL",
        "difficulty": "medium",
        "category": "edge",
        "language": "python",
        "filename": "logger.py",
        "code": """\
def log_request(method: str, path: str, status: int, duration_ms: float):
    msg = f"[{method}] {path} -> {status} ({duration_ms:.1f}ms)"
    logger.info(msg)
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "f-string用于日志格式化，非SQL，不应报注入问题",
    },

    {
        "id": "EDGE-015",
        "name": "【边界】复杂但正确的并发控制",
        "difficulty": "hard",
        "category": "edge",
        "language": "python",
        "filename": "inventory.py",
        "code": """\
import asyncio

class InventoryService:
    def __init__(self):
        self._locks: dict[int, asyncio.Lock] = {}

    def _get_lock(self, product_id: int) -> asyncio.Lock:
        if product_id not in self._locks:
            self._locks[product_id] = asyncio.Lock()
        return self._locks[product_id]

    async def deduct(self, product_id: int, qty: int) -> bool:
        async with self._get_lock(product_id):
            stock = await db.get_stock(product_id)
            if stock < qty:
                return False
            await db.update_stock(product_id, stock - qty)
            return True
""",
        "expected_high": False,
        "expected_keywords": [],
        "description": "按商品粒度加锁，正确的并发控制，应给高分",
    },
]

# ── 统计 ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    from collections import Counter
    difficulties = Counter(c["difficulty"] for c in CASES)
    categories = Counter(c["category"] for c in CASES)
    languages = Counter(c["language"] for c in CASES)
    expected_high = sum(1 for c in CASES if c["expected_high"])

    print(f"总用例数：{len(CASES)}")
    print(f"难度分布：{dict(difficulties)}")
    print(f"类别分布：{dict(categories)}")
    print(f"语言分布：{dict(languages)}")
    print(f"预期HIGH问题：{expected_high} / 预期无HIGH：{len(CASES) - expected_high}")
