.. _installation-tutorial:

Installing MDANSE
=================

MDANSE can be installed by following these steps:

Create Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create your Python virtual environment for MDANSE use ``venv`` or ``virtualenv``.
Open a terminal or command prompt.

**Navigate to Your Project Directory (Optional)**: If you have a specific
project directory where you want to work with MDANSE, navigate to that
directory using the ``cd`` command. For example:

.. code-block:: bash

   cd path/to/your/project/directory

**Create a Virtual Environment**: To create a virtual environment named
``mdanse``, use the following command:

.. code-block:: bash

   python3 -m venv mdanse

.. _venv_for_mdanse:

Activate Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After creating the virtual environment, you need to activate it
to use MDANSE within this isolated environment. The
activation command varies by operating system:

- On macOS and Linux:

  .. code-block:: bash

     source mdanse/bin/activate

- On Windows:

  .. code-block:: console

     mdanse\Scripts\activate

Install MDANSE Package
~~~~~~~~~~~~~~~~~~~~~~

Use ``pip`` to install the MDANSE package from the specified GitHub repository:

.. code-block:: bash

   pip install MDANSE

The MDANSE package contains all the code needed to perform trajectory conversion
and analysis using MDANSE, but none of the visualisation tools.

Optional Dependencies
'''''''''''''''''''''

If you intend to use MDANSE in the command line rather than in the GUI, you can
include optional dependencies targeted specifically at Command Line Interface (CLI)
users:

.. code-block:: bash

   pip install "MDANSE[cli]"

At the moment, this is equivalent to running ``pip install MDANSE tqdm``.
You can run MDANSE scripts in the command line independent of whether ``tqdm``
is installed or not, but if ``tqdm`` is present, it will be used to provide
a CLI progress bar for MDANSE jobs.

Install MDANSE_GUI Package
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Similarly, install the MDANSE_GUI package using ``pip``:

.. code-block:: bash

   pip install MDANSE_GUI

From now on, the ``mdanse_gui`` command will be available to start
the graphical interface of MDANSE, which makes it easier to create
valid inputs for different analysis types.

Run MDANSE_GUI
~~~~~~~~~~~~~~

You can now start using MDANSE by running the following command:

.. code-block:: bash

   mdanse_gui

This will launch the MDANSE graphical user interface (GUI),
and you can start using MDANSE for your analysis.

Make sure that you are starting MDANSE from a shell/console
in which you have activated the Python virtual environment,
as described above in section :ref:`venv_for_mdanse`.

Run MDANSE in the shell
~~~~~~~~~~~~~~~~~~~~~~~

As an alternative to using the GUI, MDANSE package provides
a script that can be used in the command line. To find out
more about the valid input commands, type

.. code-block:: bash

   mdanse -h

This will show the help message of the MDANSE CLI and give
you the list of available subcommands.

The currently implemented commands allow you to display the
contents of MDANSE trajectory files (.mdt) and the contents
of MDANSE analysis results (.mda), view the atom database
entries for different chemical elements, and to create
Python scripts for trajectory conversion and analysis.
At the moment the scripts contain only default values which
then need to be replaced with values relevant to the input
files you intend to use, so creating scripts in the GUI
is still easier for now.

Make sure that you are starting MDANSE from a shell/console
in which you have activated the Python virtual environment,
as described above in section :ref:`venv_for_mdanse`.

MDANSE Scripts
~~~~~~~~~~~~~~

If you intend to run your analysis on a remote platform
(e.g. a cluster), most likely you will have limited options
of using the GUI there. However, you can still prepare
a script using MDANSE_GUI on your own computer, save it
and transfer it to the other computer to run the analysis
there. You will need to change the file paths in the script,
but all the other parameters should be transferable. One 
of the design principles of MDANSE 2 is that the scripts
should not depend on any settings stored locally on
a specific computer, but should instead contain all the
information needed to run a specific analysis type.

Alternatively, you can create the scripts using the CLI.
Examples of valid commands include

.. code-block:: bash

   $ mdanse convert --help  # Basic explanation of valid commands.
   $ mdanse convert -l  # Shows the list of available converters.
   $ mdanse convert CP2K -o convert_cp2k.py  # Saves a template script for the CP2K converter.

or

.. code-block:: bash

   $ mdanse analysis --help  # Valid commands for analysis jobs.
   $ mdanse analysis -l  # Shows the list available analysis tasks
   $ mdanse analysis DensityOfStates -o mdanse_dos.py  # Saves a template script for the DOS analysis.

for converter and analysis runs. You can start by just running
:code:`mdanse --help` to get more information on what else you can
do in the CLI. The main drawback compared to the GUI approach is that
the scripts output by the CLI will not contain reasonable starting values
for your specific files and you will need to set all the parameters
manually.
