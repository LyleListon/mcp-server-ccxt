#!/usr/bin/env python3
"""
Comprehensive test script for MayArbi current setup
Tests all MCP servers, configurations, and components
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import time

class SetupTester:
    def __init__(self):
        self.results = {}
        self.errors = []
        
    def print_header(self, title: str):
        """Print a formatted header"""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
        
    def print_status(self, component: str, status: str, details: str = ""):
        """Print component status"""
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {component}: {status}")
        if details:
            print(f"   └─ {details}")
            
    def check_file_exists(self, filepath: str) -> Tuple[bool, str]:
        """Check if a file exists"""
        path = Path(filepath)
        if path.exists():
            return True, f"Found at {path.absolute()}"
        else:
            return False, f"Not found: {filepath}"
            
    def check_directory_structure(self):
        """Test directory structure"""
        self.print_header("Directory Structure")
        
        required_dirs = [
            "src", "docs", "config", "data", "tests", "tools", "scripts",
            "dexmind", "FileScopeMCP", "filesystem-mcp-server", 
            "mcp-memory-service", "mcp-server-ccxt", "serena"
        ]
        
        for dir_name in required_dirs:
            exists, details = self.check_file_exists(dir_name)
            status = "PASS" if exists else "FAIL"
            self.print_status(f"Directory: {dir_name}", status, details)
            self.results[f"dir_{dir_name}"] = exists
            
    def check_config_files(self):
        """Test configuration files"""
        self.print_header("Configuration Files")
        
        config_files = [
            "config/dex_config.json",
            "src/config/configs/default/config.json",
            "src/config/configs/development/config.json",
            "src/config/configs/test/config.json",
            "mcp-memory-service/mcp_config.json",
            "filesystem-mcp-server/mcp.json",
            "FileScopeMCP/mcp.json"
        ]
        
        for config_file in config_files:
            exists, details = self.check_file_exists(config_file)
            if exists:
                try:
                    with open(config_file, 'r') as f:
                        json.load(f)
                    status = "PASS"
                    details += " (Valid JSON)"
                except json.JSONDecodeError as e:
                    status = "FAIL"
                    details += f" (Invalid JSON: {e})"
            else:
                status = "FAIL"
                
            self.print_status(f"Config: {config_file}", status, details)
            self.results[f"config_{config_file}"] = exists
            
    def check_python_environments(self):
        """Test Python virtual environments"""
        self.print_header("Python Virtual Environments")
        
        python_projects = [
            "mcp-memory-service",
            "mcp-server-ccxt", 
            "serena"
        ]
        
        for project in python_projects:
            venv_path = f"{project}/.venv"
            exists, details = self.check_file_exists(venv_path)
            
            if exists:
                # Check if we can activate and run python
                try:
                    result = subprocess.run([
                        f"{venv_path}/bin/python", "--version"
                    ], capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0:
                        status = "PASS"
                        details += f" (Python {result.stdout.strip()})"
                    else:
                        status = "FAIL"
                        details += f" (Cannot run python: {result.stderr})"
                except Exception as e:
                    status = "FAIL"
                    details += f" (Error: {e})"
            else:
                status = "FAIL"
                
            self.print_status(f"Python venv: {project}", status, details)
            self.results[f"python_{project}"] = exists
            
    def check_node_environments(self):
        """Test Node.js environments"""
        self.print_header("Node.js Environments")
        
        node_projects = [
            "FileScopeMCP",
            "dexmind",
            "filesystem-mcp-server"
        ]
        
        for project in node_projects:
            package_json = f"{project}/package.json"
            exists, details = self.check_file_exists(package_json)
            
            if exists:
                # Check if node_modules exists (we removed them, so this should fail)
                node_modules = f"{project}/node_modules"
                nm_exists, _ = self.check_file_exists(node_modules)
                
                if nm_exists:
                    status = "PASS"
                    details += " (Dependencies installed)"
                else:
                    status = "WARN"
                    details += " (Dependencies need installation)"
            else:
                status = "FAIL"
                
            self.print_status(f"Node project: {project}", status, details)
            self.results[f"node_{project}"] = exists
            
    def check_src_structure(self):
        """Test src directory structure"""
        self.print_header("Source Code Structure")
        
        src_components = [
            "src/dex",
            "src/core", 
            "src/utils",
            "src/wallet",
            "src/integrations",
            "src/analytics",
            "src/monitoring",
            "src/common",
            "src/config"
        ]
        
        for component in src_components:
            exists, details = self.check_file_exists(component)
            
            if exists:
                # Check for index file
                index_file = f"{component} index.txt"
                index_exists, _ = self.check_file_exists(index_file)
                if index_exists:
                    details += " (Documented)"
                else:
                    details += " (Missing index file)"
                    
            status = "PASS" if exists else "FAIL"
            self.print_status(f"Source: {component}", status, details)
            self.results[f"src_{component}"] = exists
            
    def test_mcp_server_configs(self):
        """Test MCP server configurations"""
        self.print_header("MCP Server Configurations")
        
        mcp_configs = {
            "dexmind": "dexmind/package.json",
            "filesystem-mcp": "filesystem-mcp-server/mcp.json", 
            "filescopemcp": "FileScopeMCP/mcp.json",
            "memory-service": "mcp-memory-service/mcp_config.json",
            "ccxt-server": "mcp-server-ccxt/pyproject.toml"
        }
        
        for server_name, config_path in mcp_configs.items():
            exists, details = self.check_file_exists(config_path)
            status = "PASS" if exists else "FAIL"
            self.print_status(f"MCP Config: {server_name}", status, details)
            self.results[f"mcp_config_{server_name}"] = exists
            
    def test_data_directories(self):
        """Test data directory structure"""
        self.print_header("Data Directory Structure")
        
        data_dirs = [
            "data/arbitrage/executions",
            "data/arbitrage/opportunities", 
            "data/arbitrage/patterns",
            "data/arbitrage/stats"
        ]
        
        for data_dir in data_dirs:
            exists, details = self.check_file_exists(data_dir)
            status = "PASS" if exists else "FAIL"
            self.print_status(f"Data dir: {data_dir}", status, details)
            self.results[f"data_{data_dir}"] = exists
            
    def test_documentation(self):
        """Test documentation completeness"""
        self.print_header("Documentation")
        
        doc_files = [
            "README.md",
            "MIGRATION_IMPLEMENTATION_ROADMAP.md",
            "docs/README.md"
        ]
        
        # Check for index files
        index_files = []
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(" index.txt"):
                    index_files.append(os.path.join(root, file))
                    
        self.print_status("Index files found", "PASS", f"{len(index_files)} index files")
        
        for doc_file in doc_files:
            exists, details = self.check_file_exists(doc_file)
            status = "PASS" if exists else "FAIL"
            self.print_status(f"Doc: {doc_file}", status, details)
            self.results[f"doc_{doc_file}"] = exists
            
    def run_quick_dependency_check(self):
        """Quick check of key dependencies"""
        self.print_header("Quick Dependency Check")
        
        # Check Python
        try:
            result = subprocess.run([sys.executable, "--version"], 
                                  capture_output=True, text=True)
            self.print_status("Python", "PASS", result.stdout.strip())
        except Exception as e:
            self.print_status("Python", "FAIL", str(e))
            
        # Check Node.js
        try:
            result = subprocess.run(["node", "--version"], 
                                  capture_output=True, text=True)
            self.print_status("Node.js", "PASS", result.stdout.strip())
        except Exception as e:
            self.print_status("Node.js", "FAIL", str(e))
            
        # Check npm
        try:
            result = subprocess.run(["npm", "--version"], 
                                  capture_output=True, text=True)
            self.print_status("npm", "PASS", result.stdout.strip())
        except Exception as e:
            self.print_status("npm", "FAIL", str(e))
            
    def generate_summary(self):
        """Generate test summary"""
        self.print_header("Test Summary")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for test_name, result in self.results.items():
                if not result:
                    print(f"   - {test_name}")
                    
        return failed_tests == 0
        
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting MayArbi Setup Testing...")
        print(f"📁 Working directory: {os.getcwd()}")
        
        self.check_directory_structure()
        self.check_config_files()
        self.check_python_environments()
        self.check_node_environments()
        self.check_src_structure()
        self.test_mcp_server_configs()
        self.test_data_directories()
        self.test_documentation()
        self.run_quick_dependency_check()
        
        success = self.generate_summary()
        
        if success:
            print("\n🎉 All tests passed! Setup looks good.")
        else:
            print("\n⚠️  Some tests failed. Check the details above.")
            
        return success

if __name__ == "__main__":
    tester = SetupTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
