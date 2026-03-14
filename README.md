
# STANDARD Python Template
`src/`, `res/`, pytest, PyInstaller, dual-shell scripts & tasks.

## Setup
- PowerShell:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\scripts\setup-env.ps1
  ```
- CMD:
  ```bat
  scripts\setup-env.cmd
  ```
- macOS/Linux:
  ```bash
  bash ./scripts/setup-env.sh
  ```

## Build (bundled exe)
- PowerShell:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
  ```
- CMD:
  ```bat
  scripts\build.cmd
  ```
- macOS/Linux:
  ```bash
  bash ./scripts/build.sh
  ```
