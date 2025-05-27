#!/usr/bin/env python3
"""
Nuclear Bot Killer
When the bot just won't quit... FORCE IT! 💥
"""

import os
import signal
import subprocess
import sys

def kill_arbitrage_bot():
    """Kill all arbitrage bot processes with extreme prejudice."""
    
    print("💥 NUCLEAR BOT SHUTDOWN INITIATED!")
    print("=" * 50)
    print("🎯 Hunting down stubborn arbitrage processes...")
    
    # Find all Python processes running our bot
    try:
        # Get all Python processes
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        killed_count = 0
        
        for line in lines:
            if 'deploy_arbitrage_bot.py' in line or 'master_arbitrage_system' in line:
                # Extract PID (second column)
                parts = line.split()
                if len(parts) > 1:
                    try:
                        pid = int(parts[1])
                        print(f"🎯 Found bot process: PID {pid}")
                        print(f"   Command: {' '.join(parts[10:])}")
                        
                        # Kill it with fire! 🔥
                        os.kill(pid, signal.SIGKILL)
                        print(f"   💀 KILLED PID {pid}")
                        killed_count += 1
                        
                    except (ValueError, ProcessLookupError, PermissionError) as e:
                        print(f"   ⚠️  Could not kill PID {parts[1]}: {e}")
        
        if killed_count > 0:
            print(f"\n🎉 Successfully killed {killed_count} bot process(es)!")
        else:
            print(f"\n✅ No bot processes found running")
            
    except Exception as e:
        print(f"❌ Error during process hunting: {e}")
    
    # Also kill any hanging Python processes
    try:
        print(f"\n🧹 Cleaning up any hanging Python processes...")
        subprocess.run(['pkill', '-f', 'arbitrage'], capture_output=True)
        print(f"✅ Cleanup complete")
    except:
        pass
    
    print(f"\n💥 NUCLEAR SHUTDOWN COMPLETE!")
    print(f"   All arbitrage bot processes have been terminated")
    print(f"   You can now safely restart the bot")

if __name__ == "__main__":
    kill_arbitrage_bot()
