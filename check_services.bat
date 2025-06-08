@echo off
echo 🔍 CHECKING CRITICAL WINDOWS SERVICES FOR WSL2
echo ============================================================
echo.

echo 🚨 ABSOLUTELY CRITICAL - WSL2 won't work without these:
sc query LxssManager | findstr "STATE"
if errorlevel 1 echo    ❌ LxssManager - WSL Manager NOT FOUND
sc query vmcompute | findstr "STATE"
if errorlevel 1 echo    ❌ vmcompute - Hyper-V Host Compute Service NOT FOUND
sc query vmms | findstr "STATE"
if errorlevel 1 echo    ❌ vmms - Hyper-V Virtual Machine Management NOT FOUND

echo.
echo 🌐 NETWORKING ESSENTIALS - These control internet access:
sc query Dhcp | findstr "STATE"
if errorlevel 1 echo    ❌ Dhcp - DHCP Client NOT FOUND
sc query Dnscache | findstr "STATE"
if errorlevel 1 echo    ❌ Dnscache - DNS Client NOT FOUND
sc query RpcSs | findstr "STATE"
if errorlevel 1 echo    ❌ RpcSs - Remote Procedure Call NOT FOUND
sc query Netman | findstr "STATE"
if errorlevel 1 echo    ❌ Netman - Network Connections NOT FOUND
sc query NlaSvc | findstr "STATE"
if errorlevel 1 echo    ❌ NlaSvc - Network Location Awareness NOT FOUND
sc query netprofm | findstr "STATE"
if errorlevel 1 echo    ❌ netprofm - Network List Service NOT FOUND
sc query iphlpsvc | findstr "STATE"
if errorlevel 1 echo    ❌ iphlpsvc - IP Helper NOT FOUND

echo.
echo 🔒 SECURITY ^& CERTIFICATES - SSL/HTTPS won't work without these:
sc query CryptSvc | findstr "STATE"
if errorlevel 1 echo    ❌ CryptSvc - Cryptographic Services NOT FOUND
sc query PolicyAgent | findstr "STATE"
if errorlevel 1 echo    ❌ PolicyAgent - IPsec Policy Agent NOT FOUND
sc query mpssvc | findstr "STATE"
if errorlevel 1 echo    ❌ mpssvc - Windows Defender Firewall NOT FOUND
sc query BFE | findstr "STATE"
if errorlevel 1 echo    ❌ BFE - Base Filtering Engine NOT FOUND

echo.
echo ⚙️ SYSTEM ESSENTIALS - Windows breaks without these:
sc query Winmgmt | findstr "STATE"
if errorlevel 1 echo    ❌ Winmgmt - Windows Management Instrumentation NOT FOUND
sc query RpcEptMapper | findstr "STATE"
if errorlevel 1 echo    ❌ RpcEptMapper - RPC Endpoint Mapper NOT FOUND
sc query SENS | findstr "STATE"
if errorlevel 1 echo    ❌ SENS - System Event Notification Service NOT FOUND
sc query EventSystem | findstr "STATE"
if errorlevel 1 echo    ❌ EventSystem - COM+ Event System NOT FOUND

echo.
echo 🔧 COMMONLY DISABLED - These are often turned off by mistake:
sc query Themes | findstr "STATE"
if errorlevel 1 echo    ❌ Themes - Themes NOT FOUND
sc query Spooler | findstr "STATE"
if errorlevel 1 echo    ❌ Spooler - Print Spooler NOT FOUND
sc query SysMain | findstr "STATE"
if errorlevel 1 echo    ❌ SysMain - SysMain (Superfetch) NOT FOUND
sc query ProfSvc | findstr "STATE"
if errorlevel 1 echo    ❌ ProfSvc - User Profile Service NOT FOUND

echo.
echo ============================================================
echo 🎯 DIAGNOSTIC COMPLETE
echo.
echo If you see any "STOPPED" or "NOT FOUND" services above,
echo those might be causing your WSL2 networking issues!
echo.
echo To fix:
echo 1. Open services.msc as Administrator
echo 2. Find the stopped/disabled services
echo 3. Set them to "Automatic" and start them
echo 4. Run: wsl --shutdown
echo 5. Restart WSL2
echo.
pause
