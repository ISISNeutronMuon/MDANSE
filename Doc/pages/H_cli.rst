Using the MDANSE CLI
====================

MDANSE (Molecular Dynamics Analysis and Visualization) software offers a
versatile and powerful command line interface (CLI) alongside its
graphical user interface (GUI). While the GUI provides an interactive and
user-friendly environment for analysis, the command line interface is a
valuable alternative that offers distinct advantages. In this section of
the user guide, we will explore why the MDANSE command line interface is
useful and discuss its various features.

Additionally, for important commands and usage instructions on the command
line (CMD), please refer to the **Command Line Reference** section in the
MDANSE documentation.

Advantages of Using the MDANSE Command Line Interface
-----------------------------------------------------

**Automation and Scripting:** The CLI allows users to automate repetitive
analysis tasks by creating scripts or batch files. This is particularly
useful for users who need to perform the same analysis on multiple datasets,
saving time and effort. For example, you have a dataset of protein
simulations, and you want to calculate the root mean square deviation
(RMSD) for each frame in the trajectory. Instead of manually loading each
trajectory file into the GUI and setting up the analysis for each file, you
can create a script that automates this process. This approach enhances
efficiency, ensures methodological consistency, and eliminates the need for
manual repetition.

**Batch Processing:** MDANSE CLI supports batch processing, enabling users
to analyze a series of datasets sequentially or in parallel. This feature
is beneficial when working with large datasets or conducting extensive
parameter sweeps. For example, imagine you have ten different molecular
dynamics simulations, and you want to calculate the radial distribution
function (RDF) for each of them with varying parameters. You can create a
batch processing script that iterates through each simulation, applies
different parameter settings, and generates RDF plots. This allows you to
analyze all simulations efficiently without manual intervention.

**Remote and Cluster Computing:** The command line interface is well-suited
for remote and cluster computing environments. Users can execute MDANSE
analysis tasks on remote servers or high-performance computing clusters,
leveraging their computational resources. Suppose you have a massive dataset
requiring substantial computational resources for analysis. In that case,
MDANSE CLI enables you to submit analysis tasks to a remote
high-performance computing cluster. This strategy offloads the computational
workload to remote servers, optimally utilizing cluster resources and
facilitating concurrent execution of multiple simulations. This is
especially useful when rapid analysis of large datasets or computationally
intensive calculations is necessary, exceeding the capabilities of a local
machine.

**Reproducibility:** Using scripts with the CLI ensures analysis
reproducibility. Scripted workflows document steps and parameters, making
it easier to recreate results or share with collaborators. By employing
scripts with the MDANSE CLI, you create a comprehensive workflow that
meticulously documents each step of the analysis, encompassing parameter
settings and data processing. This practice guarantees that you can easily
replicate the analysis, enhancing transparency and facilitating
collaborative research efforts. For example, you have conducted an analysis
of a complex molecular system using MDANSE, and you want to share your
findings with a colleague. Instead of sharing a set of GUI-driven steps,
you can provide them with a script that contains all the analysis steps
and parameters used. This script ensures that your colleague can reproduce
your analysis exactly, promoting transparency and collaboration.

Managing jobs using the MDANSE CLI
-----------------------------------

The MDANSE Command Line Interface (CLI) provides robust capabilities for
managing and monitoring various analysis jobs. Whether you're running
molecular dynamics simulations, calculating properties, or conducting
complex analyses, the CLI allows you to efficiently handle and keep track
of your tasks.

With the MDANSE CLI, you can submit, monitor, and control the execution of
analysis jobs effortlessly. It offers features like job status checking,
error handling, and detailed logging, ensuring that you have full visibility
into the progress and results of your analyses. Whether you're dealing with
single tasks or complex workflows, the MDANSE CLI simplifies job management,
making it an indispensable tool for researchers and analysts.

Additionally, for important commands and usage instructions related to
managing and monitoring jobs using the MDANSE CLI, please refer to the
**Job Management Reference** section in the MDANSE documentation.

MDANSE Included Scripts
------------------------

When you install MDANSE, it comes bundled with several useful scripts. These
scripts are located in the `Scripts\` directory on Windows and the `bin/`
directory on Unix systems.

In the following table, which will describe some of these scripts in
more detail.

+--------------------------+-------------------------------------------------------------------+
| Script                   | Description                                                       |
+==========================+===================================================================+
| `mdanse`                 | The main MDANSE script that serves as the entry point for various |
|                          | MDANSE functionalities.                                           |
+--------------------------+-------------------------------------------------------------------+
|`mdanse_elements_database`| Provides access to the MDANSE elements database, allowing users   |
|                          | to retrieve information about chemical elements.                  |
+--------------------------+-------------------------------------------------------------------+
| `mdanse_gui`             | Launches the graphical user interface (GUI) for MDANSE, offering  |
|                          | an interactive and user-friendly environment for molecular        |
|                          | dynamics analysis and visualization.                              |
+--------------------------+-------------------------------------------------------------------+
| `mdanse_job`             | Manages MDANSE job execution, facilitating the execution of       |
|                          | analysis tasks, simulations, and other computational tasks within |
|                          | MDANSE.                                                           |
+--------------------------+-------------------------------------------------------------------+
| `mdanse_periodic_table`  | Displays the periodic table with detailed information on chemical |
|                          | elements, including atomic numbers, symbols, atomic weights, and  |
|                          | more.                                                             |
+--------------------------+-------------------------------------------------------------------+
| `mdanse_plotter`         | Allows for data plotting and visualization within MDANSE, enabling|
|                          | users to create various plots and graphs for analyzing simulation |
|                          | results.                                                          |
+--------------------------+-------------------------------------------------------------------+
| `mdanse_ud_editor`       | Opens the MDANSE units definition editor, providing a tool for    |
|                          | defining and managing units used in MDANSE simulations and        |
|                          | analyses.                                                         |
+--------------------------+-------------------------------------------------------------------+
| `mdanse_units_editor`    | Opens the MDANSE units editor, which allows users to define and   |
|                          | manage units used in MDANSE, ensuring consistency and accuracy in |
|                          | simulations and analyses.                                         |
+--------------------------+-------------------------------------------------------------------+

For more in-depth information on running and utilizing these scripts, please
consult the **Technical References** provided in the MDANSE documentation.

Custom Scripts
---------------

It is possible to edit MDANSE scripts or even write new ones from
scratch. To run an analysis using the MDANSE python library, two steps
are necessary; first, set up the parameters that the analysis requires
(equivalent to filling in the fields in the GUI), then running the
analysis (equivalent to clicking the Run button). For both of these, it
is necessary to understand how the analysis’ class works. This can be
done by reading MDANSE documentation, either by clicking the analysis’
Help button or by clicking the `Open MDANSE API <#open_mdanse_api>`__
button on the toolbar.

For more in-depth information on running and utilizing custom scripts, please
consult the **Technical References** provided in the MDANSE documentation.


Run a Basic MDANSE Analysis Using the CLI
-----------------------------------------

**Purpose:**

This guide explains how to perform a basic MDANSE analysis from the command line.

1. **Open Terminal or Command Prompt:**
   - Open your computer's terminal or command prompt.

2. **Navigate to MDANSE Directory:**
   - Use the ``cd`` command to go to the MDANSE installation directory. If it's not in your system's PATH, provide the full path to the MDANSE directory.
     Example:

     .. code-block:: bash

        cd /path/to/MDANSE

3. **List Available MDANSE Jobs:**
   - To see available analysis tasks, type:

     .. code-block:: bash

        mdanse -r job

4. **Run a Basic Analysis:**
   - Execute an analysis script with this command:

     .. code-block:: bash

        mdanse --jr my_basic_script.py

     Replace ``my_basic_script.py`` with your script's filename.

5. **Check Results:**
   - After the analysis finishes, review the results in the specified output directory, typically defined in your script.

Running Jobs Using the CLI
--------------------------

**Purpose:**

This guide explains how to run MDANSE jobs via the command line interface (CLI) for various analysis tasks.

1. **Open Terminal or Command Prompt:**
   - Begin by opening your computer's terminal or command prompt.

2. **Navigate to MDANSE Directory:**
   - Use the ``cd`` command to go to the MDANSE installation directory. If it's not in your system's PATH, provide the full path to the MDANSE directory.
     Example:

     .. code-block:: bash

        cd /path/to/MDANSE

3. **List Available MDANSE Jobs:**
   - To see available analysis tasks, type:

     .. code-block:: bash

        mdanse -r job

4. **Run a Basic MDANSE Analysis Using the CLI:**
   - Execute a basic MDANSE analysis using a command like this:

     .. code-block:: bash

        mdanse --jr my_basic_script.py

     Replace ``my_basic_script.py`` with your script's filename.

5. **Check the Results:**
   - After the analysis completes, check the results in the specified output directory.

6. **Customize MDANSE Job Parameters Using CLI:**
   - Generate a template script for your analysis using a command like this:

     .. code-block:: bash

        mdanse --js job_name

     Replace ``job_name`` with the specific analysis task you want to customize.

7. **Open the generated script in a text editor.**

8. **Import the necessary MDANSE modules at the beginning of the script.**

9. **Define the job parameters as an empty dictionary.**

   Example of importing modules and defining job parameters:

   .. code-block:: python

      # Import the necessary MDANSE modules
      from MDANSE.Core.MDANSE import REGISTRY

      # Define the job parameters
      parameters = {}

10. **Customize the parameters within the script to tailor the analysis to your research needs.**

    Example of customizing job parameters:

    .. code-block:: python

       # Set the atom charges if applicable (e.g., '1 2 0' for hydrogen, helium, and no charge)
       parameters['atom_charges'] = '1 2 0'

       # Define atom selection if needed (e.g., select atoms by index)
       parameters['atom_selection'] = '1-100'  # Select atoms with indices from 1 to 100

       # Specify the frames for analysis (e.g., from frame 0 to 500 with a step of 1)
       parameters['frames'] = (0, 500, 1)

       # Set the output directory and format (e.g., HDF)
       parameters['output_files'] = ('/path/to/custom_output_directory', ('hdf',))

       # Choose the running mode (e.g., 'multiprocessor' for multi-core analysis)
       parameters['running_mode'] = ('multiprocessor',)

       # Provide the path to the trajectory file in HDF format
       parameters['trajectory'] = '/path/to/custom_trajectory_file.hdf'

11. **Run the customized analysis script using this command:**

    .. code-block:: bash

       mdanse --jr my_custom_script.py

    Replace ``my_custom_script.py`` with your script's filename.

12. **After the analysis completes, examine the results in the specified output directory, typically defined within your customized script.**
