from mastodon import MastodonError
from lights_off import speak
import wx
from lights_off import globals
from lights_off import sound
from lights_off import utils
import platform
from . import poll

text_box_size=(600,200)
big_text_box_size=(600,300)

class TweetGui(wx.Dialog):
	def __init__(self,account,inittext="",type="tweet",status=None):
		self.account=account
		self.inittext=inittext
		self.max_length=0
		self.status=status
		self.type=type
		self.poll_runfor=None
		self.poll_options=[]
		wx.Dialog.__init__(self, None, title=type, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.panel = wx.Panel(self)
		self.main_box = wx.BoxSizer(wx.VERTICAL)

		# Content warning / spoiler text (not shown for DM-style messages)
		if self.type!="message":
			self.cw_label = wx.StaticText(self.panel, -1, "Content &Warning (optional)")
			self.main_box.Add(self.cw_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
			self.cw = wx.TextCtrl(self.panel, -1, "", style=wx.TE_DONTWRAP, size=text_box_size)
			self.main_box.Add(self.cw, 0, wx.ALL|wx.EXPAND, 10)

		self.text_label = wx.StaticText(self.panel, -1, "Te&xt")
		self.main_box.Add(self.text_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		if globals.prefs.wrap:
			self.text = wx.TextCtrl(self.panel, -1, "",style=wx.TE_MULTILINE,size=big_text_box_size)
		else:
			self.text = wx.TextCtrl(self.panel, -1, "",style=wx.TE_MULTILINE|wx.TE_DONTWRAP,size=big_text_box_size)
		if platform.system()=="Darwin":
			self.text.MacCheckSpelling(True)
		self.main_box.Add(self.text, 1, wx.ALL|wx.EXPAND, 10)
		self.text.SetFocus()
		self.text.Bind(wx.EVT_TEXT, self.Chars)

		if self.type!="message":
			self.text.AppendText(inittext)
			cursorpos=len(inittext)
		else:
			cursorpos=0

		if self.type=="message":
			self.max_length=500
		else:
			self.max_length=getattr(globals.currentAccount,"max_chars",500)

		if self.type=="message":
			self.text2_label = wx.StaticText(self.panel, -1, "Recipient")
			self.main_box.Add(self.text2_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		if self.type=="reply" or self.type=="quote" or self.type=="message":
			if self.type=="message":
				self.text2 = wx.TextCtrl(self.panel, -1, "",style=wx.TE_DONTWRAP,size=text_box_size)
			else:
				self.text2 = wx.TextCtrl(self.panel, -1, "",style=wx.TE_MULTILINE|wx.TE_DONTWRAP|wx.TE_READONLY,size=text_box_size)
			self.main_box.Add(self.text2, 0, wx.ALL|wx.EXPAND, 10)
			if self.type=="message":
				self.text2.AppendText(inittext)
			else:
				cw_prefix=""
				if self.status.spoiler_text:
					cw_prefix="CW: "+self.status.spoiler_text+" — "
				self.text2.AppendText(cw_prefix+self.status.account.acct+": "+self.status.content)
				if self.status.spoiler_text:
					self.cw.SetValue(self.status.spoiler_text)

		if self.account.prefs.footer!="":
			self.text.AppendText(" "+self.account.prefs.footer)
		self.text.SetInsertionPoint(cursorpos)

		if self.type!="message":
			self.visibility_label=wx.StaticText(self.panel, -1, "Visibility")
			self.main_box.Add(self.visibility_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
			self.visibility=wx.Choice(self.panel,-1)
			self.visibility.Insert("Public",self.visibility.GetCount())
			self.visibility.Insert("Unlisted",self.visibility.GetCount())
			self.visibility.Insert("Followers only",self.visibility.GetCount())
			self.visibility.Insert("Direct (mention only)",self.visibility.GetCount())
			self.visibility.SetSelection(0)
			self.main_box.Add(self.visibility, 0, wx.ALL, 10)

		button_row = wx.BoxSizer(wx.HORIZONTAL)
		if platform.system()=="Darwin":
			self.autocomplete = wx.Button(self.panel, wx.ID_DEFAULT, "User A&utocomplete")
		else:
			self.autocomplete = wx.Button(self.panel, wx.ID_DEFAULT, "User &Autocomplete")
		self.autocomplete.Bind(wx.EVT_BUTTON, self.Autocomplete)
		button_row.Add(self.autocomplete, 0, wx.ALL, 5)

		if self.type!="reply" and self.type!="message":
			self.poll_btn = wx.Button(self.panel, wx.ID_DEFAULT, "Poll")
			self.poll_btn.Bind(wx.EVT_BUTTON, self.Poll)
			button_row.Add(self.poll_btn, 0, wx.ALL, 5)

		if self.type=="tweet" or self.type=="reply":
			self.thread=wx.CheckBox(self.panel, -1, "&Thread mode")
			button_row.Add(self.thread, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)

		self.tweet = wx.Button(self.panel, wx.ID_DEFAULT, "&Send")
		self.tweet.Bind(wx.EVT_BUTTON, self.Tweet)
		button_row.Add(self.tweet, 0, wx.ALL, 5)
		self.close = wx.Button(self.panel, wx.ID_CANCEL, "&Cancel")
		self.close.Bind(wx.EVT_BUTTON, self.OnClose)
		button_row.Add(self.close, 0, wx.ALL, 5)
		self.main_box.Add(button_row, 0, wx.ALL|wx.EXPAND, 5)
		self.Chars(None)
		self.text.Bind(wx.EVT_CHAR, self.onKeyPress)
		self.panel.SetSizer(self.main_box)
		self.main_box.Fit(self.panel)
		self.Fit()
		self.SetMinSize(self.GetSize())
		self.Centre()

	def _visibility_value(self):
		sel=self.visibility.GetSelection() if hasattr(self,"visibility") else 0
		return ["public","unlisted","private","direct"][sel]

	def Poll(self,event):
		p=poll.PollGui()
		result=p.ShowModal()
		if result==wx.ID_CANCEL:
			return
		opts=[]
		for opt in [p.opt1.GetValue(),p.opt2.GetValue(),p.opt3.GetValue(),p.opt4.GetValue()]:
			if opt:
				opts.append(opt)
		if len(opts)>=2:
			self.poll_options=opts
			self.poll_runfor=p.runfor.GetValue()*60
			self.poll_btn.Enable(False)

	def onKeyPress(self,event):
		mods = event.HasAnyModifiers()
		keycode = event.GetKeyCode()
		if keycode == wx.WXK_RETURN:
			if not mods:
				self.Tweet(None)
		event.Skip()

	def OnToggle(self,event):
		index=event.GetInt()
		if self.list.IsChecked(index):
			speak.speak("Checked")
		else:
			speak.speak("Unchecked.")

	def Autocomplete(self,event):
		if self.type=="message":
			txt=self.text2.GetValue().split(" ")
		else:
			txt=self.text.GetValue().split(" ")
		text=""
		for i in txt:
			if (self.type!="message" and i.startswith("@") or self.type=="message") and utils.lookup_user_name(self.account,i.strip("@"),False)==-1:
				text=i.strip("@")
		if text=="":
			speak.speak("No user to autocomplete")
			return
		self.menu = wx.Menu()
		for i in globals.users:
			if i.acct.lower().startswith(text.lower()) or i.display_name.lower().startswith(text.lower()):
				self.create_menu_item(self.menu, i.display_name+" (@"+i.acct+")", lambda event, orig=text, text=i.acct: self.OnUser(event,orig,text))
		self.PopupMenu(self.menu)

	def Newline(self,event):
		nl="\n" if platform.system()=="Darwin" else "\r\n"
		self.text.WriteText(nl)

	def create_menu_item(self,menu, label, func):
		item = wx.MenuItem(menu, -1, label)
		menu.Bind(wx.EVT_MENU, func, id=item.GetId())
		menu.Append(item)
		return item

	def OnUser(self,event, orig, text):
		if self.type!="message":
			v=self.text.GetValue().replace(orig,text)
			self.text.SetValue(v)
			self.text.SetInsertionPoint(len(v))
		else:
			v=self.text2.GetValue().replace(orig,text)
			self.text2.SetValue(v)

	def next_thread(self):
		self.text.SetValue("")
		self.text.AppendText(self.inittext)
		cursorpos=len(self.inittext)
		if self.account.prefs.footer!="":
			self.text.AppendText(" "+self.account.prefs.footer)
		self.text.SetInsertionPoint(cursorpos)

	def maximum(self):
		sound.play(self.account,"max_length")

	def Chars(self, event):
		length=len(self.text.GetValue())
		if hasattr(self,"cw"):
			length+=len(self.cw.GetValue())
		if length>0 and self.max_length>0:
			percent=str(int((length/self.max_length)*100))
		else:
			percent="0"
		if self.max_length>0 and length>self.max_length:
			self.maximum()
		self.SetLabel(self.type+" - "+str(length)+" of "+str(self.max_length)+" characters ("+percent+" Percent)")

	def Tweet(self, event):
		snd=""
		status=False
		if self.type!="message":
			visibility=self._visibility_value()
			spoiler=self.cw.GetValue().strip() if hasattr(self,"cw") else ""
			globals.prefs.tweets_sent+=1
			try:
				if self.status is not None:
					if self.type=="quote":
						globals.prefs.quotes_sent+=1
						status=self.account.quote(self.status, self.text.GetValue(), spoiler_text=spoiler or None, visibility=visibility)
					else:
						globals.prefs.replies_sent+=1
						status=self.account.tweet(
							text=self.text.GetValue(),
							id=self.status.id,
							spoiler_text=spoiler or None,
							visibility=visibility,
						)
				else:
					poll_kwargs={}
					if self.poll_options:
						poll_kwargs["poll"]=self.account.api.make_poll(
							options=self.poll_options,
							expires_in=self.poll_runfor or 1440,
						)
					status=self.account.tweet(
						self.text.GetValue(),
						spoiler_text=spoiler or None,
						visibility=visibility,
						**poll_kwargs,
					)
			except MastodonError as e:
				speak.speak(str(e))
				sound.play(self.account,"error")
				return
			globals.prefs.chars_sent+=len(self.text.GetValue())
		else:
			try:
				user=utils.lookup_user_name(self.account, self.text2.GetValue())
				if user != -1:
					status=self.account.tweet("@"+user.acct+" "+self.text.GetValue(), visibility="direct")
				else:
					status=False
			except MastodonError as error:
				sound.play(self.account,"error")
				speak.speak(str(error))
				return

		if self.type=="reply" or self.type=="quote":
			snd="send_reply"
		elif self.type=="tweet":
			snd="send_post"
		elif self.type=="message":
			snd="send_message"
		if status is not False and status is not None:
			sound.play(self.account,snd)
			if hasattr(self,"thread") and not self.thread.GetValue() or not hasattr(self,"thread"):
				self.Destroy()
			else:
				self.status=status
				self.next_thread()
		else:
			sound.play(self.account,"error")

	def OnClose(self, event):
		self.Destroy()
