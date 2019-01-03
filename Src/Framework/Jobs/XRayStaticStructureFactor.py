import collections

import numpy

from MDANSE import ELEMENTS, REGISTRY
from MDANSE.Framework.Jobs.DistanceHistogram import DistanceHistogram
from MDANSE.Mathematics.Arithmetic import weight

def atomic_scattering_factor(element, qvalues):
    
    a = numpy.empty((4,),dtype=numpy.float64)
    a[0] = ELEMENTS[element,"xray_asf_a1"]
    a[1] = ELEMENTS[element,"xray_asf_a2"]
    a[2] = ELEMENTS[element,"xray_asf_a3"]
    a[3] = ELEMENTS[element,"xray_asf_a4"]

    b = numpy.empty((4,),dtype=numpy.float64)
    b[0] = ELEMENTS[element,"xray_asf_b1"]
    b[1] = ELEMENTS[element,"xray_asf_b2"]
    b[2] = ELEMENTS[element,"xray_asf_b3"]
    b[3] = ELEMENTS[element,"xray_asf_b4"]
    
    c = ELEMENTS[element,"xray_asf_c"]
    
    return c + numpy.sum(a[:, numpy.newaxis] * numpy.exp(-b[:, numpy.newaxis]*(qvalues[numpy.newaxis, :]/(4.0*numpy.pi))**2),axis=0)

class XRayStaticStructureFactor(DistanceHistogram):
    """
    Computes the X-ray static structure from the pair distribution function for a set of atoms,
	taking into account the atomic form factor for X-rays.
    """

    label = "XRay Static Structure Factor"
    
    category = ('Analysis','Structure',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]
    
    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['r_values'] = ('range', {'valueType':float, 'includeLast':True, 'mini':0.0})
    settings['q_values'] = ('range', {'valueType':float, 'includeLast':True, 'mini':0.0})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_transmutation'] = ('atom_transmutation', {'dependencies':{'trajectory':'trajectory','atom_selection':'atom_selection'}})
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

            self._outputData.add("xssf_intra_%s%s" % pair,"line", (nq,), axis='q', units="au")                                                 
            self._outputData.add("xssf_inter_%s%s" % pair,"line", (nq,), axis='q', units="au",)                                                 
            self._outputData.add("xssf_total_%s%s" % pair,"line", (nq,), axis='q', units="au")                                                 

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
                        
            self._outputData["xssf_intra_%s%s" % pair][:] = fact1*numpy.sum((r**2)*pdfIntra*sincqr,axis=1)*dr
            self._outputData["xssf_inter_%s%s" % pair][:] = 1.0 + fact1*numpy.sum((r**2)*(pdfInter-1.0)*sincqr,axis=1)*dr
            self._outputData["xssf_total_%s%s" % pair][:] = self._outputData["xssf_intra_%s%s" % pair][:] + self._outputData["xssf_inter_%s%s" % pair][:]

        self._outputData.add("xssf_intra","line", (nq,), axis='q', units="au")                                                 
        self._outputData.add("xssf_inter","line", (nq,), axis='q', units="au")                                                 
        self._outputData.add("xssf_total","line", (nq,), axis='q', units="au")                                                 

        asf = dict((k,atomic_scattering_factor(k,self._outputData['q'])) for k in nAtomsPerElement.keys())
                        
        xssfIntra = weight(asf,self._outputData,nAtomsPerElement,2,"xssf_intra_%s%s")
        self._outputData["xssf_intra"][:] = xssfIntra
 
        xssfInter = weight(asf,self._outputData,nAtomsPerElement,2,"xssf_inter_%s%s")
        self._outputData["xssf_inter"][:] = xssfInter
           
        self._outputData["xssf_total"][:] = xssfIntra + xssfInter
        
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
          
        self.configuration['trajectory']['instance'].close()
        
REGISTRY['xssf'] = XRayStaticStructureFactor
