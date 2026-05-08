import wx
from html.parser import HTMLParser

def _strip_html(raw):
	class S(HTMLParser):
		def __init__(self):
			super().__init__()
			self.parts=[]
		def handle_data(self,d):
			self.parts.append(d)
	s=S()
	s.feed(raw or "")
	return "".join(s.parts)

class ProfileGui(wx.Dialog):

	def __init__(self, account):
		self.account=account
		s=account.api.me()
		wx.Dialog.__init__(self, None, title="Profile Editor", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.panel = wx.Panel(self)
		self.main_box = wx.BoxSizer(wx.VERTICAL)
		self.name_label = wx.StaticText(self.panel, -1, "Display Name")
		self.main_box.Add(self.name_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		self.name = wx.TextCtrl(self.panel, -1, "", size=(400,-1))
		self.main_box.Add(self.name, 0, wx.ALL|wx.EXPAND, 10)
		self.name.SetFocus()
		if s.display_name:
			self.name.SetValue(s.display_name)
		self.description_label = wx.StaticText(self.panel, -1, "Bio")
		self.main_box.Add(self.description_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		self.description = wx.TextCtrl(self.panel, -1, "", style=wx.TE_MULTILINE, size=(400,200))
		self.main_box.Add(self.description, 1, wx.ALL|wx.EXPAND, 10)
		if s.note:
			self.description.SetValue(_strip_html(s.note))
		button_row = wx.BoxSizer(wx.HORIZONTAL)
		self.update = wx.Button(self.panel, wx.ID_DEFAULT, "&Update")
		self.update.SetDefault()
		self.update.Bind(wx.EVT_BUTTON, self.Update)
		button_row.Add(self.update, 0, wx.ALL, 5)
		self.close = wx.Button(self.panel, wx.ID_CANCEL, "&Cancel")
		self.close.Bind(wx.EVT_BUTTON, self.OnClose)
		button_row.Add(self.close, 0, wx.ALL, 5)
		self.main_box.Add(button_row, 0, wx.ALL|wx.ALIGN_RIGHT, 5)
		self.panel.SetSizer(self.main_box)
		self.main_box.Fit(self.panel)
		self.Fit()
		self.SetMinSize(self.GetSize())
		self.Centre()

	def Update(self, event):
		self.account.UpdateProfile(self.name.GetValue(), "", self.description.GetValue())
		self.Destroy()

	def OnClose(self, event):
		self.Destroy()
