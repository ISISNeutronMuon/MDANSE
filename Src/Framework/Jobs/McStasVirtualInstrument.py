# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/McStasVirtualInstrument.py
# @brief     Implements module/class/test McStasVirtualInstrument
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import os
import shutil
import subprocess
import tempfile
import string
import StringIO

import numpy

from MMTK import Units

from MDANSE import ELEMENTS, REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms

MCSTAS_UNITS_LUT = {'THz': measure(1,"THz",equivalent=True).toval("meV"), 
                    'nm2' : measure(1,"nm2").toval("b"),
                    '1/nm' : measure(1,"1/nm").toval("1/ang")
                    } 

class McStasError(Error):
    pass

class McStasVirtualInstrument(IJob):
    """
    Performs a virtual neutron scattering experiment using a binding to the McStas, neutron ray-tracing code.
	
	This analysis requires the coherent and incoherent dynamic structure factors to have been calculated
	and an instrument to be chosen.
	The result is the instrument-dependent perturbation of the sum of the scattering contributions including 
	instrument resolution, self-shielding and multiple scattering.
    """
        
    label = "McStas Virtual Instrument"

    category = ('Analysis','Virtual Instruments',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]
    
    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory', {'default':os.path.join('..','..','..','Data','Trajectories', 'MMTK', 'protein_in_periodic_universe.nc')})
    settings['frames'] = ('frames', {"dependencies":{'trajectory':'trajectory'}})
    settings['sample_coh'] = ('netcdf_input_file', {"widget":'input_file',
                                                    "label":'MDANSE Coherent Structure Factor',
                                                    "variables":['q','frequency','s(q,f)_total'],
                                                    'default' : os.path.join('..','..','..','Data','NetCDF','dcsf_prot.nc')})
    settings['sample_inc'] = ('netcdf_input_file', {"widget":'input_file',
                                                    "label":'MDANSE Incoherent Structure Factor',
                                                    "variables" :['q','frequency','s(q,f)_total'],
                                                    'default':os.path.join('..','..','..','Data','NetCDF','disf_prot.nc')})
    settings['temperature'] = ('float', {"default":298.0})
    settings['display'] = ('boolean', {'label':'trace the 3D view of the simulation'})
    settings['instrument'] = ('mcstas_instrument',{"label":'mcstas instrument','default' : os.path.join('..','..','..','Data','McStas','Instruments','Simple_ToF_Flat_Sample.out')})
    settings['options'] = ('mcstas_options', {'label':'mcstas options'})
    settings['parameters'] = ('mcstas_parameters', {'label':'instrument parameters',
                                                    'dependencies':{'instrument':'instrument'},
                                                    'exclude':['sample_coh','sample_inc']}) 
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        # The number of steps is set to 1 as the job is defined as single McStas run.            
        self.numberOfSteps = 1
        
        symbols = sorted_atoms(self.configuration['trajectory']['instance'].universe,"symbol")

        # Compute some parameters used for a proper McStas run
        self._mcStasPhysicalParameters = {"density"   : 0.0}
        self._mcStasPhysicalParameters["weight"]    = sum([ELEMENTS[s,'atomic_weight'] for s in symbols])
        self._mcStasPhysicalParameters["sigma_abs"] = sum([ELEMENTS[s,'xs_absorption'] for s in symbols])*MCSTAS_UNITS_LUT['nm2']
        self._mcStasPhysicalParameters["sigma_coh"] = sum([ELEMENTS[s,'xs_coherent']   for s in symbols])*MCSTAS_UNITS_LUT['nm2']
        self._mcStasPhysicalParameters["sigma_inc"] = sum([ELEMENTS[s,'xs_incoherent'] for s in symbols])*MCSTAS_UNITS_LUT['nm2']
        for frameIndex in self.configuration['frames']['value']:
            self.configuration['trajectory']['instance'].universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)                
            cellVolume = self.configuration['trajectory']['instance'].universe.cellVolume()
            self._mcStasPhysicalParameters["density"] += self._mcStasPhysicalParameters["weight"]/cellVolume
        self._mcStasPhysicalParameters["density"] /= self.configuration['frames']['n_frames']
        # The density is converty in g/cm3
        self._mcStasPhysicalParameters["density"] /= (Units.Nav/Units.cm**3)
        
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
        """
        
        sqw = ['sample_coh', 'sample_inc']
        sqwInput = ''
        self.outFile = {}
        for typ in sqw:
                        
            fout = tempfile.NamedTemporaryFile(mode = 'w', delete=False)
                        
            fout.write('# Physical parameters:\n')
            for k,v in self._mcStasPhysicalParameters.items():
                fout.write("# %s %s \n" % (k,v))
            
            fout.write('# Temperature %s \n'%self.configuration['temperature']['value']) 
            fout.write('# classical 1 \n\n') 
            
            for var in self.configuration[typ].variables:
                fout.write("# %s\n" %var)
                
                data = self.configuration[typ][var][:]
                try:
                    data *= MCSTAS_UNITS_LUT[self.configuration[typ][var].units]
                except KeyError:
                    pass
                
                numpy.savetxt(fout, data)
                fout.write('\n')                
                
            fout.close()
            self.outFile[typ] = fout.name
            sqwInput += '%s=%s '%(typ,fout.name)
            
        trace = ''
        if self.configuration['display']['value']:
            trace = ' --trace '
        execPath = self.configuration['instrument']['value']
        options = self.configuration['options']['value']
        parameters = self.configuration['parameters']['value']
        
        cmdLine = [execPath]
        cmdLine.extend(options)
        cmdLine.append(sqwInput)
        cmdLine.append(trace)
        cmdLine.extend(parameters)
        
        s = subprocess.Popen(" ".join(cmdLine), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        out,_ = s.communicate()
        
        for line in out.splitlines():
            if "ERROR" in line:
                raise McStasError("An error occured during McStas run: %s" % out)
                
        with open(os.path.join(self.configuration["options"]["mcstas_output_directory"],"mcstas_mdanse.mvi"),"w") as f:
            f.write(out)
            
        return index, None

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """
        pass

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """
                
        # Rename and move to the result dir the SQW file input
        for typ, fname in self.outFile.items():
            shutil.move(fname, os.path.join(self.configuration["options"]["mcstas_output_directory"], typ + '.sqw'))
        
        # Convert McStas output files into NetCDF format
        self.convert(self.configuration["options"]["mcstas_output_directory"])
        
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
                
    def treat_str_var(self, s):
        return s.strip().replace(' ', '_')
    
    def unique(self, key, d, value = None):
        skey = key
        i = 0
        if value is not None:
            for k, v in d.items():
                if v.shape != value.shape:
                    continue
                if numpy.allclose(v, value):
                    return k
        while d.has_key(key):
            key = skey + '_%d'%i
            i += 1
        return key 
    
    def convert(self, sim_dir):
        """
        Convert McStas data set to netCDF File Format
        """
        
        typique_sim_fnames = ['mccode.sim', 'mcstas.sim']
        sim_file = ''
        for sim_fname in typique_sim_fnames:
            sim_file = os.path.join(sim_dir,sim_fname)
            if os.path.isfile(sim_file):
                break
        
        if not sim_file:
            raise Exception('Dataset ' + sim_file + ' does not exist!')

        isBegin = lambda line: line.strip().startswith('begin')
        isCompFilename = lambda line: line.strip().startswith('filename:')
        # First, determine if this is single or overview plot...
        SimFile = filter(isBegin, open(sim_file).readlines())
        Datfile = 0
        if SimFile == []:
            FS = self.read_monitor(sim_file)
            typ = FS['type'].split('(')[0].strip()
            if typ != 'multiarray_1d':
                FS=self.save_single(FS)
                exit()
                Datfile = 1
    
        # Get filenames from the sim file
        MonFiles = filter(isCompFilename, open(sim_file).readlines())
        L = len(MonFiles)
        FSlist = []
        # Scan or overview?
        if L==0:
            """Scan view"""
            if Datfile==0:
                isFilename = lambda line: line.strip().startswith('filename')
                
                Scanfile = filter(isFilename, open(sim_file).readlines())
                Scanfile = Scanfile[0].split(': ')
                Scanfile = os.path.join(sim_dir,Scanfile[1].strip())
                # Proceed to load scan datafile
                FS = self.read_monitor(Scanfile)
                L=(len(FS['variables'].split())-1)/2
                self.scan_flag = 1
                for j in range(0, L):
                    FSsingle = self.get_monitor(FS,j)
                    FSlist[len(FSlist):] = [FSsingle]
                    FSlist[j]=self.save_single(FSsingle)
                    self.scan_length = FSsingle['data'].shape[0]
        else:
            """Overview or single monitor"""
            for j in range(0, L):
                MonFile = MonFiles[j].split(':') 
                MonFile = MonFile[1].strip()
                MonFile = os.path.join(sim_dir,MonFile)
                FS=self.read_monitor(MonFile)
                FSlist[len(FSlist):] = [FS]
                FSlist[j]=self.save_single(FS)
    
    def save_single(self, FileStruct):
        """
        save a single 1D/2D data array with axis into a NetCDF file format.
          input:  FileStruct as obtained from read_monitor()
          output: FileStruct data structure
        """
        
        typ = FileStruct['type'].split('(')[0].strip()
    
        if typ == 'array_1d':
            # 1D data set
            Xmin = eval(FileStruct['xlimits'].split()[0])
            Xmax = eval(FileStruct['xlimits'].split()[1])
            x=FileStruct['data'][:,0]
            y=FileStruct['data'][:,1]

            Title = self.unique(self.treat_str_var(FileStruct['component']), self._outputData) 
            xlabel = self.unique(self.treat_str_var(FileStruct['xlabel']), self._outputData, x)
            
            self._outputData[xlabel] = REGISTRY["outputvariable"]("line", x, xlabel, units="au")
            self._outputData[Title] = REGISTRY["outputvariable"]("line",y , Title, axis="%s"%xlabel, units="au")                 
        
        elif typ == 'array_2d':
            # 2D data set
            mysize=FileStruct['data'].shape
            
            I=FileStruct['data']
            mysize=I.shape
            I = I.T

            Xmin = eval(FileStruct['xylimits'].split()[0])
            Xmax = eval(FileStruct['xylimits'].split()[1])
            Ymin = eval(FileStruct['xylimits'].split()[2])
            Ymax = eval(FileStruct['xylimits'].split()[3])
            
            x = numpy.linspace(Xmin,Xmax,mysize[1])
            y = numpy.linspace(Ymin,Ymax,mysize[0])

            title = self.unique(self.treat_str_var(FileStruct['component']), self._outputData)
            xlabel = self.unique(self.treat_str_var(FileStruct['xlabel']), self._outputData, x)
            ylabel = self.unique(self.treat_str_var(FileStruct['ylabel']), self._outputData, y)

            self._outputData.add(xlabel,'line', x, units="au")
            self._outputData.add(ylabel,'line', y, units="au")
            self._outputData.add(title,'surface', I, axis="%s|%s" % (xlabel, ylabel), units="au")                 

        return FileStruct
        
    def read_monitor(self, simFile):
        """
        Read a monitor file (McCode format).
        
        :param simFile: the path for the monitor file.
        :type simFile: str
        
        :return: a dictionary built from the evaluation of McStas monitor file header that will contains the data and metadata about the monitor.
        :rtype: dict
        """
        
        # Read header
        isHeader = lambda line: line.startswith('#')
        f = open(simFile)
        Lines= f.readlines()
        Header = filter(isHeader, Lines)
        f.close()
        
        # Traverse header and define corresponding 'struct'
        strStruct ="{"
        for j in range(0, len(Header)):
            # Field name and data
            Line = Header[j]; Line = Line[2:len(Line)].strip()
            Line = Line.split(':')
            Field = Line[0]
            Value = ""
            Value = string.join(string.join(Line[1:len(Line)], ':').split("'"), '')            
            strStruct = strStruct + "'" + Field + "':'" + Value + "'"
            if j<len(Header)-1:
                strStruct += ","
        strStruct = strStruct + "}"
        Filestruct = eval(strStruct)
        # Add the data block

        data = []
        f = open(simFile, 'r')
        lines = f.readlines()
        f.close()
        
        header = True
        for l in lines:
            if l.startswith('#'):
                if header:
                    continue
                else:
                    break
            else:
                if header:
                    header = False
                data.append(l)
        
        
        Filestruct['data'] = numpy.genfromtxt(StringIO.StringIO(' '.join(data)))
        Filestruct['fullpath'] = simFile
        
        return Filestruct

    def get_monitor(self, monitor, col):
        """
        Extract one of the monitor in scan steps called from: display
        
        :param monitor:  the dictionary that contains data and metadata about the monitor (obtained from `read_monitor`)
        :type monitor: dict
        :param col: index of the monitor column to extract.
        :type col: int
        :return: a dictionary that contains data and metadata about monitor `j`.
        :rtype: dict
        """
        
        # Ugly, hard-coded...
        data=monitor['data'][:,(0,2*col+1,2*col+2)]
        variables=monitor['variables'].split()   
        FSsingle={'xlimits':monitor['xlimits'],
                  'data':data,'component':variables[col+1],
                  'values':'',
                  'type':'array_1d(100)',
                  'xlabel':monitor['xlabel'],
                  'ylabel':monitor['ylabel'],
                  'File':'Scan',
                  'title':''}
        
        return FSsingle
    
REGISTRY['mvi'] = McStasVirtualInstrument
    
