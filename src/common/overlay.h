#pragma once

// FPS counter (F10); everything else is in the SDK's settings window (F1)
namespace overlay {

extern bool show_fps;  // persisted in the settings file

void Ui(double fps);  // inside the ImGui frame

}  // namespace overlay
