#Requires -Version 5.1
# Empaqueta LiBooks para Windows con PyInstaller (entorno aislado .build-venv).
# Uso: .\scripts\build_windows.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$VenvDir = Join-Path $Root ".build-venv"
$Python = Join-Path $VenvDir "Scripts\python.exe"
$Pip = Join-Path $VenvDir "Scripts\pip.exe"

function Ensure-BuildVenv {
    if (-not (Test-Path $Python)) {
        Write-Host "Creando entorno de build (.build-venv)..." -ForegroundColor Cyan
        python -m venv $VenvDir
        if (-not (Test-Path $Python)) {
            throw "No se pudo crear el venv. Comprueba que Python 3.9+ este instalado."
        }
    }
}

Ensure-BuildVenv

Write-Host "Instalando dependencias en .build-venv..." -ForegroundColor Cyan
& $Python -m pip install --upgrade pip --quiet
& $Pip install -r requirements.txt pyinstaller pillow
if ($LASTEXITCODE -ne 0) {
    throw "pip install fallo. Revisa requirements.txt y tu conexion."
}

if (Test-Path "assets\icons\app_icon_512.png") {
    Write-Host "Generando iconos (render nativo por tamano)..." -ForegroundColor Cyan
    & $Python scripts\generate_app_icons.py
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudieron generar los iconos."
    }
}

Write-Host "Compilando ejecutable..." -ForegroundColor Cyan
& $Python -m PyInstaller libooks.spec --noconfirm
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller fallo con codigo $LASTEXITCODE"
}

$dist = Join-Path $Root "dist\LiBooks.exe"
if (Test-Path $dist) {
    Write-Host ""
    Write-Host "Listo: $dist" -ForegroundColor Green
    Write-Host "Siguiente paso (instalador firmado):" -ForegroundColor Yellow
    Write-Host "  .\scripts\build_installer.ps1" -ForegroundColor White
} else {
    throw "No se genero el ejecutable."
}
