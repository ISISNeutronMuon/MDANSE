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

import numpy

from MDANSE import ELEMENTS
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory

class ElasticIncoherentStructureFactor(IJob):
    """
    The Elastic Incoherent Structure Factor (EISF ) is defined as the limit of the incoherent
    intermediate scattering function for infinite time.

    The EISF appears as the incoherent amplitude of the elastic line in the neutron scattering spectrum.
    Elastic scattering is only present for systems in which the atomic motion is confined in space, as
    in solids. The Q-dependence of the EISF indicates e.g. the fraction of static/mobile atoms and the spatial dependence of the dynamics.
    """

    type = 'eisf'
    
    label = "Elastic Incoherent Structure Factor"

    # The category of the analysis.
    category = ('Scattering',)
    
    ancestor = ["mmtk_trajectory"]

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['q_vectors'] = ('q_vectors', {'dependencies':{'trajectory':'trajectory'}})
    settings['projection'] = ('projection', {'label':"project coordinates"})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory','grouping_level':'grouping_level'}})
    settings['grouping_level'] = ('grouping_level',{})
    settings['transmutated_atoms'] = ('atom_transmutation', {'dependencies':{'trajectory':'trajectory',
                                                                                  'atom_selection':'atom_selection'}})
    settings['weights'] = ('weights', {'default':'b_incoherent'})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        
        self.numberOfSteps = self.configuration['atom_selection']['n_groups']

        self._nQShells = self.configuration["q_vectors"]["n_shells"]
                
        self._nFrames = self.configuration['frames']['number']
                
        self._outputData.add("q","line", self.configuration["q_vectors"]["shells"], units="inv_nm") 
                        
        for element in self.configuration['atom_selection']['contents'].keys():
            self._outputData.add("eisf_%s" % element,"line", (self._nQShells,), axis="q", units="au")                                                 

        self._outputData.add("eisf_total","line", (self._nQShells,), axis="q", units="au")                                                 
        
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. atomicEISF (numpy.array): The atomic elastic incoherent structure factor
        """

        # get atom index
        indexes = self.configuration['atom_selection']["groups"][index]                                                                          
                
        series = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                       indexes,
                                       first=self.configuration['frames']['first'],
                                       last=self.configuration['frames']['last']+1,
                                       step=self.configuration['frames']['step'])
        
        series = self.configuration['projection']["projector"](series)

        atomicEISF = numpy.zeros((self._nQShells,), dtype=numpy.float64)

        for i,q in enumerate(self.configuration["q_vectors"]["shells"]):
            
            if not q in self.configuration["q_vectors"]["value"]:
                continue

            qVectors = self.configuration["q_vectors"]["value"][q]["q_vectors"]
            
            a = numpy.average(numpy.exp(1j * numpy.dot(series, qVectors)),axis=0)
            a = numpy.abs(a)**2
            
            atomicEISF[i] = numpy.average(a)
            
        return index, atomicEISF
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        # The symbol of the atom.
        element = self.configuration['atom_selection']['elements'][index][0]
        
        self._outputData["eisf_%s" % element] += x
    
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """
        
        for element, number in self.configuration['atom_selection']['n_atoms_per_element'].items():
            self._outputData["eisf_%s" % element][:] /= number

        props = dict([[k,ELEMENTS[k,self.configuration["weights"]["property"]]] for k in self.configuration['atom_selection']['n_atoms_per_element'].keys()])
        
        self._outputData["eisf_total"][:] = weight(props,self._outputData,self.configuration['atom_selection']['n_atoms_per_element'],1,"eisf_%s")
            
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()