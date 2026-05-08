# Troubleshooting

## Installation problems

### `wxpython` fails to install

wxPython ships pre-built wheels for common platforms. If pip tries to compile from source
it will likely fail. Make sure you are running a supported Python version (3.12–3.14) and
a supported OS (Windows 10/11, macOS 12+).

On Linux, install the system wxPython package instead of the PyPI one:
```
sudo apt install python3-wxgtk4.0
```
Then use `--system-site-packages` when creating the virtual environment.

### `sound_lib` fails to install on Apple Silicon

`sound_lib` requires the BASS audio library. Try updating to the latest version:
```
pip install --upgrade sound_lib
```
If it still fails, the app will run without sound effects — only TTS speech will work.

### `keyboard_handler` not found

`keyboard_handler` is not on PyPI. Install it from source:
```
pip install git+https://github.com/accessibleapps/keyboard_handler
```

---

## Authentication problems

### Browser does not open for OAuth

Lights Off calls `webbrowser.open()` to start the OAuth flow. If no browser opens, copy
the URL printed to the terminal and paste it into your browser manually, then copy the
authorisation code back.

### "Invalid redirect URI" or "Application not registered"

Delete the `client_secrets.secret` file for the instance from your config directory and
restart Lights Off. The app will re-register itself.

### Access token rejected

Your access token may have been revoked. Go to your instance's web interface →
Settings → Applications and revoke the `lights-off` entry, then restart the app and
re-authorise.

---

## Screen reader problems

### No speech on Windows

1. Verify that a SAPI voice is configured in Windows Settings → Accessibility → Narrator.
2. Ensure the Tolk DLLs are present inside the `lights_off/` package directory. Reinstall
   if missing: `pipx reinstall lights-off`.
3. If using NVDA, try starting NVDA before launching Lights Off.

### Speech is heard in SAPI but not in NVDA

Lights Off defaults to SAPI. To switch to NVDA output, change `Tolk.prefer_sapi(False)`
in `lights_off/speak.py` and restart.

### No speech on macOS

1. Check System Settings → Accessibility → Spoken Content and confirm a voice is selected.
2. Make sure `accessible_output2` is installed: `pip show accessible_output2`.
3. Grant accessibility permissions: System Settings → Privacy & Security → Accessibility →
   add your terminal or the `lights-off` binary.

---

## Runtime errors

### `errors.log` file

When launched normally, stderr is captured to `errors.log` in the working directory
(configurable via the `LIGHTS_OFF_LOG_STDERR` environment variable). Check this file for
Python tracebacks.

### Viewing API errors in-app

Use **Help → View API errors** (or check `globals.errors` in the application state) to see
the last Mastodon API errors without leaving the app.

### Timeline not updating

Press **F5** to force a refresh. If the timeline still does not update, check your network
connection and verify that your Mastodon instance is reachable. The background polling
thread runs every 60 seconds; check `errors.log` for threading exceptions.

---

## Reporting bugs

Open an issue at <https://github.com/matthewdeanmartin/lights-off/issues>.
Include:

- OS and Python version
- Lights Off version (`pip show lights-off`)
- Steps to reproduce
- Relevant content from `errors.log`
