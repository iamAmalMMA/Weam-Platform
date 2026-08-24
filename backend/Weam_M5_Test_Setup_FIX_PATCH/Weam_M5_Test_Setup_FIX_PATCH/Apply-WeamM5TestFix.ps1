param(
    [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$PatchRoot = $PSScriptRoot
$RelativePath = "backend\tests\test_center_matching.py"
$OriginalHash = "7d7b4543a5f881d7ff2d5e30a69e8e0644feded3acd549c979199068dc367c6d"
$PatchedHash = "82e00d27e1a2f5386bed8f469d7908b16b9264017b3f33050a73d4350223e19b"

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot "backend\app\main.py"))) {
    Write-Error "لم يتم العثور على Backend. شغّل الملف من جذر مشروع وئام الحالي."
    exit 1
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

$SourcePath = Join-Path $PatchRoot ("files\" + $RelativePath)
$TargetPath = Join-Path $ProjectRoot $RelativePath

if (-not (Test-Path -LiteralPath $SourcePath)) {
    Write-Error "ملف الإصلاح ناقص داخل الحزمة: $RelativePath"
    exit 1
}
if ((Get-Sha256 $SourcePath) -ne $PatchedHash) {
    Write-Error "فشل التحقق من سلامة ملف الإصلاح."
    exit 1
}
if (-not (Test-Path -LiteralPath $TargetPath)) {
    Write-Error "ملف اختبار M5 غير موجود. طبّق حزمة M5 الأساسية أولًا."
    exit 1
}

$CurrentHash = Get-Sha256 $TargetPath
if ($CurrentHash -eq $PatchedHash) {
    Write-Host "إصلاح اختبار M5 مطبق مسبقًا." -ForegroundColor Green
    exit 0
}
if ($CurrentHash -ne $OriginalHash) {
    Write-Error "ملف اختبار M5 مختلف عن النسخة المتوقعة؛ لم يتم تعديل أي ملف."
    exit 1
}

Copy-Item -LiteralPath $SourcePath -Destination $TargetPath -Force
Write-Host "تم إصلاح إعداد حساب المختص داخل اختبار M5 بنجاح." -ForegroundColor Green

