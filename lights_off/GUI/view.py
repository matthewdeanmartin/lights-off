import requests
import platform
from lights_off import globals
from . import misc
import wx
from lights_off import utils
text_box_size=(600,250)
small_text_box_size=(600,150)

def _humanize(n):
	import math
	n = int(n or 0)
	if n == 0:
		return "0"
	if n >= 1_000_000:
		return f"{n/1_000_000:.1f}M"
	if n >= 10_000:
		return f"{n//1_000}K"
	if n >= 1_000:
		return f"{n/1_000:.1f}K"
	if n >= 10:
		magnitude = 10 ** (math.floor(math.log10(n)) - 1)
		return str(round(n / magnitude) * magnitude)
	return str(n)

class ViewGui(wx.Dialog):

	def __init__(self,account,status):
		self.account=account
		self.status=utils.ensure_attr_access(status)
		self.tweet_text=utils.process_tweet(self.status,True)
		self.type="post"
		wx.Dialog.__init__(self, None, title="View post from "+utils.strip_display_name(status.account.display_name, status.account.acct)+" ("+status.account.acct+")", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.panel = wx.Panel(self)
		self.main_box = wx.BoxSizer(wx.VERTICAL)
		self.text_label = wx.StaticText(self.panel, -1, "Te&xt")
		self.main_box.Add(self.text_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		if globals.prefs.wrap:
			self.text = wx.TextCtrl(self.panel, style=wx.TE_READONLY|wx.TE_MULTILINE, size=text_box_size)
		else:
			self.text = wx.TextCtrl(self.panel, style=wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_DONTWRAP, size=text_box_size)
		self.main_box.Add(self.text, 1, wx.ALL|wx.EXPAND, 10)
		self.text.SetFocus()
		self.text.SetValue(self.tweet_text)

		self.text2_label = wx.StaticText(self.panel, -1, "Post &Details")
		self.main_box.Add(self.text2_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		self.text2 = wx.TextCtrl(self.panel, style=wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_DONTWRAP, size=small_text_box_size)
		self.main_box.Add(self.text2, 0, wx.ALL|wx.EXPAND, 10)
		extra=""
		if self.status.spoiler_text:
			extra += "Content warning: " + self.status.spoiler_text + "\r\n"
		if self.status.media_attachments:
			for idx, m in enumerate(self.status.media_attachments, 1):
				extra += "Media "+str(idx)+": "+m.type+"\r\n"
				if m.description:
					extra += "Description: "+m.description+"\r\n"
		posted=utils.parse_date(self.status.created_at)
		if posted:
			extra+="Posted: "+posted+"\r\n"
		self.text2.SetValue(
			extra +
			"Favourited "+_humanize(self.status.favourites_count)+" times\r\n"+
			"Boosted "+_humanize(self.status.reblogs_count)+" times."
		)
		if platform.system()=="Darwin":
			self.text2.SetValue(self.text2.GetValue().replace("\r",""))

		btn_grid = wx.GridSizer(rows=0, cols=4, vgap=4, hgap=4)

		self.view_orig = wx.Button(self.panel, -1, "&Original post")
		self.view_orig.Bind(wx.EVT_BUTTON, self.OnViewOrig)
		btn_grid.Add(self.view_orig, 0, wx.EXPAND)
		if not self.status.reblog:
			self.view_orig.Enable(False)

		self.view_image = wx.Button(self.panel, -1, "&View Image")
		self.view_image.Bind(wx.EVT_BUTTON, self.OnViewImage)
		btn_grid.Add(self.view_image, 0, wx.EXPAND)
		if not self.status.media_attachments:
			self.view_image.Enable(False)

		self.reply = wx.Button(self.panel, -1, "&Reply")
		self.reply.Bind(wx.EVT_BUTTON, self.OnReply)
		btn_grid.Add(self.reply, 0, wx.EXPAND)

		self.retweet = wx.Button(self.panel, -1, "&Boost")
		self.retweet.Bind(wx.EVT_BUTTON, self.OnRetweet)
		btn_grid.Add(self.retweet, 0, wx.EXPAND)

		self.like = wx.Button(self.panel, -1, "&Favourite")
		self.like.Bind(wx.EVT_BUTTON, self.OnLike)
		btn_grid.Add(self.like, 0, wx.EXPAND)

		extra_users = utils.get_user_objects_in_tweet(self.account, self.status, True, True)
		_name=utils.strip_display_name(self.status.account.display_name, self.status.account.acct)
		if len(extra_users) > 0:
			self.profile = wx.Button(self.panel, -1, "View &Profile of "+_name+" and "+str(len(extra_users))+" more")
		else:
			self.profile = wx.Button(self.panel, -1, "View &Profile of "+_name)
		self.profile.Bind(wx.EVT_BUTTON, self.OnProfile)
		btn_grid.Add(self.profile, 0, wx.EXPAND)

		self.message = wx.Button(self.panel, -1, "&Message "+_name)
		self.message.Bind(wx.EVT_BUTTON, self.OnMessage)
		btn_grid.Add(self.message, 0, wx.EXPAND)

		self.close = wx.Button(self.panel, wx.ID_CANCEL, "&Close")
		self.close.Bind(wx.EVT_BUTTON, self.OnClose)
		btn_grid.Add(self.close, 0, wx.EXPAND)
		self.main_box.Add(btn_grid, 0, wx.ALL|wx.EXPAND, 10)
		self.panel.SetSizer(self.main_box)
		self.main_box.Fit(self.panel)
		self.Fit()
		self.SetMinSize(self.GetSize())
		self.Centre()

	def OnViewOrig(self,event):
		if self.status.reblog:
			v=ViewGui(self.account,self.status.reblog)
			v.Show()

	def OnViewImage(self,event):
		v=ViewImageGui(self.status)
		v.Show()

	def OnReply(self,event):
		misc.reply(self.account,self.status)

	def OnRetweet(self,event):
		misc.retweet(self.account,self.status)

	def OnLike(self,event):
		misc.like(self.account,self.status)

	def OnProfile(self,event):
		u=[self.status.account]
		u2=utils.get_user_objects_in_tweet(self.account,self.status,True,True)
		for i in u2:
			u.append(i)
		g=UserViewGui(self.account,u)
		g.Show()

	def OnMessage(self,event):
		misc.message(self.account,self.status)

	def OnClose(self, event):
		self.Destroy()


class UserViewGui(wx.Dialog):

	def __init__(self,account,users=[],title="User Viewer"):
		self.account=account
		self.index=0
		self.users=users
		wx.Dialog.__init__(self, None, title=title, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.panel = wx.Panel(self)
		self.main_box = wx.BoxSizer(wx.VERTICAL)
		self.list_label=wx.StaticText(self.panel, -1, label="&Users")
		self.main_box.Add(self.list_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		self.list=wx.ListBox(self.panel, -1, size=(600,150))
		self.main_box.Add(self.list, 0, wx.ALL|wx.EXPAND, 10)
		self.list.Bind(wx.EVT_LISTBOX, self.on_list_change)
		for i in self.users:
			if i is None:
				continue
			extra=""
			if getattr(i,"locked",False):
				extra+=", Protected"
			if getattr(i,"following",False):
				extra+=", You follow"
			note=getattr(i,"note","") or ""
			if note:
				extra+=", "+utils.strip_bio(note)[:80]
			self.list.Insert(utils.strip_display_name(i.display_name, i.acct)+" (@"+i.acct+")"+extra,self.list.GetCount())
		self.index=0
		if len(self.users)==0:
			self.list.Show(False)
		elif len(self.users)==1:
			self.list.SetSelection(0)
			self.list.Show(False)
		else:
			self.list.SetSelection(0)
			self.list.SetFocus()
		self.text_label = wx.StaticText(self.panel, -1, "Info")
		self.main_box.Add(self.text_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		self.text = wx.TextCtrl(self.panel, style=wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_DONTWRAP, size=(600,200))
		self.main_box.Add(self.text, 1, wx.ALL|wx.EXPAND, 10)
		if len(self.users)<=1:
			self.text.SetFocus()
		btn_grid = wx.GridSizer(rows=0, cols=4, vgap=4, hgap=4)
		self.follow = wx.Button(self.panel, -1, "&Follow")
		self.follow.Bind(wx.EVT_BUTTON, self.OnFollow)
		btn_grid.Add(self.follow, 0, wx.EXPAND)
		self.unfollow = wx.Button(self.panel, -1, "&Unfollow")
		self.unfollow.Bind(wx.EVT_BUTTON, self.OnUnfollow)
		btn_grid.Add(self.unfollow, 0, wx.EXPAND)
		self.message = wx.Button(self.panel, -1, "&Message")
		self.message.Bind(wx.EVT_BUTTON, self.OnMessage)
		btn_grid.Add(self.message, 0, wx.EXPAND)
		self.timeline = wx.Button(self.panel, -1, "&Timeline")
		self.timeline.Bind(wx.EVT_BUTTON, self.OnTimeline)
		btn_grid.Add(self.timeline, 0, wx.EXPAND)
		self.image = wx.Button(self.panel, -1, "View Profile Ima&ge")
		self.image.Bind(wx.EVT_BUTTON, self.OnImage)
		btn_grid.Add(self.image, 0, wx.EXPAND)
		self.followers = wx.Button(self.panel, -1, "View Fo&llowers")
		self.followers.Bind(wx.EVT_BUTTON, self.OnFollowers)
		btn_grid.Add(self.followers, 0, wx.EXPAND)
		self.friends = wx.Button(self.panel, -1, "View F&riends")
		self.friends.Bind(wx.EVT_BUTTON, self.OnFriends)
		btn_grid.Add(self.friends, 0, wx.EXPAND)
		self.follow.Enable(False)
		self.unfollow.Enable(False)
		self.timeline.Enable(False)
		self.message.Enable(False)
		self.close = wx.Button(self.panel, wx.ID_CANCEL, "&Close")
		self.close.Bind(wx.EVT_BUTTON, self.OnClose)
		btn_grid.Add(self.close, 0, wx.EXPAND)
		self.main_box.Add(btn_grid, 0, wx.ALL|wx.EXPAND, 10)
		self.on_list_change(None)
		menu = wx.Menu()
		m_speak_user=menu.Append(-1, "Speak user", "speak")
		self.Bind(wx.EVT_MENU, self.OnSpeakUser, m_speak_user)
		accel=[]
		accel.append((wx.ACCEL_CTRL, ord(';'), m_speak_user.GetId()))
		accel_tbl=wx.AcceleratorTable(accel)
		self.SetAcceleratorTable(accel_tbl)
		self.panel.SetSizer(self.main_box)
		self.main_box.Fit(self.panel)
		self.Fit()
		self.SetMinSize(self.GetSize())
		self.Centre()

	def OnSpeakUser(self,event):
		self.index=self.list.GetSelection()
		user=self.users[self.index].acct
		utils.speak_user(globals.currentAccount,[user])

	def on_list_change(self,event):
		if not self.users:
			self.text.SetValue("No users found.")
			return
		self.index=max(0,self.list.GetSelection())
		user=self.users[self.index]
		if getattr(user,"following",False):
			self.unfollow.Enable(True)
			self.follow.Enable(False)
		else:
			self.unfollow.Enable(False)
			self.follow.Enable(True)
		self.message.Enable(True)
		self.timeline.Enable(True)

		extra=""
		url=getattr(user,"url","") or ""
		if url:
			extra+="\r\nURL: "+url
		last_status=getattr(user,"last_status_at",None)
		if last_status:
			extra+="\r\nLast posted: "+utils.parse_date(last_status)
		info=(
			"Display Name: "+utils.strip_display_name(user.display_name, user.acct)+"\r\n"+
			"Account: @"+user.acct+"\r\n"+
			"Bio: "+utils.strip_bio(getattr(user,"note",""))+extra+"\r\n"+
			"Followers: "+_humanize(user.followers_count)+"\r\n"+
			"Following: "+_humanize(user.following_count)+"\r\n"+
			"Posts: "+_humanize(user.statuses_count)+"\r\n"+
			"Created: "+utils.parse_date(user.created_at)+"\r\n"+
			"Locked: "+str(getattr(user,"locked",False))+"\r\n"+
			"Following: "+str(getattr(user,"following",False))
		)
		self.text.SetValue(info)
		if platform.system()=="Darwin":
			self.text.SetValue(self.text.GetValue().replace("\r",""))

	def OnFollow(self,event):
		user=self.users[self.index]
		misc.follow_user(self.account,user.acct)

	def OnUnfollow(self,event):
		user=self.users[self.index]
		misc.unfollow_user(self.account,user.acct)

	def OnFollowers(self,event):
		user=self.users[self.index]
		misc.followers(self.account,user.id)

	def OnFriends(self,event):
		user=self.users[self.index]
		misc.friends(self.account,user.id)

	def OnMessage(self,event):
		user=self.users[self.index]
		misc.message_user(self.account,user.acct)

	def OnTimeline(self,event):
		user=self.users[self.index]
		misc.user_timeline_user(self.account,user.acct)

	def OnImage(self,event):
		user=self.users[self.index]
		v=ViewImageGui(user)
		v.Show()

	def OnClose(self, event):
		self.Destroy()


class ViewTextGui(wx.Dialog):

	def __init__(self,text):
		wx.Dialog.__init__(self, None, title="Text", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.panel = wx.Panel(self)
		self.main_box = wx.BoxSizer(wx.VERTICAL)
		self.text_label = wx.StaticText(self.panel, -1, "Te&xt")
		self.main_box.Add(self.text_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		self.text = wx.TextCtrl(self.panel, style=wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_DONTWRAP, size=(600,300))
		self.main_box.Add(self.text, 1, wx.ALL|wx.EXPAND, 10)
		self.text.SetValue(text)
		self.close = wx.Button(self.panel, wx.ID_CANCEL, "&Close")
		self.close.Bind(wx.EVT_BUTTON, self.OnClose)
		self.main_box.Add(self.close, 0, wx.ALL|wx.ALIGN_RIGHT, 10)
		self.panel.SetSizer(self.main_box)
		self.main_box.Fit(self.panel)
		self.Fit()
		self.SetMinSize(self.GetSize())
		self.Centre()

	def OnClose(self, event):
		self.Destroy()


class ViewImageGui(wx.Dialog):

	def __init__(self,status):
		self.url=None
		if hasattr(status,"avatar") and status.avatar:
			self.url=status.avatar
		elif hasattr(status,"media_attachments") and status.media_attachments:
			self.url=status.media_attachments[0].url
		if not self.url:
			return
		image=requests.get(self.url)
		f=open(globals.confpath+"/temp_image","wb")
		f.write(image.content)
		f.close()
		self.image=wx.Image(globals.confpath+"/temp_image",wx.BITMAP_TYPE_ANY).ConvertToBitmap()
		self.size=(self.image.GetWidth(), self.image.GetHeight())
		wx.Dialog.__init__(self, None, title="Image", size=self.size)
		self.SetClientSize(self.size)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.panel = wx.Panel(self)
		self.text_label = wx.StaticText(self.panel, -1, "Image")
		self.text = wx.StaticBitmap(self.panel, -1, self.image, (10, 5), self.size)
		self.close = wx.Button(self.panel, wx.ID_CANCEL, "&Close")
		self.close.Bind(wx.EVT_BUTTON, self.OnClose)
		self.panel.Layout()

	def OnClose(self, event):
		self.Destroy()
