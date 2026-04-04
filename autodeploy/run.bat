@echo off
title Autonomous Auto-Post
cd /d "%~dp0"
echo ========================================
echo   AUTONOMOUS POST DEPLOYER
echo ========================================
echo.
echo Make sure Ollama is running (ollama serve)
echo Press any key to start deployment...
pause >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "deploy-post.ps1"
echo.
pause