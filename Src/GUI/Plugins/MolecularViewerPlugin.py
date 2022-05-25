# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Plugins/MolecularViewerPlugin.py
# @brief     Implements module/class/test MolecularViewerPlugin
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

import numpy

import vtk
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor 

import wx
import wx.aui as aui

from MDANSE import LOGGER, REGISTRY
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Core.Error import Error
from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.MolecularDynamics.Configuration import PeriodicRealConfiguration, RealConfiguration
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms, Trajectory

from MDANSE.GUI import PUBLISHER
from MDANSE.GUI.Plugins.DataPlugin import get_data_plugin 
from MDANSE.GUI.Plugins.ComponentPlugin import ComponentPlugin

# The colour for a selected atom (R,G,B,Alpha).
RGB_COLOURS = {}
RGB_COLOURS["selection"] = (0,(1.00,0.20,1.00))
RGB_COLOURS["default"]   = (1,(1.00,0.90,0.90))
RGB_COLOURS["axis1"]     = (2,(0.95,0.00,0.20))
RGB_COLOURS["axis2"]     = (3,(0.00,0.20,0.95))
RGB_COLOURS["basis1"]    = (4,(0.95,0.00,0.20))
RGB_COLOURS["basis2"]    = (5,(0.30,0.95,0.00))
RGB_COLOURS["basis3"]    = (6,(0.00,0.20,0.95))

class MolecularViewerError(Error):
    pass

class MyEventTimer(wx.Timer):
    def __init__(self, iren):
        wx.Timer.__init__(self)
        self._iren = iren

    def Notify(self):
        self._iren._Iren.TimerEvent()
      

class MyRenderWindowInteractor(wxVTKRenderWindowInteractor):
    def CreateTimer(self, obj, evt):
        self._timer = MyEventTimer(self)
        self._timer.Start(obj.GetTimerEventDuration(), True)

class MvEvent(int):
    def __init__(self,v):
        self = v
    def GetId(self):
        return self

class SelectionBox(vtk.vtkBoxWidget):

    def __init__(self,viewer, selection_color):
        self.viewer = viewer
        self.selection_color = selection_color
        outline = vtk.vtkOutlineFilter()
        if vtk.vtkVersion.GetVTKMajorVersion()<6:
            outline.SetInput(self.viewer._polydata)
        else:
            outline.SetInputData(self.viewer._polydata)
                    
        outlineMapper = vtk.vtkPolyDataMapper()
        outlineMapper.SetInputConnection(outline.GetOutputPort())
        self.box=vtk.vtkLODActor()
        self.box.SetMapper( outlineMapper )
        self.box.GetProperty().SetColor(1,1,1)
        self.box.PickableOff()
        
        self.SetProp3D(self.box)
        self.planes=vtk.vtkPlanes()
        self.SetInteractor(viewer.iren)
        if vtk.vtkVersion.GetVTKMajorVersion()<6:
            self.SetInput(self.viewer._polydata)
        else:
            self.SetInputData(self.viewer._polydata)
            
        self.SetPlaceFactor(1)
        self.PlaceWidget()
        self.InsideOutOn()
        self.SetRotationEnabled(0)
        self.GetPlanes(self.planes)
        self.AddObserver("EndInteractionEvent",self.on_select_atoms)

    def is_enabled(self):
                
        return self.GetEnabled()

    def show(self):

        self.SetEnabled(1)

    def hide(self):

        self.SetEnabled(0)

    def on_off(self):
        
        if self.GetEnabled():
            self.SetEnabled(0)
        else :
            self.SetEnabled(1)
               
    def on_select_atoms(self, obj = None, evt = None):
        polybox = vtk.vtkPolyData()
        self.GetPolyData(polybox)
        (xmin,xmax,ymin,ymax,zmin,zmax)=polybox.GetBounds()
        selection = []
        for i in range(self.viewer.n_atoms):
            x, y, z = self.viewer._polydata.GetPoint(i)
            if x >= xmin and x <= xmax and y >= ymin and y <= ymax and z >= zmin and z <= zmax:
                selection.append(i)

        self.viewer.pick_atoms(selection,True)

class MolecularViewerPlugin(ComponentPlugin):
    '''
    This class sets up a molecular viewer using vtk functionnalities.
    '''
            
    label = "Molecular Viewer"
    
    ancestor = ["hdf_trajectory"]
    
    category = ("Viewer",)
                
    # 0 line / 1 sphere / 2 tube / 3 sphere + tube / 4 sphere + line
    _rendmod = 4
    
    def __init__(self, parent, *args, **kwargs):
        
        ComponentPlugin.__init__(self, parent, *args, **kwargs)
        
        self.enable_picking(True)
           
    def build_panel(self):
                
        self._iren = MyRenderWindowInteractor(self, wx.ID_ANY, size=self.GetSize())
        self._iren.SetPosition((0,0))

        # define interaction style
        self._iren.GetInteractorStyle().SetCurrentStyleToTrackballCamera() # change interaction style

        self._iren.Enable(1)
        
        # create renderer  
        self._renderer = vtk.vtkRenderer()
        self._iren.GetRenderWindow().AddRenderer(self._renderer)
    
        # cam stuff
        self.camera=vtk.vtkCamera() # create camera 
        self._renderer.SetActiveCamera(self.camera) # associate camera to renderer
        self.camera.SetFocalPoint(0, 0, 0)
        self.camera.SetPosition(0, 0, 20)
        
        self.__pickerObserverId = None
        self.picker = vtk.vtkCellPicker()
        self.picker.SetTolerance(0.005)
        
        self._iren.AddObserver("TimerEvent", self.on_timer)
        self._iren.RemoveObservers("CharEvent")
        self._iren.AddObserver("CharEvent", self.on_keyboard_input)
        self._iren.AddObserver("LeftButtonPressEvent", self.emulate_focus)
        
        self._iren.Bind(wx.EVT_CONTEXT_MENU, self.on_show_popup_menu)

        PUBLISHER.subscribe(self.msg_set_selection, 'msg_set_selection')   
        PUBLISHER.subscribe(self.msg_switch_viewers_state, "msg_switch_viewers_state")
        PUBLISHER.subscribe(self.msg_clear_selection,'msg_clear_selection')                                
                
        self._mgr.AddPane(self._iren, aui.AuiPaneInfo().Dock().Center().CaptionVisible(False).CloseButton(False))
                
        self._mgr.Update()

        self._first = True    
        self._timerCounter = 0
        self._timerInterval = 5
        self._animationLoop = False
        self._trajectoryLoaded = False
        self._currentFrame = 0
        self._maxLaps = 100
        self.display_bbox = False
        self.bbox = None
        
        self._surface = None
        self._iso = None
                
        # Atoms picked from mouse or selection box.
        self.__pickedAtoms = set()
        
        self.SetFocusIgnoringChildren()
        
    def del_surface(self):
        del self._surface
        self._surface = None

    def msg_set_selection(self,message):
        
        plugin = message        
        if not self.is_parent(plugin):
            return
                
        self.show_selection(plugin.selection)
        
    def on_show_selection_box(self,message):

        window,show = message.data
        
        if get_data_plugin(self) != get_data_plugin(window):
            return
        
        self.show_selection_box(show)

    def on_enable_picking(self,message):

        window,state = message.data
        
        if get_data_plugin(self) != get_data_plugin(window):
            return
        
        self.enable_picking(state)

    def plug(self):
        
        self._parent._mgr.GetPane(self).Dock().Floatable(False).Center().CloseButton(True)

        self._parent._mgr.Update()
                        
        self._trajectory = self.dataproxy.data
                                
        self.set_trajectory(self._trajectory)
        
    def emulate_focus(self, obj=None, event=None):
        
        self.SetFocusIgnoringChildren()
           
    def close(self):
        # Ensure unsubscription
        self.__unsubscribe()
        # Clear the viewer
        self.clear_universe()

    def __del__(self):
        # Ensure unsubscription
        self.__unsubscribe()
        
    def __unsubscribe(self):
        PUBLISHER.unsubscribe(self.msg_set_selection, "msg_set_selection")
        PUBLISHER.unsubscribe(self.msg_switch_viewers_state, "msg_switch_viewers_state")
        PUBLISHER.unsubscribe(self.msg_clear_selection,'msg_clear_selection')                                
                
    def set_trajectory(self, trajectory, selection=None, frame=0):
        
        if not isinstance(trajectory,Trajectory):
            return
        
        # The trajectory argument is copied.
        if self._trajectoryLoaded:
            self.clear_universe()
        
        self._nFrames = len(trajectory)

        self._atoms = sorted_atoms(trajectory.chemical_system.atom_list())
        
        # The number of atoms of the universe stored by the trajectory.
        self._nAtoms = trajectory.chemical_system.number_of_atoms()
        
        # Hack for reducing objects resolution when the system is big
        self._resolution = int(numpy.sqrt(300000.0 / self._nAtoms))
        self._resolution = 10 if self._resolution > 10 else self._resolution
        self._resolution = 4 if self._resolution < 4 else self._resolution
                             
        # The array that will store the color and alpha scale for all the atoms.
        self._atomsColours , self._lut= self.build_ColorTransferFunction()
        self.atomsColours = numpy.copy(self._atomsColours)
                        
        # The array that will store the scale for all the atoms.
        self._atomsScales = numpy.array([ATOMS_DATABASE[at.symbol]['vdw_radius'] for at in self._atoms]).astype(numpy.float32)
        
        scalars = ndarray_to_vtkarray(self.atomsColours, self._atomsScales, self._nAtoms) 

        bonds = vtk.vtkCellArray()
        for at in self._atoms:
            idx1 = at.index
            for bat in at.bonds:
                idx2 = bat.index
                line = vtk.vtkLine()
                line.GetPointIds().SetId(0,idx1)
                line.GetPointIds().SetId(1,idx2)
                bonds.InsertNextCell(line)

        self._polydata = vtk.vtkPolyData()
        self._polydata.GetPointData().SetScalars(scalars)
        self._polydata.SetLines(bonds)
             
        self.clear_universe()
        
        self._trajectory = trajectory

        self.set_configuration(frame)
        
        self.enable_info_picking()
        
        self.__selectionBox = SelectionBox(self, RGB_COLOURS["selection"][0])
        
        self._trajectoryLoaded = True

        PUBLISHER.sendMessage('msg_set_trajectory', message=self)

    def color_string_to_RGB(self, s):
        
        if not s.strip():
            s = "1;1;1"
        
        return numpy.array(s.split(';')).astype(numpy.float32)/255.
        
    def build_ColorTransferFunction(self):
        
        lut = vtk.vtkColorTransferFunction()
        
        for (idx,color) in RGB_COLOURS.values():
            lut.AddRGBPoint(idx,*color)
            
        colours = []
        unic_colours = {}

        color_string_list = [self.color_string_to_RGB(ATOMS_DATABASE[at.symbol]['color']) for at in self._atoms]
        col_ids = len(RGB_COLOURS)
        
        for col in color_string_list:
            tup_col = tuple(col) 
            if not (tup_col in unic_colours.keys()):
                unic_colours[tup_col]=col_ids
                lut.AddRGBPoint(col_ids,*tup_col)
                colours.append(col_ids)
                col_ids += 1
            else:
                colours.append(unic_colours[tup_col])
                    
        return colours, lut
        
    def enable_picking(self,state):

        if state:
            self.__pickerObserverId = self._iren.AddObserver("LeftButtonPressEvent", self.on_pick)
        else:
            if self.__pickerObserverId is None:
                return

            self._iren.RemoveObserver(self.__pickerObserverId)
            self.__pickerObserverId = None
        
    def enable_info_picking(self):

        self._iren.AddObserver("LeftButtonPressEvent", self.on_info_pick)

    def on_show_popup_menu(self, event):

        popupMenu = wx.Menu()

        renderingMenu = wx.Menu()
        item = renderingMenu.Append(wx.ID_ANY, "Line")
        self.Bind(wx.EVT_MENU, lambda event : self.set_rendering_mode(0), item)

        item = renderingMenu.Append(wx.ID_ANY, "Stick")
        self.Bind(wx.EVT_MENU, lambda event : self.set_rendering_mode(2), item)

        item = renderingMenu.Append(wx.ID_ANY, "Ball")
        self.Bind(wx.EVT_MENU, lambda event : self.set_rendering_mode(1), item)

        item = renderingMenu.Append(wx.ID_ANY, "Ball and line")
        self.Bind(wx.EVT_MENU, lambda event : self.set_rendering_mode(4), item)

        item = renderingMenu.Append(wx.ID_ANY, "Ball and stick")
        self.Bind(wx.EVT_MENU, lambda event : self.set_rendering_mode(3), item)

        popupMenu.AppendMenu(wx.ID_ANY, "Rendering", renderingMenu)

        popupMenu.AppendSeparator()
        selectionBox = popupMenu.Append(wx.ID_ANY, 'Show/hide selection box',kind=wx.ITEM_CHECK)
        saveSelection = popupMenu.Append(wx.ID_ANY, 'Save selection')
        clearSelection = popupMenu.Append(wx.ID_ANY, 'Clear selection')

        popupMenu.AppendSeparator()
        
        parallelProjection = popupMenu.Append(wx.ID_ANY, 'Parallel projection',kind=wx.ITEM_CHECK)
        
        popupMenu.Bind(wx.EVT_MENU, self.on_toggle_selection_box, selectionBox)
        popupMenu.Bind(wx.EVT_MENU, self.on_clear_selection, clearSelection)
        popupMenu.Bind(wx.EVT_MENU, self.on_save_selection, saveSelection)
        popupMenu.Bind(wx.EVT_MENU, self.parallel_proj_onoff, parallelProjection)
        popupMenu.Check(parallelProjection.GetId(), self.camera.GetParallelProjection())
        
        boundingBox = popupMenu.Append(wx.ID_ANY, 'Show/hide bounding box', kind=wx.ITEM_CHECK)
        
        popupMenu.Bind(wx.EVT_MENU, self.bbox_onoff, boundingBox)
        popupMenu.Check(boundingBox.GetId(), self.display_bbox)
        popupMenu.Check(selectionBox.GetId(), False)

        self.PopupMenu(popupMenu)
        
        # Give to vtkinteractor the event that Wx has stoled
        self.iren.RightButtonReleaseEvent() 

    @property
    def animation_loop(self):
        return self._animationLoop

    @property
    def surface(self):
        return self._surface
    
    @property
    def iso(self):
        return self._iso
    
    @property
    def current_frame(self):
        return self._currentFrame

    @property
    def iren(self):
        return self._iren

    @property
    def max_laps(self):
        return self._maxLaps

    @property
    def n_frames(self):
        return self._nFrames

    @property
    def n_atoms(self):
        return self._nAtoms

    @property
    def selection_box(self):
        return self.__selectionBox

    @property
    def timer_interval(self):

        return self._timerInterval

    @property
    def trajectory(self):

        return self._trajectory

    @property
    def trajectory_loaded(self):

        return self._trajectoryLoaded

    @property
    def picked_atoms(self):
        
        return self.__pickedAtoms
    
    @property
    def selectedAtoms(self):
        
        return self.__pickedAtoms

    def change_frame_rate(self, laps):

        if not self._trajectoryLoaded:
            return
        
        self._timerInterval = (self._maxLaps - laps)*10 + 1
        if self._animationLoop:
            self._iren.CreateRepeatingTimer(self._timerInterval)

    def create_timer(self):
        
        self._iren.Initialize()    
        timerId = self._iren.CreateRepeatingTimer(self._timerInterval)
        self._iren.Start()

        return timerId

    def set_frame(self, frame):
        
        if not self._trajectoryLoaded:
            return
        
        self.stop_animation()
                
        self._timerCounter = frame
        
        self.set_configuration(frame)
                                
    def on_clear_labels(self, event=None):
        pass

    def on_export(self, event=None):
        pass

    def on_hide_labels(self, event=None):
        pass

    def on_select_all(self, event=None):
        pass

    def on_show_all_atoms(self, event=None):
        pass

    def on_show_labels(self, event=None):
        pass

    def on_show_unselected_atoms(self, event=None):
        pass

    def on_show_selected_atoms(self, event=None):
        pass

    def on_undo_exclude(self, event=None):
        pass

    def on_undo_include(self, event=None):
        pass
       
    def bbox_onoff(self, event=None):
        if self.bbox is None:
            return 
        if self.display_bbox:
            self.bbox.VisibilityOff()
            self.display_bbox = False
        else:
            self.bbox.VisibilityOn()
            self.display_bbox = True
        # rendering
        self._iren.Render()
    
    def parallel_proj_onoff(self, event=None):
        if self.camera.GetParallelProjection():
            self.camera.ParallelProjectionOff()
        else :
            self.camera.ParallelProjectionOn() 
        # rendering
        self._iren.Render()
        
    def on_toggle_selection_box(self,event):

        if self._trajectoryLoaded:
            self.__selectionBox.on_off()
        
    def on_keyboard_input(self, obj=None, event=None):

        if not self._trajectoryLoaded:
            return
        
        key = self._iren.GetKeyCode()

        if key in ['1','2','3','4','5']:
            mode = int(self._iren.GetKeyCode()) - 1
            self.set_rendering_mode(mode)
            
        elif key == " ":
            self.start_stop_animation()

    def on_timer(self, obj=None, event=None):

        if self._iren._timer.IsRunning():
            return
                
        self.set_configuration(self._timerCounter)
        self._timerCounter += 1
        
        PUBLISHER.sendMessage("msg_timer", message=self)

    def set_rendering_mode(self, mode):
        if not self._trajectoryLoaded:
            return

        if self._rendmod != mode:
            self._rendmod=mode
            self.set_configuration(self._currentFrame)

    def goto_first_frame(self):

        if not self._trajectoryLoaded:
            return
        
        self.stop_animation()

        self._timerCounter = 0
        self.set_configuration(0)
                   
    def goto_last_frame(self):

        if not self._trajectoryLoaded:
            return
        
        self.stop_animation()
        last = self._nFrames-1
        self._timerCounter = last
        self.set_configuration(last)

    def show_selection_box(self,show):

        if self._trajectoryLoaded:
            self.__selectionBox.SetEnabled(show)
        
    def set_timer_interval(self, timerInterval):

        self._timerInterval = timerInterval
          
    def on_pick(self, obj, event=None):
        
        if not self._trajectoryLoaded:
            return
                                
        pos = obj.GetEventPosition()
        self.picker.AddPickList(self.picking_domain)
        self.picker.PickFromListOn()
        self.picker.Pick(pos[0], pos[1], 0,self._renderer)
        pid = self.picker.GetPointId()
        if pid > 0:
            idx = self.get_atom_index(pid)
            self.pick_atoms([idx],new=(not obj.GetShiftKey()))

    def on_info_pick(self, obj, evt = None):
        
        
        if not self._trajectoryLoaded:
            return
                
        pos = obj.GetEventPosition()
        
        self.picker.AddPickList(self.picking_domain)
        self.picker.PickFromListOn()
        self.picker.Pick(pos[0], pos[1], 0,self._renderer)
        pid = self.picker.GetPointId()
        if pid > 0:
            idx = self.get_atom_index(pid)
            xyz = self._trajectory.chemical_system.configuration['coordinates'][idx,:]
            info = '%s (id:%s) at  %s'%(self._atoms[idx].full_name(), self._atoms[idx].index, '%.3f %.3f %.3f'%tuple(xyz))
            LOGGER(info, "info")
        self.picker.InitializePickList()
                
    def pick_atoms(self, atomsList, new=False):
                
        if new:        
            self.__pickedAtoms = set(atomsList)
        else:
            self.__pickedAtoms.symmetric_difference_update(atomsList)

        self.show_selection(list(self.__pickedAtoms))
                        
        PUBLISHER.sendMessage('msg_select_atoms_from_viewer', message=(self.dataplugin,list(self.__pickedAtoms)))

    def box_atoms(self, atomsList):
                                
        self.__pickedAtoms = set(atomsList)

        self.show_selection(list(self.__pickedAtoms))
                                    
    def show_selected_atoms(self, atomsList):

        self.show_selection(atomsList)
        
    def on_clear_selection(self,event=None):
        
        if not self._trajectoryLoaded:
            return
                                        
        self.atomsColours = numpy.copy(self._atomsColours)
        
        for i in range(self._nAtoms):
            self._polydata.GetPointData().GetArray("scalars").SetTuple3(i, self._atomsScales[i], self._atomsColours[i], i)
            
        self._polydata.Modified()
        
        self._iren.Render()

    def on_save_selection(self,event=None):
        
        if not self._trajectoryLoaded:
            return
        
        if not self.__pickedAtoms:
            return
        
        d = wx.TextEntryDialog(self,"Enter selection name","New selection")
 
        # If the new element dialog is closed by clicking on OK. 
        if d.ShowModal() == wx.ID_CANCEL:
            return
 
        # Get rid of wxpython unicode string formatting
        name = str(d.GetValue())
                         
        if not name:
            return
        
        target = os.path.basename(self._trajectory.filename)
        
        if UD_STORE.has_definition(target,"atom_selection",name):
            LOGGER('There is already a user-definition with that name.','error',['console'])
            return
                  
        UD_STORE.set_definition(target,"atom_selection",name,{'indexes':sorted(self.__pickedAtoms)})
                 
        UD_STORE.save()
                 
        PUBLISHER.sendMessage("msg_set_ud",message=None)
        
        LOGGER('User definition %r successfully set.' % name,'info',['console'])
                                                         
    def show_selection(self, selection):
        
        if not self._trajectoryLoaded:
            return
        
        if not isinstance(selection,dict):
            selection = {"selection":selection}
                            
        self.atomsColours = numpy.copy(self._atomsColours)
        
        for k,v in selection.items():
            self.atomsColours[v] = RGB_COLOURS[k][0]

        for idx in range(self._nAtoms):
            self._polydata.GetPointData().GetArray("scalars").SetTuple3(idx, self._atomsScales[idx], self.atomsColours[idx], idx)
                                        
        self._polydata.Modified()
        
        self._iren.Render()
        
    def start_animation(self, event=None):
        
        if self._trajectoryLoaded:
            self._timerId = self.create_timer()
            self._iren.TimerEventResetsTimerOn()
            self._animationLoop = True

    def stop_animation(self, event=None):
        
        if self._trajectoryLoaded:
            self._iren.TimerEventResetsTimerOff()
            self._animationLoop = False 

    def start_stop_animation(self, event=None, check=True):
        
        if not self._trajectoryLoaded:
            return

        if self._first:
            self._first = False
                    
        if not self._animationLoop:
            self.start_animation()
        else:
            self.stop_animation()
            
        if check:
            PUBLISHER.sendMessage("msg_switch_viewers_state", message=self) 
            
        PUBLISHER.sendMessage('msg_animate_trajectory', message=self)
    
    def msg_switch_viewers_state(self, message):
                 
        if not self._animationLoop:
            return
        
        viewer = message
        if viewer==self:
            return
         
        self.start_stop_animation(check=False)
            
    def get_atom_index(self,pid):
        
        if self._rendmod in [1,3,4]:
            _, _, idx =  self.glyph.GetOutput().GetPointData().GetArray("scalars").GetTuple3(pid)
        elif self._rendmod in [2]:
            _, _, idx =  self.tubes.GetOutput().GetPointData().GetArray("scalars").GetTuple3(pid)
        else:
            _, _, idx = self._polydata.GetPointData().GetArray("scalars").GetTuple3(pid)
        
        return int(idx)            
                                
    def get_atom_props(self,pid):
        
        if self._rendmod in [1,3,4]:
            radius, color, idx =  self.glyph.GetOutput().GetPointData().GetArray("scalars").GetTuple3(pid)
        elif self._rendmod in [2]:
            radius, color, idx =  self.tubes.GetOutput().GetPointData().GetArray("scalars").GetTuple3(pid)
        else:
            radius, color, idx = self._polydata.GetPointData().GetArray("scalars").GetTuple3(pid)
        
        return radius, color, int(idx)
    
    def this_atom_is_selected(self,pid):
        _, _, pid = self.get_atom_props(pid)
        return self.atomsColours[pid]==RGB_COLOURS["selection"][0]
       
    def pick_atom(self,pid):
        if self.this_atom_is_selected(pid):
            self.unpick_atom(pid)
        else:
            radius, _, pid = self.get_atom_props(pid)
            self.atomsColours[pid] = RGB_COLOURS["selection"][0]
            self._polydata.GetPointData().GetArray("scalars").SetTuple3(pid, radius, RGB_COLOURS["selection"][0], pid)
            self._polydata.Modified()
        
    def unpick_atom(self,pid):
        radius, _, pid = self.get_atom_props(pid)
        self.atomsColours[pid] = self._atomsColours[pid]
        self._polydata.GetPointData().GetArray("scalars").SetTuple3(pid, radius, self._atomsColours[pid], pid)
        self._polydata.Modified()
                
    def get_renwin(self):
        return self._iren.GetRenderWindow()
    
    def build_real_bbox(self, molecule):
        
        Xmin,Xmax,Ymin, Ymax, Zmin, Zmax = molecule.GetBounds()
        bbox_points = vtk.vtkPoints()
         
        bbox_points.InsertNextPoint(Xmin, Ymin, Zmin)
        bbox_points.InsertNextPoint(Xmax , Ymax, Zmax)
         
        BBox_poly = vtk.vtkPolyData()
        BBox_poly.SetPoints(bbox_points)
         
        outline = vtk.vtkOutlineFilter()
        if vtk.vtkVersion.GetVTKMajorVersion()<6:
            outline.SetInput(BBox_poly)
        else:
            outline.SetInputData(BBox_poly)

        outline_mapper = vtk.vtkPolyDataMapper()
        outline_mapper.SetInputConnection(outline.GetOutputPort())
        
        outline_actor = vtk.vtkLODActor()
        outline_actor.SetMapper(outline_mapper)
        outline_actor.GetProperty().SetColor(1,0,0)
        outline_actor.GetProperty().SetLineWidth(3)
        
        self._renderer.AddActor(outline_actor)
        self._iren.Render()
        
    def build_bbox(self, basis_vector):
        
        cell = numpy.array(basis_vector).astype(numpy.float32)
        Xmax,Ymax,Zmax =  numpy.array([cell[0,0], cell[1,1], cell[2,2]], dtype = numpy.float32)
        bbox_points = vtk.vtkPoints()
        
        self.cell_bounds_coords = numpy.array([-Xmax/2. , Xmax/2.,  -Ymax/2., Ymax/2.,  -Zmax/2., Zmax/2.])
        
        bbox_points.InsertNextPoint(-Xmax/2. , -Ymax/2., -Zmax/2.)
        bbox_points.InsertNextPoint(Xmax/2. , Ymax/2., Zmax/2.)
         
        BBox_poly = vtk.vtkPolyData()
        BBox_poly.SetPoints(bbox_points)
         
        outline = vtk.vtkOutlineFilter()
        if vtk.vtkVersion.GetVTKMajorVersion()<6:
            outline.SetInput(BBox_poly)
        else:
            outline.SetInputData(BBox_poly)

        outline_mapper = vtk.vtkPolyDataMapper()
        outline_mapper.SetInputConnection(outline.GetOutputPort())
        
        outline_actor = vtk.vtkLODActor()
        outline_actor.SetMapper(outline_mapper)
        outline_actor.GetProperty().SetColor(1,1,1)
        outline_actor.GetProperty().SetLineWidth(3)
        
        return outline_actor
     
    def build_scene(self):   
        '''
        build a vtkPolyData object for a given frame of the trajectory
        '''
        
        rendmod = self._rendmod
        
        actorList = []
        lineActor=None
        ballActor=None
        tubeActor=None
                
        if rendmod in [0,4] :
            line_mapper = vtk.vtkPolyDataMapper()
            if vtk.vtkVersion.GetVTKMajorVersion()<6:
                line_mapper.SetInput(self._polydata)
            else:
                line_mapper.SetInputData(self._polydata)
                
            line_mapper.SetLookupTable(self._lut)
            line_mapper.ScalarVisibilityOn()
            line_mapper.ColorByArrayComponent("scalars", 1)
            lineActor = vtk.vtkLODActor()
            lineActor.GetProperty().SetLineWidth(3)
            lineActor.SetMapper(line_mapper)
            actorList.append(lineActor)
            
        if rendmod in [1,3,4]:
            sphere = vtk.vtkSphereSource()
            sphere.SetCenter(0, 0, 0)
            sphere.SetRadius(0.2)
            sphere.SetThetaResolution(self._resolution)
            sphere.SetPhiResolution(self._resolution)
            glyph = vtk.vtkGlyph3D()
            if vtk.vtkVersion.GetVTKMajorVersion()<6:
                glyph.SetInput(self._polydata)
            else:
                glyph.SetInputData(self._polydata)
                
            glyph.SetScaleModeToScaleByScalar()
            glyph.SetColorModeToColorByScalar()
            glyph.SetScaleFactor(1)
            glyph.SetSourceConnection(sphere.GetOutputPort())
            glyph.SetIndexModeToScalar()
            sphere_mapper = vtk.vtkPolyDataMapper()
            sphere_mapper.SetLookupTable(self._lut)
            sphere_mapper.SetScalarRange(self._polydata.GetScalarRange())
            sphere_mapper.SetInputConnection(glyph.GetOutputPort())            
            sphere_mapper.ScalarVisibilityOn()
            sphere_mapper.ColorByArrayComponent("scalars", 1)
            ballActor = vtk.vtkLODActor()
            ballActor.SetMapper(sphere_mapper)
            ballActor.GetProperty().SetAmbient(0.2)
            ballActor.GetProperty().SetDiffuse(0.5)
            ballActor.GetProperty().SetSpecular(0.3)
            ballActor.SetNumberOfCloudPoints(30000)
            actorList.append(ballActor)
            self.glyph = glyph
            
        if rendmod in [2,3] :
            tubes = vtk.vtkTubeFilter()
            if vtk.vtkVersion.GetVTKMajorVersion()<6:
                tubes.SetInput(self._polydata)
            else:
                tubes.SetInputData(self._polydata)
            
            tubes.SetNumberOfSides(6)
            if rendmod == 2:
                tubes.CappingOn()
                tubes.SetRadius(0.015)
            else:
                tubes.SetCapping(0)
                tubes.SetRadius(0.01)
            tubes.SetNumberOfSides(self._resolution)
            tube_mapper = vtk.vtkPolyDataMapper()
            tube_mapper.SetLookupTable(self._lut)
            tube_mapper.SetInputConnection(tubes.GetOutputPort())
            tube_mapper.ScalarVisibilityOn()
            tube_mapper.ColorByArrayComponent("scalars", 1)
            tubeActor = vtk.vtkLODActor()
            tubeActor.SetMapper(tube_mapper)
            tubeActor.GetProperty().SetAmbient(0.2)
            tubeActor.GetProperty().SetDiffuse(0.5)
            tubeActor.GetProperty().SetSpecular(0.3)
            actorList.append(tubeActor)
            self.tubes = tubes
        
        self.picking_domain = [lineActor,ballActor,tubeActor,ballActor,ballActor][rendmod]
        
        basis_vector = self._trajectory[0].get('unit_cell',None)
        if not basis_vector is None:
            self.bbox = self.build_bbox(basis_vector)
            if not self.display_bbox:
                self.bbox.VisibilityOff()
            actorList.append(self.bbox)
            
        assembly = vtk.vtkAssembly()
        for actor in actorList:
            assembly.AddPart(actor)
                
        return assembly
    
    def msg_clear_selection(self,message):

        plugin = message
        if not self.is_parent(plugin):
            return
        
        self.on_clear_selection()
            
    def clear_universe(self):

        if not hasattr(self, "_actors"):
            return 
        
        self._actors.VisibilityOff()
        self._actors.ReleaseGraphicsResources(self.get_renwin())
        self._renderer.RemoveActor(self._actors)
        
        del self._actors
  
    def show_universe(self):
        '''
        Update the renderer
        '''
        # deleting old frame
        self.clear_universe()
        
        # creating new polydata
        self._actors = self.build_scene()

        # adding polydata to renderer
        self._renderer.AddActor(self._actors)
        
        # rendering
        self._iren.Render()
             
    def set_configuration(self, frame):
        '''
        Sets a new configuration.
        
        @param frame: the configuration number
        @type frame: integer
        '''
        
        self._currentFrame = frame % len(self._trajectory)
        coords = self._trajectory[self._currentFrame]['coordinates']
        unitCell = self._trajectory.unit_cell(self._currentFrame)

        if unitCell is None:
            conf = RealConfiguration(self.trajectory.chemical_system,coords)
        else:
            conf = PeriodicRealConfiguration(self.trajectory.chemical_system,coords,unitCell)
        
        self._trajectory.chemical_system.configuration = conf

        coords = conf.variables['coordinates']

        points = vtk.vtkPoints()
        points.SetNumberOfPoints(self._nAtoms)
        for i in range(self._nAtoms):
            x,y,z = coords[i]
            points.SetPoint(i,x,y,z)

        self._polydata.SetPoints(points)
                                
        # Reset the view.                        
        self.show_universe()        

def ndarray_to_vtkpoints(array):
    """Create vtkPoints from double array"""
    points = vtk.vtkPoints()
    points.SetNumberOfPoints(array.shape[0])
    vtkids = {}
    for i in range(array.shape[0]):
        point = array[i]
        vtkid = points.SetPoint(i, point[0], point[1], point[2])
        vtkids[vtkid]=i
    return points,vtkids

def ndarray_to_vtkarray(colors, radius, nbat):
    # define the colours
    color_scalars = vtk.vtkFloatArray()
    color_scalars.SetNumberOfValues(colors.shape[0])
    for i,c in enumerate(colors):
        color_scalars.SetValue(i,c)
    color_scalars.SetName("colors")
    
    # some radii
    radius_scalars = vtk.vtkFloatArray()
    radius_scalars.SetNumberOfValues(radius.shape[0])
    for i,r in enumerate(radius):
        radius_scalars.SetValue(i,r)
    radius_scalars.SetName("radius")
    
    # the original index
    index_scalars = vtk.vtkIntArray()
    index_scalars.SetNumberOfValues(nbat)
    for i in range(nbat):
        index_scalars.SetValue(i,i)
    index_scalars.SetName("index")
    
    scalars = vtk.vtkFloatArray()
    scalars.SetNumberOfComponents(3)
    scalars.SetNumberOfTuples(radius_scalars.GetNumberOfTuples())
    scalars.CopyComponent(0, radius_scalars ,0 )
    scalars.CopyComponent(1, color_scalars ,0 )
    scalars.CopyComponent(2, index_scalars ,0 )
    scalars.SetName("scalars")
    return scalars 

def ndarray_to_vtkcellarray(array):
    bonds=vtk.vtkCellArray()
    for data in array:
        line = vtk.vtkLine()
        line.GetPointIds().SetId(0,int(data[0]))
        line.GetPointIds().SetId(1,int(data[1]))
        bonds.InsertNextCell(line)

    return bonds

def get_trajectory_filename():

    filters = 'HDF file (*.h5)|*.h5|All files (*.*)|*.*'
    
    dialog = wx.FileDialog ( None, message = 'Open Trajectory file...', wildcard=filters, style=wx.OPEN)

    if dialog.ShowModal() == wx.ID_CANCEL:
        return ""
    
    return dialog.GetPath()    

def build_axes():
    axes = vtk.vtkAxesActor() #  create axes actor
    axes.SetTotalLength( 10, 10 , 10 )
    axes.SetNormalizedShaftLength( 1, 1, 1 )
    axes.SetNormalizedTipLength( 0, 0, 0 )
    axes.AxisLabelsOff()
    axes.GetXAxisTipProperty().SetColor( 0, 0, 1 )
    axes.GetXAxisShaftProperty().SetColor( 0, 0, 1  )
    axes.GetYAxisTipProperty().SetColor( 1, 1, 1 )
    axes.GetYAxisShaftProperty().SetColor( 1, 1, 1 )
    axes.GetZAxisTipProperty().SetColor( 1, 0, 0 )
    axes.GetZAxisShaftProperty().SetColor( 1, 0, 0 )
    return axes

REGISTRY["molecular_viewer"] = MolecularViewerPlugin
