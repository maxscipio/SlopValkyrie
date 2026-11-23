# Rebuild (Release), copy to out\run (which holds the ISO in assets\), run for N seconds and show the log tail.
# The exe name is GAME_EXE from build.bat; the log is the newest file in out\run\logs.
param([int]$Seconds = 40, [int]$Tail = 40, [switch]$NoRun)
$ErrorActionPreference = "Continue"
$root = Split-Path $PSScriptRoot
$Exe = ((Select-String -Path (Join-Path $root "build.bat") -Pattern 'GAME_EXE=(\S+?)"?$').Matches[0].Groups[1].Value)
$vs = & "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -property installationPath
$bat = Join-Path $env:TEMP "recomp_iter.bat"
@"
@echo off
call "$vs\Common7\Tools\VsDevCmd.bat" -arch=amd64 -host_arch=amd64 >nul
set "VSCMAKE=$vs\Common7\IDE\CommonExtensions\Microsoft\CMake"
set "PATH=%VSCMAKE%\CMake\bin;%VSCMAKE%\Ninja;$vs\VC\Tools\Llvm\x64\bin;%PATH%"
cd /d $root
cmake --preset release >nul || exit /b 1
cmake --build out\build\release 2>&1
"@ | Out-File -Encoding ascii $bat
cmd /c "`"$bat`"" | Select-Object -Last 12
if ($LASTEXITCODE -ne 0) { Write-Host "BUILD FAILED"; return }
$run = Join-Path $root "out\run"
New-Item -ItemType Directory -Force $run | Out-Null
Copy-Item "$root\out\build\release\$Exe.exe", "$root\out\build\release\$Exe.dll", "$root\out\build\release\$Exe.pdb" $run -Force
# an exe-only rebuild leaves the DLL older than the exe, and the exe would then recompile the game code on start
(Get-Item "$run\$Exe.dll").LastWriteTime = Get-Date
if ($NoRun) { return }
Remove-Item "$run\logs\*.log" -ErrorAction SilentlyContinue
$p = Start-Process -FilePath "$run\$Exe.exe" -WorkingDirectory $run -PassThru
$p.WaitForExit($Seconds * 1000) | Out-Null
$alive = -not $p.HasExited
if ($alive) { Write-Host "still running after $Seconds s"; Stop-Process -Id $p.Id }
$log = Get-ChildItem "$run\logs\*.log" | Sort-Object LastWriteTime | Select-Object -Last 1
Get-Content $log.FullName -Tail $Tail
