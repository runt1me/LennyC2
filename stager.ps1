$pythonVersion = "3.11.9"
$installerUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion-amd64.exe"
$installerPath = "$env:TEMP\python-$pythonVersion-amd64.exe"

Write-Host "Downloading Python $pythonVersion..."
Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath

Write-Host "Installing Python $pythonVersion for current user..."
# /quiet -> silent install
# InstallAllUsers=0 -> user-only install
# PrependPath=1 -> add Python to *user* PATH
Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1" -Wait

Write-Host "Cleaning up installer..."
Remove-Item $installerPath -Force

Write-Host "Refreshing PATH..."
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","User") + ";" + $env:Path

Write-Host "Verifying installation..."
python --version