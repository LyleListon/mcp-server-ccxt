#!/usr/bin/env python3
"""
📦 MEV EMPIRE DASHBOARD DEPENDENCIES INSTALLER
Install required packages for the dashboard
"""

import subprocess
import sys

def install_package(package):
    """Install a Python package"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")
        return False

def main():
    print("📦 Installing MEV Empire Dashboard dependencies...")
    
    packages = [
        "flask",
        "flask-socketio",
        "psutil",
        "requests"
    ]
    
    success_count = 0
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n📊 Installation complete: {success_count}/{len(packages)} packages installed")
    
    if success_count == len(packages):
        print("🎉 All dependencies installed successfully!")
        print("🚀 You can now run: python mev_empire_dashboard.py")
    else:
        print("⚠️ Some packages failed to install. Please install manually:")
        print("pip install flask flask-socketio psutil requests")

if __name__ == "__main__":
    main()
