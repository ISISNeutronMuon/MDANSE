# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/JobStatus.py
# @brief     Implements module/class/test JobStatus
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import datetime

import zmq

from MDANSE import PLATFORM
from MDANSE.Framework.Status import Status

class JobStatus(Status):
         
    def __init__(self, job):

        Status.__init__(self)
                                 
        self._state = {}
        self._state['pid'] = PLATFORM.pid() 
        self._state['type'] = job.__class__.__name__
        self._state['start'] = datetime.datetime.strftime(datetime.datetime.today(),"%d-%m-%Y %H:%M:%S")
        self._state['elapsed'] = "N/A"
        self._state['eta'] = "N/A"
        self._state['current_step'] = 0 
        self._state['n_steps'] = 0 
        self._state['progress'] = 0 
        self._state['state'] = "setup"
        self._state['name'] = job.name
        self._state['traceback'] = ''
        self._state['info'] = ''

        self._context = zmq.Context()

        self._server = self._context.socket(zmq.PUB)
        self._server.connect("tcp://127.0.0.1:6789")
                                        
    @property
    def state(self):
        
        return self._state    

    def send_status(self):

        self._server.send_pyobj(self._state,protocol=2)
      
    def start_status(self):
                        
        self._state["n_steps"] = self.nSteps
        self._state['state'] = "running"

        self.send_status()

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
        
        self.send_status()
        
        
