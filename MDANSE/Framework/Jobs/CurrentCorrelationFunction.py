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
Created on Mar 30, 2015

:author: Eric C. Pellegrini
'''

import collections
import itertools

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import correlation, normalize, get_spectrum

class CurrentCorrelationFunction(IJob):
    """
    Computes the current correlation function for a set of atoms.
    The transverse and longitudinal current correlation functions are typically used to study the propagation of excitations in disordered systems.
    The longitudinal current is directly related to density fluctuations and the transverse current is linked to propagating 'shear modes'.
    
    For more information, see e.g. 'J.-P. Hansen and I. R. McDonald, Theory of Simple Liquids (3rd ed., Elsevier), chapter 7.4: Correlations
    in space and time)' 
    """
    
    label = "Current Correlation Function"

    category = ('Analysis','Scattering',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['instrument_resolution'] = ('instrument_resolution',{'dependencies':{'trajectory':'trajectory','frames' : 'frames'}})
    settings['q_vectors'] = ('q_vectors',{'dependencies':{'trajectory':'trajectory'}})
    settings['atom_selection'] = ('atom_selection',{'dependencies':{'trajectory':'trajectory'}})
    settings['normalize'] = ('boolean', {'default':False})
    settings['atom_transmutation'] = ('atom_transmutation',{'dependencies':{'trajectory':'trajectory','atom_selection':'atom_selection'}})
    settings['weights'] = ('weights', {'default':'b_coherent',"dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection', 'atom_transmutation':'atom_transmutation'}})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['q_vectors']['n_shells']

        nQShells = self.configuration["q_vectors"]["n_shells"]
        
        self._nFrames = self.configuration['frames']['number']
        
        self._instrResolution = self.configuration["instrument_resolution"]
        
        self._nOmegas = self._instrResolution['n_omegas']
                
        self._outputData.add("q","line", numpy.array(self.configuration["q_vectors"]["shells"]), units="inv_nm") 

        self._outputData.add("time","line", self.configuration['frames']['time'], units='ps')
        self._outputData.add("time_window","line", self._instrResolution["time_window"], units="au") 

        self._outputData.add("omega","line", self._instrResolution["omega"],units='rad/ps')
        self._outputData.add("omega_window","line", self._instrResolution["omega_window"], axis="omega", units="au") 

        self._elements = self.configuration['atom_selection']['unique_names']
        self._elementsPairs = sorted(itertools.combinations_with_replacement(self._elements,2))
        
        self._indexesPerElement = self.configuration['atom_selection'].get_indexes()

        for pair in self._elementsPairs:
            self._outputData.add("j(q,t)_long_%s%s"  % pair,"surface", (nQShells,self._nFrames), axis="q|time", units="au")                                                 
            self._outputData.add("j(q,t)_trans_%s%s" % pair,"surface", (nQShells,self._nFrames), axis="q|time", units="au")                                                 
            self._outputData.add("J(q,f)_long_%s%s"  % pair,"surface", (nQShells,self._nOmegas), axis="q|omega", units="au") 
            self._outputData.add("J(q,f)_trans_%s%s" % pair,"surface", (nQShells,self._nOmegas), axis="q|omega", units="au") 

        self._outputData.add("j(q,t)_long_total","surface", (nQShells,self._nFrames), axis="q|time"    , units="au")                                                 
        self._outputData.add("J(q,f)_long_total","surface", (nQShells,self._nOmegas), axis="q|omega", units="au") 
        self._outputData.add("j(q,t)_trans_total","surface", (nQShells,self._nFrames), axis="q|time"    , units="au")                                                 
        self._outputData.add("J(q,f)_trans_total","surface", (nQShells,self._nOmegas), axis="q|omega", units="au") 
         
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. rho (numpy.array): The exponential part of I(q,t)
        """

        shell = self.configuration["q_vectors"]["shells"][index]
        
        if not shell in self.configuration["q_vectors"]["value"]:
            return index, None
            
        else:
            
            traj = self.configuration['trajectory']['instance']
            
            qVectors = self.configuration["q_vectors"]["value"][shell]["q_vectors"]
            
            qVectors = traj.universe._boxToRealPointArray(qVectors.T)
                                     
            qVectors = qVectors.T
            
            nQVectors = qVectors.shape[1]
            
            rho = {}
            rho_loop = {}
            rhoLong = {}
            rhoTrans = {}
            rhoLong_loop = {}
            rhoTrans_loop = {}
            for element in self._elements:
                rho[element] = numpy.zeros((self._nFrames, 3, nQVectors), dtype = numpy.complex64)
                rho_loop[element] = numpy.zeros((self._nFrames, 3, nQVectors), dtype = numpy.complex64)
                rhoLong_loop[element] = numpy.zeros((self._nFrames, 3, nQVectors), dtype = numpy.complex64)
                rhoTrans_loop[element] = numpy.zeros((self._nFrames, 3, nQVectors), dtype = numpy.complex64)

            # loop over the trajectory time steps
            for i, frame in enumerate(self.configuration['frames']['value']):
                conf = traj.configuration[frame]
                vel = traj.velocities[frame]
                
                for element,idxs in self._indexesPerElement.items():
                    selectedCoordinates = conf.array[idxs,:]
                    selectedVelocities =  vel.array[idxs,:]
                    selectedVelocities = numpy.transpose(selectedVelocities)[:,:,numpy.newaxis]
                    tmp = numpy.exp(1j*numpy.dot(selectedCoordinates, qVectors))[numpy.newaxis,:,:]
                    rho[element][i,:,:] = numpy.add.reduce(selectedVelocities*tmp,1)

            Q2 = numpy.sum(qVectors**2,axis=0)
            
            for element in self._elements:
                qj = numpy.sum(rho[element]*qVectors,axis=1)
                rhoLong[element] = (qj[:,numpy.newaxis,:]*qVectors[numpy.newaxis,:,:])/Q2
                rhoTrans[element] = rho[element] - rhoLong[element]

            return index, (rhoLong, rhoTrans)
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        if x is None:
            return
        
        jLong, jTrans = x
        
        for at1,at2 in self._elementsPairs:
            
            corrLong = numpy.zeros((self._nFrames,),dtype=numpy.float64)
            corrTrans = numpy.zeros((self._nFrames,),dtype=numpy.float64)
            
            for i in range(3):
                corrLong += correlation(jLong[at1][:,i,:],jLong[at2][:,i,:], axis=0, average=1)
                corrTrans += correlation(jTrans[at1][:,i,:],jTrans[at2][:,i,:], axis=0, average=1)
                            
            self._outputData["j(q,t)_long_%s%s" % (at1,at2)][index,:] += corrLong
            self._outputData["j(q,t)_trans_%s%s" % (at1,at2)][index,:] += corrTrans
                                        
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """
                        
        nAtomsPerElement = self.configuration['atom_selection'].get_natoms()
        for pair in self._elementsPairs:
            at1,at2 = pair
            ni = nAtomsPerElement[at1]
            nj = nAtomsPerElement[at2]
            self._outputData["j(q,t)_long_%s%s" % pair][:] /= ni*nj
            self._outputData["j(q,t)_trans_%s%s" % pair][:] /= ni*nj
            self._outputData["J(q,f)_long_%s%s" % pair][:] = get_spectrum(self._outputData["j(q,t)_long_%s%s" % pair],
                                                                          self.configuration["instrument_resolution"]["time_window"],
                                                                          self.configuration["instrument_resolution"]["time_step"],
                                                                          axis=1)        
            self._outputData["J(q,f)_trans_%s%s" % pair][:] = get_spectrum(self._outputData["j(q,t)_trans_%s%s" % pair],
                                                                           self.configuration["instrument_resolution"]["time_window"],
                                                                           self.configuration["instrument_resolution"]["time_step"],
                                                                           axis=1)        

        if self.configuration['normalize']["value"]:
            for pair in self._elementsPairs:
                self._outputData["j(q,t)_long_%s%s" % pair] = normalize(self._outputData["j(q,t)_long_%s%s" % pair],axis=1)
                self._outputData["j(q,t)_trans_%s%s" % pair] = normalize(self._outputData["j(q,t)_trans_%s%s" % pair],axis=1)

        jqtLongTotal = weight(self.configuration["weights"].get_weights(),self._outputData,nAtomsPerElement,2,"j(q,t)_long_%s%s")
        self._outputData["j(q,t)_long_total"][:] = jqtLongTotal

        jqtTransTotal = weight(self.configuration["weights"].get_weights(),self._outputData,nAtomsPerElement,2,"j(q,t)_trans_%s%s")
        self._outputData["j(q,t)_trans_total"][:] = jqtTransTotal
        
        sqfLongTotal = weight(self.configuration["weights"].get_weights(),self._outputData,nAtomsPerElement,2,"J(q,f)_long_%s%s")
        self._outputData["J(q,f)_long_total"][:] = sqfLongTotal

        sqfTransTotal = weight(self.configuration["weights"].get_weights(),self._outputData,nAtomsPerElement,2,"J(q,f)_trans_%s%s")
        self._outputData["J(q,f)_trans_total"][:] = sqfTransTotal
    
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()
        
REGISTRY['ccf'] = CurrentCorrelationFunction
        