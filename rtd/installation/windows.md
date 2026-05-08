# Installing on Windows

## Prerequisites

1. **Python 3.12 or newer.** Download from <https://www.python.org/downloads/windows/>.
   During installation, tick **"Add Python to PATH"**.

2. **pipx** (recommended). After Python is installed, open a Command Prompt or PowerShell
   window and run:

   ```
   python -m pip install --user pipx
   python -m pipx ensurepath
   ```

   Close and reopen your terminal so the new PATH takes effect.

## Install lights-off

```
pipx install lights-off
```

That is all. pipx creates an isolated environment and adds the `lights-off` command to your
PATH automatically.

## Launch

```
lights-off
```

Or search for **lights-off** in the Start menu if your `%LOCALAPPDATA%\Programs\Python\...`
Scripts folder is in PATH.

## Screen readers on Windows

Lights Off uses **Tolk**, a Windows-native library that can talk to NVDA, JAWS, or fall
back to SAPI. See [Screen Readers — Windows](../screen-readers/windows.md) for details and
troubleshooting.

## Upgrading

```
pipx upgrade lights-off
```

## Uninstalling

```
pipx uninstall lights-off
```

## Building a standalone executable

If you want a single `.exe` that does not require Python to be installed, see
`scripts/build.bat` in the repository. It uses [Nuitka](https://nuitka.net/) to compile
the application:

```batch
pip install nuitka
scripts\build.bat
```

The output lands in `c:\tempbuild\quinter.dist\`. Run `scripts\copy.bat` to assemble the
final distribution folder.

> **Note:** The Nuitka build is optional. Most users should just use `pipx`.
