"""Logging helper for Mastodon API calls.

Wraps the private ``_Mastodon__api_request`` method on a Mastodon instance so
every HTTP call goes through a stdlib ``logging`` shim. The root logger config
is set up by ``lights_off.__main__`` (or by tests).
"""

import logging
import time
from functools import wraps

log = logging.getLogger("lights_off.api")


def instrument(api, label=""):
	"""Wrap a mastodon.Mastodon instance so every API call is logged."""
	attr = "_Mastodon__api_request"
	original = getattr(api, attr, None)
	if original is None:
		log.warning("instrument: %s missing on %r", attr, api)
		return api
	if getattr(original, "_lights_off_wrapped", False):
		return api

	prefix = ("[" + label + "] ") if label else ""

	@wraps(original)
	def logged(method, endpoint, *args, **kwargs):
		start = time.monotonic()
		log.info("%s%s %s", prefix, method, endpoint)
		try:
			result = original(method, endpoint, *args, **kwargs)
		except Exception as e:
			ms = int((time.monotonic() - start) * 1000)
			log.error(
				"%s%s %s failed in %dms: %s: %s",
				prefix, method, endpoint, ms, type(e).__name__, e,
			)
			raise
		ms = int((time.monotonic() - start) * 1000)
		size = ""
		try:
			if isinstance(result, list):
				size = " (%d items)" % len(result)
			elif isinstance(result, dict) and "statuses" in result:
				size = " (%d statuses)" % len(result["statuses"])
		except Exception:
			pass
		log.info("%s%s %s ok in %dms%s", prefix, method, endpoint, ms, size)
		return result

	logged._lights_off_wrapped = True
	setattr(api, attr, logged)
	return api
