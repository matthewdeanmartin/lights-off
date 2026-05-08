# Installing on Linux

> **Status: experimental.** The core Mastodon logic works on Linux, but two subsystems
> have limited support:
>
> - **Audio** (`sound_lib`) depends on the BASS audio library, which does not have an
>   official Linux build. Sound effects will not play.
> - **Screen reader integration** uses a stub that logs speech to the Python logger instead
>   of calling a real TTS engine. Spoken output requires additional setup (see below).

If you are a developer or an adventurous user, the following steps will get the application
running without audio or native TTS.

## Prerequisites

```
sudo apt install python3.12 python3.12-venv python3-wxgtk4.0
```

Or install Python via [pyenv](https://github.com/pyenv/pyenv) if your distribution ships
an older version.

## Install

```
python3.12 -m pip install --user pipx
python3.12 -m pipx ensurepath
pipx install lights-off --system-site-packages
```

The `--system-site-packages` flag is needed so that `pipx`'s environment can see the
system-installed wxPython package, which is large and difficult to build from source.

## Launch

```
lights-off
```

Expect no sound effects and no spoken output unless you wire up Speech Dispatcher manually
(see [Screen Readers — Linux](../screen-readers/linux.md)).

## Known issues on Linux

| Issue | Cause | Workaround |
|---|---|---|
| No sound effects | `sound_lib` not available | None currently |
| No spoken output | No TTS backend | See Speech Dispatcher notes |
| wxPython build failures | C extensions need GTK dev headers | Use system wxPython package |
