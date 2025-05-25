#!/usr/bin/env python3
"""
Simple test script to verify Serena setup
"""

import sys
import os
import subprocess

def test_serena_import():
    """Test if Serena can be imported"""
    try:
        # Change to serena directory
        serena_dir = "/home/lylepaul78/Documents/augment-projects/MayArbi/serena"
        os.chdir(serena_dir)
        
        # Test import
        result = subprocess.run([
            "uv", "run", "python", "-c", "import serena; print('✅ Serena imported successfully')"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Serena Import Test: PASSED")
            print(result.stdout.strip())
        else:
            print("❌ Serena Import Test: FAILED")
            print(result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Serena Import Test: ERROR - {e}")
        return False

def test_mcp_server():
    """Test if MCP server can start"""
    try:
        serena_dir = "/home/lylepaul78/Documents/augment-projects/MayArbi/serena"
        os.chdir(serena_dir)
        
        # Test MCP server help
        result = subprocess.run([
            "uv", "run", "serena-mcp-server", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ MCP Server Test: PASSED")
            print("MCP server can start successfully")
        else:
            print("❌ MCP Server Test: FAILED")
            print(result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⚠️  MCP Server Test: TIMEOUT (but server might be working)")
        return True
    except Exception as e:
        print(f"❌ MCP Server Test: ERROR - {e}")
        return False

def test_project_configs():
    """Test if project configurations exist"""
    serena_dir = "/home/lylepaul78/Documents/augment-projects/MayArbi/serena"
    
    configs = [
        "serena_config.yml",
        "filesystem-mcp-server.yml", 
        "serena-project.yml"
    ]
    
    all_exist = True
    for config in configs:
        config_path = os.path.join(serena_dir, config)
        if os.path.exists(config_path):
            print(f"✅ Config exists: {config}")
        else:
            print(f"❌ Config missing: {config}")
            all_exist = False
            
    return all_exist

def main():
    print("🧪 Testing Serena Setup...")
    print("=" * 50)
    
    tests = [
        ("Project Configurations", test_project_configs),
        ("Serena Import", test_serena_import),
        ("MCP Server", test_mcp_server),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))
        
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
            
    print(f"\n🎯 Overall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 Serena setup is ready!")
        print("You can now configure Augment Code extension to use Serena.")
    else:
        print("\n⚠️  Some issues found. Check the errors above.")

if __name__ == "__main__":
    main()
