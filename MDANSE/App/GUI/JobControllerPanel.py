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

@author: pellegrini
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
from MDANSE.Framework.Status import convert_duration, total_seconds
from MDANSE.Framework.Jobs.JobStatus import JobState
from MDANSE.Externals.pubsub import pub
from MDANSE.Logging.Logger import LOGGER

from MDANSE.App.GUI.Icons import ICONS, scaled_bitmap
from MDANSE.App.GUI.Events.JobControllerEvent import EVT_JOB_CONTROLLER, JobControllerEvent
        
class JobController(threading.Thread):
    
    __metaclass__ = Singleton
    
    def __init__(self, window, start=False):
        
        threading.Thread.__init__(self)
        
        self._window = window
        
        self._stop = threading.Event()
                                
        self._registry = collections.OrderedDict()
        
        if start:
            self.start()
        
    @property
    def registry(self):
        
        return self._registry

    def remove_job(self, job):
        
        try:
            del self._registry[job]
        except KeyError:
            pass    

    def run(self):
        
        while not self._stop.is_set():
            self.update()
            self._stop.wait(10.0)

    def stop(self):
        
        self._stop.set()
        
    def update(self):
                        
        pids = PLATFORM.get_processes_info()
                        
        # The list of the registered jobs.
        jobs = [f for f in glob.glob(os.path.join(PLATFORM.temporary_files_directory(),'*'))]
                                   
        # Loop over the job registered at the previous controller check point     
        for j in self._registry.keys():
            # Case where a job has finished during two controller check points (i.e. its temporary file has been deleted)
            
            if self._registry[j]['state'] == 'finished':
                continue
            
            if not j in jobs:
                self._registry[j]['eta'] = 'N/A'
                self._registry[j]['progress'] = 100
                self._registry[j]['state'] = 'finished'
                start = datetime.datetime.strptime(self._registry[j]["start"],"%d-%m-%Y %H:%M:%S")
                self._registry[j]['elapsed'] = '%02d:%02dh:%02dm:%02ds' % convert_duration(total_seconds(datetime.datetime.today() - start))
        
        # Loop over the job whose temporary files are still present
        for j in jobs:

            # Open the job temporary file
            try:
                f = open(j, 'rb')
                info = cPickle.load(f)
                f.close()
                
            # If the file could not be opened/unpickled for whatever reason, try at the next checkpoint
            except:
                continue

            # The job file could be opened and unpickled properly
            else:
                # Check that the unpickled object is a JobStatus object
                if not isinstance(info,JobState):
                    continue
                
                # Check that the pid of the running job corresponds to an active pid.
                running = (info['pid'] in pids)
                
                # If so, check that the corresponding pid actually corresponds to the job by comparing 
                # the job starting date and the pid creation date.
                if running:
                    jobStartingTime = datetime.datetime.strptime(info["start"],"%d-%m-%Y %H:%M:%S")
                    procStartingTime = datetime.datetime.strptime(pids[info['pid']],"%d-%m-%Y %H:%M:%S")
                    running = (jobStartingTime >= procStartingTime)
                                                    
                # Case where the job is running, update the registry with the new status    
                if running:
                    self._registry[j] = info
                    
                # Case where the job is not running 
                else:
                    info['state'] = 'aborted'
                    self._registry[j] = info          

        wx.PostEvent(self._window, JobControllerEvent(self._registry))
                                              
class JobControllerPanel(wx.ScrolledWindow):
    
    columns = [("name",(150,-1)),("pid",(60,-1)),("start",(150,-1)),("elapsed",(150,-1)),("state",(100,-1)),("progress",(-1,-1)),("eta",(120,-1)),("kill",(50,-1))]
    
    def __init__(self, parent):
        
        wx.ScrolledWindow.__init__(self, parent, id = wx.ID_ANY)

        self.SetScrollbars(pixelsPerUnitX=1, pixelsPerUnitY=1, noUnitsX=50, noUnitsY=50)
        
        self.parent = parent
                        
        self._jobs = collections.OrderedDict()
        
        self.build_panel()

        EVT_JOB_CONTROLLER(self,self.on_update)
        
        pub.subscribe(self.on_start_job,"on_start_job")

        self._jobsController = JobController(self,True)

    def __del__(self):

        self._jobsController.stop()
        while self._jobsController.is_alive():
            time.sleep(0.01)
            
    def on_start_job(self,message):
                
        self._jobsController.update()
        

    def add_job(self, name, jobStatus):
                        
        r = self._gbSizer.Rows
        self._jobs[name] = r

        name = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_READONLY|wx.ALIGN_CENTER_HORIZONTAL)
        pid = intctrl.IntCtrl(self, wx.ID_ANY, style=wx.TE_READONLY|wx.ALIGN_CENTER_HORIZONTAL)
        start = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_READONLY|wx.ALIGN_CENTER_HORIZONTAL)
        elapsed = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_READONLY|wx.ALIGN_CENTER_HORIZONTAL)
        state = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_READONLY|wx.ALIGN_CENTER_HORIZONTAL)
        progress = wx.Gauge(self, wx.ID_ANY,range=100)
        eta = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_READONLY|wx.ALIGN_CENTER_HORIZONTAL)
        kill = wx.BitmapButton(self, wx.ID_ANY, scaled_bitmap(ICONS["stop"], 24, 24))

        self._gbSizer.Add(name    ,pos=(r,0),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        self._gbSizer.Add(pid     ,pos=(r,1),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        self._gbSizer.Add(start   ,pos=(r,2),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        self._gbSizer.Add(elapsed ,pos=(r,3),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        self._gbSizer.Add(state   ,pos=(r,4),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        self._gbSizer.Add(progress,pos=(r,5),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        self._gbSizer.Add(eta     ,pos=(r,6),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        self._gbSizer.Add(kill    ,pos=(r,7),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
                                
        self._gbSizer.Layout()

        kill.Bind(wx.EVT_BUTTON, self.on_kill_job)
                        
    def build_panel(self):
        
        self._gbSizer = wx.GridBagSizer(0,0)
        
        for i,(col,s) in enumerate(self.columns):
            self._gbSizer.Add(wx.TextCtrl(self,wx.ID_ANY,value=col.upper(),size=s,style=wx.TE_READONLY|wx.ALIGN_CENTER_HORIZONTAL),pos=(0,i),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)

        self._gbSizer.AddGrowableCol(5)
                
        self.SetSizer(self._gbSizer)

    def on_kill_job(self, event):
        
        row = self._gbSizer.GetItemPosition(event.GetEventObject())[0]
        state = self._gbSizer.FindItemAtPosition((row,4)).Window.GetValue()
        
        if state == "finished":
            return
            
        for row in range(self._gbSizer.GetCols()):
            name = self._gbSizer.FindItemAtPosition((row,0)).Window.GetValue()

        d = wx.MessageDialog(None, 'Do you really want to kill job %r ?' % name, 'Question', wx.YES_NO|wx.YES_DEFAULT|wx.ICON_EXCLAMATION)
        if d.ShowModal() == wx.ID_YES:
            try:
                pid = self._gbSizer.FindItemAtPosition((row,1)).Window.GetValue()
                PLATFORM.kill_process(pid)
            except Exception:
                LOGGER("The job %r could not be killed." % name,"error")
            else:            
                event.GetEventObject().Disable()   
                

    def update_job(self,name,jobStatus):
        
        r = self._jobs[name]
                
        for i,(name,_) in enumerate(self.columns):
            try:
                self._gbSizer.FindItemAtPosition((r,i)).Window.SetValue(jobStatus[name])
                
                if jobStatus['state'] == 'finished':
                    self._gbSizer.FindItemAtPosition((r,7)).Window.Disable()
                
            except AttributeError:
                pass
        
        info =  "\n".join(["%s = %s" % (k,v) for k,v in jobStatus.items()])
        self._gbSizer.FindItemAtPosition((r,0)).Window.SetToolTipString(info)
        
    def on_update(self, event):
                                        
        registry = event.registry
                                
        for name,jobStatus in registry.items():
                        
            if not self._jobs.has_key(name):
                if jobStatus["state"] == "aborted":
                    continue
                self.add_job(name,jobStatus)
            self.update_job(name,jobStatus)
                        
if __name__ == "__main__":
        
    app = wx.App(0)
    frame = wx.Frame(None, -1, "Job Controller")
     
    JobController = JobControllerPanel(frame)
     
    frame.Show(True)
    app.MainLoop()
    
    
    
    