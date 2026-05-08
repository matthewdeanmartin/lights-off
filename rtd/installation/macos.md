# Installing on macOS

## Prerequisites

1. **Python 3.12 or newer.** The system Python shipped with macOS is often outdated.
   Install a current version via [python.org](https://www.python.org/downloads/macos/) or
   [Homebrew](https://brew.sh/):

   ```
   brew install python@3.13
   ```

2. **pipx** (recommended):

   ```
   brew install pipx
   pipx ensurepath
   ```

## Install lights-off

```
pipx install lights-off
```

## Launch

```
lights-off
```

Or add an alias in your shell profile if the `~/.local/bin` directory is not in your PATH.

## Apple Silicon (M1/M2/M3) notes

wxPython 4.2+ provides universal2 wheels for macOS. If you encounter an architecture
mismatch error, try:

```
pip install --upgrade wxpython
```

If `sound_lib` fails to install on Apple Silicon, check that Rosetta 2 is installed
(`softwareupdate --install-rosetta`) or install a native ARM build of the BASS audio
library.

## Screen readers on macOS

Lights Off uses the `accessible_output2` library to send speech through **VoiceOver**.
See [Screen Readers — macOS](../screen-readers/macos.md) for details.

## Building a macOS app bundle

Use the PyInstaller scripts in `scripts/`:

```
# Intel Mac
bash scripts/compile.command

# Apple Silicon
bash scripts/compileM1.command
```

The result is placed in `/Applications/Quinter.app` and a zip archive is created in the
repository root.

## Upgrading

```
pipx upgrade lights-off
```

## Uninstalling

```
pipx uninstall lights-off
```
