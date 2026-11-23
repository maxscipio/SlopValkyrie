# Sample the hottest thread of a running game a few times and print the host frames (symbolised through the pdb next to the exe).
# For a hang: spinning guest thread + frozen frame counter = missing wake-up in the HLE. Usage: rip.ps1 -ProcId <pid> -Exe <GAME_EXE>
param([int]$ProcId, [string]$Exe, [int]$Samples = 8)
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public static class Rip {
    [DllImport("kernel32.dll")] static extern IntPtr OpenThread(uint a, bool i, uint tid);
    [DllImport("kernel32.dll")] static extern uint SuspendThread(IntPtr h);
    [DllImport("kernel32.dll")] static extern uint ResumeThread(IntPtr h);
    [DllImport("kernel32.dll")] static extern bool GetThreadContext(IntPtr h, IntPtr ctx);
    [DllImport("kernel32.dll")] static extern bool ReadProcessMemory(IntPtr p, ulong a, byte[] b, int n, out int r);
    [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(uint a, bool i, int pid);
    [DllImport("dbghelp.dll", CharSet = CharSet.Ansi)] static extern bool SymInitialize(IntPtr p, string path, bool inv);
    [DllImport("dbghelp.dll", CharSet = CharSet.Ansi)] static extern ulong SymLoadModuleEx(IntPtr p, IntPtr f, string img, string mod, ulong b, uint s, IntPtr d, uint fl);
    [DllImport("dbghelp.dll", CharSet = CharSet.Ansi)] static extern bool SymFromAddr(IntPtr p, ulong a, out ulong disp, IntPtr sym);
    [DllImport("dbghelp.dll")] static extern uint SymSetOptions(uint o);

    public static string SymPath = "";
    public static string Sample(int pid, uint tid, string modPath, ulong modBase) {
        IntPtr hp = OpenProcess(0x1F0FFF, false, pid);
        IntPtr ht = OpenThread(0x1FFFFF, false, tid);
        SuspendThread(ht);
        IntPtr ctx = Marshal.AllocHGlobal(2048 + 64);
        long al = ((long)ctx + 15) & ~15L;
        IntPtr c = (IntPtr)al;
        for (int i = 0; i < 1232; i++) Marshal.WriteByte(c, i, 0);
        Marshal.WriteInt32(c, 0x30, 0x10000F);
        GetThreadContext(ht, c);
        ulong rip = (ulong)Marshal.ReadInt64(c, 0xF8);
        ulong rsp = (ulong)Marshal.ReadInt64(c, 0x98);
        var sb = new StringBuilder();
        // top-of-stack return address scan
        byte[] stk = new byte[8 * 48]; int rd;
        ReadProcessMemory(hp, rsp, stk, stk.Length, out rd);
        List<ulong> addrs = new List<ulong> { rip };
        for (int i = 0; i + 8 <= rd; i += 8) {
            ulong v = BitConverter.ToUInt64(stk, i);
            if (v >= modBase && v < modBase + 0x4000000) addrs.Add(v);
        }
        ResumeThread(ht);
        SymSetOptions(0x2 | 0x4 | 0x10000);
        SymInitialize(hp, SymPath, true);
        int n = 0;
        foreach (ulong a in addrs) {
            IntPtr sym = Marshal.AllocHGlobal(512);
            for (int i = 0; i < 512; i++) Marshal.WriteByte(sym, i, 0);
            Marshal.WriteInt32(sym, 0, 88);
            Marshal.WriteInt32(sym, 80, 400);
            ulong d;
            string name = SymFromAddr(hp, a, out d, sym) ? Marshal.PtrToStringAnsi(sym + 84) : "?";
            sb.AppendLine(string.Format("  {0:X} {1}+{2:X}", a, name, d));
            if (++n >= 12) break;
        }
        return sb.ToString();
    }
}
'@
$p = Get-Process -Id $ProcId
[Rip]::SymPath = Split-Path (($p.Modules | ? { $_.ModuleName -eq "$Exe.exe" }).FileName)
$mod = $p.Modules | ? { $_.ModuleName -eq "$Exe.dll" -or $_.ModuleName -eq "$Exe.exe" } | Select -First 2
$mod | % { "{0} base {1:X} size {2}" -f $_.ModuleName, [int64]$_.BaseAddress, $_.ModuleMemorySize }
$hot = $p.Threads | Sort { $_.TotalProcessorTime } -Descending | Select -First 1
"hot thread $($hot.Id)"
foreach ($m in $mod) {
    "--- $($m.ModuleName)"
    for ($i = 0; $i -lt $Samples; $i++) {
        [Rip]::Sample($ProcId, [uint32]$hot.Id, $m.FileName, [uint64][int64]$m.BaseAddress)
        "  ."
        Start-Sleep -m 150
    }
}
