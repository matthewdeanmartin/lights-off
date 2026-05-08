import wx

class HiddenTimelinesGui(wx.Dialog):
	def __init__(self,account):
		self.account=account
		wx.Dialog.__init__(self, None, title="Hidden timelines", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.panel = wx.Panel(self)
		self.main_box = wx.BoxSizer(wx.VERTICAL)
		self.list_label=wx.StaticText(self.panel, -1, label="&Timelines")
		self.main_box.Add(self.list_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		self.list=wx.ListBox(self.panel, -1, size=(400,200))
		self.main_box.Add(self.list, 1, wx.ALL|wx.EXPAND, 10)
		self.list.SetFocus()
		self.list.Bind(wx.EVT_LISTBOX, self.on_list_change)
		self.add_items()
		button_row = wx.BoxSizer(wx.HORIZONTAL)
		self.load = wx.Button(self.panel, wx.ID_DEFAULT, "&Unhide")
		self.load.SetDefault()
		self.load.Bind(wx.EVT_BUTTON, self.Load)
		button_row.Add(self.load, 0, wx.ALL, 5)
		self.close = wx.Button(self.panel, wx.ID_CANCEL, "&Cancel")
		self.close.Bind(wx.EVT_BUTTON, self.OnClose)
		button_row.Add(self.close, 0, wx.ALL, 5)
		self.main_box.Add(button_row, 0, wx.ALL|wx.ALIGN_RIGHT, 5)
		self.panel.SetSizer(self.main_box)
		self.main_box.Fit(self.panel)
		self.Fit()
		self.SetMinSize(self.GetSize())
		self.Centre()

	def add_items(self):
		for i in self.account.list_timelines(True):
			self.list.Insert(i.name,self.list.GetCount())
		self.list.SetSelection(0)

	def on_list_change(self,event):
		self.load.Enable(True)

	def Load(self, event):
		self.account.list_timelines(True)[self.list.GetSelection()].unhide_tl()
		self.list.Delete(self.list.GetSelection())

	def OnClose(self, event):
		self.Destroy()
