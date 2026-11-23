#include "app/app.h"
#include "common/overlay.h"

static void OnUi(double fps) { overlay::Ui(fps); }

// The game draws its 3D for 4:3 only, whatever the shown aspect, so the renderer narrows it (g_widen_3d) and the stretch
// to the picture widens it back. g_wide_2d has the renderer stretch the targets and keep the 2D (laid out for 4:3) in a
// centred part: 4:3 in a 16:9 picture, 16:9 in a wider one. "Fill the screen" is ultrawide: the picture is 21:9, with
// bars above and below on a screen that is narrower (16:9), and fills a screen that is 21:9 or wider.
static void OnInit() {
    app::g_widen_3d = true;
    constexpr float kUltrawide = 21.0f / 9.0f;
    const app::Settings& s = app::Get();
    if (s.console_look || s.aspect == 1) return;
    if (s.aspect == 3) {
        app::Mode out = app::CachedOutput();
        if (!out.height || float(out.width) / float(out.height) < kUltrawide) {
            app::g_aspect = kUltrawide;
            app::g_wide_2d = true;
        }
    } else if (app::Widescreen()) {
        app::g_aspect = 16.0f / 9.0f;
        app::g_wide_2d = true;
    }
}

// what the runtime asks of the game; strings must be set, hooks may stay null
const app::GameInfo app::kGame = {
    .title = L"Gun Valkyrie",             // window and splash
    .short_title = L"Gun Valkyrie",       // message boxes
    .name = L"GunValkyrie",               // window classes, crash dumps, handover event
    .log = "gunvalkyrie",                 // log file prefix
    .settings = "settings.toml",          // settings file beside the exe
    .splash = L"splash",                  // optional splash.png or splash.bmp beside the exe
    .missing = L"Put the game in the assets folder: its disc image (.iso), or default.xbe with its folders beside it.",
    .images = {{"default.xbe", "GunValkyrie"}},  // each recompiled xbe and its exe, for title launches
    .options = {{"show_fps", &overlay::show_fps, nullptr, "Show frame rate", "Also F10."}},
    .init = OnInit,                       // after the settings load, before the window and boot
    .ui = OnUi,                           // ImGui drawing each frame: the FPS counter (F10)
    .settings_window = true,              // F1: the SDK's settings window
};
