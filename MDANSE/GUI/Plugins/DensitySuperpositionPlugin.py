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

:author: Eric C. Pellegrini
'''

import wx
import wx.aui as aui

import vtk

import numpy

from Scientific.IO.NetCDF import NetCDFFile

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.GUI.Plugins.ComponentPlugin import ComponentPlugin

class DensitySuperpositionError(Error):
    pass

class DensitySuperpositionPlugin(ComponentPlugin):
    
    label = "Density superposition"
    
    ancestor = ["molecular_viewer"]
    
    def __init__(self, parent, *args, **kwargs):

        self.currentFilename = None        

        ComponentPlugin.__init__(self, parent, size = parent.GetSize(), *args, **kwargs)
     
    def build_panel(self):
        self._mainPanel = wx.Panel(self, wx.ID_ANY, size=self.GetSize())
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        sb1 = wx.StaticBox(self._mainPanel, wx.ID_ANY, label = "Select file")
        sourcesSizer = wx.StaticBoxSizer(sb1, wx.HORIZONTAL)
        
        self._filelist = wx.Choice(self._mainPanel, wx.ID_ANY)
        self._browse = wx.Button(self._mainPanel, wx.ID_ANY, label="Browse")
        
        sourcesSizer.Add(self._filelist, 1,  wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 0)
        sourcesSizer.Add(self._browse, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        
        # Add to main sizer
        mainSizer.Add(sourcesSizer, 0, wx.ALL|wx.EXPAND, 5)

        sb1 = wx.StaticBox(self._mainPanel, wx.ID_ANY, label = "Contour Level")
        isovSizer = wx.StaticBoxSizer(sb1, wx.HORIZONTAL)
        self.isov_scale = 100.
        self.isov_slider = wx.Slider(self._mainPanel, wx.ID_ANY, style = wx.SL_HORIZONTAL)
        self.isov_slider.Disable()
        
        isovSizer.Add(self.isov_slider, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 0)
        
        self.dim_label = wx.StaticText(self._mainPanel, label="Shape")
        self.dim = wx.TextCtrl(self._mainPanel, wx.ID_ANY, style= wx.SL_HORIZONTAL|wx.TE_READONLY)
        
        self.rendlist_label = wx.StaticText(self._mainPanel, label="Rendering mode")
        self.rendlist = wx.ComboBox(self._mainPanel, id = wx.ID_ANY, choices=["surface","wireframe", "points"], style=wx.CB_READONLY)
        self.rendlist.SetValue("surface")
        
        self.opacity_label = wx.StaticText(self._mainPanel, label="Opacity level [0-1]")
        self.opacity = wx.TextCtrl(self._mainPanel, wx.ID_ANY, style= wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)
        self.opacity.SetValue(str(0.5))
        
        sb2 = wx.StaticBox(self._mainPanel, wx.ID_ANY, label = "Parameters")
        paramsbsizer = wx.StaticBoxSizer(sb2, wx.HORIZONTAL)
        
        gbSizer = wx.GridBagSizer(5,5)

        gbSizer.Add(self.dim_label, (0,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(self.dim, (0,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        gbSizer.Add(self.rendlist_label, (1,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(self.rendlist, (1,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        gbSizer.Add(self.opacity_label, (2,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(self.opacity, (2,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        
        gbSizer.Add(isovSizer, (3,0), span = (3,4), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        
        paramsbsizer.Add(gbSizer, 1, wx.ALL|wx.EXPAND, 5)
        
        # Add to main sizer
        mainSizer.Add(paramsbsizer, 1, wx.ALL|wx.EXPAND, 5)
        
        actionsSizer = wx.BoxSizer(wx.HORIZONTAL)
                        
        clearButton  = wx.Button(self._mainPanel, wx.ID_ANY, label="Clear")
        superButton  = wx.Button(self._mainPanel, wx.ID_ANY, label="Draw")
        
        actionsSizer.Add(clearButton, 0, wx.ALL, 5)
        actionsSizer.Add(superButton, 0, wx.ALL, 5)
                        
        # Add to main sizer
        mainSizer.Add(actionsSizer, 1, wx.ALL|wx.ALIGN_RIGHT, 5)
        
        
        self._mainPanel.SetSizer(mainSizer)        
        mainSizer.Fit(self._mainPanel)
        self._mainPanel.Layout()
        
        self.Bind(wx.EVT_CHOICE, self.on_select_file, self._filelist)
        self.Bind(wx.EVT_BUTTON, self.on_browse, self._browse)
        self.Bind(wx.EVT_BUTTON, self.on_clear, clearButton)
        self.Bind(wx.EVT_BUTTON, self.on_superpose, superButton)
        self.Bind(wx.EVT_SCROLL, self.on_change_isov, self.isov_slider)
        self.Bind(wx.EVT_COMBOBOX, self.on_change_surf_rend_mode, self.rendlist)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_set_opacity, self.opacity)
        
    @property
    def dataDict(self):
        return self._dataDict
    
    @property
    def renderer(self):
        return self.parent._renderer
    
    @property
    def iren(self):
        return self.parent._iren
     
    @property
    def camera(self):
        return self.parent.camera
    
    @property
    def molecule(self):
        return self.parent.molecule
    
    @property
    def surface(self):
        return self.parent._surface
    
    @surface.setter
    def surface(self, value):
        self.parent._surface = value
        
    @property
    def iso(self):
        return self.parent._iso
    
    @iso.setter
    def iso(self, value):
        self.parent._iso = value
    
    @property
    def cell_bounds_coords(self):
        return self.parent.cell_bounds_coords 
    
    def unique(self, key, dic):
        skey = key
        i = 0
        while key in dic.keys():
            key = skey + '_%d'%i
            i += 1
        return key     
    
    def on_keyboard_input(self, obj, event):
        key = self.iren.GetKeyCode()
        s = self.get_spacing()
        if key in ['x']:
            self.xyz = [1,0,0]
        elif key in ['y']:
            self.xyz = [0,1,0]
        elif key in ['z']:
            self.xyz = [0,0,1]
        elif key in ['+']:
            self.surface.AddPosition(self.xyz[0]*s[0]/2., self.xyz[1]*s[1]/2., self.xyz[2]*s[2]/2.)
        elif key in ['-']:
            self.surface.AddPosition(-self.xyz[0]*s[0]/2., -self.xyz[1]*s[1]/2., -self.xyz[2]*s[2]/2.)
        self.iren.Render()

    def on_browse(self, event):
        filters = 'NC file (*.nc)|*.nc|All files (*.*)|*.*'
        dialog = wx.FileDialog ( None, message = 'Open file...', wildcard=filters, style=wx.MULTIPLE)
        if dialog.ShowModal() == wx.ID_CANCEL:
            return
        
        pathlist = dialog.GetPaths()
        
        for i in range(len(pathlist)):
            filename = pathlist[i]
            if filename in self._filelist.GetStrings():
                continue
            self._filelist.Append(filename)
        self._filelist.Select(self._filelist.GetCount()-1)
        self.select_file(filename)


    def select_file(self, filename):
        self.currentFilename = filename
        f = NetCDFFile(filename,"r")
        variables = f.variables
        
        if not variables.has_key('molecular_trace'):
            raise DensitySuperpositionError('Trace file format not compatible with Plugin')
        
        self.dim.SetValue(str(variables['molecular_trace'].getValue().shape))
        f.close()
            
    def on_select_file(self, event):
        if event.GetString() == self.currentFilename:
            return
        self.select_file(event.GetString())

    def get_file(self):
        return self._filelist.GetStringSelection()

    def get_variable(self):
        return self.selectedVar
    
    def get_spacing(self):
        spacing = float(self.spacing.GetValue())
        return numpy.array([spacing, spacing, spacing])
    
    def on_clear(self, event=None):
        if self.surface is None:
            return 
        
        self.surface.VisibilityOff()
        self.surface.ReleaseGraphicsResources(self.iren.GetRenderWindow())
        self.renderer.RemoveActor(self.surface)
        self.parent.del_surface()
        self.iren.Render()
    
    def on_superpose(self, event):
        self.on_clear()
        rendtype = self.rendlist.GetValue()
        opacity = float(self.opacity.GetValue())
        filename = self.get_file()
        
        f = NetCDFFile(filename,"r")
        variables = f.variables
        
        data = variables['molecular_trace'].getValue()
        origin = variables['origin'].getValue()
        spacing = variables['spacing'].getValue()
        
        f.close()
        
        mi, ma = self.draw_isosurface(data, rendtype, opacity, origin, spacing)
        self.isov_slider.SetRange(mi, ma)
        self.isov_slider.Enable()
    
    def close(self):
        self.on_clear()
    
    
    def plug(self):
        self.parent.mgr.GetPane(self).Float().CloseButton(True).BestSize((360, 300))
        self.parent.mgr.Update()
        
    def array_to_3d_imagedata(self, data, spacing):
        if data.ndim !=3:
            raise DensitySuperpositionError('Data dimension should be 3')
        nx = data.shape[0]
        ny = data.shape[1]
        nz = data.shape[2]
        image = vtk.vtkImageData()
        image.SetDimensions(nx,ny,nz)
        dx, dy, dz = spacing
        image.SetSpacing(dx,dy,dz)
        image.SetExtent(0, nx-1, 0, ny-1, 0, nz-1)
        if vtk.vtkVersion.GetVTKMajorVersion()<6:
            image.SetScalarTypeToDouble()
            image.SetNumberOfScalarComponents(1)
        else:
            image.AllocateScalars(vtk.VTK_DOUBLE,1)
        
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    image.SetScalarComponentFromDouble(i,j,k,0,data[i,j,k])
                    
        return image

    def draw_isosurface(self, data, rendtype, opacity, origin, spacing):
        self.image = self.array_to_3d_imagedata(data, spacing)
        isovalue = data.mean()
        mi, ma = data.min(), data.max()
        
        self.iso = vtk.vtkMarchingContourFilter()
        self.iso.UseScalarTreeOn()
        self.iso.ComputeNormalsOn()
        if vtk.vtkVersion.GetVTKMajorVersion()<6:
            self.iso.SetInput(self.image)
        else:
            self.iso.SetInputData(self.image)
        self.iso.SetValue(0,isovalue)

        self.depthSort = vtk.vtkDepthSortPolyData()
        self.depthSort.SetInputConnection(self.iso.GetOutputPort())
        self.depthSort.SetDirectionToBackToFront()
        self.depthSort.SetVector(1, 1, 1)
        self.depthSort.SetCamera(self.camera)
        self.depthSort.SortScalarsOn()
        self.depthSort.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(self.depthSort.GetOutputPort())
        mapper.ScalarVisibilityOff()
        mapper.Update()
 
        self.surface = vtk.vtkActor()
        self.surface.SetMapper(mapper)
        self.surface.GetProperty().SetColor((0,0.5,0.75))
        self.surface.GetProperty().SetOpacity(opacity)
        self.surface.PickableOff()

        if rendtype=='wireframe':
            self.surface.GetProperty().SetRepresentationToWireframe()
        elif rendtype=='surface':
            self.surface.GetProperty().SetRepresentationToSurface()
        elif rendtype=='points':
            self.surface.GetProperty().SetRepresentationToPoints() 
            self.surface.GetProperty().SetPointSize(5)
        else:
            self.surface.GetProperty().SetRepresentationToWireframe()
        self.surface.GetProperty().SetInterpolationToGouraud()
        self.surface.GetProperty().SetSpecular(.4)
        self.surface.GetProperty().SetSpecularPower(10)
        
        self.renderer.AddActor(self.surface)
        
        self.surface.SetPosition(origin[0], origin[1], origin[2])
            
        self.iren.Render()
        
        return mi, ma
    
    def cpt_isosurf(self, event = None):
        try :
            isov = float(self.isov.GetValue())
        except:
            raise DensitySuperpositionError('Contour level has wrong format : %s'%self.isov.GetValue())
        self.iso.SetValue(0,isov)
        self.iso.Update()
        self.iren.Render()
        
    def on_change_isov(self, event = None):
        if self.iso is None:
            return
        isov = float(self.isov_slider.GetValue())/self.isov_scale
        self.iso.SetValue(0,isov)
        self.iso.Update()
        self.iren.Render()
    
    def on_set_opacity(self, event=None):
        if self.surface is None:
            return 
        opct = float(self.opacity.GetValue())
        self.surface.GetProperty().SetOpacity(opct)
        self.iren.Render()

    def on_change_surf_rend_mode(self, event = None):
        if self.surface is None:
            return 
        rendtype = self.rendlist.GetValue()
        if rendtype =='wireframe':
            self.surface.GetProperty().SetRepresentationToWireframe()
        elif rendtype =='surface':
            self.surface.GetProperty().SetRepresentationToSurface()
        elif rendtype == 'points':
            self.surface.GetProperty().SetRepresentationToPoints()
            self.surface.GetProperty().SetPointSize(3)
        self.iren.Render()


class FakeIren(object):
    def AddObserver(self, *args, **kwargs):
        pass
        
class TestFrame(wx.Frame):
    
    def __init__(self, parent, title="Density Superposition"):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title, style=wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER)
        
        self._renderer = None
        self._iren = FakeIren()
        self.camera = None
        self.molecule = None
        
        self._mgr = aui.AuiManager(self)
        
        self.__build_dialog()

    def __build_dialog(self):
        self.SetSize((360, 300))
        self.plugin = DensitySuperpositionPlugin(self)
        self._mgr.AddPane(self.plugin, aui.AuiPaneInfo().DestroyOnClose().Dock().CaptionVisible(True).CloseButton(True).BestSize(self.GetSize()))
        self._mgr.Update() 

REGISTRY["density_superposition"] = DensitySuperpositionPlugin

if __name__ == "__main__":
    app = wx.App(False)
    f = TestFrame(None)
    f.Show()
    app.MainLoop()
