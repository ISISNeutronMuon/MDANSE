# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Plugins/ComponentPlugin.py
# @brief     Implements module/class/test ComponentPlugin
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE.GUI.Plugins.IPlugin import IPlugin 
             
class ComponentPlugin(IPlugin):
    
    @property
    def datakey(self):
        return self.parent.datakey

    @property
    def dataproxy(self):
        return self.parent.dataproxy
    
    @property
    def dataplugin(self):
        return self.parent.dataplugin

