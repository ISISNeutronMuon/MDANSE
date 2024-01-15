How to Guide: Using the Command Line Interface (CLI)
====================================================

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
