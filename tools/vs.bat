@echo off
rem Runs the arguments with the VS 2022 build tools, clang, CMake and Ninja on PATH, from the repo root.
for /f "usebackq tokens=*" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -property installationPath`) do set "VS=%%i"
call "%VS%\Common7\Tools\VsDevCmd.bat" -arch=amd64 -host_arch=amd64 >nul
set "VSCMAKE=%VS%\Common7\IDE\CommonExtensions\Microsoft\CMake"
set "PATH=%VSCMAKE%\CMake\bin;%VSCMAKE%\Ninja;%VS%\VC\Tools\Llvm\x64\bin;%PATH%"
cd /d "%~dp0.."
%*
