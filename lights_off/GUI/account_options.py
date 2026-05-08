from sound_lib import stream
import platform
import os, sys
from lights_off import globals
import wx
from . import main

class general(wx.Panel, wx.Dialog):
	def __init__(self, account, parent):
		_boundary = globals.confpath+"/sounds/default/boundary.ogg"
		if not os.path.exists(_boundary):
			from importlib.resources import files, as_file
			with as_file(files("lights_off").joinpath("sounds/default/boundary.ogg")) as p:
				_boundary = str(p)
		self.snd = stream.FileStream(file=_boundary)
		self.account=account
		super(general, self).__init__(parent)
		self.main_box = wx.BoxSizer(wx.VERTICAL)
		self.soundpacklist_label=wx.StaticText(self, -1, "Soundpacks")
		self.main_box.Add(self.soundpacklist_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		self.soundpackslist = wx.ListBox(self, -1, size=(400,150))
		self.main_box.Add(self.soundpackslist, 1, wx.ALL|wx.EXPAND, 10)
		self.soundpackslist.Bind(wx.EVT_LISTBOX, self.on_soundpacks_list_change)
		dirs = os.listdir(globals.confpath+"/sounds")
		for i in range(0,len(dirs)):
			if not dirs[i].startswith("_") and not dirs[i].startswith(".DS"):
				self.soundpackslist.Insert(dirs[i],self.soundpackslist.GetCount())
				if account.prefs.soundpack==dirs[i]:
					self.soundpackslist.SetSelection(self.soundpackslist.GetCount()-1)
					self.sp=dirs[i]
		try:
			dirs2 = os.listdir("sounds")
			for i in range(0,len(dirs2)):
				if not dirs2[i].startswith("_") and not dirs2[i].startswith(".DS") and dirs2[i] not in dirs:
					self.soundpackslist.Insert(dirs2[i],self.soundpackslist.GetCount())
					if account.prefs.soundpack==dirs2[i]:
						self.soundpackslist.SetSelection(self.soundpackslist.GetCount()-1)
						self.sp=dirs2[i]
		except:
			pass
		if not hasattr(self,"sp"):
			self.sp="default"
		instance_url=getattr(account.prefs,"instance","")
		if instance_url:
			self.instance_label=wx.StaticText(self, -1, "Instance: "+instance_url)
			self.main_box.Add(self.instance_label, 0, wx.ALL, 10)
		self.pan_label = wx.StaticText(self, -1, "Sound pan")
		self.main_box.Add(self.pan_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		self.soundpan = wx.Slider(self, -1, int(self.account.prefs.soundpan*50),-50,50,name="Soundpack Pan")
		self.soundpan.Bind(wx.EVT_SLIDER,self.OnPan)
		self.main_box.Add(self.soundpan, 0, wx.ALL|wx.EXPAND, 10)
		self.footer_label = wx.StaticText(self, -1, "Post Footer (Optional)")
		self.main_box.Add(self.footer_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		self.footer = wx.TextCtrl(self, -1, "",style=wx.TE_MULTILINE, size=(500,80))
		self.main_box.Add(self.footer, 1, wx.ALL|wx.EXPAND, 10)
		self.footer.AppendText(account.prefs.footer)
		self.footer.SetMaxLength(500)
		self.SetSizer(self.main_box)

	def OnPan(self,event):
		pan=self.soundpan.GetValue()/50
		self.snd.pan=pan
		self.snd.play()

	def on_soundpacks_list_change(self, event):
		self.sp=event.GetString()

class OptionsGui(wx.Dialog):
	def __init__(self,account):
		self.account=account
		wx.Dialog.__init__(self, None, title="Account Options for "+self.account.me.acct, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.panel = wx.Panel(self)
		self.main_box = wx.BoxSizer(wx.VERTICAL)
		self.notebook = wx.Notebook(self.panel)
		self.general=general(self.account, self.notebook)
		self.notebook.AddPage(self.general, "General")
		self.general.SetFocus()
		self.main_box.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 10)
		button_row = wx.BoxSizer(wx.HORIZONTAL)
		self.ok = wx.Button(self.panel, wx.ID_OK, "&OK")
		self.ok.SetDefault()
		self.ok.Bind(wx.EVT_BUTTON, self.OnOK)
		button_row.Add(self.ok, 0, wx.ALL, 5)
		self.close = wx.Button(self.panel, wx.ID_CANCEL, "&Cancel")
		self.close.Bind(wx.EVT_BUTTON, self.OnClose)
		button_row.Add(self.close, 0, wx.ALL, 5)
		self.main_box.Add(button_row, 0, wx.ALL|wx.ALIGN_RIGHT, 5)
		self.panel.SetSizer(self.main_box)
		self.main_box.Fit(self.panel)
		self.Fit()
		self.SetMinSize(self.GetSize())
		self.Centre()

	def OnOK(self, event):
		self.account.prefs.soundpack=self.general.sp
		self.account.prefs.soundpan=self.general.soundpan.GetValue()/50
		self.account.prefs.footer=self.general.footer.GetValue()
		self.general.snd.free()
		self.Destroy()

	def OnClose(self, event):
		self.general.snd.free()
		self.Destroy()
