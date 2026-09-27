# Package the Humbly Plural Windows release

$zipName = "HumblyPlural-Windows-$(Get-Date -Format yyyyMMdd).zip"
$distExe = Join-Path $PSScriptRoot "dist\HumblyPlural.exe"
$readme = Join-Path $PSScriptRoot "README_humbly_plural.md"
$distReadme = Join-Path $PSScriptRoot "DISTRIBUTION_README.md"

if (-Not (Test-Path $distExe)) {
    Write-Error "HumblyPlural.exe not found in dist\ directory. Build the app first."
    exit 1
}

if (Test-Path $zipName) {
    Remove-Item $zipName -Force
}

Compress-Archive -Path $distExe, $readme, $distReadme -DestinationPath $zipName
Write-Host "Created release package: $zipName"