#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#71 avenue des Martyrs
#38000 Grenoble Cedex 9
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

:author: Eric C. Pellegrini
'''

import collections
import itertools

import numpy

from MDANSE import REGISTRY
from MDANSE import ELEMENTS
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import correlation, get_spectrum
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory

class DynamicTotalStructureFactorError(Error):
    pass

class DynamicTotalStructureFactor(IJob):
    """
    Computes the dynamic total structure factor for a set of atoms as the sum of the incoherent and coherent structure factors
    """
    
    label = "Dynamic Total Structure Factor"

    category = ('Analysis','Scattering',)
    
    ancestor = ["mmtk_trajectory"]

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['instrument_resolution'] = ('instrument_resolution',{'dependencies':{'trajectory':'trajectory','frames' : 'frames'}})
    settings['q_vectors'] = ('q_vectors',{'dependencies':{'trajectory':'trajectory'}})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_transmutation'] = ('atom_transmutation', {'dependencies':{'trajectory':'trajectory','atom_selection':'atom_selection'}})
    settings['weights'] = ('weights', {'default':'b_coherent',"dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection', 'atom_transmutation':'atom_transmutation'}})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        if not self.configuration['trajectory']['instance'].universe.is_periodic:
            raise DynamicCoherentStructureFactorError('Cannot start %s analysis on non-periodic system' % self.label)
        
        if not self.configuration['q_vectors']['is_lattice']:
            raise DynamicCoherentStructureFactorError('The Q vectors must be generated on a lattice to run %s analysis' % self.label)
        
        self.numberOfSteps = self.configuration['q_vectors']['n_shells']
        
        nQShells = self.configuration["q_vectors"]["n_shells"]

        self._nFrames = self.configuration['frames']['number']
        
        self._instrResolution = self.configuration["instrument_resolution"]
        
        self._nOmegas = self._instrResolution['n_omegas']

        self._outputData.add("q","line",self.configuration["q_vectors"]["shells"], units="inv_nm") 

        self._outputData.add("time","line", self.configuration['frames']['duration'], units='ps')
        self._outputData.add("time_window","line", self._instrResolution["time_window"], units="au") 

        self._outputData.add("omega","line", self._instrResolution["omega"], units='rad/ps')
        self._outputData.add("omega_window","line", self._instrResolution["omega_window"], axis="omega", units="au") 
                                
        self._elementsPairs = sorted(itertools.combinations_with_replacement(self.configuration['atom_selection']['unique_names'],2))
        self._indexesPerElement = self.configuration['atom_selection'].get_indexes()

        for element in self.configuration['atom_selection']['unique_names']:
            self._outputData.add("f_inc(q,t)_%s" % element,"surface", (nQShells,self._nFrames), axis="q|time",  units="au")
            self._outputData.add("f_tot(q,t)_%s" % element,"surface", (nQShells,self._nFrames), axis="q|time",  units="au")
            self._outputData.add("s_inc(q,f)_%s" % element,"surface", (nQShells,self._nOmegas), axis="q|omega", units="nm2/ps")
            self._outputData.add("s_tot(q,f)_%s" % element,"surface", (nQShells,self._nOmegas), axis="q|omega", units="nm2/ps")

        for pair in self._elementsPairs:
            self._outputData.add("f_coh(q,t)_%s%s" % pair,"surface", (nQShells,self._nFrames), axis="q|time" , units="au")
            self._outputData.add("s_coh(q,f)_%s%s" % pair,"surface", (nQShells,self._nOmegas), axis="q|omega", units="nm2/ps")

        self._outputData.add("f_coh(q,t)_total","surface", (nQShells,self._nFrames), axis="q|time", units="au")
        self._outputData.add("f_inc(q,t)_total","surface", (nQShells,self._nFrames), axis="q|time", units="au")
        self._outputData.add("f_coh_weighted(q,t)_total","surface", (nQShells,self._nFrames), axis="q|time", units="au")
        self._outputData.add("f_inc_weighted(q,t)_total","surface", (nQShells,self._nFrames), axis="q|time", units="au")
        self._outputData.add("f_tot(q,t)_total","surface", (nQShells,self._nFrames), axis="q|time", units="au")

        self._outputData.add("s_coh(q,f)_total","surface", (nQShells,self._nOmegas), axis="q|omega", units="nm2/ps")
        self._outputData.add("s_inc(q,f)_total","surface", (nQShells,self._nOmegas), axis="q|omega", units="nm2/ps")
        self._outputData.add("s_coh_weighted(q,f)_total","surface", (nQShells,self._nOmegas), axis="q|omega", units="nm2/ps")
        self._outputData.add("s_inc_weighted(q,f)_total","surface", (nQShells,self._nOmegas), axis="q|omega", units="nm2/ps")
        self._outputData.add("s_tot(q,f)_total","surface", (nQShells,self._nOmegas), axis="q|omega", units="nm2/ps")
 
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. rho (numpy.array): The exponential part of I(k,t)
        """
        
        shell = self.configuration["q_vectors"]["shells"][index]
        
        if not shell in self.configuration["q_vectors"]["value"]:
            return index, None
            
        else:

            traj = self.configuration['trajectory']['instance']
            
            nQVectors = self.configuration["q_vectors"]["value"][shell]["q_vectors"].shape[1]
                                                                                    
            rho = {}
            for element in self.configuration['atom_selection']['unique_names']:
                rho[element] = numpy.zeros((self._nFrames, nQVectors), dtype = numpy.complex64)

            # loop over the trajectory time steps
            for i, frame in enumerate(self.configuration['frames']['value']):
            
                qVectors = self.configuration["q_vectors"]["value"][shell]["q_vectors"]
                                
                conf = traj.configuration[frame]

                for element,idxs in self._indexesPerElement.items():

                    selectedCoordinates = numpy.take(conf.array, idxs, axis=0)
                    rho[element][i,:] = numpy.sum(numpy.exp(1j*numpy.dot(selectedCoordinates, qVectors)),axis=0)


            disf_per_q_shell = {}
            for element in self.configuration['atom_selection']['unique_names']:
                disf_per_q_shell[element] = numpy.zeros((self._nFrames,), dtype = numpy.float)

            for i,atom_indexes in enumerate(self.configuration['atom_selection']["indexes"]):

                masses = self.configuration['atom_selection']["masses"][i]

                element = self.configuration['atom_selection']["names"][i]
                        
                series = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                               atom_indexes,
                                               first=self.configuration['frames']['first'],
                                               last=self.configuration['frames']['last']+1,
                                               step=self.configuration['frames']['step'],
                                               weights=[masses])
                                                                                                    
                temp = numpy.exp(1j*numpy.dot(series, qVectors))
                res = correlation(temp, axis=0, average=1)
                    
                disf_per_q_shell[element] += res

            return index, (rho, disf_per_q_shell)
    
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """
               
        if x is not None:
            rho,disf = x

            for pair in self._elementsPairs:
                corr = correlation(rho[pair[0]],rho[pair[1]], average=1)
                self._outputData["f_coh(q,t)_%s%s" % pair][index,:] += corr

            for k,v in disf.items():
                self._outputData["f_inc(q,t)_%s" % k][index,:] += v
            
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """
        nAtomsPerElement = self.configuration['atom_selection'].get_natoms()
        
        # Compute concentrations
        nTotalAtoms = 0
        for val in nAtomsPerElement.values():
            nTotalAtoms += val

        # Compute coherent functions and structure factor
        for pair in self._elementsPairs:
            b_coh1 = ELEMENTS[pair[0],"b_coherent"]
            b_coh2 = ELEMENTS[pair[1],"b_coherent"]
            ni = nAtomsPerElement[pair[0]]
            nj = nAtomsPerElement[pair[1]]
            ci = float(ni)/nTotalAtoms
            cj = float(ni)/nTotalAtoms
            
            self._outputData["f_coh(q,t)_%s%s" % pair][:] /= numpy.sqrt(ni*nj)
            self._outputData["s_coh(q,f)_%s%s" % pair][:] = get_spectrum(self._outputData["f_coh(q,t)_%s%s" % pair],
                                                                         self.configuration["instrument_resolution"]["time_window"],
                                                                         self.configuration["instrument_resolution"]["time_step"],
                                                                         axis=1)
            self._outputData["f_coh_weighted(q,t)_total"][:] += self._outputData["f_coh(q,t)_%s%s" % pair][:] * numpy.sqrt(ci*cj) * b_coh1 * b_coh2
            self._outputData["s_coh_weighted(q,f)_total"][:] += self._outputData["s_coh(q,f)_%s%s" % pair][:] * numpy.sqrt(ci*cj) * b_coh1 * b_coh2
        
        # Compute incoherent functions and structure factor
        for element, ni in nAtomsPerElement.items():
            b_inc = ELEMENTS[element,"b_incoherent"]
            ni = nAtomsPerElement[element]
            ci = float(ni)/nTotalAtoms
            
            self._outputData["f_inc(q,t)_%s" % element][:] /= ni
            self._outputData["s_inc(q,f)_%s" % element][:] = get_spectrum(self._outputData["f_inc(q,t)_%s" % element],
                                                                          self.configuration["instrument_resolution"]["time_window"],
                                                                          self.configuration["instrument_resolution"]["time_step"],
                                                                          axis=1)
            self._outputData["f_inc_weighted(q,t)_total"][:] += self._outputData["f_inc(q,t)_%s" % element][:] * ci * b_inc**2
            self._outputData["s_inc_weighted(q,f)_total"][:] += self._outputData["s_inc(q,f)_%s" % element][:] * ci * b_inc**2
        
        # Compute total sum
        self._outputData["f_tot(q,t)_total"][:] = self._outputData["f_coh_weighted(q,t)_total"][:] + self._outputData["f_inc_weighted(q,t)_total"][:]
        self._outputData["s_tot(q,f)_total"][:] = self._outputData["s_coh_weighted(q,f)_total"][:] + self._outputData["s_inc_weighted(q,f)_total"][:]
       
        #
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        self.configuration['trajectory']['instance'].close()
  
REGISTRY['ndtsf'] = NeutronDynamicTotalStructureFactor