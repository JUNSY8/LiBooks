#Requires -Version 5.1
<#
.SYNOPSIS
    Crea un certificado autofirmado SOLO para probar el flujo de firma local.
    NO sirve para distribución pública (SmartScreen seguirá bloqueando).

.EXAMPLE
    .\scripts\create_self_signed_cert.ps1
    $env:LIBOOKS_SIGN_PFX = "..\certs\libooks-test.pfx"
    $env:LIBOOKS_SIGN_PASSWORD = "test1234"
    .\scripts\build_installer.ps1
#>
param(
    [string]$OutputDir = (Join-Path (Split-Path $PSScriptRoot -Parent) "certs"),
    [string]$Password = "test1234",
    [string]$Subject = "CN=LiBooks Test Code Signing, O=JUNSY, C=ES"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$pfxPath = Join-Path $OutputDir "libooks-test.pfx"

$cert = New-SelfSignedCertificate `
    -Type CodeSigningCert `
    -Subject $Subject `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -KeyExportPolicy Exportable `
    -KeyLength 2048 `
    -HashAlgorithm SHA256 `
    -NotAfter (Get-Date).AddYears(2)

$secure = ConvertTo-SecureString -String $Password -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $secure | Out-Null

Write-Host ""
Write-Host "Certificado de PRUEBA creado:" -ForegroundColor Yellow
Write-Host "  PFX: $pfxPath"
Write-Host "  Thumbprint: $($cert.Thumbprint)"
Write-Host ""
Write-Host "Para firmar en esta sesión:" -ForegroundColor Cyan
Write-Host "  `$env:LIBOOKS_SIGN_PFX = `"$pfxPath`""
Write-Host "  `$env:LIBOOKS_SIGN_PASSWORD = `"$Password`""
Write-Host "  .\scripts\build_installer.ps1"
Write-Host ""
Write-Host "NO uses este certificado para clientes reales." -ForegroundColor Red
