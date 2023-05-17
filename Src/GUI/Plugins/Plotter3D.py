# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Plugins/Plotter3D.py
# @brief     Implements module/class/test Plotter3D
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

import wx
import wx.aui as wxaui

import numpy

import vtk
from vtk.util.numpy_support import numpy_to_vtk
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor 

from MDANSE.Core.Error import Error

DTYPES_TO_VTK = {'uint8':vtk.VTK_UNSIGNED_CHAR,
                 'uint16':vtk.VTK_UNSIGNED_SHORT,
                 'int8':vtk.VTK_CHAR,
                 'int16':vtk.VTK_SHORT,
                 'int32':vtk.VTK_INT,
                 'uint32':vtk.VTK_UNSIGNED_INT,
                 'float32':vtk.VTK_FLOAT,
                 'float64':vtk.VTK_DOUBLE}

class Plotter3DError(Error):
    pass   

class Plotter3D(wx.Panel):
    
    type = '3d'
    
    def __init__(self, parent, *args, **kwargs):
        '''
        The constructor.
        '''
        wx.Panel.__init__(self, parent, *args, **kwargs)
        
        self.parent = parent
        
        self._mgr = wxaui.AuiManager(self)
        
        self.build_panel()
        
    def build_panel(self):
        
        self.viewer = wx.Panel(self)
                
        self.iren = wxVTKRenderWindowInteractor(self.viewer, -1, size=(500,500), flag=wx.EXPAND)
        self.iren.SetPosition((0,0))
        # define interaction style        
        self.iren.GetInteractorStyle().SetCurrentStyleToTrackballCamera() 
        self.iren.Enable(1)
        
        # create renderer  
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(1, 1, 1)
        self.iren.GetRenderWindow().AddRenderer(self.renderer)
    
        # create camera
        self.camera=vtk.vtkCamera() 
        # associate camera to renderer
        self.renderer.SetActiveCamera(self.camera)
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
        
        self._mgr.AddPane(self.viewer, wxaui.AuiPaneInfo().Center().Dock().DestroyOnClose(False).CloseButton(False).CaptionVisible(False).MinSize(self.iren.GetSize()))
        self._mgr.Update()
    
    def array_to_2d_imagedata(self):
                
        if self.data.ndim !=2:
            raise Plotter3DError('Data dimension should be 2')
        
        nx = self.data.shape[0]
        ny = self.data.shape[1]
        nz = 1
        
        image = vtk.vtkImageData()
        image.SetDimensions(nx,ny,1)
        image.SetExtent(0, nx-1, 0, ny-1, 0, nz-1)

        dtype = DTYPES_TO_VTK[self.data.dtype.name]
        
        if vtk.vtkVersion.GetVTKMajorVersion()<6:
            image.SetScalarType(dtype)
            image.SetNumberOfScalarComponents(1)
        else:
            image.AllocateScalars(dtype,1)
            
        image.SetSpacing(1.,1.,0.)

        vtk_array = numpy_to_vtk(num_array=self.data.ravel(), deep=True, array_type=dtype)
        image.GetPointData().SetScalars(vtk_array)

        return image

    def array_to_3d_imagedata(self):
        
        if self.data.ndim !=3:
            raise Plotter3DError('Data dimension should be 3')
        
        nx = self.data.shape[0]
        ny = self.data.shape[1]
        nz = self.data.shape[2]
        image = vtk.vtkImageData()
        image.SetDimensions(nx,ny,nz)
        image.SetExtent(0, nx-1, 0, ny-1, 0, nz-1)
        
        dtype = DTYPES_TO_VTK[self.data.dtype.name]
        
        if vtk.vtkVersion.GetVTKMajorVersion()<6:
            image.SetScalarType(dtype)
            image.SetNumberOfScalarComponents(1)
        else:
            image.AllocateScalars(dtype,1)

        vtk_array = numpy_to_vtk(num_array=self.data.ravel(), deep=True, array_type=dtype)
        image.GetPointData().SetScalars(vtk_array)
        
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
        
        self._mgr.AddPane(self.settings, wxaui.AuiPaneInfo().Center().Dock().Bottom().CloseButton(False).CaptionVisible(False))
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
        
        self._mgr.AddPane(self.settings, wxaui.AuiPaneInfo().Center().Dock().Bottom().CloseButton(False).CaptionVisible(False))
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
        
        self._mgr.AddPane(self.settings, wxaui.AuiPaneInfo().Center().Dock().Bottom().CloseButton(False).CaptionVisible(False))
        self._mgr.Update()
        
    def cpt_isosurf(self, event = None):
        try :
            isov = float(self.isov.GetValue())
        except:
            raise Plotter3DError('Contour level has wrong format : %s'%self.isov.GetValue())
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
        else :
            if self.axes.GetVisibility():
                self.axes.VisibilityOff()
            else:
                self.axes.VisibilityOn()
    
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

        R = numpy.array(self.ExtractRotMat(self.orientation_matrix)) #extraction de la matrice de rotation depuit la vtk 4x4
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
        R=numpy.asarray(R,float)
        if det(R) < 0. :
            raise Exception("determinant is negative\n"+str(R))
        if not numpy.allclose(numpy.mat(R)*R.T,numpy.identity(3),atol=tolerance):
            raise Exception("not an orthogonal matrix\n"+str(R))
        cang = 2.0-numpy.sum(numpy.square([ R[0,2],R[1,2],R[2,0],R[2,1],R[2,2] ]))
        cang = numpy.sqrt(min(max(cang,0.0),1.0))
        if (R[2,2]<0.0): cang=-cang
        ang= numpy.arccos(cang)
        beta=numpy.degrees(ang)
        sang=numpy.sin(ang)
        if(sang>fuzz):
            alpha=numpy.degrees(numpy.arctan2(R[1,2], R[0,2]))
            gamma=numpy.degrees(numpy.arctan2(R[2,1],-R[2,0]))
        else:
            alpha=numpy.degrees(numpy.arctan2(-R[0,1],R[0,0]*R[2,2]))
            gamma=0.
        if   self.almost(beta,0.,fuzz):
            alpha,beta,gamma = alpha+gamma,  0.,0.
        elif self.almost(beta,180.,fuzz):
            alpha,beta,gamma = alpha-gamma,180.,0.
        alpha=numpy.mod(alpha,360.);
        gamma=numpy.mod(gamma,360.)
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
