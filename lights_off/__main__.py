"""Entry point for the lights-off Mastodon client.

Run with: ``python -m lights_off``
"""

import logging
import os
import platform
import shutil
import sys

# ---------------------------------------------------------------------------
# Logging — stdlib, to stdout, on by default.
# ---------------------------------------------------------------------------

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s %(levelname)s %(name)s %(message)s",
	stream=sys.stdout,
)

log = logging.getLogger("lights_off")
log.info("starting lights-off")


# ---------------------------------------------------------------------------
# Optional legacy macOS stderr-to-file redirection. Off by default.
# Set LIGHTS_OFF_REDIRECT_STDERR=1 to enable the old behaviour.
# ---------------------------------------------------------------------------

if os.environ.get("LIGHTS_OFF_REDIRECT_STDERR") == "1" and platform.system() != "Darwin":
	try:
		sys.stderr = open("errors.log", "a")
		log.info("stderr redirected to errors.log (legacy mode)")
	except Exception as e:
		log.warning("could not redirect stderr: %s", e)


# ---------------------------------------------------------------------------
# Boot.
# ---------------------------------------------------------------------------

sys.dont_write_bytecode = True

if platform.system() == "Windows":
	import tempfile
	gen_py = os.path.join(tempfile.gettempdir(), "gen_py")
	if os.path.exists(gen_py):
		try:
			shutil.rmtree(gen_py)
		except Exception:
			pass

def main():
	import wx

	app = wx.App(redirect=False)

	import lights_off.speak as speak
	from lights_off.GUI import main as main_gui
	import lights_off.globals as globals_mod

	globals_mod.load()

	if globals_mod.prefs.window_shown:
		main_gui.window.Show()
	else:
		speak.speak("Welcome to lights-off! Main window hidden.")

	import lights_off.utils  # noqa: F401  (side-effects: registers handlers)

	app.MainLoop()


if __name__ == "__main__":
	main()
