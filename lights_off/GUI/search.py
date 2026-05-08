import wx
from lights_off import globals
from . import misc

class SearchGui(wx.Dialog):
	def __init__(self,account, type="search"):
		self.account=account
		self.type=type
		wx.Dialog.__init__(self, None, title="Search", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.panel = wx.Panel(self)
		self.main_box = wx.BoxSizer(wx.VERTICAL)
		self.text_label = wx.StaticText(self.panel, -1, "Search text")
		self.main_box.Add(self.text_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		self.text = wx.TextCtrl(self.panel, -1, "",style=wx.TE_PROCESS_ENTER|wx.TE_DONTWRAP, size=(400,-1))
		self.main_box.Add(self.text, 0, wx.ALL|wx.EXPAND, 10)
		self.text.SetFocus()
		self.text.Bind(wx.EVT_TEXT_ENTER, self.Search)
		button_row = wx.BoxSizer(wx.HORIZONTAL)
		self.search = wx.Button(self.panel, wx.ID_DEFAULT, "&Search")
		self.search.SetDefault()
		self.search.Bind(wx.EVT_BUTTON, self.Search)
		button_row.Add(self.search, 0, wx.ALL, 5)
		self.close = wx.Button(self.panel, wx.ID_CANCEL, "&Cancel")
		self.close.Bind(wx.EVT_BUTTON, self.OnClose)
		button_row.Add(self.close, 0, wx.ALL, 5)
		self.main_box.Add(button_row, 0, wx.ALL|wx.ALIGN_RIGHT, 5)
		self.panel.SetSizer(self.main_box)
		self.main_box.Fit(self.panel)
		self.Fit()
		self.SetMinSize(self.GetSize())
		self.Centre()

	def Search(self, event):
		if self.type=="search":
			misc.search(self.account,self.text.GetValue())
		else:
			misc.user_search(self.account,self.text.GetValue())
		self.Destroy()

	def OnClose(self, event):
		self.Destroy()
