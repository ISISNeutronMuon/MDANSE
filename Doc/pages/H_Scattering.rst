Running Scattering Calculations
===============================

Current Correlation Function
''''''''''''''''''''''''''''

**Purpose:**

The Current Correlation Function (CCF) analysis is a valuable tool for studying
the propagation of excitations in disordered systems. This guide aims to assist
users in effectively utilizing the CCF feature to gain insights into the dynamics
of density fluctuations and propagating shear modes within the molecular system.



2. **Load Trajectory Data:**
   - Load the relevant trajectory data using the "File" menu.

3. **Access the "Current Correlation Function" Analysis:**
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "Current Correlation Function" option from the list of available
     analysis tools.

4. **Configure Analysis Parameters:**
   - Define the appropriate parameters for frames and instrument resolution.
   - Specify the interpolation order for precise calculations.
   - Select the interpolation mode based on the available hardware and memory
     resources:
     - **One-time in-memory interpolation** [Default]: Fast but requires ample
       memory (recommended for small trajectories).
     - **Repeated interpolation**: Slower but memory-efficient (suitable for
       medium trajectories).
     - **One-time disk interpolation**: Slower, low memory usage (for large
       trajectories, SSD recommended).
     - **Automatic mode**.
   - Set the number of preloaded frames if the "one-time disk interpolation"
     mode is selected. [Default: 50]. Adjust the value to optimize memory usage
     and analysis speed.

5. **Configure Q Vectors and Atom Selection:**
   - Define the Q vectors based on the requirements of the analysis.
   - Choose the relevant atom selection for the calculation.

6. **Normalize, Atom Transmutation, and Weights:**
   - Specify whether normalization is required for the analysis.
   - Set the necessary atom transmutation and weights as per the analysis
     requirements.

7. **Configure Output Files and Running Mode:**
   - Define the output files based on the analysis requirements.
   - Select the appropriate running mode to obtain the desired output.

8. **Start the Calculation:**
   - Start the Current Correlation Function analysis by clicking on the "Run" or
     "Calculate" button within the MDANSE interface.

9. **Analyze and Interpret Results:**
   - Review the results to understand the dynamics of density fluctuations and
     propagating shear modes within the molecular system effectively.

10. **Plotting Suggestions:**
    When reviewing the Current Correlation Function analysis results, consider the
    following for better visualization:

    - Plot the CCF as a function of time or lag time to observe decay behavior.
    - Compare CCF results for different Q vectors or atom selections using plots.
    - Utilize log-scale plots for improved long-time behavior visualization.
    - Overlay multiple CCF plots to facilitate comparisons.


Dynamic Coherent Structure Factor
'''''''''''''''''''''''''''''''''

**Purpose:**
The Dynamic Incoherent Structure Factor (DISF) analysis is an essential tool for
comprehending the dynamics of incoherent scattering within the molecular system.
It aims to aid users in efficiently harnessing the DISF feature to acquire
insights into intermediate incoherent scattering functions and the resulting
dynamic structure factor within the system.



2. **Load Trajectory Data:**
   - Load the relevant trajectory data using the "File" menu.

3. **Access the "Dynamic Incoherent Structure Factor" Analysis:**
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "Dynamic Incoherent Structure Factor" option from the list of
     available analysis tools.

4. **Configure Analysis Parameters:**
   - **Frames:** Specify the range of frames for analysis. (Default: First: 0,
     Last: Entire trajectory, Step: 1)
   - **Q Vectors:** Define the wave vectors (Q) based on the dynamics of
     incoherent scattering. (Default: User-defined)
   - **Atom Selection:** Choose the relevant atom selection and group coordinates
     for the analysis. (Default: All atoms)
   - **Atom Transmutation:** Determine atom transmutation and project coordinates
     as required for the calculation. (Default: None)
   - **Weights:** Set the necessary weights to accurately represent incoherent
     scattering lengths. (Default: Equal weights)
   - **Output Settings:** Configure output files and select the appropriate
     running mode for the analysis. (Default: Monoprocessor)

5. **Start the Calculation:**
   - Start the Dynamic Incoherent Structure Factor analysis by clicking on the
     "Run" or "Calculate" button within the MDANSE interface.

6. **Analyze and Interpret Results:**
   - Review the partial and total dynamic incoherent structure factor results to
     gain insights into the incoherent intermediate scattering functions and the
     dynamics of incoherent scattering in the molecular system.
   - Interpret the data to understand the propagation of excitations, density
     fluctuations, and other incoherent modes within the system effectively.

7. **Plotting Suggestions:**
When analyzing the Dynamic Incoherent Structure Factor results, consider the
following plotting suggestions for better visualization and interpretation:

   - Plot the dynamic incoherent structure factor as a function of wave vector (Q)
   to observe the incoherent scattering behavior.
   - Create plots to compare the dynamic incoherent structure factor for different
   atom selections or group coordinates.
   - Use contour plots to visualize the evolution of the dynamic incoherent
   structure factor over time.

Dynamic Incoherent Structure Factor
'''''''''''''''''''''''''''''''''''

**Purpose:**

The Dynamic Incoherent Structure Factor analysis is a crucial tool for
understanding the dynamics of incoherent scattering in molecular systems. It
aims to help users efficiently harness the Dynamic Incoherent Structure Factor
feature, enabling them to acquire insights into intermediate incoherent
scattering functions and the resulting dynamic structure factor within the
system.

2. **Load Trajectory Data:**
   - Load the relevant trajectory data using the "File" menu.

3. **Access the "Dynamic Incoherent Structure Factor" Analysis:**
   - Navigate to the "Analysis" section within the MDANSE interface. Select the
     "Dynamic Incoherent Structure Factor" option from the list of available
     analysis tools.

4. **Configure Analysis Parameters:**
   - **Frames:** Specify the range of frames for analysis. (Default: First: 0,
     Last: Entire trajectory, Step: 1)
   - **Q Vectors:** Define the wave vectors (Q) based on the dynamics of
     incoherent scattering. (Default: User-defined)
   - **Atom Selection:** Choose the relevant atom selection and group
     coordinates for the analysis. (Default: All atoms)
   - **Atom Transmutation:** Determine atom transmutation and project
     coordinates as required for the calculation. (Default: None)
   - **Weights:** Set the necessary weights to accurately represent incoherent
     scattering lengths. (Default: Equal weights)
   - **Output Settings:** Configure output files and select the appropriate
     running mode for the analysis. (Default: Monoprocessor)

5. **Start the Calculation:**
   - Start the Dynamic Incoherent Structure Factor analysis by clicking on the
     "Run" button within the MDANSE interface. This will generate
     the data needed for plotting.

6. **Analyze and Interpret Results:**
   - Review the partial and total dynamic incoherent structure factor results to
     gain insights into the incoherent intermediate scattering functions and the
     dynamics of incoherent scattering in the molecular system.
   - Interpret the data to understand the propagation of excitations, density
     fluctuations, and other incoherent modes within the system effectively.

7. **Plotting Suggestions:**
   - When analyzing the Dynamic Incoherent Structure Factor results, consider
     the following plotting suggestions for better visualization and
     interpretation:
   - Plot the dynamic incoherent structure factor as a function of wave vector
     (Q) to observe the incoherent scattering behavior.
   - Create plots using "plt" to compare the dynamic incoherent structure factor
     for different atom selections or group coordinates.
   - Use contour plots to visualize the evolution of the dynamic incoherent
     structure factor over time.
   - Generate heat maps to represent the intensity of scattering as a function
     of Q and time, highlighting prominent features.


Elastic Incoherent Structure Factor
'''''''''''''''''''''''''''''''''''

**Purpose:**

The Elastic Incoherent Structure Factor (EISF) analysis  is
a vital tool for understanding the dynamics of incoherent scattering
within the molecular system. This guide aims to assist users in 
effectively utilizing the Elastic Incoherent Structure Factor feature 
to gain insights into the incoherent intermediate scattering functions 
and the EISF within the system.

1. **Launch MDANSE:**
   - Open the MDANSE software on your computer.

2. **Load Trajectory Data:**
   - Load the relevant trajectory data using the "File" menu.

3. **Access the "Elastic Incoherent Structure Factor" Analysis:**
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "Elastic Incoherent Structure Factor" option from the list of
     available analysis tools.

4. **Configure Analysis Parameters:**
   - **Frames:** Define the appropriate frames and Q vectors for precise
     calculations. (Default: All frames, User-defined Q vectors)
   - **Coordinates:** Specify the project coordinates, atom selection, and
     group coordinates as necessary for the analysis. (Default: All coordinates)
   - **Atom Transmutation:** Determine the atom transmutation and set the
     required weights for accurate calculations. (Default: None)
   - **Output Settings:** Configure output files and select the appropriate
     running mode for the analysis. (Default: Monoprocessor)

5. **Start the Calculation:**
   - Start the Elastic Incoherent Structure Factor analysis by clicking on the
     "Run" button within the MDANSE interface.

6. **Analyze and Interpret Results:**
   - Review the EISF results to gain insights into the sampling distribution of
     points in space and the dynamics of incoherent scattering within the
     molecular system.
   - Interpret the data to understand the behavior of the elastic line in the
     neutron scattering spectrum and its implications for the system's dynamics.

7. **Plotting Suggestions:**
     Incoherent Structure Factor (EISF) analysis results to enhance visualization
     and interpretation:
     - Plot the EISF as a function of wave vector (Q) to observe the incoherent
       scattering behavior.
     - Create line plots to analyze the behavior of the elastic line and the
       corresponding dynamics.
     - Use histograms to visualize the distribution of scattering points in space.
     - Generate 2D contour plots to explore correlations between Q vectors and
       their impact on the EISF.

Gaussian Dynamic Incoherent Structure Factor
''''''''''''''''''''''''''''''''''''''''''''

**Purpose:**

The Neutron Dynamic Total Structure Factor (NDTSF) analysis provides a
 evaluation of the coherent and incoherent contributions to the
scattering behavior in the molecular system, making it an essential tool for
neutron-specific studies.

**Guide Steps:**


2. **Load Trajectory Data:**
   - Load the relevant trajectory data using the "File" menu.

3. **Access the "Neutron Dynamic Total Structure Factor" Analysis:**
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "Neutron Dynamic Total Structure Factor" option from the
     list of available analysis tools.

4. **Configure Analysis Parameters:**
   - **Frames:** Define the appropriate frames for analysis. (Default: First: 0,
     Last: Entire trajectory, Step: 1)
   - **Instrument Resolution:** Specify the instrument resolution for accurate
     calculations. (Default: User-defined)
   - **Q Vectors:** Define the appropriate Q vectors for analysis. (Default:
     User-defined)
   - **Atom Selection:** Select the desired atom selection. (Default: All atoms)
   - **Atom Transmutation:** Configure atom transmutation and set the required
     weights for accurate calculations. (Default: None)
   - **Output Settings:** Set the output files and select the appropriate running
     mode for the analysis. (Default: Monoprocessor)

5. **Start the Calculation:**
   - Export the generated structure factor data to the desired output files for
     further analysis or visualization.

6. **Analyze and Interpret Results:**
   - Analyze the structure factor data to gain insights into the molecular
     structure, including information on the arrangement, spacing, and
     distribution of atoms within the system.

7. **Plotting Suggestions:**
   - Consider the following plotting suggestions for visualizing and interpreting
     the Neutron Dynamic Total Structure Factor (NDTSF) results:
     - Plot the NDTSF as a function of wave vector (Q) to observe the scattering
       behavior.
     - Generate contour plots or 2D representations to visualize the spatial
       distribution of scattering intensities.
     - Utilize color maps or heat maps to represent the intensity of scattering
       as a function of Q and time.
     - Explore the temporal evolution of the structure factor to understand
       dynamic changes within the system.


Neutron Dynamic Total Structure Factor
''''''''''''''''''''''''''''''''''''''

**Purpose:**

The Neutron Dynamic Total Structure Factor (NDTSF) analysis provides a
 evaluation of the coherent and incoherent contributions to the
scattering behavior in the molecular system, making it an essential tool for
neutron-specific studies.


2. **Load Trajectory Data:**
   - Load the relevant trajectory data using the "File" menu.

3. **Access the "Neutron Dynamic Total Structure Factor" Analysis:**
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "Neutron Dynamic Total Structure Factor" option from the
     list of available analysis tools.

4. **Configure Analysis Parameters:**
   - **Frames:** Define the appropriate frames for analysis. (Default: First: 0,
     Last: Entire trajectory, Step: 1)
   - **Resolution:** Specify the instrument resolution for accurate calculations.
     (Default: User-defined)
   - **Q Vectors:** Define the appropriate Q vectors for analysis. (Default:
     User-defined)
   - **Atom Selection:** Select the desired atom selection. (Default: All atoms)

5. **Start the Calculation:**
   - Export the generated structure factor data to the desired output files for
     further analysis or visualization.

6. **Analyze and Interpret Results:**
   - Analyze the structure factor data to gain insights into the molecular
     structure, including information on the arrangement, spacing, and
     distribution of atoms within the system.

7. **Plotting Suggestions:**
   - Consider the following plotting suggestions for visualizing and interpreting
     the Neutron Dynamic Total Structure Factor (NDTSF) results:
     - Plot the NDTSF as a function of wave vector (Q) to observe the scattering
       behavior.
     - Generate contour plots or 2D representations to visualize the spatial
       distribution of scattering intensities.
     - Utilize color maps or heat maps to represent the intensity of scattering
       as a function of Q and time.
     - Explore the temporal evolution of the structure factor to understand
       dynamic changes within the system.
