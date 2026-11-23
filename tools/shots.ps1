param([string]$Tag = 's', [int]$Count = 8, [int]$Every = 10, [int]$First = 20)
# test helper: take screenshots of the running game window
$d = Join-Path $PSScriptRoot '..\out\rundbg'
if (-not (Test-Path $d)) { New-Item -ItemType Directory $d | Out-Null }
$Exe = ((Select-String -Path (Join-Path $PSScriptRoot '..\build.bat') -Pattern 'GAME_EXE=(\S+?)"?$').Matches[0].Groups[1].Value)
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
Add-Type @'
using System; using System.Runtime.InteropServices;
public class W { [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h); }
'@
Start-Sleep $First
for ($i = 0; $i -lt $Count; $i++) {
    $p = Get-Process $Exe -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
    if ($p) {
        [W]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
        Start-Sleep 1
        $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
        $g = [System.Drawing.Graphics]::FromImage($bmp)
        $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
        $bmp.Save("$d\${Tag}_$i.png")
        $g.Dispose(); $bmp.Dispose()
    }
    Start-Sleep $Every
}
