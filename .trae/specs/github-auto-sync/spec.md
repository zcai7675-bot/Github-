# GitHub Auto Sync - Project Specification

## Project Name
**GitHub Auto Sync** (codename: `github-auto-sync`)

## Why
Developers often need to automatically synchronize their local code projects with GitHub repositories without manual git operations. This tool replicates the core functionality of GitHub's Dataclaw tool, providing seamless automatic uploading of code content from specified folders to GitHub repositories, compatible with any IDE or CLI environment.

## What Changes
- Create a Python-based CLI tool for automatic GitHub repository synchronization
- Implement folder watching capabilities for automatic change detection
- Provide GitHub API integration for repository operations
- Support configuration via YAML/JSON config files
- Include IDE-agnostic integration through CLI and environment variables
- Support multiple repository management
- Implement intelligent change detection and batch uploads

## Impact
- Affected systems: Local file system, GitHub API, Git operations
- Key technologies: Python, GitHub REST API, GitPython, Watchdog (file monitoring)

## ADDED Requirements

### Requirement: Project Structure and Setup
The system SHALL provide a well-organized Python project structure.

#### Scenario: Project initialization
- **WHEN** the user installs the package
- **THEN** all required dependencies are installed and CLI commands are available

### Requirement: GitHub Authentication
The system SHALL support secure GitHub authentication.

#### Scenario: Token-based authentication
- **WHEN** the user provides a GitHub Personal Access Token
- **THEN** the system can authenticate and perform repository operations

#### Scenario: Credential storage
- **WHEN** the user authenticates successfully
- **THEN** credentials are securely stored in the system's keyring or environment

### Requirement: Repository Management
The system SHALL support creating and managing GitHub repositories.

#### Scenario: Create new repository
- **WHEN** the user specifies a new repository name
- **THEN** the system creates a private/public repository on GitHub

#### Scenario: Link existing repository
- **WHEN** the user provides an existing repository URL
- **THEN** the system links the local folder to the remote repository

### Requirement: Folder Synchronization
The system SHALL automatically synchronize local folders to GitHub repositories.

#### Scenario: Initial sync
- **WHEN** the user initiates sync for a folder
- **THEN** all files are uploaded to the specified GitHub repository

#### Scenario: Incremental sync
- **WHEN** files are modified in the watched folder
- **THEN** only changed files are committed and pushed

#### Scenario: Batch uploads
- **WHEN** multiple files change within a short time window
- **THEN** changes are batched into a single commit

### Requirement: File Watching
The system SHALL monitor folders for changes.

#### Scenario: Real-time monitoring
- **WHEN** the watch mode is enabled
- **THEN** file system changes are detected in real-time

#### Scenario: Ignore patterns
- **WHEN** files match configured ignore patterns (e.g., .gitignore)
- **THEN** they are excluded from synchronization

### Requirement: CLI Interface
The system SHALL provide a comprehensive command-line interface.

#### Scenario: Initialize configuration
- **WHEN** the user runs `github-auto-sync init`
- **THEN** a configuration file is created

#### Scenario: Start synchronization
- **WHEN** the user runs `github-auto-sync sync`
- **THEN** the specified folder is synchronized to GitHub

#### Scenario: Watch mode
- **WHEN** the user runs `github-auto-sync watch`
- **THEN** the folder is monitored for changes and auto-synced

#### Scenario: Repository listing
- **WHEN** the user runs `github-auto-sync list`
- **THEN** all configured repositories are displayed

### Requirement: Configuration Management
The system SHALL support flexible configuration options.

#### Scenario: Config file support
- **WHEN** a `.github-auto-sync.yml` file exists
- **THEN** settings are loaded from the configuration file

#### Scenario: Environment variables
- **WHEN** environment variables are set (e.g., `GITHUB_TOKEN`)
- **THEN** they override config file settings

#### Scenario: Command-line arguments
- **WHEN** CLI arguments are provided
- **THEN** they override both config and environment settings

### Requirement: IDE Integration
The system SHALL be compatible with any IDE or editor.

#### Scenario: VS Code integration
- **WHEN** the user configures VS Code tasks
- **THEN** the tool can be invoked from the IDE

#### Scenario: JetBrains integration
- **WHEN** the user configures external tools
- **THEN** the tool can be invoked from JetBrains IDEs

#### Scenario: Generic IDE support
- **WHEN** the IDE supports CLI tool execution
- **THEN** the tool can be integrated without custom plugins

## Technical Specifications

### Core Technologies
- **Language**: Python 3.8+
- **Git Operations**: GitPython library
- **GitHub API**: PyGithub library
- **File Watching**: Watchdog library
- **CLI Framework**: Click or Typer
- **Configuration**: PyYAML

### Supported Platforms
- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 18.04+, CentOS 7+)

### Security Requirements
- GitHub tokens stored in system keyring (keyring library)
- Support for GitHub Personal Access Tokens (classic and fine-grained)
- No hardcoded credentials
- Support for .env files (python-dotenv)

### Performance Requirements
- Handle repositories up to 100MB efficiently
- Batch file changes within 5-second windows
- Maximum 100 files per batch commit
- Support for .gitignore patterns

## Functional Description

### Key Features

1. **Automatic Synchronization**: Automatically detects file changes and syncs them to GitHub without manual git commands.

2. **Multi-Repository Support**: Manage and sync multiple local folders to different GitHub repositories from a single tool.

3. **Smart Change Detection**: Uses file system watchers to detect changes in real-time and batch them intelligently.

4. **IDE Agnostic**: Works with any IDE or text editor through CLI integration, no plugins required.

5. **Flexible Configuration**: Configure via YAML files, environment variables, or command-line arguments.

6. **Secure Authentication**: Securely stores GitHub credentials using system keyring services.

7. **Selective Sync**: Respect .gitignore patterns and support custom ignore rules.

8. **Repository Management**: Create new repositories or link to existing ones directly from the CLI.

### Use Cases

1. **Backup Workflow**: Developers can automatically backup their code projects to GitHub as they work.

2. **Portfolio Management**: Designers and developers can maintain live portfolios that update automatically.

3. **Documentation Sync**: Technical writers can sync documentation folders to GitHub repositories.

4. **Multi-Project Management**: Manage synchronization settings for multiple projects from a single tool.

5. **CI/CD Integration**: Trigger CI/CD pipelines automatically when code is synced to GitHub.

### Technical Architecture

```
github-auto-sync/
├── src/
│   └── github_auto_sync/
│       ├── __init__.py
│       ├── cli.py              # CLI interface
│       ├── config.py           # Configuration management
│       ├── auth.py             # GitHub authentication
│       ├── sync.py             # Synchronization logic
│       ├── watcher.py          # File system watcher
│       └── github_client.py    # GitHub API client
├── tests/
├── docs/
├── requirements.txt
├── setup.py
└── README.md
```

### CLI Commands

- `github-auto-sync init` - Initialize configuration
- `github-auto-sync auth` - Authenticate with GitHub
- `github-auto-sync sync [folder]` - Sync folder to GitHub
- `github-auto-sync watch [folder]` - Watch folder for changes
- `github-auto-sync list` - List configured repositories
- `github-auto-sync config` - Manage configuration

### Configuration File Format

```yaml
# .github-auto-sync.yml
github:
  token: ${GITHUB_TOKEN}
  username: your-username

repositories:
  - name: my-project
    local_path: /path/to/project
    remote_url: https://github.com/username/my-project
    branch: main
    auto_sync: true
    ignore_patterns:
      - "*.log"
      - "node_modules/"
      - ".env"

sync:
  batch_window: 5  # seconds
  max_files_per_commit: 100
  commit_message_template: "Auto-sync: {timestamp}"
```
