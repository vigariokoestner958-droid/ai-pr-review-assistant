"""Create multiple test PRs with different vulnerability scenarios."""
import requests, os, base64, time
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('GITHUB_TOKEN')
H = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
username = requests.get('https://api.github.com/user', headers=H).json()['login']
repo = 'pr-review-test'
BASE = f'https://api.github.com/repos/{username}/{repo}'

def b64(s): return base64.b64encode(s.encode()).decode()

def get_sha(path, branch='main'):
    r = requests.get(f'{BASE}/contents/{path}', headers=H, params={'ref': branch})
    return r.json().get('sha')

def put_file(path, content, message, branch, sha=None):
    body = {'message': message, 'content': b64(content), 'branch': branch}
    if sha: body['sha'] = sha
    r = requests.put(f'{BASE}/contents/{path}', headers=H, json=body)
    return r.status_code

def create_branch(name):
    main_sha = requests.get(f'{BASE}/git/ref/heads/main', headers=H).json()['object']['sha']
    r = requests.post(f'{BASE}/git/refs', headers=H,
        json={'ref': f'refs/heads/{name}', 'sha': main_sha})
    return r.status_code

def create_pr(title, body, branch):
    r = requests.post(f'{BASE}/pulls', headers=H,
        json={'title': title, 'body': body, 'head': branch, 'base': 'main'})
    d = r.json()
    return d.get('html_url', f'ERROR: {d}')

# ─────────────────────────────────────────────────────────────────────────────
# PR 2: JavaScript 前端 XSS + 不安全 eval
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== PR 2: Frontend XSS ===')
create_branch('feature/frontend-search')
time.sleep(1)

search_js = '''// Search feature
function renderResults(query) {
    const container = document.getElementById('results');
    // XSS vulnerability: directly injecting user input into innerHTML
    container.innerHTML = `<h2>Results for: ${query}</h2>`;

    // Dangerous eval usage
    const filter = document.getElementById('filter').value;
    const filterFn = eval(`(item) => ${filter}`);
    return results.filter(filterFn);
}

function loadUserConfig(configStr) {
    // Prototype pollution
    const config = JSON.parse(configStr);
    Object.assign({}, config);
    Object.keys(config).forEach(key => {
        window.__config[key] = config[key];
    });
}

function fetchUserData(userId) {
    // No input validation
    return fetch(`/api/users/${userId}/data`)
        .then(r => r.json())
        .then(data => {
            localStorage.setItem('userData', JSON.stringify(data));
            // Sensitive data stored in localStorage
            localStorage.setItem('authToken', data.token);
        });
}
'''

put_file('static/search.js', search_js, 'feat: add search and user config', 'feature/frontend-search')
time.sleep(1)
url2 = create_pr(
    'feat: add frontend search and user config loader',
    'Adds search result rendering and dynamic user config loading from server.',
    'feature/frontend-search'
)
print('PR 2:', url2)

time.sleep(2)

# ─────────────────────────────────────────────────────────────────────────────
# PR 3: 数据库操作 + 密码明文存储
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== PR 3: Database + Password Storage ===')
create_branch('feature/user-database')
time.sleep(1)

db_py = '''import sqlite3
import os

def init_db():
    conn = sqlite3.connect('app.db')
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,  -- stored as plaintext
            email TEXT,
            is_admin INTEGER DEFAULT 0
        )
    """)
    # Default admin with hardcoded password
    conn.execute("INSERT OR IGNORE INTO users VALUES (1, 'admin', 'admin123', 'admin@app.com', 1)")
    conn.commit()

def find_user(username, password):
    conn = sqlite3.connect('app.db')
    # SQL injection + plaintext password comparison
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    return conn.execute(query).fetchone()

def update_user_email(user_id, new_email):
    conn = sqlite3.connect('app.db')
    # No ownership check - any user can update any email
    conn.execute(f"UPDATE users SET email='{new_email}' WHERE id={user_id}")
    conn.commit()
    return True

def get_user_by_email(email):
    conn = sqlite3.connect('app.db')
    # Returns full row including password
    return conn.execute(f"SELECT * FROM users WHERE email='{email}'").fetchone()

def delete_user(user_id):
    conn = sqlite3.connect('app.db')
    # No auth check, no soft delete
    conn.execute(f"DELETE FROM users WHERE id={user_id}")
    conn.commit()
    print(f"Deleted user {user_id}")
'''

put_file('database.py', db_py, 'feat: add database module', 'feature/user-database')
time.sleep(1)
url3 = create_pr(
    'feat: add user database module',
    'Adds SQLite database with user management: create, find, update, delete.',
    'feature/user-database'
)
print('PR 3:', url3)

time.sleep(2)

# ─────────────────────────────────────────────────────────────────────────────
# PR 4: 性能问题 N+1 查询 + 内存泄露
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== PR 4: Performance Issues ===')
create_branch('feature/post-service')
time.sleep(1)

post_service = '''import time
from database import find_user

# Global cache that never gets cleared - memory leak
_cache = {}
_connections = []

def get_posts_with_authors(post_ids):
    posts = []
    for post_id in post_ids:
        # N+1 query: one DB call per post
        post = db.query(f"SELECT * FROM posts WHERE id={post_id}")
        # Another query per post to get author
        author = db.query(f"SELECT * FROM users WHERE id={post['author_id']}")
        post['author'] = author
        posts.append(post)
    return posts

def process_feed(user_id, limit=100):
    results = []
    all_posts = db.query("SELECT * FROM posts ORDER BY created_at DESC")
    # Loading ALL posts then filtering in Python - O(n) memory
    for post in all_posts:
        if len(results) >= limit:
            break
        followers = db.query(f"SELECT * FROM followers WHERE user_id={user_id}")
        if post['author_id'] in [f['follower_id'] for f in followers]:
            results.append(post)
    return results

def cache_user(user_id, data):
    # Cache grows forever, no TTL, no eviction
    _cache[user_id] = {'data': data, 'time': time.time()}
    conn = db.get_connection()
    _connections.append(conn)  # connections never closed

def send_notifications(user_ids, message):
    # Synchronous notification to potentially thousands of users
    for uid in user_ids:
        email = db.query(f"SELECT email FROM users WHERE id={uid}")[0]
        send_email(email, message)  # blocking call in loop
        time.sleep(0.1)
'''

put_file('post_service.py', post_service, 'feat: add post service', 'feature/post-service')
time.sleep(1)
url4 = create_pr(
    'feat: add post feed and notification service',
    'Adds post feed aggregation with author info and push notification system.',
    'feature/post-service'
)
print('PR 4:', url4)

time.sleep(2)

# ─────────────────────────────────────────────────────────────────────────────
# PR 5: 干净的 PR（应该高分）
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== PR 5: Clean Code (should score high) ===')
create_branch('feature/utils')
time.sleep(1)

utils_py = '''"""Utility functions for input validation and formatting."""
import re
from datetime import datetime


def validate_email(email: str) -> bool:
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate username: 3-20 chars, alphanumeric + underscore only.
    Returns (is_valid, error_message).
    """
    if not username:
        return False, "Username cannot be empty"
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 20:
        return False, "Username must be at most 20 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""


def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO 8601 string."""
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def paginate(items: list, page: int, page_size: int = 20) -> dict:
    """Return paginated slice with metadata."""
    if page < 1:
        page = 1
    total = len(items)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    return {
        'items': items[start:end],
        'page': page,
        'page_size': page_size,
        'total': total,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1,
    }
'''

put_file('utils.py', utils_py, 'feat: add input validation utilities', 'feature/utils')
time.sleep(1)
url5 = create_pr(
    'feat: add input validation and utility functions',
    'Adds reusable utilities: email/username validation, datetime formatting, pagination.',
    'feature/utils'
)
print('PR 5:', url5)

print('\n=== All PRs Created ===')
print('PR 2 (XSS):', url2)
print('PR 3 (DB):', url3)
print('PR 4 (Performance):', url4)
print('PR 5 (Clean):', url5)
