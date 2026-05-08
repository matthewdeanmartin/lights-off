# Installation overview

Lights Off is a Python application distributed on PyPI. The recommended install method is
`pipx`, which isolates it in its own virtual environment and puts the `lights-off` command
on your PATH.

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.12, 3.13, or 3.14 |
| Operating system | Windows 10/11 or macOS 12+ |
| Screen reader | NVDA, JAWS, or SAPI (Windows); VoiceOver (macOS); optional |

Linux is not fully supported — the GUI and audio layers depend on libraries that do not
have stable Linux packages. See [Linux](linux.md) for the current status.

## Install methods

| Method | Best for |
|---|---|
| `pipx install lights-off` | End users — isolated, no dependency conflicts |
| `pip install lights-off` | Developers or existing virtual environments |
| `uv tool install lights-off` | Users who already use `uv` |
| Clone + `uv sync` | Contributors |

See the platform-specific pages for exact steps:

- [Windows](windows.md)
- [macOS](macos.md)
- [Linux](linux.md)

## First-run note

On the first launch you will be asked for your Mastodon instance URL (e.g.
`https://mastodon.social`) and will complete a one-time OAuth browser flow to authorise
the application. Credentials are stored locally in your user config directory; no password
is ever stored in plain text.
