# Weam M5 — Test Setup Fix

إصلاح صغير لاختبار M5 الذي ينشئ حساب مختص دون حقل `provider_specialty` الإلزامي.

- لا يغير كود المنتج أو منطق المطابقة.
- لا يغير قاعدة البيانات ولا يحتاج Migration جديدة.
- لا يغير Frontend.

## التطبيق من جذر المشروع

```powershell
powershell.exe -ExecutionPolicy Bypass -File ".\Weam_M5_Test_Setup_FIX_PATCH\Apply-WeamM5TestFix.ps1"
```

## الاختبار

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q tests\test_center_matching.py
.\.venv\Scripts\python.exe -m pytest -q
```
