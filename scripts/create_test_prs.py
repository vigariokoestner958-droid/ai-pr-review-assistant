"""Create 10 new test PRs: 5 easy / 3 medium / 2 hard."""
import requests, base64, time, json
import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv('GITHUB_TOKEN', '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')
H = {'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
USERNAME = 'vigariokoestner958-droid'
REPO = 'pr-review-test'
BASE = f'https://api.github.com/repos/{USERNAME}/{REPO}'

def b64(s): return base64.b64encode(s.encode()).decode()

def get_main_sha():
    r = requests.get(f'{BASE}/git/ref/heads/main', headers=H)
    return r.json()['object']['sha']

def create_branch(name, sha):
    r = requests.post(f'{BASE}/git/refs', headers=H,
                      json={'ref': f'refs/heads/{name}', 'sha': sha})
    return r.status_code in (200, 201, 422)

def push_file(branch, path, content, msg):
    r = requests.get(f'{BASE}/contents/{path}', headers=H, params={'ref': branch})
    body = {'message': msg, 'content': b64(content), 'branch': branch}
    if r.status_code == 200:
        body['sha'] = r.json()['sha']
    r = requests.put(f'{BASE}/contents/{path}', headers=H, json=body)
    return r.status_code in (200, 201)

def create_pr(title, branch, body=''):
    r = requests.post(f'{BASE}/pulls', headers=H,
                      json={'title': title, 'head': branch, 'base': 'main', 'body': body})
    if r.status_code in (200, 201):
        d = r.json()
        return d['number'], d['html_url']
    print(f'  PR error {r.status_code}: {r.json().get("errors", r.text)[:120]}')
    return None, None

# ─────────────────────────────────────────────────────────────────
# 10 个测试用例
# ─────────────────────────────────────────────────────────────────
CASES = [
  # EASY 1
  ('test/e1-sqli', 'feat: add admin search endpoint', 'admin/search.py', '''\
import sqlite3

def search_users(keyword):
    conn = sqlite3.connect("users.db")
    sql = "SELECT id, username, email FROM users WHERE username LIKE '%" + keyword + "%'"
    return conn.execute(sql).fetchall()
''', 'SQL注入：字符串拼接到查询'),

  # EASY 2
  ('test/e2-hardkey', 'feat: add payment module', 'payment/client.py', '''\
import requests

STRIPE_SECRET = "sk_live_4eC39HqLyjWDarjtT1zdp7dc"

def charge(amount, token):
    return requests.post("https://api.stripe.com/v1/charges",
        auth=(STRIPE_SECRET, ""),
        data={"amount": amount, "currency": "usd", "source": token}
    ).json()
''', '硬编码生产密钥'),

  # EASY 3
  ('test/e3-xss', 'feat: add comment rendering', 'static/comments.js', '''\
function renderComments(comments) {
    let html = "";
    comments.forEach(c => {
        // 直接用 innerHTML 插入用户内容
        html += "<div class=\\"comment\\">" + c.body + "</div>";
    });
    document.getElementById("feed").innerHTML = html;
}
''', 'XSS：innerHTML直接插入用户输入'),

  # EASY 4
  ('test/e4-plainpwd', 'feat: add user signup', 'user/signup.py', '''\
import sqlite3

def signup(username, password, email):
    conn = sqlite3.connect("users.db")
    conn.execute(
        "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
        (username, password, email)   # 密码明文存储
    )
    conn.commit()
    print(f"[DEBUG] New user: {username} pass={password}")
''', '密码明文存储并打印到日志'),

  # EASY 5
  ('test/e5-noauth', 'feat: add admin delete API', 'api/admin.py', '''\
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

@app.route("/admin/delete", methods=["POST"])
def delete_user():
    # 无任何鉴权
    uid = request.json["user_id"]
    conn = sqlite3.connect("users.db")
    conn.execute("DELETE FROM users WHERE id=?", (uid,))
    conn.commit()
    return jsonify({"deleted": uid})
''', '管理接口无身份验证'),

  # MEDIUM 1
  ('test/m1-n1query', 'feat: show post list with author info', 'blog/views.py', '''\
from models import Post, User

def get_feed():
    posts = Post.query.all()
    result = []
    for post in posts:
        author = User.query.get(post.author_id)   # N+1 查询
        result.append({
            "title": post.title,
            "author": author.username if author else "?",
        })
    return result
''', 'N+1查询问题'),

  # MEDIUM 2
  ('test/m2-race', 'feat: implement balance transfer', 'finance/transfer.py', '''\
import sqlite3, time

def transfer(from_id, to_id, amount):
    conn = sqlite3.connect("bank.db")
    bal = conn.execute("SELECT balance FROM accounts WHERE id=?", (from_id,)).fetchone()[0]
    if bal < amount:
        return False
    time.sleep(0.01)   # 模拟延迟，竞态窗口
    conn.execute("UPDATE accounts SET balance=balance-? WHERE id=?", (amount, from_id))
    conn.execute("UPDATE accounts SET balance=balance+? WHERE id=?", (amount, to_id))
    conn.commit()
    return True
''', 'TOCTOU竞态+无事务保护'),

  # MEDIUM 3
  ('test/m3-pathtraversal', 'feat: add file download API', 'api/files.py', '''\
import os
from flask import Flask, send_file, request, abort

app = Flask(__name__)
UPLOAD_DIR = "/var/app/uploads"

@app.route("/download")
def download():
    name = request.args.get("file", "")
    path = os.path.join(UPLOAD_DIR, name)   # 未规范化路径
    if not os.path.exists(path):
        abort(404)
    return send_file(path)
''', '路径拼接未做规范化，可能路径遍历'),

  # HARD 1
  ('test/h1-jwt-none', 'feat: implement JWT verification', 'auth/jwt_verify.py', '''\
import json, base64, hmac, hashlib

SECRET = "super-secret"

def verify_token(token: str):
    parts = token.split(".")
    if len(parts) != 3:
        return None
    h64, p64, sig = parts
    header = json.loads(base64.b64decode(h64 + "=="))
    alg = header.get("alg", "HS256")
    if alg == "none":           # alg:none 攻击：跳过验签
        return json.loads(base64.b64decode(p64 + "=="))
    expected = base64.b64encode(
        hmac.new(SECRET.encode(), f"{h64}.{p64}".encode(), hashlib.sha256).digest()
    ).decode().rstrip("=")
    if sig != expected:
        return None
    return json.loads(base64.b64decode(p64 + "=="))
''', 'JWT alg:none绕过签名验证'),

  # HARD 2
  ('test/h2-pickle-rce', 'feat: add Redis session cache', 'cache/session.py', '''\
import pickle, redis, base64

r = redis.Redis(host="localhost", port=6379, db=0)

def save_session(sid, data):
    r.setex(f"sess:{sid}", 3600, pickle.dumps(data))

def load_session(sid):
    raw = r.get(f"sess:{sid}")
    return pickle.loads(raw) if raw else None   # 反序列化Redis数据

def load_from_cookie(cookie):
    # 直接反序列化用户cookie — 可导致RCE
    return pickle.loads(base64.b64decode(cookie))
''', 'pickle反序列化用户输入，可RCE'),
]

# ── 执行 ──────────────────────────────────────────────────────────
main_sha = get_main_sha()
print(f'Main SHA: {main_sha[:8]}\n')

created = []
for branch, title, filename, code, desc in CASES:
    print(f'[{branch}] {title}')
    create_branch(branch, main_sha)
    time.sleep(0.5)
    ok = push_file(branch, filename, code, f'add {filename}')
    print(f'  push: {"ok" if ok else "FAIL"}')
    time.sleep(0.5)
    num, url = create_pr(title, branch, f'测试用例：{desc}')
    if num:
        print(f'  PR #{num}: {url}')
        created.append({'number': num, 'url': url, 'title': title, 'desc': desc})
    time.sleep(1.5)

print(f'\n=== Created {len(created)}/10 PRs ===')
for c in created:
    print(f'  #{c["number"]} {c["url"]}')

with open('scripts/test_prs_new.json', 'w', encoding='utf-8') as f:
    json.dump(created, f, ensure_ascii=False, indent=2)
print('Saved to scripts/test_prs_new.json')
