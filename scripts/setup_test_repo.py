"""Create a test GitHub repo with intentional vulnerabilities for PR review testing."""
import requests, os, base64, time
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('GITHUB_TOKEN')
H = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}

def b64(s): return base64.b64encode(s.encode()).decode()

# Get username
username = requests.get('https://api.github.com/user', headers=H).json()['login']
repo = 'pr-review-test'
print(f'User: {username}')

# 1. Create repo
r = requests.post('https://api.github.com/user/repos', headers=H, json={
    'name': repo, 'description': 'Test repo for AI PR Review', 'private': False, 'auto_init': False
})
print(f'Create repo: {r.status_code}')
if r.status_code not in (200, 201, 422):
    print(r.json()); exit(1)

time.sleep(2)

# 2. Initial files on main
auth_py = '''import os
import jwt
import sqlite3

SECRET = "hardcoded_secret_123"

def login(username, password):
    conn = sqlite3.connect("users.db")
    query = f"SELECT * FROM users WHERE username=\'{username}\' AND password=\'{password}\'"
    result = conn.execute(query).fetchone()
    if result:
        token = jwt.encode({"user": username}, SECRET, algorithm="HS256")
        return token
    return None

def get_users():
    conn = sqlite3.connect("users.db")
    return [row for row in conn.execute("SELECT * FROM users")]
'''

readme = '# PR Review Test App\nA simple app for testing AI PR Review.\n'

r = requests.put(f'https://api.github.com/repos/{username}/{repo}/contents/auth.py',
    headers=H, json={'message': 'init: add auth module', 'content': b64(auth_py)})
print(f'auth.py: {r.status_code}')

r = requests.put(f'https://api.github.com/repos/{username}/{repo}/contents/README.md',
    headers=H, json={'message': 'init: add readme', 'content': b64(readme)})
print(f'README: {r.status_code}')

time.sleep(2)

# 3. Get main SHA
main_sha = requests.get(
    f'https://api.github.com/repos/{username}/{repo}/git/ref/heads/main', headers=H
).json()['object']['sha']
print(f'Main SHA: {main_sha[:8]}')

# 4. Create feature branch
r = requests.post(f'https://api.github.com/repos/{username}/{repo}/git/refs', headers=H, json={
    'ref': 'refs/heads/feature/add-user-api', 'sha': main_sha
})
print(f'Branch: {r.status_code}')

time.sleep(1)

# 5. Add new file with vulnerabilities on feature branch
api_py = '''import os, subprocess
import jwt
from auth import login, SECRET

CORS_ORIGINS = "*"
JWT_EXPIRY = 99999999

def create_user(username, password, role="admin"):
    token = login(username, password)
    return {"token": token, "role": role}

def verify_token(token):
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except:
        return None

def get_all_users():
    result = subprocess.run(f"cat users.db", shell=True, capture_output=True)
    return result.stdout
'''

# Update auth.py on feature branch
auth_sha = requests.get(
    f'https://api.github.com/repos/{username}/{repo}/contents/auth.py',
    headers=H, params={'ref': 'feature/add-user-api'}
).json()['sha']

auth_updated = auth_py + '''
def reset_password(email):
    new_password = email.split("@")[0] + "123"
    return new_password
'''

r = requests.put(f'https://api.github.com/repos/{username}/{repo}/contents/auth.py',
    headers=H, json={
        'message': 'feat: add password reset',
        'content': b64(auth_updated),
        'sha': auth_sha,
        'branch': 'feature/add-user-api'
    })
print(f'Update auth.py: {r.status_code}')

r = requests.put(f'https://api.github.com/repos/{username}/{repo}/contents/api.py',
    headers=H, json={
        'message': 'feat: add user API endpoints',
        'content': b64(api_py),
        'branch': 'feature/add-user-api'
    })
print(f'Add api.py: {r.status_code}')

time.sleep(1)

# 6. Create PR
r = requests.post(f'https://api.github.com/repos/{username}/{repo}/pulls', headers=H, json={
    'title': 'feat: add user API and password reset',
    'body': 'Adds user management API endpoints and password reset functionality.',
    'head': 'feature/add-user-api',
    'base': 'main'
})
pr = r.json()
print(f'PR: {r.status_code}')
print(f'PR URL: {pr.get("html_url", "error: " + str(pr))}')
