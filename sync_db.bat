@echo off
cd /d "%~dp0"
py scripts\sync_db.py %*
