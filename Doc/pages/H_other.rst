Running Other Calculations
==========================

Infrared: Dipole AutoCorrelation Function
-----------------------------------------

**Purpose**
The Infrared: Dipole AutoCorrelation Function analysis focuses on studying
molecular vibrations and infrared spectra using dipole auto-correlation.

#. **Load Trajectory Data:**
   - Click on the "File" menu.
   - Select "Load Trajectory Data" and choose your trajectory file.

#. **Access the "Dipole AutoCorrelation Function" Analysis:**
   - In the MDANSE interface, navigate to the "Analysis" section.
   - Locate and select "Dipole AutoCorrelation Function" from the available
     analysis options.

#. **Configure Analysis Parameters:**
   - **Frames:** Specify the frames or time points (Default: First: 0, Last: Entire
     trajectory, Step: 1).
   - **Atom Selection:** Choose the atoms or particles.
   - **Output Files (Optional):** Configure output file settings as needed.

#. **Run the Calculation:**
   - Click on the "Run" button.

#. **Review Results:**
   - Access and interpret the dipole autocorrelation function results to study
     molecular vibrations and infrared spectra.

#. **Recommended Plots:**
   - Dipole AutoCorrelation Function Plot: Visualizes how the dipole autocorrelation
     changes over time, providing insights into molecular vibrations.

   - Infrared Spectra Plot: Illustrates the infrared spectra obtained from the
     analysis, showing the vibrational modes of the system.


Thermodynamics: Density
-----------------------

**Purpose**
The Thermodynamics: Density analysis focuses on calculating the density of a molecular system.

#. **Load Trajectory Data:**
   - Click on the "File" menu.
   - Select "Load Trajectory Data" and choose your trajectory file.

#. **Access the "Density" Analysis:**
   - In the MDANSE interface, navigate to the "Analysis" section.
   - Select "Density" from the available analysis options.

#. **Configure Analysis Parameters:**
   - **Frames:** Specify the frames or time points (Default: First: 0, Last: Entire trajectory, Step: 1).
   - **Atom Selection:** Choose the atoms or particles.
   - **Output Files (Optional):** Configure output file settings as needed.

#. **Run the Calculation:**
   - Click on the "Run" button.

#. **Review Density Results:**
   - Access and interpret the density results obtained from the analysis.

#. **Recommended Plot:**
   - Density Plot: Visualizes how the density changes over time, providing insights into the system's behavior.

Thermodynamics: Density
-----------------------

**Purpose**
The Thermodynamics: Density analysis focuses on calculating the density of a
molecular system.

#. **Load Trajectory Data:**
   - Click on the "File" menu.
   - Select "Load Trajectory Data" and choose your trajectory file.

#. **Access the "Density" Analysis:**
   - In the MDANSE interface, navigate to the "Analysis" section.
   - Select "Density" from the available analysis options.

#. **Configure Analysis Parameters:**
   - **Frames:** Specify the frames or time points (Default: First: 0, Last: Entire
     trajectory, Step: 1).
   - **Atom Selection:** Choose the atoms or particles.
   - **Output Files (Optional):** Configure output file settings as needed.

#. **Run the Calculation:**
   - Click on the "Run" button.

#. **Review Density Results:**
   - Access and interpret the density results obtained from the analysis.

#. **Recommended Plot:**
   - Density Plot: Visualizes how the density changes over time, providing insights
     into the system's behavior.

Thermodynamics: Temperature
---------------------------

**Purpose**
The Thermodynamics: Temperature analysis focuses on calculating the temperature of
a molecular system.

#. **Load Trajectory Data:**
   - Click on the "File" menu.
   - Select "Load Trajectory Data" and choose your trajectory file.

#. **Access the "Temperature" Analysis:**
   - In the MDANSE interface, navigate to the "Analysis" section.
   - Select "Temperature" from the available analysis options.

#. **Configure Analysis Parameters:**
   - **Frames:** Specify the frames or time points (Default: First: 0, Last: Entire
     trajectory, Step: 1).
   - **Atom Selection:** Choose the atoms or particles.
   - **Output Files (Optional):** Configure output file settings as needed.

#. **Run the Calculation:**
   - Click on the "Run" button.

#. **Review Temperature Results:**
   - Access and interpret the temperature results obtained from the analysis.

#. **Recommended Plot:**
   - Temperature Plot: Visualizes how the temperature changes over time, providing
     insights into the system's thermal behavior.


Center Of Masses Trajectory
---------------------------

**Purpose**
The Center Of Masses Trajectory analysis aims to reduce the complexity of a
molecular dynamics simulation by focusing on the motion of groups of atoms, such
as molecules or subunits.

#. **Load Trajectory Data:**
   - Click on the "File" menu.
   - Select "Load Trajectory Data" and choose your trajectory file.

#. **Access the "Center Of Masses Trajectory" Analysis:**
   - Navigate to the "Analysis" section in the MDANSE interface.
   - Select "Center Of Masses Trajectory" from the available plugins.

#. **Configure Settings:**
   - **Frames:** Specify the frames for COMT calculation (Default: First: 0, Last: Entire trajectory, Step: 1).
   - **Atom Selection:** Choose atoms for the center of mass computation.
   - **Group Coordinates:** Define groups of atoms for calculation.
   - **Output Files:** Configure file settings as needed.
   - **Running Mode:** Define the mode (Default: 0).

#. **Run the Calculation:**
   - Click the "Run" button for the COMT calculation.

#. **Recommended Plot:**
   - Center Of Masses Trajectory Plot: Visualizes the motion of groups of atoms'
     centers of mass, providing insights into the system's overall dynamics.

Cropped Trajectory
------------------

**Purpose**
The Cropped Trajectory analysis allows you to extract a subset of frames from your
trajectory.

#. **Load Trajectory Data:**
   - Follow the same steps as in the "Center Of Masses Trajectory" section.

#. **Access the "Cropped Trajectory" Analysis:**
   - Navigate to the "Analysis" section in MDANSE.
   - Select "Cropped Trajectory" from the available plugins.

#. **Configure Settings:**
   - **Frames:** Specify the frames for the cropped trajectory (Default: First: 0,
     Last: Entire trajectory, Step: 1).
   - **Atom Selection:** Choose atoms to be included.
   - **Output Files:** Configure file settings as needed.
   - **Running Mode:** Define the mode (Default: 0).

#. **Run the Calculation:**
   - Click the "Run" button to create the cropped trajectory.

#. **Recommended Plot:**
   - Cropped Trajectory Plot: Visualizes the subset of frames extracted from the
     trajectory, highlighting specific segments of interest.

Global Motion Filtered Trajectory
----------------------------------

**Purpose**
The Global Motion Filtered Trajectory analysis separates global motion from internal
motion within the trajectory, focusing on relevant internal dynamics.

#. **Load Trajectory Data:**
   - Click on the "File" menu.
   - Select "Load Trajectory Data" and choose your trajectory file.

#. **Access the "Global Motion Filtered Trajectory" Analysis:**
   - In MDANSE, navigate to "Analysis" and select "Global Motion Filtered Trajectory."

#. **Configure Settings:**
   - **Frames:** Specify frames for rigid body analysis (Default: First: 0, Last:
     Entire trajectory, Step: 1).
   - **Atom Selection:** Choose atoms involved in the analysis.
   - **Group Coordinates:** Define groups of atoms as rigid bodies.
   - **Reference:** Specify reference frame number (Default: 0).
   - **Remove Translation:** Optionally remove translation (Default: False).
   - **Output Files:** Configure file settings as needed.
   - **Running Mode:** Define the mode (Default: 0).

#. **Run the Calculation:**
   - Click "Run" to extract rigid body motions from the trajectory.

#. **Recommended Plot:**
   - Rigid Body Trajectory Plot: Visualizes the extracted rigid body motions,
     providing insights into the system's rigid body dynamics.