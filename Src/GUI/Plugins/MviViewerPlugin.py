# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Plugins/MviViewerPlugin.py
# @brief     Implements module/class/test MviViewerPlugin
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import numpy

import vtk
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor 

import wx
import wx.aui as aui

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.GUI.Plugins.ComponentPlugin import ComponentPlugin

UC_COMP       = 'COMPONENT:'
MC_COMP       = 'MCDISPLAY: component'
MC_COMP_SHORT = 'COMP: '
MC_LINE       = 'MCDISPLAY: multiline'
MC_CIRCLE     = 'MCDISPLAY: circle'
MC_ENTER      = 'ENTER:'
MC_LEAVE      = 'LEAVE:'
MC_STATE      = 'STATE:'
MC_SCATTER    = 'SCATTER:'
MC_ABSORB     = 'ABSORB:'
MC_MAGNIFY    = 'MCDISPLAY: magnify'
MC_START      = 'MCDISPLAY: start'
MC_END        = 'MCDISPLAY: end'
MC_STOP       = 'INSTRUMENT END:'

POINTS_IN_CIRCLE = 128

class MviViewerPluginError(Error):
    pass
   
class MviViewerPlugin(ComponentPlugin):
    '''
    This class sets up the Mcstas virtual instrument viewer using vtk functionnalities.
    '''
        
    label = "McStas Virtual Instrument Viewer"
    
    ancestor = ["mvi_trace"]
    
    category = ("Viewer",)
            
    def __init__(self, parent, *args, **kwargs):
        
        ComponentPlugin.__init__(self, parent, *args, **kwargs)
   
    def build_panel(self):
                
        self._iren = wxVTKRenderWindowInteractor(self, wx.ID_ANY, size=self.GetSize())
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
        
        self._iren.AddObserver("LeftButtonPressEvent", self.emulate_focus)
        
        self._mgr.AddPane(self._iren, aui.AuiPaneInfo().Dock().Center().CaptionVisible(False).CloseButton(False))
                
        self._mgr.Update()

    def plug(self):
        
        self._parent._mgr.GetPane(self).Dock().Floatable(False).Center().CloseButton(True)

        self._parent._mgr.Update()
                        
        self.parse_trace(self.dataproxy._filename)
             
    def emulate_focus(self, obj, event):
        
        self.SetFocusIgnoringChildren()
             
    def close(self):
        pass

    def parse_trace(self, fname):
        ''' 
        Parse McStas trace output from stdin and write results to file objects csv_comps and csv_lines 
        '''

        color = 0
    
        # map from component name to (position, rotation matrix)
        comps = {}
    
        # active (position, rotation matrix)
        comp = (numpy.array([0,0,0]),numpy.array([1,0,0,0,1,0,0,0,1]).reshape(3,3))
    
        # previous neutron position
        prev = None
        skip = False
        # we are drawing a neutron
        active = False
        xstate=[]
        ystate=[]
        zstate=[]
        
        circlePoints = vtk.vtkPoints()
        circleLines = vtk.vtkCellArray()
        circle_pid = 0
        
        multiPoints = vtk.vtkPoints()
        multiLines = vtk.vtkCellArray()
        multi_pid = 0
        
        neutronPoints = vtk.vtkPoints()
        neutronLines = vtk.vtkCellArray()
        neutron_pid = 0
        
        f = open(fname, 'r')
        lines = f.readlines()
        
        for i, line in enumerate(lines):
            if not line:
                break
            line = line.strip()
            # register components
            if line.startswith(UC_COMP):
                # grab info line
                info = lines[i+1]
                assert info[:4] == 'POS:'
                nums = [x.strip() for x in info[4:].split(',')]
                # extract fields
                name = line[len(UC_COMP):].strip(' "\n')
                pos = numpy.array([float(x) for x in nums[:3]])
                # read flat 3x3 rotation matrix
                rot = numpy.array([float(x) for x in nums[3:3+9]]).reshape(3, 3)
                comps[name] = (pos, rot)
    
            # switch perspective
            elif line.startswith(MC_COMP):
                color += 1
                comp = comps[line[len(MC_COMP) + 1:]]
    
            elif line.startswith(MC_COMP_SHORT):
                name = line[len(MC_COMP_SHORT) + 1:].strip('"')
                comp = comps[name]
                skip = True
    
            # process multiline
            elif line.startswith(MC_LINE):
                points = self.parse_multiline(line[len(MC_LINE):].strip('()'))
                points.pop(0)
                coords = self.rotate_points(points, comp)
                beg = multi_pid
                for p in coords:
                    multiPoints.InsertNextPoint(p)
                    multi_pid += 1
                end = multi_pid
                for idx in range(beg, end-1):
                    vline = vtk.vtkLine()
                    vline.GetPointIds().SetId(0,idx)
                    vline.GetPointIds().SetId(1,idx +1)
                    multiLines.InsertNextCell(vline)
                    
            # process circle
            elif line.startswith(MC_CIRCLE):
                xyz = 'xyz'
                items = line[len(MC_CIRCLE):].strip('()').split(',')
                # plane
                pla = [xyz.find(a) for a in items[0].strip("''")]
                # center and radius
                pos = [float(x) for x in items[1:4]]
                rad = float(items[4])
                coords = self.draw_circle(pla, pos, rad, comp)
                beg = circle_pid
                for p in coords:
                    circlePoints.InsertNextPoint(p)
                    circle_pid += 1
                end = circle_pid
                for idx in range(beg, end-1):
                    vline = vtk.vtkLine()
                    vline.GetPointIds().SetId(0,idx)
                    vline.GetPointIds().SetId(1,idx +1)
                    circleLines.InsertNextCell(vline)
            
                    
            # activate neutron when it enters
            elif line.startswith(MC_ENTER):
                prev = None
                skip = True
                active = True
                color = 0
                xstate=[]
                ystate=[]
                zstate=[]
            # deactivate neutron when it leaves
            elif line.startswith(MC_LEAVE):
                
                coords = numpy.column_stack([xstate, ystate, zstate])
                beg = neutron_pid
                for p in coords:
                    neutronPoints.InsertNextPoint(p)
                    neutron_pid += 1
                end = neutron_pid
                for idx in range(beg, end-1):
                    vline = vtk.vtkLine()
                    vline.GetPointIds().SetId(0,idx)
                    vline.GetPointIds().SetId(1,idx +1)
                    neutronLines.InsertNextCell(vline)
                active = False
                prev = None
                
            elif line.startswith(MC_ABSORB):
                pass
    
            # register state and scatter
            elif line.startswith(MC_STATE) or line.startswith(MC_SCATTER):
                
                if not active:
                    continue
    
                if skip:
                    skip = False
                    continue
                
                xyz = [float(x) for x in line[line.find(':')+1:].split(',')[:3]]
                xyz = self.rotate(xyz, comp)
                if prev is not None:
                    xstate.append(xyz[0])
                    ystate.append(xyz[1])
                    zstate.append(xyz[2])
                prev = xyz
                xstate.append(prev[0])
                ystate.append(prev[1])
                zstate.append(prev[2])
    
        circlePolydata =vtk.vtkPolyData()
        circlePolydata.SetPoints(circlePoints)
        circlePolydata.SetLines(circleLines)
    
        circle_mapper = vtk.vtkPolyDataMapper()
        circle_mapper.SetInput(circlePolydata)
        circle_actor = vtk.vtkActor()
        circle_actor.SetMapper(circle_mapper)
        circle_actor.GetProperty().SetAmbient(0.2)
        circle_actor.GetProperty().SetDiffuse(0.5)
        circle_actor.GetProperty().SetSpecular(0.3)
        circle_actor.GetProperty().SetColor(0,0.7,0.7)
        circle_actor.GetProperty().SetLineWidth(3)   
        
        
        multiPolydata =vtk.vtkPolyData()
        multiPolydata.SetPoints(multiPoints)
        multiPolydata.SetLines(multiLines)
    
        multi_mapper = vtk.vtkPolyDataMapper()
        multi_mapper.SetInput(multiPolydata)
        multi_actor = vtk.vtkActor()
        multi_actor.SetMapper(multi_mapper)
        multi_actor.GetProperty().SetAmbient(0.2)
        multi_actor.GetProperty().SetDiffuse(0.5)
        multi_actor.GetProperty().SetSpecular(0.3)
        multi_actor.GetProperty().SetColor(1,0,0.5)
        multi_actor.GetProperty().SetLineWidth(3)
        
        neutronPolydata =vtk.vtkPolyData()
        neutronPolydata.SetPoints(neutronPoints)
        neutronPolydata.SetLines(neutronLines)
    
        neutron_mapper = vtk.vtkPolyDataMapper()
        neutron_mapper.SetInput(neutronPolydata)
        neutron_actor = vtk.vtkActor()
        neutron_actor.SetMapper(neutron_mapper)
        neutron_actor.GetProperty().SetAmbient(0.2)
        neutron_actor.GetProperty().SetDiffuse(0.5)
        neutron_actor.GetProperty().SetSpecular(0.3)
        neutron_actor.GetProperty().SetColor(1,1,1)
        neutron_actor.GetProperty().SetLineWidth(2) 
        
        self._renderer.AddActor(circle_actor)
        self._renderer.AddActor(multi_actor)
        self._renderer.AddActor(neutron_actor)
        self._renderer.SetBackground(0, 0, 0)
        
        self._iren.Render()

    def parse_multiline(self,line):
        ''' 
        Parse a multiline with size as first elements and n points as rest 
        '''
        
        elems = [float(x) for x in line.split(',')]
        count = int(elems.pop(0))
        points = []
        while count > 0:
            points.append(elems[0:3])
            elems = elems[3:]
            count -= 1
    
        points.append(points[0])
        return points

    def rotate(self, point, (origin, rotm)):
        ''' 
        Rotate and move v according to origin and rotation matrix 
        '''
        return numpy.dot(point, rotm) + origin

    def rotate_points(self, points, (origin, rotm)):
        ''' 
        Rotate and move v according to origin and rotation matrix 
        '''
        
        count = 0
        rpoints=[]
        x=[]
        y=[]
        z=[]
        while count < len(points):
            p=points[count]
            rpoints.append(self.rotate(p, (origin, rotm)))
            p=rpoints[count]
            x.append(p[0])
            y.append(p[1])
            z.append(p[2])
            count +=1
        x.append(x[0]);
        y.append(y[0]);
        z.append(z[0]);
        return numpy.column_stack([x,y,z])

    def draw_circle(self, plane, pos, radius, comp):
        ''' 
        Draw a circle in plane, at pos and with r radius, rotated by comp 
        '''
        x=[]
        y=[]
        z=[]
        for i in xrange(0, POINTS_IN_CIRCLE):
            walk = 2 * numpy.pi * i / POINTS_IN_CIRCLE
            xyz = numpy.array(pos)
            xyz[plane[0]] += numpy.cos(walk) * radius
            xyz[plane[1]] += numpy.sin(walk) * radius
            # rotate
            xyz = self.rotate(xyz, comp)
            x.append(xyz[0])
            y.append(xyz[1])
            z.append(xyz[2])
        x.append(x[0]);
        y.append(y[0]);
        z.append(z[0]); 
        return numpy.column_stack([x,y,z])
    
REGISTRY["mvi_viewer"] = MviViewerPlugin
