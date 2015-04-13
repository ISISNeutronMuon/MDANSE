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
import itertools

import numpy

from MDANSE import ELEMENTS
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import correlation, get_spectrum

class DynamicCoherentStructureFactorError(Error):
    pass

class DynamicCoherentStructureFactor(IJob):
    """
    Computes the dynamic coherent structure factor for a set of atoms.
    """

    type = 'dcsf'
    
    label = "Dynamic Coherent Structure Factor"

    category = ('Scattering',)
    
    ancestor = "mmtk_trajectory"

    configurators = collections.OrderedDict()
    configurators['trajectory'] = ('mmtk_trajectory',{})
    configurators['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    configurators['instrument_resolution'] = ('instrument_resolution',{'dependencies':{'trajectory':'trajectory',
                                                                                       'frames' : 'frames'}})
    configurators['q_vectors'] = ('q_vectors',{'dependencies':{'trajectory':'trajectory'}})
    configurators['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    configurators['transmutated_atoms'] = ('atom_transmutation', {'dependencies':{'trajectory':'trajectory',
                                                                                  'atom_selection':'atom_selection'}})
    configurators['weights'] = ('weights', {'default':'b_coherent'})
    configurators['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    configurators['running_mode'] = ('running_mode',{})
    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        if not self.configuration['trajectory']['instance'].universe.is_periodic:
            raise DynamicCoherentStructureFactorError('Cannot start %s analysis on non-periodic system'%self.label)
        
        if not self.configuration['q_vectors']['is_lattice']:
            raise DynamicCoherentStructureFactorError('The Q vectors must be generated on a lattice to run %s analysis'%self.label)
        
        self.numberOfSteps = self.configuration['q_vectors']['n_shells']
        
        nQShells = self.configuration["q_vectors"]["n_shells"]

        self._nFrames = self.configuration['frames']['number']
        
        self._instrResolution = self.configuration["instrument_resolution"]
        
        self._nFrequencies = self._instrResolution['n_frequencies']

        self._outputData.add("q","line",self.configuration["q_vectors"]["shells"], units="inv_nm") 

        self._outputData.add("time","line", self.configuration['frames']['time'], units='ps')
        self._outputData.add("time_window","line", self._instrResolution["time_window"], axis="time", units="au") 

        self._outputData.add("frequency","line", self._instrResolution["frequencies"], units='THz')
        self._outputData.add("frequency_window","line", self._instrResolution["frequency_window"], axis="frequency", units="au") 
                                
        self._elementsPairs = sorted(itertools.combinations_with_replacement(self.configuration['atom_selection']['contents'].keys(),2))

        for pair in self._elementsPairs:
            self._outputData.add("f(q,t)_%s%s" % pair,"surface", (nQShells,self._nFrames),axis="q|time"     , units="au")                                                 
            self._outputData.add("s(q,f)_%s%s" % pair,"surface", (nQShells,self._nFrequencies), axis="q|frequency", units="nm2/ps") 

        self._outputData.add("f(q,t)_total","surface", (nQShells,self._nFrames), axis="q|time", units="au")                                                 
        self._outputData.add("s(q,f)_total","surface", (nQShells,self._nFrequencies), axis="q|frequency", units="nm2/ps") 
 
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
            
            qVectors = self.configuration["q_vectors"]["value"][shell]["q_vectors"]
            
            qVectors = traj.universe._boxToRealPointArray(qVectors.T)
                                     
            qVectors = qVectors.T
                                                            
            rho = {}
            for element in self.configuration['atom_selection']['contents'].keys():
                rho[element] = numpy.zeros((self._nFrames, qVectors.shape[1]), dtype = numpy.complex64)

            # loop over the trajectory time steps
            for i, frame in enumerate(self.configuration['frames']['value']):
                
                conf = traj.configuration[frame]

                conf.convertToBoxCoordinates()

                for element,idxs in self.configuration['atom_selection']['contents'].items():
                    selectedCoordinates = numpy.take(conf.array, idxs, axis=0)
                    rho[element][i,:] = numpy.sum(numpy.exp(1j*numpy.dot(selectedCoordinates, qVectors)),axis=0)

            return index, rho
    
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """
               
        for pair in self._elementsPairs:
            corr = correlation(x[pair[0]],x[pair[1]], reduce=1)/x[pair[0]].shape[1]
            self._outputData["f(q,t)_%s%s" % pair][index,:] += corr
            
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """
        
        for pair in self._elementsPairs:
            ni = self.configuration['atom_selection']['n_atoms_per_element'][pair[0]]
            nj = self.configuration['atom_selection']['n_atoms_per_element'][pair[1]]
            self._outputData["f(q,t)_%s%s" % pair][:] /= numpy.sqrt(ni*nj)
            self._outputData["s(q,f)_%s%s" % pair][:] = get_spectrum(self._outputData["f(q,t)_%s%s" % pair],
                                                                     self.configuration["instrument_resolution"]["time_window"],
                                                                     self.configuration["instrument_resolution"]["time_step"],
                                                                     axis=1)        
        
        props = dict([[k,ELEMENTS[k,self.configuration["weights"]["property"]]] for k in self.configuration['atom_selection']['n_atoms_per_element'].keys()])

        fqtTotal = weight(props,self._outputData,self.configuration['atom_selection']['n_atoms_per_element'],2,"f(q,t)_%s%s")

        self._outputData["f(q,t)_total"][:] = fqtTotal
        
        sqfTotal = weight(props,self._outputData,self.configuration['atom_selection']['n_atoms_per_element'],2,"s(q,f)_%s%s")
        self._outputData["s(q,f)_total"][:] = sqfTotal
    
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self.header)
        
        self.configuration['trajectory']['instance'].close()     
  
        