import os
import webbrowser
import platform
import pyperclip
import sys
import logging
from lights_off import application
import wx
from lights_off.keyboard_handler.wx_handler import WXKeyboardHandler
from lights_off import globals
from lights_off import speak
from . import account_options, accounts, invisible, lists, misc, options, profile, search, timelines, tray, tweet, view
from lights_off import utils
from lights_off import sound
import threading

_log = logging.getLogger("lights_off.menu")


def _logged(label):
	"""Decorator that logs the menu action name before the handler runs."""
	def decorator(fn):
		def wrapper(self, event=None):
			_log.info("menu: %s", label)
			return fn(self, event)
		wrapper.__name__ = fn.__name__
		return wrapper
	return decorator


class MainGui(wx.Frame):
	def __init__(self, title):
		self.invisible=False
		wx.Frame.__init__(self, None, title=title,size=(800,600))
		self.Center()
		if platform.system()!="Darwin":
			self.trayicon=tray.TaskBarIcon(self)
		self.handler=WXKeyboardHandler(self)
		self.handler.register_key("control+alt+win+t",self.ToggleWindow)
		self.handler.register_key("control+alt+win+q",self.OnClose)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.panel = wx.Panel(self)
		self.main_box = wx.BoxSizer(wx.VERTICAL)
		self.menuBar = wx.MenuBar()
		if platform.system()!="Darwin":
			ctrl="control"
		else:
			ctrl="command"

		menu = wx.Menu()
		m_accounts = menu.Append(-1, "Accounts ("+ctrl+"+A)", "accounts")
		self.Bind(wx.EVT_MENU, self.OnAccounts, m_accounts)
		m_update_profile = menu.Append(-1, "Update profile", "profile")
		self.Bind(wx.EVT_MENU, self.OnUpdateProfile, m_update_profile)
		m_lists = menu.Append(-1, "Lists", "lists")
		self.Bind(wx.EVT_MENU, self.OnLists, m_lists)
		m_followers = menu.Append(-1, "List Followers ("+ctrl+"+Left Bracket)", "followers")
		self.Bind(wx.EVT_MENU, self.OnFollowers, m_followers)
		m_friends = menu.Append(-1, "List Friends ("+ctrl+"+right bracket)", "friends")
		self.Bind(wx.EVT_MENU, self.OnFriends, m_friends)
		if platform.system()!="Darwin":
			m_options = menu.Append(wx.ID_PREFERENCES, "Global Options", "options")
		else:
			m_options = menu.Append(wx.ID_PREFERENCES, "Preferences ("+ctrl+"+comma", "options")
		self.Bind(wx.EVT_MENU, self.OnOptions, m_options)
		m_account_options = menu.Append(-1, "Account options", "account_options")
		self.Bind(wx.EVT_MENU, self.OnAccountOptions, m_account_options)
		m_close = menu.Append(wx.ID_EXIT, "exit", "exit")
		self.Bind(wx.EVT_MENU, self.OnClose, m_close)
		self.menuBar.Append(menu, "&Application")
		menu2 = wx.Menu()
		m_tweet = menu2.Append(-1, "New post ("+ctrl+"+n)", "tweet")
		self.Bind(wx.EVT_MENU, self.OnTweet, m_tweet)
		m_reply = menu2.Append(-1, "Reply ("+ctrl+"+r)", "reply")
		self.Bind(wx.EVT_MENU, self.OnReply, m_reply)
		m_retweet = menu2.Append(-1, "Boost ("+ctrl+"+shift+r)", "retweet")
		self.Bind(wx.EVT_MENU, self.OnRetweet, m_retweet)
		if platform.system()=="Darwin":
			m_quote = menu2.Append(-1, "Quote post (option+q)", "quote")
		else:
			m_quote = menu2.Append(-1, "Quote post ("+ctrl+"+q)", "quote")
		self.Bind(wx.EVT_MENU, self.OnQuote, m_quote)
		m_like=menu2.Append(-1, "Favourite ("+ctrl+"+l)", "like")
		self.Bind(wx.EVT_MENU, self.OnLike, m_like)
		m_url=menu2.Append(-1, "Open URL ("+ctrl+"+o)", "url")
		self.Bind(wx.EVT_MENU, self.OnUrl, m_url)
		m_tweet_url=menu2.Append(-1, "Open URL of Tweet ("+ctrl+"+shift+o)", "tweet_url")
		self.Bind(wx.EVT_MENU, self.OnTweetUrl, m_tweet_url)
		m_delete = menu2.Append(-1, "Delete Post (Delete)", "tweet")
		self.Bind(wx.EVT_MENU, self.OnDelete, m_delete)
		m_copy = menu2.Append(-1, "Copy post to clipboard ("+ctrl+"+c)", "copy")
		self.Bind(wx.EVT_MENU, self.onCopy, m_copy)
		m_message=menu2.Append(-1, "Direct message ("+ctrl+"+d)", "message")
		self.Bind(wx.EVT_MENU, self.OnMessage, m_message)
		m_follow=menu2.Append(-1, "Follow ("+ctrl+"+f)", "follow")
		self.Bind(wx.EVT_MENU, self.OnFollow, m_follow)
		m_unfollow=menu2.Append(-1, "Unfollow ("+ctrl+"+shift+f", "follow")
		self.Bind(wx.EVT_MENU, self.OnUnfollow, m_unfollow)
		m_add_to_list=menu2.Append(-1, "Add to list ("+ctrl+"+i)", "addlist")
		self.Bind(wx.EVT_MENU, self.OnAddToList, m_add_to_list)
		m_remove_from_list=menu2.Append(-1, "Remove from list ("+ctrl+"+shift+i)", "removelist")
		self.Bind(wx.EVT_MENU, self.OnRemoveFromList, m_remove_from_list)
		m_block=menu2.Append(-1, "Block ("+ctrl+"+b)", "block")
		self.Bind(wx.EVT_MENU, self.OnBlock, m_block)
		m_unblock=menu2.Append(-1, "Unblock ("+ctrl+"+shift+b)", "unblock")
		self.Bind(wx.EVT_MENU, self.OnUnblock, m_unblock)
		m_mute_user=menu2.Append(-1, "Mute", "mute")
		self.Bind(wx.EVT_MENU, self.OnMuteUser, m_mute_user)
		m_unmute_user=menu2.Append(-1, "Unmute", "unmute")
		self.Bind(wx.EVT_MENU, self.OnUnmuteUser, m_unmute_user)
		m_view=menu2.Append(-1, "View post (Enter)", "view")
		self.Bind(wx.EVT_MENU, self.OnView, m_view)
		m_user_profile=menu2.Append(-1, "User Profile ("+ctrl+"+shift+u)", "profile")
		self.Bind(wx.EVT_MENU, self.OnUserProfile, m_user_profile)
		m_speak_user=menu2.Append(-1, "Speak user ("+ctrl+"+semicolon)", "speak")
		self.Bind(wx.EVT_MENU, self.OnSpeakUser, m_speak_user)
		m_speak_reply=menu2.Append(-1, "Speak reference post of this reply ("+ctrl+"+shift+semicolon)", "speak2")
		self.Bind(wx.EVT_MENU, self.OnSpeakReply, m_speak_reply)
		m_conversation=menu2.Append(-1, "Load conversation/related posts ("+ctrl+"+g)", "conversation")
		self.Bind(wx.EVT_MENU, self.OnConversation, m_conversation)
		self.menuBar.Append(menu2, "A&ctions")
		menu7 = wx.Menu()
		m_mutual_following=menu7.Append(-1, "View mutual follows (users who I follow that also follow me)", "conversation")
		self.Bind(wx.EVT_MENU, self.OnMutualFollowing, m_mutual_following)
		m_not_following=menu7.Append(-1, "View users who follow me that I do not follow", "conversation")
		self.Bind(wx.EVT_MENU, self.OnNotFollowing, m_not_following)
		m_not_following_me=menu7.Append(-1, "View users who I follow that do not follow me", "conversation")
		self.Bind(wx.EVT_MENU, self.OnNotFollowingMe, m_not_following_me)
		m_havent_tweeted=menu7.Append(-1, "View users who I follow that haven't posted in a year", "conversation")
		self.Bind(wx.EVT_MENU, self.OnHaventTweeted, m_havent_tweeted)
		self.menuBar.Append(menu7, "U&sers")
		menu3 = wx.Menu()
		m_refresh = menu3.Append(-1, "Refresh timeline (F5)", "refresh")
		self.Bind(wx.EVT_MENU, self.onRefresh, m_refresh)
		m_prev = menu3.Append(-1, "Load older posts (alt/option+pageup)", "prev")
		self.Bind(wx.EVT_MENU, self.onPrev, m_prev)
		m_hide = menu3.Append(-1, "Hide Timeline ("+ctrl+"+h)", "hide")
		self.Bind(wx.EVT_MENU, self.OnHide, m_hide)
		m_manage_hide = menu3.Append(-1, "Manage hidden Timelines ("+ctrl+"+shift+h)", "manage_hide")
		self.Bind(wx.EVT_MENU, self.OnManageHide, m_manage_hide)
		m_read = menu3.Append(-1, "Toggle autoread ("+ctrl+"+e)", "autoread")
		self.Bind(wx.EVT_MENU, self.OnRead, m_read)
		if platform.system()!="Darwin":
			m_mute = menu3.Append(-1, "Toggle mute ("+ctrl+"+m)", "mute")
		else:
			m_mute = menu3.Append(-1, "Toggle mute ("+ctrl+"+shift+m)", "mute")
		self.Bind(wx.EVT_MENU, self.OnMute, m_mute)
		m_user_timeline = menu3.Append(-1, "User timeline ("+ctrl+"+u)", "user")
		self.Bind(wx.EVT_MENU, self.OnUserTimeline, m_user_timeline)
		m_search = menu3.Append(-1, "Search ("+ctrl+"+slash)", "search")
		self.Bind(wx.EVT_MENU, self.OnSearch, m_search)
		m_user_search = menu3.Append(-1, "User Search ("+ctrl+"+shift+slash)", "search")
		self.Bind(wx.EVT_MENU, self.OnUserSearch, m_user_search)
		self.m_close_timeline = menu3.Append(-1, "Close timeline ("+ctrl+"+w)", "removetimeline")
		self.m_close_timeline.Enable(False)
		self.Bind(wx.EVT_MENU, self.OnCloseTimeline, self.m_close_timeline)
		self.menuBar.Append(menu3, "Time&line")
		menu4 = wx.Menu()
		m_play_external = menu4.Append(-1, "Play media ("+ctrl+"+enter)", "play_external")
		self.Bind(wx.EVT_MENU, self.OnPlayExternal, m_play_external)
		m_volup = menu4.Append(-1, "Volume up (alt/option+up)", "volup")
		self.Bind(wx.EVT_MENU, self.OnVolup, m_volup)
		m_voldown = menu4.Append(-1, "Volume down (alt/option+down)", "voldown")
		self.Bind(wx.EVT_MENU, self.OnVoldown, m_voldown)
		self.menuBar.Append(menu4, "A&udio")
		menu5 = wx.Menu()
		m_previous_in_thread = menu5.Append(-1, "Previous post in thread ("+ctrl+"+up)", "prevtweet")
		self.Bind(wx.EVT_MENU, self.OnPreviousInThread, m_previous_in_thread)
		m_next_in_thread = menu5.Append(-1, "Next post in thread ("+ctrl+"+down)", "nexttweet")
		self.Bind(wx.EVT_MENU, self.OnNextInThread, m_next_in_thread)
		m_previous_from_user = menu5.Append(-1, "Previous post from user ("+ctrl+"+left)", "prevuser")
		self.Bind(wx.EVT_MENU, self.OnPreviousFromUser, m_previous_from_user)
		m_next_from_user = menu5.Append(-1, "Next post from user ("+ctrl+"+right)", "nextuser")
		self.Bind(wx.EVT_MENU, self.OnNextFromUser, m_next_from_user)
		m_next_timeline = menu5.Append(-1, "Next timeline (alt/option+right)", "nexttl")
		self.Bind(wx.EVT_MENU, self.OnNextTimeline, m_next_timeline)
		m_prev_timeline = menu5.Append(-1, "Previous timeline (alt/Option+left)", "prevtl")
		self.Bind(wx.EVT_MENU, self.OnPrevTimeline, m_prev_timeline)
		self.menuBar.Append(menu5, "Navigation")
		menu6 = wx.Menu()
		m_readme = menu6.Append(-1, "Readme (F1)", "readme")
		self.Bind(wx.EVT_MENU, self.OnReadme, m_readme)
		m_cfu = menu6.Append(-1, "Check for updates", "cfu")
		self.Bind(wx.EVT_MENU, self.OnCfu, m_cfu)
		m_stats = menu6.Append(-1, "Stats for nerds", "stats")
		self.Bind(wx.EVT_MENU, self.OnStats, m_stats)
		m_errors = menu6.Append(-1, "View API errors", "errors")
		self.Bind(wx.EVT_MENU, self.OnErrors, m_errors)
		m_view_user_db = menu6.Append(-1, "View user database", "viewusers")
		self.Bind(wx.EVT_MENU, self.OnViewUserDb, m_view_user_db)
		m_clean_user_db = menu6.Append(-1, "Refresh user database", "cleanusers")
		self.Bind(wx.EVT_MENU, self.OnCleanUserDb, m_clean_user_db)
		self.menuBar.Append(menu6, "&Help")
		self.SetMenuBar(self.menuBar)
		self.list_label=wx.StaticText(self.panel, -1, label="Timelines")
		self.main_box.Add(self.list_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		self.list=wx.ListBox(self.panel, -1, size=(-1,120))
		self.main_box.Add(self.list, 0, wx.ALL|wx.EXPAND, 10)
		self.list.Bind(wx.EVT_LISTBOX, self.on_list_change)
		self.list.SetFocus()
		self.list2_label=wx.StaticText(self.panel, -1, label="Contents")
		self.main_box.Add(self.list2_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		self.list2=wx.ListBox(self.panel, -1, size=(-1,300))
		self.main_box.Add(self.list2, 1, wx.ALL|wx.EXPAND, 10)
		self.list2.Bind(wx.EVT_LISTBOX, self.on_list2_change)
		accel=[]
		accel.append((wx.ACCEL_ALT, ord('X'), m_close.GetId()))
		if platform.system()=="Darwin":
			accel.append((wx.ACCEL_CTRL, ord(','), m_options.GetId()))
			accel.append((wx.ACCEL_CTRL|wx.ACCEL_SHIFT, ord(','), m_account_options.GetId()))
		accel.append((wx.ACCEL_CTRL, ord('N'), m_tweet.GetId()))
		accel.append((wx.ACCEL_CTRL, ord('R'), m_reply.GetId()))
		accel.append((wx.ACCEL_CTRL|wx.ACCEL_SHIFT, ord('R'), m_retweet.GetId()))
		if platform.system()=="Darwin":
			accel.append((wx.ACCEL_ALT, ord('Q'), m_quote.GetId()))
		else:
			accel.append((wx.ACCEL_CTRL, ord('Q'), m_quote.GetId()))
		accel.append((wx.ACCEL_CTRL, ord('O'), m_url.GetId()))
		accel.append((wx.ACCEL_CTRL|wx.ACCEL_SHIFT, ord('O'), m_tweet_url.GetId()))
		accel.append((wx.ACCEL_CTRL, ord('D'), m_message.GetId()))
		accel.append((wx.ACCEL_CTRL, ord('f'), m_follow.GetId()))
		accel.append((wx.ACCEL_CTRL|wx.ACCEL_SHIFT, ord('f'), m_unfollow.GetId()))
		accel.append((wx.ACCEL_CTRL, ord('b'), m_block.GetId()))
		accel.append((wx.ACCEL_CTRL|wx.ACCEL_SHIFT, ord('b'), m_unblock.GetId()))
		accel.append((wx.ACCEL_CTRL, ord('a'), m_accounts.GetId()))
		accel.append((wx.ACCEL_CTRL, ord('i'), m_add_to_list.GetId()))
		accel.append((wx.ACCEL_CTRL|wx.ACCEL_SHIFT, ord('i'), m_remove_from_list.GetId()))
		accel.append((wx.ACCEL_CTRL, ord("c"), m_copy.GetId()))
		accel.append((wx.ACCEL_NORMAL, wx.WXK_RETURN, m_view.GetId()))
		accel.append((wx.ACCEL_CTRL, wx.WXK_RETURN, m_play_external.GetId()))
		accel.append((wx.ACCEL_CTRL, ord('U'), m_user_timeline.GetId()))
		accel.append((wx.ACCEL_CTRL, ord('/'), m_search.GetId()))
		accel.append((wx.ACCEL_CTRL|wx.ACCEL_SHIFT, ord('/'), m_user_search.GetId()))
		accel.append((wx.ACCEL_CTRL|wx.ACCEL_SHIFT, ord('U'), m_user_profile.GetId()))
		accel.append((wx.ACCEL_CTRL, ord('W'), self.m_close_timeline.GetId()))
		accel.append((wx.ACCEL_ALT, wx.WXK_PAGEUP, m_prev.GetId()))
		accel.append((wx.ACCEL_CTRL, ord('h'), m_hide.GetId()))
		accel.append((wx.ACCEL_CTRL|wx.ACCEL_SHIFT, ord('h'), m_manage_hide.GetId()))
		accel.append((wx.ACCEL_CTRL, ord('L'), m_like.GetId()))
		accel.append((wx.ACCEL_CTRL, ord('G'), m_conversation.GetId()))
		accel.append((wx.ACCEL_CTRL, ord(';'), m_speak_user.GetId()))
		accel.append((wx.ACCEL_CTRL|wx.ACCEL_SHIFT, ord(';'), m_speak_reply.GetId()))
		accel.append((wx.ACCEL_ALT, wx.WXK_UP, m_volup.GetId()))
		accel.append((wx.ACCEL_ALT, wx.WXK_DOWN, m_voldown.GetId()))
		accel.append((wx.ACCEL_CTRL, ord("e"), m_read.GetId()))
		if platform.system()=="Darwin":
			accel.append((wx.ACCEL_CTRL|wx.ACCEL_SHIFT, ord("m"), m_mute.GetId()))
		else:
			accel.append((wx.ACCEL_CTRL, ord("m"), m_mute.GetId()))
		accel.append((wx.ACCEL_CTRL, wx.WXK_UP, m_previous_in_thread.GetId()))
		accel.append((wx.ACCEL_CTRL, wx.WXK_DOWN, m_next_in_thread.GetId()))
		accel.append((wx.ACCEL_CTRL, wx.WXK_LEFT, m_previous_from_user.GetId()))
		accel.append((wx.ACCEL_CTRL, wx.WXK_RIGHT, m_next_from_user.GetId()))
		accel.append((wx.ACCEL_ALT, wx.WXK_RIGHT, m_next_timeline.GetId()))
		accel.append((wx.ACCEL_ALT, wx.WXK_LEFT, m_prev_timeline.GetId()))
		accel.append((wx.ACCEL_CTRL, ord("["), m_followers.GetId()))
		accel.append((wx.ACCEL_CTRL, ord("]"), m_friends.GetId()))
		accel.append((wx.ACCEL_CTRL|wx.ACCEL_SHIFT, ord("L"), m_lists.GetId()))
		accel.append((wx.ACCEL_NORMAL, wx.WXK_F5, m_refresh.GetId()))
		accel.append((wx.ACCEL_NORMAL, wx.WXK_DELETE, m_delete.GetId()))
		accel.append((wx.ACCEL_NORMAL, wx.WXK_F1, m_readme.GetId()))
		accel_tbl=wx.AcceleratorTable(accel)
		self.SetAcceleratorTable(accel_tbl)
		self.panel.SetSizer(self.main_box)
		self.main_box.Fit(self.panel)
		self.SetMinSize((600, 500))

	def _read_keymap(self):
		from importlib.resources import files, as_file
		name = "keymac.keymap" if platform.system()=="Darwin" else "keymap.keymap"
		ref = files("lights_off").joinpath(name)
		with as_file(ref) as p:
			return p.read_text(encoding="utf-8").split("\n")

	def register_keys(self):
		self.invisible=True
		for i in self._read_keymap():
			key=i.strip(" ").split("=")
			invisible.register_key(key[0],key[1])

	def unregister_keys(self):
		self.invisible=False
		for i in self._read_keymap():
			key=i.split("=")
			invisible.register_key(key[0],key[1],False)

	def ToggleWindow(self):
		if self.IsShown():
			self.Show(False)
			globals.prefs.window_shown=False
		else:
			self.Show(True)
			self.Raise()
			globals.prefs.window_shown=True
			if not globals.prefs.invisible_sync:
				self.list.SetSelection(globals.currentAccount.currentIndex)
				self.on_list_change(None)
				self.list2.SetSelection(globals.currentAccount.currentTimeline.index)
				self.on_list2_change(None)

	@_logged("Help / Readme")
	def OnReadme(self,event=None):
		webbrowser.open("https://github.com/QuinterApp/Quinter")

	@_logged("Timeline / Toggle autoread")
	def OnRead(self,event=None):
		globals.currentAccount.currentTimeline.toggle_read()

	@_logged("Timeline / Toggle mute")
	def OnMute(self,event=None):
		globals.currentAccount.currentTimeline.toggle_mute()

	@_logged("Help / Stats for nerds")
	def OnStats(self, event=None):
		txt=view.ViewTextGui("You have sent a total of "+str(globals.prefs.tweets_sent)+" posts, of which "+str(globals.prefs.replies_sent)+" are replies and "+str(globals.prefs.quotes_sent)+" are quotes.\r\nYou have boosted "+str(globals.prefs.retweets_sent)+" posts, and favourited "+str(globals.prefs.likes_sent)+" posts.\r\nYou have sent "+str(globals.prefs.chars_sent)+" characters to Mastodon from lights-off!\r\nYou have received "+str(globals.prefs.statuses_received)+" posts in total through all of your timelines.")
		txt.Show()

	@_logged("Help / View API errors")
	def OnErrors(self, event=None):
		errors=""
		for i in globals.errors:
			errors+=i+"\r\n"
		txt=view.ViewTextGui(errors)
		txt.Show()

	@_logged("Timeline / Manage hidden timelines")
	def OnManageHide(self, event=None):
		gui=timelines.HiddenTimelinesGui(globals.currentAccount)
		gui.Show()

	@_logged("Help / Check for updates")
	def OnCfu(self, event=None):
		utils.cfu(False)

	@_logged("Actions / Copy post")
	def onCopy(self,event=None):
		pyperclip.copy(utils.template_to_string(globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index],globals.prefs.copyTemplate))
		speak.speak("Copied")

	@_logged("Application / Exit")
	def OnClose(self, event=None):
		speak.speak("Exiting.")
		if platform.system()!="Darwin":
			self.trayicon.on_exit(event,False)
		self.Destroy()
		sys.exit()

	@_logged("Audio / Play media")
	def OnPlayExternal(self,event=None):
		threading.Thread(target=misc.play_external,args=(globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index],)).start()


	@_logged("Actions / Load conversation")
	def OnConversation(self,event=None):
		misc.load_conversation(globals.currentAccount,globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index])

	@_logged("Actions / Delete post")
	def OnDelete(self,event=None):
		misc.delete(globals.currentAccount,globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index])

	@_logged("Timeline / Hide timeline")
	def OnHide(self,event=None):
		globals.currentAccount.currentTimeline.hide_tl()

	@_logged("Navigation / Next in thread")
	def OnNextInThread(self,event=None):
		if not globals.prefs.reversed:
			misc.next_in_thread(globals.currentAccount)
		else:
			misc.previous_in_thread(globals.currentAccount)

	@_logged("Navigation / Previous in thread")
	def OnPreviousInThread(self,event=None):
		if not globals.prefs.reversed:
			misc.previous_in_thread(globals.currentAccount)
		else:
			misc.next_in_thread(globals.currentAccount)

	@_logged("Navigation / Previous from user")
	def OnPreviousFromUser(self,event=None):
		misc.previous_from_user(globals.currentAccount)

	@_logged("Navigation / Next timeline")
	def OnNextTimeline(self,event=None):
		invisible.inv.next_tl(True)

	@_logged("Navigation / Previous timeline")
	def OnPrevTimeline(self,event=None):
		invisible.inv.prev_tl(True)

	@_logged("Navigation / Next from user")
	def OnNextFromUser(self,event=None):
		misc.next_from_user(globals.currentAccount)

	@_logged("Actions / Speak user")
	def OnSpeakUser(self,event=None):
		users=[]
		status=globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index]
		users.append(status.account.acct)
		if getattr(status,"reblog",None) and status.reblog.account.acct not in users:
			users.insert(0,status.reblog.account.acct)
		for i in utils.get_user_objects_in_tweet(globals.currentAccount,status):
			if i.acct not in users:
				users.append(i.acct)
		utils.speak_user(globals.currentAccount,users)

	@_logged("Actions / Speak reply")
	def OnSpeakReply(self,event=None):
		status=globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index]
		utils.speak_reply(globals.currentAccount,status)

	def refreshTimelines(self):
		old_selection=self.list.GetSelection()
		self.list.Clear()
		for i in globals.currentAccount.list_timelines():
			self.list.Insert(i.name,self.list.GetCount())
		try:
			self.list.SetSelection(old_selection)
		except Exception:
			self.list.SetSelection(1)

	def on_list_change(self, event):
		globals.currentAccount.currentTimeline=globals.currentAccount.list_timelines()[self.list.GetSelection()]
		globals.currentAccount.currentIndex=self.list.GetSelection()
		if globals.currentAccount.currentTimeline.removable:
			self.m_close_timeline.Enable(True)
		else:
			self.m_close_timeline.Enable(False)

		self.play_earcon()
		self.refreshList()

	def play_earcon(self):
		if globals.prefs.earcon_top and (not globals.prefs.reversed and globals.currentAccount.currentTimeline.index > 0 or globals.prefs.reversed and globals.currentAccount.currentTimeline.index < len(globals.currentAccount.currentTimeline.statuses) - 1):
			sound.play(globals.currentAccount,"new")

	@_logged("Users / List followers")
	def OnFollowers(self,event=None):
		misc.followers(globals.currentAccount)

	@_logged("Users / List friends")
	def OnFriends(self,event=None):
		misc.friends(globals.currentAccount)

	@_logged("Users / View mutual follows")
	def OnMutualFollowing(self,event=None):
		misc.mutual_following(globals.currentAccount)

	@_logged("Users / Followers I don't follow back")
	def OnNotFollowing(self,event=None):
		misc.not_following(globals.currentAccount)

	@_logged("Users / Friends not following me")
	def OnNotFollowingMe(self,event=None):
		misc.not_following_me(globals.currentAccount)

	@_logged("Users / Haven't posted recently")
	def OnHaventTweeted(self,event=None):
		misc.havent_tweeted(globals.currentAccount)

	def refreshList(self):
		stuffage=globals.currentAccount.currentTimeline.get()
		self.list2.Freeze()
		self.list2.Clear()
		for i in stuffage:
			self.list2.Insert(i,self.list2.GetCount())
		try:
			self.list2.SetSelection(globals.currentAccount.currentTimeline.index)
		except Exception:
			self.list2.SetSelection(globals.currentAccount.currentTimeline.index-1)
		self.list2.Thaw()

	@_logged("Help / View user database")
	def OnViewUserDb(self, event=None):
		u=view.UserViewGui(globals.currentAccount,globals.users,"User Database containing "+str(len(globals.users))+" users.")
		u.Show()

	@_logged("Help / Refresh user database")
	def OnCleanUserDb(self, event=None):
		globals.clean_users()
		globals.save_users()

	def on_list2_change(self, event):
		globals.currentAccount.currentTimeline.index=self.list2.GetSelection()
		tl=globals.currentAccount.currentTimeline
		if globals.prefs.earcon_audio and tl.type!="messages":
			item=tl.statuses[tl.index]
			if len(sound.get_media_urls(utils.find_urls_in_tweet(item))) > 0:
				sound.play(globals.currentAccount,"media")
		# if event is not None:
		# 	from lights_off.GUI.invisible import inv
		# 	inv.speak_item()

	@_logged("Timeline / Refresh")
	def onRefresh(self,event=None):
		globals.currentAccount.currentTimeline.load()

	def add_to_list(self,list):
		self.list2.Freeze()
		for i in list:
			self.list2.Insert(i,0)
		self.list2.Thaw()

	def append_to_list(self,list):
		self.list2.Freeze()
		for i in list:
			self.list2.Insert(i,self.list2.GetCount())
		self.list2.Thaw()

	@_logged("Actions / View post")
	def OnView(self,event=None):
		tl=globals.currentAccount.currentTimeline
		if not tl.statuses:
			return
		viewer=view.ViewGui(globals.currentAccount,tl.statuses[tl.index])
		viewer.Show()

	@_logged("Timeline / Load older posts")
	def onPrev(self,event=None):
		globals.currentAccount.currentTimeline.load(True)

	@_logged("Audio / Volume up")
	def OnVolup(self, event=None):
		if globals.prefs.volume<1.0:
			globals.prefs.volume+=0.1
			globals.prefs.volume=round(globals.prefs.volume,1)
			sound.play(globals.currentAccount,"volume_changed")

	@_logged("Audio / Volume down")
	def OnVoldown(self, event=None):
		if globals.prefs.volume>0.0:
			globals.prefs.volume-=0.1
			globals.prefs.volume=round(globals.prefs.volume,1)
			sound.play(globals.currentAccount,"volume_changed")

	@_logged("Application / Global options")
	def OnOptions(self, event=None):
		Opt=options.OptionsGui()
		Opt.Show()

	@_logged("Application / Account options")
	def OnAccountOptions(self, event=None):
		Opt=account_options.OptionsGui(globals.currentAccount)
		Opt.Show()

	@_logged("Application / Update profile")
	def OnUpdateProfile(self, event=None):
		Profile=profile.ProfileGui(globals.currentAccount)
		Profile.Show()

	@_logged("Application / Accounts")
	def OnAccounts(self, event=None):
		acc=accounts.AccountsGui()
		acc.Show()

	@_logged("Actions / New post")
	def OnTweet(self, event=None):
		NewTweet=tweet.TweetGui(globals.currentAccount)
		NewTweet.Show()

	@_logged("Timeline / User timeline")
	def OnUserTimeline(self, event=None):
		misc.user_timeline(globals.currentAccount,globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index])

	@_logged("Timeline / Search")
	def OnSearch(self, event=None):
		s=search.SearchGui(globals.currentAccount)
		s.Show()

	@_logged("Timeline / User search")
	def OnUserSearch(self, event=None):
		s=search.SearchGui(globals.currentAccount,"user")
		s.Show()

	@_logged("Application / Lists")
	def OnLists(self, event=None):
		s=lists.ListsGui(globals.currentAccount)
		s.Show()

	@_logged("Actions / User profile")
	def OnUserProfile(self, event=None):
		misc.user_profile(globals.currentAccount,globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index])

	@_logged("Actions / Open URL")
	def OnUrl(self, event=None):
		misc.url_chooser(globals.currentAccount,globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index])

	@_logged("Actions / Open URL of post")
	def OnTweetUrl(self, event=None):
		status=globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index]
		url=status.url
		if platform.system()!="Darwin":
			webbrowser.open(url)
		else:
			os.system("open " + url)

	@_logged("Actions / Follow")
	def OnFollow(self, event=None):
		misc.follow(globals.currentAccount,globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index])

	@_logged("Actions / Add to list")
	def OnAddToList(self, event=None):
		misc.add_to_list(globals.currentAccount,globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index])

	@_logged("Actions / Remove from list")
	def OnRemoveFromList(self, event=None):
		misc.remove_from_list(globals.currentAccount,globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index])

	@_logged("Actions / Unfollow")
	def OnUnfollow(self, event=None):
		misc.unfollow(globals.currentAccount,globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index])

	@_logged("Actions / Block")
	def OnBlock(self, event=None):
		misc.block(globals.currentAccount,globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index])

	@_logged("Actions / Unblock")
	def OnUnblock(self, event=None):
		misc.unblock(globals.currentAccount, globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index])

	@_logged("Actions / Mute user")
	def OnMuteUser(self, event=None):
		misc.mute(globals.currentAccount,globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index])

	@_logged("Actions / Unmute user")
	def OnUnmuteUser(self, event=None):
		misc.unmute(globals.currentAccount,globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index])

	@_logged("Timeline / Close timeline")
	def OnCloseTimeline(self, event=None):
		tl=globals.currentAccount.currentTimeline
		if tl.removable:
			if globals.prefs.ask_dismiss:
				dlg=wx.MessageDialog(None,"Are you sure you wish to close "+tl.name+"?","Warning",wx.YES_NO | wx.ICON_QUESTION)
				result=dlg.ShowModal()
				dlg.Destroy()
			if not globals.prefs.ask_dismiss or globals.prefs.ask_dismiss and result== wx.ID_YES:
				if tl.type=="user" and tl.data in globals.currentAccount.prefs.user_timelines:
					globals.currentAccount.prefs.user_timelines.remove(tl.data)
				if tl.type=="list" and tl.data in globals.currentAccount.prefs.list_timelines:
					globals.currentAccount.prefs.list_timelines.remove(tl.data)
				if tl.type=="search" and tl.data in globals.currentAccount.prefs.search_timelines:
					globals.currentAccount.prefs.search_timelines.remove(tl.data)
				globals.currentAccount.timelines.remove(tl)
				sound.play(globals.currentAccount,"close")
				self.refreshTimelines()
				self.list.SetSelection(0)
				globals.currentAccount.currentIndex=0
				self.on_list_change(None)
				del tl

	@_logged("Actions / Reply")
	def OnReply(self, event=None):
		status=globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index]
		misc.reply(globals.currentAccount,status)

	@_logged("Actions / Quote post")
	def OnQuote(self, event=None):
		status=globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index]
		misc.quote(globals.currentAccount,status)

	@_logged("Actions / Direct message")
	def OnMessage(self, event=None):
		tl=globals.currentAccount.currentTimeline
		if len(tl.statuses)==0:
			misc.message_user(globals.currentAccount,"")
			return
		status=tl.statuses[tl.index]
		misc.message(globals.currentAccount,status)

	@_logged("Actions / Boost")
	def OnRetweet(self, event=None):
		status=globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index]
		misc.retweet(globals.currentAccount,status)

	@_logged("Actions / Favourite")
	def OnLike(self, event=None):
		status=globals.currentAccount.currentTimeline.statuses[globals.currentAccount.currentTimeline.index]
		misc.like(globals.currentAccount,status)

global window
window=MainGui(application.name+" "+application.version)
