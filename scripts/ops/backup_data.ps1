# Backup the single-disk data layer (docs/29 u9).
#
# What is protected WHERE:
#   collected/  (options/analyst/8k/gdelt snapshots) -- git-tracked, pushed daily by
#               the monitor bot => GitHub IS the off-site backup; not this script's job.
#   data/       (~540MB: FinMind panels, OHLCV store, Form-4, fundamentals, drip
#               states) -- gitignored, SINGLE DISK. Re-downloadable in principle but
#               at ~1 month of quota-limited drip time. This script snapshots it.
#
# Usage:
#   powershell -File scripts/ops/backup_data.ps1                # default local dest
#   powershell -File scripts/ops/backup_data.ps1 -Dest "E:\bk"  # external/cloud dir
#
# A SAME-DISK archive protects against deletion/corruption only. For disk-loss
# protection point -Dest at an external drive or a cloud-synced folder
# (MEGAsync/OneDrive are installed on this machine). Keeps the 6 newest archives.

param(
    [string]$Dest = "$env:USERPROFILE\Backups\trading-analysis"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$stamp = Get-Date -Format "yyyy-MM-dd_HHmm"
New-Item -ItemType Directory -Force $Dest | Out-Null

$target = Join-Path $Dest "data_$stamp.zip"
Write-Host "[backup] compressing data\ -> $target"
Compress-Archive -Path (Join-Path $repo "data") -DestinationPath $target -CompressionLevel Optimal

$mb = [math]::Round((Get-Item $target).Length / 1MB, 1)
Write-Host "[backup] done: $target ($mb MB)"

# manifest: sizes per subdir + drip-state summary, next to the archive
$manifest = Join-Path $Dest "manifest_$stamp.txt"
Get-ChildItem (Join-Path $repo "data") -Directory | ForEach-Object {
    $s = (Get-ChildItem $_.FullName -Recurse -File -EA SilentlyContinue | Measure-Object Length -Sum).Sum
    "{0,-28} {1,10:N1} MB" -f $_.Name, ($s / 1MB)
} | Set-Content -Encoding utf8 $manifest
Get-ChildItem (Join-Path $repo "data") -Filter "_*state*.json" | ForEach-Object {
    Add-Content -Encoding utf8 $manifest ("state: " + $_.Name)
}
Write-Host "[backup] manifest: $manifest"

# retention: keep the 6 newest archives
Get-ChildItem $Dest -Filter "data_*.zip" | Sort-Object Name -Descending |
    Select-Object -Skip 6 | ForEach-Object {
        Write-Host "[backup] pruning old archive $($_.Name)"
        Remove-Item $_.FullName -Confirm:$false
    }
