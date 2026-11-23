# Gun Valkyrie (Xbox, Smilebit/Sega 2002) porting notes

## Milestone 1: XBE identified and symbols resolved

- Disc `Gun Valkyrie (Europe) (En,Fr,De,Es,It).iso` (1,067,057,152 bytes, XDVDFS). It holds `data\xbox\` (about 1,800 files),
  `Media\` (`SOUNDADX.BIN` 199 MB, `SOUNDWAV.BIN` 118 MB, `GvSoundConf.txt`) and one `default.xbe`.
- `default.xbe`: 2,646,016 bytes, SHA-1 `C180A284B3D469093289EF2865A0031EC8D67F47`, title `GUNVALKYRIE`, title ID `49470017`
  (IG-023), retail, base 0x10000, entry 0x13B719, image 0x2E2440, debug name `C:\prj\netgun\Release\NetGunXB\NetGunXB.exe`.
- **XDK 4134 for every library** (XAPILIB, D3DX8, DSOUND, XBOXKRNL, LIBCMT, LIBCPMT, D3D8, XGRAPHC). The SDK has no 4134 data;
  the nearest is `xdk\4361\layout.toml` (layout only, from Burnout).
- Sections: `.text` 0x17FF30, D3DX 0x650, DSOUND, MMATRIX, D3D, XGRPH, XPP, `.rdata`, `.data`, EFFDATA, DOLBY, `$$XTIMAGE`.
  No XNET/XONLINE/XVOICE, WMA or Bink. No video file on the disc.
- `xbe_symbols` originally stopped with "no signatures for these library builds; available: 4831 4928 5455 5659 5849". All 8
  libraries are 1.0.4134.
- Resolved symbols (done): no 4134 or 4361 libs are on this machine, so the Burnout XBE (XDK 4361) was used as a proxy. Its
  `game.toml` was signed with `xbe_symbols --sign`, giving `xdk\4134\signatures.toml` (a proxy, not real 4134 signatures).
  `xbe_symbols` then matched 355 of 696 functions; the rest of the D3D, DSOUND and XPP names were checked by hand by
  diffing against Burnout (`tools\sidebyside.py`, `gapmatch.py`, `libcalls.py`). `tools\hlecheck.py` compares every mapped
  name's `ret N` with the HLE argument count: 55 consistent, 0 mismatched.
- `xdk\4134\layout.toml` is written from the Valkyrie code. Fields from 0x44C to 0x460 sit 4 bytes lower than in 4361 (ZScale
  0x44C, SuperSampleX 0x454, SuperSampleY 0x458). Render-state defaults and tables are byte-identical to 4361, so
  `RenderState_Numbering = 4361`. Left out on purpose, so they trap if used: `CDevice_Palettes` (4134 has no SetPalette),
  VBlankCallback/VBlankCount (VerticalBlank stays disabled as with Burnout) and the stream vtables (the game never creates a
  DirectSound stream).
- Signature matches in DSOUND were ambiguous because the thunks have the same shape; the callee decided. Corrected: 0x191FFC is
  SetHeadroom (there is no SetEG), 0x192018 SetMixBins, 0x1927A6 SetI3DL2Source (not SetMode, now 0), plus Lock, Unlock,
  Get/SetCurrentPosition, SetPosition, SetVelocity, `DSound_GetObject` and `IDirectSound_Release`.
  **Unverified:** 0x192782 (float + apply) is mapped as `SetMinDistance`; it could be MaxDistance.
- `XInputOpen` is 0x1B594D (it compares the type pointer with the three XPP type records at 0x1AEA20/2C/38).
- No `setjmp3`/`longjmp` code exists in this XBE (no matching bytes), so no `[xbe] setjmp` key is needed.
- `D3DDevice_SetTextureState_ParameterCheck` (0x1A2369) is unverified; no HLE uses it.
- Next: first full build (Milestone 2).

## Milestone 2: first build

- `tools\iter.ps1 -NoRun` configures (fetches SDL3, Zydis, ImGui, VMA) and builds in about 15 minutes; the recompiler wrote 12,722
  functions into 32 partitions. Later builds only recompile changed partitions or the runtime (5 to 10 minutes).
- The ISO is hardlinked into `out\run\assets\GunValkyrie.iso`.

## Milestone 3: boots to the title screen

First-run failures and their fixes, all in `config\game.toml`:

| Symptom | Cause | Fix |
|---------|-------|-----|
| `indirect call to 00163C00 has no recompiled function` | virtual function stored only in a vtable | `[[function]]` entries; the data scan (pointers into `.text` from `.rdata` that are not recompiled functions) found 19 more in the 0x153420 to 0x16C8C0 range |
| `indirect call to 001AEBCC` | callbacks inside the XPP device type records | `[[function]]` for the 0x1AEA50 records (0x1AEBCC, 0x1B0443, 0x1AFE6E and 11 more) |
| read of 0xFED00000 in XPP | `XInitDevices` not mapped, so the guest USB stack ran | `XInitDevices` = 0x1AF818 (thunk to 0x1AEE0C, `ret 8`). `hlecheck.py` reports a false mismatch because the thunk is a `jmp` and the next `ret` belongs to XGetDevices |
| null read in `D3D_BlockOnTime` (0x1A1C80) after 17 s | vertex buffer `Lock` calls `BlockUntilNotBusy`, which reads the GPU put pointer | mapped `D3D_BlockOnTime` 0x1A1C80, `D3DResource_BlockUntilNotBusy` 0x1A1FF0, `D3D_BlockOnResource` 0x1A1F70, `D3DResource_IsBusy` 0x1A0120, `D3D_KickOffAndWaitForIdle` 0x1A1F50 |

- Result: the title screen ("Please press START to begin.") renders on D3D12 (Intel Iris Xe), the log is clean and the process stays up.
- Visual issue to look at: the blue glow on the GUN VALKYRIE logo shows scrambled texture content. It may be an intended animation; compare with a console capture.
- Not mapped (the game may need them later): `D3DDevice_BlockOnFence`, `InsertFence`, `IsFencePending`, `D3D_SetFence`
  (no separate fence functions were found in the 4134 D3D; `BlockOnTime` is called directly).
- Gamepad: the log said `Xbox One Controller ... not recognized as a gamepad` (padmap). Cause: the SDK's `input.cpp` on the `valkyrie`
  branch inherited `SDL_HINT_JOYSTICK_DIRECTINPUT = "1"` from Burnout, so the Xbox One pad (guid `03008d12...045e...02ff`) came up as a raw
  DirectInput joystick with no SDL mapping. The hint is back to `"0"` (as in the Gun SDK branch): the pad now arrives through WGI as
  `XINPUT compatible HID device`. Burnout's `kPadMapping` is still in the file but unused here.
- With a pad connected the game calls `XInputClose`, which was unmapped, so the guest ran on the host handle and crashed (read of
  0xB09D7003 at 8 s). `XInputClose = 0x1B59C2` is now in `config\game.toml`.
- The pad was still dead: before each `XInputGetState` the game calls `XInputPoll` (0x1B5C69, `ret 4`), which was unmapped. The guest
  version reads the handle as an XPP device object, found nothing and returned 0x48F, so the game closed and reopened the pad every
  ~100 ms and never got to `XInputGetState`. `XInputPoll = 0x1B5C69` is now mapped; the SDK's `xapi.cpp` has an HLE that returns 0.
- A `padmap:` startup line can be absent even with a pad plugged in: WGI enumerates after `padmap::Load`. Run with `XBE_LOG=1` to see `input:` lines.
- Thrusting made distant terrain vanish. An F3 capture (`XBE_CAPTURE_DIR`) showed the game draws the whole scene into a 512x384
  offscreen target (a distortion pass) while its depth buffer stays 640x480. `D3D12Backend::BindTargets` dropped the depth buffer
  whenever its size differed from the target's, so all 558 draws ran with no depth test. A depth buffer larger than the target is
  valid and is now kept (`runtime\gpu\d3d12.cpp` and `vulkan.cpp`); confirmed fixed in-game on both backends.
- F8 panel: added the "Aspect ratio" combo (Automatic / 4:3 / 16:9, `Settings::aspect`, applies at the next start), copied from gun-recomp. The SDK side (PR #20) was already in `ref`; only this game's panel lacked the control.
## Milestone 4: moved to the reference SDK, plays

The game now builds against the reference SDK ([maxscipio/XboxXBERecomp](https://github.com/maxscipio/XboxXBERecomp), `main`), which `CMakeLists.txt` downloads unless there is an `sdk` folder here or a checkout in `..\XboxXBERecomp`. The old SDK branch and `patches\sdk.patch` are gone. The SDK's own `docs\games\valkyrie-patches.md` lists what Valkyrie needed from it.

- The old F8/F9/F12 ImGui panels (`enhance`, `graphics`, `pad_mapping`) are removed; the SDK's F1 settings window replaces them, and `overlay` only draws the FPS counter (F10).
- Black screen at start: the game called `XLaunchNewImage` and quit to the dash because its input init returned E_FAIL. Two causes: the disc check `XapiVerifyMediaInDrive` (0x13DE10) was unmapped (now in `config\game.toml`), and the SDK's `XInitDevices` filled the pad record at once, so the game's first `XGetDeviceChanges` saw a pending insertion (the SDK now leaves that to `XGetDevices` and its poller).
- Widescreen: the game has no widescreen mode and draws its 3D with programmable vertex shaders for 4:3 only, so a hook on its projection code was not enough (the matrices are built by 0x14E2E0 and sent as vertex shader constants). `OnInit` in `src\common\game_info.cpp` sets `app::g_widen_3d`, and the SDK renderer narrows the 3D about the centre by 4/3 over the aspect; the stretch to the picture widens it back and shows more of the world. The 2D is kept in a centred 4:3 part at 16:9 and a 16:9 part at 21:9. Open: the game's CPU culling is 4:3, so objects at the edges can pop in; lock-on markers may sit slightly off; Direct3D 12 only.

## Setup facts

- `assets\` holds `default.xbe` (and, before the first run, a hardlink to the ISO); the run folder gets only the ISO hardlink.
- Backend: Direct3D 12 by default; `XBE_BACKEND=vulkan` for Vulkan.
- Names: exe `GunValkyrie`, library `GunValkyrie.dll`, log prefix `gunvalkyrie`.
