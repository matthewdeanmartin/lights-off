# Component provenance

This page lists third-party components bundled with or required by Lights Off and their
respective licenses and origins.

## Bundled components

### Tolk.py

| Field | Value |
|---|---|
| File | `lights_off/Tolk.py` |
| Author | Davy Kager |
| License | LGPLv3 |
| Source | <https://github.com/dkager/tolk> |
| Purpose | Windows screen reader bridge (NVDA, JAWS, SAPI) |

Tolk is bundled directly as a Python file because the LGPLv3 licence is compatible with
the application's GPL-2.0-only licence under standard LGPL linking terms.

## Runtime dependencies

| Package | License | Purpose |
|---|---|---|
| wxPython | wxWindows Library Licence (GPL exception) | Cross-platform GUI framework |
| Mastodon.py | MIT | Mastodon API client |
| tweak | MIT | Per-application configuration storage |
| pyperclip | BSD-3-Clause | Clipboard access |
| sound_lib | MIT | Audio playback (Windows/macOS) |
| accessible_output2 | MIT | macOS screen reader output |
| keyboard_handler | MIT | Always-on hotkey registration |

## Forked from

Lights Off is a fork of [Quinter](https://github.com/QuinterApp/Quinter), a Twitter client
originally written by Quintin Storm and contributors. The original Quinter code was not
explicitly licensed at the time of the fork; the lights-off project has been re-released
under GPL-2.0-only with the fork history preserved in git.
