# AI PR Review — 测试报告

**测试日期：** 2026-05-29
**测试仓库：** https://github.com/vigariokoestner958-droid/pr-review-test
**测试目标：** 验证 AI 代码审查工具对不同类型漏洞的检测准确性

---

## 总体结果一览

| PR | 标题 | 预埋类型 | 评分 | 判断 | HIGH | MEDIUM | LOW |
|----|------|---------|------|------|------|--------|-----|
| [#1](https://github.com/vigariokoestner958-droid/pr-review-test/pull/1) | 命令注入 + CORS | 安全漏洞 | 4/10 | 🚫 拒绝合并 | 2 | 2 | 1 |
| [#2](https://github.com/vigariokoestner958-droid/pr-review-test/pull/2) | XSS + eval | 前端安全 | 4/10 | 🚫 拒绝合并 | 3 | 1 | 0 |
| [#3](https://github.com/vigariokoestner958-droid/pr-review-test/pull/3) | SQL注入 + 明文密码 | 数据库安全 | 2/10 | 🚫 拒绝合并 | 4 | 2 | 1 |
| [#4](https://github.com/vigariokoestner958-droid/pr-review-test/pull/4) | N+1 + 内存泄露 | 性能问题 | 3/10 | 🚫 拒绝合并 | 3 | 2 | 0 |
| [#5](https://github.com/vigariokoestner958-droid/pr-review-test/pull/5) | 干净代码（对照组）| 无漏洞 | 8/10 | ✅ 建议合并 | 0 | 1 | 1 |

---

## PR #1 — 命令注入 + CORS

**文件：** `api.py`, `auth.py`
**评分：** 4/10 🚫 请修复后再合并

### 预埋漏洞 vs 检测结果

| 预埋漏洞 | 检测到 | 级别 | 定位 |
|---------|--------|------|------|
| `subprocess.run(shell=True)` 命令注入 | ✅ | HIGH | `api.py:16` |
| `CORS_ORIGINS = "*"` 过于宽泛 | ✅ | HIGH | `api.py:1` |
| 弱密码生成（邮箱前缀 + "123"）| ✅ | MEDIUM | `auth.py:19` |
| JWT 过期时间 99999999 秒 | ✅ | MEDIUM | `api.py:10` |
| 多余 `import subprocess` | ✅ | LOW | `api.py:1` |

### 关键输出摘录

```
🔴 HIGH — 命令注入风险 (api.py:16)
使用 shell=True 拼接字符串执行 cat 命令，攻击者可注入任意命令。

suggestion:
def get_all_users():
    with open('users.db', 'rb') as f:
        return f.read()

🔴 HIGH — CORS 配置过于宽泛 (api.py:1)
CORS_ORIGINS = '*' 允许任何域名跨域访问 API。

suggestion:
CORS_ORIGINS = ['https://myapp.example.com']

🟡 MEDIUM — 弱密码生成逻辑 (auth.py:19)
suggestion:
import secrets; new_password = secrets.token_urlsafe(12)

🟡 MEDIUM — JWT 过期时间过长 (api.py:10)
suggestion:
JWT_EXPIRY = 3600
```

---

## PR #2 — XSS + eval（前端安全）

**文件：** `static/search.js`
**评分：** 4/10 🚫 请修复后再合并

### 预埋漏洞 vs 检测结果

| 预埋漏洞 | 检测到 | 级别 | 定位 |
|---------|--------|------|------|
| `innerHTML` 直接注入用户输入（XSS） | ✅ | HIGH | `search.js:7` |
| `eval()` 执行用户输入 | ✅ | HIGH | `search.js:11` |
| `localStorage` 存储 `authToken` | ✅ | HIGH | `search.js:32` |
| 原型污染（`Object.assign` + 不可信来源）| ✅ | MEDIUM | `search.js:22` |

### 关键输出摘录

```
🔴 HIGH — XSS漏洞：innerHTML注入 (search.js:7)
suggestion:
container.textContent = `Results for: ${query}`;

🔴 HIGH — 危险eval用法 (search.js:11)
suggestion:
const allowedFilters = { active: item => item.active, inactive: item => !item.active };
const filterFn = allowedFilters[filter] || (() => true);

🔴 HIGH — 认证令牌存入localStorage (search.js:32)
suggestion:
// 删除这行，改用服务器设置HttpOnly Cookie
// localStorage.setItem('authToken', data.token);

🟡 MEDIUM — 原型污染风险 (search.js:22)
suggestion:
const safeConfig = Object.create(null);
Object.keys(config).forEach(key => {
  if (key === '__proto__' || key === 'constructor') return;
  safeConfig[key] = config[key];
});
```

> **备注：** PR #2 的 HIGH 数量比预期多（3个，原本只预埋了2个明显的），工具额外识别出了 `localStorage` 存 token 的问题，属于**超预期发现**。

---

## PR #3 — SQL注入 + 明文密码（数据库安全）

**文件：** `database.py`
**评分：** 2/10 🚫 请修复后再合并

### 预埋漏洞 vs 检测结果

| 预埋漏洞 | 检测到 | 级别 | 定位 |
|---------|--------|------|------|
| f-string 拼接 SQL（`find_user`）| ✅ | HIGH | `database.py:18` |
| 硬编码明文管理员密码 `admin123` | ✅ | HIGH | `database.py:9` |
| 多处 f-string 拼接 SQL | ✅ | HIGH | `database.py:6` |
| 无权限校验（`delete_user` 等）| ✅ | HIGH | `database.py` |
| 每次函数新建连接（无连接池）| ✅ | MEDIUM | `database.py:2` |
| 注释暴露安全隐患 | ✅ | MEDIUM | `database.py:9` |
| `print()` 调试语句 | ✅ | LOW | `database.py:40` |

### 关键输出摘录

```
🔴 HIGH — SQL注入漏洞 (database.py:18)
suggestion:
query = "SELECT * FROM users WHERE username=? AND password=?"
return conn.execute(query, (username, password)).fetchone()

🔴 HIGH — 硬编码明文密码 (database.py:9)
密码必须用bcrypt等算法哈希后再存储，即使泄露也无法逆向。

🟡 MEDIUM — 数据库连接未复用 (database.py:2)
suggestion:
@contextmanager
def db_cursor():
    conn = get_connection()
    try:
        yield conn, conn.cursor()
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
```

> **备注：** 此 PR 得分最低（2/10），符合预期——漏洞数量最多且最严重。

---

## PR #4 — N+1查询 + 内存泄露（性能问题）

**文件：** `post_service.py`
**评分：** 3/10 🚫 请修复后再合并

### 预埋漏洞 vs 检测结果

| 预埋漏洞 | 检测到 | 级别 | 定位 |
|---------|--------|------|------|
| N+1 查询（每篇帖子各查一次作者）| ✅ | HIGH | `post_service.py:9` |
| 全局缓存无限增长 + 连接未关闭 | ✅ | HIGH | `post_service.py:2` |
| 全表加载后内存过滤 | ✅ | MEDIUM | `post_service.py:19` |
| 同步阻塞批量发送通知 | ✅ | MEDIUM | `post_service.py:33` |
| f-string 拼接 SQL | ✅ | HIGH | `post_service.py:10` |

### 关键输出摘录

```
🔴 HIGH — N+1查询问题 (post_service.py:9)
如果有1000篇帖子，就会执行1000次额外查询。

suggestion:
author_ids = [p['author_id'] for p in posts]
authors = db.query("SELECT * FROM users WHERE id IN (...)", author_ids)
author_map = {a['id']: a for a in authors}

🔴 HIGH — 全局缓存无限增长 (post_service.py:2)
suggestion:
from collections import OrderedDict
MAX_CACHE_SIZE = 1000
_cache = OrderedDict()
def cache_user(user_id, data):
    if len(_cache) >= MAX_CACHE_SIZE:
        _cache.popitem(last=False)

🟡 MEDIUM — 同步阻塞发送通知 (post_service.py:33)
10万个用户就需要sleep 10000秒，用户请求会卡死。

suggestion:
from celery import group
@celery.task
def send_notification(uid, message): ...
def send_notifications_bulk(user_ids, message):
    group(send_notification.s(uid, message) for uid in user_ids).apply_async()
```

---

## PR #5 — 干净代码（对照组）

**文件：** `utils.py`
**评分：** 8/10 ✅ 建议合并

### 预埋漏洞 vs 检测结果

| 预埋情况 | 检测到 | 级别 | 定位 |
|---------|--------|------|------|
| 无预埋漏洞 | — | — | — |
| 时区处理不严格（`format_datetime` 不验证 tzinfo）| ✅ 主动发现 | MEDIUM | `utils.py:39` |
| `page<1` 静默修正不报错 | ✅ 主动发现 | LOW | `utils.py:44` |

```
🟡 MEDIUM — 时区信息丢失 (utils.py:39)
如果传入的是本地时间，直接格式化为'Z'会误导使用者以为是UTC。

suggestion:
from datetime import timezone
def format_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

🟢 LOW — page参数异常 (utils.py:44)
suggestion:
if page < 1:
    raise ValueError('page must be >= 1')
```

> **备注：** 对照组正确获得高分，且额外发现了2个合理的小问题（非误报），符合预期行为。

---

## 分析结论

### 检测准确性

| 维度 | 结果 |
|------|------|
| 预埋漏洞总数 | 20 个 |
| 正确检测数 | 20 个 |
| 漏报数 | 0 个 |
| 误报数 | 0 个（PR#2 额外发现1个有效问题，不算误报） |
| **检测率** | **100%** |

### 各类漏洞检测能力

| 漏洞类型 | 检测效果 | 备注 |
|---------|---------|------|
| SQL 注入 | ⭐⭐⭐⭐⭐ | 定位准确，修复代码规范 |
| XSS | ⭐⭐⭐⭐⭐ | 识别出 innerHTML、eval 多种形式 |
| 命令注入 | ⭐⭐⭐⭐⭐ | 识别 `shell=True` 风险 |
| 密码安全 | ⭐⭐⭐⭐⭐ | 明文存储、弱生成逻辑均识别 |
| 性能问题 | ⭐⭐⭐⭐☆ | N+1、内存泄露识别准确 |
| 权限缺失 | ⭐⭐⭐⭐☆ | 识别无 auth 校验问题 |
| 代码质量 | ⭐⭐⭐⭐☆ | `print`/import 等小问题也识别 |

### 修复建议质量

所有 HIGH 级别问题均附带可直接使用的 `suggestion` 代码块，修复方案合理：
- SQL注入 → 参数化查询
- XSS → `textContent` 替换 `innerHTML`
- 命令注入 → `open()` 替换 `subprocess`
- 弱密码 → `secrets.token_urlsafe()`
- 缓存泄露 → `OrderedDict` + 上限控制
- 同步通知 → Celery 异步任务

### 评分合理性

```
PR#3 (2/10) < PR#4 (3/10) < PR#1,#2 (4/10) < PR#5 (8/10)
```

评分严格区分了漏洞数量和严重程度，最干净的代码正确得到最高分。

---

## 待优化观察

1. **PR#1 分析失败一次**（JSON 解析错误），第二次正常，需排查 Claude API 返回格式稳定性
2. **评分刻度**：PR#1 和 PR#2 同为 4/10，但 PR#2 实际有 3 个 HIGH（多于 PR#1 的 2 个），评分粒度有待细化
3. **性能类问题级别**：N+1 查询被标记为 HIGH，符合严格审查标准，但实际项目中通常是 MEDIUM，可考虑加配置开关

---

*生成时间：2026-05-29 | 工具路径：`C:\Users\THC\Desktop\当前工作资料\个人antigravity\qnycs\pr-review\`*
