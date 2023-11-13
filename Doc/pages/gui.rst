
.. _section-7:

Section 7: Navigating the MDANSE GUI
=====================================

The MDANSE Graphical User Interface (GUI) is the central hub for
performing various actions, including opening trajectories, configuring
analysis parameters, and visualizing results. This section provides an
overview of how to effectively utilize the MDANSE GUI.

7.1. Key Actions in the MDANSE GUI
-----------------------------------

Through the MDANSE GUI, you can perform a range of essential tasks:

- Opening Trajectories: Begin by opening a trajectory, which serves as
  the foundation for your analyses.
- Configuring Analysis: Specify the parameters for the analysis you wish
  to perform, tailoring it to your research needs.
- Initiating Calculations: Start the calculation process to obtain
  insightful results.
- Plotting Analysis Results: Visualize and interpret the outcomes of your
  analysis through plots and graphs.
- File Conversions: Perform file conversions, enabling compatibility with
  different formats.
- Geometrical Structure Visualization: Explore the geometrical structure
  of your calculations for deeper insights.
- Creating Input Files and Scripts: Generate input files for the
  command-line interface or auto-start analysis Python scripts directly
  from the GUI.

7.2. Operating the MDANSE GUI
-------------------------------

The MDANSE GUI offers user-friendly interaction methods, including the
following:

- Double-Click: You can double-click various objects within the GUI to
  trigger actions.
- Drag & Drop: An equivalent Drag & Drop mechanism is also available.
  Simply drag your trajectory into the main GUI window, and a tab will
  be created. Drop an analysis operation into the tab to perform the
  analysis on the trajectory. Drop the Molecular Viewer into the tab to
  visualize the trajectory.

7.3. Starting the MDANSE GUI
-------------------------------

The MDANSE GUI can be initiated on different platforms as follows:

7.3.1. Windows
---------------

- If you selected the option to create a desktop shortcut during
  installation, you can use that shortcut to start MDANSE.
- Alternatively, navigate to the folder where MDANSE is installed
  (default path: C:\Program Files\MDANSE). There, you can double-click
  the file named "MDANSE" with the MDANSE icon.
- To start MDANSE from the command line, execute the batch file
  "MDANSE_launcher.bat." Ensure you use quotation marks if the path
  contains spaces.

7.3.2. MacOS
-------------

- If you installed MDANSE normally, you can find the MDANSE icon in the
  Applications folder and start it like any other app. Note that you may
  need to adjust your system settings due to Apple's security measures
  (see Ref [Ref4] for a guide).
- To start MDANSE GUI from the terminal, use the following command
  (replace /Applications if you installed MDANSE elsewhere):

  .. code-block:: bash

     /Applications/MDANSE.app/Contents/MacOS/MDANSE

7.3.3. Linux
-------------

- If your Linux distribution has an applications menu, you should find
  an MDANSE icon there for launching the GUI.
- If not, you can start MDANSE from the terminal using the following
  command:

  .. code-block:: bash

     mdanse_gui

  If this command doesn't work, locate the MDANSE installation directory.
  By default, it should be in /usr/local. Search for the mdanse_gui script
  within /usr/local/bin. Once found, run the following command:

  .. code-block:: bash

     /usr/local/bin/mdanse_gui

The MDANSE GUI serves as a versatile platform for performing a wide range
of analyses and visualizations in a user-friendly manner, enhancing your
research capabilities.

7.4. Standalone GUI Elements
---------------------------

Certain parts of the MDANSE GUI can be initiated independently, offering
specialized functionality:

7.4.1. mdanse_elements_database
-------------------------------

- This script opens the Elements Database Editor GUI window.
- It does not require any additional options.

7.4.2. mdanse_gui
-------------------

- This script opens the main MDANSE GUI window.
- It does not require any additional options.

7.4.3. mdanse_job
-------------------

- This script is used to run a specific job, opening the GUI window for
  the selected job without launching the main window.
- It requires two positional arguments:
  - job: The short name of the job to be executed (e.g., "pdf" for Pair
    Distribution Function).
  - trajectory (only required for analyses): The path to an MMTK
    trajectory file used for the job.

7.4.4. mdanse_periodic_table
-------------------------------

- This script opens the Periodic Table GUI window.

7.4.5. mdanse_plotter
-----------------------

- This script opens the 2D/3D Plotter GUI window.

7.4.6. mdanse_ud_editor
------------------------

- This script opens the User Definitions Editor GUI window.

7.4.7. mdanse_units_editor
---------------------------

- This script opens the Units Editor GUI window.
- It does not require any additional options.

7.5. The Main Window
---------------------

Below is an image of the main MDANSE GUI window with annotated
descriptions of its key components:

1. File Menu: Handles file manipulation, including loading HDF trajectories
   and converting other trajectories into the HDF file format.
2. View Menu: Allows you to show or hide various parts of MDANSE.
3. Help Menu: Provides access to files for better understanding MDANSE and
   its underlying theory.
4. Load Trajectory Button: Loads an HDF trajectory.
5. Periodic Table Viewer: Opens a periodic table containing constants and
   data used by MDANSE for calculations.
6. Elements Database Editor: Allows you to modify the atomic constants used
   by MDANSE.
7. 2D/3D Plotter: Launches a window for plotting calculated data and
   formatting plots.
8. User Definitions Editor: Opens a window to view definitions created for
   each trajectory (more on definitions in Selections).
9. Units Editor: Opens a window to manage units used in MDANSE.
10. MDANSE Classes Framework: Permits access to documentation for MDANSE
    classes, useful for command-line usage.
11. Save Analysis Template: Creates a new analysis available in My jobs
    inside the Plugins panel for running like native analyses.
12. Open MDANSE API: Opens MDANSE documentation in a browser, similar to
    MDANSE Classes Framework.
13. Open MDANSE Website: Opens the MDANSE website in a browser.
14. About: Launches a window with basic information about your installed
    MDANSE version.
15. Bug Report: Opens your default mail application or directs you to create
    an issue on MDANSE GitHub for reporting issues.
16. Quit MDANSE: Closes the MDANSE window.
17. Data Panel: Contains loaded HDF files and enables file manipulation.
18. Plugins Panel: Provides various options for the selected trajectory.
19. Working Panel: Displays opened trajectories for inspection.
20. Logger: Shows messages generated by MDANSE, including errors and
    information messages.
21. Console: Acts as a Python shell, allowing interaction with bundled modules
    (importing required).
22. Jobs: Displays the status of ongoing jobs, including analysis progress
    monitoring.

These components collectively create a versatile environment for performing
advanced analyses and visualizations within MDANSE's GUI.

7.6. The Main Window
---------------------

When you access the Data menu, you'll find the following options:

1. File Menu: Handles HDF file manipulation, loading, and conversion.
2. View Menu: Customizes the MDANSE interface.
3. Help Menu: Provides resources for understanding MDANSE and its theory.
4. Load Trajectory Button: Quickly loads HDF trajectories for analysis.
5. Periodic Table Viewer: Accesses a comprehensive periodic table for MDANSE
   calculations.
6. Elements Database Editor: Modifies atomic constants for MDANSE calculations.
7. 2D/3D Plotter: Opens a plotting window for data visualization.
8. User Definitions Editor: Reviews trajectory definitions.
9. Units Editor: Manages MDANSE units.
10. MDANSE Classes Framework: Offers command-line documentation.
11. Save Analysis Template: Allows you to create a new analysis, which will be
    available in My Jobs inside the Plugins panel for running like native analyses.
12. Open MDANSE API: Opens MDANSE documentation in a web browser, similar to
    the MDANSE Classes Framework.
13. Open MDANSE Website: Opens the MDANSE website in a web browser.
14. About: Displays basic MDANSE information.
15. Bug Report: Reports issues.
16. Quit MDANSE: Closes MDANSE.


7.6.1. Load Data
----------------

This option allows you to select an MMTK HDF file. Clicking the Load Data
button opens a standard (platform-specific) file browser, similar to the
one shown below:

[Image: File Browser]

Use it as you normally would, and the selected file will appear in the
Data Panel. While the file browser suggests that you can load the MVI trace
file format, please note that this feature is not currently implemented.
Therefore, only load HDF files generated using MMTK or MMTK-based software.
If you have a trajectory from another source, it must first be converted.
For more details on converting trajectories, please refer to the next section.

7.6.2. Trajectory Converter
---------------------------

This option enables the conversion of a trajectory derived from a non-MMTK-based
program to the HDF MMTK trajectory format. Hovering over the Trajectory Converter
reveals the following menu:

- Help: Opens MDANSE documentation for the converter class.
- Save: Creates a Python script with the values of all the fields set as they
  were when the button was clicked. This script can be used to quickly run
  the conversion again in the future.
- Run: Initiates the conversion, and its progress can be monitored in the Jobs
  panel. After a successful run, the converted trajectory is saved in the
  location specified in the "output files" field in the converter interface.
Descriptions of all converters can be found in Appendix 1.

7.6.3. Quit
-----------

Selecting this option opens a confirmation prompt. If you select "Yes," MDANSE
will close.

7.7. The View Menu
-------------------

This menu offers several options to show/hide various parts of MDANSE:

- Toggle Data Tree: Shows/hides the Data Panel.
- Toggle Plugins Tree: Shows/hides the Plugins Panel.
- Toggle Controller: Shows/hides the bottom bar containing Logger, Console, and Jobs.
- Toggle Toolbar: Shows/hides the toolbar.

7.8. The Help Menu
-------------------

Clicking the Help button reveals the following menu:

- About: Opens a window containing information about the MDANSE version,
  a short summary, and a list of authors.
- Simple Help: Opens a window with a brief summary of the MDANSE workflow
  and the various options available.
- Theoretical Background: Opens a document summarizing the theory behind many
  of the analyses in a web browser.
- User Guide: Opens the DOI link to this user guide in the default browser,
  displaying an RAL Technical Report webpage. From there, you can download
  this user guide in PDF format.
- Bug Report: Opens your default email application, allowing you to send an
  email to inform us of any issues you have encountered. When reporting an issue,
  please include a screenshot or error details, such as the traceback from job failures.

7.9. Toolbar
------------

The Toolbar is a set of pictographic buttons that enable you to quickly
perform essential actions. Below is a brief overview of each button, from left
to right:

- Load Trajectory Button: Used to load an HDF trajectory. Further details
  are available in the Load Data section.
- Periodic Table Viewer: Opens a periodic table containing constants and data
  used by MDANSE for calculations.
- Elements Database Editor: Allows you to modify atomic constants used by MDANSE.
- 2D/3D Plotter: Launches a window for plotting calculated data and formatting plots.
- User Definitions Editor: Opens a window where calculated data can be plotted and plots formatted.
- Units Editor: Opens a window where you can view definitions created for each trajectory (more on definitions in Selections).
- MDANSE Classes Framework: Provides access to documentation for MDANSE classes, useful for command-line usage.
- Save Analysis Template: Creates a new analysis available in My jobs inside the Plugins panel
  for running like native analyses.
- Open MDANSE API: Opens MDANSE documentation in a web browser, similar to MDANSE Classes Framework.
- Open MDANSE Website: Opens the MDANSE website in a web browser.
- About: Launches a window with basic information about your installed MDANSE version.
- Bug Report: Opens your default email application or directs you to our GitHub [Ref9] to report any issues.
  When reporting an issue, please include a screenshot or error details, such as the traceback from job failures.
- Quit MDANSE: Closes MDANSE.

7.9.1. Periodic Table Viewer
---------------------------

Upon launching, this window will appear:

[Image: Periodic Table Viewer]

Hovering over an element will display detailed information from MDANSE's elements
database at the top. Clicking on an element will open a menu listing its isotopes:

[Image: Isotope menu for a periodic table element]

Selecting an isotope will display all the information stored in the database for that isotope:

[Image: Details of an isotope, including properties and data]

Clicking on the link at the bottom opens a Wikipedia article about that element.
However, interactions within this page are limited. To modify any displayed data,
you should use the Elements Database Editor
