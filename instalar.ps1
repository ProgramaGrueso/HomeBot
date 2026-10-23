# HomeBot - instalador para Windows 10/11. Ejecutar:  clic derecho > "Ejecutar con PowerShell"  (o  powershell -ExecutionPolicy Bypass -File instalar.ps1)
# Revisa qué le falta a la PC (Python, Hermes, paquetes), lo descarga, crea el bot, pide TU API key de DeepSeek y deja Windows + Y listo.
$ErrorActionPreference = "Stop"
$Aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Aqui
function Paso($t) { Write-Host "`n== $t" -ForegroundColor Cyan }
function Existe($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function RecargarPath { $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User") }

Paso "1/6 Python 3.10+"
$py = $null
foreach ($c in @("py -3", "python")) {
    try { $v = & cmd /c "$c --version 2>&1"; if ($v -match "Python 3\.(1[0-9]|[2-9][0-9])") { $py = $c; break } } catch {}
}
if (-not $py) {
    if (-not (Existe winget)) { throw "Falta Python y no hay winget. Instala Python 3.12 desde python.org (marca 'Add to PATH') y vuelve a ejecutar." }
    Write-Host "Instalando Python 3.12..."
    winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
    RecargarPath; $py = "py -3"
}
Write-Host "Python OK ($py)"

Paso "2/6 Hermes Agent"
if (-not (Existe hermes)) {
    Write-Host "Instalando Hermes (puede tardar unos minutos)..."
    iex (irm https://hermes-agent.nousresearch.com/install.ps1)
    RecargarPath
}
if (-not (Existe hermes)) { throw "Hermes se instaló pero no aparece en esta ventana. Cierra y abre PowerShell y ejecuta instalar.ps1 otra vez." }
Write-Host "Hermes OK"

Paso "3/6 Paquetes de HomeBot (requirements.txt)"
if (-not (Test-Path ".venv")) { & cmd /c "$py -m venv .venv" }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
Write-Host "Paquetes OK"

Paso "4/6 Tu bot"
$nombre = Read-Host "¿Cómo se llamará tu bot? (Enter = HomeBot)"; if (-not $nombre) { $nombre = "HomeBot" }
$dueno  = Read-Host "¿Cómo te llamas tú?"; if (-not $dueno) { $dueno = "tu dueño" }
$tono   = Read-Host "¿Qué tono quieres? (Enter = cercano, tranquilo y con chispa)"; if (-not $tono) { $tono = "cercano, tranquilo y con chispa" }
if (-not (& hermes profile list 2>&1 | Select-String -SimpleMatch "homebot")) {
    & hermes profile create homebot --no-alias --description "HomeBot: asistente personal" | Out-Null
}
$cfg  = (& hermes -p homebot config path).Trim()
$envp = (& hermes -p homebot config env-path).Trim()
$dir  = Split-Path -Parent $cfg
$alma = (Get-Content plantillas\SOUL.md -Raw -Encoding UTF8).Replace("{{NOMBRE}}",$nombre).Replace("{{DUENO}}",$dueno).Replace("{{TONO}}",$tono)
[IO.File]::WriteAllText((Join-Path $dir "SOUL.md"), $alma, (New-Object Text.UTF8Encoding $false))
& hermes -p homebot config set model.provider deepseek | Out-Null
& hermes -p homebot config set model.default deepseek-flash | Out-Null
foreach ($t in "terminal","file","code_execution","browser","computer_use","delegation","image_gen","tts") {
    & hermes -p homebot tools disable $t 2>&1 | Out-Null
}
Write-Host "Perfil 'homebot' listo (sin terminal ni archivos: solo conversa y busca en la web)."

Paso "5/6 Tu API key de DeepSeek"
& .\cambiar-clave.ps1 -Silencioso

Paso "6/6 Arranque con Windows"
$pyw  = Join-Path $Aqui ".venv\Scripts\pythonw.exe"
$lnk  = Join-Path ([Environment]::GetFolderPath("Startup")) "HomeBot.lnk"
$sh   = New-Object -ComObject WScript.Shell
$a    = $sh.CreateShortcut($lnk); $a.TargetPath = $pyw; $a.Arguments = "`"$Aqui\homebot.py`""; $a.WorkingDirectory = $Aqui; $a.Save()
Start-Process $pyw -ArgumentList "`"$Aqui\homebot.py`"" -WorkingDirectory $Aqui
Write-Host "`nListo. Pulsa  Windows + Y  para hablar (otra vez para enviar)." -ForegroundColor Green
Write-Host "  Windows + Shift + Y  escribirle   |   Windows + Ctrl + Y  cortar"
Write-Host "La primera vez que hables tardará un poco: descarga el modelo de voz (~500 MB)."
