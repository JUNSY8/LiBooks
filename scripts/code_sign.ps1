#Requires -Version 5.1
<#
.SYNOPSIS
    Firma Authenticode de ejecutables LiBooks (signtool.exe).

.DESCRIPTION
    Usa un certificado .pfx o un certificado del almacén de Windows.
    Variables de entorno recomendadas (no commitear secretos):
      LIBOOKS_SIGN_PFX      — ruta al archivo .pfx
      LIBOOKS_SIGN_PASSWORD — contraseña del .pfx
      LIBOOKS_SIGN_THUMB    — huella SHA1 (alternativa al .pfx, almacén CurrentUser\My)

.EXAMPLE
    $env:LIBOOKS_SIGN_PFX = "C:\certs\junsy-codesign.pfx"
    $env:LIBOOKS_SIGN_PASSWORD = "..."
    .\scripts\code_sign.ps1 -FilePath dist\LiBooks.exe
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$FilePath,

    [string]$CertPath = $env:LIBOOKS_SIGN_PFX,
    [string]$CertPassword = $env:LIBOOKS_SIGN_PASSWORD,
    [string]$CertThumbprint = $env:LIBOOKS_SIGN_THUMB,

    [string]$TimestampUrl = "http://timestamp.digicert.com",
    [string]$Description = "LiBooks",
    [string]$DescriptionUrl = "https://github.com/JUNSY/LiBooks"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $FilePath)) {
    throw "No se encontró el archivo a firmar: $FilePath"
}

function Find-SignTool {
    $kits = @(
        "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\signtool.exe",
        "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x86\signtool.exe",
        "${env:ProgramFiles}\Windows Kits\10\bin\*\x64\signtool.exe"
    )
    foreach ($pattern in $kits) {
        $found = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue |
            Sort-Object { $_.Directory.Name } -Descending |
            Select-Object -First 1
        if ($found) { return $found.FullName }
    }
    $inPath = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($inPath) { return $inPath.Source }
    return $null
}

$signtool = Find-SignTool
if (-not $signtool) {
    throw @"
No se encontró signtool.exe.
Instala «Windows SDK» (Signing Tools for Desktop Apps):
https://developer.microsoft.com/windows/downloads/windows-sdk/
"@
}

$usePfx = [bool]($CertPath -and (Test-Path -LiteralPath $CertPath))
$useStore = [bool]$CertThumbprint

if (-not $usePfx -and -not $useStore) {
    throw @"
Certificado de firma no configurado.
Define LIBOOKS_SIGN_PFX + LIBOOKS_SIGN_PASSWORD
o LIBOOKS_SIGN_THUMB (huella SHA1 del certificado en el almacén).
"@
}

$args = @(
    "sign",
    "/fd", "sha256",
    "/tr", $TimestampUrl,
    "/td", "sha256",
    "/d", $Description,
    "/du", $DescriptionUrl,
    "/v"
)

if ($usePfx) {
    $args += @("/f", (Resolve-Path $CertPath).Path)
    if ($CertPassword) {
        $args += @("/p", $CertPassword)
    }
} else {
    $args += @("/sha1", $CertThumbprint, "/sm")
}

$args += $FilePath

Write-Host "Firmando: $FilePath" -ForegroundColor Cyan
Write-Host "  signtool: $signtool" -ForegroundColor DarkGray
& $signtool @args
if ($LASTEXITCODE -ne 0) {
    throw "signtool falló con código $LASTEXITCODE"
}

& $signtool verify /pa /v $FilePath
if ($LASTEXITCODE -ne 0) {
    throw "La verificación de firma falló"
}

Write-Host "Firma verificada correctamente." -ForegroundColor Green
