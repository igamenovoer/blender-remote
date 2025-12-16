[CmdletBinding()]
param(
    [switch]$Force,
    [string]$BlenderVersion,
    [string]$BlenderDownloadUrl
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$externDir = $PSScriptRoot
$repoRoot = (Resolve-Path (Join-Path $externDir "..")).Path

$tmpDir = Join-Path $repoRoot (Join-Path "tmp" "blender-win64")
$blenderDir = Join-Path $externDir "blender-win64"

function Get-LatestBlenderWin64ZipUrl {
    param(
        [string]$BlenderVersion,
        [string]$BlenderDownloadUrl
    )

    $base = "https://download.blender.org/release/"

    if ($BlenderDownloadUrl) {
        return $BlenderDownloadUrl
    }

    if ($BlenderVersion) {
        $parts = $BlenderVersion.Split(".")
        if ($parts.Length -lt 2) {
            throw "BLENDER_VERSION must look like 'X.Y.Z' (got '$BlenderVersion')"
        }
        $majorMinor = "$($parts[0]).$($parts[1])"
        return "${base}Blender${majorMinor}/blender-${BlenderVersion}-windows-x64.zip"
    }

    $indexHtml = (Invoke-WebRequest -UseBasicParsing -Uri $base).Content
    $minorVers = [regex]::Matches($indexHtml, "Blender(\d+)\.(\d+)/") | ForEach-Object {
        [version]"$($_.Groups[1].Value).$($_.Groups[2].Value)"
    } | Sort-Object -Unique
    if (-not $minorVers) {
        throw "Failed to discover Blender release directories from $base"
    }

    $latestMinor = $minorVers | Sort-Object | Select-Object -Last 1
    $relDir = "Blender$($latestMinor.Major).$($latestMinor.Minor)/"

    $relHtml = (Invoke-WebRequest -UseBasicParsing -Uri ($base + $relDir)).Content
    $patchVers = [regex]::Matches($relHtml, "blender-(\d+\.\d+\.\d+)-windows-x64\.zip") | ForEach-Object {
        [version]$_.Groups[1].Value
    } | Sort-Object -Unique
    if (-not $patchVers) {
        throw "Failed to discover Blender windows-x64 zip in $($base + $relDir)"
    }

    $latestPatch = $patchVers | Sort-Object | Select-Object -Last 1
    return ($base + $relDir + "blender-$latestPatch-windows-x64.zip")
}

Write-Host "Bootstrapping externals in $externDir ..."
New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null
New-Item -ItemType Directory -Force -Path $blenderDir | Out-Null

$url = Get-LatestBlenderWin64ZipUrl -BlenderVersion $BlenderVersion -BlenderDownloadUrl $BlenderDownloadUrl
$zipName = Split-Path -Leaf $url
$zipPath = Join-Path $tmpDir $zipName

if ((-not $Force) -and (Test-Path $zipPath)) {
    Write-Host "  - Blender zip already present; skipping download: $zipPath"
} else {
    Write-Host "  - Downloading Blender: $url"
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $zipPath
}

$existingExtract = Get-ChildItem -Path $blenderDir -Directory -Filter "blender-*-windows-x64" -ErrorAction SilentlyContinue
if ($Force -and $existingExtract) {
    Write-Host "  - Removing existing extracted Blender (force)"
    $existingExtract | ForEach-Object { Remove-Item -Recurse -Force -Path $_.FullName }
    $existingExtract = @()
}

$hasExe = $false
foreach ($d in $existingExtract) {
    if (Test-Path (Join-Path $d.FullName "blender.exe")) {
        $hasExe = $true
        break
    }
}

if ($hasExe) {
    Write-Host "  - Blender already extracted; leaving as-is."
} else {
    Write-Host "  - Extracting: $zipPath"
    Expand-Archive -Path $zipPath -DestinationPath $blenderDir -Force
}

$exe = Get-ChildItem -Path $blenderDir -Filter "blender.exe" -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $exe) {
    throw "Blender extraction did not produce blender.exe under $blenderDir"
}

Write-Host "Done. Blender: $($exe.FullName)"
