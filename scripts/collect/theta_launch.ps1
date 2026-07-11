# Theta Terminal launcher (docs/24 action #3, ThetaData free tier).
# Reads THETADATA_EMAIL / THETADATA_PASSWORD from the repo .env, regenerates
# ~/.theta/creds.txt, and launches ThetaTerminal.jar with --creds-file (which
# reads the file directly -- no password on the command line / in process args).
# The portable JRE + jar live in ~/.theta (installed 2026-07-12; see chat).
#
# NOTE: ThetaData's auth rejects passwords containing certain special characters
# (e.g. '#', '$'). If you see INVALID_CREDENTIALS, reset the password at
# thetadata.net to letters+digits only, update .env, and re-run this.
#
# Run:  powershell -ExecutionPolicy Bypass -File scripts\collect\theta_launch.ps1
#       (from the repo root)

$ErrorActionPreference = "Stop"
$theta = Join-Path $env:USERPROFILE ".theta"
$java  = (Get-Content (Join-Path $theta "java_path.txt") -Raw).Trim()
$jar   = Join-Path $theta "ThetaTerminal.jar"

# regenerate creds.txt from the repo .env (single source of truth)
$envFile = Join-Path (Get-Location) ".env"
$email = ""; $pw = ""
foreach ($ln in Get-Content $envFile) {
    if ($ln -like "THETADATA_EMAIL=*")    { $email = $ln.Substring(16) }
    if ($ln -like "THETADATA_PASSWORD=*") { $pw    = $ln.Substring(19) }
}
if (-not $email -or -not $pw) { Write-Output "THETADATA_EMAIL/PASSWORD missing from .env"; exit 1 }
$creds = Join-Path $theta "creds.txt"
Set-Content -Path $creds -Value @($email, $pw) -Encoding Ascii

# stop any prior instance
Get-CimInstance Win32_Process -Filter "name='java.exe'" |
    Where-Object { $_.CommandLine -like "*ThetaTerminal*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2

$log = Join-Path $theta "terminal.log"
if (Test-Path $log) { Clear-Content $log }
$p = Start-Process -FilePath $java `
    -ArgumentList @("-jar", $jar, "--creds-file", $creds) `
    -WorkingDirectory $theta -WindowStyle Hidden `
    -RedirectStandardOutput $log -RedirectStandardError (Join-Path $theta "terminal.err.log") `
    -PassThru
Write-Output "Theta Terminal launched (PID $($p.Id)). Waiting 20s to confirm login ..."
Start-Sleep -Seconds 20
if (Select-String -Path $log -Pattern "INVALID_CREDENTIALS" -Quiet) {
    Write-Output "LOGIN FAILED (INVALID_CREDENTIALS) -- reset the password (letters+digits only) and re-run."
} elseif (Select-String -Path $log -Pattern "CONNECTED|Listening|http" -Quiet) {
    Write-Output "Login OK. REST API on http://127.0.0.1:25510"
} else {
    Write-Output "Status unclear; last log lines:"
    Get-Content $log -Tail 8
}
