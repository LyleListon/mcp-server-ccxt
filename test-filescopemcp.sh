#!/bin/bash

echo "Testing FileScopeMCP setup..."
echo "================================"

# Test 1: Check if the run.sh script exists and is executable
echo "1. Checking run.sh script..."
if [ -x "FileScopeMCP/run.sh" ]; then
    echo "   ✅ run.sh is executable"
else
    echo "   ❌ run.sh is not executable or doesn't exist"
    exit 1
fi

# Test 2: Check if Node.js path is correct
echo "2. Checking Node.js installation..."
if [ -f "/home/lylepaul78/.nvm/versions/node/v22.14.0/bin/node" ]; then
    echo "   ✅ Node.js found at expected path"
    /home/lylepaul78/.nvm/versions/node/v22.14.0/bin/node --version
else
    echo "   ❌ Node.js not found at expected path"
    echo "   Current Node.js location: $(which node)"
fi

# Test 3: Check if the compiled server exists
echo "3. Checking compiled MCP server..."
if [ -f "FileScopeMCP/dist/mcp-server.js" ]; then
    echo "   ✅ Compiled MCP server found"
else
    echo "   ❌ Compiled MCP server not found"
    exit 1
fi

# Test 4: Check if config.json exists
echo "4. Checking configuration..."
if [ -f "FileScopeMCP/config.json" ]; then
    echo "   ✅ Configuration file found"
    echo "   Exclude patterns: $(grep -c '"' FileScopeMCP/config.json) patterns configured"
else
    echo "   ❌ Configuration file not found"
fi

# Test 5: Quick server startup test (5 second timeout)
echo "5. Testing server startup..."
timeout 5s ./FileScopeMCP/run.sh > /dev/null 2>&1
if [ $? -eq 124 ]; then
    echo "   ✅ Server starts successfully (timed out as expected)"
else
    echo "   ❌ Server failed to start or exited unexpectedly"
fi

echo ""
echo "Setup test complete!"
echo ""
echo "Next steps:"
echo "1. Open VSCode with Augment extension"
echo "2. Go to Augment Settings Panel (gear icon)"
echo "3. Add MCP server with:"
echo "   Name: FileScopeMCP"
echo "   Command: /home/lylepaul78/Documents/augment-projects/MayArbi/FileScopeMCP/run.sh"
echo "4. Restart VSCode"
echo "5. Test by asking Augment to analyze your project files"
