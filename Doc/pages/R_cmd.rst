Using MDANSE Command Line Interface Information
================================================

Managing jobs using the MDANSE CLI
-----------------------------------
While the full list of the CLI options is listed below, here are
some useful examples that illustrate how the CLI should
be used.

+-----------------------------------------------+-----------------------------------------------------------------------------+
| Command                                       | Description                                                                 |
+===============================================+=============================================================================+
| ``mdanse -r job``                             | Display a list of different tasks that can be run in MDANSE.                |
+-----------------------------------------------+-----------------------------------------------------------------------------+
| ``mdanse --js dacf``                          | Create a template script for the Dipole AutoCorrelation Function. This      |
|                                               | script can then be edited to change the job parameters.                     |
+-----------------------------------------------+-----------------------------------------------------------------------------+
| ``mdanse --jr my_modified_script.py``         | Run the job defined in the file 'my_modified_script.py'.                    |
+-----------------------------------------------+-----------------------------------------------------------------------------+
| ``mdanse --jl``                               | Display the list of currently existing MDANSE jobs.                         |
+-----------------------------------------------+-----------------------------------------------------------------------------+

Important Commands
-------------------

This table lists various options, and for each option, the expected
arguments should be entered as space-separated values.

For example, to display the chemical contents of a trajectory, use the
following command:

```bash
mdanse --traj my_trajectory.dcd

+----------------------------------+-----------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| Option                           | Description                                                     | Expected Arguments                                                                                                                  |
+==================================+=================================================================+=====================================================================================================================================+
| :code:`--version`                | Displays the version of the installed MDANSE                    | None                                                                                                                                |
+----------------------------------+-----------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| :code:`--add-mmtk-def`           | Adds the provided definition to the MMTK database               | code, typ, filename (code: MMTK code for the molecule, typ: molecular type, filename: path to the file storing the MMTK definition) |
+----------------------------------+-----------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| :code:`--database` or :code:`-d` | Displays chemical information about the provided element        | ename (ename: name of a registered element)                                                                                         |
+----------------------------------+-----------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| :code:`--registry` or :code:`-r` | Displays the contents of MDANSE classes registry                | None or interface (None: information on all classes, interface: name of a class for specific class information)                     |
+----------------------------------+-----------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| :code:`--traj` or :code:`-t`     | Displays the chemical contents of a trajectory                  | trajName (trajName: name of a trajectory loaded into MDANSE)                                                                        |
+----------------------------------+-----------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| :code:`--jc`                     | Shows the status of the provided job                            | filename (filename: name of a file representing an MDANSE job)                                                                      |
+----------------------------------+-----------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| :code:`--jl`                     | Displays the job list                                           | None                                                                                                                                |
+----------------------------------+-----------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| :code:`--jr`                     | Runs the provided MDANSE job(s)                                 | filename (filename: path to an MDANSE python script)                                                                                |
+----------------------------------+-----------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| :code:`--js`                     | Saves a job script for the provided job with default parameters | name (name: name of a job, e.g., ccf for Current Correlation Function)                                                              |
+----------------------------------+-----------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| :code:`--jt`                     | Saves a new job template                                        | classname, shortname (classname: full name for the new job, shortname: short name for the new job)                                  |
+----------------------------------+-----------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+


Python interpreter information
------------------------------

When using MDANSE with different operating systems, you may need to
access the MDANSE Python interpreter. Below are instructions for
various platforms:

- **Windows**: Windows has a dedicated command line, which can be run
  using the `MDANSE_command_shell` file. This script sets environment
  variables so that the MDANSE Python becomes the default Python
  interpreter in that command line. You can use this dedicated command
  line for MDANSE-related tasks.

- **MacOS**: On MacOS, you should use the full path to the MDANSE
  Python interpreter, which is typically located at
  `/Applications/MDANSE.app/Contents/MacOS/python3` if MDANSE is
  installed in the default location. It's important to use the `python3`
  file on MacOS, as the other Python file may not have some required
  environmental variables set up.

- **Linux**: On Linux systems, you can use the full path to the MDANSE
  Python interpreter, which is usually located at
  `/usr/local/bin/python` if MDANSE is installed in the default
  location.

These pythons (as discussed in previous paragraph) can then be used to
run MDANSE python scripts like any other python script:

+---------------------------+----------------------------------------------------------+
| Operating System          | Command                                                  |
+===========================+==========================================================+
| Windows                   | `python script.py`                                       |
+---------------------------+----------------------------------------------------------+
| MacOS                     | `path/python3 script.py`                                 |
+---------------------------+----------------------------------------------------------+
| Linux                     | `path/python script.py`                                  |
+---------------------------+----------------------------------------------------------+
| All OS (Additional)       | - Install packages: `python -m pip install package_name` |
|                           | - Run short code: `python -c "print('Hello, World!')"`   |
|                           | - Activate REPL: `python`                                |
+---------------------------+----------------------------------------------------------+


MDANSE Included Scripts
------------------------

When MDANSE is installed, multiple scripts come with it, installed into
the Scripts\\ directory on Windows and bin/ directory on Unix systems.
They can be run with python, for example


To run the 'mdanse_gui' script, use the following command:

.. code-block:: bash

   python mdanse_gui

Additionally, on Unix systems, you can run the scripts directly, although
this mode might not be available on Windows:

.. code-block:: bash

   mdanse_gui

MDANSE instuctions on how to run scripts, are in the following table:

+---------------------------+---------------------------------------+------------------------------------------------------+
| Script Name               | How to Run                            | Description                                          |
+===========================+=======================================+======================================================+
| `mdanse`                  | `python mdanse` or `mdanse` (Unix)    | Interface with the MDANSE installation without       |
|                           |                                       | launching the GUI.                                   |
+---------------------------+---------------------------------------+------------------------------------------------------+
| `mdanse_elements_database`| `python mdanse_elements_database`     | Manage the elements database used in MDANSE.         |
+---------------------------+---------------------------------------+------------------------------------------------------+
| `mdanse_gui`              | `python mdanse_gui` or                | Launch the MDANSE graphical user interface.          |
|                           | `mdanse_gui` (Unix)                   |                                                      |
+---------------------------+---------------------------------------+------------------------------------------------------+
| `mdanse_job`              | `python mdanse_job` or                | Manage and run MDANSE analysis jobs.                 |
|                           | `mdanse_job` (Unix)                   |                                                      |
+---------------------------+---------------------------------------+------------------------------------------------------+
| `mdanse_periodic_table`   | `python mdanse_periodic_table` or     | Access the MDANSE periodic table.                    |
|                           | `mdanse_periodic_table` (Unix)        |                                                      |
+---------------------------+---------------------------------------+------------------------------------------------------+
| `mdanse_plotter`          | `python mdanse_plotter` or            | Perform data plotting tasks.                         |
|                           | `mdanse_plotter` (Unix)               |                                                      |
+---------------------------+---------------------------------------+------------------------------------------------------+
| `mdanse_ud_editor`        | `python mdanse_ud_editor` or          | Edit user-defined potential energy functions.        |
|                           | `mdanse_ud_editor` (Unix)             |                                                      |
+---------------------------+---------------------------------------+------------------------------------------------------+
| `mdanse_units_editor`     | `python mdanse_units_editor` or       | Edit units and unit systems used in MDANSE.          |
|                           | `mdanse_units_editor` (Unix)          |                                                      |
+---------------------------+---------------------------------------+------------------------------------------------------+

To obtain detailed information about any script, you can use
the `-h` flag, as demonstrated below:

.. code-block:: bash

   python mdanse_gui -h


Custom scripts
--------------

Here is an example of a custom script 

.. code-block:: python

  ################################################################
  
  # Job parameters #
  
  ################################################################
  
  
  parameters = {}
  parameters['atom_charges'] = ''
  parameters['atom_selection'] = None
  parameters['frames'] = (0, 2258, 1)
  parameters['output_files'] =
  (u'C:\\\\Users\\\\TACHYON\\\\Downloads\\\\output_NaF', (u'hdf',))
  parameters['running_mode'] = ('monoprocessor',)
  parameters['trajectory'] =
  u'C:\\\\Users\\\\TACHYON\\\\Downloads\\\\NaF.hdf'
  
  ################################################################
  
  # Setup and run the analysis #
  
  ################################################################
  
  # Create an instance of the class
  
  dacf = REGISTRY['job']['dacf']()

  # Run the analysis
  
  dacf.run(parameters,status=True)



