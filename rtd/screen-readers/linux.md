# Screen readers on Linux

> **Current status:** Linux TTS integration is a stub. The `speak()` function logs text
> to the Python logger (`lights_off.speak`) at INFO level instead of calling a TTS engine.
> No speech is produced unless you configure a separate log consumer.

This page describes the current state and how to add Speech Dispatcher support yourself
while waiting for an official implementation.

## Current behaviour

`lights_off/speak.py` on Linux:

```python
import logging as _logging
_log = _logging.getLogger("lights_off.speak")
def speak(text, interrupt=False):
    _log.info("speak: %s", text)
```

## Manually adding Speech Dispatcher

[Speech Dispatcher](https://freebsoft.org/speechd) is the standard TTS middleware on
Linux. It is used by Orca (the GNOME screen reader), Emacspeak, and many other accessible
applications.

### 1. Install Speech Dispatcher

```
sudo apt install speech-dispatcher python3-speechd   # Debian/Ubuntu
sudo dnf install speech-dispatcher                    # Fedora
```

### 2. Install the Python binding

```
pip install speechd
```

### 3. Patch speak.py

Replace the Linux branch in `lights_off/speak.py`:

```python
else:
    import speechd as _speechd
    _client = _speechd.SSIPClient("lights-off")
    _client.set_output_module("espeak-ng")
    _client.set_language("en")

    def speak(text, interrupt=False):
        if interrupt:
            _client.cancel()
        _client.say(text)
```

### 4. Start Speech Dispatcher

```
speech-dispatcher
```

Or it may be started automatically by your desktop session.

## Orca

[Orca](https://gitlab.gnome.org/GNOME/orca) is the primary screen reader for the GNOME
desktop. It uses AT-SPI2 (Assistive Technology Service Provider Interface) to interact
with applications. wxPython on Linux exposes AT-SPI2 accessibility information, so Orca
can announce focused controls, but Lights Off's own `speak()` calls will not reach Orca
unless Speech Dispatcher is configured as described above.

## Contributing

If you get Speech Dispatcher working, please open a pull request to add it to the upstream
`speak.py`. The pattern is already established — it is a clean `else` branch with no
platform-specific dependencies at import time.
