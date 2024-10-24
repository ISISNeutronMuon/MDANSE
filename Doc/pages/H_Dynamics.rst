Running Dynamics Calculations
=============================

Angular Correlation
-------------------

**Purpose:**
Angular correlation analysis helps users understand the autocorrelation
of vectors representing molecule extent in three orthogonal directions.
This feature assists users in effectively utilizing the Angular Correlation
to gain insights into the dynamics of molecular systems.

#. **Load Molecular Data:**
   - Load the relevant trajectory or molecular data using the "File" menu.

#. **Access the "Angular Correlation" Analysis:**
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "Angular Correlation" option from the list of available
     analysis tools.

#. **Configure Analysis Parameters:**
   - **Frames:** Specify the range of frames for analysis. (Default: First:
     0, Last: Entire trajectory, Step: 1)
   - **Axis Selection:** Choose the relevant axis for vector calculations.
     (Default: Principal axes of the molecule)
   - **Output Settings:** Define output settings such as contributions and
     output files. (Default: Equal contribution unless specified)
   - **Running Mode:** Select the appropriate running mode based on the nature
     of the analysis and desired output. (Default: Monoprocessor)

#. **Start the Calculation:**
   - Start the Angular Correlation analysis by clicking on the "Run" button
     within the MDANSE interface.

#. **Analyze and Interpret Results:**
   - Review the autocorrelation function results to understand the dynamics
     and correlations of the selected molecular vectors within the system
     effectively.

#. **Recommended Plots:**
   - Autocorrelation Plot for Molecular Vectors in Three Orthogonal Directions
     (time vs. correlation): Visualize the degree of correlation and fluctuations
     in different directions over time.
   - Rotational Dynamics Plot for Molecules in the System (angle vs. time):
     Provides insights into how molecules rotate and orient themselves within
     the molecular system.


Density Of States
------------------

**Purpose:**
The Density Of States analysis aids in calculating the power spectrum of the
VACF (Velocity Autocorrelation Function) to define the discrete DOS (Density Of
States). This gives a  understanding of molecular dynamics.

#. **Load Molecular Data:**
   - Load the relevant trajectory or molecular data using the "File" menu.

#. **Access the "Density Of States" Tool:**
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "Density Of States" option from the list of available tools.

#. **Configure Parameters:**
   - **Frames:** Define the desired range of frames for analysis. (Default:
     First: 0, Last: Entire trajectory, Step: 1)
   - **Instrumental Resolution:** Specify the instrumental resolution for
     accurate calculations. (Default: Automatic selection)
   - **Interpolation Order:** Set the interpolation order for accurate
     calculations. (Default: Automatic selection)
   - **Project Coordinates:** Choose the project coordinates for analysis.
     (Default: All atoms)
   - **Atom Selection:** Define the atom selection for analysis. (Default: All
     atoms)
   - **Group Coordinates:** Specify group coordinates for analysis. (Default:
     All atoms)
   - **Atom Transmutation:** Determine atom transmutation if needed. (Default:
     No transmutation)
   - **Weights:** Configure weights for the calculation. (Default: Equal
     weights)
   - **Output Files:** Configure output files as required. (Default: Standard
     output)
   - **Running Mode:** Select the appropriate running mode. (Default:
     Monoprocessor)

#. **Start the Calculation:**
   - Start the Density Of States analysis by clicking on the "Run" or
     "Calculate" button within the MDANSE interface.

#. **Analyze and Interpret Results:**
   - Review the power spectrum results and the density of states characteristics
     to understand the molecular dynamics and vibrational properties of the
     system.
   - Interpret the data to gain insights into the phonon modes and the behavior
     of the molecular components in the system.

#. **Recommended Plots:**
   - Power Spectrum Plot of the VACF: Provides information about vibrational
     modes and frequencies.
   - Density of States (DOS) Plot: Illustrates the distribution of vibrational
     states in the system.

General AutoCorrelation Function
---------------------------------

**Purpose:**
The General AutoCorrelation Function calculates the autocorrelation function
for a selected variable, typically used for position autocorrelation.


#. **Load Molecular Data:**
   - Load the relevant trajectory or molecular data using the "File" menu.

#. **Access the "General AutoCorrelation Function" Tool:**
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "General AutoCorrelation Function" option from the list of
     available tools.

#. **Configure Parameters:**
   - **Frames:** Specify the desired range of frames for the analysis. (Default:
     First: 0, Last: Entire trajectory, Step: 1)
   - **Atom Selection:** Choose the relevant atom selection for the correlation
     function calculation. (Default: All Atoms)
   - **Group Coordinates:** Define the group coordinates for the correlation
     function calculation. (Default: All atoms)
   - **Trajectory Variable:** Specify the trajectory variable and any required
     normalization. (Default: No normalization)
   - **Weights:** Set weights for the calculation. (Default: Equal weights)
   - **Output Files:** Configure output files based on requirements.
     (Default: Standard output)
   - **Running Mode:** Select the appropriate running mode. (Default:
     Monoprocessor)

#. **Start the Calculation:**
   - Start the General AutoCorrelation Function calculation by clicking the
     "Run" button within the MDANSE interface.

#. **Analyze and Interpret Results:**
   - Review the autocorrelation function results to gain insights into the
     position dynamics of the molecular system.
   - Interpret the data to understand the correlation time and behavior of the
     selected variable within the system effectively.

#. **Recommended Plots:**
   - Autocorrelation Function Plot for the Selected Variable: Shows how the
     variable's correlation changes over time.
   - Correlation Time Plot: Illustrates characteristic time scales of the
     system's behavior.


Mean Square Displacement
-------------------------

**Purpose:**
Mean Square Displacement (MSD) helps understand particle diffusion. This guide aims
to assist users in effectively utilizing the Mean Square Displacement feature to
comprehend the dynamics of molecular systems and explore characteristic time scales
of the system's behavior.

#. **Load Molecular Data:**
   - Load the relevant trajectory or molecular data using the "File" menu.

#. **Access the "Mean Square Displacement" Tool:**
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "Mean Square Displacement" option from the list of available tools.

#. **Configure Analysis Parameters:**
   - **Frames:** Specify the desired range of frames for analysis. (Default: First: 0,
     Last: Entire trajectory, Step: 1)
   - **Project Coordinates:** Define the project coordinates and relevant atom
     selections for the calculation.
   - **Group Coordinates:** Set the necessary group coordinates, atom transmutation, and
     weights as required. (Default: equal weights)
   - **Output Files:** Configure output files according to the analysis requirements.
   - **Running Mode:** Choose the appropriate running mode for the analysis. (Default:
     Monoprocessor)

#. **Start the Calculation:**
   - Start the Mean Square Displacement analysis by clicking on the "Run" button
     within the MDANSE interface.

#. **Analyze and Interpret Results:**
   - Review the MSD results to understand the diffusion behavior of particles in the
     molecular system.
   - Analyze the relationship between MSD and the velocity autocorrelation function
     (VACF) to gain insights into the system's dynamics effectively.

#. **Recommended Plots:**
   - **Mean Square Displacement vs. Time Plot:** Provides insights into particle
     diffusion over time.
   - **Velocity Autocorrelation Function (VACF) Plot:** Illustrates the velocity
     autocorrelation and its significance in system dynamics.

Order Parameter
----------------

**Purpose:**
The Order Parameter facilitates the study of conformational dynamics of proteins. This
guide aims to assist users in effectively utilizing the Order Parameter feature to
gain insights into the behavior and structural changes of proteins in molecular systems.

#. **Load Molecular Data:**
   - Load the relevant trajectory or molecular data using the "File" menu.

#. **Access the "Order Parameter" Tool:**
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "Order Parameter" option from the list of available tools.

#. **Configure Analysis Parameters:**
   - **Frames:** Specify the desired range of frames for the analysis. (Default: First: 0,
     Last: Entire trajectory, Step: 1)
   - **Axis Selection:** Select the appropriate axis selection or reference basis for the
     order parameter calculation. (Default: equal weights)
     (Defaults: x-component: 0, y-component: 0, z-component: 1)
   - **Output Contributions:** Specify the output contributions per axis and configure
     output files according to the analysis requirements.
   - **Running Mode:** Choose the appropriate running mode to obtain the desired output.
     (Default: Monoprocessor)

#. **Start the Calculation:**
   - Start the Order Parameter analysis by clicking on the "Run" button within the MDANSE
     interface.

#. **Analyze and Interpret Results:**
   - Review the order parameter results to understand the conformational dynamics and
     structural changes of proteins within the molecular system.
   - Analyze the internal and global correlation functions to gain insights into the
     protein's behavior effectively.

#. **Recommended Plots:**
   - **Order Parameter vs. Time Plot:** Reflects protein conformational dynamics over time.
   - **Internal and Global Correlation Function Plots:** Provide insights into the
     protein's behavior effectively.



Position AutoCorrelation Function
-----------------------------------

**Purpose:**
The Position AutoCorrelation Function analysis focuses on position autocorrelation.
This gains insights into the positional dynamics of molecular systems.

#. **Load Molecular Data:**
   - Load the relevant trajectory or molecular data using the "File" menu.

#. **Access the "Position AutoCorrelation Function" Analysis:**
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "Position AutoCorrelation Function" option from the list of available analysis tools.

#. **Configure Analysis Parameters:**
   - **Frames:** Specify the desired range of frames for the analysis. (Default: First: 0,
     Last: Entire trajectory, Step: 1)
   - **Group Coordinates:** Set the necessary group coordinates, atom transmutation, and
     weights as required. (Default: equal weights)
   - **Output Files:** Configure output files according to the analysis requirements.
   - **Running Mode:** Choose the appropriate running mode for the analysis. (Default:
     Monoprocessor)

#. **Start the Calculation:**
   - Start the Position AutoCorrelation Function analysis by clicking on the "Run" button
     within the MDANSE interface.

#. **Analyze and Interpret Results:**
   - Review the position autocorrelation function results to gain insights into the
     positional dynamics of the molecular system.
   - Interpret the data to understand the characteristic time scales and behavior of the
     system effectively.

#. **Recommended Plots:**
   - Position AutoCorrelation Function Plot. Visualizes how the variable's correlation
     changes over time.
   - Characteristic Time Scales Plot. Shows characteristic time scales of the system's
     behavior.
