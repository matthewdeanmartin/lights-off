import html
from html.parser import HTMLParser
import logging
import platform
import json
import datetime
import time
import re
from lights_off import globals
from lights_off import speak
import wx
import requests
import webbrowser
from lights_off import application
from lights_off import sound
import os

url_re=re.compile(r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?]))")
url_re2=re.compile(r"(?:\w+://|www\.)[^ ,.?!#%=+][^ ]*")
bad_chars="'\\.,[](){}:;\""


class _HTMLStripper(HTMLParser):
	def __init__(self):
		super().__init__()
		self.parts=[]
		self._in_anchor=False
		self._anchor_text=[]
		self._anchor_href=""

	def handle_starttag(self,tag,attrs):
		if tag=="a":
			self._in_anchor=True
			self._anchor_text=[]
			self._anchor_href=dict(attrs).get("href","")

	def handle_endtag(self,tag):
		if tag=="a" and self._in_anchor:
			text="".join(self._anchor_text).strip()
			href=self._anchor_href
			# Mastodon wraps bare URLs in anchors whose visible text is the
			# shortened URL (e.g. "github.com/foo/ba…"). Use that instead of
			# the raw href, unless the anchor text itself looks like a full URL.
			if href and (href.startswith("http://") or href.startswith("https://")):
				if text and not (text.startswith("http://") or text.startswith("https://")):
					self.parts.append(text)
				else:
					# fall back to domain only
					from urllib.parse import urlparse
					self.parts.append(urlparse(href).netloc or text)
			else:
				self.parts.append(text)
			self._in_anchor=False

	def handle_data(self,data):
		if self._in_anchor:
			self._anchor_text.append(data)
		else:
			self.parts.append(data)

	def get_text(self):
		return "".join(self.parts)


def strip_html(raw):
	s=_HTMLStripper()
	s.feed(raw)
	return s.get_text()


def shorten_acct(acct):
	"""Return just the local username part, dropping @instance."""
	if acct and "@" in acct:
		return acct.split("@")[0]
	return acct


def process_tweet(s, return_only_text=False, template=""):
	"""Convert a Mastodon status object to display text."""
	if s is None:
		return ""
	# Mastodon content is HTML
	raw=getattr(s,"content","") or ""
	text=strip_html(html.unescape(raw))

	if s.reblog:
		text=process_tweet(s.reblog, False, globals.prefs.retweetTemplate)

	s.content=text
	if not return_only_text:
		return template_to_string(s,template)
	else:
		return text


def process_message(s, return_text=False):
	"""Render a Mastodon conversation's last_status as a DM-style string."""
	# s may be a conversation dict (has 'last_status') or a bare status
	if hasattr(s, "last_status") and s.last_status is not None:
		status = s.last_status
	else:
		status = s
	if status is None:
		return ""
	raw = getattr(status, "content", "") or ""
	text = strip_html(html.unescape(raw))
	sender = getattr(getattr(status, "account", None), "acct", "unknown")
	return sender + ": " + text

def find_urls_in_text(text):
	return [s.strip(bad_chars) for s in url_re2.findall(text)]

def find_urls_in_tweet(s):
	urls=[]
	if hasattr(s,"content") and s.content:
		urls+=find_urls_in_text(s.content)
	if hasattr(s,"media_attachments") and s.media_attachments:
		for m in s.media_attachments:
			if m.url:
				urls.append(m.url)
	return urls

def template_to_string(s, template="", _shorten_acct=True):
	if template=="":
		template=globals.prefs.tweetTemplate
	temp=template.split(" ")
	for i in range(len(temp)):
		if "$" in temp[i]:
			t=temp[i].split("$")
			r=t[1]
			if "." in r:
				q=r.split(".")
				o=q[0]
				p=q[1]
				if hasattr(s,o) and hasattr(getattr(s,o),p):
					try:
						f1=getattr(s,o)
						val=getattr(f1,p)
						if globals.prefs.demojify and ("name" in (o,p)):
							val=strip_display_name(str(val), getattr(f1,"acct",""))
						if _shorten_acct and p=="acct":
							val=shorten_acct(str(val))
						template=template.replace("$"+t[1]+"$",str(val))
					except Exception as e:
						print(e)
			else:
				if hasattr(s,t[1]):
					try:
						val=getattr(s,t[1])
						if t[1]=="display_name" and globals.prefs.demojify:
							val=strip_display_name(str(val), getattr(s,"acct",""))
						if t[1]=="content" and globals.prefs.demojify_tweet:
							val=demojify(str(val))
						if t[1]=="created_at":
							val=parse_date(val)
						if _shorten_acct and t[1]=="acct":
							val=shorten_acct(str(val))
						template=template.replace("$"+t[1]+"$",str(val))
					except Exception as e:
						print(e)
	return template


def message_template_to_string(s):
	return ""

def get_users_in_tweet(account, s):
	new=""
	if s.reblog and s.reblog.account.id!=account.me.id:
		s.content=s.content+" "+s.reblog.account.acct
	if s.account.acct!=account.me.acct:
		new=s.account.acct
	mentions=getattr(s,"mentions",[]) or []
	for m in mentions:
		if m.acct!=account.me.acct:
			new+=" "+m.acct
	return new

def dict_match(d1, d2):
	for i in d2:
		if i not in d1:
			d1[i]=d2[i]
	return d1

def class_match(d1, d2):
	names1=[p for p in dir(d1) if isinstance(getattr(d1,p),property)]
	names2=[p for p in dir(d2) if isinstance(getattr(d2,p),property)]
	for i in names2:
		if i not in names1:
			setattr(d1,i,getattr(d2,i,None))
	return d1

def parse_date(date,convert=True):
	ti=datetime.datetime.now()
	dst=time.localtime().tm_isdst
	if dst==1:
		tz=time.altzone
	else:
		tz=time.timezone
	if convert:
		try:
			date+=datetime.timedelta(seconds=0-tz)
		except Exception:
			pass
	returnstring=""

	try:
		dateFormatString = "%m/%d/%Y"
		timeFormatString = "%I:%M:%S %p"
		if globals.prefs.use24HourTime:
			timeFormatString = "%H:%M:%S"
		#include the date if the date to be output happened before today, else just use the time
		if date.year==ti.year:
			if date.day==ti.day and date.month==ti.month:
				returnstring=""
			else:
				returnstring=date.strftime(f"{dateFormatString}, ")
		else:
			returnstring=date.strftime(f"{dateFormatString}, ")

		returnstring+=date.strftime(timeFormatString)
	except Exception:
		pass
	return returnstring

def isDuplicate(status, statuses):
	for i in statuses:
		if str(i.id)==str(status.id):
			return True
	return False


def _nget(obj, key, default=None):
	"""Read a field from either an object (attr) or a plain dict (key)."""
	if obj is None:
		return default
	if isinstance(obj, dict):
		return obj.get(key, default)
	return getattr(obj, key, default)


def notification_to_status(n):
	"""Convert a Mastodon notification into a status-like object for display.

	Mention/status/update/poll notifications carry a real status; we annotate
	it with a one-line prefix. Follow / favourite / reblog notifications have
	no status text (or refer to our own post), so we synthesize a stub.
	"""
	if n is None:
		return None
	ntype=_nget(n,"type","") or ""
	src=_nget(n,"status",None)
	actor=_nget(n,"account",None)
	actor_acct=_nget(actor,"acct","") if actor is not None else ""
	actor_label="@"+actor_acct if actor_acct else "someone"
	prefix={
		"mention": actor_label+" mentioned you: ",
		"status": actor_label+" posted: ",
		"update": actor_label+" edited a post: ",
		"poll": "Poll ended: ",
		"favourite": actor_label+" favourited your post",
		"reblog": actor_label+" boosted your post",
		"follow": actor_label+" followed you",
		"follow_request": actor_label+" requested to follow you",
	}.get(ntype, actor_label+" "+ntype)

	notif_id=_nget(n,"id","0")

	if src is not None and not isinstance(src, dict):
		# Real Mastodon status object: annotate content in-place.
		raw=getattr(src,"content","") or ""
		sep=" — " if raw else ""
		src.content="<p>"+prefix+sep+"</p>"+raw
		src.id=notif_id
		return src

	# Either no backing status, or src is a raw dict (streaming). Build a stub.
	src_content=_nget(src,"content","") if src is not None else ""
	src_account=_nget(src,"account",actor) if src is not None else actor
	if isinstance(src_account, dict):
		src_account=dict2obj(src_account)
	sep=" — " if src_content else ""
	stub=dict_obj({
		"id": notif_id,
		"content": "<p>"+prefix+sep+"</p>"+(src_content or ""),
		"account": src_account,
		"reblog": None,
		"in_reply_to_id": _nget(src,"in_reply_to_id",None) if src is not None else None,
		"spoiler_text": _nget(src,"spoiler_text","") if src is not None else "",
		"media_attachments": _nget(src,"media_attachments",[]) if src is not None else [],
		"favourites_count": _nget(src,"favourites_count",0) if src is not None else 0,
		"reblogs_count": _nget(src,"reblogs_count",0) if src is not None else 0,
		"favourited": _nget(src,"favourited",False) if src is not None else False,
		"reblogged": _nget(src,"reblogged",False) if src is not None else False,
		"created_at": _nget(n,"created_at",None),
		"url": _nget(src,"url","") if src is not None else "",
		"visibility": _nget(src,"visibility","public") if src is not None else "public",
	})
	return stub


class dict_obj:
	def __init__(self, dict1):
		self.__dict__.update(dict1)

def dict2obj(dict1):
	return json.loads(json.dumps(dict1), object_hook=dict_obj)


def ensure_attr_access(item):
	"""Promote a plain dict response into an attribute-access object.

	Mastodon.py normally returns ``AttribAccessDict`` subclasses where attr
	access works, but some response paths fall back to plain dicts. The rest
	of the codebase assumes ``status.account`` works, so anything that's a
	bare dict is converted via ``dict2obj`` before flowing downstream.
	"""
	if item is None:
		return item
	# AttribAccessDict subclasses dict but supports attribute access via
	# __getattr__ — leave them alone.
	if hasattr(type(item), "__getattr__"):
		return item
	if isinstance(item, dict):
		try:
			return dict2obj(item)
		except Exception:
			return item
	return item

def add_users(status):
	def _add(account_obj):
		if account_obj is None:
			return
		if isinstance(account_obj, dict) and not hasattr(type(account_obj),"__getattr__"):
			account_obj=dict2obj(account_obj)
		# Remove any existing entry with the same id to avoid duplicates
		try:
			uid=str(account_obj.id)
			globals.users=[u for u in globals.users if str(u.id)!=uid]
		except (AttributeError, TypeError):
			pass
		globals.users.insert(0,account_obj)

	if status is None:
		return
	# conversation objects have an 'accounts' list instead of a single 'account'
	accounts_list=_nget(status,"accounts")
	if accounts_list is not None:
		for a in accounts_list:
			_add(a)
		last=_nget(status,"last_status")
		if last is not None:
			_add(_nget(last,"account"))
		return
	_add(_nget(status,"account"))
	reblog=_nget(status,"reblog")
	if reblog is not None:
		_add(_nget(reblog,"account"))

def lookup_user(id):
	for i in globals.users:
		try:
			if int(i.id)==int(id):
				return i
		except (ValueError, TypeError):
			pass
	globals.unknown_users.append(id)
	return None

def lookup_user_name(account, name, use_api=True):
	name_clean=name.lower().lstrip("@")
	for i in globals.users:
		if getattr(i,"acct","").lower()==name_clean:
			return i
	if not use_api:
		return -1
	try:
		results=account.api.account_search(name_clean, limit=1)
		if results:
			user=results[0]
			try:
				globals.users.remove(user)
			except ValueError:
				pass
			globals.users.insert(0,user)
			return user
	except Exception:
		pass
	return -1

def get_user_objects_in_tweet(account, status, exclude_self=False, exclude_orig=False):
	users=[]
	if not exclude_orig and status.account not in users:
		users.append(status.account)
	if status.reblog and status.reblog.account not in users:
		users.append(status.reblog.account)
	mentions=getattr(status,"mentions",[]) or []
	for m in mentions:
		if exclude_self and m.acct==account.me.acct:
			continue
		un=lookup_user_name(account,m.acct)
		if un!=-1 and un not in users:
			users.append(un)
	if exclude_self:
		users=[u for u in users if u.id!=account.me.id]
	return users

def speak_user(account, users):
	text=""
	for i in users:
		user=lookup_user_name(account,i)
		if user is not None and user!=-1:
			text+=". "+template_to_string(user,globals.prefs.userTemplate,_shorten_acct=False)
		text=text.rstrip(".")
	text=text.lstrip(".")
	speak.speak(str(len(users))+" users: "+text)

def lookup_status(account,id):
	for i in account.timelines:
		for i2 in i.statuses:
			if i2.id==id:
				return i2
	return account.api.status(id)

def find_status(tl,id):
	index=0
	for i in tl.statuses:
		if i.id==id:
			return index
		index+=1

	return -1

def find_reply(tl, id):
	index=0
	for i in tl.statuses:
		if getattr(i,"in_reply_to_id",None)==id:
			return index
		index+=1

	return -1

def speak_reply(account, status):
	if getattr(status,"in_reply_to_id",None):
		ref=lookup_status(account,status.in_reply_to_id)
		speak.speak(process_tweet(ref))
	else:
		speak.speak("Not a reply.")

def question(title,text, parent=None):
	dlg=wx.MessageDialog(parent,text,title,wx.YES_NO | wx.ICON_QUESTION)
	result=dlg.ShowModal()
	dlg.Destroy()
	if result== wx.ID_YES:
		return 1
	else:
		return 2

def warn(message, caption = 'Warning!', parent=None):
	dlg = wx.MessageDialog(parent, message, caption, wx.OK | wx.ICON_WARNING)
	dlg.ShowModal()
	dlg.Destroy()

def alert(message, caption = "", parent=None):
	dlg = wx.MessageDialog(parent, message, caption, wx.OK)
	dlg.ShowModal()
	dlg.Destroy()

_cfu_log = logging.getLogger("lights_off.cfu")

def cfu(silent=True):
	url="https://pypi.org/pypi/lights-off/json"
	_cfu_log.info("checking for updates at %s (current version: %s)", url, application.version)
	try:
		data=json.loads(requests.get(url, timeout=5).content.decode())
		latest=data["info"]["version"]
		_cfu_log.info("latest version on PyPI: %s", latest)
		if application.version<latest:
			_cfu_log.info("update available: %s -> %s", application.version, latest)
			ud=question(
				"Update available: "+latest,
				"There is an update available. Your version: "+application.version+
				". Latest version: "+latest+
				".\r\nRun: pip install --upgrade lights-off\r\nDo you want to open the PyPI page?",
			)
			if ud==1:
				webbrowser.open("https://pypi.org/project/lights-off/")
		else:
			_cfu_log.info("already up to date")
			if not silent:
				alert("No updates available! The latest version is "+latest,"No update available")
	except Exception as e:
		_cfu_log.warning("update check failed: %s", e)

def demojify(text):
	import unicodedata
	# Strip Symbol-other (So) chars — the Unicode category that covers emoji.
	# Keeps letters (including accented), numbers, punctuation, and separators.
	return "".join(ch for ch in text if unicodedata.category(ch) != "So").strip()


def strip_bio(raw):
	"""HTML-decode and strip tags from a Mastodon bio/note field."""
	if not raw:
		return ""
	return strip_html(html.unescape(raw))


def strip_display_name(display_name, acct_fallback=""):
	"""Strip emojis from display_name, but keep it if it's entirely emojis."""
	stripped = demojify(display_name)
	if stripped:
		return stripped
	# Name was all emojis — keep original so the user isn't nameless
	return display_name or acct_fallback

def handle_error(error, name="Unknown"):
	msg=str(error)
	globals.errors.append("Error in "+name+": "+msg)
	if globals.prefs.errors:
		speak.speak("Error in "+name+": "+msg)
		if globals.currentAccount:
			sound.play(globals.currentAccount,"error")

def get_account(id):
	for i in globals.accounts:
		if i.me.id==id:
			return i
	return -1

def openURL(url):
	if platform.system()!="Darwin":
		webbrowser.open(url)
	else:
		os.system(f"open {url}")

