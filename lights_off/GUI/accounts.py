from lights_off import application
import wx
from lights_off import globals
from . import main

class AccountsGui(wx.Dialog):
	def __init__(self):
		wx.Dialog.__init__(self, None, title="Accounts", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.panel = wx.Panel(self)
		self.main_box = wx.BoxSizer(wx.VERTICAL)
		self.list_label=wx.StaticText(self.panel, -1, label="&Accounts")
		self.main_box.Add(self.list_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		self.list=wx.ListBox(self.panel, -1, size=(400,200))
		self.main_box.Add(self.list, 1, wx.ALL|wx.EXPAND, 10)
		self.list.SetFocus()
		self.list.Bind(wx.EVT_LISTBOX, self.on_list_change)
		self.add_items()
		button_row = wx.BoxSizer(wx.HORIZONTAL)
		self.load = wx.Button(self.panel, wx.ID_DEFAULT, "&Switch")
		self.load.SetDefault()
		self.load.Bind(wx.EVT_BUTTON, self.Load)
		button_row.Add(self.load, 0, wx.ALL, 5)
		self.new = wx.Button(self.panel, wx.ID_DEFAULT, "&Add account")
		self.new.Bind(wx.EVT_BUTTON, self.New)
		button_row.Add(self.new, 0, wx.ALL, 5)
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
		index=0
		for i in globals.accounts:
			self.list.Insert(i.me.acct,self.list.GetCount())
			if i==globals.currentAccount:
				self.list.SetSelection(index)
			index+=1

	def on_list_change(self,event):
		pass

	def New(self, event):
		globals.add_session()
		globals.prefs.accounts+=1
		globals.currentAccount=globals.accounts[len(globals.accounts)-1]
		main.window.refreshTimelines()
		main.window.on_list_change(None)
		main.window.SetLabel(globals.currentAccount.me.acct+" - "+application.name+" "+application.version)
		self.Destroy()

	def Load(self, event):
		globals.currentAccount=globals.accounts[self.list.GetSelection()]
		main.window.refreshTimelines()
		main.window.list.SetSelection(globals.currentAccount.currentIndex)
		main.window.on_list_change(None)
		main.window.SetLabel(globals.currentAccount.me.acct+" - "+application.name+" "+application.version)
		self.Destroy()

	def OnClose(self, event):
		self.Destroy()
