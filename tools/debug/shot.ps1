param([string]$Out, [string]$Exe = "")
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
Add-Type @'
using System; using System.Runtime.InteropServices;
public class Win { [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h); [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int c); }
'@
# one screenshot of the game window; -Exe is the process name (default: the GAME_EXE of ..\..\build.bat if present)
if (-not $Exe) { $bat = Join-Path $PSScriptRoot "..\..\build.bat"; if (Test-Path $bat) { $Exe = ((Select-String -Path $bat -Pattern 'GAME_EXE=(\S+?)"?$').Matches[0].Groups[1].Value) } }
$p = Get-Process $Exe | Where-Object { $_.MainWindowHandle -ne 0 } | Select -Last 1
[Win]::ShowWindow($p.MainWindowHandle, 9) | Out-Null
[Win]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
Start-Sleep 2
$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
$bmp.Save($Out)
