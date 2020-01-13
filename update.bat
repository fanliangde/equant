@echo off

set updatepath="%~dp0update.py"

set pypath="%~dp0..\miniconda\python.exe"
if not exist %pypath% (
	set pypath="python.exe"
)

%pypath% %updatepath%
TIMEOUT /T 10