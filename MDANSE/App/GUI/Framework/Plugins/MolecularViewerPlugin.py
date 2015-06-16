#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#goret[at]ill.fr
#aoun[at]ill.fr
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

''' 
Created on Apr 14, 2015

:author: Gael Goret, Bachir Aoun, Eric C. Pellegrini
'''

import numpy

import vtk
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor 

import wx
import wx.aui as aui

from MMTK.Trajectory import Trajectory

from MDANSE import ELEMENTS, LOGGER
from MDANSE.Core.Error import Error
from MDANSE.Externals.pubsub import pub
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms

from MDANSE.App.GUI.Framework.Plugins.ComponentPlugin import ComponentPlugin

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
        self.box=vtk.vtkActor()
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
        
        self.viewer.pick_atoms(selection)

class MolecularViewerPanel(ComponentPlugin):
    '''
    This class sets up a molecular viewer using vtk functionnalities.
    '''
        
    type = "molecular_viewer"
    
    label = "Molecular Viewer"
    
    ancestor = "mmtk_trajectory"
    
    category = ("Viewer",)
                
    # 0 line / 1 sphere / 2 tube / 3 sphere + tube / 4 sphere + line
    _rendmod = 3
    
    def __init__(self, parent, *args, **kwargs):
        
        ComponentPlugin.__init__(self, parent, *args, **kwargs)
   
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

        pub.subscribe(self.check_switch_consistancy, ('Switch'))
        
        self._iren.Bind(wx.EVT_CONTEXT_MENU, self.on_show_popup_menu)
                
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

    def plug(self):
        
        self._parent._mgr.GetPane(self).Dock().Floatable(False).Center().CloseButton(True)

        self._parent._mgr.Update()
                        
        self._trajectory = self.dataproxy.data
                                
        self.set_trajectory(self._trajectory)
        
    def emulate_focus(self, obj, event):
        
        self.SetFocusIgnoringChildren()
           
    def close(self):
                
        self.clear_universe()
        
        pub.unsubscribe(self.check_switch_consistancy, "Switch")
        
    def set_trajectory(self, trajectory, selection=None, frame=0):
        
        if not isinstance(trajectory,Trajectory):
            return
        
        # The trajectory argument is copied.
        if self._trajectoryLoaded:
            self.clear_universe()
        
        self._nFrames = len(trajectory)

        self._atoms = sorted_atoms(trajectory.universe)
        
        # The number of atoms of the universe stored by the trajectory.
        self._nAtoms = trajectory.universe.numberOfAtoms()
                                   
        self.coords = trajectory.universe.contiguousObjectConfiguration().array

        # The array that will store the color and alpha scale for all the atoms.
        self._atomsColours , self._lut= self.build_ColorTransferFunction()
        self.atomsColours = numpy.copy(self._atomsColours)
                        
        # The array that will store the scale for all the atoms.
        self._atomsScales = numpy.array([ELEMENTS[at.symbol,'vdw_radius'] for at in self._atoms]).astype(numpy.float32)
             
        self.clear_universe()
        
        self._trajectory = trajectory
        
        # Set the configuration and display it.        
        self.set_configuration(frame)
        
        self.enable_info_picking()
        
        self.__selectionBox = SelectionBox(self, RGB_COLOURS["selection"][0])
        
        self._trajectoryLoaded = True

        pub.sendMessage(('Load trajectory'), message = self)

    def color_string_to_RGB(self, s):
        
        return numpy.array(s.split(';')).astype(numpy.float32)/255.
        
    def build_ColorTransferFunction(self):
        
        lut = vtk.vtkColorTransferFunction()
        
        for (idx,color) in RGB_COLOURS.values():
            lut.AddRGBPoint(idx,*color)
            
        colours = []
        unic_colours = {}

        color_string_list = [self.color_string_to_RGB(ELEMENTS[at.symbol,'color']) for at in self._atoms]
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
        
    def enable_picking(self):

        self.__pickerObserverId = self._iren.AddObserver("LeftButtonPressEvent", self.on_pick)
        
    def enable_info_picking(self):

        self._iren.AddObserver("LeftButtonPressEvent", self.on_info_pick)

    def disable_picking(self):
        if self.__pickerObserverId is None:
            return
        self._iren.RemoveObserver(self.__pickerObserverId)
        self.__pickerObserverId = None

    def on_show_popup_menu(self, event):

        popupMenu = wx.Menu()

        if self._animationLoop:
            animationLabel = "Stop animation"
        else:
            animationLabel = "Start animation"

        item = popupMenu.Append(wx.ID_ANY, animationLabel)
        popupMenu.Bind(wx.EVT_MENU, self.start_stop_animation, item)

        popupMenu.AppendSeparator()

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
        
        parallel = popupMenu.Append(wx.ID_ANY, 'Parallel Projection', 
            'Parallel Projection', kind=wx.ITEM_CHECK)
        
        popupMenu.Bind(wx.EVT_MENU, self.parallel_proj_onoff, parallel)
        popupMenu.Check(parallel.GetId(), self.camera.GetParallelProjection())
        
        display_bbox = popupMenu.Append(wx.ID_ANY, 'Cell', 'Bounding Box', kind=wx.ITEM_CHECK)
        
        popupMenu.Bind(wx.EVT_MENU, self.bbox_onoff, display_bbox)
        popupMenu.Check(display_bbox.GetId(), self.display_bbox)

        self.PopupMenu(popupMenu)
        
        self.iren.RightButtonReleaseEvent() # Give to vtkinteractor the event that Wx has stoled

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

    def on_clear_selection(self, event=None):
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
        
        pub.sendMessage(("On timer"), message = self)

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

    def show_hide_selection_box(self):

        if self._trajectoryLoaded:
            self.__selectionBox.on_off()
        
    def set_timer_interval(self, timerInterval):

        self._timerInterval = timerInterval
          
    def on_pick(self, obj, evt=None):
        
        if not self._trajectoryLoaded:
            return
        
        pos = obj.GetEventPosition()
        self.picker.AddPickList(self.picking_domain)
        self.picker.PickFromListOn()
        self.picker.Pick(pos[0], pos[1], 0,self._renderer)
        pid = self.picker.GetPointId()
        if pid > 0:
            idx = self.get_atom_index(pid)
            self.pick_atoms([idx])

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
            info = '%s (id:%s) at  %s'%(self._atoms[idx].fullName(), self._atoms[idx].index, '%.3f %.3f %.3f'%tuple(self._atoms[idx].position()))
            LOGGER(info, "info")
        self.picker.InitializePickList()
                
    def pick_atoms(self, atomsList):
        
        if not atomsList:
            return
                        
        self.__pickedAtoms.symmetric_difference_update(atomsList)
                        
        pub.sendMessage(('select atoms'), message = list(self.__pickedAtoms))
            
    def show_selected_atoms(self, atomsList):

        self.show_selection(atomsList)
        
    def clear_selection(self):
        
        if not self._trajectoryLoaded:
            return
                                        
        self.atomsColours = numpy.copy(self._atomsColours)
        
        for i in range(self._nAtoms):
            self._polydata.GetPointData().GetArray("scalars").SetTuple3(i, self._atomsScales[i], self._atomsColours[i], i)
            
        self._polydata.Modified()
        
        self._iren.Render()
        
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
            pub.sendMessage(('Switch'), message = self)
            
        pub.sendMessage(('Animation'), message = self)
    
    def check_switch_consistancy(self, message):
        
        if not self._animationLoop:
            return

        mv = message
        if self == mv:
            return
        
        self.start_stop_animation(check = False)
            
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
        
        outline_actor = vtk.vtkActor()
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
        
        outline_actor = vtk.vtkActor()
        outline_actor.SetMapper(outline_mapper)
        outline_actor.GetProperty().SetColor(1,1,1)
        outline_actor.GetProperty().SetLineWidth(3)
        
        return outline_actor
     
    def build_polydata(self):   
        '''
        build a vtkPolyData object for a given frame of the trajectory
        '''
        
        self._polydata = vtk.vtkPolyData()
        
        # Converts the numpy coordinates into a vtk array
        coords, self.vtkids = ndarray_to_vtkpoints(self.coords)
        self._polydata.SetPoints(coords)
        del coords
        
        scalars = ndarray_to_vtkarray(self.atomsColours, self._atomsScales, self._nAtoms) 
        self._polydata.GetPointData().SetScalars(scalars) 
        del scalars
        
        bonds = []
        for at in self._atoms:
            for bat in at.bondedTo():
                if set([at.index,bat.index]) not in bonds:
                    bonds.append([at.index,bat.index])
        bonds = ndarray_to_vtkcellarray(bonds)
        self._polydata.SetLines(bonds)
        del bonds
        
        rendmod = self._rendmod
        
        actor_list = []
        line_acteur=None
        ball_acteur=None
        tube_acteur=None
        
        if rendmod in [0,4] :
            line_mapper = vtk.vtkPolyDataMapper()
            if vtk.vtkVersion.GetVTKMajorVersion()<6:
                line_mapper.SetInput(self._polydata)
            else:
                line_mapper.SetInputData(self._polydata)
                
            line_mapper.SetLookupTable(self._lut)
            line_mapper.ScalarVisibilityOn()
            line_mapper.ColorByArrayComponent("scalars", 1)
            line_acteur = vtk.vtkActor()
            line_acteur.GetProperty().SetLineWidth(3)
            line_acteur.SetMapper(line_mapper)
            actor_list.append(line_acteur)
            
        if rendmod in [1,3,4]:
            sphere = vtk.vtkSphereSource()
            sphere.SetCenter(0, 0, 0)
            sphere.SetRadius(0.2)
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
            ball_acteur = vtk.vtkActor()
            ball_acteur.SetMapper(sphere_mapper)
            ball_acteur.GetProperty().SetAmbient(0.2)
            ball_acteur.GetProperty().SetDiffuse(0.5)
            ball_acteur.GetProperty().SetSpecular(0.3)
            actor_list.append(ball_acteur)
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
            tube_mapper = vtk.vtkPolyDataMapper()
            tube_mapper.SetLookupTable(self._lut)
            tube_mapper.SetInputConnection(tubes.GetOutputPort())
            tube_mapper.ScalarVisibilityOn()
            tube_mapper.ColorByArrayComponent("scalars", 1)
            tube_acteur = vtk.vtkActor()
            tube_acteur.SetMapper(tube_mapper)
            tube_acteur.GetProperty().SetAmbient(0.2)
            tube_acteur.GetProperty().SetDiffuse(0.5)
            tube_acteur.GetProperty().SetSpecular(0.3)
            actor_list.append(tube_acteur)
            self.tubes = tubes
        
        self.picking_domain = {0:line_acteur,1:ball_acteur,2:tube_acteur,3:ball_acteur,4:ball_acteur}[rendmod]
        
        basis_vector = self._trajectory.universe.basisVectors()
        if not basis_vector is None:
            self.bbox = self.build_bbox(basis_vector)
            if not self.display_bbox:
                self.bbox.VisibilityOff()
            actor_list.append(self.bbox)
            
        assembly = vtk.vtkAssembly()
        for actor in actor_list:
            assembly.AddPart(actor)
        
        #self.build_real_bbox(assembly)
        
        return assembly
    
    def clear_universe(self):

        if not hasattr(self, "molecule"):
            return 
        
        self.molecule.VisibilityOff()
        self.molecule.ReleaseGraphicsResources(self.get_renwin())
        self._renderer.RemoveActor(self.molecule)
        
        del self.molecule 
  
    def show_universe(self):
        '''
        Update the renderer
        '''
        # deleting old frame
        self.clear_universe()
        
        # creating new polydata
        self.molecule = self.build_polydata()

        # adding polydata to renderer
        self._renderer.AddActor(self.molecule)
        
        # rendering
        self._iren.Render()
             
    def set_configuration(self, frame):
        '''
        Sets a new configuration.
        
        @param frame: the configuration number
        @type frame: integer
        '''
        
        self._currentFrame = frame % len(self._trajectory)
        self._trajectory.universe.setConfiguration(self._trajectory.configuration[self._currentFrame])
        self.coords = self._trajectory.universe.contiguousObjectConfiguration().array
                        
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

    filters = 'NC file (*.nc)|*.nc|All files (*.*)|*.*'
    
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
