"""
AI 代码描述生成模块

提供基于 AI 的代码变更分析功能，生成有意义的提交描述。
此模块与 code-describer SKILL 配合使用。

使用方法：
    from ai_description import generate_commit_description
    
    description = generate_commit_description(
        repo_path="./my-project",
        changed_files=["src/auth.py", "src/user.py"],
        language="zh",
    )
"""

import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


def is_ai_description_available() -> bool:
    """
    检查 AI 描述功能是否可用
    
    Returns:
        如果 AI 描述功能可用返回 True
    """
    # 此函数在 sync.py 中被调用，用于检查模块是否加载成功
    return True


def analyze_file_change(file_path: str, repo_path: str) -> dict:
    """
    分析单个文件的变更
    
    Args:
        file_path: 文件路径
        repo_path: 仓库根路径
        
    Returns:
        包含文件分析结果的字典
    """
    full_path = Path(repo_path) / file_path
    
    result = {
        "path": file_path,
        "type": "unknown",
        "purpose": "",
        "keywords": [],
    }
    
    # 根据文件扩展名判断类型
    if full_path.suffix == ".py":
        result["type"] = "python"
        result["keywords"].extend(["def", "class", "import"])
    elif full_path.suffix in [".js", ".ts"]:
        result["type"] = "javascript"
        result["keywords"].extend(["function", "const", "let", "var"])
    elif full_path.suffix in [".html", ".htm"]:
        result["type"] = "html"
    elif full_path.suffix == ".css":
        result["type"] = "css"
    elif full_path.suffix == ".md":
        result["type"] = "markdown"
        result["purpose"] = "文档"
    elif full_path.suffix in [".yml", ".yaml", ".json"]:
        result["type"] = "config"
        result["purpose"] = "配置"
    elif "test" in file_path.lower() or "spec" in file_path.lower():
        result["type"] = "test"
        result["purpose"] = "测试"
    
    # 根据文件路径判断用途
    if "src/" in file_path or "app/" in file_path:
        result["purpose"] = "核心功能"
    elif "test/" in file_path or "tests/" in file_path:
        result["purpose"] = "测试"
    elif "docs/" in file_path:
        result["purpose"] = "文档"
    elif "config/" in file_path or file_path.endswith((".yml", ".yaml", ".json", ".toml")):
        result["purpose"] = "配置"
    
    return result


def categorize_changes(changed_files: List[str]) -> dict:
    """
    对变更文件进行分类
    
    Args:
        changed_files: 变更文件列表
        
    Returns:
        分类结果字典
    """
    categories = {
        "feature": [],      # 新功能
        "fix": [],          # 修复
        "refactor": [],     # 重构
        "docs": [],         # 文档
        "config": [],       # 配置
        "test": [],         # 测试
        "other": [],        # 其他
    }
    
    for file_path in changed_files:
        file_lower = file_path.lower()
        
        # 根据文件名和路径判断类别
        if any(kw in file_lower for kw in ["fix", "bug", "error", "patch"]):
            categories["fix"].append(file_path)
        elif any(kw in file_lower for kw in ["test", "spec", "_test.", "_spec."]):
            categories["test"].append(file_path)
        elif any(kw in file_lower for kw in ["doc", "readme", "md", "doc/", "docs/"]):
            categories["docs"].append(file_path)
        elif any(kw in file_lower for kw in ["config", "setting", ".yml", ".yaml", ".json", ".toml"]):
            categories["config"].append(file_path)
        elif any(kw in file_lower for kw in ["refactor", "restructure", "clean", "optimize"]):
            categories["refactor"].append(file_path)
        elif any(kw in file_lower for kw in ["add", "new", "create", "implement", "feature"]):
            categories["feature"].append(file_path)
        else:
            categories["other"].append(file_path)
    
    return categories


def generate_commit_description(
    repo_path: str,
    changed_files: List[str],
    language: str = "auto",
    include_details: bool = True,
    max_length: int = 500,
) -> Optional[str]:
    """
    生成提交描述
    
    此函数分析代码变更并生成有意义的提交描述。
    注意：这是一个基础实现，实际使用时应该由 AI 根据 SKILL 指导生成更准确的描述。
    
    Args:
        repo_path: 仓库路径
        changed_files: 变更的文件列表
        language: 描述语言 ("auto", "zh", "en")
        include_details: 是否包含详细变更列表
        max_length: 最大描述长度
        
    Returns:
        生成的提交描述，如果生成失败返回 None
    """
    if not changed_files:
        return None
    
    try:
        # 对变更进行分类
        categories = categorize_changes(changed_files)
        
        # 确定主要变更类型
        primary_category = None
        for cat, files in categories.items():
            if files:
                primary_category = cat
                break
        
        # 根据语言选择标签
        if language.lower() in ["zh", "zh-cn", "zh-tw", "auto"]:
            category_labels = {
                "feature": "功能",
                "fix": "修复",
                "refactor": "重构",
                "docs": "文档",
                "config": "配置",
                "test": "测试",
                "other": "更新",
            }
            
            # 生成中文描述
            label = category_labels.get(primary_category, "更新")
            
            # 生成简短描述
            if len(changed_files) == 1:
                file_name = Path(changed_files[0]).name
                short_desc = f"更新 {file_name}"
            else:
                # 找出主要变更的文件类型
                file_types = set()
                for f in changed_files:
                    ext = Path(f).suffix
                    if ext:
                        file_types.add(ext)
                
                if file_types:
                    type_str = ", ".join(sorted(file_types))[:30]
                    short_desc = f"更新 {len(changed_files)} 个文件 ({type_str})"
                else:
                    short_desc = f"更新 {len(changed_files)} 个文件"
            
            # 构建完整描述
            description = f"[{label}] {short_desc}"
            
            # 添加详细列表
            if include_details and len(changed_files) <= 10:
                description += "\n"
                for file_path in changed_files[:5]:  # 最多显示5个文件
                    # 分析文件
                    analysis = analyze_file_change(file_path, repo_path)
                    purpose = analysis.get("purpose", "")
                    if purpose:
                        description += f"\n- {file_path} ({purpose})"
                    else:
                        description += f"\n- {file_path}"
                
                if len(changed_files) > 5:
                    description += f"\n- ... 及其他 {len(changed_files) - 5} 个文件"
            
        else:
            # 生成英文描述
            category_labels = {
                "feature": "feat",
                "fix": "fix",
                "refactor": "refactor",
                "docs": "docs",
                "config": "config",
                "test": "test",
                "other": "update",
            }
            
            label = category_labels.get(primary_category, "update")
            
            if len(changed_files) == 1:
                file_name = Path(changed_files[0]).name
                short_desc = f"update {file_name}"
            else:
                short_desc = f"update {len(changed_files)} files"
            
            description = f"[{label}] {short_desc}"
            
            if include_details and len(changed_files) <= 10:
                description += "\n"
                for file_path in changed_files[:5]:
                    analysis = analyze_file_change(file_path, repo_path)
                    purpose = analysis.get("purpose", "")
                    if purpose:
                        description += f"\n- {file_path} ({purpose})"
                    else:
                        description += f"\n- {file_path}"
                
                if len(changed_files) > 5:
                    description += f"\n- ... and {len(changed_files) - 5} more files"
        
        # 截断到最大长度
        if len(description) > max_length:
            description = description[:max_length - 3] + "..."
        
        return description
        
    except Exception as e:
        logger.error(f"Failed to generate commit description: {e}")
        return None


def generate_description_with_ai(
    repo_path: str,
    changed_files: List[str],
    language: str = "auto",
) -> Optional[str]:
    """
    使用 AI 生成提交描述（占位函数）
    
    此函数应该由 AI 实现，根据 code-describer SKILL 的指导
    分析代码并生成准确的描述。
    
    Args:
        repo_path: 仓库路径
        changed_files: 变更的文件列表
        language: 描述语言
        
    Returns:
        AI 生成的提交描述
    """
    # 这是一个占位符，实际的 AI 描述生成应该由 AI 完成
    # AI 应该：
    # 1. 读取变更文件的内容
    # 2. 分析代码的功能和变更
    # 3. 根据 SKILL.md 的指导生成描述
    
    logger.debug("AI description generation should be handled by the AI assistant")
    return None
