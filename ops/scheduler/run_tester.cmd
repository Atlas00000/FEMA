@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scheduled_tester.ps1"
exit /b %ERRORLEVEL%
