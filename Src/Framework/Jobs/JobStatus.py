# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/JobStatus.py
# @brief     Implements module/class/test JobStatus
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import cPickle
import datetime
import os
import threading
import time

from MDANSE import PLATFORM
from MDANSE.Framework.Status import Status

class JobState(collections.OrderedDict):
    pass

class JobStatus(Status):
         
    def __init__(self, job):

        Status.__init__(self)
                                 
        self._state = JobState()
        self._state['pid'] = PLATFORM.pid() 
        self._state['type'] = job.__class__.__name__
        self._state['start'] = datetime.datetime.strftime(datetime.datetime.today(),"%d-%m-%Y %H:%M:%S")
        self._state['elapsed'] = "N/A"
        self._state['eta'] = "N/A"
        self._state['current_step'] = 0 
        self._state['n_steps'] = 0 
        self._state['progress'] = 0 
        self._state['state'] = "running"
        self._state['name'] = job.name
        self._state['traceback'] = ''
        self._state['temporary_file'] = os.path.join(PLATFORM.temporary_files_directory(), self._state['name'])
        self._state['info'] = ''
        
        self.save_status()
                    
    def finish_status(self):
        # Launch a thread that will wait before erasing the file
        t= threading.Thread(target = self.cleanup)
        t.start()
                    
    @property
    def state(self):
        
        return self._state    

    def cleanup(self):
        # Wait before cleaning
        time.sleep(PLATFORM.jobs_launch_delay())
        try:
            os.unlink(self._state['temporary_file'])
        except:
            pass
                 
    def start_status(self):
                        
        self._state["n_steps"] = self.nSteps

        self.save_status()
                                
    def save_status(self):

        with open(self._state['temporary_file'], 'wb') as f:
            cPickle.dump(self._state, f, protocol=2)

    def stop_status(self):
        pass
                    
    def update_status(self):
        
        self._state['elapsed'] = self.elapsedTime
        self._state['current_step'] = self.currentStep
        if self._nSteps is not None:
            self._state['eta'] = self.eta
            self._state['progress'] = 100*self.currentStep/self.nSteps
        else:
            self._eta = "N/A"
            self._state['progress'] = 0
        
        self.save_status()
        
