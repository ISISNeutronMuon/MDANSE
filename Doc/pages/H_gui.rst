How to Guide: Using MDANSE Graphical User Interface
===================================================

Introduction
------------

MDANSE (Molecular Dynamics Analysis for Neutron Scattering Experiments)
provides a user-friendly graphical user interface (GUI) for working with
molecular dynamics trajectories. This guide explains how to use the MDANSE
GUI for various tasks.

.. note::
   Before proceeding, make sure you have MDANSE installed on your system
   and have a trajectory file in HDF format ready for analysis.

**New MDANSE GUI**: The new MDANSE GUI is a separate Python package that
can be installed using pip. It is based on the QtPy interface, which will
use your Python bindings of choice to interface with the Qt libraries. The
interface should work as long as you have one of the following installed:

- PyQt5
- PyQt6
- PySide 2

More documentation of the GUI will follow as the interface becomes more
complete.

Index Descriptions
------------------

Below are descriptions and images that you'll encounter in this guide:

1. **Load Trajectory Button**
   ![Load Trajectory](images/load_trajectory.png)
   This button is used to open the file browser for loading trajectory files.

2. **Select Trajectory File**
   ![Select Trajectory File](images/select_trajectory.png)
   This image shows the file selection dialog where you choose your
   trajectory file in HDF format.

3. **Trajectory Tab in Working Panel**
   ![Trajectory Tab](images/trajectory_tab.png)
   The "Trajectory Tab" is displayed in the "Working Panel" after loading a
   trajectory. It represents the loaded trajectory data.

4. **Access Analysis Options**
   ![Access Analysis Options](images/access_analysis_options.png)
   This image illustrates how to access analysis options in the "Plugins
   Panel." These options allow you to configure specific analysis
   parameters.

5. **Parameter Configuration**
   ![Parameter Configuration](images/parameter_configuration.png)
   Here, you can see various analysis-specific parameters that you can
   configure based on your analysis requirements.

6. **Initiate Analysis**
   ![Initiate Analysis](images/initiate_analysis.png)
   The "Run" button is used to start the analysis calculation process.

7. **Monitor Progress**
   ![Monitor Progress](images/monitor_progress.png)
   This panel displays the ongoing tasks and progress status of your
   analysis calculations.


Opening Trajectories
--------------------

MDANSE allows you to conveniently open molecular dynamics trajectories.
Here's how to do it:

1. **Launch MDANSE GUI:** Start by opening MDANSE using the appropriate
   method for your operating system (Windows, MacOS, or Linux). Refer
   to the respective section in the user guide for detailed
   instructions on how to open MDANSE on your platform.

2. **Load Trajectory:** Once MDANSE GUI is open, you can load a
   trajectory by either:
   - Clicking on the "Load trajectory" button in the toolbar.
   - Using the File menu and selecting "Load data."

   [Index: Load Trajectory Button]

3. **Select Trajectory File:** A standard file browser window will
   appear. Navigate to the location of your trajectory file (in HDF
   format), select it, and click "Open."

   [Index: Select Trajectory File]

4. **Trajectory Tab:** After loading the trajectory, a new tab
   representing the trajectory will appear in the "Working panel." You
   can now inspect and work with the loaded trajectory.

   [Index: Trajectory Tab in Working Panel]

Configuring Analysis Parameters
-------------------------------

Now that we have a trajectory loaded, let's configure the parameters for
the analysis you wish to perform:

1. **Select Trajectory:** Ensure the trajectory you want to analyze is
   open in the "Working panel."

2. **Access Analysis Options:** To configure analysis parameters, find
   the analysis you want to perform in the "Plugins panel." Click the
   plus button next to the analysis name to reveal its options.

   [Index: Access Analysis Options]

3. **Parameter Configuration:** You will see various analysis-specific
   parameters. Configure these parameters according to your analysis
   requirements.

   [Index: Parameter Configuration]

Starting Calculations
---------------------

With your analysis parameters configured, it's time to initiate the
calculation:

1. **Initiate Analysis:** Locate and click the "Run" button at the
   bottom of the analysis configuration window.

   [Index: Initiate Analysis]

2. **Confirmation:** You will likely receive a prompt asking if you want
   to proceed with the analysis. Confirm and proceed.

3. **Monitor Progress:** The status of your analysis can be monitored in
   the "Jobs" panel, which displays ongoing tasks. Keep an eye on this
   panel for updates on the progress of your calculation.

   [Index: Monitor Progress]

   
Plotting Analysis Results
-------------------------

Once you have completed an analysis, you may want to visualize the
results. MDANSE provides a simple way to plot these results:

1. **Completed Analysis:** Ensure that the analysis you want to
   visualize the results of has been completed.

2. **Access Plotter:** Click on the "2D/3D Plotter" button in the
   toolbar.

   ![Access Plotter](images/access_plotter.png)
   *Figure 8: Access Plotter Button*

3. **Load Data:** In the Plotter, load the analysis data you want to
   plot from the list of available data variables.

   ![Load Data](images/load_data.png)
   *Figure 9: Load Data in Plotter*

4. **Select Plot Type:** Choose the type of plot you want to create
   (e.g., line plot, 2D image).

   ![Select Plot Type](images/select_plot_type.png)
   *Figure 10: Select Plot Type*

5. **Plot Data:** Click the "Plot in a new window" button to generate
   and display the selected plot.

   ![Plot Data](images/plot_data.png)
   *Figure 11: Plot Data*

File Conversions
----------------

MDANSE allows you to convert trajectory files into the HDF format.
Here's how to perform a file conversion:

1. **Access Trajectory Converter:** Click on the "Trajectory converter"
   button in the toolbar.

   ![Access Trajectory Converter](images/access_trajectory_converter.png)
   *Figure 12: Access Trajectory Converter Button*

2. **Select Conversion Type:** Choose the appropriate conversion option
   (e.g., from another format to HDF).

   ![Select Conversion Type](images/select_conversion_type.png)
   *Figure 13: Select Conversion Type*

3. **Configure Conversion Parameters:** Set the required parameters for
   the conversion, such as input and output file paths.

   ![Configure Conversion Parameters](images/configure_conversion_parameters.png)
   *Figure 14: Configure Conversion Parameters*

4. **Initiate Conversion:** Click the "Run" button to start the
   conversion process.

   ![Initiate Conversion](images/initiate_conversion.png)
   *Figure 15: Initiate Conversion*

Viewing Geometrical Structures
-------------------------------

MDANSE enables you to visualize the geometrical structures within your
calculations:

1. **Access Molecular Viewer:** In the "Working panel," locate and open
   the trajectory you want to visualize.

2. **Access Molecular Viewer:** Click on the "Molecular Viewer" button
   in the toolbar.

   ![Access Molecular Viewer](images/access_molecular_viewer.png)
   *Figure 16: Access Molecular Viewer Button*

3. **Explore Geometries:** The Molecular Viewer will display the
   geometrical structures from your trajectory. You can interactively
   explore and analyze these structures.

   ![Explore Geometries](images/explore_geometries.png)
   *Figure 17: Explore Geometries in Molecular Viewer*

Creating Input Files
--------------------

MDANSE allows you to create input files for the command-line interface
and auto-start analysis scripts. These files serve as convenient
starting points for running new analyses directly from the command
line:

1. **Access Input File Creation:** Click on the "Save analysis template"
   button in the toolbar.

   ![Access Input File Creation](images/access_input_file_creation.png)
   *Figure 18: Access Input File Creation Button*

2. **Configure Input Parameters:** Specify the parameters for your
   analysis as needed.

   ![Configure Input Parameters](images/configure_input_parameters.png)
   *Figure 19: Configure Input Parameters*

3. **Save the Input File:** Click the "Save" button to generate the
   input file. You can use this file to set up and run new analyses
   from the command line.

   ![Save the Input File](images/save_input_file.png)
   *Figure 20: Save the Input File*

Creating Auto-Start Analysis Scripts
------------------------------------

Alternatively, you can also create an auto-start analysis Python script
using the same process. This script can automate the analysis setup and
execution:

1. **Access Auto-Start Script Generator:** Click on the "Auto-Start
   Script Generator" button in the toolbar.

   ![Access Auto-Start Script Generator](images/access_auto_start_script_generator.png)
   *Figure 21: Access Auto-Start Script Generator Button*

2. **Configure Analysis Parameters:** Specify the analysis parameters you
   want to include in the script. You can set up the same analysis
   configurations as you would in the GUI.

   ![Configure Analysis Parameters](images/configure_analysis_parameters.png)
   *Figure 22: Configure Analysis Parameters*

3. **Generate Script:** Click the "Generate Script" button to create
   the Python script.

   ![Generate Script](images/generate_script.png)
   *Figure 23: Generate Script Button*

4. **Save the Script:** Save the generated script to a location of your
   choice on your computer.

   ![Save the Script](images/save_script.png)
   *Figure 24: Save the Script*

5. **Execute the Script:** You can now execute the script from the
   command line to start the analysis. The script will set up the
   analysis based on the parameters you specified and initiate the
   calculation.

   ![Execute the Script](images/execute_script.png)
   *Figure 25: Execute the Script*

Auto-start analysis scripts provide a convenient way to automate
repetitive tasks and streamline your workflow when working with MDANSE.

Please note that the exact steps and options for creating auto-start
scripts may vary depending on the specific version and features of
MDANSE, so it's advisable to consult the MDANSE documentation or user
guide for the most up-to-date instructions and options.
