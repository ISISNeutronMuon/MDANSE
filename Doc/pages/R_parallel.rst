Parallelism of MDANSE tasks
===========================

Analysis tasks normally run on a single CPU core. Their configuration
contains an input parameter :code:`running_mode`, shown in the scripts as

.. code-block:: python

  parameters["running_mode"] = ("single-core", )

which means that all the steps of the analysis will be executed sequentially
on a single CPU core. For most tasks, however, the option of parallel execution
is also available.

Multiprocessing
---------------

It is possible to run an analysis in MDANSE using multiple CPU cores.
The parts of the analysis that initialise and finalise the calculation
will still execute on a single core, but the main analysis steps will
be performed by separate processes. Typically, one step of an analysis
is dealing either with a single atom, or with a single q-vector shell.

To parallelise an analysis over 8 processes, the value of
:code:`running_mode` can be replaced with

.. code-block:: python

  parameters["running_mode"] = ("multicore", 8)

Trajectory converters do not offer a :code:`multicore` option, since they typically
rely on reading frames from an input file in a fixed order.

Suppression of threading
------------------------

Python code typically is less likely to benefit from multithreading, since
most of the currently (as of 2025) supported versions of CPython still allow
only one thread at a time to access the Python interpreter. However, libraries
such as :code:`numpy` are able to release the interpreter lock
and launch multiple threads for some of the tasks they perform.
MDANSE code can already use multiple CPU cores using processes,
and potentially as many of them as there are available cores.
For this reason it is preferred for these libraries not to start
additional threads.

This is the code which MDANSE always executes to set the environment
variables with may control the threading of the backend libraries,
especially :code:`numpy`:

.. code-block:: python

  #!/home/mdanse_user/python_venv/bin/python3.11

  import os
  os.environ.update(
      OMP_NUM_THREADS = '1',
      OPENBLAS_NUM_THREADS = '1',
      MKL_NUM_THREADS = '1',
      VECLIB_MAXIMUM_THREADS = '1',
      NUMEXPR_NUM_THREADS = '1'
  )

These environment variables are set by both the GUI and the CLI. This could
be important on platforms where many tasks are already running and it is
important not to oversubscribe the available CPU cores. Other than this,
there are no other mechanisms in place to prevent the processes from
starting additional threads.

Possible future support for multi-node tasks
--------------------------------------------

Currently, it is not possible to parallelise an MDANSE analysis
over multiple cluster nodes. Please let us know if you require
this option, so a higher priority can be given to this goal.
