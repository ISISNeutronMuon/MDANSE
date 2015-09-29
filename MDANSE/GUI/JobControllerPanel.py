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
Created on Apr 10, 2015

:author: Gael Goret and Eric C. Pellegrini
'''

import collections
import cPickle
import datetime
import glob
import os
import threading
import time

import wx
import wx.lib.intctrl as intctrl

from MDANSE.Core.Platform import PLATFORM
from MDANSE.Core.Singleton import Singleton
from MDANSE.Externals.pubsub import pub
from MDANSE.Framework.Status import convert_duration, total_seconds
from MDANSE.GUI.Icons import ICONS
from MDANSE.GUI.Events.JobControllerEvent import EVT_JOB_CONTROLLER, JobControllerEvent
        
class JobController(threading.Thread):
    
    __metaclass__ = Singleton
    
    def __init__(self, window, start=False):
        
        threading.Thread.__init__(self)
        
        self._window = window
        
        self._stop = threading.Event()
                                
        self._registry = collections.OrderedDict()
        
        self._firstCheck = True
        
        self._init = True
        
        if start:
            self.start()
        
    @property
    def registry(self):
        
        return self._registry

    def kill_job(self, info):
                
        if self._registry.has_key(info["name"]):

            if info['state'] == 'running':
                try:
                    PLATFORM.kill_process(info['pid'])
                except:
                    pass

            del self._registry[info["name"]]

        if os.path.exists(info['temporary_file']):            
            try:
                os.unlink(info['temporary_file'])
            except:
                pass

        self.update()
        
    def run(self):
        
        while not self._stop.is_set():
            self.update()
            self._stop.wait(10.0)

    def stop(self):
        
        self._stop.set()
        
    def update(self, init=False):
                        
        pids = PLATFORM.get_processes_info()
                        
        # The list of the registered jobs.
        jobs = [f for f in glob.glob(os.path.join(PLATFORM.temporary_files_directory(),'*'))]
                        
        # Loop over the job registered at the previous controller check point     
        for job in self._registry.keys():            

            # Case where a job has finished during two controller check points (i.e. its temporary file has been deleted)
            if self._registry[job]['state'] == 'finished':
                del self._registry[job]
                continue
            
            # Case where the jobs has finished properly (e.g. its temporary file has been removed)
            if not job in jobs:
                self._registry[job]['eta'] = 'N/A'
                self._registry[job]['progress'] = 100
                self._registry[job]['state'] = 'finished'
                start = datetime.datetime.strptime(self._registry[job]["start"],"%d-%m-%Y %H:%M:%S")
                self._registry[job]['elapsed'] = '%02d:%02dh:%02dm:%02ds' % convert_duration(total_seconds(datetime.datetime.today() - start))
                
        # Loop over the job whose temporary files are still present
        for job in jobs:

            # Open the job temporary file
            try:
                f = open(job, 'rb')
                info = cPickle.load(f)
                f.close()
                
            # If the file could not be opened/unpickled for whatever reason, try at the next checkpoint
            except:
                continue

            # The job file could be opened and unpickled properly
            else:
                
                name = info['name']
                                
                # Check that the pid of the running job corresponds to an active pid.
                running = (info['pid'] in pids)
                                
                # If so, check that the corresponding pid actually corresponds to the job by comparing 
                # the job starting date and the pid creation date.
                if running:
                    jobStartingTime = datetime.datetime.strptime(info["start"],"%d-%m-%Y %H:%M:%S")
                    procStartingTime = datetime.datetime.strptime(pids[info['pid']],"%d-%m-%Y %H:%M:%S")
                    running = (jobStartingTime >= procStartingTime)
                    
                if not running:
                    info["state"] = "aborted"
                    
                # If the job was aborted, display the traceback on the dialog logger and remove the corresponding job temporary file
                if self._init and info['state'] == 'aborted':
                    self.kill_job(info)
                    self._init = False
                    continue

                self._registry[name] = info
                
        wx.PostEvent(self._window, JobControllerEvent(self._registry))
                                              
class JobControllerPanel(wx.ScrolledWindow):
    
    columns = [("name",(150,-1)),("pid",(60,-1)),("start",(150,-1)),("elapsed",(150,-1)),("state",(100,-1)),("progress",(-1,-1)),("eta",(120,-1)),("kill",(50,-1))]
    
    def __init__(self, parent):
        
        wx.ScrolledWindow.__init__(self, parent, id = wx.ID_ANY)

        self.SetScrollbars(pixelsPerUnitX=1, pixelsPerUnitY=1, noUnitsX=50, noUnitsY=50)
        
        self.parent = parent
                                
        self._gbSizer = wx.GridBagSizer(0,0)
                        
        self.SetSizer(self._gbSizer)

        self._jobsController = JobController(self,True)

        EVT_JOB_CONTROLLER(self,self.on_update)
        
        pub.subscribe(self.msg_start_job,"msg_start_job")

    def __del__(self):

        self._jobsController.stop()
        while self._jobsController.is_alive():
            time.sleep(0.01)
            
    def msg_start_job(self,message):
                
        self._jobsController.update()

    def add_job(self, name, jobStatus):
                        
        name = wx.Button(self, wx.ID_ANY, style=wx.BU_EXACTFIT,label=jobStatus['name'])
        if jobStatus["state"] == "aborted":
            name.SetBackgroundColour(wx.RED)
        pid = intctrl.IntCtrl(self, wx.ID_ANY, style=wx.TE_READONLY|wx.ALIGN_CENTER_HORIZONTAL,value=jobStatus['pid'])
        start = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_READONLY|wx.ALIGN_CENTER_HORIZONTAL,value=jobStatus['start'])
        elapsed = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_READONLY|wx.ALIGN_CENTER_HORIZONTAL,value=jobStatus['elapsed'])
        state = wx.Button(self, wx.ID_ANY, style=wx.BU_EXACTFIT,label=jobStatus['state'])
        progress = wx.Gauge(self, wx.ID_ANY,range=100)
        progress.SetValue(jobStatus['progress'])
        eta = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_READONLY|wx.ALIGN_CENTER_HORIZONTAL,value=jobStatus['eta'])
        kill = wx.BitmapButton(self, wx.ID_ANY, ICONS["stop",16,16])
        

        r = self._gbSizer.GetRows()

        self._gbSizer.Add(name    ,pos=(r,0),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        self._gbSizer.Add(pid     ,pos=(r,1),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        self._gbSizer.Add(start   ,pos=(r,2),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        self._gbSizer.Add(elapsed ,pos=(r,3),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        self._gbSizer.Add(state   ,pos=(r,4),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        self._gbSizer.Add(progress,pos=(r,5),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        self._gbSizer.Add(eta     ,pos=(r,6),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        self._gbSizer.Add(kill    ,pos=(r,7),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)

        self._gbSizer.Layout()

        self.Bind(wx.EVT_BUTTON,self.on_display_info,name)
        self.Bind(wx.EVT_BUTTON,self.on_display_traceback,state)
        self.Bind(wx.EVT_BUTTON, self.on_kill_job,kill)

    def on_display_info(self,event):
        
        row = self._gbSizer.GetItemPosition(event.GetEventObject())[0]
        name = self._gbSizer.FindItemAtPosition((row,0)).Window.GetLabel() 

        f = wx.Frame(self,size=(800,500))
                
        panel = wx.Panel(f,wx.ID_ANY)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        info = self._jobsController.registry[name]['info'].strip()
        if not info:
            info = "No information available about %r job." % name
        
        self._info = wx.TextCtrl(panel,wx.ID_ANY,style=wx.TE_AUTO_SCROLL|wx.TE_READONLY|wx.TE_MULTILINE)
        self._info.SetValue(info)
        
        sizer.Add(self._info,1,wx.ALL|wx.EXPAND,5)
        
        panel.SetSizer(sizer)
        
        f.Show()

    def on_display_traceback(self,event):
        
        row = self._gbSizer.GetItemPosition(event.GetEventObject())[0]
        name = self._gbSizer.FindItemAtPosition((row,0)).Window.GetLabel() 

        f = wx.Frame(self,size=(800,500))
                
        panel = wx.Panel(f,wx.ID_ANY)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        tb = self._jobsController.registry[name]['traceback'].strip()
        if not tb:
            tb = "No traceback available about %r job." % name
        
        self._tb = wx.TextCtrl(panel,wx.ID_ANY,style=wx.TE_AUTO_SCROLL|wx.TE_READONLY|wx.TE_MULTILINE)
        self._tb.SetValue(tb)
        
        sizer.Add(self._tb,1,wx.ALL|wx.EXPAND,5)
        
        panel.SetSizer(sizer)
        
        f.Show()
                                    
    def on_kill_job(self, event):
                
        row = self._gbSizer.GetItemPosition(event.GetEventObject())[0]
        name = self._gbSizer.FindItemAtPosition((row,0)).Window.GetLabel() 

        d = wx.MessageDialog(None, 'Do you really want to kill job %r ?' % name, 'Question', wx.YES_NO|wx.YES_DEFAULT|wx.ICON_EXCLAMATION)
        if d.ShowModal() == wx.ID_YES:
            self._jobsController.kill_job(self._jobsController.registry[name])
                        
    def on_update(self, event):
                                        
        registry = event.registry

        self._gbSizer.Clear(True)

        for i,(col,s) in enumerate(self.columns):
            self._gbSizer.Add(wx.TextCtrl(self,wx.ID_ANY,value=col.upper(),size=s,style=wx.TE_READONLY|wx.ALIGN_CENTER_HORIZONTAL),pos=(0,i),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)

        self._gbSizer.AddGrowableCol(5)
                                 
        self._gbSizer.Layout()
                                                
        for name,jobStatus in registry.items():                         
            self.add_job(name,jobStatus)
                                                                            
if __name__ == "__main__":
        
    app = wx.App(0)
    frame = wx.Frame(None, -1, "Job Controller")
     
    JobController = JobControllerPanel(frame)
     
    frame.Show(True)
    app.MainLoop()
    
    
    
    