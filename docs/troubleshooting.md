# GitHub Auto Sync 故障排除指南

本文档提供了常见问题的诊断和解决方案。

## 目录

- [常见问题和解决方案](#常见问题和解决方案)
- [认证问题](#认证问题)
- [同步失败](#同步失败)
- [Git 冲突](#git-冲突)
- [网络问题](#网络问题)
- [如何调试](#如何调试)

---

## 常见问题和解决方案

### 问题：命令未找到

**症状：**
```bash
$ github-auto-sync
bash: github-auto-sync: command not found
```

**解决方案：**

1. **检查安装：**
   ```bash
   pip list | grep github-auto-sync
   ```

2. **重新安装：**
   ```bash
   pip install --upgrade github-auto-sync
   ```

3. **检查 PATH：**
   ```bash
   which python
   python -m site
   ```
   确保 Python 的 scripts 目录在 PATH 中。

4. **使用 Python 模块方式运行：**
   ```bash
   python -m github_auto_sync
   ```

---

### 问题：配置文件未找到

**症状：**
```
✗ 错误: 未找到配置文件。请运行 'github-auto-sync init' 初始化配置。
```

**解决方案：**

1. **初始化配置：**
   ```bash
   github-auto-sync init
   ```

2. **指定配置文件路径：**
   ```bash
   github-auto-sync -c /path/to/config.yml sync
   ```

3. **检查当前目录：**
   ```bash
   ls -la .github-auto-sync.yml
   ```

4. **向上查找配置：**
   工具会自动向上级目录查找配置文件，确保你在正确的目录中运行命令。

---

### 问题：权限被拒绝

**症状：**
```
✗ 权限不足: 无法访问仓库
⚠ 请检查您的 GitHub Token 权限
```

**解决方案：**

1. **检查 Token 权限：**
   - 访问 GitHub Settings -> Developer settings -> Personal access tokens
   - 确保 token 有以下权限：
     - `repo` - 访问仓库
     - `workflow` - 访问 GitHub Actions（可选）

2. **重新生成 Token：**
   - 在 GitHub 上删除旧 token
   - 创建新 token 并复制
   - 重新登录：
     ```bash
     github-auto-sync auth logout
     github-auto-sync auth login -t ghp_new_token
     ```

3. **验证 Token：**
   ```bash
   github-auto-sync auth status
   ```

---

## 认证问题

### 问题：Token 验证失败

**症状：**
```
✗ Token 验证失败: Token 无效或已过期
```

**诊断步骤：**

1. **检查 Token 格式：**
   - Classic token: `ghp_xxxxxxxx` (40 位十六进制)
   - Fine-grained token: `github_pat_xxx`

2. **验证 Token 有效性：**
   ```bash
   curl -H "Authorization: Bearer ghp_your_token" https://api.github.com/user
   ```

3. **检查 Token 是否过期：**
   - 在 GitHub 设置中查看 token 的过期日期

**解决方案：**

1. **创建新 Token：**
   - 访问 https://github.com/settings/tokens
   - 点击 "Generate new token"
   - 选择适当的权限范围
   - 复制新生成的 token

2. **更新认证：**
   ```bash
   github-auto-sync auth login -t ghp_new_token
   ```

3. **使用环境变量（推荐用于 CI/CD）：**
   ```bash
   export GITHUB_TOKEN="ghp_your_token"
   github-auto-sync sync
   ```

---

### 问题：系统密钥环访问失败

**症状：**
```
✗ 认证成功，但存储凭证失败: 无法访问系统密钥环
```

**原因：**
- Linux: 未安装或运行 keyring 服务
- macOS: Keychain 访问权限问题
- Windows: Windows Credential Manager 访问问题

**解决方案：**

**Linux：**
```bash
# 安装 keyring 依赖
sudo apt-get install libsecret-1-dev  # Debian/Ubuntu
sudo yum install libsecret-devel      # RHEL/CentOS

# 或使用不存储凭证的方式
github-auto-sync auth login -t ghp_token --no-store
```

**macOS：**
```bash
# 重置钥匙串权限
security unlock-keychain

# 或使用环境变量
export GITHUB_TOKEN="ghp_your_token"
```

**Windows：**
```powershell
# 以管理员身份运行 PowerShell
# 或使用环境变量
$env:GITHUB_TOKEN="ghp_your_token"
```

---

### 问题：环境变量未生效

**症状：**
```
✗ 未提供 token，且未找到 GITHUB_TOKEN 环境变量
```

**诊断步骤：**

1. **检查环境变量：**
   ```bash
   # Linux/macOS
   echo $GITHUB_TOKEN
   
   # Windows PowerShell
   $env:GITHUB_TOKEN
   
   # Windows CMD
   echo %GITHUB_TOKEN%
   ```

2. **检查变量名拼写：**
   - 正确：`GITHUB_TOKEN`
   - 错误：`github_token`, `GITHUB-TOKEN`, `GH_TOKEN`

**解决方案：**

1. **正确设置环境变量：**
   ```bash
   # Linux/macOS (当前会话)
   export GITHUB_TOKEN="ghp_your_token"
   
   # Linux/macOS (永久)
   echo 'export GITHUB_TOKEN="ghp_your_token"' >> ~/.bashrc
   source ~/.bashrc
   
   # Windows PowerShell (当前会话)
   $env:GITHUB_TOKEN="ghp_your_token"
   
   # Windows PowerShell (永久)
   [Environment]::SetEnvironmentVariable("GITHUB_TOKEN", "ghp_your_token", "User")
   ```

2. **使用 .env 文件：**
   ```bash
   # 创建 .env 文件
echo "GITHUB_TOKEN=ghp_your_token" > .env
   echo "GITHUB_USERNAME=your_username" >> .env
   ```
   
   工具会自动加载当前目录的 `.env` 文件。

---

## 同步失败

### 问题：初始同步失败

**症状：**
```
✗ 同步失败: Failed to initialize git repository
或
✗ 同步失败: Failed to create GitHub repository
```

**诊断步骤：**

1. **检查本地路径：**
   ```bash
   ls -la /path/to/local/repo
   ```

2. **检查 GitHub 仓库是否存在：**
   ```bash
   github-auto-sync repo list | grep repo-name
   ```

3. **检查网络连接：**
   ```bash
   curl https://api.github.com
   ```

**解决方案：**

1. **路径不存在：**
   ```bash
   mkdir -p /path/to/local/repo
   github-auto-sync sync repo-name --initial
   ```

2. **GitHub 仓库已存在：**
   ```bash
   # 删除现有仓库（谨慎操作！）
   github-auto-sync repo delete repo-name
   # 或
   # 更新配置使用现有仓库
   github-auto-sync config set repositories.0.remote_url https://github.com/user/existing-repo.git
   ```

3. **使用试运行模式排查：**
   ```bash
   github-auto-sync sync repo-name --initial --dry-run -v
   ```

---

### 问题：推送失败

**症状：**
```
✗ 同步失败: push failed
或
✗ Failed to push to remote: Authentication failed
```

**常见原因和解决方案：**

1. **认证问题：**
   - 重新登录：`github-auto-sync auth login`
   - 检查 token 是否有 `repo` 权限

2. **分支保护：**
   - 检查 GitHub 仓库的分支保护规则
   - 可能需要使用 Pull Request 流程

3. **远程 URL 错误：**
   ```bash
   # 检查远程配置
   cd /path/to/repo
   git remote -v
   
   # 更新远程 URL
   github-auto-sync config set repositories.0.remote_url https://github.com/user/repo.git
   ```

4. **网络代理问题：**
   ```bash
   # 设置代理
   export HTTPS_PROXY=http://proxy.company.com:8080
   git config --global http.proxy http://proxy.company.com:8080
   ```

---

### 问题：拉取失败

**症状：**
```
✗ Failed to pull from remote: merge conflict
```

**解决方案：**

1. **禁用自动拉取：**
   ```bash
   github-auto-sync config set sync.auto_pull false
   ```

2. **手动解决冲突后同步：**
   ```bash
   cd /path/to/repo
   git pull origin main
   # 解决冲突
   git add .
   git commit -m "Resolve conflicts"
   github-auto-sync sync repo-name
   ```

3. **使用覆盖策略：**
   ```bash
   github-auto-sync config set sync.conflict_strategy overwrite
   github-auto-sync sync repo-name
   ```

---

### 问题：文件未同步

**症状：**
某些文件没有被同步到 GitHub。

**诊断步骤：**

1. **检查忽略模式：**
   ```bash
   github-auto-sync config get repositories.0.ignore_patterns
   ```

2. **检查 .gitignore：**
   ```bash
   cat /path/to/repo/.gitignore
   ```

3. **检查文件状态：**
   ```bash
   cd /path/to/repo
   git status
   ```

**解决方案：**

1. **更新忽略模式：**
   ```yaml
   # .github-auto-sync.yml
   repositories:
     - name: "my-project"
       ignore_patterns:
         - ".git/"
         - "__pycache__/"
         # 移除不需要的忽略模式
   ```

2. **强制添加被忽略的文件：**
   ```bash
   cd /path/to/repo
   git add -f path/to/file
   github-auto-sync sync my-project
   ```

---

## Git 冲突

### 问题：合并冲突

**症状：**
```
⚠ Conflicts detected: ['file1.txt', 'file2.txt']
✗ 同步失败: Merge conflicts detected
```

**解决方案：**

#### 方案 1：使用本地版本（覆盖远程）

```bash
# 设置冲突策略
github-auto-sync config set sync.conflict_strategy overwrite

# 处理冲突
result = manager.handle_conflicts(strategy="overwrite")
```

#### 方案 2：使用远程版本（放弃本地修改）

```bash
cd /path/to/repo

# 放弃本地修改，使用远程版本
git fetch origin
git reset --hard origin/main

# 重新同步
github-auto-sync sync my-project
```

#### 方案 3：手动解决冲突

```bash
cd /path/to/repo

# 查看冲突文件
git diff --name-only --diff-filter=U

# 编辑冲突文件，解决冲突
# 冲突标记格式：
# <<<<<<< HEAD
# 本地版本
# =======
# 远程版本
# >>>>>>> origin/main

# 标记冲突已解决
git add <resolved-file>

# 提交解决
git commit -m "Resolve merge conflicts"

# 推送
git push origin main
```

#### 方案 4：跳过冲突文件

```bash
# 设置冲突策略为跳过
github-auto-sync config set sync.conflict_strategy skip

# 同步其他文件
github-auto-sync sync my-project
```

---

### 问题：冲突持续发生

**症状：**
每次同步都出现冲突。

**原因和解决方案：**

1. **多设备同时修改：**
   - 在同步前总是先拉取更新
   - 启用自动拉取：`github-auto-sync config set sync.auto_pull true`

2. **行尾符问题（Windows/Linux）：**
   ```bash
   # 配置 Git 自动处理行尾符
   git config --global core.autocrlf true   # Windows
   git config --global core.autocrlf input  # Linux/macOS
   ```

3. **文件权限变更：**
   ```bash
   # 忽略文件权限变更
   git config --global core.filemode false
   ```

---

## 网络问题

### 问题：连接超时

**症状：**
```
✗ 验证超时，请检查网络连接
或
✗ Network error: Connection timed out
```

**诊断步骤：**

1. **检查网络连接：**
   ```bash
   ping github.com
   curl -I https://api.github.com
   ```

2. **检查 DNS：**
   ```bash
   nslookup github.com
   ```

3. **检查防火墙：**
   ```bash
   # 检查端口 443
   telnet github.com 443
   ```

**解决方案：**

1. **使用代理：**
   ```bash
   export HTTPS_PROXY=http://proxy.company.com:8080
   export HTTP_PROXY=http://proxy.company.com:8080
   ```

2. **增加超时时间：**
   ```bash
   # 在 Python 代码中设置
   import socket
   socket.setdefaulttimeout(60)
   ```

3. **使用镜像（仅限 Git 操作）：**
   ```bash
   # 使用镜像加速
   git config --global url."https://mirror.example.com/".insteadOf "https://github.com/"
   ```

---

### 问题：API 速率限制

**症状：**
```
✗ API 速率限制: API rate limit exceeded
⚠ 请稍后重试或检查您的 GitHub API 配额
```

**诊断：**

```bash
# 检查当前速率限制
curl -H "Authorization: Bearer ghp_token" https://api.github.com/rate_limit
```

**解决方案：**

1. **等待重置：**
   - 未认证：每小时 60 次请求
   - 已认证：每小时 5,000 次请求
   - 重置时间会在错误消息中显示

2. **使用缓存：**
   ```bash
   # 减少不必要的 API 调用
   github-auto-sync config set sync.batch_window 60
   ```

3. **使用 GitHub App 认证（企业用户）：**
   - 获得更高的速率限制

---

### 问题：SSL 证书错误

**症状：**
```
✗ SSL certificate verify failed
```

**解决方案：**

1. **更新证书：**
   ```bash
   # macOS
   brew install ca-certificates
   
   # Ubuntu/Debian
   sudo apt-get update && sudo apt-get install ca-certificates
   
   # RHEL/CentOS
   sudo yum install ca-certificates
   ```

2. **临时禁用 SSL 验证（不推荐用于生产）：**
   ```bash
   export GIT_SSL_NO_VERIFY=1
   git config --global http.sslVerify false
   ```

---

## 如何调试

### 启用详细日志

**方法 1：使用 -v 选项**
```bash
github-auto-sync -v sync my-project
github-auto-sync -v watch my-project
```

**方法 2：设置日志级别**
```bash
# 环境变量
export GITHUB_LOG_LEVEL=DEBUG

# 或配置文件
github-auto-sync config set logging.level DEBUG
```

**方法 3：使用日志文件**
```bash
github-auto-sync config set logging.file /path/to/sync.log
github-auto-sync sync my-project
```

---

### 使用试运行模式

试运行模式不会实际执行任何操作，只显示将要执行的操作：

```bash
github-auto-sync sync my-project --dry-run -v
```

输出示例：
```
⚠ 试运行模式 - 不会实际执行任何操作
ℹ [DRY RUN] Would initialize git repository at: /path/to/repo
ℹ [DRY RUN] Would create GitHub repository: my-project
ℹ [DRY RUN] Would commit with message: Initial sync: add 10 files
ℹ [DRY RUN] Would push changes
```

---

### 检查 Git 状态

```bash
cd /path/to/repo

# 查看仓库状态
git status

# 查看远程配置
git remote -v

# 查看分支
git branch -a

# 查看日志
git log --oneline -10

# 查看未跟踪文件
git ls-files --others --exclude-standard
```

---

### 检查配置文件

```bash
# 显示完整配置
github-auto-sync config show

# 检查特定配置项
github-auto-sync config get github.token
github-auto-sync config get repositories.0.local_path
github-auto-sync config get sync.conflict_strategy
```

---

### Python 调试

在 Python 代码中调试：

```python
import logging

# 启用调试日志
logging.basicConfig(level=logging.DEBUG)

from github_auto_sync.config import Config
from github_auto_sync.sync import SyncManager

# 加载配置
config = Config.load()
print(f"Config path: {config.config_path}")
print(f"Repositories: {config.repositories}")

# 创建同步管理器
repo_config = config.get_repository("my-project")
manager = SyncManager(config, repo_config, dry_run=True)

# 执行同步并检查详细结果
result = manager.initial_sync()
print(f"Success: {result.success}")
print(f"Status: {result.status}")
print(f"Message: {result.message}")
print(f"Files synced: {result.files_synced}")
print(f"Files failed: {result.files_failed}")
print(f"Commit hash: {result.commit_hash}")
print(f"Duration: {result.duration}")
print(f"Details: {result.details}")
```

---

### 常见问题检查清单

在提交 Issue 前，请检查以下项目：

- [ ] 使用的是最新版本：`pip install --upgrade github-auto-sync`
- [ ] Python 版本 >= 3.8：`python --version`
- [ ] Git 版本 >= 2.0：`git --version`
- [ ] 配置文件存在且格式正确：`github-auto-sync config show`
- [ ] 认证有效：`github-auto-sync auth status`
- [ ] 网络连接正常：`curl https://api.github.com`
- [ ] 本地路径存在且可访问
- [ ] 有足够的磁盘空间
- [ ] 有写入权限

---

### 收集诊断信息

如果问题仍然存在，请收集以下信息：

```bash
# 1. 版本信息
github-auto-sync --version
python --version
git --version

# 2. 配置信息（移除敏感信息）
github-auto-sync config show | grep -v token

# 3. 认证状态
github-auto-sync auth status

# 4. 详细日志（试运行）
github-auto-sync sync my-project --dry-run -v 2>&1

# 5. 系统信息
uname -a  # Linux/macOS
systeminfo  # Windows

# 6. 网络测试
curl -v https://api.github.com/rate_limit 2>&1 | head -20
```

---

### 获取帮助

如果以上方法都无法解决问题：

1. **查看文档：**
   - [使用指南](./usage.md)
   - [API 文档](./api.md)

2. **搜索已知问题：**
   - 查看 GitHub Issues 页面

3. **提交新 Issue：**
   提供以下信息：
   - 问题描述
   - 复现步骤
   - 预期行为
   - 实际行为
   - 环境信息（OS、Python 版本等）
   - 错误日志（使用 `-v` 选项）
