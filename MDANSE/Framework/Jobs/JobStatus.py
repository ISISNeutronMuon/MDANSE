import collections
import cPickle
import datetime
import os

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

        self.cleanup()
                    
    @property
    def state(self):
        
        return self._state    

    def cleanup(self):
                        
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
        self._state['eta'] = self.eta
        self._state['progress'] = 100*self.currentStep/self.nSteps
        
        self.save_status()
        
