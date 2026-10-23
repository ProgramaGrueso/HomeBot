# Quita HomeBot: el arranque con Windows y el perfil del bot (no desinstala Hermes ni Python).
$lnk = Join-Path ([Environment]::GetFolderPath("Startup")) "HomeBot.lnk"
if (Test-Path $lnk) { Remove-Item $lnk }
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" | Where-Object { $_.CommandLine -match "homebot.py" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
& hermes profile delete homebot
Write-Host "HomeBot quitado. Borra esta carpeta si quieres eliminar todo."
