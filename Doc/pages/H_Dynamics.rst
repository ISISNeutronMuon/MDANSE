Section 10 How to Analysis: Dynamics
======================================

Angular Correlation Analysis
===========================

Index 1: GUI for Angular Correlation Analysis

Purpose: Angular correlation analysis helps users understand the autocorrelation
of vectors representing molecule extent in three orthogonal directions. This
guide aims to assist users in effectively utilizing the Angular Correlation
feature to gain insights into the dynamics of molecular systems.

1. Launch MDANSE:
   - Open the MDANSE software on your computer.

2. Load Molecular Data:
   - Load the relevant trajectory or molecular data using the "File" menu.

3. Access the "Angular Correlation" Analysis:
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "Angular Correlation" option from the list of available analysis tools.

4. Configure Analysis Parameters:
   - Frames: Specify the range of frames for analysis. (Default: First: 0, Last: Entire trajectory, Step: 1)
   - Choose the relevant axis for vector calculations.(Default: Principal axes of the molecule)
   - Define output settings such as contributions and output files.(Default: Equal contribution unless specified)
   - Select the appropriate running mode based on the nature of the analysis and desired output (Default: Standard or Basic mode)

5. Initiate the Calculation:
   - Start the Angular Correlation analysis by clicking on the "Run" button within the MDANSE interface.

6. Analyze and Interpret Results:
   - Review the autocorrelation function results to understand the dynamics and correlations of the selected molecular vectors within the system effectively.
   - Interpret the data to gain insights into the rotational dynamics of the molecules and their behavior in the molecular system.

   Recommended Plots:
   - Autocorrelation Plot for Molecular Vectors in Three Orthogonal Directions (time vs. correlation).
   visualize the degree of correlation and fluctuations in different directions over time.
   - Rotational Dynamics Plot for Molecules in the System (angle vs. time).
   provides insights into how molecules rotate and orient themselves within the molecular system

Density Of States Analysis
=========================

Index 2: GUI for Density Of States Analysis

Purpose: The Density Of States analysis aids in calculating the power spectrum
of the VACF (Velocity Autocorrelation Function) to define the discrete DOS
(Density Of States). This gives a comprehensive understanding of molecular dynamics.

1. Launch MDANSE:
   - Open the MDANSE software on your computer.

2. Load Molecular Data:
   - Load the relevant trajectory or molecular data using the "File" menu.

3. Access the "Density Of States" Analysis:
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "Density Of States" option from the list of available analysis tools.

4. Configure Analysis Parameters:
   - Define the desired range of frames for analysis. (Default: First: 0, Last: Entire trajectory, Step: 1)
   - Specify the instrumental resolution and interpolation order for accurate calculations. (Default: Automatic selection)
   - Choose the project coordinates, atom selection, and group coordinates for analysis.(Default: All atoms)
   - Determine the atom transmutation and weights for the calculation.(Default: No transmutation, equal weights)
   - Configure output files and select the appropriate running mode.(Default: Standard mode)

5. Initiate the Calculation:
   - Start the Density Of States analysis by clicking on the "Run" or "Calculate" button within the MDANSE interface.

6. Analyze and Interpret Results:
   - Review the power spectrum results and the density of states characteristics to understand the molecular dynamics and vibrational properties of the system.
   - Interpret the data to gain insights into the phonon modes and the behavior of the molecular components in the system.

   Recommended Plots:
   - Power Spectrum Plot of the VACF. Provides information about vibrational modes and frequencies.
   - Density of States (DOS) Plot.  Illustrates the distribution of vibrational states in the system.

General AutoCorrelation Function Analysis
========================================

Index 3: GUI for General AutoCorrelation Function Analysis

Purpose: The General AutoCorrelation Function analysis calculates the autocorrelation function
for a selected variable, typically used for position autocorrelation. 

1. Launch MDANSE:
   - Open the MDANSE software on your computer.

2. Load Molecular Data:
   - Load the relevant trajectory or molecular data using the "File" menu.

3. Access the "General AutoCorrelation Function" Analysis:
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "General AutoCorrelation Function" option from the list of available analysis tools.

4. Configure Analysis Parameters:
   - Specify the desired range of frames for the analysis. (Default: First: 0, Last: Entire trajectory, Step: 1)
   - Choose the relevant atom selection and group coordinates for the correlation function calculation.(Default:All Atoms)
   - Define the trajectory variable and any required normalization. (Default: No normalization)
   - Set weights and configure output files based on analysis requirements.(Default: equal weights)
   - Select the appropriate running mode to obtain the desired output.(Default: Standard mode)

5. Initiate the Calculation:
   - Start the General AutoCorrelation Function analysis by clicking on the "Run" button within the MDANSE interface.

6. Analyze and Interpret Results:
   - Review the autocorrelation function results to gain insights into the position dynamics of the molecular system.
   - Interpret the data to understand the correlation time and behavior of the selected variable within the system effectively.

   Recommended Plots:
   - Autocorrelation Function Plot for the Selected Variable.How the variable's correlation changes over time.
   - Correlation Time Plot.Shows characteristic time scales of the system's behavior.


Mean Square Displacement Analysis
=================================
Index 4: GUI for Mean Square Displacement Analysis

Purpose: Mean Square Displacement (MSD) analysis helps understand particle diffusion.
This guide aims to assist users in effectively utilizing the Mean Square Displacement feature
to comprehend the dynamics of molecular systems. Shows characteristic time scales of the system's behavior.

1. Launch MDANSE:
   - Open the MDANSE software on your computer.

2. Load Molecular Data:
   - Load the relevant trajectory or molecular data using the "File" menu.

3. Access the "Mean Square Displacement" Analysis:
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "Mean Square Displacement" option from the list of available analysis tools.

4. Configure Analysis Parameters:
   - Define the desired range of frames for analysis. (Default: First: 0, Last: Entire trajectory, Step: 1)
   - Specify the project coordinates and relevant atom selections for the calculation.(Default:)
   - Set the necessary group coordinates, atom transmutation, and weights as required.(Default: equal weights)
   - Configure output files and select the appropriate running mode for the analysis.(Default: Standard mode)

5. Initiate the Calculation:
   - Start the Mean Square Displacement analysis by clicking on the "Run" button within the MDANSE interface.

6. Analyze and Interpret Results:
   - Review the MSD results to understand the diffusion behavior of particles in the molecular system.
   - Analyze the relationship between MSD and the velocity autocorrelation function to gain insights into the system's dynamics effectively.

   Recommended Plots:
   - Mean Square Displacement vs. Time Plot.(vs) add more info 
   - Velocity Autocorrelation Function (VACF) Plot.(vs) add more info 

Order Parameter Analysis
========================
Index 5: GUI for Order Parameter Analysis

Purpose: The Order Parameter analysis facilitates the study of conformational dynamics of proteins.
This guide aims to assist users in effectively utilizing the Order Parameter feature to gain insights
into the behavior and structural changes of proteins in molecular systems.

1. Launch MDANSE:
   - Open the MDANSE software on your computer.

2. Load Molecular Data:
   - Load the relevant trajectory or molecular data using the "File" menu.

3. Access the "Order Parameter" Analysis:
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "Order Parameter" option from the list of available analysis tools.

4. Configure Analysis Parameters:
   - Define the desired range of frames for the analysis. (Default: First: 0, Last: Entire trajectory, Step: 1)
   - Select the appropriate axis selection or reference basis for the order parameter calculation.
    (Default: equal weights)
    (Defaults: x-component: 0, y-component: 0, z-component: 1)
   - Specify the output contributions per axis and configure output files according to the analysis requirements.
   - Choose the appropriate running mode to obtain the desired output.(Default: Standard mode)

5. Initiate the Calculation:
   - Start the Order Parameter analysis by clicking on the "Run" button within the MDANSE interface.

6. Analyze and Interpret Results:
   - Review the order parameter results to understand the conformational dynamics and structural changes of proteins within the molecular system.
   - Analyze the internal and global correlation functions to gain insights into the protein's behavior effectively.

   Recommended Plots:
   - Order Parameter vs. Time Plot. order parameter changes over time, reflecting protein conformational dynamics.
   - Internal and Global Correlation Function Plots. gain insights into the protein's behavior effectively.

Position AutoCorrelation Function Analysis
==========================================
 GUI for Position AutoCorrelation Function Analysis

Purpose: The Position AutoCorrelation Function analysis focuses on position autocorrelation.
This gains insights into the positional dynamics of molecular systems.

1. Launch MDANSE:
   - Open the MDANSE software on your computer.

2. Load Molecular Data:
   - Load the relevant trajectory or molecular data using the "File" menu.

3. Access the "Position AutoCorrelation Function" Analysis:
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "Position AutoCorrelation Function" option from the list of available analysis tools.

4. Configure Analysis Parameters:
   - Specify the desired range of frames for the analysis.(Default: First: 0, Last: Entire trajectory, Step: 1)
   - Define any necessary normalization procedures.(Default: No normalization)
   - Choose project coordinates, atom selection, and group coordinates for the correlation function calculation.(Default: All available atoms) 
   - Determine the atom transmutation and set weights as required.(Default: equal weights, standard output)
   - Configure output files and select the appropriate running mode based on the analysis requirements. (Default: Standard mode)

5. Initiate the Calculation:
   - Start the Position AutoCorrelation Function analysis by clicking on the "Run" button within the MDANSE interface.

6. Analyze and Interpret Results:
   - Review the position autocorrelation function results to gain insights into the positional dynamics of the molecular system.
   - Interpret the data to understand the characteristic time scales and behavior of the system effectively.

   Recommended Plots:
   - Position AutoCorrelation Function Plot. Visualizes how the variable's correlation changes over time.
   - Characteristic Time Scales Plot. Shows characteristic time scales of the system's behavior.
