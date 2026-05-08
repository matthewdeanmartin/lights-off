import platform
import sys

_system = platform.system()

if _system == "Darwin":
	from accessible_output2 import outputs
	_speaker = outputs.auto.Auto()
	def speak(text, interrupt=False):
		_speaker.speak(text, interrupt)

elif _system == "Windows":
	from lights_off import Tolk as _tolk
	_tolk.load()
	_tolk.try_sapi = True
	def speak(text, interrupt=False):
		_tolk.output(text, interrupt)

else:
	# Linux: no screen reader integration yet.
	# speech-dispatcher support can be added here when needed.
	import logging as _logging
	_log = _logging.getLogger("lights_off.speak")
	def speak(text, interrupt=False):
		_log.info("speak: %s", text)
