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

import os
from MDANSE import PLATFORM

import Pyro
Pyro.config.PYRO_STORAGE = PLATFORM.home_directory()
Pyro.config.PYRO_NS_URIFILE = os.path.join(Pyro.config.PYRO_STORAGE,'Pyro_NS_URI')
Pyro.config.PYRO_LOGFILE = os.path.join(Pyro.config.PYRO_STORAGE,'Pyro_log')
Pyro.config.PYRO_USER_LOGFILE = os.path.join(Pyro.config.PYRO_STORAGE,'Pyro_userlog')
Pyro.config.PYROSSL_CERTDIR = os.path.join(Pyro.config.PYRO_STORAGE,'certs')

# Define (or import) all the task handlers.
def do_run_step(job, step):
    '''
    Computes a single step of a distributed job.
    
    :param job: the distributed job
    :type job: any class that implements the run_step method
    :param step: the step number
    :type step: int
    
    :return: the return values of the distributed job for this step
    :rtype: tuple of the form (step,return values)
    '''
             
    return job.run_step(step)

from MDANSE.DistributedComputing.MasterSlave import startSlaveProcess
# Start the slave process
startSlaveProcess(master_host="localhost:%d")
    

