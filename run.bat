@echo off
title EduPredict - Big Data Analytics Portal
echo ========================================================
echo  Launching EduPredict Application (Aptech eProject)
echo ========================================================

REM Check if .venv exists
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run.py
) else (
    python run.py
)
pause
