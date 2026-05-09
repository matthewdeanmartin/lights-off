import wx
from . import misc
from . import view

class ListsGui(wx.Dialog):
	def __init__(self,account,user=None,add=True):
		self.account=account
		self.add=add
		self.user=user
		from lights_off.utils import ensure_attr_access
		self.lists=[ensure_attr_access(i) for i in self.account.api.lists()]
		wx.Dialog.__init__(self, None, title="Lists", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.panel = wx.Panel(self)
		self.main_box = wx.BoxSizer(wx.VERTICAL)
		self.list_label=wx.StaticText(self.panel, -1, label="&Lists")
		self.main_box.Add(self.list_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		self.list=wx.ListBox(self.panel, -1, size=(450,200))
		self.main_box.Add(self.list, 1, wx.ALL|wx.EXPAND, 10)
		self.list.SetFocus()
		self.list.Bind(wx.EVT_LISTBOX, self.on_list_change)
		self.add_items()
		button_row = wx.BoxSizer(wx.HORIZONTAL)
		if self.user is not None:
			if self.add:
				self.load = wx.Button(self.panel, wx.ID_DEFAULT, "&Add")
			else:
				self.load = wx.Button(self.panel, wx.ID_DEFAULT, "&Remove")
		else:
			self.load = wx.Button(self.panel, wx.ID_DEFAULT, "&Load list")
		self.load.SetDefault()
		self.load.Bind(wx.EVT_BUTTON, self.Load)
		self.load.Enable(False)
		button_row.Add(self.load, 0, wx.ALL, 5)
		if len(self.lists)>0:
			self.list.SetSelection(0)
			self.on_list_change(None)
		if self.user is None:
			self.new = wx.Button(self.panel, wx.ID_DEFAULT, "&New list")
			self.new.Bind(wx.EVT_BUTTON, self.New)
			button_row.Add(self.new, 0, wx.ALL, 5)
			self.edit = wx.Button(self.panel, wx.ID_DEFAULT, "&Edit list")
			self.edit.Bind(wx.EVT_BUTTON, self.Edit)
			button_row.Add(self.edit, 0, wx.ALL, 5)
			if len(self.lists)==0:
				self.edit.Enable(False)
			self.view_members = wx.Button(self.panel, wx.ID_DEFAULT, "&View list members")
			self.view_members.Bind(wx.EVT_BUTTON, self.ViewMembers)
			button_row.Add(self.view_members, 0, wx.ALL, 5)
			if len(self.lists)==0:
				self.view_members.Enable(False)
			self.remove = wx.Button(self.panel, wx.ID_DEFAULT, "&Remove list")
			self.remove.Bind(wx.EVT_BUTTON, self.Remove)
			button_row.Add(self.remove, 0, wx.ALL, 5)
			if len(self.lists)==0:
				self.remove.Enable(False)
		self.close = wx.Button(self.panel, wx.ID_CANCEL, "&Cancel")
		self.close.Bind(wx.EVT_BUTTON, self.OnClose)
		button_row.Add(self.close, 0, wx.ALL, 5)
		self.main_box.Add(button_row, 0, wx.ALL|wx.EXPAND, 5)
		self.panel.SetSizer(self.main_box)
		self.main_box.Fit(self.panel)
		self.Fit()
		self.SetMinSize(self.GetSize())
		self.Centre()

	def add_items(self):
		for i in self.lists:
			self.list.Insert(i.title, self.list.GetCount())
		if len(self.lists)>0:
			self.list.SetSelection(0)
		else:
			if hasattr(self,"load"):
				self.load.Enable(False)
			if hasattr(self,"edit"):
				self.edit.Enable(False)
			if hasattr(self,"remove"):
				self.remove.Enable(False)

	def on_list_change(self,event):
		self.load.Enable(True)
		if hasattr(self,"edit"):
			self.edit.Enable(True)
		if hasattr(self,"remove"):
			self.remove.Enable(True)

	def New(self, event):
		gui=NewListGui(self.account)
		gui.Show()

	def Edit(self, event):
		gui=NewListGui(self.account,self.lists[self.list.GetSelection()])
		gui.Show()

	def Remove(self, event):
		self.account.api.list_delete(self.lists[self.list.GetSelection()].id)
		self.lists.remove(self.lists[self.list.GetSelection()])
		self.list.Clear()
		self.add_items()

	def ViewMembers(self, event):
		lst=self.lists[self.list.GetSelection()]
		members=self.account.api.list_accounts(lst.id)
		v=view.UserViewGui(self.account,members,"List members")
		v.Show()

	def Load(self, event):
		if self.user is None:
			misc.list_timeline(self.account,self.lists[self.list.GetSelection()].title, self.lists[self.list.GetSelection()].id)
		else:
			if self.add:
				self.account.api.list_accounts_add(self.lists[self.list.GetSelection()].id, [self.user.id])
			else:
				self.account.api.list_accounts_delete(self.lists[self.list.GetSelection()].id, [self.user.id])
		self.Destroy()

	def OnClose(self, event):
		self.Destroy()

class NewListGui(wx.Dialog):
	def __init__(self,account,list=None):
		self.account=account
		self.list=list
		title="New list"
		if list is not None:
			title="Edit list "+list.title
		wx.Dialog.__init__(self, None, title=title, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.panel = wx.Panel(self)
		self.main_box = wx.BoxSizer(wx.VERTICAL)
		self.text_label = wx.StaticText(self.panel, -1, "Name of list")
		self.main_box.Add(self.text_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		self.text = wx.TextCtrl(self.panel, -1, "",style=wx.TE_PROCESS_ENTER|wx.TE_DONTWRAP, size=(400,-1))
		self.main_box.Add(self.text, 0, wx.ALL|wx.EXPAND, 10)
		self.text.SetFocus()
		if list is not None:
			self.text.SetValue(self.list.title)
		self.type_label = wx.StaticText(self.panel, -1, "Reply policy")
		self.main_box.Add(self.type_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
		self.type = wx.ComboBox(self.panel, -1, "",style=wx.CB_READONLY)
		self.type.Insert("followed",0)
		self.type.Insert("list",1)
		self.type.Insert("none",2)
		self.type.SetSelection(0)
		self.main_box.Add(self.type, 0, wx.ALL|wx.EXPAND, 10)
		button_row = wx.BoxSizer(wx.HORIZONTAL)
		if self.list is not None:
			self.create = wx.Button(self.panel, wx.ID_DEFAULT, "&Edit list")
		else:
			self.create = wx.Button(self.panel, wx.ID_DEFAULT, "&Create list")
		self.create.SetDefault()
		self.create.Bind(wx.EVT_BUTTON, self.Create)
		button_row.Add(self.create, 0, wx.ALL, 5)
		self.close = wx.Button(self.panel, wx.ID_CANCEL, "&Cancel")
		self.close.Bind(wx.EVT_BUTTON, self.OnClose)
		button_row.Add(self.close, 0, wx.ALL, 5)
		self.main_box.Add(button_row, 0, wx.ALL|wx.ALIGN_RIGHT, 5)
		self.panel.SetSizer(self.main_box)
		self.main_box.Fit(self.panel)
		self.Fit()
		self.SetMinSize(self.GetSize())
		self.Centre()

	def Create(self, event):
		reply_policy=self.type.GetString(self.type.GetSelection())
		if self.list is None:
			self.account.api.list_create(self.text.GetValue(), replies_policy=reply_policy)
		else:
			self.account.api.list_update(self.list.id, self.text.GetValue(), replies_policy=reply_policy)
		self.Destroy()

	def OnClose(self, event):
		self.Destroy()
