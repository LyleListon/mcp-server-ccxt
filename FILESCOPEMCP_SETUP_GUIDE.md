# FileScopeMCP Setup Guide for Augment Code Extension

## ✅ Installation Status
FileScopeMCP has been successfully installed and configured in your project!

## 🔧 Configuration Details

### Server Location
- **Path**: `/home/lylepaul78/Documents/augment-projects/MayArbi/FileScopeMCP/`
- **Executable**: `run.sh`
- **Base Directory**: `/home/lylepaul78/Documents/augment-projects/MayArbi/` (your main project)

### Key Features Enabled
- ✅ File importance analysis (0-10 scale)
- ✅ Dependency tracking (bidirectional)
- ✅ File summaries
- ✅ Mermaid diagram generation
- ✅ File watching (auto-updates)
- ✅ Multi-language support (Python, JS, TS, C/C++, Rust, Lua, Zig)

## 🚀 Integration with Augment Code Extension

### Method 1: Augment Settings Panel (Recommended)
1. Open VSCode with your project
2. Look for the Augment panel in VSCode
3. Click the **gear icon** in the upper right of the Augment panel
4. In the MCP servers section, click the **`+` button**
5. Fill in:
   - **Name**: `FileScopeMCP`
   - **Command**: `/home/lylepaul78/Documents/augment-projects/MayArbi/FileScopeMCP/run.sh`
6. **Restart VSCode**

### Method 2: Manual settings.json Configuration
1. Press `Ctrl+Shift+P` in VSCode
2. Type "Edit Settings" and select Augment option
3. Under Advanced, click "Edit in settings.json"
4. Add this configuration:

```json
{
  "augment.advanced": {
    "mcpServers": [
      {
        "name": "FileScopeMCP",
        "command": "/home/lylepaul78/Documents/augment-projects/MayArbi/FileScopeMCP/run.sh"
      }
    ]
  }
}
```

## 🧪 Testing the Setup

### Verify Installation
Run the test script:
```bash
cd /home/lylepaul78/Documents/augment-projects/MayArbi
./test-filescopemcp.sh
```

### Test with Augment
After configuring in Augment, try these commands:
- "Show me the most important files in this project"
- "What are the dependencies of [filename]?"
- "Generate a project structure diagram"
- "Analyze the file importance in this codebase"

## 🛠 Available Tools

FileScopeMCP provides these tools to Augment:

### File Analysis
- `list_files` - List all files with importance rankings
- `get_file_importance` - Get detailed file information
- `find_important_files` - Find most critical files
- `read_file_content` - Read file contents

### File Management
- `create_file_tree` - Create new file tree for directory
- `select_file_tree` - Switch between file trees
- `list_saved_trees` - Show all saved trees

### Summaries
- `get_file_summary` - Get stored file summary
- `set_file_summary` - Add/update file summary

### Visualization
- `generate_diagram` - Create Mermaid diagrams (HTML or text)

### File Watching
- `toggle_file_watching` - Enable/disable auto-updates
- `get_file_watching_status` - Check watching status

## 📁 Project Structure Analysis

FileScopeMCP will analyze your project and:
- Rank files by importance (0-10 scale)
- Track which files import/depend on others
- Identify the most critical files in your codebase
- Generate visual dependency diagrams
- Exclude unnecessary files (node_modules, .venv, etc.)

## 🔍 Exclude Patterns

The following patterns are automatically excluded:
- `**/node_modules/**`, `**/.git/**`, `**/dist/**`
- `**/venv/**`, `**/.venv/**`, `**/env/**`
- `**/*.log`, `**/*.lock`, `**/*.pyc`
- And many more...

## 🐛 Troubleshooting

### If FileScopeMCP doesn't appear in Augment:
1. Check that you restarted VSCode after configuration
2. Verify the command path is correct
3. Test the server manually: `./FileScopeMCP/run.sh`
4. Check Augment's output panel for error messages

### If server fails to start:
1. Ensure WSL is running: `wsl --list --running`
2. Check Node.js is available: `which node`
3. Verify file permissions: `ls -la FileScopeMCP/run.sh`

## 📞 Support

If you encounter issues:
1. Run the test script to verify setup
2. Check the FileScopeMCP logs in `FileScopeMCP/logs/`
3. Refer to the original repository: https://github.com/admica/FileScopeMCP

---

**Status**: ✅ Ready to use with Augment Code Extension!
