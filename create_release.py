"""
创建 GitHub Release 并上传 ZIP 文件
"""
import os
import sys
import json
import urllib.request
import urllib.error
import base64

# 配置
REPO_OWNER = "zcai7675-bot"
REPO_NAME = "Github-"
TAG_NAME = "v1.0.0"
RELEASE_NAME = "GitHub Auto Sync v1.0.0"
ZIP_FILE = "github-auto-sync-v1.0.0.zip"
GITHUB_TOKEN = ""  # 请在运行前设置您的 GitHub Token

def create_release(token):
    """创建 GitHub Release"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    data = {
        "tag_name": TAG_NAME,
        "name": RELEASE_NAME,
        "body": """## GitHub Auto Sync v1.0.0

### 功能特性
- 自动文件监控和同步
- GitHub API 集成
- 安全认证机制
- AI 智能提交描述
- 完整测试套件

### 安装
```bash
pip install -e .
```

### 使用
```bash
github-auto-sync init
github-auto-sync auth login
github-auto-sync sync
```""",
        "draft": False,
        "prerelease": False
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print(f"✅ Release 创建成功: {result['html_url']}")
            return result['upload_url'].replace("{?name,label}", "")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ 创建 Release 失败: {e.code}")
        print(f"错误信息: {error_body}")
        return None

def upload_asset(upload_url, token, file_path):
    """上传 ZIP 文件到 Release"""
    file_name = os.path.basename(file_path)
    url = f"{upload_url}?name={file_name}"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/zip"
    }
    
    with open(file_path, "rb") as f:
        data = f.read()
    
    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print(f"✅ 文件上传成功: {result['browser_download_url']}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ 上传文件失败: {e.code}")
        print(f"错误信息: {error_body}")
        return False

def main():
    # 使用配置的 GitHub Token
    token = GITHUB_TOKEN
    
    if not token or token == "your_token_here":
        print("❌ 请在脚本中设置 GITHUB_TOKEN")
        sys.exit(1)
    
    # 检查 ZIP 文件是否存在
    if not os.path.exists(ZIP_FILE):
        print(f"❌ 找不到文件: {ZIP_FILE}")
        sys.exit(1)
    
    print(f"🚀 创建 Release: {TAG_NAME}")
    upload_url = create_release(token)
    
    if upload_url:
        print(f"📦 上传文件: {ZIP_FILE}")
        if upload_asset(upload_url, token, ZIP_FILE):
            print("\n✅ 全部完成!")
            print(f"🔗 Release 地址: https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/tag/{TAG_NAME}")
        else:
            sys.exit(1)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
