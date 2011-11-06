#!/usr/bin/python
from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, Pango, GObject
import os
from os.path import realpath,isfile,isdir,basename,dirname,join,exists,normpath,expanduser,abspath
import lfsengine
import random


le = lfsengine.LfsEngine("%s/.lfs.db" % expanduser('~'))

# MODEL

#Signals

class CustomSignals(GObject.GObject):
    __gsignals__ = {
        'node-created': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_STRING,))
        ,'nodes-selected': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_STRING,))
        ,'current-treepath-changed': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_INT,))
    }
Signals = CustomSignals()

globals = {}
# GUI ELEMENTS

def pathlist(path):
  return [node for node in path.split('/') if node != ""]


class SelectedNodePanel(Gtk.Box):
  def __init__(self):
    Gtk.Box.__init__(self)
    self.get_style_context().add_class("selected-node-panel")    

    self.set_size_request(180,-1)    
    

    Signals.connect('nodes-selected',self.on_node_selected)
    
  def on_node_selected(self,a,b):
    if('selected-nodes' in globals):
      for node in globals['selected-nodes']:
        label=Gtk.Label()    
        label.set_text(node)
        self.pack_start(label,False,False,0)
    
        
class NewNodeButton(Gtk.Button):
  def __init__(self):
    Gtk.Button.__init__(self)
    self.get_style_context().add_class("new-node-button")

    label = Gtk.Label("(x)")
    self.add(label)
    
    self.connect("clicked",self.on_new_button_clicked)
        
  def on_new_button_clicked(self,button):
    le.empty_brain()    

class NewLabelEntry(Gtk.Entry):
  def __init__(self):
    Gtk.Entry.__init__(self)
    self.get_style_context().add_class("new-label-entry")

    self.set_placeholder_text("NEW LABEL")
    self.set_width_chars(9)
    
    self.connect('activate',self.on_activate)
    self.connect('notify::text',self.on_notify_text)
    
  def on_notify_text(self,entry,data):
    globals['NewLabelEntry'] = entry.get_text()
    
  def on_activate(self,entry):
    if 'NewLabelEntry' in globals:
      le.create_label(globals['NewLabelEntry'])
      for label in globals['current-treepath']:
        le.add_label_to_node(label,globals['NewLabelEntry'])
      Signals.emit('node-created',globals['NewLabelEntry'])    

class NewFileEntry(Gtk.Entry):
  def __init__(self):
    Gtk.Entry.__init__(self)
    self.get_style_context().add_class("new-file-entry")
 
    self.set_placeholder_text("new file")
    self.set_width_chars(11)

    self.connect('activate',self.on_activate)
    self.connect('notify::text',self.notify_text)
    
  def notify_text(self,entry,data):
    globals['NewFileEntry'] = entry.get_text();    

  def on_activate(self,entry):
    if 'NewFileEntry' in globals:
      le.create_file(globals['NewFileEntry'],"%s" % globals['NewFileEntry'])
      for label in globals['current-treepath']:
        le.add_label_to_node(label,globals['NewFileEntry'])
      Signals.emit('node-created',label['name'])    

        
class NewEntryBar(Gtk.Box):
  def __init__(self):
    Gtk.Toolbar.__init__(self)
    self.get_style_context().add_class("new-entry-bar")
    #context = toolbar.get_style_context()
    entry=NewLabelEntry()
    self.add(entry)
    entry=NewFileEntry()
    self.add(entry)
    #button=NewNodeButton()
    #self.add(button)

class LocationButton(Gtk.ToggleToolButton):
  def __init__(self,text):
    Gtk.ToggleToolButton.__init__(self)
    self.get_style_context().add_class("location-button")

    button = Gtk.ToggleButton.new_with_label(text)
    child = self.get_child()

    self.remove(child)
    self.add(button)
    

class LocationBar(Gtk.Frame):
  def __init__(self):
    Gtk.Frame.__init__(self)
    self.get_style_context().add_class("location-bar")    
    self.set_shadow_type(Gtk.ShadowType.NONE)

    self.toolbar=Gtk.Toolbar()
    self.toolbar.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
    self.add(self.toolbar)
    self.fill()

    Signals.connect('current-treepath-changed',self.on_query_changed)
    
  def on_query_changed(self,num,num2):
    self.fill()
      
  def fill(self):
    for child in self.toolbar.get_children():
      self.toolbar.remove(child)
    curr_path = globals['current-treepath']
    if len(curr_path) == 0:
      curr_path = ['ALL','LABELS']
      
    for node in curr_path:
      added=1
      togglebutton = LocationButton(node)
      togglebutton.set_active(1)
      self.toolbar.add(togglebutton)
    self.show_all()
          
class IconView(Gtk.IconView):
  def __init__(self):
    self.list_store = Gtk.ListStore(GdkPixbuf.Pixbuf,str)
    Gtk.IconView.__init__(self,model=self.list_store)
    self.get_style_context().add_class("icon-view")    
 
    self.set_pixbuf_column(0)
    self.set_markup_column(1)
    self.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
    
    self.icon_theme=Gtk.IconTheme.get_default()
    self.fill_store('~*')
        
    dnd_list = Gtk.TargetEntry.new("text/uri-list", 0, 0)
    self.drag_dest_set(
      Gtk.DestDefaults.MOTION |
      Gtk.DestDefaults.HIGHLIGHT |
      Gtk.DestDefaults.DROP,
      [dnd_list],
      Gdk.DragAction.MOVE )
    self.drag_dest_add_uri_targets()

    Signals.connect('node-created', self.on_node_created)
    Signals.connect('current-treepath-changed', self.on_current_treepath_changed)

    self.connect("drag-data-received", self.on_drag_data_received)
    self.connect("key_release_event", self.on_key_release)
    self.connect('selection-changed',self.on_selection_changed)

  def on_selection_changed(self,arg):
    pathlist = self.get_selected_items()
    any_selected=0
    for path in pathlist:
      any_selected=1
      tree_iter = self.list_store.get_iter(path)
      selected_name = self.list_store.get_value(tree_iter,1)
      globals['selected-nodes'] = selected_name
      Signals.emit('nodes-selected',1)

  def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
    uris = data.get_uris()
    s = ""
    curr_path = globals['current-treepath']
    refresh_name=0
    for uri in uris:
      uri = uri.replace("file://","")
      bn = basename(uri)
      if isfile(uri):
        le.create_file(bn,uri)
        refresh_name=uri
        if len(curr_path)>0:
          le_query = '+["%s"],["%s"]' % ('" | "'.join(curr_path),bn)
          le.execute(le_query)
      else:
        for i in range(len(curr_path)): 
          le.create_label(curr_path[i])
          refresh_name=uri
          le_query = '+["%s"],["%s"]' % (curr_path[i-1],curr_path[i])
          le.execute('+["%s"],["%s"]' % ('" | "'.join(curr_path[:i]),curr_path[i]))
        for r,d,fs in os.walk(uri):
          rel = r.replace(uri,"")
          pl = pathlist(rel)
          for i in range(len(pl)):
            le.create_label(pl[i])
            refresh_name=pl[i]
            if i > 0:
              le_query = '+["%s"],["%s"]' % (pl[i-1],pl[i])
              le.execute(le_query)
          for f in fs:
            le.create_file(f,"%s/%s" % (r,f))
            refresh_name=f
            le_query = '+["%s"],["%s"]' % ('" | "'.join(pl),f)
            le.execute(le_query)
    refresh_name and Signals.emit('node-created',refresh_name)

  def on_node_created(self,num,num2):
    self.fill_store('~*')
  
  def on_current_treepath_changed(self,num,num2):
    le_query = '~*'
    curr_path = globals['current-treepath']
    if len(curr_path) >0:
      le_query = '~[<"%s"] | #<"%s"' % ('" & <"'.join(curr_path),curr_path[-1])

    self.fill_store(le_query)
    
  def fill_store(self,query):
    self.list_store.clear()

    for node in le.query(query):
      pixbuf = self.render_icon(Gtk.STOCK_FILE, Gtk.IconSize.DIALOG, None)
      #file= Gio.File.new_for_path(node['uri'])
      #type=file.query_file_type(0,None)
      #print "type=",type,file.get_path()
      self.list_store.append([pixbuf,node['name'].replace("&","")])

  def on_key_release(self,widget,event):
    if event.keyval == 65535:
      pathlist = self.get_selected_items()
      any_selected=0
      for path in pathlist:
        any_selected=1
        tree_iter = self.list_store.get_iter(path)
        selected_name = self.list_store.get_value(tree_iter,1)
        le.delete_node(selected_name)
      if any_selected: self.fill_store('~*')

  
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
    self.selection.connect("changed",self.on_change)
    self.set_size_request(200, -1)
    self.set_headers_visible(False)

    self.reset_store()
    
    path=Gtk.TreePath("0")
    self.expand_row(path,False)
    
    self.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK,
                  [('text/plain', 0, 0)],
                  Gdk.DragAction.DEFAULT | Gdk.DragAction.MOVE)

    self.connect("drag-begin", self.drag_data_get_cb)
    Signals.connect('node-created', self.on_node_created)
    self.connect('row-expanded', self.on_row_expanded)
    self.connect('key_release_event',self.on_key_release)

  def drag_data_get_cb(self, context, selection):
      treeselection = self.get_selection()
      (model, iter) = treeselection.get_selected()
      text = self.tree_store.get_value(iter, 0)
      
      #pb=GdkPixbuf.Pixbuf()
      #pb.new_from_file("/home/gerard/label.svg")
      #display = self.get_display()
      #cursor=Gdk.Cursor.new_from_pixbuf(display,pb,0,0) #Gdk.CursorType.PENCIL)
      #cursor.new_from_pixbuf(pb)
      #gdkwin = Gdk.get_default_root_window()
      #gdkwin.set_cursor(cursor)
  
  def on_node_created(self,signal,name):
    tree_selection = self.get_selection()
    (model, pathlist) = tree_selection.get_selected_rows()
    iters_selected = []
    for path in pathlist:
      self.refresh_iter(self.tree_store.get_iter(path))
      self.expand_row(path, True)
    
  def reset_store(self):
    self.tree_store.clear()
    parent = self.tree_store.append(None, ('labels',))
    for node in le.query('#^<*'):
      if 'name' in node:
        parent2=self.tree_store.append(parent, (node['name'],))
        for node2 in le.query('#<"%s"'%node['name']):
          parent3=self.tree_store.append(parent2, (node2['name'],))
        
  def on_row_expanded(self,tree_view,tree_iter,path):
    self.refresh_iter(tree_iter)
  
  def refresh_iter(self,tree_iter):
    name = self.tree_store.get_value(tree_iter,0)
    child = self.tree_store.iter_children(tree_iter)
    # anem en compte de no eliminar tots els children
    # eliminem l'ultim despres d'afegir els nous
    while self.tree_store.iter_n_children(tree_iter) > 1:
      child_name = self.tree_store.get_value(child,0)
      self.tree_store.remove(child)
      child = self.tree_store.iter_children(tree_iter)
    name = self.tree_store.get_value(tree_iter,0)
    le_query=''
    if name == 'labels':
      le_query = ('#^<*')
    else:
      le_query = ('#<"%s"' % name)
      
    for node in le.query(le_query):
      if 'name' in node:
        parent2=self.tree_store.append(tree_iter, (node['name'],))
        parent3=self.tree_store.append(parent2, ('.',))
    if child != None:
      self.tree_store.remove(child)
        
  def on_change(self,tree_selection):
    (model, pathlist) = tree_selection.get_selected_rows()
    globals['current-treepath']=[]
    globals['selected-nodes']=[]
    for path in pathlist :
      tree_iter = model.get_iter(path)
      name = model.get_value(tree_iter,0)
      if name != 'labels':
        globals['current-treepath'].insert(0,name)
        globals['selected-nodes'].insert(0,name)
      parent = model.iter_parent(tree_iter)
      while parent != None:
        parent_name = model.get_value(parent,0)
        if parent_name != 'labels':
          globals['current-treepath'].insert(0,parent_name)
        parent = model.iter_parent(parent)

    Signals.emit('nodes-selected',1)
    Signals.emit('current-treepath-changed',1)

  def on_key_release(self,widget,event):
    if event.keyval == 65535:
      tree_selection = self.get_selection()
      (model, pathlist) = tree_selection.get_selected_rows()
      for path in pathlist :
        tree_iter = model.get_iter(path)
        selected_name = model.get_value(tree_iter,0)
        le.delete_node(selected_name)
        parent = model.iter_parent(tree_iter)
        self.refresh_iter(parent)
        #while parent != None:
        #  parent_name = model.get_value(parent,0)
        #  if parent_name != 'LABELS':
        #    le.remove_label_from_node(parent_name,selected_name)
        #    self.refresh_tree_iter(parent)
        #  parent = model.iter_parent(parent)
class WindowPane(Gtk.ScrolledWindow):
  def __init__(self):
    Gtk.ScrolledWindow.__init__(self)

class RightPane(Gtk.Box):
  def __init__(self):
    Gtk.Box.__init__(self)
    self.get_style_context().add_class("right-pane")
    self.table = Gtk.Table(1,1,False)
    self.add(self.table)

  def add(self,child):
    self.table.attach(child,0,1,0,1,Gtk.AttachOptions.FILL,Gtk.AttachOptions.FILL)

class CenterPane(Gtk.Frame):
  def __init__(self):
    Gtk.Frame.__init__(self)
    self.get_style_context().add_class("center-pane")    
    self.set_shadow_type(Gtk.ShadowType.NONE)
    self.table = Gtk.Table(2,1,False)
    self.table.get_style_context().add_class("center-pane-table")
    self.add(self.table)


  def add1(self,child):
    self.table.attach(child,0,1,0,1,Gtk.AttachOptions.FILL,Gtk.AttachOptions.FILL)

  def add2(self,child):
    win = Gtk.ScrolledWindow()
    win.add(child)
    self.table.attach(win,0,1,1,2) #,Gtk.AttachOptions.EXPAND) #,Gtk.AttachOptions.FILL)
  
class LeftPane(Gtk.Frame):
  def __init__(self):
    Gtk.Frame.__init__(self)
    self.set_shadow_type(Gtk.ShadowType.NONE)
    self.table = Gtk.Table(2,1,False)
    self.add(self.table)
    self.get_style_context().add_class("left-pane")    

  def add1(self,child):
    self.table.attach(child,0,1,0,1,Gtk.AttachOptions.FILL,Gtk.AttachOptions.FILL)

  def add2(self,child):
    win = Gtk.ScrolledWindow()
    win.add(child)

    self.table.attach(win,0,1,1,2) #,Gtk.AttachOptions.FILL,Gtk.AttachOptions.EXPAND)

class MainLayout(Gtk.Paned):
  def __init__(self):
    Gtk.Paned.__init__(self)
    
    self.Pane2 = Gtk.Paned()
    self.pack1(self.Pane2,0,0)
    self.get_style_context().add_class("main-layout")    

  def add_1(self,child):
    self.get_child1().pack1(child,0,0)
    
  def add_2(self,child):
    self.get_child1().pack2(child,1,0)
    
  def add_3(self,child):
    self.pack2(child,0,0)

class LabelsWindow(Gtk.Window):
  def __init__(self):
    Gtk.Window.__init__(self, title="Labels")
    self.get_style_context().add_class("labels-window")    
    
    self.set_default_size(600,400)

    globals['current-treepath'] = []
        
    mainlayout = MainLayout()
    self.add(mainlayout)

    leftpane = LeftPane()
    mainlayout.add_1(leftpane)
    centerpane = CenterPane()
    mainlayout.add_2(centerpane)
    #rightpane = RightPane()
    #mainlayout.add_3(rightpane)

    toolbar = NewEntryBar()
    leftpane.add1(toolbar)
    treeview = TreeView()
    leftpane.add2(treeview)
    
    locationbar = LocationBar()
    centerpane.add1(locationbar)
    iconview = IconView()
    centerpane.add2(iconview)

    #selectednodepanel = SelectedNodePanel()
    #rightpanel.add(selectednodepanel)
    
    self.set_focus(iconview)
    
    self.connect("delete-event", Gtk.main_quit)
    self.show_all()

class LabelsGUI:
  def __init__(self):
    self.win = LabelsWindow()
    provider = Gtk.CssProvider();
    provider.load_from_path("/home/gerard/labelfs/gtk-style.css");
    
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, 600);

if __name__ == "__main__":
  GUI = LabelsGUI()
  Gtk.main()
