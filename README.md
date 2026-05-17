# lights-off

**lights-off** is a lightweight, keyboard-driven, accessible Mastodon client for Windows
and macOS, built with wxPython. It is a fork of
[Quinter](https://github.com/QuinterApp/Quinter), a Twitter client, converted for the
Mastodon network.

Every action is reachable by keyboard shortcut. All content is routed through the platform
screen reader (NVDA/JAWS/SAPI on Windows, VoiceOver on macOS) so blind and low-vision
users can browse, post, and manage their account without touching the mouse.

## Install

```
pipx install lights-off
```

Requires Python 3.12+. See the [installation docs](https://lights-off.readthedocs.io/en/latest/) for platform-specific steps.

## Run

```
lights-off
```

On first launch you will be prompted for your Mastodon instance URL (e.g.
`https://mastodon.social`) and will complete a one-time OAuth browser flow.

## Documentation

Full documentation is at <https://lights-off.readthedocs.io/>.

- [Installation](https://lights-off.readthedocs.io/installation/overview/)
- [Screen reader setup](https://lights-off.readthedocs.io/screen-readers/overview/)
- [Keyboard reference](https://lights-off.readthedocs.io/getting-started/keyboard-reference/)
- [Troubleshooting](https://lights-off.readthedocs.io/reference/troubleshooting/)

## Development

```bash
git clone https://github.com/matthewdeanmartin/lights-off
cd lights-off
uv sync
uv run lights-off
```

Run tests across all supported Python versions:

```
tox
```

## Contributing

Pull requests welcome. For large feature additions, open an issue first.

## Licenses

- Quinter - no declared license, per Mastodon conversation with Quinn, forking and MIT is okay.
- SAAPI65.dll - (C) All rights reserved
- nvdaControllerClient64.dll LGPL
- GPL-2.0-only. `Tolk.py` is LGPLv3 (copyright Davy Kager).
- .ogg soundfiles - unknown license
- keyboard_handler - vendorized, MIT, copyright Christopher Toth
