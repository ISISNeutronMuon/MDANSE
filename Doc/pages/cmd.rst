
.. _mdanse-cli:

Using MDANSE Command Line Interface
===================================

The MDANSE analysis tasks can exist and operate independent of
a graphical interface. For this reason, the MDANSE command line
interface is a valid alternative to the MDANSE GUI.

Managing jobs using the MDANSE CLI
----------------------------------

While the full list of the CLI options is listed below, here are
some useful examples that illustrate how the CLI should
be used.

.. code-block:: console

  mdanse -r job

will display a list of different tasks that can be run in MDANSE.

.. code-block:: console

  mdanse --js dacf

will create a template script for the Dipole AutoCorrelation Function.
This script can then be edited to change the job parameters.

.. code-block:: console

  mdanse --jr my_modified_script.py

will run the job defined in the file 'my_modified_script.py'.

.. code-block:: console

  mdanse --jl

will display the list of currently existing MDANSE jobs.

Congratulations! Using these four lines (and a text editor) you
just performed an analysis task on a trajectory, and confirmed
that your task has executed correctly.

Python interpreter information
------------------------------

Windows, has a dedicated command line which can be run using
MDANSE_command_shell file, which sets some environment variables so
that, in it, MDANSE python is the default python. On other platforms,
you have to use a normal terminal and use MDANSE python by calling its
full path, which should be (if MDANSE is in default installation
location) `/Applications/MDANSE.app/Contents/MacOS/python2` on MacOS, and
`/usr/local/bin/python` on Linux systems. Please only use the
**python2** file on MacOS, the other python file does not have some
environmental variables set up.

These pythons (as discussed in previous paragraph) can then be used to
run MDANSE python scripts like any other python script:

`python script.py` -- Windows

`path/python2 script.py` -- MacOS

`path/python script.py` -- Linux

The python can also be used to install other packages, run short code
(using the -c option), or to activate python REPL.

Custom scripts
--------------

It is possible to edit MDANSE scripts or even write new ones from
scratch. To run an analysis using the MDANSE python library, two steps
are necessary; first, set up the parameters that the analysis requires
(equivalent to filling in the fields in the GUI), then running the
analysis (equivalent to clicking the Run button). For both of these, it
is necessary to understand how the analysis’ class works. This can be
done by reading MDANSE documentation, either by clicking the analysis’
Help button or by clicking the `Open MDANSE API <#open_mdanse_api>`__
button on the toolbar. An example script is below.

.. code-block:: python

  ################################################################
  
  # Job parameters #
  
  ################################################################
  
  
  parameters = {}
  parameters['atom_charges'] = ''
  parameters['atom_selection'] = None
  parameters['frames'] = (0, 2258, 1)
  parameters['output_files'] =
  (u'C:\\\\Users\\\\TACHYON\\\\Downloads\\\\output_NaF', (u'netcdf',))
  parameters['running_mode'] = ('monoprocessor',)
  parameters['trajectory'] =
  u'C:\\\\Users\\\\TACHYON\\\\Downloads\\\\NaF.nc'
  
  ################################################################
  
  # Setup and run the analysis #
  
  ################################################################
  
  # Create an instance of the class
  
  dacf = REGISTRY['job']['dacf']()

  # Run the analysis
  
  dacf.run(parameters,status=True)

.. _mdanse-scripts-1:

MDANSE Scripts
--------------

When MDANSE is installed, multiple scripts come with it, installed into
the Scripts\\ directory on Windows and bin/ directory on Unix systems.
They can be run with python, for example

.. code-block:: console

  python mdanse_gui

or by themselves (this mode might be unavailable on Windows):

.. code-block:: console

  mdanse_gui

The following scripts come with MDANSE, each of which is described in
the following subsections, though more information about a script can
also be gained by calling the script with -h, e.g.,

.. code-block:: console

  python mdanse_gui -h

-  mdanse
-  mdanse_elements_database
-  mdanse_gui
-  mdanse_job
-  mdanse_periodic_table
-  mdanse_plotter
-  mdanse_ud_editor
-  mdanse_units_editor

mdanse
~~~~~~

This script is used to interface with the current installation of MDANSE
without running the GUI. It has the following options, where the
expected arguments should be inputted after the option as
space-separated values:

:code:`--version`

- *Description:* displays the version of the installed MDANSE
- *Expected arguments:* None

:code:`--add-mmtk-def`

- *Description:* adds the provided definition to the MMTK database
- *Expected arguments:* code, typ, filename
- *code*: the MMTK code for the molecule to register (i.e., HOH for water)
- *typ*: the molecular type; one of amino_acid, molecule, nucleic_acid
- *filename*: the path to the file that stores the MMTK definition of the molecule being added

:code:`--database` or :code:`-d`

- *Description:* displays chemical information about the provided element
- *Expected arguments:* ename
- *ename*: the name of a registered element

:code:`--registry` or :code:`-r`

- *Description:* displays the contents of MDANSE classes registry
- *Expected arguments:* None or interface

  - None -> information on all classes is displayed
  - *interface*: the name of a class -> information on only the subclasses of the provided class is displayed

:code:`--traj` or :code:`-t`

- *Description:* displays the chemical contents of a trajectory
- *Expected arguments:* trajName
- *trajName*: the name of a trajectory that has been loaded into MDANSE

:code:`--jc`

- *Description:* shows the status of the provided job
- *Expected arguments:* filename

  - *filename*: the name (not path!) of a file representing an MDANSE job

:code:`--jl`

- *Description:* displays the job list
- *Expected arguments:* None

:code:`--jr`

- *Description:* runs the provided MDANSE job(s)
- *Expected arguments:* filename

  - *filename*: the path to an MDANSE python script

:code:`--js`

- *Description:* saves a job script for the provided job with default parameters
- *Expected arguments:* name

  - *name*: the name of a job (e.g., ccf for Current Correlation Function)

:code:`--jt`

- *Description:* saves a new job template
- *Expected arguments:* classname, shortname

  - *classname*: a full name for the new job (e.g., TXTConverter)
  - *shortname*: a short name for the new job (e.g., txtc)

