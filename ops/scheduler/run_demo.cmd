@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scheduled_demo.ps1"
exit /b %ERRORLEVEL%
