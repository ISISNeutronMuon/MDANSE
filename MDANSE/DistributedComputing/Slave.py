"""This modules contains the handlers functions used by Pyro slaves to perform the job.

Functions:
    * do_run_step: performs the analysis step by step.
"""

# Define (or import) all the task handlers.
def do_run_step(job, step):
             
    return job.run_step(step)

from MDANSE.DistributedComputing.MasterSlave import startSlaveProcess
startSlaveProcess(master_host="localhost:%d")
    

