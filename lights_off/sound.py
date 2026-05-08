import os
import sound_lib
from sound_lib import stream
from sound_lib import output as o
from lights_off import globals
import re

out = o.Output()
handle = None

def return_url(url):
	return url

media_matchlist = [
	{"match": r"https://sndup.net/[a-zA-Z0-9]+/[ad]$", "func":return_url},
	{"match": r"^http:\/\/\S+(\/\S+)*(\/)?\.(mp3|m4a|ogg|opus|flac)$", "func":return_url},
	{"match": r"^https:\/\/\S+(\/\S+)*(\/)?\.(mp3|m4a|ogg|opus|flac)$", "func":return_url},
	{"match": r"^http:\/\/\S+:[+-]?[1-9]\d*|0(\/\S+)*(\/)?$", "func":return_url},
	{"match": r"^https:\/\/\S+:[+-]?[1-9]\d*|0(\/\S+)*(\/)?$", "func":return_url},
	{"match": r"https?://twitch.tv/.", "func":return_url},
	{"match": r"http?://twitch.tv/.", "func":return_url},
	{"match": r"https?://vm.tiktok.com/.+", "func":return_url},
	{"match": r"https?://soundcloud.com/.+", "func":return_url},
	{"match": r"https?://t.co/.", "func":return_url},
	{"match": r"^(?:https?:\/\/)?(?:m\.|www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))((\w|-){11})(?:\S+)?$", "func":return_url}
]

def get_media_urls(urls):
	result = []
	for u in urls:
		for service in media_matchlist:
			if re.match(service['match'], u.lower()) is not None:
				result.append({"url":u, "func":service['func']})
	return result

def _bundled_sound_path(filename):
	"""Return an os.fspath-compatible path to a bundled sound file, or None."""
	from importlib.resources import files
	candidate = files("lights_off").joinpath(f"sounds/default/{filename}.ogg")
	try:
		# as_file() context manager extracts if needed (zip installs); for
		# directory installs it just returns the real path without extraction.
		from importlib.resources import as_file
		with as_file(candidate) as p:
			if p.exists():
				return str(p)
	except Exception:
		pass
	return None


def play(account, filename, pack="", wait=False):
	global handle
	if handle is not None:
		try:
			handle.stop()
		except sound_lib.main.BassError:
			pass
		try:
			handle.free()
		except sound_lib.main.BassError:
			pass
	# 1. User soundpack in config dir
	if os.path.exists(globals.confpath + "/sounds/" + account.prefs.soundpack + "/" + filename + ".ogg"):
		path = globals.confpath + "/sounds/" + account.prefs.soundpack + "/" + filename + ".ogg"
	# 2. Default sounds copied to config dir at startup
	elif os.path.exists(globals.confpath + "/sounds/default/" + filename + ".ogg"):
		path = globals.confpath + "/sounds/default/" + filename + ".ogg"
	# 3. Bundled sounds inside the installed package (importlib.resources)
	else:
		path = _bundled_sound_path(filename)
		if path is None:
			return
	try:
		handle = stream.FileStream(file=path)
		handle.pan=account.prefs.soundpan
		handle.volume = globals.prefs.volume
		handle.looping = False
		if wait:
			handle.play_blocking()
		else:
			handle.play()
	except sound_lib.main.BassError:
		pass
