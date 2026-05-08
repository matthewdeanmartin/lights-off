import time
from lights_off import globals
from lights_off import utils
from lights_off import speak
from lights_off import sound
import threading
import os
from lights_off.GUI import main
class TimelineSettings(object):
	def __init__(self,account,tl):
		self.account_id=account
		self.tl=tl
		self.mute=False
		self.read=False
		self.hide=False

class timeline(object):
	def __init__(self,account,name,type,data=None,user=None,status=None,silent=False):
		self.members=[]
		self.account=account
		self.status=status
		self.name=name
		self.removable=False
		self.initial=True
		self.statuses=[]
		self.type=type
		self.data=data
		self.user=user
		self.index=0
		self.page=0
		self.mute=False
		self.read=False
		self.hide=False
		for i in globals.timeline_settings:
			if i.account_id==self.account.me.id and i.tl==self.name:
				self.mute=i.mute
				self.read=i.read
				self.hide=i.hide
		if self.type=="user" and self.name!="Sent" or self.type=="conversation" or self.type=="search" or self.type=="list":
			if not silent:
				sound.play(self.account,"open")
			self.removable=True
		self.update_kwargs={"limit":globals.prefs.count}
		self.prev_kwargs={"limit":globals.prefs.count}
		if self.type=="home":
			self.func=self.account.api.timeline_home
		elif self.type=="notifications":
			self.func=self.account.api.notifications
		elif self.type=="likes":
			self.func=self.account.api.favourites
		elif self.type=="user":
			self.func=self.account.api.account_statuses
			user_id=self.data
			# data may be a username string, an int id, or a user object
			if isinstance(user_id,str) and not user_id.isdigit():
				resolved=utils.lookup_user_name(self.account,user_id) if self.user is None else self.user
				if resolved is not None and resolved!=-1:
					user_id=resolved.id
			elif hasattr(user_id,"id"):
				user_id=user_id.id
			self.update_kwargs['id']=user_id
			self.prev_kwargs['id']=user_id
		elif self.type=="list":
			self.func=self.account.api.timeline_list
			self.update_kwargs['id']=self.data
			self.prev_kwargs['id']=self.data
		elif self.type=="search":
			self.func=self.account.api.search_v2
			# search_v2 does not accept limit; clear it and set q
			self.update_kwargs.pop('limit', None)
			self.prev_kwargs.pop('limit', None)
			self.update_kwargs['q']=self.data
			self.prev_kwargs['q']=self.data
		elif self.type=="messages":
			self.func=self.account.api.conversations
		if self.type!="conversation":
			threading.Thread(target=self.load,daemon=True).start()
		else:
			self.load_conversation()
		if self.type=="messages":
			m=globals.load_messages(self.account)
			if m is not None:
				self.statuses=m
				self.initial=False

	def read_items(self,items):
		pref=""
		if len(globals.accounts)>1:
			pref=self.account.me.acct+": "
		if len(items)>=4:
			speak.speak(pref+str(len(items))+" new in "+self.name)
			return
		speak.speak(pref+", ".join(self.prepare(items)))

	def load_conversation(self):
		status=self.status
		self.process_status(status)
		if globals.prefs.reversed:
			self.statuses.reverse()
		if self.account.currentTimeline==self:
			main.window.refreshList()
		sound.play(self.account,"search")

	def play(self):
		if self.type=="user":
			user_acct=getattr(self.user,"acct","") if self.user else ""
			user_sound=globals.confpath+"/sounds/"+self.account.prefs.soundpack+"/"+user_acct+".ogg"
			if not os.path.exists(user_sound):
				sound.play(self.account,"user")
			else:
				sound.play(self.account,user_acct)
		else:
			if self.type=="search":
				sound.play(self.account,"search")
			elif self.type=="list":
				sound.play(self.account,"list")
			else:
				sound.play(self.account,self.name.lower())

	def process_status(self, status):
		self.statuses.append(status)
		try:
			if getattr(status,"in_reply_to_id",None):
				self.process_status(utils.lookup_status(self.account,status.in_reply_to_id))
			if status.reblog:
				self.process_status(status.reblog)
		except Exception:
			pass

	def hide_tl(self):
		if self.type=="user" and self.name!="Sent" or self.type=="list" or self.type=="search" or self.type=="conversation":
			utils.alert("You can't hide this timeline. Try closing it instead.","Error")
			return
		self.hide=True
		globals.get_timeline_settings(self.account.me.id,self.name).hide=self.hide
		globals.save_timeline_settings()
		if self.account.currentTimeline==self:
			self.account.currentTimeline=self.account.timelines[0]
			main.window.refreshTimelines()

	def unhide_tl(self):
		self.hide=False
		globals.get_timeline_settings(self.account.me.id,self.name).hide=self.hide
		globals.save_timeline_settings()
		main.window.refreshTimelines()

	def load(self,back=False,speech=False,items=[]):
		if self.hide:
			return False
		if items==[]:
			if back:
				if not globals.prefs.reversed:
					self.prev_kwargs['max_id']=self.statuses[len(self.statuses)-1].id
				else:
					self.prev_kwargs['max_id']=self.statuses[0].id
			tl=None
			try:
				if not back:
					tl=self.func(**self.update_kwargs)
				else:
					tl=self.func(**self.prev_kwargs)
			except Exception as error:
				utils.handle_error(error,self.account.me.acct+"'s "+self.name)
				if self.removable:
					if self.type=="user" and self.data in self.account.prefs.user_timelines:
						self.account.prefs.user_timelines.remove(self.data)
					if self.type=="list" and self.data in self.account.prefs.list_timelines:
						self.account.prefs.list_timelines.remove(self.data)
					if self.type=="search" and self.data in self.account.prefs.search_timelines:
						self.account.prefs.search_timelines.remove(self.data)
					self.account.timelines.remove(self)
					if self.account==globals.currentAccount:
						main.window.refreshTimelines()
						if self.account.currentTimeline==self:
							main.window.list.SetSelection(0)
							self.account.currentIndex=0
							main.window.on_list_change(None)

				return
		else:
			tl=items
		# search_v2 returns a dict; unwrap statuses list
		if isinstance(tl, dict) and "statuses" in tl:
			tl=tl["statuses"]
		# Notifications come back as Notification objects; convert them.
		if self.type=="notifications" and tl is not None:
			converted=[]
			for n in tl:
				s=utils.notification_to_status(n)
				if s is not None:
					converted.append(s)
			tl=converted
		# Some response paths hand back plain dicts instead of typed
		# AttribAccessDicts (e.g. Mastodon.py fallback parsing for
		# instance-specific JSON quirks). Promote them so attribute access
		# works downstream.
		if tl is not None:
			tl=[utils.ensure_attr_access(i) for i in tl]
		if tl is not None:
			newitems=0
			objs=[]
			objs2=[]
			for i in tl:
				utils.add_users(i)
				if not utils.isDuplicate(i, self.statuses):
					newitems+=1
					if self.initial or back:
						if not globals.prefs.reversed:
							self.statuses.append(i)
							objs2.append(i)
						else:
							self.statuses.insert(0,i)
							objs2.insert(0,i)
					else:
						if not globals.prefs.reversed:
							objs.append(i)
							objs2.append(i)
						else:
							objs.insert(0,i)
							objs2.insert(0,i)

			if newitems==0 and speech:
				speak.speak("Nothing new.")
			if newitems>0:
				if self.read:
					self.read_items(objs2)
				if len(objs)>0:
					if not globals.prefs.reversed:
						objs.reverse()
						objs2.reverse()
					for i in objs:
						if not globals.prefs.reversed:
							self.statuses.insert(0,i)
						else:
							self.statuses.append(i)

				if globals.currentAccount==self.account and self.account.currentTimeline==self:
					if not back and not self.initial:
						if not globals.prefs.reversed:
							main.window.add_to_list(self.prepare(objs2))
						else:
							objs2.reverse()
							main.window.append_to_list(self.prepare(objs2))

					else:
						if not globals.prefs.reversed:
							main.window.append_to_list(self.prepare(objs2))
						else:
							main.window.add_to_list(self.prepare(objs2))

				if items==[] and self.type!="messages":
					if not globals.prefs.reversed:
						self.update_kwargs['since_id']=tl[0].id
					else:
						self.update_kwargs['since_id']=tl[len(tl)-1].id

				if not back and not self.initial:
					if not globals.prefs.reversed:
						self.index+=newitems
						if globals.currentAccount==self.account and self.account.currentTimeline==self and len(self.statuses)>0:
							try:
								main.window.list2.SetSelection(self.index)
							except Exception:
								pass
				if back and globals.prefs.reversed:
					self.index+=newitems
					if globals.currentAccount==self.account and self.account.currentTimeline==self and len(self.statuses)>0:
						main.window.list2.SetSelection(self.index)

				if self.initial:
					if not globals.prefs.reversed:
						self.index=0
					else:
						self.index=len(self.statuses)-1
				if not self.mute and not self.hide:
					self.play()
				globals.prefs.statuses_received+=newitems
				if speech:
					announcement=f"{newitems} new item"
					if newitems!=1:
						announcement+="s"
					speak.speak(announcement)
			if self.initial:
				self.initial=False
#			if globals.currentTimeline==self:
#				main.window.refreshList()
		if self == self.account.timelines[len(self.account.timelines) - 1] and not self.account.ready:
			self.account.ready=True
			sound.play(self.account,"ready")

	def toggle_read(self):
		if self.read:
			self.read=False
			speak.speak("Autoread off")
		else:
			self.read=True
			speak.speak("Autoread on")
		globals.get_timeline_settings(self.account.me.id,self.name).read=self.read
		globals.save_timeline_settings()

	def toggle_mute(self):
		if self.mute:
			self.mute=False
			speak.speak("Unmuted")
		else:
			self.mute=True
			speak.speak("Muted")
		globals.get_timeline_settings(self.account.me.id,self.name).mute=self.mute
		globals.save_timeline_settings()

	def _render(self, item):
		if self.type=="messages":
			return utils.process_message(item)
		return utils.process_tweet(item)

	def get(self):
		return [self._render(i) for i in self.statuses]

	def prepare(self, items):
		items2=[]
		for i in items:
			if not globals.prefs.reversed:
				items2.append(self._render(i))
			else:
				items2.insert(0,self._render(i))
		return items2

def add(account,name,type,data=None,user=None):
	account.timelines.append(timeline(account,name,type,data,user))
	if account==globals.currentAccount:
		main.window.refreshTimelines()

def timelineThread(account):
	while 1:
		time.sleep(globals.prefs.update_time*60)
		for i in account.timelines:
			try:
				if i.type=="list":
					try:
						members=account.api.list_accounts(i.data)
						i.members=[]
						for i2 in members:
							i.members.append(i2.id)
					except Exception:
						pass
				if i.type!="conversation":
					i.load()
			except Exception as error:
				sound.play(account,"error")
				speak.speak(str(error))
		if globals.prefs.streaming and not getattr(account,"_stream_thread",None) or globals.prefs.streaming and hasattr(account,"_stream_thread") and not account._stream_thread.is_alive():
			account.start_stream()
		if len(globals.unknown_users)>0:
			try:
				for uid in globals.unknown_users:
					u=account.api.account(uid)
					if u not in globals.users:
						globals.users.insert(0,u)
				globals.unknown_users=[]
			except Exception:
				globals.unknown_users=[]

		globals.save_users()
def reverse():
	for i in globals.accounts:
		for i2 in i.timelines:
			i2.statuses.reverse()
			i2.index=(len(i2.statuses)-1)-i2.index
	main.window.on_list_change(None)
