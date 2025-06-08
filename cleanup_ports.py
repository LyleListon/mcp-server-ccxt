#!/usr/bin/env python3
"""
🧹 SMART PORT CLEANUP
Clean up unnecessary ports while preserving essential services
"""

import subprocess
import psutil
import time

# Essential services to NEVER kill
ESSENTIAL_SERVICES = {
    'sillytavern': ['8000'],
    'stable_diffusion': ['7860'], 
    'lm_studio': ['1234'],
    'mev_empire': ['ethereum_node_master', 'spy_enhanced_arbitrage', 'ethereum_dex_scanner']
}

# Services that can be safely killed
SAFE_TO_KILL = {
    'neo4j': [7687, 7474, 7473],  # Graph database (not needed for MEV)
    'ollama': [11434],  # Conflicts with LM Studio
    'postgresql': [5432],  # Database (check if needed)
    'vscode_extras': [33403, 33755],  # Extra VSCode processes
    'unknown_services': [49000, 49443, 49155, 49156, 49259, 8811]
}

def get_port_process(port):
    """Get process using a specific port"""
    try:
        result = subprocess.run(['lsof', '-i', f':{port}'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                return {
                    'command': parts[0],
                    'pid': int(parts[1]),
                    'user': parts[2]
                }
    except:
        pass
    return None

def is_essential_process(pid, command):
    """Check if process is essential"""
    try:
        proc = psutil.Process(pid)
        cmdline = ' '.join(proc.cmdline()).lower()
        
        # Check for MEV empire processes
        mev_keywords = ['ethereum_node_master', 'spy_enhanced_arbitrage', 'ethereum_dex_scanner']
        if any(keyword in cmdline for keyword in mev_keywords):
            return True
            
        # Check for AI services
        ai_keywords = ['sillytavern', 'stable', 'diffusion', 'lmstudio', 'lm-studio']
        if any(keyword in cmdline for keyword in ai_keywords):
            return True
            
        return False
    except:
        return True  # If we can't check, assume it's essential

def cleanup_ports():
    """Clean up unnecessary ports"""
    
    print("🧹" * 30)
    print("🧹 SMART PORT CLEANUP")
    print("🧹" * 30)
    
    print("🔍 Scanning for unnecessary services...")
    
    killed_count = 0
    preserved_count = 0
    
    # Check each category of services to kill
    for category, ports in SAFE_TO_KILL.items():
        print(f"\n📊 Checking {category}...")
        
        for port in ports:
            proc_info = get_port_process(port)
            if proc_info:
                pid = proc_info['pid']
                command = proc_info['command']
                
                if is_essential_process(pid, command):
                    print(f"  ✅ Port {port}: {command} (PID {pid}) - PRESERVED (essential)")
                    preserved_count += 1
                else:
                    try:
                        print(f"  🔧 Port {port}: {command} (PID {pid}) - KILLING...")
                        psutil.Process(pid).terminate()
                        time.sleep(1)
                        
                        # Force kill if still running
                        if psutil.pid_exists(pid):
                            psutil.Process(pid).kill()
                            
                        print(f"  ✅ Killed {command} (PID {pid})")
                        killed_count += 1
                        
                    except Exception as e:
                        print(f"  ❌ Failed to kill {command}: {e}")
            else:
                print(f"  ⚪ Port {port}: Not in use")
    
    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"  🔧 Processes killed: {killed_count}")
    print(f"  ✅ Essential services preserved: {preserved_count}")
    
    # Show remaining port count
    try:
        result = subprocess.run(['ss', '-tln'], capture_output=True, text=True)
        listening_ports = len([line for line in result.stdout.split('\n') if 'LISTEN' in line])
        print(f"  📊 Remaining listening ports: {listening_ports}")
    except:
        print("  📊 Could not count remaining ports")

def show_essential_services():
    """Show status of essential services"""
    
    print("\n✅ ESSENTIAL SERVICES STATUS:")
    
    # Check MEV Empire
    print("💰 MEV Empire:")
    mev_processes = ['ethereum_node_master.py', 'spy_enhanced_arbitrage.py', 'ethereum_dex_scanner.py']
    for proc_name in mev_processes:
        running = False
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline'] and any(proc_name in cmd for cmd in proc.info['cmdline']):
                    print(f"  ✅ {proc_name} - RUNNING (PID {proc.info['pid']})")
                    running = True
                    break
        except:
            pass
        if not running:
            print(f"  🔴 {proc_name} - NOT RUNNING")
    
    # Check AI services ports
    print("\n🤖 AI Services:")
    ai_ports = [8000, 7860, 1234]
    ai_names = ['SillyTavern', 'Stable Diffusion', 'LM Studio']
    
    for port, name in zip(ai_ports, ai_names):
        proc_info = get_port_process(port)
        if proc_info:
            print(f"  ✅ {name} (:{port}) - RUNNING")
        else:
            print(f"  ❓ {name} (:{port}) - NOT DETECTED")

if __name__ == "__main__":
    try:
        cleanup_ports()
        show_essential_services()
        
        print("\n🎉 PORT CLEANUP COMPLETE!")
        print("🔍 Your essential AI services and MEV empire should still be running")
        
    except KeyboardInterrupt:
        print("\n🛑 Cleanup cancelled by user")
    except Exception as e:
        print(f"\n💥 Error during cleanup: {e}")
