#Requires -Version 5.1
<#
.SYNOPSIS
    Build completo: PyInstaller + firma del .exe + instalador Inno Setup + firma del setup.

.PARAMETER SkipSign
    Omite la firma (solo para pruebas locales sin certificado).

.PARAMETER SkipBuild
    Reutiliza dist\LiBooks.exe existente.

.EXAMPLE
    $env:LIBOOKS_SIGN_PFX = "C:\certs\codesign.pfx"
    $env:LIBOOKS_SIGN_PASSWORD = "tu-contraseña"
    .\scripts\build_installer.ps1
#>
param(
    [switch]$SkipSign,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

function Get-BuildPython {
    $venvPy = Join-Path $Root ".build-venv\Scripts\python.exe"
    if (Test-Path $venvPy) { return $venvPy }
    return "python"
}

function Get-AppVersion {
    $py = Get-BuildPython
    & $py -c "from version import APP_VERSION; print(APP_VERSION)"
}

function Find-InnoCompiler {
    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
        "${env:LocalAppData}\Programs\Inno Setup 6\ISCC.exe"
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) { return $path }
    }
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

$version = (Get-AppVersion).Trim()
Write-Host "LiBooks v$version - build de instalador" -ForegroundColor Cyan
Write-Host ""

# ── 1. Compilar ejecutable ─────────────────────────────────────────────
if (-not $SkipBuild) {
    & (Join-Path $PSScriptRoot "build_windows.ps1")
} elseif (-not (Test-Path "dist\LiBooks.exe")) {
    throw "dist\LiBooks.exe no existe. Ejecuta sin -SkipBuild."
}

$exePath = Join-Path $Root "dist\LiBooks.exe"

# ── 2. Firmar ejecutable ─────────────────────────────────────────────
if (-not $SkipSign) {
    Write-Host ""
    Write-Host "Firmando LiBooks.exe..." -ForegroundColor Cyan
    & (Join-Path $PSScriptRoot "code_sign.ps1") -FilePath $exePath
} else {
    Write-Host "Firma omitida (-SkipSign)." -ForegroundColor Yellow
}

# ── 3. Compilar instalador Inno Setup ──────────────────────────────────
$iscc = Find-InnoCompiler
if (-not $iscc) {
    throw @"
No se encontró Inno Setup 6 (ISCC.exe).
Descarga: https://jrsoftware.org/isdl.php
"@
}

$iss = Join-Path $Root "installer\libooks.iss"
$setupName = "LiBooks-Setup-$version.exe"
$setupPath = Join-Path $Root "dist\$setupName"

Write-Host ""
Write-Host "Compilando instalador..." -ForegroundColor Cyan
& $iscc "/DMyAppVersion=$version" $iss
if ($LASTEXITCODE -ne 0) {
    throw "ISCC falló con código $LASTEXITCODE"
}

if (-not (Test-Path $setupPath)) {
    throw "No se generó el instalador esperado: $setupPath"
}

# ── 4. Firmar instalador ───────────────────────────────────────────────
if (-not $SkipSign) {
    Write-Host ""
    Write-Host "Firmando instalador..." -ForegroundColor Cyan
    & (Join-Path $PSScriptRoot "code_sign.ps1") -FilePath $setupPath -Description "LiBooks Setup"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Instalador listo:" -ForegroundColor Green
Write-Host " $setupPath" -ForegroundColor White
if (-not $SkipSign) {
    Write-Host " Firmado con Authenticode + marca de tiempo" -ForegroundColor Green
} else {
    Write-Host " SIN FIRMA - solo para pruebas locales" -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Green
