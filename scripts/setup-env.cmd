
@echo off
setlocal ENABLEDELAYEDEXPANSION
python -m venv .venv || goto :error
set PYTHON_EXE=.venv\Scripts\python.exe
"%PYTHON_EXE%" -m pip install --upgrade pip || goto :error
"%PYTHON_EXE%" -m pip install -r requirements-dev.txt || goto :error
if exist requirements.txt (
  for /f %%A in (requirements.txt) do set HASREQ=1
)
if defined HASREQ (
  "%PYTHON_EXE%" -m pip install -r requirements.txt || goto :error
)
echo.
echo [OK] .venv ready.
exit /b 0
:error
echo Setup failed. Check error above.
exit /b 1
