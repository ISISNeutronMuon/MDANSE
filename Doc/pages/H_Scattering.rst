How to Guide Analysis: Scattering
==================================

Current Correlation Function Analysis 
''''''''''''''''''''''''''''''''''''''

**Purpose:**

The Current Correlation Function analysis  is a valuable
tool for studying the propagation of excitations in disordered systems.
This guide aims to assist users in effectively utilizing 
the Current Correlation Function feature to gain insights 
into the dynamics of density fluctuations and propagating 
shear modes within the molecular system.

**Guide Steps:**

1. **Launch MDANSE:**
   Open the MDANSE software on your computer.

2. **Load Trajectory Data:**
   Load the relevant trajectory data using the "File" menu.

3. **Access the "Current Correlation Function" Analysis:**
   Navigate to the "Analysis" section within the MDANSE interface.
Select the "Current Correlation Function" option from the list of
available analysis tools.

4. **Configure Analysis Parameters:**
   - Define the appropriate parameters for frames and instrument resolution.
   - Specify the interpolation order for precise calculations.
- Select the interpolation mode based on the available hardware
and memory resources.
    Choose from the available options:
one-time in-memory interpolation [Default]: Fast but requires ample memory 
(recommended for small trajectories).
repeated interpolation Slower but memory-efficient (suitable for medium trajectories).
one-time disk interpolation Slower, low memory usage (for large trajectories,
SSD recommended).
    automatic mode 
- Set the number of preloaded frames if the "one-time
disk interpolation" mode is selected.[Default: 50].
    Adjust the value to optimize memory usage and analysis speed.

5. **Configure Q Vectors and Atom Selection:**
Define the Q vectors based on the requirements of the
analysis.
   Choose the relevant atom selection for the calculation.

6. **Normalize, Atom Transmutation, and Weights:**
   Specify whether normalization is required for the analysis.
Set the necessary atom transmutation and weights as per the
analysis requirements.

7. **Configure Output Files and Running Mode:**
   Define the output files based on the analysis requirements.
   Select the appropriate running mode to obtain the desired output.

8. **Initiate the Calculation:**
Start the Current Correlation Function analysis by clicking on the
"Run" or "Calculate" button within the MDANSE interface.

9. **Analyze and Interpret Results:**
Review the results to understand the dynamics of density fluctuations
and propagating shear modes within the molecular system effectively.

**Plotting Suggestions:**

Once you have obtained the results from the Current Correlation
Function analysis, consider the following plotting suggestions:

- Plot the Current Correlation Function as a function of
time or lag time to observe the decay behavior.
- Create plots to compare the Current Correlation Function for
different Q vectors or atom selections.
- Use log-scale plots for better visualization of long-time behavior.
- Overlay multiple Current Correlation Functions on a single plot
for comparative analysis.

Dynamic Coherent Structure Factor Analysis 
'''''''''''''''''''''''''''''''''''''''''''

**Purpose:**

The Dynamic Coherent Structure Factor analysis  is a
crucial tool for understanding the dynamics of coherent scattering in
disordered systems. This guide aims to assist users in effectively 
utilizing the Dynamic Coherent Structure Factor feature to 
gain insights into the intermediate coherent scattering functions 
and the subsequent dynamic structure factor in the molecular system.

**Guide Steps:**

1. **Launch MDANSE:**
   Open the MDANSE software on your computer.

2. **Load Trajectory Data:**
   Load the relevant trajectory data using the "File" menu.

3. **Access the "Dynamic Coherent Structure Factor" Analysis:**
   Navigate to the "Analysis" section within the MDANSE interface.
Select the "Dynamic Coherent Structure Factor" option from the list
of available analysis tools.

4. **Configure Analysis Parameters:**
- Define the appropriate frames and instrument resolution for precise
calculations.
- Specify the Q vectors based on the dynamics of
the coherent scattering within the system.
   - Choose the relevant atom selection for the analysis.
   - Determine the atom transmutation as required for the calculation.
- Set the necessary weights to represent coherent scattering lengths
accurately.
- Configure output files and select the appropriate running mode
for the analysis.

5. **Initiate the Calculation:**
Start the Dynamic Coherent Structure Factor analysis by clicking on
the "Run" or "Calculate" button within the MDANSE interface.

6. **Analyze and Interpret Results:**
- Review the partial and total dynamic coherent structure factor
results to gain insights into the coherent intermediate scattering functions
and the dynamics of coherent scattering in the molecular system.
- Interpret the data to understand the propagation of excitations,
density fluctuations, and propagating shear modes within the system effectively.

**Plotting Suggestions:**

After obtaining the Dynamic Coherent Structure Factor results, consider the
following plotting suggestions to visualize and interpret the data effectively:

- Plot the dynamic coherent structure factor as a function
of wave vector (Q) to observe the scattering behavior.
- Create contour plots to visualize the evolution of the
dynamic coherent structure factor over time.
- Use color maps to represent the intensity of scattering
as a function of Q and time.
- Generate radial distribution function plots to analyze the spatial
correlations in the system.

Dynamic Incoherent Structure Factor Analysis 
'''''''''''''''''''''''''''''''''''''''''''''

**Purpose:**

The Dynamic Incoherent Structure Factor analysis  is a
crucial tool for understanding the dynamics of incoherent scattering in
the molecular system. This guide aims to assist users in effectively
utilizing the Dynamic Incoherent Structure Factor feature to gain 
insights into the intermediate incoherent scattering functions 
and the subsequent dynamic structure factor within the system.

**Guide Steps:**

1. **Launch MDANSE:**
   Open the MDANSE software on your computer.

2. **Load Trajectory Data:**
   Load the relevant trajectory data using the "File" menu.

3. **Access the "Dynamic Incoherent Structure Factor" Analysis:**
   Navigate to the "Analysis" section within the MDANSE interface.
Select the "Dynamic Incoherent Structure Factor" option from the list
of available analysis tools.

4. **Configure Analysis Parameters:**
- Define the appropriate frames and instrument resolution for precise
calculations.
- Specify the Q vectors based on the dynamics of
the incoherent scattering within the system.
- Choose the relevant atom selection and group coordinates for
the analysis.
- Determine the atom transmutation and project coordinates as required
for the calculation.
- Set the necessary weights to represent incoherent scattering lengths
accurately.
- Configure output files and select the appropriate running mode
for the analysis.

5. **Initiate the Calculation:**
Start the Dynamic Incoherent Structure Factor analysis by clicking on
the "Run" or "Calculate" button within the MDANSE interface.

6. **Analyze and Interpret Results:**
- Review the partial and total dynamic incoherent structure factor
results to gain insights into the incoherent intermediate scattering functions
and the dynamics of incoherent scattering in the molecular system.
- Interpret the data to understand the propagation of excitations,
density fluctuations, and other incoherent modes within the system effectively.

**Plotting Suggestions:**

When analyzing the Dynamic Incoherent Structure Factor results, consider the
following plotting suggestions for better visualization and interpretation:

- Plot the dynamic incoherent structure factor as a function
of wave vector (Q) to observe the incoherent scattering behavior.
- Create plots to compare the dynamic incoherent structure factor
for different atom selections or group coordinates.
- Use contour plots to visualize the evolution of the
dynamic incoherent structure factor over time.
- Generate heat maps to represent the intensity of scattering
as a function of Q and time, highlighting prominent features.

Elastic Incoherent Structure Factor Analysis 
'''''''''''''''''''''''''''''''''''''''''''''

**Purpose:**

The Elastic Incoherent Structure Factor (EISF) analysis  is
a vital tool for understanding the dynamics of incoherent scattering
within the molecular system. This guide aims to assist users in 
effectively utilizing the Elastic Incoherent Structure Factor feature 
to gain insights into the incoherent intermediate scattering functions 
and the EISF within the system.

**Guide Steps:**

1. **Launch MDANSE:**
   Open the MDANSE software on your computer.

2. **Load Trajectory Data:**
   Load the relevant trajectory data using the "File" menu.

3. **Access the "Elastic Incoherent Structure Factor" Analysis:**
   Navigate to the "Analysis" section within the MDANSE interface.
Select the "Elastic Incoherent Structure Factor" option from the list
of available analysis tools.

4. **Configure Analysis Parameters:**
- Define the appropriate frames and Q vectors for precise
calculations.
- Specify the project coordinates, atom selection, and group coordinates
as necessary for the analysis.
- Determine the atom transmutation and set the required weights
for accurate calculations.
- Configure output files and select the appropriate running mode
for the analysis.

5. **Initiate the Calculation:**
Start the Elastic Incoherent Structure Factor analysis by clicking on
the "Run" or "Calculate" button within the MDANSE interface.

6. **Analyze and Interpret Results:**
- Review the EISF results to gain insights into the
sampling distribution of points in space and the dynamics of
incoherent scattering within the molecular system.
- Interpret the data to understand the behavior of the
elastic line in the neutron scattering spectrum and its implications
for the system's dynamics.

**Plotting Suggestions:**

When working with Elastic Incoherent Structure Factor (EISF) analysis results,
consider the following plotting suggestions to visualize and interpret the
data effectively:

- Plot the EISF as a function of wave vector
(Q) to observe the incoherent scattering behavior.
- Create line plots to analyze the behavior of the
elastic line and the corresponding dynamics.
- Use histograms to visualize the distribution of scattering points
in space.
- Generate 2D contour plots to explore correlations between Q
vectors and their impact on the EISF.

Gaussian Dynamic Incoherent Structure Factor Analysis 
''''''''''''''''''''''''''''''''''''''''''''''''''''''

**Purpose:**

The Gaussian Dynamic Incoherent Structure Factor (GDIF) analysis 
is a valuable tool for understanding the dynamics of incoherent
scattering within the molecular system using the Gaussian approximation.
This guide aims to assist users in effectively utilizing the Gaussian Dynamic 
Incoherent Structure Factor feature to gain insights into the incoherent 
intermediate scattering functions and their relationship to the 
mean-square displacements within the system.

**Guide Steps:**

1. **Launch MDANSE:**
   Open the MDANSE software on your computer.

2. **Load Trajectory Data:**
   Load the relevant trajectory data using the "File" menu.

3. **Access the "Gaussian Dynamic Incoherent Structure Factor" Analysis:**
   Navigate to the "Analysis" section within the MDANSE interface.
Select the "Gaussian Dynamic Incoherent Structure Factor" option from the
list of available analysis tools.

4. **Configure Analysis Parameters:**
- Define the appropriate frames and Q shells for precise
calculations.
- Specify the instrument resolution, project coordinates, and other relevant
parameters.
- Determine the atom selection and group coordinates as necessary
for the analysis.
- Configure atom transmutation and set the required weights for
accurate calculations.
- Set the output files and select the appropriate running
mode for the analysis.

5. **Initiate the Calculation:**
Start the Gaussian Dynamic Incoherent Structure Factor analysis by clicking
on the "Run" or "Calculate" button within the MDANSE interface.

6. **Analyze and Interpret Results:**
- Review the GDIF results to gain insights into the
incoherent intermediate scattering functions within the molecular system using the
Gaussian approximation.
- Interpret the data to understand the dynamics of incoherent
scattering and their relationship to the mean-square displacements within the
system.

**Plotting Suggestions:**

When analyzing the Gaussian Dynamic Incoherent Structure Factor (GDIF) results,
consider the following plotting suggestions to visualize and interpret the
data effectively:

- Plot the GDIF as a function of wave vector
(Q) to observe the incoherent scattering behavior.
- Create line plots or histograms to explore the relationship
between GDIF and mean-square displacements.
- Use 2D contour plots to visualize correlations between Q
vectors and GDIF values.
- Generate error bars or confidence intervals to represent uncertainty
in GDIF calculations.



Neutron Dynamic Total Structure Factor Analysis 
''''''''''''''''''''''''''''''''''''''''''''''''

**Purpose:**

The Neutron Dynamic Total Structure Factor (NDTSF) analysis provides a
comprehensive evaluation of the coherent and incoherent contributions to the
scattering behavior in the molecular system, making it an essential tool for
neutron-specific studies.

**Guide Steps:**

1. **Launch MDANSE:**
   Open the MDANSE software on your computer.

2. **Load Trajectory Data:**
   Load the relevant trajectory data using the "File" menu.

3. **Access the "Neutron Dynamic Total Structure Factor" Analysis:**
   Navigate to the "Analysis" section within the MDANSE interface.
Select the "Neutron Dynamic Total Structure Factor" option from the
list of available analysis tools.

4. **Configure Analysis Parameters:**
- Define the appropriate frames, instrument resolution, and Q vectors
for accurate calculations.
   - Select the desired atom selection

5. **Initiate the Calculation:**
Export the generated structure factor data to the desired output
files for further analysis or visualization.

6. **Analyze and Interpret Results:**
Analyze the structure factor data to gain insights into the
molecular structure, including information on the arrangement, spacing, and distribution
of atoms within the system.
no keep this information but format it like the one
above



