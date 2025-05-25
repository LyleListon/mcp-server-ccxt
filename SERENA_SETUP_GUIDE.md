# Serena Setup Guide for Augment Code Extension

## 🎯 Overview
This guide will help you set up Serena (a powerful coding agent toolkit) to work with the Augment Code extension in VSCode Insiders.

## 📁 Current Setup
- **Serena Location**: `/home/lylepaul78/Documents/augment-projects/MayArbi/serena`
- **Filesystem MCP Server**: `/home/lylepaul78/Documents/augment-projects/MayArbi/filesystem-mcp-server`
- **Projects Configured**: 
  - filesystem-mcp-server (TypeScript)
  - serena-project (Python)

## 🔧 Configuration Files Created

### 1. Serena Main Config (`serena/serena_config.yml`)
```yaml
enable_project_activation: True
projects:
  - filesystem-mcp-server.yml
  - serena-project.yml
gui_log_window: False
gui_log_level: 20
```

### 2. Project Configurations

#### Filesystem MCP Server Project (`serena/filesystem-mcp-server.yml`)
```yaml
project_root: /home/lylepaul78/Documents/augment-projects/MayArbi/filesystem-mcp-server
language: typescript
ignore_all_files_in_gitignore: true
ignored_paths: 
  - node_modules/**
  - dist/**
  - logs/**
  - "*.log"
read_only: false
excluded_tools: []
```

#### Serena Project (`serena/serena-project.yml`)
```yaml
project_root: /home/lylepaul78/Documents/augment-projects/MayArbi/serena
language: python
ignore_all_files_in_gitignore: true
ignored_paths: 
  - test/**
  - "*.pyc"
  - __pycache__/**
  - .pytest_cache/**
read_only: false
excluded_tools: []
```

## 🚀 Starting Serena MCP Server

### Option 1: Using the Start Script
```bash
./start-serena.sh --project-file /home/lylepaul78/Documents/augment-projects/MayArbi/serena/filesystem-mcp-server.yml
```

### Option 2: Direct UV Command
```bash
cd /home/lylepaul78/Documents/augment-projects/MayArbi/serena
uv run serena-mcp-server --project-file filesystem-mcp-server.yml
```

### Option 3: With Project Activation (Recommended)
```bash
cd /home/lylepaul78/Documents/augment-projects/MayArbi/serena
uv run serena-mcp-server
# Then in Augment, you can switch projects using: "activate project filesystem-mcp-server"
```

## 🔌 Augment Code Extension Integration

### Method 1: MCP Server Connection
1. Open VSCode Insiders with Augment Code extension
2. Configure Augment to connect to Serena MCP server
3. Use one of these connection methods:

#### Stdio Connection (Recommended)
```json
{
  "command": "/home/lylepaul78/.local/bin/uv",
  "args": [
    "run",
    "--directory",
    "/home/lylepaul78/Documents/augment-projects/MayArbi/serena",
    "serena-mcp-server"
  ]
}
```

#### SSE Connection (Alternative)
If stdio doesn't work, start Serena in SSE mode:
```bash
cd /home/lylepaul78/Documents/augment-projects/MayArbi/serena
uv run serena-mcp-server --transport sse --port 9121
```
Then connect Augment to: `http://localhost:9121`

## 🛠️ Serena Tools Available

Serena provides 30+ powerful tools including:
- `find_symbol` - Search for symbols in code
- `get_symbols_overview` - Get overview of file/directory symbols
- `read_file` - Read project files
- `create_text_file` - Create new files
- `replace_symbol_body` - Replace function/class definitions
- `execute_shell_command` - Run shell commands
- `search_for_pattern` - Search patterns in code
- `onboarding` - Analyze project structure
- `activate_project` - Switch between projects

## 🎯 Usage Examples

### 1. Project Analysis
```
"Use Serena to analyze the filesystem-mcp-server project structure"
```

### 2. Code Search
```
"Find all TypeScript interfaces in the filesystem-mcp-server project"
```

### 3. Project Switching
```
"Activate the serena-project and show me the main agent code"
```

### 4. Code Editing
```
"Add a new method to handle file uploads in the filesystem server"
```

## 🔍 Troubleshooting

### Common Issues:
1. **Python Path Conflicts**: Use the start script to isolate environment
2. **Tool Name Collisions**: Serena conflicts with filesystem MCP server - use only one at a time
3. **Permission Issues**: Ensure execute permissions on start script

### Debug Commands:
```bash
# Test Serena installation
cd /home/lylepaul78/Documents/augment-projects/MayArbi/serena
uv run python -c "import serena; print('Serena imported successfully')"

# List available tools
uv run serena-list-tools

# Test MCP server
uv run serena-mcp-server --help
```

## 📚 Next Steps

1. **Test the Setup**: Try connecting Augment to Serena
2. **Explore Tools**: Use Serena's semantic code analysis
3. **Project Onboarding**: Let Serena analyze your projects
4. **Memory System**: Serena will create memories in `.serena/memories/`
5. **Integration**: Combine with your existing filesystem-mcp-server

## 🎉 Benefits of Using Serena

- **Semantic Code Understanding**: Uses language servers for deep code analysis
- **Multi-Language Support**: Python, TypeScript, Go, Rust, Java, C++, PHP
- **Project Memory**: Learns about your codebase over time
- **Free & Open Source**: No API costs or subscriptions
- **IDE-Quality Tools**: Symbol-level code navigation and editing
