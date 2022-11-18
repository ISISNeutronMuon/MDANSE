
.. _mdanse-cli:

Using MDANSE from command line
==============================

In some situations a graphical interface cannot be used for technical reasons (e.g., text-mode
connection to remote machines or Tk not available) or it is not the most convenient solution.
This occurs typically when one needs to perform a large number of similar calculations or when
the subset, deuteration or group selections that are to be used for a given analysis requires
more flexibility than the MDANSE GUI selection dialogs can offer. For these situations,
MDANSE provides a command-line interface that reads all input information from a single
input file.

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

The last way to use MDANSE from the command line is to use default
MDANSE scripts to interface with select parts of MDANSE GUI. This is
described in a :ref:`_mdanse-scripts`.

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

################################################################

# Job parameters #

################################################################

.. code-block:: python

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

.. code-block:: python
  
  dacf = REGISTRY['job']['dacf']()

# Run the analysis

.. code-block:: python
  
  dacf.run(parameters,status=True)

.. _mdanse-scripts-1:

MDANSE Scripts
--------------

When MDANSE is installed, multiple scripts come with it, installed into
the Scripts\\ directory on Windows and bin/ directory on Unix systems.
They can be run with python, for example

python mdanse_gui

or by themselves (this mode might be unavailable on Windows):

mdanse_gui

The following scripts come with MDANSE, each of which is described in
the following subsections, though more information about a script can
also be gained by calling the script with -h, e.g.,

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

-  **--version**

*Description:* displays the version of the installed MDANSE

*Expected arguments:* None

-  **--add-mmtk-def**

*Description:* adds the provided definition to the MMTK database

*Expected arguments:* code, typ, filename

*code*: the MMTK code for the molecule to register (i.e., HOH for water)

*typ*: the molecular type; one of amino_acid, molecule, nucleic_acid

*filename*: the path to the file that stores the MMTK definition of the
molecule being added

-  **--database** or **-d**

*Description:* displays chemical information about the provided element

*Expected arguments:* ename

*ename*: the name of a registered element

-  **--registry** or **-r**

*Description:* displays the contents of MDANSE classes registry

*Expected arguments:* None or interface

None → information on all classes is displayed

*interface*: the name of a class → information on only the subclasses of
the provided class is displayed

-  **--traj** or **-t**

*Description:* displays the chemical contents of a trajectory

*Expected arguments:* trajName

*trajName*: the name of a trajectory that has been loaded into MDANSE

-  **--jc**

*Description:* shows the status of the provided job

*Expected arguments:* filename

*filename*: the name (not path!) of a file representing an MDANSE job

-  **--jl**

*Description:* displays the job list

*Expected arguments:* None

-  **--jr**

*Description:* runs the provided MDANSE job(s)

*Expected arguments:* filename

*filename*: the path to an MDANSE python script

-  **--js**

*Description:* saves a job script for the provided job with default
parameters

*Expected arguments:* name

*name*: the name of a job (e.g., ccf for Current Correlation Function)

-  **--jt**

*Description:* saves a new job template

*Expected arguments:* classname, shortname

*classname*: a full name for the new job (e.g., TXTConverter)

*shortname*: a short name for the new job (e.g., txtc)

mdanse_elements_database
~~~~~~~~~~~~~~~~~~~~~~~~

This script has no options. When run, it opens the `Elements Database
Editor <#_Elements_database_editor>`__ GUI window.

mdanse_gui
~~~~~~~~~~

This script has no options. When run, it opens the main `MDANSE
GUI <#_The_main_window>`__ window.

mdanse_job
~~~~~~~~~~

This script is used to run a `job <#_Analysis>`__. It opens the GUI
window for the selected job without opening the main window. To do this,
two positional arguments are required (meaning only the values should be
placed after mdanse_job, no -- options like for the mdanse script).
These two arguments are as follows:

-  **job** – the short name of the job to be run (e.g., pdf for Pair
   Distribution Function).
-  **trajectory** – (only required for analyses; should be left blank
   for trajectory converters) the path to an MMTK trajectory file used
   for the job.

mdanse_periodic_table
~~~~~~~~~~~~~~~~~~~~~

This script has no options. When run, it opens the `Periodic
Table <#_Periodic_table_viewer>`__ GUI window.

mdanse_plotter
~~~~~~~~~~~~~~

This script has no options. When run, it opens the :ref:`2d3dplotter`
GUI window.

mdanse_ud_editor
~~~~~~~~~~~~~~~~

This script has no options. When run, it opens the `User Definitions
Editor <#_User_definition>`__ GUI window.

mdanse_units_editor
~~~~~~~~~~~~~~~~~~~

This script has no options. When run, it opens the Units Editor GUI
window.
