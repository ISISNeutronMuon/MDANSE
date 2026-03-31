.. _cluster-tutorial:

Running MDANSE on a cluster
===========================

We expect that you will be running your MDANSE analysis on a cluster
using Python scripts which can be run from the shell. These will be
called within a batch script which you submit to the cluster's queuing system.

If you installed MDANSE yourself, just activate the MDANSE Python virtual environment
in your batch scripts. On clusters using
`modules <https://hpc-wiki.info/hpc/Modules>`_ you will have to make sure that
your script activates the same Python module which you used to create the virtual
environment.

Progress bar
~~~~~~~~~~~~

Normally, when you are running a Python script with an MDANSE analysis 
and `tqdm` is available (possibly through installing the `cli` extra), 
it will attempt to display a progress bar. 
As cluster jobs are not interactive, the progress bar
will be repeatedly written into the standard output and most likely saved
in your log file. Depending on your preference, you may decide just to disable
the progress bar in the run method:

.. code-block:: Python

    ANALYSIS_INSTANCE.run(parameters, ... , prog_bar=False)

MDANSE scripts
~~~~~~~~~~~~~~

The recommended way of preparing the scripts is to create them
on your local computer using the GUI. You can then upload them
onto the cluster and modify them. The main things you will need
to change will be:

  * paths to the input files,
  * paths to the output files,
  * number of CPU cores in multicore runs.

Other than this, the scripts are designed to be transferable between
platforms, so as long as you use the same input files on the
cluster that you used to create the script in the GUI,
the values of the input parameters should work the same as they
would on your local computer.

Current limitations
~~~~~~~~~~~~~~~~~~~

MDANSE does not use MPI in its parallel runs. This means that you
will only be able to run your analysis on a single node. Additionally,
there is no mechanism of selecting which specific cores or sockets
your analysis will run on, so most likely you will need to reserve
the entire node for your MDANSE runs to avoid conflicts with the
tasks submitted by other users.
