# Screen readers on macOS

## How it works

On macOS, Lights Off uses the **`accessible_output2`** Python library to send speech to
VoiceOver. The library is installed automatically as a dependency on macOS:

```
accessible_output2>=0.17; sys_platform == 'darwin'
```

At module load time `lights_off/speak.py` does:

```python
from accessible_output2 import outputs
_speaker = outputs.auto.Auto()
```

`Auto()` selects the best available output driver. On a standard macOS system this routes
through **AppKit's `NSSpeechSynthesizer`**, which feeds into VoiceOver's speech channel.

## VoiceOver

VoiceOver is Apple's built-in screen reader. Enable it with **Command + F5** or via
System Settings → Accessibility → VoiceOver.

Lights Off does not require VoiceOver to be running. When VoiceOver is off, speech is still
delivered through the macOS TTS engine (the same voices used by VoiceOver), so you will
hear content even with VoiceOver disabled.

## Changing the speech voice

The voice used by Lights Off is the **System Voice** configured in:
System Settings → Accessibility → Spoken Content → System Voice.

Changing it there also changes what you hear in Lights Off.

## Apple Silicon notes

`accessible_output2` is a pure-Python wrapper around macOS system APIs and works natively
on Apple Silicon. No Rosetta 2 is required for TTS.

## Supported output backends

`accessible_output2` supports several output drivers. On macOS the driver used is
`outputs.osx_sapi.OSXSAPI` (wraps `NSSpeechSynthesizer`) or
`outputs.auto.Auto` (auto-detects). You can check which driver is active:

```python
from accessible_output2 import outputs
driver = outputs.auto.Auto()
print(driver.__class__.__name__)
```

## Troubleshooting

**No speech on macOS.**
1. Open System Settings → Accessibility → Spoken Content and verify the System Voice is
   set and works with the **Speak** button.
2. Ensure `accessible_output2` is installed: `pip show accessible_output2`.
3. If running in a terminal, check that the app has Accessibility permissions in
   System Settings → Privacy & Security → Accessibility.

**VoiceOver and Lights Off speaking at the same time.**
VoiceOver will also narrate focus changes in the wxPython window. This is normal. If it
is distracting, you can silence VoiceOver with **Control** while Lights Off speaks
through the TTS engine independently.
