Tutorial: Neutron Scattering Dynamic Coherent Structure Factor (DCSF)
======================================================================

This tutorial provides a guide on performing neutron scattering analysis using
the MDANSE software. We will cover launching MDANSE, loading trajectory data in
HDF format, configuring the analysis, troubleshooting common issues, and saving
simulation data.

**Step 1: Launching MDANSE and Loading HDF Trajectory**

*1.1 Launch MDANSE:*
- Begin by launching MDANSE, either by double-clicking its icon or running it
  from the command line, if necessary.

*1.2 Load HDF Trajectory:*
- Once MDANSE is running, ensure that you have your molecular dynamics
  trajectory data in the HDF format loaded into the software, suitable for
  neutron scattering analysis.

  - To load the HDF trajectory, follow these steps:
    1. Go to the "File" menu at the top of the MDANSE window.
    2. Select "Load Trajectory" from the dropdown menu.
    3. Browse your file system and select the MDANSE HDF trajectory file you want
       to analyze. Click "Open" to load it into MDANSE.

**Step 2: Configuring Dynamic Coherent Structure Factor Analysis**

*2.1 Access Analysis Menu:*
- In the MDANSE GUI, navigate to the "Analysis" menu located at the top of the
  window.

*2.2 Initiate Analysis:*
- From the "Analysis" menu, choose "Dynamic Coherent Structure Factor" to
  initiate the analysis. This opens a dialog for configuring the analysis
  parameters.

*2.3 **Configure Analysis Parameters:***
- In the "Dynamic Coherent Structure Factor" dialog, configure the analysis
  parameters as follows:
  - **Frames:** For this analysis, we want to analyze all frames of the HDF
    trajectory. You can specify a range of frames if needed (Default: First: 0,
    Last: Entire trajectory, Step: 1).
  - **Instrument Resolution:** Leave this setting at its default value for this
    neutron scattering example (Default: Auto).
  - **Q Vectors:** Select the "Isotropic" option for Q vectors as we want to
    analyze a wide range of scattering vectors in all directions suitable for
    neutron scattering experiments (Default: Isotropic).
  - **Atom Selection:** Choose "All" to analyze all atoms in the system relevant
    to your neutron scattering analysis (Default: All).
  - **Atom Transmutation:** No specific atom transmutation is needed for this
    analysis, so leave it at its default setting (Default: None).
  - **Weights:** MDANSE will automatically calculate weights based on neutron
    coherent scattering lengths, so leave this setting at its default value
    (Default: Auto).
  - **Output Files:** You can specify the output file format and location. For
    this example, we'll use the default settings, which typically include HDF
    as the format (Default: Format: HDF, Location: Default).
    

*2.4 Troubleshooting Tips:*
- **Issue:** If MDANSE encounters an error during the analysis setup, double-
  check the configuration parameters, ensuring they are appropriate for your
  data and analysis. Pay special attention to the Q Vectors and Atom Selection.
- **Issue:** If the analysis takes an unexpectedly long time to complete,
  review your system specifications and the number of frames in your trajectory.
  It may be beneficial to reduce the number of frames or use a more efficient
  workstation.

**Step 3: Running the Analysis**

*3.1 Initiate Analysis Run:*
- After configuring the analysis parameters in the "Dynamic Coherent Structure
  Factor" dialog, click the "Run" button within the dialog to initiate the
  analysis.

*3.2 Monitor Progress:*
- MDANSE will start performing the calculations, and you'll see progress
  indicators or logs in the MDANSE interface.

*3.3 Review Results:*
- Once the analysis is complete, MDANSE will generate the results, including the
  total and partial dynamic coherent structure factors, and save them in the
  default HDF file format, which you specified earlier. These HDF files will
  typically be located in the default output location.

**Step 4: Saving Simulation Data**

*4.1 Save Project:*
- In MDANSE, go to the "File" menu and select "Save" to save your project. This
  will save your current analysis configuration and settings.

*4.2 Export Data:*
- To save simulation trajectories, energy profiles, and other relevant data,
  consult MDANSE's documentation or menu options specific to data export. You can
  typically export data in various formats, including text, CSV, or specific file
  formats for further analysis in external software.

**Step 5: Organizing and Storing Simulation Results**

- Organizing and storing simulation results effectively is crucial for easy
  access and future analysis. Consider creating a dedicated folder or directory
  structure for your simulation project and its associated data. You can organize
  it as follows:
  - Create a main project folder with a descriptive name.
  - Within the project folder, create subfolders for specific types of data
    (e.g., "Trajectories," "Energy Profiles," "Analysis Results").
  - Save simulation trajectories, energy profiles, and other data in their
    respective subfolders.

- Additionally, consider using version control systems or documenting your work to
  track changes and ensure reproducibility of your simulations.
