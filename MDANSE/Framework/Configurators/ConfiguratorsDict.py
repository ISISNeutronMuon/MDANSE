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
Created on Mar 30, 2015

@author: pellegrini
'''

import collections

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error

class ConfiguratorDictError(Error):
    pass
    
class ConfiguratorsDict(collections.OrderedDict):
    
    def add_item(self, name, typ, *args, **kwargs):
                
        try:
            self[name] = REGISTRY["configurator"][typ](name, *args, **kwargs)
        except KeyError:
            raise ConfiguratorDictError("invalid type for %r configurator" % name)
                                                
    def build_doc(self):
        
        if not self:
            return ""
                    
        docdict = collections.OrderedDict()
        
        for i, (k,v) in enumerate(self.items()):
            docdict[i] = {'Parameter' : str(k), 
                          'Default' : str(v.default),
                          'Description' : str(v.__doc__)
                          }
            
        l = ['Parameters','Default','Description']
        
        sizes = []  
        sizes.append([len(l[0])]) 
        sizes.append([len(l[1])]) 
        sizes.append([len(l[2])]) 
        
        for k, v in docdict.items():
            sizes[0].append(len(v['Parameter']))
            sizes[1].append(len(v['Default']))
            
            v['Description'] = v['Description'].replace('\n',' ').replace('  ',' ').replace('  ',' ').replace('  ',' ')
            sizes[2].append(len(v['Description']))
            
        maxSizes = [max(s) for s in sizes]
            
        s = (maxSizes[0]+2, maxSizes[1]+2, maxSizes[2]+2)
                
        table = '\n**Job input parameters:** \n\n'
        
        table += '+%s+%s+%s+\n'%(s[0]*'-',s[1]*'-',s[2]*'-')
        
        table += '| %s%s | %s%s | %s%s |\n' %(l[0], (s[0]-len(l[0])-2)*' ', l[1],(s[1]-len(l[1])-2)*' ', l[2],(s[2]-len(l[2])-2)*' ')            
        
        table += '+%s+%s+%s+\n'%(s[0]*'=',s[1]*'=',s[2]*'=') 
        
        for k,v in docdict.items():
            p = v['Parameter']
            df = v['Default']
            ds = v['Description']
            table += '| %s%s | %s%s | %s%s |\n'%(p,(s[0]-len(p)-2)*' ', df,(s[1]-len(df)-2)*' ', ds,(s[2]-len(ds)-2)*' ')
            table += '+%s+%s+%s+\n'%(s[0]*'-',s[1]*'-',s[2]*'-')
    
        return table
    
    def get_default_parameters(self):
        
        params = collections.OrderedDict()
        for k,v in self.items():
            params[k] = v.default
            
        return params