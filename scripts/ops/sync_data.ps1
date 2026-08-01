# Pull the latest cloud-collected data into the local data/ layer (docs/30).
#
# Precondition: data/ has been seeded as a clone of the PRIVATE trading-data repo
# (one-time steps in docs/30-cloud-drip.md §4). Until then this script just explains.
# Direction is cloud -> local only; local sessions keep writing locally and the
# daily-drip workflow keeps writing in the cloud -- git merges both histories.

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$data = Join-Path $repo "data"

if (-not (Test-Path (Join-Path $data ".git"))) {
    Write-Host "[sync] data\ is not yet a clone of the private trading-data repo."
    Write-Host "[sync] One-time setup: docs/30-cloud-drip.md section 4 (seed + secrets)."
    exit 0
}

Write-Host "[sync] pulling cloud drips into data\ ..."
git -C $data pull --rebase --autostash
git -C $data log --oneline -3
Write-Host "[sync] done. If local sessions collected new data, push it back with:"
Write-Host "       git -C data add -A; git -C data commit -m 'local drip'; git -C data push"
