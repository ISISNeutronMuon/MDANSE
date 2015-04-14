# Standards imports
import os
import collections
import warnings

# The wx imports.
import wx
import wx.aui as aui
import wx.lib.mixins.listctrl  as  listmix

# The matplotlib imports.
import matplotlib as mpl
from matplotlib.ticker import AutoMinorLocator, MultipleLocator, NullLocator, AutoLocator
from matplotlib.widgets import Cursor
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg, NavigationToolbar2WxAgg
from matplotlib.figure import Figure
from matplotlib.colors import LogNorm, Normalize, NoNorm

# The VTK imports.
import vtk
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor 

# The numpy imports.
import numpy as np

# The Scientific imports.
from Scientific.IO.NetCDF import NetCDFFile

# The nmoldyn imports.
from nMOLDYN import LOGGER
from nMOLDYN.Core.Error import Error
from nMOLDYN.Framework.Plugins.Plugin import ComponentPlugin
from nMOLDYN.Externals.magnitude import magnitude
from nMOLDYN.GUI.Resources.Icons import ICONS, scaled_bitmap

NORMALIZER = {'log': LogNorm(), 'auto' : Normalize()}

class Plotter3d(wx.Panel):
    type = '3d'
    def __init__(self, parent, *args, **kwargs):
        '''
        The constructor.
        '''
        wx.Panel.__init__(self, parent, *args, **kwargs)
        
        self.parent = parent
        
        self._mgr = aui.AuiManager(self)
        
        self.build_panel()
        
    def build_panel(self):
        self.viewer = wx.Panel(self)
        
        self.iren = wxVTKRenderWindowInteractor(self.viewer, -1, size=(500,500), flag=wx.EXPAND)
        self.iren.SetPosition((0,0))
        # define interaction style
        self.iren.GetInteractorStyle().SetCurrentStyleToTrackballCamera() # change interaction style
        self.iren.Enable(1)
        
        # create renderer  
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(1, 1, 1)
        self.iren.GetRenderWindow().AddRenderer(self.renderer)
    
        # cam stuff
        self.camera=vtk.vtkCamera() # create camera 
        self.renderer.SetActiveCamera(self.camera) # associate camera to renderer
        self.camera.SetFocalPoint(0, 0, 0)
        self.camera.SetPosition(0, 0, 0)
        
        self.data = None
        self.image = None
        self.axes = None
        self.actor_list = []
        self.plot_type = '' 
        
        Sizer = wx.BoxSizer(wx.VERTICAL)
        Sizer.Add(self.iren, 1, wx.EXPAND, 0)
        
        self.viewer.SetSizer(Sizer)        
        Sizer.Fit(self.viewer)
        self.viewer.Layout()
        
        self._mgr.AddPane(self.viewer, aui.AuiPaneInfo().Center().Dock().DestroyOnClose(False).CloseButton(False).CaptionVisible(False).MinSize(self.iren.GetSize()))
        self._mgr.Update()
    
    def array_to_2d_imagedata(self):
        if self.data.ndim !=2:
            raise PlotterError('Data dimension should be 2')
        nx = self.data.shape[0]
        ny = self.data.shape[1]
        nz = 1
        image = vtk.vtkImageData()
        image.SetDimensions(nx,ny,1)
        image.SetExtent(0, nx-1, 0, ny-1, 0, nz-1)
        if vtk.vtkVersion.GetVTKMajorVersion()<6:
            image.SetScalarTypeToDouble()
            image.SetNumberOfScalarComponents(1)
        else:
            image.AllocateScalars(vtk.VTK_DOUBLE,1)
        image.SetSpacing(1.,1.,0.)
        for i in range(nx):
            for j in range(ny):
                image.SetScalarComponentFromDouble(i,j,0,0,self.data[i,j])
        return image

    def array_to_3d_imagedata(self):
        if self.data.ndim !=3:
            raise PlotterError('Data dimension should be 3')
        nx = self.data.shape[0]
        ny = self.data.shape[1]
        nz = self.data.shape[2]
        image = vtk.vtkImageData()
        image.SetDimensions(nx,ny,nz)
        image.SetExtent(0, nx-1, 0, ny-1, 0, nz-1)
        if vtk.vtkVersion.GetVTKMajorVersion()<6:
            image.SetScalarTypeToDouble()
            image.SetNumberOfScalarComponents(1)
        else:
            image.AllocateScalars(vtk.VTK_DOUBLE,1)
        
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    image.SetScalarComponentFromDouble(i,j,k,0,self.data[i,j,k])
        return image
    
    def scalarfield(self, data):
        self.data = data
        self.settings = wx.Panel(self)
        
        self.plot_type = self.type = 'scalarfield'
        
        self.image = self.array_to_3d_imagedata()

        imageCast = vtk.vtkImageCast()
        if vtk.vtkVersion.GetVTKMajorVersion()<6:
            imageCast.SetInput(self.image)
        else:
            imageCast.SetInputData(self.image)
         
        imageCast.SetOutputScalarTypeToUnsignedShort()
    
        # Create transfer mapping scalar value to opacity
        opacityTransferFunction = vtk.vtkPiecewiseFunction()
        opacityTransferFunction.AddPoint(self.data.min(), 0)
        opacityTransferFunction.AddPoint(self.data.max(), 1)
        
        # Create transfer mapping scalar value to color
        colorTransferFunction = vtk.vtkColorTransferFunction()
        colorTransferFunction.SetColorSpaceToRGB()
        colorTransferFunction.AddRGBPoint(self.data.min(), 0, 0, 1)
#         colorTransferFunction.AddRGBPoint((self.data.min()+self.data.max())/2., 0, 1, 0)
        colorTransferFunction.AddRGBPoint(self.data.max(), 1, 0, 0)
        scalarBar = vtk.vtkScalarBarActor()
        # Must add this to avoid vtkTextActor error
        scalarBar.SetTitle("")
        scalarBar.SetWidth(0.1)
        scalarBar.SetHeight(0.9)
        scalarBar.SetLookupTable(colorTransferFunction)
         
        self.outline = vtk.vtkOutlineFilter()
        self.outline.SetInputConnection(imageCast.GetOutputPort())
        self.outline.Update()
             
        outlineMapper = vtk.vtkPolyDataMapper()
        if vtk.vtkVersion.GetVTKMajorVersion()<6:
            outlineMapper.SetInputConnection(self.outline.GetOutputPort())
        else:
            outlineMapper.SetInputData(self.outline.GetOutputDataObject(0))
            
             
        box=vtk.vtkActor()
        box.SetMapper(outlineMapper)
        box.GetProperty().SetColor(0,0,0)
         
        # The property describes how the data will look
        volumeProperty = vtk.vtkVolumeProperty()
        volumeProperty.SetColor(colorTransferFunction)
        volumeProperty.SetScalarOpacity(opacityTransferFunction)
        volumeProperty.ShadeOn()
        volumeProperty.SetInterpolationTypeToLinear()
         
        # The mapper / ray cast function know how to render the data
        compositeFunction = vtk.vtkVolumeRayCastCompositeFunction()
        volumeMapper = vtk.vtkVolumeRayCastMapper()
        volumeMapper.SetVolumeRayCastFunction(compositeFunction)
        volumeMapper.SetInputConnection(imageCast.GetOutputPort())

        # The volume holds the mapper and the property and
        # can be used to position/orient the volume
        volume = vtk.vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)
         
        self.renderer.AddVolume(volume)
        self.renderer.AddActor2D(scalarBar)
        self.renderer.AddActor(box)
        self.build_axes()
        self.actor_list.append(volume)      
        self.actor_list.append(scalarBar)
        self.actor_list.append(box)
          
        self.center_on_actor(volume, out=True)
        self.iren.Render()
        
        control_sizer = wx.BoxSizer()
        content1 = wx.StaticText(self.settings, -1, "X :", style=wx.ALIGN_CENTER_VERTICAL)
        self.x_slider = wx.Slider(self.settings,id=wx.ID_ANY,value=100,minValue=0,maxValue=200, style= wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.x_slider.Bind(wx.EVT_SCROLL, self.x_spacing_onmove)
        content2 = wx.StaticText(self.settings, -1, "Y :", style=wx.ALIGN_CENTER_VERTICAL)
        self.y_slider = wx.Slider(self.settings,id=wx.ID_ANY,value=100,minValue=0,maxValue=200, style= wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.y_slider.Bind(wx.EVT_SCROLL, self.y_spacing_onmove)
        content3 = wx.StaticText(self.settings, -1, "Z :", style=wx.ALIGN_CENTER_VERTICAL)
        self.z_slider = wx.Slider(self.settings,id=wx.ID_ANY,value=100,minValue=0,maxValue=200, style= wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.z_slider.Bind(wx.EVT_SCROLL, self.z_spacing_onmove)
        
        # build sizer
        control_sizer.Add((20, -1),proportion= 0, flag=wx.EXPAND | wx.ALIGN_RIGHT)
        control_sizer.Add(content1, proportion=0, flag = wx.ALIGN_BOTTOM)
        control_sizer.Add(self.x_slider,proportion=1, flag=wx.EXPAND)
        control_sizer.Add((20, -1),proportion= 0, flag=wx.EXPAND | wx.ALIGN_RIGHT)
        control_sizer.Add(content2, proportion=0, flag = wx.ALIGN_BOTTOM)
        control_sizer.Add(self.y_slider,proportion=1, flag=wx.EXPAND)
        control_sizer.Add((20, -1),proportion= 0, flag=wx.EXPAND | wx.ALIGN_RIGHT)
        control_sizer.Add(content3, proportion=0, flag = wx.ALIGN_BOTTOM)
        control_sizer.Add(self.z_slider,proportion=1, flag=wx.EXPAND) 
        
        self.save_fig  = wx.Button(self.settings, wx.ID_ANY, label="Save current view")
        self.save_fig.Bind(wx.EVT_BUTTON, self.Screen_shot)
        
        Sizer = wx.BoxSizer(wx.VERTICAL)
        
        Sizer.Add(control_sizer, 0, wx.EXPAND, 0)
        Sizer.Add(self.save_fig, 0, wx.EXPAND, 0)
       
        self.settings.SetSizer(Sizer)        
        Sizer.Fit(self.settings)
        self.settings.Layout()
        
        self._mgr.AddPane(self.settings, aui.AuiPaneInfo().Center().Dock().Bottom().CloseButton(False).CaptionVisible(False))
        self._mgr.Update()
         
    def elevation(self, data):
        self.data = data
        
        
        self.settings = wx.Panel(self)
        
        self.plot_type= self.type = 'elevation'
        
        self.image = self.array_to_2d_imagedata()
        
        geometry = vtk.vtkImageDataGeometryFilter()  
        if vtk.vtkVersion.GetVTKMajorVersion()<6:
            geometry.SetInput(self.image)
        else:
            geometry.SetInputData(self.image)
            
        self.warp = vtk.vtkWarpScalar()
        self.warp.SetInputConnection(geometry.GetOutputPort())
        self.warp.SetScaleFactor(1)
        self.warp.UseNormalOn()
        self.warp.SetNormal(0,0,1)
        self.warp.Update()
        
        lut =vtk.vtkLookupTable()
        lut.SetTableRange(self.image.GetScalarRange())
        lut.SetNumberOfColors(256)
        lut.SetHueRange(0.7, 0)
        lut.Build()
        
        merge=vtk.vtkMergeFilter()
        if vtk.vtkVersion.GetVTKMajorVersion()<6:
            merge.SetGeometry(self.warp.GetOutput())
            merge.SetScalars(self.image)
        else:
            merge.SetGeometryInputData(self.warp.GetOutput())
            merge.SetScalarsData(self.image)
        merge.Update()
        
        self.outline = vtk.vtkOutlineFilter()
        self.outline.SetInputConnection(merge.GetOutputPort())
        self.outline.Update()
        
        outlineMapper = vtk.vtkPolyDataMapper()
        if vtk.vtkVersion.GetVTKMajorVersion()<6:
            outlineMapper.SetInputConnection(self.outline.GetOutputPort())
        else:
            outlineMapper.SetInputData(self.outline.GetOutputDataObject(0))
        
        box=vtk.vtkActor()
        box.SetMapper(outlineMapper)
        box.GetProperty().SetColor(0,0,0)
        
        self.renderer.AddActor(box)
        self.actor_list.append(box)
        
        mapper=vtk.vtkPolyDataMapper()
        mapper.SetLookupTable(lut)
        mapper.SetScalarRange(self.image.GetScalarRange())
        mapper.SetInputConnection(merge.GetOutputPort())
        
        actor=vtk.vtkActor()
        actor.SetMapper(mapper)
        self.renderer.AddActor(actor)
        self.actor_list.append(actor)
        
        scalarBar = vtk.vtkScalarBarActor()
        scalarBar.SetTitle("")
        scalarBar.SetWidth(0.1)
        scalarBar.SetHeight(0.9)
        scalarBar.SetLookupTable(lut)
        self.renderer.AddActor2D(scalarBar)
        self.actor_list.append(scalarBar)
        
        self.build_axes(noZaxis = True)
        
        self.center_on_actor(actor)
        self.iren.Render()
        self.warp.SetScaleFactor(0)
        self.warp.Update()
        self.outline.Update()
        
        self.renderer.ResetCameraClippingRange()
        self.iren.Render()
        
        
        sb0 = wx.StaticBox(self.settings, wx.ID_ANY, label = "Scaling Panel")
        Sizer0 = wx.StaticBoxSizer(sb0, wx.HORIZONTAL)
        

        content1 = wx.StaticText(self.settings, -1, "X")
        
        self.x_Offset = wx.TextCtrl(self.settings, wx.ID_ANY, size = (45,27),style = wx.TE_PROCESS_ENTER )
        self.Bind(wx.EVT_TEXT_ENTER, self.x_spacing_onmove ,self.x_Offset)
        self.x_Offset.SetValue('1.0')
        
        
        self.x_slider = wx.Slider(self.settings,id=wx.ID_ANY,value=100,minValue=0,maxValue=200, style= wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.x_slider.Bind(wx.EVT_SCROLL, self.x_spacing_onmove)
        content2 = wx.StaticText(self.settings, -1, "Y")
        
        self.y_Offset = wx.TextCtrl(self.settings, wx.ID_ANY,size = (45,27), style = wx.TE_PROCESS_ENTER )
        self.Bind(wx.EVT_TEXT_ENTER, self.y_spacing_onmove ,self.y_Offset)
        self.y_Offset.SetValue('1.0')
        
        self.y_slider = wx.Slider(self.settings,id=wx.ID_ANY,value=100,minValue=0,maxValue=200, style= wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.y_slider.Bind(wx.EVT_SCROLL, self.y_spacing_onmove)
        
        sb1 = wx.StaticBox(self.settings, wx.ID_ANY, label = "Elevation Panel")
        Sizer1 = wx.StaticBoxSizer(sb1, wx.HORIZONTAL)
        
        content3 = wx.StaticText(self.settings, -1, "Warp")
        
        
        self.z_Offset = wx.TextCtrl(self.settings, wx.ID_ANY, size = (45,27),style = wx.TE_PROCESS_ENTER )
        self.Bind(wx.EVT_TEXT_ENTER, self.z_spacing_onmove ,self.z_Offset)
        self.z_Offset.SetValue('1.0')
        
        
        self.z_slider = wx.Slider(self.settings,id=wx.ID_ANY,value=0,minValue=0,maxValue=100, style= wx.SL_HORIZONTAL )
        self.z_slider.Bind(wx.EVT_SCROLL, self.z_spacing_onmove)
        
        # build sizer
        Sizer0.Add(content1, proportion=0, flag = wx.ALIGN_BOTTOM)
        Sizer0.Add(self.x_Offset,proportion=0, flag= wx.ALIGN_CENTER_VERTICAL)
        Sizer0.Add(self.x_slider,proportion=1, flag= wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        Sizer0.Add((20, -1),proportion= 0, flag= wx.ALIGN_CENTER_VERTICAL)
        Sizer0.Add(content2, proportion=0, flag = wx.ALIGN_CENTER_VERTICAL)
        Sizer0.Add(self.y_Offset,proportion=0, flag= wx.ALIGN_BOTTOM)
        Sizer0.Add(self.y_slider,proportion=1, flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        
        Sizer1.Add(content3, proportion=0, flag = wx.ALIGN_CENTER_VERTICAL)
        Sizer1.Add(self.z_Offset,proportion=0, flag= wx.ALIGN_CENTER_VERTICAL)
        Sizer1.Add(self.z_slider,proportion=1, flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND) 
        
        self.save_fig  = wx.Button(self.settings, wx.ID_ANY, label="Save current view")
        self.save_fig.Bind(wx.EVT_BUTTON, self.Screen_shot)
        
        Sizer = wx.BoxSizer(wx.VERTICAL)
        
        HSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        HSizer.Add(Sizer0, 1, wx.EXPAND, 0)
        HSizer.Add(Sizer1, 1, wx.EXPAND, 0)
        
        
        Sizer.Add(HSizer, 0, wx.EXPAND, 0)
        Sizer.Add(self.save_fig, 0, wx.EXPAND, 0)
       
        self.settings.SetSizer(Sizer)
        Sizer.Fit(self.settings)
        self.settings.Layout()
        
        self._mgr.AddPane(self.settings, aui.AuiPaneInfo().Center().Dock().Bottom().CloseButton(False).CaptionVisible(False))
        self._mgr.Update()
        
    def x_spacing_onmove(self, evt=None):
        if self.image:
            try:
                offset_mupltiplier = float(self.x_Offset.GetValue())
            except:
                offset_mupltiplier = 1.
            _,y,z = self.image.GetSpacing ()
            val = self.x_slider.GetValue()
            x = (val*offset_mupltiplier)/100.
            self.axes.SetTotalLength( (self.data.shape[0]-1)*x, (self.data.shape[1]-1)*y, self.data.max()*z )
            self.image.SetSpacing(x,y,z)
            if self.plot_type=='elevation':
                self.warp.Update()
            self.outline.Update()
            self.iren.Render()
             
    def y_spacing_onmove(self, evt=None):
        if self.image:
            try:
                offset_mupltiplier = float(self.y_Offset.GetValue())
            except:
                offset_mupltiplier = 1.
            x,_,z = self.image.GetSpacing ()
            val = self.y_slider.GetValue()
            y = (val*offset_mupltiplier)/100.
            self.axes.SetTotalLength( (self.data.shape[0]-1)*x , (self.data.shape[1]-1)*y, self.data.max()*z )
            self.image.SetSpacing(x,y,z)
            if self.plot_type=='elevation':
                self.warp.Update()
            self.outline.Update()
            self.iren.Render()
            
    def z_spacing_onmove(self, evt=None):
        if self.image:
            try:
                offset_mupltiplier = float(self.z_Offset.GetValue())
            except:
                offset_mupltiplier = 1.
            x,y,_ = self.image.GetSpacing ()
            val = self.z_slider.GetValue()
            z = (val/25.)*offset_mupltiplier
            self.axes.SetTotalLength( (self.data.shape[0]-1)*x, (self.data.shape[1]-1)*y, self.data.max()*z )
            if self.plot_type=='elevation':
                    self.warp.SetScaleFactor(z)
                    self.warp.Update()
            self.image.SetSpacing(x,y,z)
            self.renderer.ResetCameraClippingRange()
            self.outline.Update()
            self.iren.Render()
    
    def reset_sliders(self):
        self.x_slider.SetValue(0)
        self.y_slider.SetValue(0)
        self.z_slider.SetValue(0)    
        
    def isosurface(self, data, isovalue, rendtype):
        self.data = data
        
        self.settings = wx.Panel(self)
        
        self.plot_type = self.type = 'isosurface'
        
        self.image = self.array_to_3d_imagedata()

        self.iso = vtk.vtkMarchingContourFilter()
        self.iso.UseScalarTreeOn()
        self.iso.ComputeNormalsOn()
        if vtk.vtkVersion.GetVTKMajorVersion()<6:
            self.iso.SetInput(self.image)
        else:
            self.iso.SetInputData(self.image)
        self.iso.SetValue(0,isovalue)

        depthSort = vtk.vtkDepthSortPolyData()
        depthSort.SetInputConnection(self.iso.GetOutputPort())
        depthSort.SetDirectionToBackToFront()
        depthSort.SetVector(1, 1, 1)
        depthSort.SetCamera(self.camera)
        depthSort.SortScalarsOn()
        depthSort.Update()
 
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(depthSort.GetOutputPort())
        mapper.ScalarVisibilityOff()
        mapper.Update()
 
        self.surf = vtk.vtkActor()
        self.surf.SetMapper(mapper)
        self.surf.GetProperty().SetColor((0,0.5,0.75))
        self.surf.PickableOff()
         
        outline = vtk.vtkOutlineFilter()
        
        if vtk.vtkVersion.GetVTKMajorVersion()<6:
            outline.SetInput(self.image)
        else:
            outline.SetInputData(self.image)
        outlineMapper = vtk.vtkPolyDataMapper()
        outlineMapper.SetInputConnection(outline.GetOutputPort())
        box=vtk.vtkActor()
        box.SetMapper( outlineMapper )
        box.GetProperty().SetColor((0,0,0))
        box.PickableOff()
     
        self.renderer.AddActor(box)
     
        if rendtype=='w':
            self.surf.GetProperty().SetRepresentationToWireframe()
        elif rendtype=='s':
            self.surf.GetProperty().SetRepresentationToSurface()
        elif rendtype=='p':
            self.surf.GetProperty().SetRepresentationToPoints() 
            self.surf.GetProperty().SetPointSize(5)
        else:
            self.surf.GetProperty().SetRepresentationToWireframe()
        self.surf.GetProperty().SetInterpolationToGouraud()
        self.surf.GetProperty().SetSpecular(.4)
        self.surf.GetProperty().SetSpecularPower(10)
        
        self.renderer.AddActor(self.surf)
        self.build_axes()
 
        self.center_on_actor(self.surf, out=True)
        
        
        sb1 = wx.StaticBox(self.settings, wx.ID_ANY, label = "Contour Level")
        isovSizer = wx.StaticBoxSizer(sb1, wx.HORIZONTAL)
        self.isov_scale = 100.
        self.isov_slider = wx.Slider(self.settings, wx.ID_ANY, value = isovalue*self.isov_scale , 
                                     minValue = int(self.data.min()*self.isov_scale) , 
                                     maxValue = int(self.data.max()*self.isov_scale),  
                                     size = (60,27), style = wx.SL_HORIZONTAL)
        
        self.isov_slider.Bind(wx.EVT_SCROLL,self.on_change_isov)
        isovSizer.Add(self.isov_slider, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        
        
        rendSizer = wx.BoxSizer()
        self.rendlist_label = wx.StaticText(self.settings, label="Rendering mode")
        self.rendlist = wx.ComboBox(self.settings, id = wx.ID_ANY, choices=["surface","wireframe", "points"], style=wx.CB_READONLY)
        self.rendlist.SetValue("wireframe")
        self.rendlist.Bind(wx.EVT_COMBOBOX, self.on_change_surf_rend_mode)
        
        self.opacity_label = wx.StaticText(self.settings, label="Opacity level [0-1]")
        self.opacity = wx.TextCtrl(self.settings, wx.ID_ANY, style= wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)
        self.opacity.SetValue(str(1.0))
        self.opacity.Bind(wx.EVT_TEXT_ENTER, self.on_set_opacity)
        
        rendSizer.Add(self.rendlist_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        rendSizer.Add(self.rendlist, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        rendSizer.Add(self.opacity_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        rendSizer.Add(self.opacity, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        sb = wx.StaticBox(self.settings, wx.ID_ANY, label = "Slice orientation")
        sliceSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        
        self.sagittal = wx.RadioButton(self.settings, wx.ID_ANY, label = "sagittal (// to Y,Z)")
        self.axial = wx.RadioButton(self.settings, wx.ID_ANY, label = "axial (// to X,Y)")
        self.coronal = wx.RadioButton(self.settings, wx.ID_ANY, label = "coronal (// to X,Z)")
        self.oblique = wx.RadioButton(self.settings, wx.ID_ANY, label = "oblique (// to X,Y+Z)")
        
        self.Bind(wx.EVT_RADIOBUTTON, self.on_slice_selection, self.sagittal)
        self.Bind(wx.EVT_RADIOBUTTON, self.on_slice_selection, self.axial)
        self.Bind(wx.EVT_RADIOBUTTON, self.on_slice_selection, self.coronal)
        self.Bind(wx.EVT_RADIOBUTTON, self.on_slice_selection, self.oblique)
        
        sliceSizer.Add(self.sagittal, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        sliceSizer.Add(self.axial, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        sliceSizer.Add(self.coronal, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        sliceSizer.Add(self.oblique, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        
        self.iren.AddObserver("CharEvent", self.on_keyboard_input)
        self.reslice = None
        key_doc = wx.StaticText(self.settings, wx.ID_ANY, label = "Press '+' and '-' keys to translate the slice")
        
        self.save_fig  = wx.Button(self.settings, wx.ID_ANY, label="Save current view")
        self.save_fig.Bind(wx.EVT_BUTTON, self.Screen_shot)
        
        Sizer = wx.BoxSizer(wx.VERTICAL)
        
        Sizer.Add(rendSizer, 0, wx.EXPAND, 0)
        Sizer.Add(isovSizer, 0, wx.EXPAND, 0)
        Sizer.Add(sliceSizer, 0, wx.EXPAND, 0)
        Sizer.Add(key_doc, 0, wx.EXPAND, 0)
        Sizer.Add(self.save_fig, 0, wx.EXPAND, 0)
        
        self.iren.Render()
        
        
        self.settings.SetSizer(Sizer)
        Sizer.Fit(self.settings)
        self.settings.Layout()
        
        self._mgr.AddPane(self.settings, aui.AuiPaneInfo().Center().Dock().Bottom().CloseButton(False).CaptionVisible(False))
        self._mgr.Update()
        
    def cpt_isosurf(self, event = None):
        try :
            isov = float(self.isov.GetValue())
        except:
            raise PlotterError('Contour level has wrong format : %s'%self.isov.GetValue())
        self.iso.SetValue(0,isov)
        self.iso.Update()
        self.iren.Render()
        
    def on_change_isov(self, event = None):
        isov = float(self.isov_slider.GetValue())/self.isov_scale
        self.iso.SetValue(0,isov)
        self.iso.Update()
        self.iren.Render()
    
    def on_set_opacity(self, event=None):
        opct = float(self.opacity.GetValue())
        self.surf.GetProperty().SetOpacity(opct)
        self.iren.Render()
    
    def on_change_surf_rend_mode(self, event = None):
        rendtype = self.rendlist.GetValue()
        if rendtype =='wireframe':
            self.surf.GetProperty().SetRepresentationToWireframe()
        elif rendtype =='surface':
            self.surf.GetProperty().SetRepresentationToSurface()
        elif rendtype == 'points':
            self.surf.GetProperty().SetRepresentationToPoints()
            self.surf.GetProperty().SetPointSize(3)
        self.iren.Render()
    
    def on_keyboard_input(self, obj, event):
        key = self.iren.GetKeyCode()
        if key in ['+']:
            self.on_move_slice(1)
        elif key in ['-']:
            self.on_move_slice(-1)
            
        elif key == " ":
            self.start_stop_animation()
            
    def build_axes(self, noZaxis = False):
        if self.axes is None:
            self.axes = vtk.vtkAxesActor()
#             self.axes.SetShaftTypeToCylinder()
            if not noZaxis:
                self.axes.SetTotalLength( self.data.shape[0] - 1, self.data.shape[1] - 1, self.data.shape[2] - 1)
            else:
                self.axes.SetTotalLength( self.data.shape[0] - 1, self.data.shape[1] - 1, 0 )
            self.axes.SetNormalizedShaftLength( 1, 1, 1 )
            self.axes.SetNormalizedTipLength( 0, 0, 0 )
#             self.axes.SetNormalizedShaftLength( 0.85, 0.85, 0.85 )
#             self.axes.SetNormalizedTipLength( 0.15, 0.15, 0.15 )
            self.axes.AxisLabelsOn()
            self.axes.GetXAxisTipProperty().SetColor( 0, 0, 1)
            self.axes.GetXAxisShaftProperty().SetColor( 0, 0, 1)
            self.axes.GetXAxisShaftProperty().SetLineWidth (2)
            self.axes.SetXAxisLabelText('x')
            txtprop = vtk.vtkTextProperty()
            txtprop.SetColor(0, 0, 0)
            txtprop.SetFontFamilyToArial()
            txtprop.SetFontSize(12)
            txtprop.SetOpacity(0.5)
            self.axes.GetXAxisCaptionActor2D().SetCaptionTextProperty(txtprop)
            
            self.axes.GetYAxisTipProperty().SetColor( 0, 1, 0)
            self.axes.GetYAxisShaftProperty().SetColor( 0, 1, 0)
            self.axes.GetYAxisShaftProperty().SetLineWidth (2)
            self.axes.SetYAxisLabelText('y')
            txtprop = vtk.vtkTextProperty()
            txtprop.SetColor(0, 0, 0)
            txtprop.SetFontFamilyToArial()
            txtprop.SetFontSize(12)
            txtprop.SetOpacity(0.5)
            self.axes.GetYAxisCaptionActor2D().SetCaptionTextProperty(txtprop)
            
            self.axes.GetZAxisTipProperty().SetColor( 1, 0, 0 )
            self.axes.GetZAxisShaftProperty().SetColor( 1, 0, 0)
            self.axes.GetZAxisShaftProperty().SetLineWidth (2)
            self.axes.SetZAxisLabelText('z')
            txtprop = vtk.vtkTextProperty()
            txtprop.SetColor(0, 0, 0)
            txtprop.SetFontFamilyToArial()
            txtprop.SetFontSize(12)
            txtprop.SetOpacity(0.5)
            self.axes.GetZAxisCaptionActor2D().SetCaptionTextProperty(txtprop)
            
            self.renderer.AddActor(self.axes)   
            self.iren.Render()
        else :
            if self.axes.GetVisibility():
                self.axes.VisibilityOff()
            else:
                self.axes.VisibilityOn()
            self.iren.Render()    
    
    def on_slice_selection(self, event=None):
        orientation = str(event.GetEventObject().GetLabelText()).lower().split()[0]
        self.slice_orientation = orientation
        self.slice()
        self.iren.Render()
    
    def slice(self):
        
        self.clear_universe()
        
        center = [self.data.shape[0]/2.,self.data.shape[1]/2.,self.data.shape[2]/2.]
        # Matrices for axial, coronal, sagittal, oblique view orientations
        axial = vtk.vtkMatrix4x4()
        axial.DeepCopy((1, 0, 0, center[0],
                        0, 1, 0, center[1],
                        0, 0, 1, center[2],
                        0, 0, 0, 1))
        
        coronal = vtk.vtkMatrix4x4()
        coronal.DeepCopy((1, 0, 0, center[0],
                          0, 0, 1, center[1],
                          0,-1, 0, center[2],
                          0, 0, 0, 1))
        
        sagittal = vtk.vtkMatrix4x4()
        sagittal.DeepCopy((0, 0,-1, center[0],
                           1, 0, 0, center[1],
                           0,-1, 0, center[2],
                           0, 0, 0, 1))
        
        oblique = vtk.vtkMatrix4x4()
        oblique.DeepCopy((1, 0, 0, center[0],
                          0, 0.866025, -0.5, center[1],
                          0, 0.5, 0.866025, center[2],
                          0, 0, 0, 1))
        
        orientation = { "sagittal" : sagittal , "axial" : axial, "coronal" : coronal, "oblique" : oblique}
        self.orientation_matrix = orientation[self.slice_orientation]
        
        # Extract a slice in the desired orientation
        self.reslice = vtk.vtkImageReslice()
        if vtk.vtkVersion.GetVTKMajorVersion() < 6:
            self.reslice.SetInput(self.image)
        else:
            self.reslice.SetInputData(self.image)
#             xmi,xma,ymi,yma,zmi,zma
            #self.reslice.SetOutputExtent(0, 100, 0, 100, 0, 0)
        self.reslice.Update()
        self.reslice.SetOutputDimensionality(2)
        self.reslice.SetResliceAxes(orientation[self.slice_orientation])

        table = vtk.vtkLookupTable()
        
        table.SetRange(self.data.min(), self.data.max()) # image intensity range
        table.SetHueRange(0.7, 0)
        table.Build()
        
        # Map the image through the lookup table
        color = vtk.vtkImageMapToColors()
        color.SetLookupTable(table)
        color.SetOutputFormatToRGB()
        color.PassAlphaToOutputOff() 
        color.SetInputConnection(self.reslice.GetOutputPort())
        color.Update()
        
        # Display the image
        self.slice_actor = vtk.vtkImageActor()

        R = np.array(self.ExtractRotMat(self.orientation_matrix)) #extraction de la matrice de rotation depuit la vtk 4x4
        alpha, beta, gamma = self.R2Eul(R)
        self.RotaEuler(self.slice_actor, alpha, beta, gamma)
        
        self.slice_actor.SetPosition(center[0],center[1],center[2])
        if vtk.vtkVersion.GetVTKMajorVersion() < 6:
            self.slice_actor.SetInput(color.GetOutput())
        else:
            self.slice_actor.SetInputData(color.GetOutputDataObject(0))
            self.slice_actor.Update()
        self.actor_list.append(self.slice_actor)
        
        self.renderer.AddActor(self.slice_actor)
    
    def center_on_actor(self,actor, out=False):#TODO out is useless : remove param
        Xmin,Xmax,Ymin,Ymax,Zmin,Zmax = actor.GetBounds()
        Xavg = (Xmin+Xmax)/2. 
        Yavg = (Ymin+Ymax)/2.
        Zavg = (Zmin+Zmax)/2.
        self.camera.SetFocalPoint(Xavg, Yavg, Zavg)
        self.camera.SetPosition(Xavg, Yavg, 3*Zmax)
        
    def clear_universe(self):
        for actor in self.actor_list:
            actor.VisibilityOff()
            self.renderer.RemoveActor(actor)
            actor.ReleaseGraphicsResources(self.iren.GetRenderWindow())
            del actor
        self.plot_type=''
        self.actor_list = []

    def on_move_slice(self, t):
        if self.reslice is None:
            return
        self.reslice.Update()
        matrix = self.reslice.GetResliceAxes()
        # move the center point that we are slicing through
        center = matrix.MultiplyPoint((0, 0, t, 1))
        matrix.SetElement(0, 3, center[0])
        matrix.SetElement(1, 3, center[1])
        matrix.SetElement(2, 3, center[2])
        self.slice_actor.SetPosition(center[0], center[1], center[2])
        self.iren.Render()

    def ExtractRotMat(self, mat):
        res=[[0,0,0],[0,0,0],[0,0,0]]
        for i in range(3):
            for j in range(3):
                res[i][j]=mat.GetElement(i,j)
        return res

    def R2Eul(self, R,tolerance=1e-5):
        """
        R must be an indexable of shape (3,3) and represent and ORTHOGONAL POSITIVE
        DEFINITE matrix. Otherwise, one should use GetEul().
        """
        from numpy.linalg import det
        
        fuzz=1e-3
        R=np.asarray(R,float)
        if det(R) < 0. :
            raise Exception, "determinant is negative\n"+str(R)
        if not np.allclose(np.mat(R)*R.T,np.identity(3),atol=tolerance):
            raise Exception, "not an orthogonal matrix\n"+str(R)
        cang = 2.0-np.sum(np.square([ R[0,2],R[1,2],R[2,0],R[2,1],R[2,2] ]))
        cang = np.sqrt(min(max(cang,0.0),1.0))
        if (R[2,2]<0.0): cang=-cang
        ang= np.arccos(cang)
        beta=np.degrees(ang)
        sang=np.sin(ang)
        if(sang>fuzz):
            alpha=np.degrees(np.arctan2(R[1,2], R[0,2]))
            gamma=np.degrees(np.arctan2(R[2,1],-R[2,0]))
        else:
            alpha=np.degrees(np.arctan2(-R[0,1],R[0,0]*R[2,2]))
            gamma=0.
        if   self.almost(beta,0.,fuzz):
            alpha,beta,gamma = alpha+gamma,  0.,0.
        elif self.almost(beta,180.,fuzz):
            alpha,beta,gamma = alpha-gamma,180.,0.
        alpha=np.mod(alpha,360.);
        gamma=np.mod(gamma,360.)
        if self.almost(alpha,360.,fuzz):
            alpha=0.
        if self.almost(gamma,360.,fuzz):
            gamma=0.
        return alpha,beta,gamma

    def almost(self, a, b, tolerance=1e-7):
        return (abs(a-b)<tolerance) 

    def RotaEuler(self, acteur, alpha ,beta ,gamma):
        acteur.RotateWXYZ(gamma,0,0,1)
        acteur.RotateWXYZ(beta,0,1,0)
        acteur.RotateWXYZ(alpha,0,0,1)

    def Screen_shot(self, event = None):
        windowToImageFilter = vtk.vtkWindowToImageFilter()
        windowToImageFilter.SetInput(self.iren.GetRenderWindow())
        windowToImageFilter.SetMagnification(3) # set the resolution of the output image (3 times the current resolution of vtk render window)
        windowToImageFilter.SetInputBufferTypeToRGBA() # also record the alpha (transparency) channel
        windowToImageFilter.Update()
        
        dlg = wx.FileDialog(self, "Save Figure as...", os.getcwd(), "", "*.png", wx.SAVE|wx.OVERWRITE_PROMPT)
        result = dlg.ShowModal()
        inFile = dlg.GetPath()
        dlg.Destroy()
        if result == wx.ID_CANCEL:    #Either the cancel button was pressed or the window was closed
            return
        writer = vtk.vtkPNGWriter()
        writer.SetFileName(inFile)
        writer.SetInputConnection(windowToImageFilter.GetOutputPort())
        writer.Write()


class Plotter2d(wx.Panel):
    type = 'image'
    def __init__(self, parent, data = None):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        
        self.setting = None
                
        ### Initialize variables ###
        self.parent = parent
        self.figure = Figure(figsize=(5,4), dpi=None)
        self.axes = self.figure.add_axes( (10,10,10,10), frameon=True, axisbg='b')
        self.canvas = FigureCanvasWxAgg( self, wx.ID_ANY, self.figure )
        self.toolbar = NavigationToolbar2WxAgg(self.canvas)
        self.ax = None
        self.color_bar = None
        self.slice_checkbox = wx.CheckBox(self, id=wx.ID_ANY, label="Slicing mode")
        
        self.annotation =  wx.StaticText(self, label='x : , y : , data[x,y] :' , style=wx.ALIGN_CENTER_VERTICAL)
        
        hsizer = wx.BoxSizer()
        hsizer.Add(self.toolbar, 0, flag=wx.ALL|wx.EXPAND)
        hsizer.Add(self.slice_checkbox, 0, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL )
        
        ### sizer ###
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, flag=wx.EXPAND) 
        self.sizer.Add(hsizer, 0, flag=wx.EXPAND)
        self.SetSizer(self.sizer) 
        
        ### set bindings ###
        self.Bind(wx.EVT_CHECKBOX, self.slice, id = self.slice_checkbox.GetId())
        
        # Slice attributes
        self.unique = False
        self.slice_event_id = None
        
        self.slice_coords = []
        self.slice_widget = []
        
#         self.segment_slice_canvas = None        
#         self.segment_slice_dialog = None
#         self.segment_slice_plot = None
#         self.segment_slice_fig = None 
#         self.segment_slice_color_index = 0
#         self.segment_slice_legend = []
        
        self.cross_slice_canvas = None 
        self.cross_slice_dialog = None
        self.h_cross_slice_plot = None
        self.v_cross_slice_plot = None
        self.cross_slice_fig = None
        self.cross_slice_color_index = -1
        self.h_cross_slice_legend = []
        self.v_cross_slice_legend = []
        self.color_list = collections.OrderedDict([['blue','b'],['green','g'],['red','r'],['cyan','c'],['magenta','m'],['yellow','y'],['black','k']])
        
        self.Xmin = 0
        self.Ymin = 0
        self.Xmax = 0
        self.Ymax = 0
        
        self.Xunit = None
        self.Yunit = None
        
        self.Xinit_unit = None
        self.Yinit_unit = None
        
        self.Xaxis =  [] 
        self.Yaxis =  []
        
        self.Xaxis_label = ''
        self.Yaxis_label = ''
        
        self.Xticks =  [] 
        self.Yticks =  []
        
        self.Xlabel = ''
        self.Ylabel = ''
        
        self.aspect = 'equal'
        self.interpolation = 'nearest'
        self.normType = 'none'
        
        hsizer = wx.BoxSizer()
        hsizer.Add(self.toolbar, 0, flag=wx.ALL|wx.EXPAND)
        hsizer.Add(self.slice_checkbox, 0, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL )
        hsizer.AddSpacer(25)
        hsizer.Add(self.annotation, 0, flag=wx.ALIGN_CENTER_VERTICAL)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, flag=wx.EXPAND) 
        self.sizer.Add(hsizer, 0, flag=wx.EXPAND)
        self.SetSizer(self.sizer) 
        
        ### set bindings ###
        self.Bind(wx.EVT_CHECKBOX, self.slice, id = self.slice_checkbox.GetId())
        self.menu_event_id = self.canvas.mpl_connect('button_press_event', self.on_click)
        cursor = Cursor(self.axes)
        self.on_motion_id = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        #### sizer automatically fitting window size ####
        self.toolbar.Realize()
        self.SetSizeHints(600,500,1000,1000) # SetSizeHints(minW, minH, maxW, maxH)
        self.sizer.Fit(self)
        self.Show(True)
    
    @property
    def dataproxy(self):
        return self.parent.dataproxy
    
    @property
    def fmt_Xunit(self):
        if not self.Xunit:
            return ''
        else:    
            return ' (' + self.Xunit + ')'
    
    @property
    def fmt_Yunit(self):
        if not self.Yunit:
            return ''
        else:    
            return ' (' + self.Yunit + ')'
        
    def on_click(self, event = None):
        if event.button != 3:
            return
        
        popupMenu = wx.Menu()

        settings = popupMenu.Append(wx.ID_ANY, "Settings")
        popupMenu.Bind(wx.EVT_MENU, self.image_setting_dialog, settings)
        
        popupMenu.AppendSeparator()
        
        export = popupMenu.Append(wx.ID_ANY, "Export data")
        popupMenu.Bind(wx.EVT_MENU, self.export_data, export)

        self.canvas.ReleaseMouse()
        wx.CallAfter(self.PopupMenu, popupMenu) 
    
    def on_motion(self, event):
        if event.inaxes:
            x = event.xdata
            y = event.ydata
            if self.Xmin <= x and x <= self.Xmax and self.Ymin <= y and y <= self.Ymax:
                try:
                    dx = (self.Xmax - self.Xmin)/float(self.data.shape[1])
                    dy = (self.Ymax - self.Ymin)/float(self.data.shape[0])
                    X = np.floor((x - self.Xmin)/dx)
                    Y = np.floor((y - self.Ymin)/dy)
                    i = self.data[Y, X]
                    self.annotation.SetLabel('x : %g (%g), y : %g (%g), data[x,y] : %g'%(X,x*self.Xunit_conversion_factor,Y,y*self.Yunit_conversion_factor,i))
                except:
                    self.annotation.SetLabel('') # rarely useful except outside figure

        else:
            self.annotation.SetLabel('')
   
   
    def export_data(self, event = None):
        header = '# Data         : %s\n# First row    : %s\n# First column : %s\n' % (self.varname,self.Xlabel,self.Ylabel)
        output_fname = self.get_output_filename()
        
        x = np.concatenate(([0],self.Xaxis))
        data = np.vstack((x,np.hstack((self.Yaxis[:,np.newaxis],self.data))))
        if output_fname:
            with open(output_fname, 'w') as f:
                f.write(header)
                np.savetxt(f, data, fmt='%12.4e', delimiter="  ")
                f.close()
    
    def get_output_filename(self):
        path = ''
        dlg = wx.FileDialog(self, "Save As", '', '', "All Files|*.*", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()
        return path
    
    def slice(self, event):
        if not event.IsChecked():
            self.canvas.mpl_disconnect(self.slice_event_id)
            self.slice_event_id = None
            self.menu_event_id = self.canvas.mpl_connect('button_press_event', self.on_click)
            self.canvas.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
            for w in self.slice_widget:
                w.remove()
            self.slice_widget = []
            
            self.cross_slice_fig = None
            self.segment_slice_fig = None
            
            self.segment_slice_color_index = 0 
            self.cross_slice_color_index = -1
            self.v_cross_slice_plot = None
            self.h_cross_slice_plot = None
            self.segment_slice_legend = []
            self.h_cross_slice_legend = []
            self.v_cross_slice_legend = []
            if self.cross_slice_dialog:
                self.cross_slice_dialog.Close()
            self.canvas.draw()
            return
        self.canvas.mpl_disconnect(self.menu_event_id)
        self.menu_event_id = None
        self.slice_event_id = self.canvas.mpl_connect('button_press_event', self.build_slice_widget) 
        self.canvas.SetCursor(wx.CROSS_CURSOR)
        self.canvas.draw() 

        
    def build_slice_widget(self, event):
        if not event.inaxes:
                return
#         if event.button == 3: # SEGMENT SLICING CASE
#             
#             self.slice_coords.append([event.xdata,event.ydata ])
#             
#             if len(self.slice_coords) == 2:
#                 x, y = self.slice_coords[0]
#                 xp, yp = self.slice_coords[1]
#                 
#                 slice, X, Y  = self.extract_segment_slice(self.slice_coords)
#                 segment = self.subplot.plot([x, xp], [y, yp], '%so-'%self.get_circular_color(self.segment_slice_color_index))
#                 self.slice_widget += segment
#                 if self.segment_slice_dialog is None or not self.segment_slice_dialog:
#                     self.segment_slice_dialog = wx.Frame(self, title="Segment slicing")
#                     self.segment_slice_fig = Figure()
#                     self.segment_slice_canvas = FigureCanvasWxAgg(self.segment_slice_dialog, wx.ID_ANY, self.segment_slice_fig)
#                     self.segment_slice_toolbar = NavigationToolbar2WxAgg(self.segment_slice_canvas)
#                     sizer = wx.BoxSizer(wx.VERTICAL)
#                     sizer.Add(self.segment_slice_canvas, 1, flag=wx.EXPAND) 
#                     sizer.Add(self.segment_slice_toolbar, 0, flag=wx.EXPAND)
#                     self.segment_slice_dialog.SetSizer(sizer) 
#                     sizer.Fit(self.segment_slice_dialog)
#                     
#                 self.segment_slice_plot = self.segment_slice_fig.add_subplot(111)
#                 
#                 tmp_plot = self.segment_slice_plot.plot(X, slice, color='%s'%self.get_circular_color(self.segment_slice_color_index))
#                 self.segment_slice_legend.append([tmp_plot[0],'segment[(%d,%d),(%d,%d)]'%(x,y,xp,yp)])
#                 
#                 self.segment_slice_fig.gca().legend(tuple([e[0] for e in self.segment_slice_legend]), tuple([e[1] for e in self.segment_slice_legend]), loc = 'best', frameon = True, shadow = True)
#                 
#                 oldXticks = np.array(self.segment_slice_plot.get_xticks())
#                 
#                 Xticks = map('{:g}'.format, oldXticks*self.Xunit_conversion_factor)
#                 
#                 self.segment_slice_fig.gca().xaxis.set_ticks(oldXticks)
#                 self.segment_slice_fig.gca().xaxis.set_ticklabels(Xticks)
#                 
#                 self.segment_slice_fig.gca().set_xlabel(self.Xlabel + self.fmt_Xunit )
#                 
#                 self.subplot.axis('image')
#                 if self.aspect == 'auto':
#                     self.subplot.set_aspect("auto","datalim")
#                 self.canvas.draw()
#                 self.segment_slice_dialog.Show()
#                 self.segment_slice_canvas.draw()
#                 self.segment_slice_color_index += 1
#                 self.slice_coords = []
                
        elif event.button == 1: # CROSS SLICING CASE
            
            x, y = event.xdata , event.ydata 
            dx = (self.Xmax - self.Xmin)/float(self.data.shape[1])
            dy = (self.Ymax - self.Ymin)/float(self.data.shape[0])
            X = np.floor((x - self.Xmin)/dx)
            Y = np.floor((y - self.Ymin)/dy)
            vslice, hslice = self.extract_cross_slice(X, Y)
            
            if not self.parent.unique_slicer is None:
                self.cross_slice_dialog = self.parent.unique_slicer.dialog
                self.cross_slice_canvas = self.parent.unique_slicer.canvas 
                self.h_cross_slice_plot = self.parent.unique_slicer.hplot
                self.v_cross_slice_plot = self.parent.unique_slicer.vplot
                self.cross_slice_fig = self.parent.unique_slicer.fig
                self.cross_slice_color_index = self.parent.unique_slicer.color_index
                self.parent.unique_slicer.color_index += 1
                self.h_cross_slice_legend = self.parent.unique_slicer.hlegend
                self.v_cross_slice_legend = self.parent.unique_slicer.vlegend
                
            elif self.cross_slice_fig is None or not self.cross_slice_fig:
                    self.cross_slice_fig = Figure()
                    self.v_cross_slice_plot = self.cross_slice_fig.add_subplot(211)
                    self.h_cross_slice_plot = self.cross_slice_fig.add_subplot(212)
            
            if self.cross_slice_dialog is None or not self.cross_slice_dialog:
                self.cross_slice_dialog = wx.Frame(self, title="Cross slicing")  
                self.cross_slice_canvas = FigureCanvasWxAgg(self.cross_slice_dialog, wx.ID_ANY, self.cross_slice_fig)
                self.cross_slice_toolbar = NavigationToolbar2WxAgg(self.cross_slice_canvas)
                
                    
                self.unique_target_checkbox = wx.CheckBox(self.cross_slice_dialog, id=wx.ID_ANY, label="Single target plot")
                self.Bind(wx.EVT_CHECKBOX, self.made_unique_target, id = self.unique_target_checkbox.GetId())
                self.unique_target_checkbox.SetValue(self.unique)
                
                self.auto_scale_button = wx.Button(self.cross_slice_dialog, id=wx.ID_ANY, label="Auto-Scale")
                self.Bind(wx.EVT_BUTTON, self.auto_scale_cross_plot, self.auto_scale_button)
                
                sizer = wx.BoxSizer(wx.VERTICAL)
                sizer.Add(self.cross_slice_canvas, 1, flag=wx.EXPAND) 
                hsizer = wx.BoxSizer()
                hsizer.Add(self.cross_slice_toolbar, 0, flag=wx.EXPAND)
                hsizer.AddSpacer(10)
                hsizer.Add(self.auto_scale_button,0 ,flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL )
                hsizer.AddSpacer(10)
                hsizer.Add(self.unique_target_checkbox, 0, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL )
                
                sizer.Add(hsizer, 0, flag=wx.EXPAND) 
                
                self.cross_slice_dialog.SetSizer(sizer) 
                sizer.Fit(self.cross_slice_dialog)
            
            self.cross_slice_color_index += 1 
            
            self.slice_widget.append(self.subplot.axvline(x=x, linewidth=3, color='%s'%self.get_circular_color(self.cross_slice_color_index)))
            self.slice_widget.append(self.subplot.axhline(y=y, linewidth=3, color='%s'%self.get_circular_color(self.cross_slice_color_index)))
            
            v_tmp_plot = self.v_cross_slice_plot.plot(self.Xaxis*self.Xunit_conversion_factor, vslice, color='%s'%self.get_circular_color(self.cross_slice_color_index))
            h_tmp_plot = self.h_cross_slice_plot.plot(self.Yaxis*self.Yunit_conversion_factor, hslice, color='%s'%self.get_circular_color(self.cross_slice_color_index))
            
            self.v_cross_slice_legend.append([v_tmp_plot[0],'x = %d'%x])
            self.h_cross_slice_legend.append([v_tmp_plot[0],'y = %d'%y])
            
            self.v_cross_slice_plot.set_xlabel(self.Xlabel + self.fmt_Xunit)
            self.h_cross_slice_plot.set_xlabel(self.Ylabel + self.fmt_Yunit)
            
            self.v_cross_slice_plot.legend(tuple([e[0] for e in self.v_cross_slice_legend]), tuple([e[1] for e in self.v_cross_slice_legend]), loc = 'best', frameon = True, shadow = True)
            self.h_cross_slice_plot.legend(tuple([e[0] for e in self.h_cross_slice_legend]), tuple([e[1] for e in self.h_cross_slice_legend]), loc = 'best', frameon = True, shadow = True)
            
            if self.aspect == 'auto':
                self.subplot.set_aspect("auto","datalim")
                
            self.canvas.draw()
            self.cross_slice_dialog.Show()
            self.cross_slice_canvas.draw()
            

    def made_unique_target(self, event):
        self.parent.unique_slicer = CrossSlicer(self,
                                                self.cross_slice_canvas, 
                                                self.cross_slice_dialog, 
                                                self.h_cross_slice_plot, 
                                                self.v_cross_slice_plot, 
                                                self.cross_slice_fig, 
                                                self.cross_slice_color_index, 
                                                self.h_cross_slice_legend, 
                                                self.v_cross_slice_legend) 
        if self.unique:
            self.cross_slice_canvas = None
            self.cross_slice_fig = None
            self.h_cross_slice_plot = None 
            self.v_cross_slice_plot = None 
            self.cross_slice_color_index = 0
            self.h_cross_slice_legend = []
            self.v_cross_slice_legend = []
            for w in self.slice_widget:
                w.remove()
            self.slice_widget = []
            self.canvas.draw() 
            self.parent.unique_slicer = None
            self.cross_slice_dialog.Close()

        self.unique = not self.unique
        

    def auto_scale_cross_plot(self, event):
        
        norm = Normalize()
        
        for hl in self.h_cross_slice_plot.get_lines(): 
            d = hl.get_ydata()
            norm.autoscale(d)
            hl.set_ydata(norm(d))
          
        for vl in self.v_cross_slice_plot.get_lines(): 
            d = vl.get_ydata()
            norm.autoscale(d)
            vl.set_ydata(norm(d))
        
        
        self.v_cross_slice_plot.relim()
        self.h_cross_slice_plot.relim()
        self.v_cross_slice_plot.autoscale_view(True,True,True)
        self.h_cross_slice_plot.autoscale_view(True,True,True)

        self.cross_slice_canvas.draw()
            
    def get_circular_color(self, idx):
        circ_idx = idx%len(self.color_list)
        return self.color_list.values()[circ_idx]
                
    def extract_segment_slice(self, coords):
        x, y = coords[0]
        xp, yp = coords[1]
        dist =  np.sqrt((x-xp)**2+(y-yp)**2)
        
        RX = np.linspace(x, xp, dist)
        RY = np.linspace(y, yp, dist)
        X, Y = RX.astype(np.int), RY.astype(np.int)
        # Extract the values along the line
        slice = self.data[X, Y]
        return slice, RX, RY
    
    def extract_cross_slice(self, x, y):
        x = int(x)
        y = int(y)
        hslice = self.data.T[x,:]
        vslice = self.data.T[:,y]
        return vslice, hslice
        
    def set_lim(self):
        self.Xmin, self.Xmax = self.Xaxis[0], self.Xaxis[-1]
        self.Ymin, self.Ymax = self.Yaxis[0], self.Yaxis[-1]
    
    def reset_axis(self):
        self.set_lim()
        self.figure.gca().axis([self.Xmin, self.Xmax, self.Ymin, self.Ymax]) 
        self.canvas.draw()
    
    def Plot(self, data, varname, Xaxis = None, Xunit = None, Yaxis = None, Yunit = None, transposition = True):
        if data is None:
            return
        
        if not (Xaxis != None and Xunit != None and Yaxis != None and Yunit != None):
            self.set_axis_property(varname,data)
        else:
            self.Xaxis = Xaxis
            self.Xunit = Xunit
            self.Yaxis = Yaxis
            self.Yunit = Yunit
        
        if transposition:
            self.data = data.T
        else:
            self.data = data
            
        self.varname = varname
        
        self.subplot = self.figure.add_subplot( 111 )   
        
        self.ax = self.subplot.imshow(self.data, interpolation=self.interpolation, origin='lower')


        self.subplot.set_aspect('auto')
        self.aspect = 'auto'

        self.Xlabel = self.Xaxis_label
        self.Ylabel = self.Yaxis_label
        self.figure.gca().set_xlabel(self.Xlabel + self.fmt_Xunit )
        self.figure.gca().set_ylabel(self.Ylabel + self.fmt_Yunit )
        
        self.set_ticks()
        self.reset_axis()
        
        self.color_bar = self.figure.colorbar(self.ax)
        
        self.canvas.draw()
    
    def rePlot(self, oldinstance):
        
        self.data = oldinstance.data
        self.Xaxis = oldinstance.Xaxis
        self.Xunit = oldinstance.Xunit
        self.Yaxis = oldinstance.Yaxis
        self.Yunit = oldinstance.Yunit
        self.varname = oldinstance.varname
        self.Xaxis_label = oldinstance.Xaxis_label
        self.Yaxis_label = oldinstance.Yaxis_label
        self.normType = oldinstance.normType
        self.aspect = oldinstance.aspect
        self.subplot = self.figure.add_subplot( 111 )   
        
        self.ax = self.subplot.imshow(self.data, interpolation=self.interpolation, origin='lower')

        self.subplot.set_aspect(self.aspect)

        self.Xlabel = self.Xaxis_label
        self.Ylabel = self.Yaxis_label
        self.figure.gca().set_xlabel(self.Xlabel + self.fmt_Xunit )
        self.figure.gca().set_ylabel(self.Ylabel + self.fmt_Yunit )
        
        self.set_ticks()
        self.reset_axis()
        
        self.color_bar = self.figure.colorbar(self.ax)
        
        self.scale(onReplot = True)
        
        self.canvas.draw()
        
    def scale(self, onReplot = False):
        
        if not NORMALIZER.has_key(self.normType):
            self.color_bar.set_clim(self.data.min(), self.data.max())
            self.ax.set_norm(None)
            return
        
        norm = NORMALIZER[self.normType]
        norm.autoscale(self.data)
        
        try :
            self.ax.set_norm(norm)
        except ValueError:
            raise PlotterError('Could not set normalization : difference between minimum and maximum values is to small')

        if onReplot: 
            normd = norm(self.data)
            self.color_bar.set_clim(normd.min(), normd.max())
            
             
    def compute_conversion_factor(self):
        try:
            self.Xunit_conversion_factor = magnitude.mg(1., self.Xinit_unit, self.Xunit).toval()
        except magnitude.MagnitudeError:
            self.Xunit_conversion_factor = 1.0

        try:
            self.Yunit_conversion_factor = magnitude.mg(1., self.Yinit_unit, self.Yunit).toval()
        except magnitude.MagnitudeError:
            self.Yunit_conversion_factor = 1.0

    
    def set_ticks(self):

        self.compute_conversion_factor()
        
        self.figure.gca().xaxis.set_major_locator(ScaledLocator(dx = self.Xunit_conversion_factor))
        self.figure.gca().xaxis.set_major_formatter(ScaledFormatter(dx = self.Xunit_conversion_factor))      
        
        self.figure.gca().yaxis.set_major_locator(ScaledLocator(dx = self.Yunit_conversion_factor))
        self.figure.gca().yaxis.set_major_formatter(ScaledFormatter(dx = self.Yunit_conversion_factor)) 
        
        self.ax.set_extent([self.Xaxis[0], self.Xaxis[-1], self.Yaxis[0], self.Yaxis[-1]])
        
    def set_axis_property(self, varname, data):
        oldXunit = self.Xinit_unit
        oldYunit = self.Yinit_unit

        try :
            self.Xaxis_label = self.dataproxy[varname]['axis'][0]
            self.Xunit = self.Xinit_unit = self.dataproxy[self.Xaxis_label]['units']
            self.Xaxis = self.dataproxy[self.Xaxis_label]['data']
        except:
            self.Xunit = self.Xinit_unit = 'au'
            self.Xaxis = np.arange(data.shape[0]) 
            
        try :
            self.Yaxis_label = self.dataproxy[varname]['axis'][1]
            self.Yunit = self.Yinit_unit = self.dataproxy[self.Yaxis_label]['units']
            self.Yaxis = self.dataproxy[self.Yaxis_label]['data']
        except:
            self.Yunit = self.Yinit_unit = 'au'
            self.Yaxis = np.arange(data.shape[1]) 
            
        if not oldXunit is None:
            if oldXunit != self.Xinit_unit:
                LOGGER('the x axis unit (%s) of data-set %r is inconsistent with the unit (%s) of the precedent data plotted '%(self.Xinit_unit, varname,  oldXunit), 'warning')
        if not oldYunit is None:
            if oldYunit != self.Yinit_unit:
                LOGGER('the y axis unit (%s) of data-set %r is inconsistent with the unit (%s) of the precedent data plotted '%(self.Yinit_unit, varname,  oldYunit), 'warning')

        if self.Yaxis.shape[0] != data.shape[1]:
             LOGGER('the y axis dimension is inconsistent with the shape of data ', 'error')
        if self.Xaxis.shape[0] != data.shape[0]:
             LOGGER('the x axis dimension is inconsistent with the shape of data ', 'error')
            
    def image_setting_dialog(self, event = None):
        d = ImageSettingsDialog(self)
        d.SetFocus()
        d.ShowModal()
        d.Destroy()
        

class Plotter1d(wx.Panel):
    type = 'line'
    def __init__(self, parent, data = None):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        
        self.setting = None
                
        ### Initialize variables ###
        self.parent = parent
        self.figure = Figure(figsize=(5,4), dpi=None)
        self.axes = self.figure.add_axes( (10,10,10,10), frameon=True, axisbg='b')
        self.canvas = FigureCanvasWxAgg( self, wx.ID_ANY, self.figure )
        self.toolbar = NavigationToolbar2WxAgg(self.canvas)
        self.plots = {}
        self.selectedLine = None
        
    
        self.annotation =  wx.StaticText(self, label='x : , y : ' , style=wx.ALIGN_CENTER_VERTICAL)

        ### Initialize figure parameters ###
        self.title = ''
        self.titleStyle = 0
        self.titleWeight = 0
        self.titleWidth = 4 # large
        
        self.xlabel = ''
        self.xlabelStyle = 0
        self.xlabelWeight = 0
        self.xlabelWidth = 3 # medium
        
        self.ylabel = ''
        self.ylabelStyle = 0
        self.ylabelWeight = 0
        self.ylabelWidth = 3 # medium
        
        self.gridStyle = 'None'
        self.gridWidth = 1
        self.gridColor = (1,0,0)
        
        self.Xscale = 'linear'
        self.Yscale = 'linear'
        
        self.xMinorTicks = False
        self.yMinorTicks = False
        
        self.Xposition = 'none'
        self.Yposition = 'none'

        self.Xlabel = ''
        self.Ylabel = ''
        
        self.Xaxis_label = ''
        self.Yaxis_label = ''
        
        self.Xunit = None
        self.Yunit = None
        
        self.Xinit_unit = None
        self.Yinit_unit = None
        
        self.Xaxis = np.array([])
        self.Yaxis = np.array([])
        
        self.Xticks = []
        self.Yticks = []
        
        self.Xmax = 0
        self.Ymax = 0
        self.Xmin = 0
        self.Ymin = 0
        
        self.offset = 0.0
        self.verticalCut = None
        
        self.show_legend = False
        self.legend_location = 'best'
        self.legend_frameon = True
        self.legend_shadow = True
        self.legend_fancybox = False

        # add sliders
        cutSizer = wx.BoxSizer(wx.HORIZONTAL)
        offsetSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.offset_label = wx.StaticText(self, label="Offset Value" , style=wx.ALIGN_CENTER_VERTICAL)
        self.yAxisSliderOffset = wx.Slider(self, wx.ID_ANY, size = (60,27), style = wx.SL_HORIZONTAL)
        self.offset_multiplier_label = wx.StaticText(self, label="Modulation" , style=wx.ALIGN_CENTER_VERTICAL)
        self.yAxisOffset = wx.TextCtrl(self, wx.ID_ANY, size = (60,27), style = wx.TE_PROCESS_ENTER )
        self.yAxisOffset.SetValue('0.0')
        self.autoFitAxesButton = wx.Button(self, label = "Fit axes range", size = (120,27))

        hsizer = wx.BoxSizer()
        hsizer.Add(self.toolbar, 0, flag=wx.ALL|wx.EXPAND)
        hsizer.AddSpacer(25)
        hsizer.Add(self.annotation, 0, flag=wx.ALIGN_CENTER_VERTICAL)
        
        hsizer2 = wx.BoxSizer()
        hsizer2.AddSpacer(5)
        hsizer2.Add(self.offset_label, 0, flag=wx.ALIGN_CENTER_VERTICAL)
        hsizer2.AddSpacer(5)
        hsizer2.Add(self.yAxisOffset, 0, flag=wx.ALIGN_CENTER_VERTICAL)
        hsizer2.AddSpacer(5)
        hsizer2.Add(self.offset_multiplier_label, 0, flag=wx.ALIGN_CENTER_VERTICAL )
        hsizer2.AddSpacer(5)
        hsizer2.Add(self.yAxisSliderOffset, 1, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        hsizer2.AddSpacer(5)
        hsizer2.Add(self.autoFitAxesButton,0, flag = wx.ALIGN_CENTER_VERTICAL)
        
        ### sizer ###
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, flag=wx.EXPAND) 
        self.sizer.Add(hsizer, 0, flag=wx.EXPAND)
        self.sizer.Add(hsizer2, 0, flag=wx.EXPAND)
        self.SetSizer(self.sizer) 
        
        ### set bindings ###
        self.Bind(wx.EVT_CLOSE, self.on_close_figure) 
        self.Bind(wx.EVT_TEXT_ENTER, self.on_offset ,id = self.yAxisOffset.GetId())
        self.Bind(wx.EVT_SCROLL,self.on_offset ,id = self.yAxisSliderOffset.GetId())
        self.Bind(wx.EVT_BUTTON, self.on_auto_fit, id = self.autoFitAxesButton.GetId())
#         self.Bind(wx.EVT_CHECKBOX, self.slice, id = self.slice_checkbox.GetId())
        
        self.binds_mpl_events()

        #### sizer automatically fitting window size ####
        self.toolbar.Realize()
        self.SetSizeHints(600,500,1000,1000) # SetSizeHints(minW, minH, maxW, maxH)
        self.sizer.Fit(self)
        self.Show(True)
        
    @property
    def dataproxy(self):
        return self.parent.dataproxy
    
    @property
    def fmt_Xunit(self):
        if not self.Xunit:
            return ''
        else:    
            return ' (' + self.Xunit + ')'
    
    @property
    def fmt_Yunit(self):
        if not self.Yunit:
            return ''
        else:    
            return ' (' + self.Yunit + ')'
    
    def binds_mpl_events(self):
        self.menu_event_id = self.canvas.mpl_connect('button_press_event', self.on_click)
        self.pick_event_id = self.canvas.mpl_connect("pick_event", self.on_pick_line)
        self.key_event_id = self.canvas.mpl_connect('key_press_event', self.on_key)  
        self.on_motion_id = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        
    def on_click(self, event = None):
        if event.button != 3:
            return
        
        popupMenu = wx.Menu()

        general = popupMenu.Append(wx.ID_ANY, "General settings")
        popupMenu.Bind(wx.EVT_MENU, self.general_setting_dialog, general)
        
        axes = popupMenu.Append(wx.ID_ANY, "Axes settings")
        popupMenu.Bind(wx.EVT_MENU, self.axes_setting_dialog, axes)
        
        lines = popupMenu.Append(wx.ID_ANY, "Lines settings")
        popupMenu.Bind(wx.EVT_MENU, self.lines_setting_dialog, lines)

        popupMenu.AppendSeparator()

        clear = popupMenu.Append(wx.ID_ANY, "Clear")
        popupMenu.Bind(wx.EVT_MENU, self.clear, clear)

        popupMenu.AppendSeparator()        


        export = popupMenu.Append(wx.ID_ANY, "Export data")
        popupMenu.Bind(wx.EVT_MENU, self.export_data, export)
        
        self.canvas.ReleaseMouse()
        wx.CallAfter(self.PopupMenu, popupMenu) 
    
    def on_motion(self, event):
        if event.inaxes:
            x = event.xdata
            y = event.ydata
            self.annotation.SetLabel('x : %g, y : %g'%(x,y))
        else:
            self.annotation.SetLabel('')
            
    def clear(self, event = None):
        d = wx.MessageDialog(None,
                 'Do you really want clean the plot window ?',
                 'Question',
                 wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if d.ShowModal() == wx.ID_YES:
            pass
        else:
            return
        self.plots = {}
        self.figure.gca().clear()
        self.figure.canvas.draw()  
           
    def on_offset(self, event = None):
        try :
            offsetValue = float(self.yAxisOffset.GetValue())
        except:
            offsetValue = 0.
        offsetPercent = float(self.yAxisSliderOffset.GetValue())/100.0
        AddFactor = float(offsetValue*offsetPercent) - float(self.offset)
        self.offset = float(offsetValue*offsetPercent) 
        
        self.add_offset(AddFactor)
    
    def export_data(self, event = None):

        first = True
        
        for v in self.plots.values():
           
            line, label, varname = v
            if first:
                try:
                    axis = self.dataproxy[varname]['axis'][0]
                    data = [self.dataproxy[axis]['data']]
                    labels = ['%s (%s)'%(axis, self.dataproxy[axis]['units'])]
                except:
                    data = [np.arange(self.dataproxy[varname]['data'].shape[0])]
                    labels = ['default_axis (au)']
                first = False
                    
            try:
                line.get_xydata()
                data.append(line.get_ydata())
                labels.append('%s (%s)'%(label, self.dataproxy[varname]['units']))
            except:
                LOGGER('encounter issue for variable %r while exporting data'%varname,'warning')
        header = '# '
        if labels:
            for l in labels:
                header += '%s, '%l
            header = header[:-2] + os.linesep   
        output_fname = self.get_output_filename()
        if output_fname:
            with open(output_fname, 'w') as f:
                f.write(header)
                np.savetxt(f,np.column_stack(data), fmt='%12.4e', delimiter="  ")
                f.close()
        
    def get_output_filename(self):
        path = ''
        dlg = wx.FileDialog(self, "Save As", '', '', "All Files|*.*", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()
        return path
            
    def add_offset(self, offset):
        lines = self.figure.gca().lines
        # remove vertical line if existing
        if self.verticalCut is not None :        
            lines.remove(self.verticalCut)
            self.verticalCut = None
            
        for idx in range(len(lines)):
            line = lines[idx]
            
            y = line.get_ydata()
            line.set_ydata( (idx+1)*offset +y  )
        
        # set activeFigure to this figure
        self.figure.canvas.draw()

    def on_auto_fit(self, event = None):
        lines = self.figure.gca().lines
        if lines == []:
            return
        xMin = 1.0e10
        xMax = 0
        yMin = 1.0e10
        yMax = 0
        for line in lines:
            xMin = min( xMin, min(line.get_xdata()) )
            xMax = max( xMax, max(line.get_xdata()) )
            yMin = min( yMin, min(line.get_ydata()) )
            yMax = max( yMax, max(line.get_ydata()) )
   
        self.Xmin =xMin
        self.Xmax = xMax
        self.Ymin = yMin
        self.Ymax=  yMax + 0.05*(yMax-yMin)
        
        self.figure.gca().axis([self.Xmin, self.Xmax, self.Ymin, self.Ymax])
        self.figure.canvas.draw()
    
    def on_key(self, event = None):
        if event.key =='delete':
            if self.selectedLine is None:
                return
            # remove offset
            self.add_offset(-self.offset)
            # actualize plotsFileData
            for k,v in self.plots.items():
                if v[0] is self.selectedLine:
                    d = wx.MessageDialog(None,
                             'Do you really want delete this line ?',
                             'Question',
                             wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
                    if d.ShowModal() == wx.ID_YES:
                        pass
                    else:
                        return
                    self.plots.pop(k)
            # remove line
            self.selectedLine.remove()
            # add offset
            self.add_offset(self.offset)
            self.update_legend()
            self.selectedLine = None
            self.canvas.draw()
    
    def delete_line(self, line): 
        self.add_offset(-self.offset)
        
        for k,v in self.plots.items():
            if v[0] is line: 
                self.plots.pop(k)
        
        line.remove()
        self.add_offset(self.offset)
        self.canvas.draw()
        
    def on_close_figure(self, event = None):
        # remove any selection made in any figure
        if self.parent.selectedPlot is not None:
            self.parent.selectedPlot = None
        
        # destroy window
        self.Destroy()
        self = None

    def scale_xAxis(self):
        scaleStr = self.Xscale
        if scaleStr == 'linear':
            self.figure.gca().set_xscale('linear')
        elif  scaleStr == 'symlog':
            self.figure.gca().set_xscale('symlog')
        elif scaleStr == 'ln':
            self.figure.gca().set_xscale('log', basex=np.exp(1))
        elif scaleStr == 'log 10':
            self.figure.gca().set_xscale('log', basex=10)
        elif scaleStr == 'log 2':
            self.figure.gca().set_xscale('log', basex=2)
        self.on_auto_fit()  
        self.figure.canvas.draw()
        
    def scale_yAxis(self):
        scaleStr = self.Yscale
        if scaleStr == 'linear':
            self.figure.gca().set_yscale('linear')
        elif  scaleStr == 'symlog':
            self.figure.gca().set_yscale('symlog')
        elif scaleStr == 'ln':
            self.figure.gca().set_yscale('log', basex=np.exp(1))
        elif scaleStr == 'log 10':
            self.figure.gca().set_yscale('log', basex=10)
        elif scaleStr == 'log 2':
            self.figure.gca().set_yscale('log', basex=2)
        self.on_auto_fit() 
        self.figure.canvas.draw()
        
    def on_pick_line(self, event = None):
        # set alpha of previous selection to 1
        if self.selectedLine is not None: 
            self.selectedLine.set_alpha(1.0)
            self.selectedLine.figure.canvas.draw()
        # unselect previous selection
        if event.artist == self.selectedLine:
            self.selectedLine = None
            return 
        # set new selection and alpha  
        self.selectedLine = event.artist
        self.selectedLine.set_alpha(0.4)
        self.selectedLine.figure.canvas.draw()

    def update_legend(self):
        legend = [[],[]] 
        for v in self.plots.values():
            legend[0].append(v[0])
            legend[1].append(v[1]) 
        self.figure.gca().legend(tuple(legend[0]), tuple(legend[1]), loc = self.legend_location, frameon = self.legend_frameon, shadow = self.legend_shadow, fancybox = self.legend_fancybox) 
        self.show_legend = True
        
    def Plot(self, data, varname):
        if data is None:
            return
        self.set_axis_property(varname, data)
        self.subplot = self.figure.add_subplot( 111 )  
        name = self.unique(varname, self.plots) 
        self.plots[name] = [self.subplot.plot(self.Xaxis, data, picker = 3)[0], name, varname]
        self.set_ticks()
        self.Xlabel = self.Xaxis_label
        self.Ylabel = self.Yaxis_label
        self.figure.gca().set_xlabel(self.Xlabel + self.fmt_Xunit )
        self.figure.gca().set_ylabel(self.Ylabel + self.fmt_Yunit )
        self.on_auto_fit()
        self.canvas.draw() 
    
    def set_axis_property(self, varname, data):
        oldXunit = self.Xinit_unit
        oldYunit = self.Yinit_unit
        self.Yaxis_label = varname
        self.Yaxis = self.dataproxy[varname]['data']
        try :
            self.Xaxis_label = self.dataproxy[varname]['axis'][0]
            self.Xunit = self.Xinit_unit = self.dataproxy[self.Xaxis_label]['units']
            self.Xaxis = self.dataproxy[self.Xaxis_label]['data']
        except:
            self.Xunit = self.Xinit_unit = 'au'
            self.Xaxis = np.arange(data.shape[0]) 
        try :
            self.Yunit = self.Yinit_unit = self.dataproxy[varname]['units']
        except:
            self.Yunit = self.Yinit_unit = 'au'
            
        
        
        if not oldXunit is None:
            if oldXunit != self.Xinit_unit:
                LOGGER('the x axis unit (%s) of data-set %r is inconsistent with the unit (%s) of the precedent data plotted '%(self.Xinit_unit, varname,  oldXunit), 'warning')
        if not oldYunit is None:
            if oldYunit != self.Yinit_unit:
                LOGGER('the y axis unit (%s) of data-set %r is inconsistent with the unit (%s) of the precedent data plotted '%(self.Yinit_unit, varname,  oldYunit), 'warning')
    
    def compute_conversion_factor(self):
        try:
            self.Xunit_conversion_factor = magnitude.mg(1., self.Xinit_unit, self.Xunit).toval()
        except magnitude.MagnitudeError:
            self.Xunit_conversion_factor = 1.0
        
        try:
            self.Yunit_conversion_factor = magnitude.mg(1., self.Yinit_unit, self.Yunit).toval()
        except magnitude.MagnitudeError:
            self.Yunit_conversion_factor = 1.0
                   
    def set_ticks(self):
        self.compute_conversion_factor()
        
        self.figure.gca().xaxis.set_major_locator(ScaledLocator(dx = self.Xunit_conversion_factor))
        self.figure.gca().xaxis.set_major_formatter(ScaledFormatter(dx = self.Xunit_conversion_factor))      
        
        self.figure.gca().yaxis.set_major_locator(ScaledLocator(dx = self.Yunit_conversion_factor))
        self.figure.gca().yaxis.set_major_formatter(ScaledFormatter(dx = self.Yunit_conversion_factor)) 
                                                    
        

    def unique(self, key, dict):
        skey = key
        i = 0
        while dict.has_key(key):
            key = skey + '_%d'%i
            i += 1
        return key 
    
    def general_setting_dialog(self, event = None):
        d = GeneralSettingsDialog(self)
        d.SetFocus()
        d.ShowModal()
        d.Destroy()
        
    def axes_setting_dialog(self, event = None):
        d = AxesSettingsDialog(self)
        d.SetFocus()
        d.ShowModal()
        d.Destroy()
        
    def lines_setting_dialog(self, event = None):
        d = LinesSettingsDialog(self)
        d.SetFocus()
        d.ShowModal()
        d.Destroy()


class ImageSettingsDialog(wx.Dialog):
    
    def __init__(self, parent=None):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title="Image Settings", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX)
        self.parent = parent
        self.build_dialog()
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
    def build_dialog(self):
        
        self.norm_choices = ['none', 'log']
        self.aspect_choices = ['equal', 'auto']
        self.interpolation_choices =  ['none', 'nearest', 'bilinear', 'bicubic', 'spline16', \
                                       'spline36', 'hanning', 'hamming', 'hermite', 'kaiser', \
                                        'quadric', 'catrom', 'gaussian', 'bessel', 'mitchell', \
                                         'sinc', 'lanczos']
        
        Sizer = wx.BoxSizer(wx.VERTICAL)
        
        
        sb = wx.StaticBox(self, wx.ID_ANY, label = "Label")
        sbsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
        
        gbSizer = wx.GridBagSizer(5,5)
        
        self.title_label = wx.StaticText(self, label="Title" , style=wx.ALIGN_CENTER_VERTICAL)
        self.title = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        self.Xlabel_label = wx.StaticText(self, label="X Axis", style=wx.ALIGN_CENTER_VERTICAL)
        self.Xlabel = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        self.Ylabel_label = wx.StaticText(self, label="Y Axis", style=wx.ALIGN_CENTER_VERTICAL)
        self.Ylabel = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        gbSizer.Add(self.title_label, (0,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(self.title, (0,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        gbSizer.Add(self.Xlabel_label, (1,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(self.Xlabel, (1,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        gbSizer.Add(self.Ylabel_label, (2,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(self.Ylabel, (2,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        
        gbSizer.AddGrowableCol(1)
        
        sbsizer.Add(gbSizer, 0, wx.EXPAND, 5)
        
        Sizer.Add(sbsizer, 0, wx.EXPAND)
        

        gbSizer2 = wx.GridBagSizer(5,5)
        
        hsizer = wx.BoxSizer(wx.HORIZONTAL)

        
        sb2 = wx.StaticBox(self, wx.ID_ANY, label = "Aspect")
        sbsizer2 = wx.StaticBoxSizer(sb2, wx.VERTICAL)
        
        self.aspect_label = wx.StaticText(self, label="Proportions" , style=wx.ALIGN_CENTER_VERTICAL)
        self.aspect = wx.ComboBox(self, id = wx.ID_ANY, choices=self.aspect_choices, style=wx.CB_READONLY)
        
        self.interpolation_label = wx.StaticText(self, label="Interpolation" , style=wx.ALIGN_CENTER_VERTICAL)
        self.interpolation = wx.ComboBox(self, id = wx.ID_ANY, choices=self.interpolation_choices, style=wx.CB_READONLY)
        
        self.norm_label = wx.StaticText(self, label="Scale" , style=wx.ALIGN_CENTER_VERTICAL)
        self.normType = wx.ComboBox(self, id = wx.ID_ANY, choices=self.norm_choices, style=wx.CB_READONLY)
        self.normType.SetValue(self.norm_choices[0])
        
        gbSizer2.Add(self.aspect_label, (0,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer2.Add(self.aspect, (0,2), flag = wx.ALIGN_CENTER_VERTICAL)
       
        gbSizer2.Add(self.interpolation_label,(1,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer2.Add(self.interpolation, (1,2), flag = wx.ALIGN_CENTER_VERTICAL)     
        
        gbSizer2.Add(self.norm_label,(2,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer2.Add(self.normType, (2,2), flag = wx.ALIGN_CENTER_VERTICAL)         
                
        sbsizer2.Add(gbSizer2, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        
        gbSizer1 = wx.GridBagSizer(5,5)
        
        sb1 = wx.StaticBox(self, wx.ID_ANY, label = "Units")
        sbsizer1 = wx.StaticBoxSizer(sb1, wx.VERTICAL)
        
        self.X_label = wx.StaticText(self, label="X", style=wx.ALIGN_CENTER_VERTICAL)

        self.Xunit = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)
        
        self.Y_label = wx.StaticText(self, label="Y", style=wx.ALIGN_CENTER_VERTICAL)

        self.Yunit = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)
        
        gbSizer1.Add(self.X_label, (0,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer1.Add(self.Xunit, (0,2), flag = wx.ALIGN_CENTER_VERTICAL)
       
        gbSizer1.Add(self.Y_label,(1,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer1.Add(self.Yunit, (1,2), flag = wx.ALIGN_CENTER_VERTICAL)
        
        sbsizer1.Add(gbSizer1, 0, wx.EXPAND, 5)
        
        hsizer.Add(sbsizer2,0,wx.EXPAND)
        hsizer.Add(sbsizer1,0,wx.EXPAND)
        
        Sizer.Add(hsizer, 0, wx.EXPAND)
        
        hsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.apply_button  = wx.Button(self, wx.ID_ANY, label="Apply")
        self.quit_button  = wx.Button(self, wx.ID_ANY, label="Quit")
        hsizer1.Add(self.apply_button, 0, wx.EXPAND, 0)
        hsizer1.Add(self.quit_button, 0, wx.EXPAND, 0)
        
        Sizer.Add(hsizer1, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.ALL, 5)
        
        self.SetSizer(Sizer)        
        Sizer.Fit(self)
        self.Layout()
        
        self.Bind(wx.EVT_BUTTON, self.set_settings, self.apply_button)    
        self.Bind(wx.EVT_BUTTON, self.on_close, self.quit_button)  
        
        self.get_settings()
    
    def get_settings(self, event = None):
        self.title.SetValue(self.parent.figure.gca().get_title())
        self.Xlabel.SetValue(self.parent.Xlabel)
        self.Ylabel.SetValue(self.parent.Ylabel)
        
        self.Xunit.SetValue(str(self.parent.Xunit))
        self.Yunit.SetValue(str(self.parent.Yunit))
        
        self.aspect.SetValue(self.parent.figure.gca().get_aspect())
        self.interpolation.SetValue(self.parent.interpolation)
        self.normType.SetValue(self.parent.normType)
        
    def set_settings(self, event = None):
        
        self.parent.figure.gca().set_title(self.title.GetValue())
        self.parent.Xlabel = self.Xlabel.GetValue()
        self.parent.Ylabel = self.Ylabel.GetValue()
        
        if self.parent.Xunit !=self.Xunit.GetValue() or self.parent.Yunit != self.Yunit.GetValue():
            self.parent.Xunit = self.Xunit.GetValue()
            self.parent.Yunit = self.Yunit.GetValue()
            self.parent.set_ticks()
            self.parent.reset_axis()
         
        self.parent.figure.gca().set_xlabel(self.parent.Xlabel + self.parent.fmt_Xunit )
        self.parent.figure.gca().set_ylabel(self.parent.Ylabel + self.parent.fmt_Yunit )
         
        self.parent.aspect = self.aspect.GetValue()
        self.parent.interpolation = self.interpolation.GetValue()
        self.parent.normType = self.normType.GetValue()
        
        self.parent.figure.gca().set_aspect(self.parent.aspect)
        self.parent.ax.set_interpolation(self.parent.interpolation)
        
        self.parent.scale(True)
        self.parent.color_bar.update_normal(self.parent.ax)
        self.parent.canvas.draw()
    
    def on_close(self, event = None):
        self.MakeModal(False)
        self.Destroy()
    
    
class GeneralSettingsDialog(wx.Dialog):
    
    def __init__(self, parent=None):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title="General Settings", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX)
        self.parent = parent
        self.build_dialog()
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
    def build_dialog(self):
        self.legend_location_choice = ['best' , 'upper right' , 'upper left' ,\
                                     'lower left' , 'lower right' , 'right' ,\
                                     'center left','center right','lower center',\
                                     'upper center','center']
        self.style_choice = ['-' , '--' , '-.' , ':', 'None']
        
        Sizer = wx.BoxSizer(wx.VERTICAL)
        
        sb = wx.StaticBox(self, wx.ID_ANY, label = "Label")
        sbsizer0 = wx.StaticBoxSizer(sb, wx.VERTICAL)
        
        gbSizer0 = wx.GridBagSizer(5,5)
        
        self.title_label = wx.StaticText(self, label="Title" , style=wx.ALIGN_CENTER_VERTICAL)
        self.title = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        self.Xlabel_label = wx.StaticText(self, label="X Axis", style=wx.ALIGN_CENTER_VERTICAL)
        self.Xlabel = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        self.Ylabel_label = wx.StaticText(self, label="Y Axis", style=wx.ALIGN_CENTER_VERTICAL)
        self.Ylabel = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        gbSizer0.Add(self.title_label, (0,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.title, (0,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        gbSizer0.Add(self.Xlabel_label, (1,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Xlabel, (1,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        gbSizer0.Add(self.Ylabel_label, (2,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Ylabel, (2,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        
        gbSizer0.AddGrowableCol(1)
        
        sbsizer0.Add(gbSizer0, 1, wx.EXPAND, 5)
        
        sb = wx.StaticBox(self, wx.ID_ANY, label = "Legend")
        sbsizer1 = wx.StaticBoxSizer(sb, wx.VERTICAL)
        
        self.show_legend = wx.CheckBox(self, id=wx.ID_ANY, label="Show")
        
        hsizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.legend_location_label = wx.StaticText(self, label="Location" , style=wx.ALIGN_CENTER_VERTICAL)
        self.legend_location = wx.ComboBox(self, id = wx.ID_ANY, choices=self.legend_location_choice, style=wx.CB_READONLY)
        self.legend_location.SetValue(self.legend_location_choice[0])
        self.legend_style_label = wx.StaticText(self, label="Style" , style=wx.ALIGN_CENTER_VERTICAL)
        self.frame_on = wx.CheckBox(self, id=wx.ID_ANY, label="Frame on")
        self.fancy_box = wx.CheckBox(self, id=wx.ID_ANY, label="Fancy box")
        self.shadow = wx.CheckBox(self, id=wx.ID_ANY, label="Shadow")
        
        self.frame_on.SetValue(True)
        self.fancy_box.SetValue(False)
        self.shadow.SetValue(True)
        
        hsizer3.Add(self.legend_location_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer3.Add(self.legend_location, 1,wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer3.AddSpacer(20)
        hsizer3.Add(self.legend_style_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer3.Add(self.frame_on, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer3.Add(self.fancy_box, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer3.Add(self.shadow, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        
        sbsizer1.Add(self.show_legend, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sbsizer1.Add(hsizer3, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        
        sb = wx.StaticBox(self, wx.ID_ANY, label = "Grid")
        sbsizer2 = wx.StaticBoxSizer(sb, wx.VERTICAL)
        
        hsizer4 = wx.BoxSizer(wx.HORIZONTAL)
        self.grid_syle_label = wx.StaticText(self, label="Style" , style=wx.ALIGN_CENTER_VERTICAL)
        self.grid_style = wx.ComboBox(self, id = wx.ID_ANY, choices=self.style_choice, style=wx.CB_READONLY)
        
        self.grid_style.SetValue(self.style_choice[-1])
        
        self.grid_width_label = wx.StaticText(self, label="Width" , style=wx.ALIGN_CENTER_VERTICAL)
        self.grid_width = wx.SpinCtrl(self, id=wx.ID_ANY, style = wx.SP_ARROW_KEYS)
        
        self.grid_color_label = wx.StaticText(self, label="Color" , style=wx.ALIGN_CENTER_VERTICAL)
        self.grid_color_picker = wx.ColourPickerCtrl(self, id = wx.ID_ANY, col = 'black')
        
        hsizer4.Add(self.grid_syle_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer4.Add(self.grid_style, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer4.AddSpacer(20)
        hsizer4.Add(self.grid_width_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer4.Add(self.grid_width, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer4.AddSpacer(20)
        hsizer4.Add(self.grid_color_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer4.Add(self.grid_color_picker, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        
        sbsizer2.Add(hsizer4, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        
        hsizer5 = wx.BoxSizer(wx.HORIZONTAL)
        self.apply_button  = wx.Button(self, wx.ID_ANY, label="Apply")
        self.quit_button  = wx.Button(self, wx.ID_ANY, label="Quit")
        hsizer5.Add(self.apply_button, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALIGN_RIGHT, 0)
        hsizer5.Add(self.quit_button, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALIGN_RIGHT, 0)
        
        Sizer.Add(sbsizer0, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        Sizer.Add(sbsizer1, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        Sizer.Add(sbsizer2, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        Sizer.Add(hsizer5, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.ALL, 5)
        
        self.SetSizer(Sizer)        
        Sizer.Fit(self)
        self.Layout()    

        self.Bind(wx.EVT_BUTTON, self.set_settings, self.apply_button)    
        self.Bind(wx.EVT_BUTTON, self.on_close, self.quit_button)  
        
        self.get_settings()
    
    def get_settings(self, event = None):
        self.title.SetValue(self.parent.figure.gca().get_title())
        self.Xlabel.SetValue(self.parent.Xlabel)
        self.Ylabel.SetValue(self.parent.Ylabel)
        self.show_legend.SetValue(self.parent.show_legend)
        self.grid_style.SetValue(self.parent.gridStyle)
        self.grid_width.SetValue(self.parent.gridWidth)
        self.grid_color_picker.SetColour(wx.Colour(int(self.parent.gridColor[0]*255),int(self.parent.gridColor[1]*255),int(self.parent.gridColor[2]*255)))
        
    def set_settings(self, event = None):
        self.parent.figure.gca().set_title(self.title.GetValue())
        self.parent.Xlabel = self.Xlabel.GetValue()
        self.parent.Ylabel = self.Ylabel.GetValue()
        
        self.parent.figure.gca().set_xlabel(self.parent.Xlabel +  self.parent.fmt_Xunit)
        self.parent.figure.gca().set_ylabel(self.parent.Ylabel +  self.parent.fmt_Yunit)
        
        if self.show_legend.GetValue():
            self.parent.show_legend = True
            self.update_currentFig_legend()
        else:
            self.parent.show_legend = False
            self.parent.figure.gca().legend_ = None
        
        self.update_currentFig_grid()
        
        self.parent.canvas.draw()  
        
    def update_currentFig_legend(self):
        self.parent.legend_location = self.legend_location.GetValue()
        self.parent.legend_frameon = self.frame_on.GetValue()
        self.parent.legend_shadow = self.shadow.GetValue()
        self.parent.legend_fancybox = self.fancy_box.GetValue()

        self.parent.update_legend()  
  
        self.parent.canvas.draw()
    
    def update_currentFig_grid(self):
        style = self.grid_style.GetValue()
        width = self.grid_width.GetValue()
        color = self.grid_color_picker.GetColour()
        rvb_color = (color.Red()/255., color.Green()/255., color.Blue()/255.)

        self.parent.gridStyle = style
        self.parent.gridWidth = width
        self.parent.gridColor = rvb_color
        
        self.parent.figure.gca().grid(True, linestyle = style)
        self.parent.figure.gca().grid(True, linewidth = width)
        self.parent.figure.gca().grid(True, color = rvb_color)
        
        self.parent.canvas.draw() 
                
    def on_close(self, event = None):
        self.MakeModal(False)
        self.Destroy()


class AxesSettingsDialog(wx.Dialog):
    
    def __init__(self, parent=None):
        
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title="Axes Settings", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX)
        self.parent = parent
        self.build_dialog()
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
    def build_dialog(self):
        
        self.axis_scales_choices = ['linear', 'symlog', 'ln', 'log 10', 'log 2']
              
        Sizer = wx.BoxSizer(wx.VERTICAL)
        
        hsizer0 = wx.BoxSizer(wx.HORIZONTAL)
        
        sb0 = wx.StaticBox(self, wx.ID_ANY, label = "Bounds")
        sbsizer0 = wx.StaticBoxSizer(sb0, wx.VERTICAL)
        
        gbSizer0 = wx.GridBagSizer(5,5)
        
        self.Xmin_label = wx.StaticText(self, label="X Min", style=wx.ALIGN_CENTER_VERTICAL)
        self.Xmin = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        self.Ymin_label = wx.StaticText(self, label="Y Min", style=wx.ALIGN_CENTER_VERTICAL)
        self.Ymin = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)
        
        self.Xmax_label = wx.StaticText(self, label="X Max", style=wx.ALIGN_CENTER_VERTICAL)
        self.Xmax = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        self.Ymax_label = wx.StaticText(self, label="Y Max", style=wx.ALIGN_CENTER_VERTICAL)
        self.Ymax = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        self.auto_fit_button  = wx.Button(self, wx.ID_ANY, label="Auto fit")
        
        gbSizer0.Add(self.Xmin_label, (0,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Xmin, (0,1), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Ymin_label, (1,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Ymin, (1,1), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Xmax_label, (0,2), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Xmax, (0,3), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Ymax_label, (1,2), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Ymax, (1,3), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.auto_fit_button, (2,1),span = (1,3), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        sbsizer0.Add(gbSizer0, 1, wx.EXPAND, 5)
        
        sb1 = wx.StaticBox(self, wx.ID_ANY, label = "Unit and Scale")
        sbsizer1 = wx.StaticBoxSizer(sb1, wx.VERTICAL)
        
        gbSizer1 = wx.GridBagSizer(5,5)
        
        self.Xscale_label = wx.StaticText(self, label="X", style=wx.ALIGN_CENTER_VERTICAL)
        self.Xscale = wx.ComboBox(self, id = wx.ID_ANY, choices=self.axis_scales_choices, style=wx.CB_READONLY)

        self.Xunit = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)
        
        self.Yscale_label = wx.StaticText(self, label="Y", style=wx.ALIGN_CENTER_VERTICAL)
        self.Yscale = wx.ComboBox(self, id = wx.ID_ANY, choices=self.axis_scales_choices, style=wx.CB_READONLY)

        self.Yunit = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)
        
        gbSizer1.Add(self.Xscale_label, (0,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer1.Add(self.Xunit, (0,2), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer1.Add(self.Xscale, (0,4), flag = wx.ALIGN_CENTER_VERTICAL)
       
        gbSizer1.Add(self.Yscale_label,(1,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer1.Add(self.Yunit, (1,2), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer1.Add(self.Yscale, (1,4), flag = wx.ALIGN_CENTER_VERTICAL)
        
        sbsizer1.Add(gbSizer1, 1, wx.EXPAND, 5)
        
        hsizer0.Add(sbsizer0, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        hsizer0.Add(sbsizer1, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

               
        hsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.apply_button  = wx.Button(self, wx.ID_ANY, label="Apply")
        self.quit_button  = wx.Button(self, wx.ID_ANY, label="Quit")
        hsizer1.Add(self.apply_button, 0, wx.EXPAND, 0)
        hsizer1.Add(self.quit_button, 0, wx.EXPAND, 0)
        
        Sizer.Add(hsizer0, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        Sizer.Add(hsizer1, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.ALL, 5)
        
        self.SetSizer(Sizer)        
        Sizer.Fit(self)
        self.Layout()
        
        self.Bind(wx.EVT_BUTTON, self.auto_fit, self.auto_fit_button)
        self.Bind(wx.EVT_BUTTON, self.set_settings, self.apply_button)    
        self.Bind(wx.EVT_BUTTON, self.on_close, self.quit_button)  
    
        self.get_settings()
    
    def get_settings(self, event = None):
        [Xmin, Xmax, Ymin, Ymax] = self.parent.figure.gca().axis()
        self.parent.Xmin = Xmin
        self.parent.Ymin = Ymin
        self.parent.Xmax = Xmax
        self.parent.Ymax = Ymax
        
        self.Xmin.SetValue(str(self.parent.Xmin))
        self.Ymin.SetValue(str(self.parent.Ymin))
        self.Xmax.SetValue(str(self.parent.Xmax))
        self.Ymax.SetValue(str(self.parent.Ymax))
         
        self.Xunit.SetValue(str(self.parent.Xunit))
        self.Yunit.SetValue(str(self.parent.Yunit))
         
        self.Xscale.SetValue(self.parent.Xscale)
        self.Yscale.SetValue(self.parent.Yscale)
        
    def set_settings(self, event = None):
        self.parent.Xunit = self.Xunit.GetValue()
        self.parent.Yunit = self.Yunit.GetValue()
         
        self.parent.figure.gca().set_xlabel(self.parent.Xlabel + self.parent.fmt_Xunit )
        self.parent.figure.gca().set_ylabel(self.parent.Ylabel + self.parent.fmt_Yunit )
         
        self.parent.Xscale = self.Xscale.GetValue()
        self.parent.Yscale = self.Yscale.GetValue()
         
        self.parent.scale_xAxis()
        self.parent.scale_yAxis()
         
        self.parent.Xmin = float(self.Xmin.GetValue())
        self.parent.Ymin = float(self.Ymin.GetValue())
        self.parent.Xmax = float(self.Xmax.GetValue())
        self.parent.Ymax = float(self.Ymax.GetValue())
         
        self.parent.figure.gca().axis([self.parent.Xmin, self.parent.Xmax, self.parent.Ymin, self.parent.Ymax])  
        
        self.parent.set_ticks()
        self.parent.canvas.draw()
    
    def auto_fit(self, event = None):
        self.parent.on_auto_fit()
        self.Xmin.SetValue(str(self.parent.Xmin))
        self.Ymin.SetValue(str(self.parent.Ymin))
        self.Xmax.SetValue(str(self.parent.Xmax))
        self.Ymax.SetValue(str(self.parent.Ymax))
    
    def on_close(self, event = None):
        self.MakeModal(False)
        self.Destroy()


class LinesSettingsDialog(wx.Dialog):
    
    def __init__(self, parent=None):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title="Lines Settings", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX)
        self.parent = parent
        self.current_line = None
        self.build_dialog()
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
    def build_dialog(self):
        
        self.marker = ['o', '^','s', 'p' ,'*']
        
        self.style_choice = ['-' , '--' , '-.' , ':', 'None'] + self.marker
        
        Sizer = wx.BoxSizer(wx.VERTICAL)
        
        bagSizer    = wx.GridBagSizer(hgap=5, vgap=5)
        
        self.lines = wx.ListCtrl(self, wx.ID_ANY, style = wx.LC_REPORT)
        self.lines.InsertColumn(0, 'Lines')
        
        self.del_button  = wx.Button(self, wx.ID_ANY, label="Delete")
        
        self.color_label = wx.StaticText(self, label="Color" , style=wx.ALIGN_CENTER_VERTICAL)
        self.color_picker = wx.ColourPickerCtrl(self, id = wx.ID_ANY, col = 'black')
        
        self.legend_label = wx.StaticText(self, label="Legend" , style=wx.ALIGN_CENTER_VERTICAL)
        self.legend = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)
        
        self.style_label = wx.StaticText(self, label="Style", style=wx.ALIGN_CENTER_VERTICAL)
        self.style = wx.ComboBox(self, id = wx.ID_ANY, choices=self.style_choice, style=wx.CB_READONLY)
        
        self.width_label = wx.StaticText(self, label="Width" , style=wx.ALIGN_CENTER_VERTICAL)
        self.width = wx.SpinCtrl(self, id=wx.ID_ANY, style = wx.SP_ARROW_KEYS)
        
        bagSizer.Add(self.lines, pos=(0,0), span=(4,3), flag = wx.EXPAND)
        
        bagSizer.Add(self.del_button, pos=(4,0), span=(1,3), flag = wx.EXPAND)
        
        bagSizer.Add(self.legend_label, pos=(1,4), flag = wx.ALIGN_CENTER_VERTICAL)
        bagSizer.Add(self.legend, pos=(1,5) ,span=(1,5), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        
        bagSizer.Add(self.style_label, pos=(2,4), flag = wx.ALIGN_CENTER_VERTICAL)
        bagSizer.Add(self.style, pos=(2,5), flag = wx.ALIGN_CENTER_VERTICAL)
        
        bagSizer.Add(self.width_label, pos=(2,7), flag = wx.ALIGN_CENTER_VERTICAL)
        bagSizer.Add(self.width, pos=(2,8), flag = wx.ALIGN_CENTER_VERTICAL)
        
        bagSizer.Add(self.color_label, pos=(3,4), flag = wx.ALIGN_CENTER_VERTICAL)
        bagSizer.Add(self.color_picker, pos=(3,5), flag = wx.ALIGN_CENTER_VERTICAL)
        
        hsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.apply_button  = wx.Button(self, wx.ID_ANY, label="Apply")
        self.quit_button  = wx.Button(self, wx.ID_ANY, label="Quit")
        hsizer1.Add(self.apply_button, 0, wx.EXPAND, 0)
        hsizer1.Add(self.quit_button, 0, wx.EXPAND, 0)
        
        Sizer.Add(bagSizer, 0, wx.EXPAND|wx.ALL, 5)
        Sizer.Add(hsizer1, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.ALL, 5)
          
        self.SetSizer(Sizer)        
        Sizer.Fit(self)
        self.Layout()
        
        self.Bind(wx.EVT_BUTTON, self.delete_line, self.del_button)    
        self.Bind(wx.EVT_BUTTON, self.set_settings, self.apply_button)    
        self.Bind(wx.EVT_BUTTON, self.on_close, self.quit_button)  
        self.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.on_select_item, self.lines)
    
        self.set_lines()
    
    def set_lines(self):
        self.lines.DeleteAllItems()
        id = 0
        for k in self.parent.plots.keys():
            if type(self.parent.plots[k][0].get_color()) is str:
                r,g,b = mpl.colors.colorConverter.colors[self.parent.plots[k][0].get_color()]
            else:
                r,g,b = self.parent.plots[k][0].get_color()
            self.lines.InsertStringItem(index = id, label = k)
            color = wx.Colour(int(r*255), int(g*255), int(b*255))
            self.lines.SetItemTextColour(id, color)
            id += 1
    
    def on_select_item(self, event):
        line_name = event.GetLabel()
        if not line_name:
            return
        self.current_line = self.parent.plots[line_name][0]
        if self.parent.selectedLine is not None: 
            self.parent.selectedLine.set_alpha(1.0)
            self.parent.figure.canvas.draw()

        # set new selection and alpha  
        self.parent.selectedLine = self.current_line
        self.parent.selectedLine.set_alpha(0.4)
        self.parent.figure.canvas.draw()
        
        if type(self.current_line.get_color()) is str:
            r,g,b = mpl.colors.colorConverter.colors[self.current_line.get_color()]
        else:
            r,g,b = self.current_line.get_color()
        color = wx.Colour(int(r*255), int(g*255), int(b*255))
        self.color_picker.SetColour(color)
        self.legend.SetValue(self.parent.plots[line_name][1])
        self.style.SetValue(self.current_line.get_linestyle())
        self.width.SetValue(self.current_line.get_linewidth())
        
    def set_settings(self, event = None):
        if self.current_line is None:
            return
        
        color= self.color_picker.GetColour()
        self.current_line.set_color((color.Red()/255., color.Green()/255., color.Blue()/255.))
        for k,v in self.parent.plots.items():
            if v[0] is self.current_line:
                new_legend = self.legend.GetValue()
                if new_legend != v[1]:
                    v[1] = new_legend
                    self.parent.update_legend()
        s = self.style.GetValue()
        if s in self.marker:
            self.current_line.set_linestyle('None')
            self.current_line.set_marker(s)
        else:
            self.current_line.set_marker('')
            self.current_line.set_linestyle(self.style.GetValue())
        self.current_line.set_linewidth(self.width.GetValue())
        if self.parent.show_legend:
            self.parent.update_legend()
        self.parent.canvas.draw()
        self.set_lines()
        
    def delete_line(self, event = None):
        d = wx.MessageDialog(None,
                 'Do you really want delete this line ?',
                 'Question',
                 wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if d.ShowModal() == wx.ID_YES:
            pass
        else:
            return
        self.parent.delete_line(self.current_line)
        self.set_lines()
        
    def on_close(self, event = None):
        self.MakeModal(False)
        # unselect selection
        if self.parent.selectedLine is not None:
            self.parent.selectedLine.set_alpha(1.0)
            self.parent.selectedLine.figure.canvas.draw()
            self.parent.selectedLine = None
        self.Destroy()

class ScaledLocator(mpl.ticker.MaxNLocator):
    """
    Locates regular intervals along an axis scaled by *dx* and shifted by
    *x0*. For example, this would locate minutes on an axis plotted in seconds
    if dx=60.  This differs from MultipleLocator in that an approriate interval
    of dx units will be chosen similar to the default MaxNLocator.
    """
    def __init__(self, dx=1.0, x0=0.0):
        self.dx = dx
        self.x0 = x0
        mpl.ticker.MaxNLocator.__init__(self, nbins=9, steps=[1, 2, 5, 10])

    def rescale(self, x):
        return x * self.dx + self.x0
    def inv_rescale(self, x):
        return  (x - self.x0) / self.dx

    def __call__(self): 
        vmin, vmax = self.axis.get_view_interval()
        vmin, vmax = self.rescale(vmin), self.rescale(vmax)
        vmin, vmax = mpl.transforms.nonsingular(vmin, vmax, expander = 0.05)
        locs = self.bin_boundaries(vmin, vmax)
        locs = self.inv_rescale(locs)
        prune = self._prune
        if prune=='lower':
            locs = locs[1:]
        elif prune=='upper':
            locs = locs[:-1]
        elif prune=='both':
            locs = locs[1:-1]
        return self.raise_if_exceeds(locs)

class ScaledFormatter(mpl.ticker.OldScalarFormatter):
    """Formats tick labels scaled by *dx* and shifted by *x0*."""
    def __init__(self, dx=1.0, x0=0.0, **kwargs):
        self.dx, self.x0 = dx, x0

    def rescale(self, x):
        return x * self.dx + self.x0

    def __call__(self, x, pos=None):
        xmin, xmax = self.axis.get_view_interval()
        xmin, xmax = self.rescale(xmin), self.rescale(xmax)
        d = abs(xmax - xmin)
        x = self.rescale(x)
        s = self.pprint_val(x, d)
        return s

            
class PlotterError(Error):
    pass   


class PlotterPanel(wx.Panel):
    
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self.parent = parent
        self._mgr = aui.AuiManager(self)
        
        self.build_panel()
        self.build_layout()
        
    @property
    def dataproxy(self):
        return self.parent._data
    
    @property
    def active_plot(self):
        try :
            page = self.plot_notebook.GetPage(self.plot_notebook.GetSelection())
            return page  
        except: 
            return None
        
    def build_panel(self):
        self.plot_notebook = aui.AuiNotebook(self)
    
    def build_layout(self):
        self._mgr.AddPane(self.plot_notebook, aui.AuiPaneInfo().Center().Dock().CloseButton(False).Caption("Multiple Plot Window"))
        self._mgr.Update()


class CrossSlicer(object):
    def __init__(self, parent, canvas, dialog, hplot, vplot, fig, color_index, hlegend, vlegend):
        self.related_plot = parent        
        self.canvas = canvas       
        self.dialog = dialog
        self.hplot = hplot
        self.vplot = vplot
        self.fig = fig
        self.color_index =color_index
        self.hlegend = hlegend
        self.vlegend = vlegend


class MultiView(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self.parent = parent
 
        self.type = 'image'
        
        self.unique_slicer = None
        self.related_slicer_checkbox=None
        
        self._mgr = aui.AuiManager(self)
        self.Layout()

    @property
    def dataproxy(self):
        return self.parent.dataproxy

    def AddPane(self, *args, **kwds):
        self._mgr.AddPane(*args, **kwds)

    def Update(self):
        self._mgr.Update()
        
        
class DataPanel(wx.Panel):

    def __init__(self, parent, *args,**kwds):
        wx.Panel.__init__(self, parent, *args, **kwds)
        self.parent = parent
        self._mgr = aui.AuiManager(self)
        
        self.selectedVar = None
        self.activePlot = None
        self.selectedPlot = None
        
        self.unique_slicer = None
        self.related_slicer_checkbox=None
        
        self.build_panel()
                
    def build_panel(self):    
        
        self.setup = wx.Panel(self)
        
        sizer0 =  wx.BoxSizer(wx.VERTICAL)
        
        if self.standalone:
            self.datasetlist = wx.ListCtrl(self.setup, wx.ID_ANY,style = wx.LC_REPORT|wx.LC_SINGLE_SEL)
            self.datasetlist.InsertColumn(0, 'key', width=100)
            self.datasetlist.InsertColumn(1, 'filename', width=100)
            self.datasetlist.InsertColumn(2, 'path', width=500)
            
            sizer0.Add(self.datasetlist, 1, wx.ALL|wx.EXPAND, 2)
            
            sizer3 =  wx.BoxSizer(wx.HORIZONTAL)

            self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_dataset,  self.datasetlist) 
            self.Bind(wx.EVT_LIST_KEY_DOWN, self.delete_dataset, self.datasetlist)

        self.datalist = wx.ListCtrl(self.setup, wx.ID_ANY,style = wx.LC_REPORT|wx.LC_SINGLE_SEL)
        self.datalist.InsertColumn(0, 'Variable', width=100)
        self.datalist.InsertColumn(1, 'Unit', width=65)
        self.datalist.InsertColumn(2, 'Axis', width=50)
        self.datalist.InsertColumn(3, 'Dimension')
        
        sizer1 =  wx.BoxSizer(wx.HORIZONTAL)
       
        self.plot_type_label = wx.StaticText(self.setup, label="Select Plotter")
        self.plotter_list = {'Line':1, 'Image':2, 'Elevation':2,'Iso-Surface':3,'Scalar-Field':3}
        self.plot_type  = wx.ComboBox(self.setup, style=wx.CB_READONLY)
        
        sizer1.Add(self.plot_type_label, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.plot_type, 1, wx.ALIGN_CENTER_VERTICAL)
        
        sizer2 =  wx.BoxSizer(wx.HORIZONTAL)
        
        self.plot_button  = wx.Button(self.setup, wx.ID_ANY, label="Plot in new window")
        self.replot_button  = wx.Button(self.setup, wx.ID_ANY, label="Plot in current figure")
        
        sizer2.Add(self.plot_button, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        sizer2.Add(self.replot_button, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        
        sizer0.Add(self.datalist, 2, wx.ALL|wx.EXPAND, 2)
        sizer0.Add(sizer1, 0, wx.ALL|wx.EXPAND, 2)
        sizer0.Add(sizer2, 0, wx.ALL|wx.EXPAND, 2)
        
        self.setup.SetSizer(sizer0)        
        sizer0.Fit(self.setup)
        self.setup.Layout()
        
        qviewPanel = wx.Panel(self)
        sb_sizer2 =  wx.BoxSizer(wx.VERTICAL)
                      
        self.QV_Figure = Figure(figsize=(1,1))
        self.QV_Canvas = FigureCanvasWxAgg(qviewPanel, wx.ID_ANY, self.QV_Figure)
        self.QV_Plot = self.QV_Figure.add_axes([0.01,0.01,0.98,0.98])
        sb_sizer2.Add(self.QV_Canvas, 1, wx.ALL|wx.EXPAND, 2)
        
        qviewPanel.SetSizer(sb_sizer2)        
        sb_sizer2.Fit(qviewPanel)
        qviewPanel.Layout()
        
        self._mgr.AddPane(qviewPanel,aui.AuiPaneInfo().Dock().Bottom().Floatable(False).CloseButton(False).Caption("Quick View").MinSize((300,300)))
        self._mgr.AddPane(self.setup,aui.AuiPaneInfo().Dock().Center().Floatable(False).CloseButton(False).Caption("Data"))
        
        self._mgr.Update()

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_variables,  self.datalist) 
        self.Bind(wx.EVT_BUTTON, self.on_plot, self.plot_button)
        self.Bind(wx.EVT_BUTTON, self.on_replot, self.replot_button)
        
    @property
    def dataDict(self):
        if self.standalone:
            return self.parent._dataDict
        else:
            return None
    
    @property
    def standalone(self):
        return self.parent.standalone
        
    @property
    def dataproxy(self):
        return self.parent._data
    
    @property
    def plotterPanel(self):
        return self.parent._plotterPanel
    
    @property
    def plotterNotebook(self):
        return self.parent._plotterPanel.plot_notebook
   
    def delete_dataset(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_DELETE:
            dataset = self.datasetlist.GetItemText(self.datasetlist.GetFocusedItem())
            self.dataDict.pop(dataset)
            self.datasetlist.DeleteItem(self.datasetlist.GetFocusedItem())
            self.datalist.DeleteAllItems()
            self.datasetlist.Select(0,1) 
            
    def on_select_dataset(self, event):
        if event is None:
            return
        currentItem = event.m_itemIndex
        var = self.datasetlist.GetItemText(currentItem)
        self.parent._data = self.dataDict[var]['data']
        self.show_data()
        
    def show_dataset(self):
        self.datasetlist.DeleteAllItems()
        for i, k in enumerate(self.dataDict.keys()):
            self.datasetlist.InsertStringItem(i, k)
            self.datasetlist.SetStringItem(i, 1,self.dataDict[k]['basename'])
            self.datasetlist.SetStringItem(i, 2,self.dataDict[k]['path'])
        self.datasetlist.Select(0, True)
        
    def show_data(self):
        self.datalist.DeleteAllItems()
        for i, var in enumerate(sorted(self.dataproxy.keys())):
            self.datalist.InsertStringItem(i, var)
            self.datalist.SetStringItem(i, 1,self.dataproxy[var]['units'])
            axis = ','.join(self.dataproxy[var]['axis'])
            if not axis :
                axis = 'None'
            self.datalist.SetStringItem(i, 2,axis)
            self.datalist.SetStringItem(i, 3,str(self.dataproxy[var]['data'].ndim))
        self.datalist.Select(0, True)
            
    def on_select_variables(self, event = None):
        if event is None:
            return
        currentItem = event.m_itemIndex
        var = self.datalist.GetItemText(currentItem)
        axis_list = self.dataproxy[var]['axis']
        data = self.dataproxy[var]['data']
        ndim = data.ndim
        unit = self.dataproxy[var]['units']
        self.plot_type.Clear()
        types = []
        for type, req_dim in self.plotter_list.items():
            if ndim == req_dim:
                types += [type]
        self.plot_type.SetItems(types)
        if not self.plot_type.IsEmpty():            
            self.plot_type.SetStringSelection(types[-1])

        self.selectedVar = var
        self.QV_plot(data)            
    
    def QV_plot(self, data):
        self.QV_Plot.clear()
        ndim = data.ndim

        if ndim == 1:
            self.QV_Plot.plot(data)
            self.QV_Figure.gca().legend((self.selectedVar,None), loc = 'best', frameon = True, shadow = True, fancybox = False) 
        elif ndim == 2:
            self.QV_Plot.imshow(data.T, interpolation='nearest', origin='lower')
            
        else:
            self.QV_Plot.text(0.1, 0.5, 'No QuickView for data with dimension > 2 ')
        self.QV_Plot.set_aspect('auto', 'datalim')

        self.QV_Canvas.draw()

    def on_plot(self, event=None):
        if self.selectedVar is None:
            return
        
        data = self.dataproxy[self.selectedVar]['data']
        plot_type = self.plot_type.GetValue()
        if plot_type == 'Line':
            Plotter = Plotter1d(self)
            self.plotterNotebook.AddPage(Plotter, "%s(%s)"%(self.selectedVar,plot_type))
            Plotter.Plot(data, self.selectedVar)
            
        elif plot_type == 'Image':
            Plotter = Plotter2d(self)
            self.plotterNotebook.AddPage(Plotter, "%s(%s)"%(self.selectedVar,plot_type))
            Plotter.Plot(data, self.selectedVar)
            
        elif plot_type == 'Elevation':
            Plotter = Plotter3d(self.parent)
            self.plotterNotebook.AddPage(Plotter, "%s(%s)"%(self.selectedVar,plot_type))
            Plotter.elevation(data)
            
        elif plot_type == 'Iso-Surface':
            Plotter = Plotter3d(self.parent)
            self.plotterNotebook.AddPage(Plotter, "%s(%s)"%(self.selectedVar,plot_type))
            Plotter.isosurface(data,data.mean(), 'w')
            
        elif plot_type == 'Scalar-Field':
            Plotter = Plotter3d(self.parent)
            self.plotterNotebook.AddPage(Plotter, "%s(%s)"%(self.selectedVar,plot_type))
            Plotter.scalarfield(data)
        else :
            raise PlotterError("Unrecognized plotter type : %s"%plot_type)
        
    def on_replot(self, event=None):
        self.selectedPlot = self.plotterPanel.active_plot
        
        if self.selectedPlot is None:
            return
        
        plot_type = self.plot_type.GetValue()
        if plot_type == 'Line' and self.selectedPlot.type == 'line':     
            data = self.dataproxy[self.selectedVar]['data']
            self.selectedPlot.Plot(data, self.selectedVar)
            
        if plot_type == 'Image' and self.selectedPlot.type == 'image': 
            data = self.dataproxy[self.selectedVar]['data']
            if hasattr(self.selectedPlot, 'AddPane'):
                Plotter = Plotter2d(self.selectedPlot)
                Plotter.Plot(data, self.selectedVar)
                self.selectedPlot.AddPane(Plotter, aui.AuiPaneInfo().Right().CloseButton(True).CaptionVisible(True).Caption(self.selectedVar).MinSize((200,-1)))
                self.selectedPlot.Update()
            else:
                li_idx = self.plotterNotebook.GetPageIndex(self.selectedPlot)
                
                multiplot = MultiView(self)
                
                NewPlotter = Plotter2d(multiplot)
                NewPlotter.Plot(data, self.selectedVar)
                
                OldPlotter = Plotter2d(multiplot)
                OldPlotter.rePlot(self.selectedPlot)

                multiplot.AddPane(NewPlotter, aui.AuiPaneInfo().Right().CloseButton(True).CaptionVisible(True).Caption(self.selectedVar).MinSize((200,-1)))
                multiplot.AddPane(OldPlotter, aui.AuiPaneInfo().Center().CloseButton(True).CaptionVisible(True).Caption(self.selectedPlot.varname))
                multiplot.Update()
                
                self.selectedPlot.Destroy()
                self.selectedPlot = None
                self.plotterNotebook.RemovePage(li_idx)
                self.plotterNotebook.AddPage(multiplot, '*MultiView*(Image)', select=True)
            
            

class PlotterPlugin(ComponentPlugin):

    type = "plotter"
    
    label = "2D/3D Plotter"
    
    ancestor = 'netcdf_data'
    
    category = ("Plotter",)
    
    def __init__(self, parent, mode = 'embeded', *args, **kwargs):
        
        self.standalone = False
        
        if mode == 'standalone':
            self.make_standalone()
        
        ComponentPlugin.__init__(self, parent, *args, **kwargs)
        
        
    def build_panel(self):
        self._dataPanel = DataPanel(self)
        self._plotterPanel = PlotterPanel(self)
        
        self._mgr.AddPane(self._dataPanel, aui.AuiPaneInfo().Dock().Left().Floatable(False).CloseButton(False).CaptionVisible(False).MinSize((300,-1)))
        self._mgr.AddPane(self._plotterPanel, aui.AuiPaneInfo().Center().Dock().Floatable(False).CloseButton(False).CaptionVisible(False))
    
    def make_standalone(self):
        self.standalone = True
        self._dataDict = collections.OrderedDict()
        
    def plug(self, *args, **kwargs):
        self._data = self.dataproxy.data
        self._dataPanel.show_data()

        self._parent._mgr.GetPane(self).Dock().Floatable(False).Center().CloseButton(True).Caption("2D/3D Plotter")
        self._parent._mgr.Update()        

    
class PlotterFrame(wx.Frame):
    
    def __init__(self, parent, title="2D/3D Plotter"):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title, style=wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER)
        self.__build_dialog()
        self.__build_menu()
 
    def __build_menu(self):
        mainMenu = wx.MenuBar()
        fileMenu = wx.Menu()
        loadData = fileMenu.Append(wx.ID_ANY, 'Load')
        fileMenu.AppendSeparator()
        quit = fileMenu.Append(wx.ID_ANY, 'Quit')

        mainMenu.Append(fileMenu, 'File')
        
        
        icon = wx.Icon(ICONS["plot"], wx.BITMAP_TYPE_PNG)
        self.SetIcon(icon) 
        
        self.SetMenuBar(mainMenu)
        
        self.Bind(wx.EVT_MENU, self.on_load_data, loadData)
        self.Bind(wx.EVT_MENU, self.on_quit, quit)
        self.Bind(wx.EVT_CLOSE, self.on_quit)
   
    def on_quit(self, event=None):
        d = wx.MessageDialog(None,
                             'Do you really want to quit ?',
                             'Question',
                             wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if d.ShowModal() == wx.ID_YES:
            d.Destroy()
            self.Destroy()
                
    def on_load_data(self, event=None):
        filters = 'NC file (*.nc)|*.nc|All files (*.*)|*.*'
        dialog = wx.FileDialog ( self, message = 'Open file...', wildcard=filters, style=wx.MULTIPLE)
        if dialog.ShowModal() == wx.ID_CANCEL:
            return
        
        baselist = dialog.GetFilenames()
        filelist = dialog.GetPaths()
        
        for i in range(len(filelist)):
            basename = baselist[i]    
            filename = filelist[i]
            
            f = NetCDFFile(filename,"r")
            vars = f.variables
            data = collections.OrderedDict()
            for k in vars:
                data[k]={}
                if hasattr(vars[k], 'axis'):
                    if vars[k].axis:
                        data[k]['axis'] =  vars[k].axis.split('|')
                    else:
                        data[k]['axis'] = []
                else:
                    data[k]['axis'] = []
                data[k]['data'] = vars[k].getValue()
                data[k]['units'] = getattr(vars[k],"units","au")
            
            unique_name = self.unique(basename, self.plugin._dataDict)
            
            self.plugin._dataDict[unique_name]={'data':data,'path':filename,'basename':basename}
            self.plugin._dataPanel.show_dataset()
    
    def unique(self, key, dict):
        skey = key
        i = 0
        while key in dict.keys():
            key = skey + '_%d'%i
            i += 1
        return key 
    
    def __build_dialog(self):
        mainPanel = wx.Panel(self, wx.ID_ANY)
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.plugin = PlotterPlugin(mainPanel, mode = 'standalone')
         
        mainSizer.Add(self.plugin, 1, wx.ALL|wx.EXPAND, 5)

        mainPanel.SetSizer(mainSizer)        
        mainSizer.Fit(mainPanel)
        mainPanel.Layout()

        self.SetSize((1200, 900))


if __name__ == "__main__":
    app = wx.App(False)
    f = PlotterFrame(None)
    f.Show()
    app.MainLoop()
    