# Gun Valkyrie - XBE Recomp

An unofficial native PC port of the original Xbox version of Gun Valkyrie, built with the [Xbox XBE Recomp](https://github.com/maxscipio/XboxXBERecomp) SDK.

> [!NOTE]
> This project does not include any game assets. You must provide the files from your own legally acquired copy of the game.

## Installation

- Put your game files in the `assets` folder: the disc image (`.iso`), or `default.xbe` with the game's folders beside it.
- Run `GunValkyrie.exe`.
- Settings are in `settings.toml` beside the exe, and in the F1 settings window.

## Features

- Direct3D 12 renderer with resolution scale, MSAA and a frame rate cap. The frame rate does not change the game's speed.
- Aspect ratio: 4:3, 16:9 or fill the screen (21:9). The game draws its 3D for 4:3 only, so the renderer narrows it and shows more of the world at the sides, and keeps the HUD in proportion. The game's own culling is still 4:3, so objects at the very edges can appear late.
- Xbox, PlayStation and Switch controllers.
- F10 shows the frame rate.

## Building

1. Clone this repository.
2. Put the game files in `assets` (`default.xbe` must be there, with the game's folders beside it).
3. Install Visual Studio 2022 with **Desktop development with C++**, **C++ Clang tools for Windows** and **C++ CMake tools for Windows**.
4. Run `build.bat`. The first build downloads the SDK ([maxscipio/XboxXBERecomp](https://github.com/maxscipio/XboxXBERecomp)) and the libraries it needs, recompiles the game and takes a while. Later builds are faster.

To build against a local SDK checkout, put it in `sdk` here, or in `..\XboxXBERecomp`.

See `docs\PORTING_NOTES.md` for how the game was brought up.
