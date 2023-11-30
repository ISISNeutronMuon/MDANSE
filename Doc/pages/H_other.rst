How to Guide Analysis: Other Options
=====================================

Infrared: Dipole AutoCorrelation Function
-----------------------------------------

**Load Trajectory Data**

1. Open MDANSE on your computer.
2. Click on the "File" menu.
3. Select "Load Trajectory Data" and choose your trajectory file.

**Access the "Dipole AutoCorrelation Function" Analysis**

1. In the MDANSE interface, navigate to the "Analysis" section.
2. Locate and select "Dipole AutoCorrelation Function" from the available
analysis options.

**Configure Settings**

- Frames: Specify the frames or time points (Default: First:
0, Last: Entire trajectory, Step: 1).
- Atom Selection: Choose the atoms or particles.
- Output Files (Optional): Configure output file settings as needed.

**Run the Calculation**

- Click on the "Run" button.

**Review Results**

- Access and interpret the dipole autocorrelation function results for
studying molecular vibrations and infrared spectra.

Macromolecules: Refolded Membrane Trajectory
--------------------------------------------

**Load Trajectory Data**

1. Open MDANSE on your computer.
2. Click on the "File" menu.
3. Select "Load Trajectory Data" and choose your trajectory file.

**Access the "Refolded Membrane Trajectory" Analysis**

1. Navigate to the "Analysis" section in MDANSE.
2. Expand the "Macromolecules" subsection.
3. Select "Refolded Membrane Trajectory" from the available plugins.

**Configure Settings**

- Membrane Axis: Choose the axis for membrane manipulation.
- Name of the Lipid (Upper Leaflet): Specify the lipid
name in the upper leaflet.
- Name of the Lipid (Lower Leaflet): Specify the lipid
name in the lower leaflet.
- Output Files: Configure output file settings as needed.

**Run the Calculation**

- Click on the "Run" button.

**Review Results**

- Examine the modified membrane trajectory.

Thermodynamics: Density and Temperature
----------------------------------------

**Load Trajectory Data**

1. Open MDANSE on your computer.
2. Click on the "File" menu.
3. Select "Load Trajectory Data" and choose your trajectory file.

**Access the Desired Analysis**

- For "Density":
    1. Select "Density" from the analysis options.
    2. Configure additional settings if necessary.
    3. Click "Run" to calculate the density.
- For "Temperature":
    1. Select "Temperature" from the analysis options.
    2. Configure additional settings if necessary.
    3. Click "Run" to calculate the temperature.

**Review Results**

- Access and interpret the density or temperature results, depending
on the performed analysis.


Box Translated Trajectory
---------------------------

**Purpose**
- Useful for simulating scenarios where repositioning the entire simulation
box is needed to study system behavior under different conditions 
or to set up specific simulation environments.

**Load Trajectory Data**
   1. Open MDANSE on your computer.
   2. Click on the "File" menu.
   3. Select "Load Trajectory Data" and choose your trajectory file.

**Access the "Box Translated Trajectory" Analysis**
   - In the MDANSE interface, navigate to the "Analysis" section.
   - Select "Box Translated Trajectory" from the available plugins.

**Configure Settings**
- Frames: Specify the frames or time points for box
translation (Default: First: 0, Last: Entire trajectory, Step: 1).
- Atom Selection: Choose the atoms or particles involved in
the translation.
   - Output Files: Configure output file settings as needed.
   - Running Mode: Define the running mode (Default: 0).

**Run the Calculation**
- Click on the "Run" button to perform the box
translation.

Center Of Masses Trajectory
---------------------------

**Purpose**
- To reduce the complexity of a molecular dynamics simulation
by focusing on the motion of groups of atoms, such as molecules or subunits.

**Load Trajectory Data**
   1. Open MDANSE on your computer.
   2. Click on the "File" menu.
   3. Select "Load Trajectory Data" and choose your trajectory file.

**Access the "Center Of Masses Trajectory" Analysis**
   - Navigate to the "Analysis" section in the MDANSE interface.
   - Select "Center Of Masses Trajectory" from the available plugins.

**Configure Settings**
- Frames: Specify the frames for COMT calculation (Default: First:
0, Last: Entire trajectory, Step: 1).
- Atom Selection: Choose atoms for the center of mass
computation.
   - Group Coordinates: Define groups of atoms for calculation.
   - Output Files: Configure file settings as needed.
   - Running Mode: Define the mode (Default: 0).

**Run the Calculation**
   - Click the "Run" button for the COMT calculation.

Cropped Trajectory
------------------

**Purpose**
   - To extract a subset of frames from your trajectory.

**Load Trajectory Data**
- Follow the same steps as in the Center Of
Masses Trajectory.

**Access the "Cropped Trajectory" Analysis**
   - Navigate to the "Analysis" section in MDANSE.
   - Select "Cropped Trajectory" from the available plugins.

**Configure Settings**
- Frames: Specify the frames for the cropped trajectory (Default:
First: 0, Last: Entire trajectory, Step: 1).
   - Atom Selection: Choose atoms to be included.
   - Output Files: Configure file settings as needed.
   - Running Mode: Define the mode (Default: 0).

**Run the Calculation**
   - Click the "Run" button to create the cropped trajectory.

Global Motion Filtered Trajectory
---------------------------------

**Purpose**
- To separate global motion from internal motion within the
trajectory, focusing on relevant internal dynamics.

**Load Trajectory Data**
   1. Open MDANSE on your computer.
   2. Click on the "File" menu.
   3. Select "Load Trajectory Data" and choose your trajectory file.

**Access the "Global Motion Filtered Trajectory" Analysis**
- In MDANSE, navigate to "Analysis" and select "Global Motion
Filtered Trajectory".

**Configure Settings**
- Frames: Specify frames for global motion filtering (Default: First:
0, Last: Entire trajectory, Step: 1).
   - Atom Selection: Choose atoms involved in the analysis.
   - Reference Basis: Select the reference basis for filtering.
   - Chemical Object Contiguity: Optionally make configuration contiguous (Default: False).
   - Output Files: Configure file settings as needed.
   - Running Mode: Define the mode (Default: 0).

**Run the Calculation**
   - Click "Run" to generate the global motion filtered trajectory.

Rigid Body Trajectory
---------------------

**Purpose**
- To extract rigid body motions from a molecular dynamics
trajectory.

**Load Trajectory Data**
- Follow the same steps as in the Global Motion
Filtered Trajectory.

**Access the "Rigid Body Trajectory" Analysis**
   - Navigate to "Analysis" and select "Rigid Body Trajectory".

**Configure Settings**
- Frames: Specify frames for rigid body analysis (Default: First:
0, Last: Entire trajectory, Step: 1).
   - Atom Selection: Choose atoms involved in the analysis.
   - Group Coordinates: Define groups of atoms as rigid bodies.
   - Reference: Specify reference frame number (Default: 0).
   - Remove Translation: Optionally remove translation (Default: False).
   - Output Files: Configure file settings as needed.
   - Running Mode: Define the mode (Default: 0).

**Run the Calculation**
- Click "Run" to extract rigid body motions from the
trajectory.


