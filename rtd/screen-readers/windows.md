# Screen readers on Windows

## How it works

Lights Off uses **Tolk**, an open-source Windows library (LGPLv3, by Davy Kager) that
provides a unified API over NVDA, JAWS, and the Windows built-in SAPI 5 speech engine.

At startup the application calls:

```python
Tolk.try_sapi(True)    # enable SAPI as a fallback
Tolk.prefer_sapi(True) # prefer SAPI over screen readers
Tolk.load()
```

This means speech is delivered through the **SAPI 5 voice** configured in Windows Settings
→ Accessibility → Narrator → Voice (or Control Panel → Speech Recognition → Text to
Speech on older systems), even if NVDA or JAWS is running.

## Choosing your screen reader

If you prefer to receive output through **NVDA** or **JAWS** instead of SAPI, you can
change the preference by editing `globals.py` or — once a settings UI is added — through
the Options dialog. The relevant Tolk calls are:

| Preference | Call |
|---|---|
| Use SAPI (default) | `Tolk.prefer_sapi(True)` |
| Use NVDA / JAWS if running | `Tolk.prefer_sapi(False)` |

## Supported screen readers

| Screen reader | Supported | Notes |
|---|---|---|
| NVDA | Yes | Tolk uses the NVDA Controller Client DLL |
| JAWS | Yes | Tolk uses the JAWS COM interface |
| SAPI 5 | Yes | Always available; used as fallback |
| Narrator | Partial | Not directly targeted; SAPI output is heard through Narrator if SAPI is set as Narrator's voice source |

## Installing NVDA

NVDA is free, open-source, and widely used. Download it from
<https://www.nvaccess.org/download/>.

## SAPI voices

Windows ships with a small set of SAPI voices. Additional voices can be installed from
Settings → Time & Language → Speech (Windows 11) or from third-party vendors. The quality
of speech you hear in Lights Off depends entirely on which SAPI voice is active.

## Troubleshooting

**No speech at all.**
Check that a SAPI voice is installed and configured in Windows Settings. Open Narrator's
settings and verify that the selected voice works there first.

**Speech is choppy or cuts out.**
This can happen if the SAPI engine is slow. Try switching to a different SAPI voice, or
set `prefer_sapi(False)` to use NVDA or JAWS directly if one is running.

**Tolk DLL not found.**
Tolk ships as `Tolk.py` plus compiled DLLs in the `lights_off/` package. If you see a
`ctypes` error about a missing DLL, reinstall the package:
```
pipx reinstall lights-off
```
