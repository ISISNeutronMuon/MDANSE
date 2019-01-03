import abc
import os

from MDANSE.Framework.InputData.IInputData import IInputData

class InputFileData(IInputData):
        
    def __init__(self, filename, load=True):
                
        IInputData.__init__(self,filename)
                
        self._basename = os.path.basename(filename)
        self._dirname = os.path.dirname(filename)
    
        if load:    
            self.load()

    @property
    def filename(self):
        '''
        Returns the filename associated with the input data.
        
        :return: the filename associated with the input data.
        :rtype: str
        '''
        
        return self._name

    @property
    def shortname(self):
        '''
        Returns the shortname of the file associated with the input data.
        
        :return: the shortname of the file associated with the input data.
        :rtype: str
        '''

        return self._basename    

    @property
    def basename(self):
        '''
        Returns the basename of the file associated with the input data.
        
        :return: the basename of the file associated with the input data.
        :rtype: str
        '''

        return self._basename    
        
    @property
    def dirname(self):
        return self._dirname    

    @abc.abstractmethod
    def load(self):
        pass   

    @abc.abstractmethod
    def close(self):
        pass    
