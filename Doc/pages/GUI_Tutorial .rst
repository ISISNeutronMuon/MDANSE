Tutorial 1: Using MDANSE Graphical User Interface
==================================================

Subsection 1: Introduction to MDANSE GUI
-----------------------------------------

Welcome to the tutorial on using MDANSE's Graphical User Interface (GUI).
In this tutorial, you will learn how to efficiently navigate through MDANSE's
user-friendly interface to open trajectories, configure analysis parameters,
and initiate calculations. Additionally, we will explore other useful actions
available within the GUI.

Sub-subsection 1: Opening Trajectories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MDANSE allows you to work with molecular dynamics trajectories conveniently.
To open a trajectory using MDANSE's GUI, follow these steps:

1. Launch MDANSE GUI: Start by opening MDANSE using the appropriate method for
your operating system (Windows, MacOS, or Linux). Refer to the respective
section in the user guide for detailed instructions on how to open MDANSE on
your platform.
2. Load Trajectory: Once MDANSE GUI is open, you can load a trajectory by
either:
   - Clicking on the "Load trajectory" button in the toolbar.
   - Using the File menu and selecting "Load data."
3. Select Trajectory File: A standard file browser window will appear.
Navigate to the location of your trajectory file (in HDF format), select it,
and click "Open."
4. Trajectory Tab: After loading the trajectory, a new tab representing the
trajectory will appear in the "Working panel." You can now inspect and work
with the loaded trajectory.

Sub-subsection 2: Configuring Analysis Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that we have a trajectory loaded, let's configure the parameters for the
analysis you wish to perform:

1. Select Trajectory: Ensure the trajectory you want to analyze is open in the
"Working panel."
2. Access Analysis Options: To configure analysis parameters, find the analysis
you want to perform in the "Plugins panel." Click the plus button next to the
analysis name to reveal its options.
3. Parameter Configuration: You will see various analysis-specific parameters.
Configure these parameters according to your analysis requirements. If you're
unsure about a specific parameter, you can usually find more information in
the MDANSE documentation or consult with your specific analysis documentation.

Sub-subsection 3: Starting Calculations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With your analysis parameters configured, it's time to initiate the calculation:

1. Initiate Analysis: Locate and click the "Run" button at the bottom of the
analysis configuration window.
2. Confirmation: You will likely receive a prompt asking if you want to proceed
with the analysis. Confirm and proceed.
3. Monitor Progress: The status of your analysis can be monitored in the "Jobs"
panel, which displays ongoing tasks. Keep an eye on this panel for updates on
the progress of your calculation.

Subsection 2: Additional Actions in MDANSE GUI
----------------------------------------------

In this section, we'll explore some additional actions you can perform within
MDANSE's GUI, including plotting analysis results, performing file conversions,
and viewing geometrical structures. We'll also touch upon creating input files
for command-line use and auto-start analysis scripts.

Sub-subsection 1: Plotting Analysis Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have completed an analysis, you may want to visualize the results.
MDANSE provides a simple way to plot these results:

1. Completed Analysis: Ensure that the analysis you want to visualize the results
of has been completed.
2. Access Plotter: Click on the "2D/3D Plotter" button in the toolbar.
3. Load Data: In the Plotter, load the analysis data you want to plot from the
list of available data variables.
4. Select Plot Type: Choose the type of plot you want to create (e.g., line plot,
2D image).
5. Plot Data: Click the "Plot in new window" button to generate and display the
selected plot.

Sub-subsection 2: File Conversions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MDANSE allows you to convert trajectory files into the HDF format. Here's how to
perform a file conversion:

1. Access Trajectory Converter: Click on the "Trajectory converter" button in
the toolbar.
2. Select Conversion Type: Choose the appropriate conversion option (e.g., from
another format to HDF).
3. Configure Conversion Parameters: Set the required parameters for the
conversion, such as input and output file paths.
4. Initiate Conversion: Click the "Run" button to start the conversion process.

Sub-subsection 3: Viewing Geometrical Structures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MDANSE enables you to visualize the geometrical structures within your
calculations:

1. Access Molecular Viewer: In the "Working panel," locate and open the
trajectory you want to visualize.
2. Access Molecular Viewer: Click on the "Molecular Viewer" button in the
toolbar.
3. Explore Geometries: The Molecular Viewer will display the geometrical
structures from your trajectory. You can interactively explore and analyze
these structures.

Sub-subsection 4: Creating Input Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MDANSE allows you to create input files for the command-line interface and
auto-start analysis scripts. These files serve as convenient starting points
for running new analyses directly from the command line:

1. Access Input File Creation: Click on the "Save analysis template" button in
the toolbar.
2. Configure Input Parameters: Specify the parameters for your analysis as
needed.
3. Save the Input File: Click the "Save" button to generate the input file. You
can use this file to set up and run new analyses from the command line.

Sub-subsection 5: Creating Auto-Start Analysis Scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Alternatively, you can also create an auto-start analysis Python script using
the same process. This script can automate the analysis setup and execution.

1. Access Auto-Start Script Generator: Click on the "Auto-Start Script
Generator" button in the toolbar.
2. Configure Analysis Parameters: Specify the analysis parameters you want to
include in the script. You can set up the same analysis configurations as you
would in the GUI.
3. Generate Script: Click the "Generate Script" button to create the Python
script.
4. Save the Script: Save the generated script to a location of your choice on
your computer.
5. Execute the Script: You can now execute the script from the command line to
start the analysis. The script will set up the analysis based on the parameters
you specified and initiate the calculation.

Auto-start analysis scripts provide a convenient way to automate repetitive
tasks and streamline your workflow when working with MDANSE.

Please note that the exact steps and options for creating auto-start scripts may
vary depending on the specific version and features of MDANSE, so it's advisable
to consult the MDANSE documentation or user guide for the most up-to-date
instructions and options.
