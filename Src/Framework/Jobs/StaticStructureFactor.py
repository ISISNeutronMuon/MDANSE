import collections

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.DistanceHistogram import DistanceHistogram
from MDANSE.Mathematics.Arithmetic import weight

class StaticStructureFactor(DistanceHistogram):
    """
    Computes the static structure factor from the pair distribution function for a set of atoms.
    """

    label = "Static Structure Factor"
    
    category = ('Analysis','Structure',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]
    
    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['r_values'] = ('range', {'valueType':float, 'includeLast':True, 'mini':0.0})
    settings['q_values'] = ('range', {'valueType':float, 'includeLast':True, 'mini':0.0})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_transmutation'] = ('atom_transmutation', {'dependencies':{'trajectory':'trajectory','atom_selection':'atom_selection'}})
    settings['weights'] = ('weights', {'default':'b_coherent',"dependencies":{'atom_selection':'atom_selection','atom_transmutation':'atom_transmutation'}})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
                
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """   

        nq = self.configuration['q_values']['number']
                
        nFrames = self.configuration['frames']['number']

        self.averageDensity /= nFrames
        
        densityFactor = 4.0*numpy.pi*self.configuration['r_values']['mid_points']
        
        shellSurfaces = densityFactor*self.configuration['r_values']['mid_points']
        
        shellVolumes  = shellSurfaces*self.configuration['r_values']['step']

        self._outputData.add('q',"line", self.configuration['q_values']['value'], units="inv_nm") 

        q = self._outputData['q']
        r = self.configuration['r_values']['mid_points']
  
        fact1 = 4.0*numpy.pi*self.averageDensity

        sincqr = numpy.sinc(numpy.outer(q,r)/numpy.pi)
        
        dr = self.configuration['r_values']['step']
        
        nAtomsPerElement = self.configuration['atom_selection'].get_natoms()
        for pair in self._elementsPairs:

            self._outputData.add("ssf_intra_%s%s" % pair,"line", (nq,), axis='q', units="au")                                                 
            self._outputData.add("ssf_inter_%s%s" % pair,"line", (nq,), axis='q', units="au",)                                                 
            self._outputData.add("ssf_total_%s%s" % pair,"line", (nq,), axis='q', units="au")                                                 

            ni = nAtomsPerElement[pair[0]]
            nj = nAtomsPerElement[pair[1]]
            
            idi = self.selectedElements.index(pair[0])
            idj = self.selectedElements.index(pair[1])

            if pair[0] == pair[1]:
                nij = ni*(ni-1)/2.0    
            else:
                nij = ni*nj
                self.hIntra[idi,idj] += self.hIntra[idj,idi]
                self.hInter[idi,idj] += self.hInter[idj,idi]
            
            fact = nij*nFrames*shellVolumes

            pdfIntra = self.hIntra[idi,idj,:] / fact
            pdfInter = self.hInter[idi,idj,:] / fact
                        
            self._outputData["ssf_intra_%s%s" % pair][:] = fact1*numpy.sum((r**2)*pdfIntra*sincqr,axis=1)*dr
            self._outputData["ssf_inter_%s%s" % pair][:] = 1.0 + fact1*numpy.sum((r**2)*(pdfInter-1.0)*sincqr,axis=1)*dr
            self._outputData["ssf_total_%s%s" % pair][:] = self._outputData["ssf_intra_%s%s" % pair][:] + self._outputData["ssf_inter_%s%s" % pair][:]

        self._outputData.add("ssf_intra","line", (nq,), axis='q', units="au")                                                 
        self._outputData.add("ssf_inter","line", (nq,), axis='q', units="au",)                                                 
        self._outputData.add("ssf_total","line", (nq,), axis='q', units="au")                                                 

        weights = self.configuration["weights"].get_weights()

        ssfIntra = weight(weights,self._outputData,nAtomsPerElement,2,"ssf_intra_%s%s")
        self._outputData["ssf_intra"][:] = ssfIntra

        ssfInter = weight(weights,self._outputData,nAtomsPerElement,2,"ssf_inter_%s%s")

        self._outputData["ssf_inter"][:] = ssfInter
 
        self._outputData["ssf_total"][:] = ssfIntra + ssfInter
        
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()
        
REGISTRY['ssf'] = StaticStructureFactor
