#include "common/overlay.h"

#include <algorithm>
#include <cfloat>
#include <cstdio>

#include <imgui.h>

#include "app/app.h"

namespace overlay {

bool show_fps = false;

namespace {

float Scale() { return std::clamp(ImGui::GetIO().DisplaySize.y / 720.0f, 1.0f, 3.0f); }

void ShowFps(double fps) {
    char text[32];
    std::snprintf(text, sizeof text, "%.0f FPS", fps);
    ImDrawList* dl = ImGui::GetForegroundDrawList();
    ImFont* font = ImGui::GetFont();
    float size = ImGui::GetFontSize() * Scale() * 1.3f;
    ImVec2 extent = font->CalcTextSizeA(size, FLT_MAX, 0, text);
    ImVec2 pos(ImGui::GetIO().DisplaySize.x - extent.x - 16 * Scale(), 10 * Scale());
    dl->AddText(font, size, ImVec2(pos.x + 1.5f, pos.y + 1.5f), IM_COL32(0, 0, 0, 220), text);
    dl->AddText(font, size, pos, IM_COL32(120, 255, 120, 240), text);
}

}  // namespace

void Ui(double fps) {
    if (ImGui::IsKeyPressed(ImGuiKey_F10, false)) {
        show_fps = !show_fps;
        app::Save();
    }
    if (show_fps) ShowFps(fps);
}

}  // namespace overlay
