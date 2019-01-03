import os
import StringIO
import tarfile

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.Formats.IFormat import IFormat

class ASCIIFormat(IFormat):
    '''
    This class handles the writing of output variables in ASCII format. Each output variable is written into separate ASCII files which are further
    added to a single archive file. 
    '''
    
    extension = ".dat"

    extensions = ['.dat','.txt']
    
    @classmethod
    def write(cls, filename, data, header=""):
        '''
        Write a set of output variables into a set of ASCII files.
        
        Each output variable will be output in a separate ASCII file. All the ASCII files will be compressed into a tar file.
        
        :param filename: the path to the output archive file that will contain the ASCII files written for each output variable.
        :type filename: str
        :param data: the data to be written out.
        :type data: dict of Framework.OutputVariables.IOutputVariable
        :param header: the header to add to the output file.
        :type header: str
        '''
                
        filename = os.path.splitext(filename)[0]
        filename = "%s.tar" % filename

        tf = tarfile.open(filename,'w')
        
        for var in data.values():

            tempStr = StringIO.StringIO()
            tempStr.write(var.info())
            tempStr.write('\n\n')            
            cls.write_array(tempStr,var)
            tempStr.seek(0)

            info = tarfile.TarInfo(name='%s%s' % (var.name,cls.extensions[0]))
            info.size=tempStr.len
            tf.addfile(tarinfo=info, fileobj=tempStr)
            
        if header:
            tempStr = StringIO.StringIO()
            tempStr.write(header)
            tempStr.write('\n\n')  
            tempStr.seek(0)
            info = tarfile.TarInfo(name='jobinfo.txt')
            info.size=tempStr.len
            tf.addfile(tarinfo=info, fileobj=tempStr)
                                    
        tf.close()

    @classmethod
    def write_array(cls, fileobject, array, slices=None):
        '''
        Write an Framework.OutputVariables.IOutputVariable into a file-like object
        
        :param fileobject: the file object where the output variable should be written.
        :type fileobject: python file-like object
        :param array: the output variable to write (subclass of NumPy array).
        :type array: Framework.OutputVariables.IOutputVariable
        :param slices: the slices of the output variable to write. If None, the whole output variable will be written.
        :type: python slice
        
        :attention: this is a recursive method.
        '''
        
        if slices is None:
            slices = [0]*array.ndim
            slices[-2:] = array.shape[-2:]

        if array.ndim > 2:
        
            for a in array:
                cls.write_array(fileobject,a, slices)
                slices[len(slices)-array.ndim] = slices[len(slices)-array.ndim] + 1

        else:
            fileobject.write('#slice:%s\n' % slices)
            numpy.savetxt(fileobject, array)
            fileobject.write('\n')

REGISTRY['ascii'] = ASCIIFormat
