Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile "$env:TEMP\python-3.11.9-amd64.exe"
Start-Process -FilePath "$env:TEMP\python-3.11.9-amd64.exe" -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1" -Wait
Remove-Item $installerPath -Force
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","User") + ";" + $env:Path
python --version