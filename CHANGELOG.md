# Changelog

所有关于 GitHub Auto Sync 的显著变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 新增
- 初始项目结构
- CLI 命令行界面
- GitHub API 集成
- 文件系统监控功能
- 自动同步功能
- 配置管理
- 安全凭证存储

## [0.1.0] - 2024-XX-XX

### 新增
- 项目初始化
- 基础同步功能
- 配置文件支持 (YAML)
- 命令行工具 (CLI)
- GitHub Token 认证
- 文件变化监控
- 自动提交和推送

### 安全
- 使用 keyring 安全存储凭证
- 支持环境变量配置

---

## 版本说明

- **主版本号 (X.y.z)**: 当做了不兼容的 API 修改
- **次版本号 (x.Y.z)**: 当做了向下兼容的功能性新增
- **修订号 (x.y.Z)**: 当做了向下兼容的问题修正

## 标签说明

- `Added` 新添加的功能。
- `Changed` 对现有功能的变更。
- `Deprecated` 已经不建议使用，即将移除的功能。
- `Removed` 已经移除的功能。
- `Fixed` 对 bug 的修复。
- `Security` 对安全性的改进。
