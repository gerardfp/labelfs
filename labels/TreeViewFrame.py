from gi.repository import Gtk, Gdk

class TreeViewFrame(Gtk.Frame):
  def __init__(self):
    Gtk.Frame.__init__(self)
    self.set_shadow_type(Gtk.ShadowType.NONE)
    self.get_style_context().add_class("tree-view-frame")    

    self.table = Gtk.Table(2,1,False) 
    self.add(self.table)

    self.new_node_bar = NewNodeBar()
    self.table.attach(self.new_node_bar,0,1,0,1,Gtk.AttachOptions.FILL,Gtk.AttachOptions.FILL)

    self.tree_view = TreeView()
    self.win = Gtk.ScrolledWindow()
    self.win.add(self.tree_view)
    self.table.attach(self.win,0,1,1,2)

class TreeView(Gtk.TreeView):
  def __init__(self):
    Gtk.TreeView.__init__(self)
    self.get_style_context().add_class("tree-view")    

    self.tree_store = Gtk.TreeStore(str)
    self.set_model(self.tree_store)
    
    treeviewcolumn = Gtk.TreeViewColumn("Label")
    self.append_column(treeviewcolumn)
    cellrenderertext = Gtk.CellRendererText()
    treeviewcolumn.pack_start(cellrenderertext, False)
    treeviewcolumn.add_attribute(cellrenderertext, "text", 0)
    
    self.selection = self.get_selection()
    self.selection.set_mode(Gtk.SelectionMode.BROWSE)

    self.set_size_request(200, -1)
    self.set_headers_visible(False)
        
    self.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK,
                  [('text/plain', 0, 0)],
                  Gdk.DragAction.DEFAULT | Gdk.DragAction.MOVE)

class NewNodeBar(Gtk.Box):
  def __init__(self):
    Gtk.Toolbar.__init__(self)
    self.get_style_context().add_class("new-node-bar")
    self.new_label_entry=NewLabelEntry()
    self.add(self.new_label_entry)
    self.new_file_entry=NewFileEntry()
    self.add(self.new_file_entry)

class NewLabelEntry(Gtk.Entry):
  def __init__(self):
    Gtk.Entry.__init__(self)
    self.get_style_context().add_class("new-label-entry")

    self.set_placeholder_text("NEW LABEL")
    self.set_width_chars(9)
    
class NewFileEntry(Gtk.Entry):
  def __init__(self):
    Gtk.Entry.__init__(self)
    self.get_style_context().add_class("new-file-entry")
 
    self.set_placeholder_text("new file")
    self.set_width_chars(11)


