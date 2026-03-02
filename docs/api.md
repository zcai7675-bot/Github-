# GitHub Auto Sync API 文档

本文档提供了 GitHub Auto Sync 各模块的详细 API 参考。

## 目录

- [模块概述](#模块概述)
- [Config 模块](#config-模块)
- [Auth 模块](#auth-模块)
- [GitHub Client 模块](#github-client-模块)
- [Sync 模块](#sync-模块)
- [Watcher 模块](#watcher-模块)
- [Git Operations 模块](#git-operations-模块)

---

## 模块概述

GitHub Auto Sync 由以下核心模块组成：

| 模块 | 文件 | 功能描述 |
|------|------|----------|
| `config` | `config.py` | 配置文件管理、YAML 解析、环境变量支持 |
| `auth` | `auth.py` | GitHub Token 管理、安全凭证存储 |
| `github_client` | `github_client.py` | GitHub API 客户端封装 |
| `sync` | `sync.py` | 同步引擎、状态管理、冲突处理 |
| `watcher` | `watcher.py` | 文件系统监控、事件处理 |
| `git_operations` | `git_operations.py` | Git 操作封装 |

---

## Config 模块

配置文件管理模块，提供 YAML 配置文件的加载、验证、保存功能。

### 类

#### `Config`

主配置类，管理所有配置项。

```python
from github_auto_sync.config import Config

# 从文件加载配置
config = Config.load("path/to/config.yml")

# 创建默认配置
config = Config()
```

**类属性：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `github` | `Dict[str, str]` | GitHub 认证配置 |
| `repositories` | `List[RepositoryConfig]` | 仓库配置列表 |
| `sync` | `SyncConfig` | 同步设置 |
| `logging` | `LoggingConfig` | 日志设置 |
| `notifications` | `NotificationConfig` | 通知设置 |

**类方法：**

##### `Config.load(config_path=None, use_env=True, create_default=False)`

从配置文件加载配置。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `config_path` | `str \| Path \| None` | `None` | 配置文件路径 |
| `use_env` | `bool` | `True` | 是否使用环境变量覆盖 |
| `create_default` | `bool` | `False` | 文件不存在时是否创建默认配置 |

**返回：** `Config` 实例

**异常：**
- `FileNotFoundError` - 配置文件不存在
- `ValueError` - 配置文件格式错误

**示例：**

```python
# 加载当前目录的配置
config = Config.load()

# 加载指定路径的配置
config = Config.load("/path/to/config.yml")

# 创建默认配置（如果不存在）
config = Config.load(create_default=True)
```

##### `Config.generate_template(include_comments=True)`

生成默认配置模板。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `include_comments` | `bool` | `True` | 是否包含注释说明 |

**返回：** `str` - 配置模板字符串

**示例：**

```python
template = Config.generate_template()
print(template)
```

**实例方法：**

##### `validate()`

验证配置有效性。

**返回：** `List[str]` - 错误消息列表，空列表表示配置有效

**示例：**

```python
errors = config.validate()
if errors:
    for error in errors:
        print(f"配置错误: {error}")
else:
    print("配置有效")
```

##### `is_valid()`

检查配置是否有效。

**返回：** `bool`

##### `to_dict()`

将配置转换为字典。

**返回：** `Dict[str, Any]`

**示例：**

```python
import json
config_dict = config.to_dict()
print(json.dumps(config_dict, indent=2))
```

##### `save(config_path=None)`

保存配置到文件。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `config_path` | `str \| Path \| None` | `None` | 保存路径，默认使用加载时的路径 |

**示例：**

```python
config.save()  # 保存到原路径
config.save("/new/path/config.yml")  # 保存到新路径
```

##### `update(updates)`

更新配置。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `updates` | `Dict[str, Any]` | 要更新的配置项字典 |

**示例：**

```python
config.update({
    "github": {"token": "new_token", "username": "new_user"},
    "sync": {"batch_window": 60}
})
```

##### `get_repository(name)`

根据名称获取仓库配置。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 仓库名称 |

**返回：** `RepositoryConfig \| None`

**示例：**

```python
repo_config = config.get_repository("my-project")
if repo_config:
    print(f"本地路径: {repo_config.local_path}")
```

##### `add_repository(repo_config)`

添加仓库配置。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `repo_config` | `RepositoryConfig` | 仓库配置对象 |

**异常：**
- `ValueError` - 仓库名称已存在

**示例：**

```python
from github_auto_sync.config import RepositoryConfig

repo_config = RepositoryConfig(
    name="new-project",
    local_path="/path/to/project",
    branch="main"
)
config.add_repository(repo_config)
```

##### `remove_repository(name)`

移除仓库配置。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 仓库名称 |

**返回：** `bool` - 是否成功移除

#### `RepositoryConfig`

仓库配置数据类。

```python
from github_auto_sync.config import RepositoryConfig

repo_config = RepositoryConfig(
    name="my-project",
    local_path="./my-project",
    remote_url="https://github.com/user/repo.git",
    branch="main",
    auto_sync=True,
    ignore_patterns=[".git/", "__pycache__/"]
)
```

**属性：**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | 必填 | 仓库名称 |
| `local_path` | `str` | 必填 | 本地路径 |
| `remote_url` | `str` | `""` | 远程仓库 URL |
| `branch` | `str` | `"main"` | 默认分支 |
| `auto_sync` | `bool` | `True` | 是否启用自动同步 |
| `ignore_patterns` | `List[str]` | 默认列表 | 忽略模式列表 |

#### `SyncConfig`

同步设置配置类。

**属性：**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `batch_window` | `int` | `30` | 批处理时间窗口（秒） |
| `max_files_per_commit` | `int` | `50` | 每次提交的最大文件数 |
| `commit_message_template` | `str` | `"auto-sync: {action} {files} files"` | 提交消息模板 |
| `auto_push` | `bool` | `True` | 是否自动推送 |
| `auto_pull` | `bool` | `True` | 是否自动拉取 |
| `conflict_strategy` | `str` | `"skip"` | 冲突解决策略 |

#### `LoggingConfig`

日志配置类。

**属性：**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `level` | `str` | `"INFO"` | 日志级别 |
| `file` | `str` | `""` | 日志文件路径 |
| `color` | `bool` | `True` | 是否启用彩色输出 |

#### `NotificationConfig`

通知配置类。

**属性：**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `on_error` | `bool` | `True` | 同步失败时发送通知 |
| `on_success` | `bool` | `False` | 同步成功时发送通知 |

### 函数

#### `init_config(path=None, force=False)`

初始化配置文件。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | `str \| Path \| None` | `None` | 配置文件路径 |
| `force` | `bool` | `False` | 是否强制覆盖已存在的文件 |

**返回：** `Path` - 创建的配置文件路径

**异常：**
- `FileExistsError` - 文件已存在且 force=False

**示例：**

```python
from github_auto_sync.config import init_config

# 在当前目录创建配置
config_path = init_config()
print(f"配置文件已创建: {config_path}")

# 强制覆盖
config_path = init_config(force=True)
```

#### `find_config_file(start_path=None)`

向上查找配置文件。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `start_path` | `str \| Path \| None` | `None` | 起始路径 |

**返回：** `Path \| None` - 配置文件路径或 None

**示例：**

```python
from github_auto_sync.config import find_config_file

config_path = find_config_file("/path/to/project/subdir")
if config_path:
    print(f"找到配置文件: {config_path}")
```

---

## Auth 模块

GitHub 认证模块，提供 Token 管理、安全凭证存储功能。

### 异常类

#### `AuthenticationError`

认证错误异常。

```python
from github_auto_sync.auth import AuthenticationError

try:
    token = ensure_authenticated()
except AuthenticationError as e:
    print(f"认证失败: {e}")
```

#### `TokenValidationError`

Token 验证错误异常。

### 函数

#### `authenticate(token=None, username=None, store=True)`

使用 GitHub Token 进行认证。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `token` | `str \| None` | `None` | GitHub Token，None 则从环境变量获取 |
| `username` | `str \| None` | `None` | GitHub 用户名 |
| `store` | `bool` | `True` | 是否存储到系统密钥环 |

**返回：** `Tuple[bool, str]` - (是否成功, 消息)

**异常：**
- `AuthenticationError` - 认证过程中发生错误

**示例：**

```python
from github_auto_sync.auth import authenticate

# 使用指定 token 认证
success, message = authenticate("ghp_xxxxxx", "myusername")
if success:
    print(f"认证成功: {message}")
else:
    print(f"认证失败: {message}")

# 从环境变量获取 token
success, message = authenticate()
```

#### `validate_token(token)`

验证 GitHub Token 的有效性。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `token` | `str` | GitHub Token |

**返回：** `Tuple[bool, str]` - (是否有效, 用户名或错误消息)

**异常：**
- `TokenValidationError` - 验证过程中发生网络错误

**示例：**

```python
from github_auto_sync.auth import validate_token

valid, info = validate_token("ghp_xxxxxx")
if valid:
    print(f"Token 有效，用户: {info}")
else:
    print(f"验证失败: {info}")
```

#### `is_authenticated()`

检查用户是否已认证。

**返回：** `bool`

**示例：**

```python
from github_auto_sync.auth import is_authenticated

if is_authenticated():
    print("用户已认证")
else:
    print("请先认证")
```

#### `logout()`

清除存储的凭证（登出）。

**返回：** `bool` - 是否成功清除

**示例：**

```python
from github_auto_sync.auth import logout

if logout():
    print("已成功登出")
```

#### `get_auth_token()`

获取当前有效的认证 token。

**返回：** `str \| None`

**获取优先级：**
1. 系统密钥环中存储的 token
2. 环境变量 `GITHUB_TOKEN`

**示例：**

```python
from github_auto_sync.auth import get_auth_token

token = get_auth_token()
if token:
    headers = {"Authorization": f"Bearer {token}"}
```

#### `get_auth_username()`

获取当前认证的用户名。

**返回：** `str \| None`

**示例：**

```python
from github_auto_sync.auth import get_auth_username

username = get_auth_username()
print(f"当前用户: @{username}")
```

#### `ensure_authenticated()`

确保用户已认证并返回 token。

**返回：** `str` - 有效的 GitHub token

**异常：**
- `AuthenticationError` - 用户未认证

**示例：**

```python
from github_auto_sync.auth import ensure_authenticated

try:
    token = ensure_authenticated()
    # 使用 token 进行 API 调用
except AuthenticationError as e:
    print(f"请先认证: {e}")
```

#### `get_auth_headers()`

获取带有认证信息的 HTTP 请求头。

**返回：** `dict` - 包含 Authorization 头的字典

**异常：**
- `AuthenticationError` - 用户未认证

**示例：**

```python
from github_auto_sync.auth import get_auth_headers
import requests

headers = get_auth_headers()
response = requests.get("https://api.github.com/user", headers=headers)
```

#### `load_dotenv(dotenv_path=None)`

从 `.env` 文件加载环境变量。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `dotenv_path` | `Path \| None` | `None` | `.env` 文件路径 |

**返回：** `bool` - 是否成功加载

**示例：**

```python
from github_auto_sync.auth import load_dotenv
from pathlib import Path

# 加载当前目录的 .env
loaded = load_dotenv()

# 加载指定路径
loaded = load_dotenv(Path("/path/to/.env"))
```

### 类

#### `AuthContext`

认证上下文管理器，用于临时使用特定的认证信息。

```python
from github_auto_sync.auth import AuthContext

with AuthContext("ghp_xxxx", "username"):
    # 在此代码块中使用指定的认证
    headers = get_auth_headers()
    # ...
# 代码块结束后恢复之前的认证
```

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `token` | `str \| None` | `None` | GitHub token |
| `username` | `str \| None` | `None` | GitHub 用户名 |
| `use_env` | `bool` | `True` | 是否允许从环境变量获取 token |

**示例：**

```python
from github_auto_sync.auth import AuthContext, get_auth_token

# 保存当前 token
original_token = get_auth_token()

# 使用临时 token
with AuthContext("ghp_temporary_token"):
    temp_token = get_auth_token()
    print(f"临时 token: {temp_token}")

# 恢复原始 token
current_token = get_auth_token()
print(f"恢复后的 token: {current_token}")  # 与 original_token 相同
```

---

## GitHub Client 模块

GitHub API 客户端模块，提供基于 PyGithub 的高级封装。

### 异常类

| 异常类 | 说明 |
|--------|------|
| `GitHubClientError` | 客户端基础异常 |
| `RepositoryError` | 仓库操作异常 |
| `RepositoryNotFoundError` | 仓库不存在异常 |
| `RepositoryAlreadyExistsError` | 仓库已存在异常 |
| `RateLimitError` | API 速率限制异常 |
| `PermissionError` | 权限不足异常 |
| `NetworkError` | 网络连接异常 |

### 类

#### `GitHubClient`

GitHub API 客户端封装类。

```python
from github_auto_sync.github_client import GitHubClient

# 使用存储的凭证
client = GitHubClient()

# 使用指定 token
client = GitHubClient("ghp_xxxxxx")
```

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `token` | `str \| None` | `None` | GitHub Token，None 则从存储获取 |

**异常：**
- `AuthenticationError` - 无法获取有效的 token

**方法：**

##### `get_rate_limit()`

获取 API 速率限制信息。

**返回：** `Dict[str, Any]`

```python
{
    "limit": 5000,        # 总限制次数
    "remaining": 4990,    # 剩余次数
    "reset": 1234567890,  # 重置时间戳
    "used": 10,           # 已使用次数
    "reset_datetime": datetime  # 重置时间
}
```

**示例：**

```python
rate = client.get_rate_limit()
print(f"API 配额: {rate['remaining']}/{rate['limit']}")
```

##### `check_rate_limit(min_remaining=10)`

检查 API 速率限制是否充足。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `min_remaining` | `int` | `10` | 最小剩余次数阈值 |

**返回：** `bool` - 如果剩余次数大于阈值则返回 True

**异常：**
- `RateLimitError` - 剩余次数不足

##### `get_user_info()`

获取认证用户详细信息。

**返回：** `Dict[str, Any]`

```python
{
    "login": "username",
    "id": 12345,
    "name": "Display Name",
    "email": "user@example.com",
    "avatar_url": "https://...",
    "html_url": "https://github.com/username",
    "bio": "User bio",
    "location": "Location",
    "company": "Company",
    "blog": "https://blog.com",
    "public_repos": 10,
    "private_repos": 5,
    "total_repos": 15,
    "followers": 100,
    "following": 50,
    "created_at": "2020-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00",
    "type": "User"
}
```

**示例：**

```python
info = client.get_user_info()
print(f"用户: @{info['login']}, 仓库数: {info['total_repos']}")
```

##### `list_repos(type_filter="all", sort="updated", direction="desc", visibility=None)`

列出用户的所有仓库。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `type_filter` | `str` | `"all"` | 仓库类型筛选 (all, owner, member) |
| `sort` | `str` | `"updated"` | 排序字段 (created, updated, pushed, full_name) |
| `direction` | `str` | `"desc"` | 排序方向 (asc, desc) |
| `visibility` | `str \| None` | `None` | 可见性筛选 (all, public, private) |

**返回：** `List[Dict[str, Any]]` - 仓库信息列表

**示例：**

```python
# 列出所有仓库
repos = client.list_repos()

# 只列出私有仓库，按创建时间排序
repos = client.list_repos(visibility="private", sort="created")

for repo in repos:
    print(f"{repo['full_name']}: {repo['description']}")
```

##### `get_repo(name, owner=None)`

获取指定仓库的详细信息。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | 必填 | 仓库名称（可以是 'owner/repo' 格式） |
| `owner` | `str \| None` | `None` | 仓库所有者 |

**返回：** `Dict[str, Any]` - 仓库信息

**异常：**
- `RepositoryNotFoundError` - 仓库不存在

**示例：**

```python
# 使用完整名称
repo = client.get_repo("username/repo-name")

# 分开指定
repo = client.get_repo("repo-name", "username")

print(f"仓库: {repo['full_name']}")
print(f"Stars: {repo['stargazers_count']}")
```

##### `repo_exists(name, owner=None)`

检查仓库是否存在。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | 必填 | 仓库名称 |
| `owner` | `str \| None` | `None` | 仓库所有者 |

**返回：** `bool`

**示例：**

```python
if client.repo_exists("my-repo"):
    print("仓库已存在")
else:
    print("仓库不存在")
```

##### `create_repo(name, description="", private=True, auto_init=False, ...)`

创建新仓库。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | 必填 | 仓库名称 |
| `description` | `str` | `""` | 仓库描述 |
| `private` | `bool` | `True` | 是否私有仓库 |
| `auto_init` | `bool` | `False` | 是否自动初始化 README |
| `gitignore_template` | `str \| None` | `None` | Gitignore 模板 |
| `license_template` | `str \| None` | `None` | 许可证模板 |
| `allow_rebase_merge` | `bool` | `True` | 是否允许 rebase 合并 |
| `allow_squash_merge` | `bool` | `True` | 是否允许 squash 合并 |
| `allow_merge_commit` | `bool` | `True` | 是否允许普通合并 |
| `delete_branch_on_merge` | `bool` | `False` | 合并后是否删除分支 |
| `homepage` | `str \| None` | `None` | 项目主页 URL |
| `has_issues` | `bool` | `True` | 是否启用 Issues |
| `has_wiki` | `bool` | `True` | 是否启用 Wiki |
| `has_projects` | `bool` | `True` | 是否启用 Projects |

**返回：** `Dict[str, Any]` - 创建的仓库信息

**异常：**
- `RepositoryAlreadyExistsError` - 仓库已存在
- `PermissionError` - 权限不足

**示例：**

```python
# 创建基本私有仓库
repo = client.create_repo("my-new-repo")

# 创建带描述的公开仓库
repo = client.create_repo(
    "my-new-repo",
    description="我的新项目",
    private=False,
    auto_init=True,
    gitignore_template="Python",
    license_template="mit"
)

print(f"创建成功: {repo['html_url']}")
```

##### `delete_repo(name, owner=None)`

删除仓库。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | 必填 | 仓库名称 |
| `owner` | `str \| None` | `None` | 仓库所有者 |

**返回：** `bool` - 删除成功返回 True

**异常：**
- `RepositoryNotFoundError` - 仓库不存在
- `PermissionError` - 权限不足

**警告：** 此操作不可恢复！

**示例：**

```python
if client.delete_repo("old-repo"):
    print("仓库已删除")
```

##### `update_repo(name, owner=None, description=None, private=None, ...)`

更新仓库设置。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | 必填 | 仓库名称 |
| `owner` | `str \| None` | `None` | 仓库所有者 |
| `description` | `str \| None` | `None` | 新的描述 |
| `private` | `bool \| None` | `None` | 是否私有 |
| `homepage` | `str \| None` | `None` | 项目主页 |
| `has_issues` | `bool \| None` | `None` | 是否启用 Issues |
| `has_wiki` | `bool \| None` | `None` | 是否启用 Wiki |
| `has_projects` | `bool \| None` | `None` | 是否启用 Projects |
| `default_branch` | `str \| None` | `None` | 默认分支名称 |
| `archived` | `bool \| None` | `None` | 是否归档仓库 |

**返回：** `Dict[str, Any]` - 更新后的仓库信息

**示例：**

```python
repo = client.update_repo(
    "my-repo",
    description="更新后的描述",
    has_wiki=False,
    private=False
)
```

##### `get_repo_languages(name, owner=None)`

获取仓库使用的编程语言统计。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | 必填 | 仓库名称 |
| `owner` | `str \| None` | `None` | 仓库所有者 |

**返回：** `Dict[str, int]` - 语言名称到代码字节数的映射

**示例：**

```python
langs = client.get_repo_languages("my-repo")
for lang, bytes_count in langs.items():
    print(f"{lang}: {bytes_count} bytes")
```

##### `search_repos(query, sort="updated", order="desc", limit=30)`

搜索仓库。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | `str` | 必填 | 搜索查询字符串 |
| `sort` | `str` | `"updated"` | 排序字段 (stars, forks, updated) |
| `order` | `str` | `"desc"` | 排序方向 (asc, desc) |
| `limit` | `int` | `30` | 返回结果数量限制 |

**返回：** `List[Dict[str, Any]]` - 仓库信息列表

**示例：**

```python
# 搜索 Python 机器学习项目
repos = client.search_repos("machine learning language:python", sort="stars")
for repo in repos:
    print(f"{repo['full_name']}: {repo['stargazers_count']} stars")
```

### 上下文管理器

`GitHubClient` 支持上下文管理器模式：

```python
from github_auto_sync.github_client import GitHubClient

with GitHubClient() as client:
    repos = client.list_repos()
    # 自动关闭连接
```

### 便捷函数

#### `create_client(token=None)`

创建 GitHub 客户端实例。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `token` | `str \| None` | `None` | GitHub Token |

**返回：** `GitHubClient` 实例

#### `get_client()`

获取默认 GitHub 客户端实例（使用存储的凭证）。

**返回：** `GitHubClient` 实例

**异常：**
- `AuthenticationError` - 未找到有效凭证

---

## Sync 模块

同步引擎模块，提供完整的同步功能。

### 枚举

#### `SyncStatus`

同步状态枚举。

| 成员 | 说明 |
|------|------|
| `NOT_SYNCED` | 未同步 |
| `SYNCING` | 同步中 |
| `SYNCED` | 已同步 |
| `ERROR` | 同步错误 |
| `CONFLICT` | 存在冲突 |
| `PAUSED` | 暂停同步 |

#### `SyncAction`

同步操作类型枚举。

| 成员 | 值 | 说明 |
|------|-----|------|
| `INITIAL` | `"initial"` | 初始同步 |
| `INCREMENTAL` | `"incremental"` | 增量同步 |
| `PULL` | `"pull"` | 拉取更新 |
| `PUSH` | `"push"` | 推送更新 |
| `COMMIT` | `"commit"` | 提交变更 |

### 数据类

#### `SyncResult`

同步结果类。

```python
from github_auto_sync.sync import SyncResult

result = SyncResult(
    success=True,
    status=SyncStatus.SYNCED,
    action=SyncAction.INCREMENTAL,
    message="Sync completed",
    files_synced=["file1.txt", "file2.txt"],
    commit_hash="abc1234"
)
```

**属性：**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `success` | `bool` | `False` | 是否成功 |
| `status` | `SyncStatus` | `SyncStatus.NOT_SYNCED` | 同步后的状态 |
| `action` | `SyncAction \| None` | `None` | 执行的操作类型 |
| `message` | `str` | `""` | 结果消息 |
| `files_synced` | `List[str]` | `[]` | 已同步的文件列表 |
| `files_failed` | `List[str]` | `[]` | 同步失败的文件列表 |
| `commit_hash` | `str \| None` | `None` | 提交哈希 |
| `timestamp` | `datetime` | `datetime.now()` | 同步时间戳 |
| `duration` | `float` | `0.0` | 同步耗时（秒） |
| `details` | `Dict[str, Any]` | `{}` | 详细信息字典 |

### 异常类

#### `SyncError`

同步错误基础异常。

#### `SyncConflictError`

同步冲突异常。

### 类

#### `SyncManager`

同步管理器类，主要的同步协调器。

```python
from github_auto_sync.sync import SyncManager
from github_auto_sync.config import Config, RepositoryConfig

config = Config.load()
repo_config = config.get_repository("my-project")

manager = SyncManager(config, repo_config)
```

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `config` | `Config` | 必填 | 全局配置对象 |
| `repo_config` | `RepositoryConfig` | 必填 | 仓库配置对象 |
| `dry_run` | `bool` | `False` | 是否为试运行模式 |

**异常：**
- `ValueError` - 配置无效
- `GitHubClientError` - GitHub 客户端初始化失败

**方法：**

##### `initial_sync()`

执行初始同步（全量上传）。

**返回：** `SyncResult`

**示例：**

```python
result = manager.initial_sync()
if result.success:
    print(f"初始同步成功: {result.message}")
    print(f"同步文件数: {len(result.files_synced)}")
else:
    print(f"同步失败: {result.message}")
```

##### `sync_changes(files=None)`

执行增量同步。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `files` | `List[str] \| None` | `None` | 要同步的文件列表，None 表示同步所有变更 |

**返回：** `SyncResult`

**示例：**

```python
# 同步所有变更
result = manager.sync_changes()

# 同步指定文件
result = manager.sync_changes(["file1.txt", "file2.txt"])
```

##### `start_auto_sync()`

启动自动同步。

**返回：** `bool` - 是否成功启动

**示例：**

```python
if manager.start_auto_sync():
    print("自动同步已启动")
    # 保持运行
    import time
    try:
        while manager.is_auto_sync_running():
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop_auto_sync()
```

##### `stop_auto_sync()`

停止自动同步。

**示例：**

```python
manager.stop_auto_sync()
print("自动同步已停止")
```

##### `is_auto_sync_running()`

检查自动同步是否正在运行。

**返回：** `bool`

##### `get_status()`

获取当前同步状态。

**返回：** `SyncStatus`

##### `get_last_result()`

获取上次同步结果。

**返回：** `SyncResult \| None`

##### `get_last_sync_time()`

获取上次同步时间。

**返回：** `datetime \| None`

##### `pause()`

暂停同步。

**示例：**

```python
manager.pause()
print("同步已暂停")
```

##### `resume()`

恢复同步。

**示例：**

```python
manager.resume()
print("同步已恢复")
```

##### `handle_conflicts(strategy=None)`

处理合并冲突。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `strategy` | `str \| None` | `None` | 冲突解决策略，None 使用配置中的策略 |

**返回：** `SyncResult`

**示例：**

```python
result = manager.handle_conflicts(strategy="overwrite")
if result.success:
    print("冲突已解决")
```

##### `set_callbacks(on_sync_complete=None, on_sync_error=None, on_conflict=None)`

设置事件回调函数。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `on_sync_complete` | `Callable[[SyncResult], None] \| None` | `None` | 同步完成回调 |
| `on_sync_error` | `Callable[[SyncError], None] \| None` | `None` | 同步错误回调 |
| `on_conflict` | `Callable[[List[str]], None] \| None` | `None` | 冲突检测回调 |

**示例：**

```python
def on_sync_complete(result: SyncResult):
    print(f"同步完成: {result.message}")

def on_sync_error(error: SyncError):
    print(f"同步错误: {error}")

def on_conflict(files: List[str]):
    print(f"检测到冲突文件: {files}")

manager.set_callbacks(
    on_sync_complete=on_sync_complete,
    on_sync_error=on_sync_error,
    on_conflict=on_conflict
)
```

##### `force_sync()`

强制同步，忽略当前状态。

**返回：** `SyncResult`

**示例：**

```python
result = manager.force_sync()
```

##### `get_pending_files()`

获取待同步的文件列表。

**返回：** `List[str]`

##### `clear_pending_files()`

清空待同步文件队列。

### 上下文管理器

`SyncManager` 支持上下文管理器模式：

```python
from github_auto_sync.sync import SyncManager

with SyncManager(config, repo_config) as manager:
    result = manager.initial_sync()
    # 自动停止自动同步
```

### 便捷函数

#### `sync_repository(repo_config, config=None, initial=False, dry_run=False)`

同步仓库的便捷函数。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `repo_config` | `RepositoryConfig` | 必填 | 仓库配置 |
| `config` | `Config \| None` | `None` | 全局配置，None 则创建默认配置 |
| `initial` | `bool` | `False` | 是否执行初始同步 |
| `dry_run` | `bool` | `False` | 是否为试运行模式 |

**返回：** `SyncResult`

**示例：**

```python
from github_auto_sync.sync import sync_repository
from github_auto_sync.config import RepositoryConfig

repo_config = RepositoryConfig(
    name="my-project",
    local_path="/path/to/project"
)

result = sync_repository(repo_config, initial=True)
```

#### `create_sync_manager(config, repo_name, dry_run=False)`

创建同步管理器的工厂函数。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `config` | `Config` | 必填 | 全局配置 |
| `repo_name` | `str` | 必填 | 仓库名称 |
| `dry_run` | `bool` | `False` | 是否为试运行模式 |

**返回：** `SyncManager` 实例

**异常：**
- `ValueError` - 找不到指定名称的仓库配置

**示例：**

```python
from github_auto_sync.sync import create_sync_manager

manager = create_sync_manager(config, "my-project")
result = manager.initial_sync()
```

---

## Watcher 模块

文件系统监控模块，提供基于 watchdog 的文件监控功能。

### 枚举

#### `ChangeType`

文件变更类型枚举。

| 成员 | 说明 |
|------|------|
| `CREATED` | 文件创建 |
| `MODIFIED` | 文件修改 |
| `DELETED` | 文件删除 |
| `MOVED` | 文件移动 |

### 数据类

#### `FileChangeEvent`

文件变更事件类。

```python
from github_auto_sync.watcher import FileChangeEvent, ChangeType

event = FileChangeEvent(
    path="/path/to/file.txt",
    change_type=ChangeType.MODIFIED,
    is_directory=False
)
```

**属性：**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | `str` | 必填 | 文件或目录的路径 |
| `change_type` | `ChangeType` | 必填 | 变更类型 |
| `is_directory` | `bool` | `False` | 是否为目录 |
| `src_path` | `str \| None` | `None` | 移动事件的源路径 |
| `timestamp` | `float` | `time.time()` | 事件发生的时间戳 |

### 类

#### `FileWatcher`

文件监控器类。

```python
from github_auto_sync.watcher import FileWatcher, FileChangeEvent

def on_changes(events: List[FileChangeEvent]):
    for event in events:
        print(f"{event.change_type.name}: {event.path}")

watcher = FileWatcher(
    path="/path/to/watch",
    callback=on_changes,
    batch_window=5.0
)
```

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | `str \| Path` | 必填 | 要监控的目录路径 |
| `callback` | `Callable[[List[FileChangeEvent]], None]` | 必填 | 回调函数 |
| `ignore_patterns` | `List[str] \| None` | `None` | 自定义忽略模式列表 |
| `batch_window` | `float` | `5.0` | 批处理时间窗口（秒） |
| `debounce_interval` | `float` | `0.5` | 防抖间隔（秒） |
| `use_gitignore` | `bool` | `True` | 是否自动加载 .gitignore 文件 |

**异常：**
- `FileNotFoundError` - 监控路径不存在
- `NotADirectoryError` - 监控路径不是目录

**方法：**

##### `start()`

开始监控。

**异常：**
- `RuntimeError` - 监控器已经在运行

**示例：**

```python
watcher.start()
print("监控已启动")
```

##### `stop()`

停止监控。

会刷新所有待处理的事件后再停止。

**示例：**

```python
watcher.stop()
print("监控已停止")
```

##### `is_running()`

检查监控器是否正在运行。

**返回：** `bool`

**示例：**

```python
if watcher.is_running():
    print("监控器正在运行")
```

##### `add_ignore_pattern(pattern)`

动态添加忽略模式。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `pattern` | `str` | 要添加的忽略模式 |

**示例：**

```python
watcher.add_ignore_pattern("*.log")
```

##### `remove_ignore_pattern(pattern)`

移除忽略模式。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `pattern` | `str` | 要移除的忽略模式 |

**返回：** `bool` - 是否成功移除

**示例：**

```python
if watcher.remove_ignore_pattern("*.log"):
    print("忽略模式已移除")
```

##### `get_pending_events()`

获取当前待处理的事件。

**返回：** `List[FileChangeEvent]`

**示例：**

```python
pending = watcher.get_pending_events()
print(f"待处理事件数: {len(pending)}")
```

##### `flush()`

立即刷新所有待处理的事件。

**示例：**

```python
watcher.flush()
```

### 上下文管理器

`FileWatcher` 支持上下文管理器模式：

```python
from github_auto_sync.watcher import FileWatcher

with FileWatcher("/path/to/watch", on_changes) as watcher:
    # 监控器已自动启动
    import time
    time.sleep(60)
    # 自动停止监控
```

### 函数

#### `load_gitignore(path)`

加载 `.gitignore` 文件中的忽略模式。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | `str \| Path` | `.gitignore` 文件路径或包含 `.gitignore` 的目录路径 |

**返回：** `List[str]` - 忽略模式列表

**示例：**

```python
from github_auto_sync.watcher import load_gitignore

# 从目录加载
patterns = load_gitignore("/path/to/project")

# 从文件加载
patterns = load_gitignore("/path/to/project/.gitignore")
```

#### `should_ignore(path, patterns)`

检查路径是否应该被忽略。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | `str \| Path` | 要检查的文件或目录路径 |
| `patterns` | `List[str]` | 忽略模式列表 |

**返回：** `bool` - 是否应该忽略

**示例：**

```python
from github_auto_sync.watcher import should_ignore

patterns = ["*.pyc", "__pycache__/", ".git/"]

if should_ignore("file.pyc", patterns):
    print("应该忽略")
```

#### `watch_directory(path, callback, ignore_patterns=None, batch_window=5.0, use_gitignore=True)`

便捷函数：创建并启动文件监控器。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | `str \| Path` | 必填 | 要监控的目录路径 |
| `callback` | `Callable[[List[FileChangeEvent]], None]` | 必填 | 回调函数 |
| `ignore_patterns` | `List[str] \| None` | `None` | 忽略模式列表 |
| `batch_window` | `float` | `5.0` | 批处理时间窗口 |
| `use_gitignore` | `bool` | `True` | 是否使用 .gitignore |

**返回：** `FileWatcher` - 已启动的 FileWatcher 实例

**示例：**

```python
from github_auto_sync.watcher import watch_directory

def on_changes(events):
    for e in events:
        print(f"{e.change_type.name}: {e.path}")

watcher = watch_directory("/path/to/watch", on_changes)
# ...
watcher.stop()
```

#### `create_default_ignore_patterns()`

创建默认的忽略模式列表。

**返回：** `List[str]`

**示例：**

```python
from github_auto_sync.watcher import create_default_ignore_patterns

patterns = create_default_ignore_patterns()
print(f"默认忽略模式数: {len(patterns)}")
```

---

## Git Operations 模块

Git 操作封装模块，基于 GitPython 提供高级 Git 操作接口。

### 异常类

#### `GitOperationError`

Git 操作错误异常。

### 函数

#### `init_repo(path)`

初始化新的 git 仓库。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | `str` | 仓库目录路径 |

**返回：** `Repo` - GitPython Repo 对象

**异常：**
- `GitOperationError` - 初始化失败

**示例：**

```python
from github_auto_sync.git_operations import init_repo

repo = init_repo("/path/to/new/repo")
```

#### `add_remote(path, name, url)`

添加远程仓库。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | `str` | 仓库路径 |
| `name` | `str` | 远程名称（如 'origin'） |
| `url` | `str` | 远程仓库 URL |

**异常：**
- `GitOperationError` - 添加失败

**示例：**

```python
from github_auto_sync.git_operations import add_remote

add_remote("/path/to/repo", "origin", "https://github.com/user/repo.git")
```

#### `commit(path, message, files=None)`

提交变更。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | `str` | 必填 | 仓库路径 |
| `message` | `str` | 必填 | 提交消息 |
| `files` | `List[str] \| None` | `None` | 要提交的文件列表，None 表示提交所有变更 |

**异常：**
- `GitOperationError` - 提交失败

**示例：**

```python
from github_auto_sync.git_operations import commit

# 提交所有变更
commit("/path/to/repo", "Initial commit")

# 提交指定文件
commit("/path/to/repo", "Update files", ["file1.txt", "file2.txt"])
```

#### `push(path, remote="origin", branch=None)`

推送变更到远程仓库。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | `str` | 必填 | 仓库路径 |
| `remote` | `str` | `"origin"` | 远程名称 |
| `branch` | `str \| None` | `None` | 分支名称，None 使用当前分支 |

**异常：**
- `GitOperationError` - 推送失败

**示例：**

```python
from github_auto_sync.git_operations import push

push("/path/to/repo")  # 推送到 origin 的当前分支
push("/path/to/repo", "origin", "main")  # 推送到 origin/main
```

#### `pull(path, remote="origin", branch=None)`

从远程仓库拉取变更。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | `str` | 必填 | 仓库路径 |
| `remote` | `str` | `"origin"` | 远程名称 |
| `branch` | `str \| None` | `None` | 分支名称 |

**异常：**
- `GitOperationError` - 拉取失败

**示例：**

```python
from github_auto_sync.git_operations import pull

pull("/path/to/repo")
```

#### `get_status(path)`

获取仓库状态。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | `str` | 仓库路径 |

**返回：** `Dict[str, Any]`

```python
{
    "is_dirty": True,                    # 是否有未提交变更
    "untracked_files": ["file1.txt"],    # 未跟踪文件列表
    "modified_files": ["file2.txt"],     # 修改的文件列表
    "staged_files": ["file3.txt"],       # 已暂存的文件列表
    "deleted_files": ["file4.txt"],      # 删除的文件列表
    "current_branch": "main"             # 当前分支
}
```

**异常：**
- `GitOperationError` - 获取状态失败

**示例：**

```python
from github_auto_sync.git_operations import get_status

status = get_status("/path/to/repo")
if status["is_dirty"]:
    print(f"未跟踪文件: {status['untracked_files']}")
```

#### `get_current_branch(path)`

获取当前分支名称。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | `str` | 仓库路径 |

**返回：** `str \| None` - 分支名称，如果处于分离 HEAD 状态则返回 None

**异常：**
- `GitOperationError` - 获取失败

#### `create_branch(path, branch_name, checkout=False)`

创建新分支。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | `str` | 必填 | 仓库路径 |
| `branch_name` | `str` | 必填 | 分支名称 |
| `checkout` | `bool` | `False` | 创建后是否切换到新分支 |

**异常：**
- `GitOperationError` - 创建失败

#### `checkout_branch(path, branch_name)`

切换到指定分支。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | `str` | 仓库路径 |
| `branch_name` | `str` | 分支名称 |

**异常：**
- `GitOperationError` - 切换失败

#### `clone_repo(url, path, branch=None)`

克隆远程仓库。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | `str` | 必填 | 远程仓库 URL |
| `path` | `str` | 必填 | 本地保存路径 |
| `branch` | `str \| None` | `None` | 要克隆的分支 |

**返回：** `Repo` - GitPython Repo 对象

**异常：**
- `GitOperationError` - 克隆失败

**示例：**

```python
from github_auto_sync.git_operations import clone_repo

repo = clone_repo("https://github.com/user/repo.git", "/path/to/clone")
```

#### `has_uncommitted_changes(path)`

检查是否有未提交的变更。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | `str` | 仓库路径 |

**返回：** `bool`

**异常：**
- `GitOperationError` - 检查失败

#### `get_last_commit(path)`

获取最后一次提交的信息。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | `str` | 仓库路径 |

**返回：** `Dict[str, Any] \| None`

```python
{
    "hash": "abc123...",           # 完整哈希
    "short_hash": "abc1234",       # 短哈希
    "message": "Commit message",   # 提交消息
    "author": "Author Name",       # 作者名
    "email": "author@example.com", # 作者邮箱
    "date": datetime,              # 提交日期
    "files_changed": ["file.txt"]  # 变更的文件列表
}
```

**异常：**
- `GitOperationError` - 获取失败

#### `is_git_repository(path)`

检查给定路径是否是 git 仓库。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | `str` | 要检查的路径 |

**返回：** `bool`

**示例：**

```python
from github_auto_sync.git_operations import is_git_repository

if is_git_repository("/path/to/check"):
    print("是 git 仓库")
```

#### `get_remotes(path)`

获取配置的远程仓库列表。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | `str` | 仓库路径 |

**返回：** `List[Dict[str, str]]`

```python
[
    {"name": "origin", "url": "https://github.com/user/repo.git"},
    {"name": "upstream", "url": "https://github.com/original/repo.git"}
]
```

**异常：**
- `GitOperationError` - 获取失败

#### `remove_remote(path, name)`

移除远程仓库。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | `str` | 仓库路径 |
| `name` | `str` | 远程名称 |

**异常：**
- `GitOperationError` - 移除失败

#### `fetch(path, remote="origin")`

从远程仓库获取更新。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | `str` | 必填 | 仓库路径 |
| `remote` | `str` | `"origin"` | 远程名称 |

**异常：**
- `GitOperationError` - 获取失败

#### `checkout_ours(path, file_path)`

在合并冲突时使用本地版本。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | `str` | 仓库路径 |
| `file_path` | `str` | 文件路径（相对于仓库根目录） |

**异常：**
- `GitOperationError` - 检出失败

#### `checkout_theirs(path, file_path)`

在合并冲突时使用远程版本。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | `str` | 仓库路径 |
| `file_path` | `str` | 文件路径（相对于仓库根目录） |

**异常：**
- `GitOperationError` - 检出失败
