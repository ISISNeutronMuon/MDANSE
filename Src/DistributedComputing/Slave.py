# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/DistributedComputing/Slave.py
# @brief     Implements module/class/test Slave
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

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

if __name__ == "__builtin__":
    from MDANSE.DistributedComputing.MasterSlave import startSlaveProcess
    # Start the slave process
    startSlaveProcess(master_host="localhost:%d")
    

