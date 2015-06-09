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

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.DistanceHistogram import DistanceHistogram

class CoordinationNumber(DistanceHistogram):
    """
    The Coordination Number is computed from the pair distribution function for a set of atoms. 
    It describes the total number of neighbours, as a function of distance, from a central atom, or the centre of a group of atoms.
    """

    type = 'cn'

    label = "Coordination Number"
    
    category = ('Structure',)
    
    ancestor = "mmtk_trajectory"        

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['r_values'] = ('range', {'valueType':float, 'includeLast':True, 'mini':0.0})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['transmutated_atoms'] = ('atom_transmutation', {'dependencies':{'trajectory':'trajectory',
                                                                                  'atom_selection':'atom_selection'}})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
                
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """   

        npoints = len(self.configuration['r_values']['mid_points'])

        self._outputData['r'] = REGISTRY["outputvariable"]("line", self.configuration['r_values']['mid_points'], "r", units="nm") 
        
        for pair in self._elementsPairs:
            invPair = pair[::-1]
            self._outputData.add("cn_intra_%s%s" % pair,"line", (npoints,), 'r', units="au")                                                 
            self._outputData.add("cn_inter_%s%s" % pair,"line", (npoints,), 'r', units="au",)                                                 
            self._outputData.add("cn_total_%s%s" % pair,"line", (npoints,), 'r', units="au")                                                 
            self._outputData.add("cn_intra_%s%s" % invPair,"line", (npoints,), 'r', units="au")                                                 
            self._outputData.add("cn_inter_%s%s" % invPair,"line", (npoints,), 'r', units="au",)                                                 
            self._outputData.add("cn_total_%s%s" % invPair,"line", (npoints,), 'r', units="au")                                                 
        
        nFrames = self.configuration['frames']['number']
        
        densityFactor = 4.0*numpy.pi*self.configuration['r_values']['mid_points']
        
        shellSurfaces = densityFactor*self.configuration['r_values']['mid_points']
        
        shellVolumes  = shellSurfaces*self.configuration['r_values']['step']
  
        self.averageDensity *= 4.0*numpy.pi/nFrames

        r2 = self.configuration['r_values']['mid_points']**2
        dr = self.configuration['r_values']['step']
        
        for k in self._concentrations.keys():
            self._concentrations[k] /= nFrames

        for pair in self._elementsPairs:
            ni = self.configuration['atom_selection']['n_atoms_per_element'][pair[0]]
            nj = self.configuration['atom_selection']['n_atoms_per_element'][pair[1]]
            
            idi = self.selectedElements.index(pair[0])
            idj = self.selectedElements.index(pair[1])

            if idi == idj:
                nij = ni*(ni-1)/2.0    
            else:
                nij = ni*nj
                self.hIntra[idi,idj] += self.hIntra[idj,idi]
                self.hInter[idi,idj] += self.hInter[idj,idi]
            
            fact = nij*nFrames*shellVolumes
             
            self.hIntra[idi,idj,:] /= fact             
            self.hInter[idi,idj,:] /= fact
                         
            cnIntra = numpy.add.accumulate(self.hIntra[idi,idj,:]*r2)*dr
            cnInter = numpy.add.accumulate(self.hInter[idi,idj,:]*r2)*dr
            cnTotal = cnIntra + cnInter
            
            cAlpha = self._concentrations[pair[0]]
            cBeta = self._concentrations[pair[1]]
                        
            invPair = pair[::-1]
            self._outputData["cn_intra_%s%s" % pair][:] = self.averageDensity*cBeta*cnIntra
            self._outputData["cn_inter_%s%s" % pair][:] = self.averageDensity*cBeta*cnInter        
            self._outputData["cn_total_%s%s" % pair][:] = self.averageDensity*cBeta*cnTotal 
            self._outputData["cn_intra_%s%s" % invPair][:] = self.averageDensity*cAlpha*cnIntra
            self._outputData["cn_inter_%s%s" % invPair][:] = self.averageDensity*cAlpha*cnInter        
            self._outputData["cn_total_%s%s" % invPair][:] = self.averageDensity*cAlpha*cnTotal 

        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self.header)
        
        self.configuration['trajectory']['instance'].close()     
  
        DistanceHistogram.finalize(self)
