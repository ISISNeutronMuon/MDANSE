class IFormat(object):
    '''
    This is the base class for writing MDANSE output data. In MDANSE, the output of an analysis can be written in different file format.
    
    Currently, MDANSE supports NetCDF, SVG and ASCII output file formats. To introduce a new file output file format, just create a new concrete 
    subclass of IFormat and overload the "write" class method as defined in IFormat base class which will actually write the output variables, 
    and redefine the "type", "extension" and "extensions" class attributes.
    '''
        
    _registry = "format"

    @classmethod    
    def write(cls, filename, data, header=""):
        '''
        Write a set of output variables into filename using a given file format.
        
        :param filename: the path to the output file.
        :type filename: str
        :param data: the data to be written out.
        :type data: dict of Framework.OutputVariables.IOutputVariable
        :param header: the header to add to the output file.
        :type header: str
        '''
        
        pass
