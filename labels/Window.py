from gi.repository import Gtk

import TreeViewFrame
import QueryViewFrame
import SelectedNodesFrame

class ThreePaned(Gtk.Paned):
  def __init__(self):
    Gtk.Paned.__init__(self)
    
    self.Pane2 = Gtk.Paned()
    self.pack1(self.Pane2,0,0)
    self.get_style_context().add_class("three-paned")    

  def add_left(self,child):
    self.get_child1().pack1(child,0,0)
    
  def add_center(self,child):
    self.get_child1().pack2(child,1,0)
    
  def add_right(self,child):
    self.pack2(child,0,0)

class Window(Gtk.Window):
  def __init__(self):
    Gtk.Window.__init__(self, title="Labels")
    self.get_style_context().add_class("window")    
    
    self.set_default_size(600,400)
        
    self.three_paned = ThreePaned()
    self.add(self.three_paned)

    self.tree_view_frame = TreeViewFrame.TreeViewFrame()
    self.three_paned.add_left(self.tree_view_frame)

    self.query_view_frame = QueryViewFrame.QueryViewFrame()
    self.three_paned.add_center(self.query_view_frame)

    #self.selected_nodes_frame = SelectedNodesFrame.SelectedNodesFrame()
    #self.three_paned.add_right(self.selected_nodes_frame)
        
    self.set_focus(self.query_view_frame.icon_view)

    self.connect("delete-event", Gtk.main_quit)

    self.show_all()

