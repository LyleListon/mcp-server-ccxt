#!/usr/bin/env python3
"""
Check critical Windows services for WSL2 networking
"""

import subprocess
import json

def check_service_status(service_name):
    """Check if a Windows service is running."""
    try:
        # Use PowerShell to check service status
        cmd = f'powershell.exe "Get-Service -Name {service_name} | ConvertTo-Json"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            service_info = json.loads(result.stdout)
            return {
                'name': service_info.get('Name', service_name),
                'status': service_info.get('Status', 'Unknown'),
                'start_type': service_info.get('StartType', 'Unknown')
            }
        else:
            return {'name': service_name, 'status': 'Not Found', 'start_type': 'Unknown'}
    except Exception as e:
        return {'name': service_name, 'status': 'Error', 'start_type': str(e)}

def main():
    """Check critical Windows services for WSL2."""
    
    print("🔍 CHECKING CRITICAL WINDOWS SERVICES FOR WSL2")
    print("=" * 60)
    
    # CRITICAL services for WSL2 networking (the ones you probably disabled!)
    critical_services = [
        # 🔥 ABSOLUTELY CRITICAL - WSL2 won't work without these
        ('LxssManager', '🚨 WSL Manager - CORE WSL2 functionality'),
        ('vmcompute', '🚨 Hyper-V Host Compute Service - WSL2 VM management'),
        ('vmms', '🚨 Hyper-V Virtual Machine Management - VM networking'),

        # 🌐 NETWORKING ESSENTIALS - These control internet access
        ('Dhcp', '🌐 DHCP Client - Network IP assignment'),
        ('Dnscache', '🌐 DNS Client - Domain name resolution'),
        ('RpcSs', '🌐 Remote Procedure Call - Core Windows networking'),
        ('Netman', '🌐 Network Connections - Network interface management'),
        ('NlaSvc', '🌐 Network Location Awareness - Network connectivity detection'),
        ('netprofm', '🌐 Network List Service - Network profile management'),
        ('iphlpsvc', '🌐 IP Helper - IPv6 connectivity and tunnel technology'),

        # 🔒 SECURITY & CERTIFICATES - SSL/HTTPS won't work without these
        ('CryptSvc', '🔒 Cryptographic Services - SSL/TLS certificates'),
        ('PolicyAgent', '🔒 IPsec Policy Agent - Network security'),
        ('mpssvc', '🔒 Windows Defender Firewall - Network filtering'),
        ('BFE', '🔒 Base Filtering Engine - Network packet filtering'),

        # ⚙️ SYSTEM ESSENTIALS - Windows breaks without these
        ('Winmgmt', '⚙️ Windows Management Instrumentation - System management'),
        ('RpcEptMapper', '⚙️ RPC Endpoint Mapper - Network service discovery'),
        ('SENS', '⚙️ System Event Notification Service - Network event detection'),
        ('EventSystem', '⚙️ COM+ Event System - System event handling'),
        ('Appinfo', '⚙️ Application Information - UAC and service elevation'),
        ('Schedule', '⚙️ Task Scheduler - Background network tasks'),

        # 🌍 HTTP/PROXY - Web access and downloads
        ('WinHttpAutoProxySvc', '🌍 WinHTTP Web Proxy Auto-Discovery - HTTP proxy detection'),
        ('BITS', '🌍 Background Intelligent Transfer Service - HTTP downloads'),
        ('WebClient', '🌍 WebClient - WebDAV file access'),

        # 🔧 COMMONLY DISABLED - These are often turned off by mistake
        ('Themes', '🔧 Themes - Sometimes affects networking (weird but true)'),
        ('Spooler', '🔧 Print Spooler - Sometimes affects networking'),
        ('WSearch', '🔧 Windows Search - Sometimes affects networking'),
        ('SysMain', '🔧 SysMain (Superfetch) - Memory management'),
        ('ProfSvc', '🔧 User Profile Service - User profile management'),
        ('UxSms', '🔧 Desktop Window Manager Session Manager - Desktop management'),
        ('Power', '🔧 Power - Power management'),
        ('PlugPlay', '🔧 Plug and Play - Device management'),
    ]
    
    print("🔍 Checking services...")
    
    stopped_critical = []
    disabled_critical = []
    running_services = []
    
    for service_name, description in critical_services:
        status = check_service_status(service_name)
        
        if status['status'] == 'Running':
            running_services.append((service_name, description))
        elif status['status'] == 'Stopped':
            stopped_critical.append((service_name, description, status['start_type']))
        elif status['start_type'] == 'Disabled':
            disabled_critical.append((service_name, description))
    
    print(f"\n✅ RUNNING SERVICES: {len(running_services)}")
    for service, desc in running_services[:10]:  # Show first 10
        print(f"   ✅ {service} - {desc}")
    if len(running_services) > 10:
        print(f"   ... and {len(running_services) - 10} more")
    
    print(f"\n⚠️  STOPPED SERVICES: {len(stopped_critical)}")
    for service, desc, start_type in stopped_critical:
        print(f"   ⚠️  {service} ({start_type}) - {desc}")
    
    print(f"\n❌ DISABLED SERVICES: {len(disabled_critical)}")
    for service, desc in disabled_critical:
        print(f"   ❌ {service} - {desc}")
    
    if stopped_critical or disabled_critical:
        print(f"\n🔧 POTENTIAL FIXES:")
        print(f"   1. Start stopped services: services.msc")
        print(f"   2. Enable disabled services: Set to 'Automatic' or 'Manual'")
        print(f"   3. Restart WSL2: wsl --shutdown")
        print(f"   4. Restart Windows (if major services are affected)")
    else:
        print(f"\n✅ All critical services appear to be running!")

if __name__ == "__main__":
    main()
