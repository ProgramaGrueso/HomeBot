# Cambia o pone tu API key de DeepSeek (consíguela en https://platform.deepseek.com/api_keys). Queda SOLO en tu PC.
param([switch]$Silencioso)
$ErrorActionPreference = "Stop"
$envp = (& hermes -p homebot config env-path).Trim()
Write-Host "Pega tu API key de DeepSeek (no se ve mientras escribes) y pulsa Enter:"
$sec = Read-Host -AsSecureString
$clave = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)).Trim()
if (-not $clave) { throw "No escribiste ninguna clave." }
$lineas = @(); if (Test-Path $envp) { $lineas = @(Get-Content $envp -Encoding UTF8 | Where-Object { $_ -notmatch '^DEEPSEEK_API_KEY=' }) }
$lineas += "DEEPSEEK_API_KEY=$clave"
[IO.File]::WriteAllLines($envp, $lineas, (New-Object Text.UTF8Encoding $false))
Write-Host "Clave guardada en $envp"
if (-not $Silencioso) { Write-Host "Reinicia HomeBot (cierra sesión o ejecuta iniciar.bat) para usarla." }
