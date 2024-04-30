Using the MDANSE GUI
====================

Opening Trajectories
--------------------

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

   *Figure 8: Access Plotter Button*

3. **Load Data:** In the Plotter, load the analysis data you want to
   plot from the list of available data variables.

   *Figure 9: Load Data in Plotter*

4. **Select Plot Type:** Choose the type of plot you want to create
   (e.g., line plot, 2D image).

   *Figure 10: Select Plot Type*

5. **Plot Data:** Click the "Plot in a new window" button to generate
   and display the selected plot.

   *Figure 11: Plot Data*

File Conversions
----------------

1. **Access Trajectory Converter:** Click on the "Trajectory converter"
   button in the toolbar.


   *Figure 12: Access Trajectory Converter Button*

2. **Select Conversion Type:** Choose the appropriate conversion option
   (e.g., from another format to HDF).


   *Figure 13: Select Conversion Type*

3. **Configure Conversion Parameters:** Set the required parameters for
   the conversion, such as input and output file paths.

   *Figure 14: Configure Conversion Parameters*

4. **Initiate Conversion:** Click the "Run" button to start the
   conversion process.


   *Figure 15: Initiate Conversion*

Viewing Geometrical Structures
-------------------------------

MDANSE enables you to visualize the geometrical structures within your
calculations:

1. **Access Molecular Viewer:** In the "Working panel," locate and open
   the trajectory you want to visualize.

2. **Access Molecular Viewer:** Click on the "Molecular Viewer" button
   in the toolbar.


   *Figure 16: Access Molecular Viewer Button*

3. **Explore Geometries:** The Molecular Viewer will display the
   geometrical structures from your trajectory. You can interactively
   explore and analyze these structures.

   *Figure 17: Explore Geometries in Molecular Viewer*

Creating Input Files
--------------------

MDANSE allows you to create input files for the command-line interface
and auto-start analysis scripts. These files serve as convenient
starting points for running new analyses directly from the command
line:

1. **Access Input File Creation:** Click on the "Save analysis template"
   button in the toolbar.

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


   *Figure 21: Access Auto-Start Script Generator Button*

2. **Configure Analysis Parameters:** Specify the analysis parameters you
   want to include in the script. You can set up the same analysis
   configurations as you would in the GUI.


   *Figure 22: Configure Analysis Parameters*

3. **Generate Script:** Click the "Generate Script" button to create
   the Python script.


   *Figure 23: Generate Script Button*

4. **Save the Script:** Save the generated script to a location of your
   choice on your computer.


   *Figure 24: Save the Script*

5. **Execute the Script:** You can now execute the script from the
   command line to start the analysis. The script will set up the
   analysis based on the parameters you specified and initiate the
   calculation.


   *Figure 25: Execute the Script*

