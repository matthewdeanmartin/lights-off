# What is Lights Off?

Lights Off is a desktop Mastodon client built specifically for users who rely on screen readers
or prefer a purely keyboard-driven interface. It is a fork of
[Quinter](https://github.com/QuinterApp/Quinter), which was originally a Twitter client, converted
to work with the Mastodon API.

## Design principles

**Keyboard-first.** Every timeline, action, and setting is reachable without a mouse.
Menus carry accelerators; the most common actions have single-chord shortcuts.

**Screen-reader-first.** On Windows the app talks directly to NVDA, JAWS, or SAPI through
Tolk. On macOS it uses `accessible_output2` to reach VoiceOver. All status text is spoken
as you move through the list; earcon sounds play when new posts arrive.

**Lightweight.** The UI is two list boxes — one for timelines, one for the posts in the
selected timeline. There is no WebView, no embedded browser, no images rendered inline.

## What it is not

Lights Off is not a general-purpose graphical Mastodon client. If you want image previews,
video thumbnails, an emoji picker, or a point-and-click interface, other clients will serve
you better. Lights Off trades visual richness for reliability with assistive technology.

## Technology

| Layer | Library |
|---|---|
| GUI | wxPython 4.2+ |
| Mastodon API | Mastodon.py 2.2+ |
| Screen reader (Windows) | Tolk (LGPLv3, Davy Kager) + SAPI |
| Screen reader (macOS) | accessible_output2 |
| Audio | sound_lib (BASS on Windows, CoreAudio on macOS) |
| Configuration | tweak |
