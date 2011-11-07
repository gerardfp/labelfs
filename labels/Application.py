from gi.repository import Gtk, GObject
import os

import Globals
import Window
import LfsController

class Application(GObject.GObject):
  def __init__(self):
    self.lfs = LfsController.LfsController("%s/.lfs.db" % os.path.expanduser('~'))
    self.win = Window.Window()

    self.new_label_entry = self.win.tree_view_frame.new_node_bar.new_label_entry
    self.new_file_entry = self.win.tree_view_frame.new_node_bar.new_file_entry

    self.tree_view = self.win.tree_view_frame.tree_view
    self.tree_store = self.win.tree_view_frame.tree_view.tree_store    

    self.location_bar = self.win.query_view_frame.location_bar

    self.icon_view = self.win.query_view_frame.icon_view
    self.icon_store = self.win.query_view_frame.icon_view.list_store


    self.new_label_entry.connect('activate',self.on_new_label_entry_activate)
    self.new_file_entry.connect('activate',self.on_new_file_entry_activate)

    self.tree_view.selection.connect("changed",self.on_tree_view_selection_change)
    self.tree_view.connect("drag-begin", self.on_tree_view_drag_data_get_cb)
    self.tree_view.connect('row-expanded', self.on_tree_view_row_expanded)
    self.tree_view.connect('key_release_event',self.on_tree_view_key_release)

    self.icon_view.connect("drag-data-received", self.on_icon_view_drag_data_received)
    self.icon_view.connect("key_release_event", self.on_icon_view_key_release)
    self.icon_view.connect('selection-changed',self.on_icon_view_selection_changed)

    self.app_start()

  def app_start(self):

    self.reset_tree_store()
    path=Gtk.TreePath("0")
    self.tree_view.expand_row(path,False)

    self.refresh_location_bar()
  
    self.fill_icon_view()


  def reset_tree_store(self):
    self.tree_store.clear()
    parent = self.tree_store.append(None, ('labels',))
    for node in self.lfs.query('#^<*'):
      if 'name' in node:
        parent2=self.tree_store.append(parent, (node['name'],))
        for node2 in self.lfs.query('#<"%s"'%node['name']):
          parent3=self.tree_store.append(parent2, (node2['name'],))

  def refresh_tree_iter(self,tree_iter=None):
    name='labels'
    child=None
    if tree_iter != None:
      name = self.tree_store.get_value(tree_iter,0)
      child = self.tree_store.iter_children(tree_iter)
      # anem en compte de no eliminar tots els children
      # eliminem l'ultim despres d'afegir els nous
      while self.tree_store.iter_n_children(tree_iter) > 1:
        child_name = self.tree_store.get_value(child,0)
        self.tree_store.remove(child)
        child=self.tree_store.iter_children(tree_iter)
    le_query=''
    if name == 'labels':
      le_query = ('#^<*')
    else:
      le_query = ('#<"%s"' % name)
      
    for node in self.lfs.query(le_query):
      if 'name' in node:
        parent2=self.tree_store.append(tree_iter, (node['name'],))
        parent3=self.tree_store.append(parent2, ('.',))
    if child != None:
      self.tree_store.remove(child)
  
  def refresh_tree_selected_iters(self):
    tree_selection = self.tree_view.get_selection()
    (model, pathlist) = tree_selection.get_selected_rows()
    iters_selected = []
    for path in pathlist:
      self.refresh_tree_iter(self.tree_store.get_iter(path))
      self.tree_view.expand_row(path, True)

  def fill_icon_view(self):
    self.icon_store.clear()
    
    le_query = '~*'
    curr_path = Globals.current_treepath
    if len(curr_path) >0:
      le_query = '~[<"%s"] | #<"%s"' % ('" & <"'.join(curr_path),curr_path[-1])

    for node in self.lfs.query(le_query):
      pixbuf = self.icon_view.render_icon(Gtk.STOCK_FILE, Gtk.IconSize.DIALOG, None)
      self.icon_store.append([pixbuf,node['name'].replace("&","")])


  def on_tree_view_selection_change(self,tree_selection):
    (model, pathlist) = tree_selection.get_selected_rows()
    Globals.current_treepath=[]
    Globals.selected_nodes=[]
    for path in pathlist :
      tree_iter = model.get_iter(path)
      name = model.get_value(tree_iter,0)
      if name != 'labels':
        Globals.current_treepath.insert(0,name)
        Globals.selected_nodes.insert(0,name)
      parent = model.iter_parent(tree_iter)
      while parent != None:
        parent_name = model.get_value(parent,0)
        if parent_name != 'labels':
          Globals.current_treepath.insert(0,parent_name)
        parent = model.iter_parent(parent)

  def on_tree_view_drag_data_get_cb(self, context, selection):
      treeselection = self.get_selection()
      (model, iter) = treeselection.get_selected()
      text = self.tree_store.get_value(iter, 0)
      
  def on_tree_view_row_expanded(self,tree_view,tree_iter,path):
    self.refresh_tree_iter(tree_iter)          

  def on_tree_view_key_release(self,widget,event):
    if event.keyval == 65535:
      tree_selection = self.tree_view.get_selection()
      (model, pathlist) = tree_selection.get_selected_rows()
      for path in pathlist :
        tree_iter = model.get_iter(path)
        selected_name = model.get_value(tree_iter,0)
        self.lfs.delete_node(selected_name)
        parent = model.iter_parent(tree_iter)
        self.refresh_iter(parent)
        while parent != None:
          parent_name = model.get_value(parent,0)
          if parent_name != 'labels':
            self.lfs.remove_label_from_node(parent_name,selected_name)
            self.refresh_tree_iter(parent)
          parent = model.iter_parent(parent)

    
  def on_new_label_entry_activate(self,entry):
    new_label_entry_text = self.new_label_entry.get_text()
    if new_label_entry_text != "":
      self.lfs.create_label(new_label_entry_text)
      for label in Globals.current_treepath:
        self.lfs.add_label_to_node(label,new_label_entry_text)

  def on_new_file_entry_activate(self,entry):
    new_file_entry_text = self.new_file_entry.get_text()
    if new_file_entry_text != "":
      self.lfs.create_file(new_file_entry_text)
      for label in Globals.current_treepath:
        self.lfs.add_label_to_node(label,new_file_entry_text)

  def on_icon_view_selection_changed(self,arg):
    pathlist = self.icon_view.get_selected_items()
    any_selected=0
    for path in pathlist:
      any_selected=1
      tree_iter = self.icon_store.get_iter(path)
      selected_name = self.icon_store.get_value(tree_iter,1)
      Globals.selected_nodes = [selected_name]

  def on_icon_view_drag_data_received(self, widget, drag_context, x, y, data, info, time):
    self.lfs.create_nodes_from_uris_in_path(data.get_uris(),Globals.current_path)
          
  def on_icon_view_key_release(self,widget,event):
    if event.keyval == 65535:
      pathlist = self.get_selected_items()
      any_selected=0
      for path in pathlist:
        any_selected=1
        tree_iter = self.icon_store.get_iter(path)
        selected_name = self.icon_store.get_value(tree_iter,1)
        le.delete_node(selected_name)
      if any_selected: self.fill_icon_view()
  
  def refresh_location_bar(self):
    self.location_bar.refresh(Globals.current_treepath)
