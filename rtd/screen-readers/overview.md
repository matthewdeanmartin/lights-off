# Screen reader support overview

Lights Off routes all spoken output through the platform's assistive technology stack. The
mechanism is different on each OS:

| Platform | Library | Backends supported |
|---|---|---|
| Windows | Tolk (LGPLv3, Davy Kager) | NVDA, JAWS, SAPI 5 |
| macOS | accessible_output2 | VoiceOver (via AppKit speech) |
| Linux | Python `logging` (stub) | None yet — see [Linux](linux.md) |

The `speak(text, interrupt=False)` function in `lights_off/speak.py` is the single call
site for all speech output. When `interrupt=True` the current utterance is cut off and the
new text begins immediately — used for rapid navigation.

## Choosing a screen reader on Windows

Lights Off prefers **SAPI** over NVDA/JAWS by default (set via `Tolk.prefer_sapi(True)`).
This means you hear speech through whatever SAPI voice is configured in Windows, even if
NVDA or JAWS is also running. If you prefer NVDA or JAWS output, see
[Windows screen reader settings](windows.md#choosing-your-screen-reader).

## Platform-specific pages

- [Windows (NVDA / JAWS / SAPI)](windows.md)
- [macOS (VoiceOver)](macos.md)
- [Linux (Speech Dispatcher)](linux.md)
