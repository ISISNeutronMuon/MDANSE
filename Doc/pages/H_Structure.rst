Running Structure Calculations
==============================

Area Per Molecule
-----------------
Index 1: GUI Area Per Molecule

**Purpose:** The Area Per Molecule analysis calculates the surface area occupied
by each molecule within a molecular system. This is essential for understanding
the spatial distribution of molecules and their interactions with the surrounding
environment.


2. **Load Molecular Data**:
   - Click on the "File" menu.
   - Select "Load Molecular Data" and choose your data file.

3. **Access the "Area Per Molecule" Analysis**:
   - In the MDANSE interface, navigate to the "Analysis" section.
   - Locate and select "Area Per Molecule" from the available analysis options.

4. **Configure Settings**:
   - *Frames*: Specify the frames or time points for Area Per Molecule
     calculation (Default: First: 0, Last: All, Step: 1).
   - *Molecule Name*: Specify the name of the molecules for which the calculation
     will take place (Default: DMPC). The name inputted here must match a name in
     the HDF file.
   - *Output Files (Optional)*: Configure output file settings if necessary.

5. **Run the Calculation**:
   - Click on the "Run" button to initiate the Area Per Molecule calculation.

6. **Review Results**:
   - After the calculation, access and interpret the Area Per Molecule results.

7. **Suggested Plots**:
   - *Area Per Molecule Plot*: Visualize the distribution of surface area occupied
     by individual molecules within the system.

Coordination Number
--------------------
Index 2: GUI Coordination Number

**Purpose:** The Coordination Number analysis determines the number of neighboring
atoms or molecules that are within a specified distance of a central atom or
molecule. This is crucial for understanding the local environment and bonding in a
material or molecular system.


2. **Load Atomic or Molecular Data**:
   - Click on the "File" menu.
   - Select "Load Atomic/Molecular Data" and choose your data file.

3. **Access the "Coordination Number" Analysis**:
   - In the MDANSE interface, navigate to the "Analysis" section.
   - Locate and select "Coordination Number" from the available analysis options.

4. **Configure Settings**:
   - *Central Atom/Molecule Selection*: Choose the atom or molecule of interest for
     which you want to calculate the coordination number.
   - *Cutoff Distance*: Define the maximum distance from a central particle in
     nanometers for considering neighboring atoms or molecules (Default: threshold
     based on loaded data, maximum distance of interacting particles).
   - *Frames*: Specify the frames or time points for Coordination Number calculation
     (Default: First: 0, Last: All, Step: 1).
   - *r values*:
     - *from*: Set the minimum distance from a central particle in nanometers taken
       into consideration (Default: 0).
     - *to*: Set the maximum distance from a central particle in nanometers. Only
       particles up to and including this distance will be counted (Default: 10).
     - *by step of*: Define the size of the step in nanometers used to generate a
       range of values between the above two extremes (Default: 1). For example, using
       the default r-values, the range will be {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10}.
   - *Output Files (Optional)*: Configure output file settings if needed.

5. **Run the Calculation**:
   - Click on the "Run" button to initiate the Coordination Number calculation.

6. **Review Results**:
   - After the calculation, access and interpret the Coordination Number results.

7. **Suggested Plots**:
   - *Coordination Number Histogram*: Visualize the distribution of coordination
     numbers for the selected central atom or molecule.


Density Profile
---------------
Index : GUI Density Profile

**Purpose:** The Density Profile analysis calculates the spatial distribution of
particles or molecules along a specific axis within a simulation box. It provides
insights into how the density of particles varies across the system.

2. **Load Atomic or Molecular Data**:
   - Click on the "File" menu.
   - Select "Load Atomic/Molecular Data" and choose your data file.

3. **Access the "Density Profile" Analysis**:
   - In the MDANSE interface, navigate to the "Analysis" section.
   - Locate and select "Density Profile" from the available analysis options.

4. **Configure Settings**:
   - *Axis Selection*: Choose the simulation box axis (e.g., x, y, z) along which you
     want to calculate the density profile (Default: c).
   - *Binning and Range*: Define the bin size and range for the density profile
     calculation (Default based on particle distribution in loaded data).
   - *dr*: During Density Profile calculation, the axis specified in the "Axis" field
     is divided into a number of bins along its length. "dr" specifies how large each
     of these bins will be (Default: 0.01).
   - *Weights*: Configure the weights for Density Profile calculation (Default: Equal).
   - *Output Files (Optional)*: Configure output file settings as needed.
   - *Running Mode*: Select the desired running mode for the calculation.

5. **Run the Calculation**:
   - Click on the "Run" button to initiate the Density Profile calculation.

6. **Review Results**:
   - After the calculation, access and interpret the Density Profile results.

7. **Suggested Plots**:
   - *Density Profile Plot*: Visualize the spatial distribution of particles or
     molecules along the selected axis



Eccentricity
------------
Index 4: GUI Eccentricity

**Purpose:** The Eccentricity analysis calculates the eccentricity of molecules
within a molecular system. Eccentricity measures how elongated or flattened a
molecule is, providing insights into its shape and structure.


2. **Load Molecular Data**:
   - Click on the "File" menu.
   - Select "Load Molecular Data" and choose your data file.

3. **Access the "Eccentricity" Analysis**:
   - In the MDANSE interface, navigate to the "Analysis" section.
   - Locate and select "Eccentricity" from the available analysis options.

4. **Configure Settings**:
   - *Frames*: Specify the frames or time points for the Eccentricity calculation
     (Default: First: 0, Last: All, Step: 1).
   - *Output Files (Optional)*: Configure output file settings if necessary
     (Default: Customizable).

5. **Run the Calculation**:
   - Click on the "Run" button to initiate the Eccentricity calculation.

6. **Review Results**:
   - After the calculation, access and interpret the Eccentricity results.

7. **Suggested Plots**:
   - *Eccentricity Histogram*: Visualize the distribution of eccentricity values for
     the molecules within the system.


Molecular Trace Analysis
------------------------
Index : GUI Molecular Trace Analysis

**Purpose:** The Molecular Trace analysis in MDANSE facilitates the visualization
and examination of the trajectories of selected atoms or groups within the
molecular system. By tracing the spatial paths of specific entities, researchers
can gain valuable insights into the movement, behavior, and interactions of these
molecular components, aiding in the comprehensive analysis of the system's dynamics.


.

2. **Load Atomic Data:**
   - Load the trajectory data or the relevant atomic information using the "File"
     menu.

3. **Access the "Molecular Trace" Analysis:**
   - Navigate to the "Analysis" section within the MDANSE interface.
   - Select the "Molecular Trace" option from the list of available analysis tools.

4. **Configure Analysis Settings:**
   - Specify the range of frames or time points for the analysis.
   - Choose the specific atoms or groups for which the molecular trace will be
     generated (Default: First: 0, Last: All, Step: 1).
   - Set the spatial resolution, determining the number of grid points used to
     represent a unit of length in the trace (Default: 0.1).

5. **Configure Output Settings (Optional):**
   - Customize the output file settings based on your preferences and requirements
     for data analysis and documentation.

6. **Choose Running Mode:**
   - Select the appropriate running mode according to the nature of the analysis
     and the desired output.

7. **Run the Calculation:**
   - Initiate the Molecular Trace analysis by clicking on the "Run" within the
     MDANSE interface.

8. **Review and Interpret Results:**
   - After the analysis is complete, review and interpret the Molecular Trace
     results.
   - Suggested Plots:
     - *Molecular Trace Visualization:* Generate trajectory plots to visualize the
       movement and interactions of selected atoms or groups.


Pair Distribution Function (PDF)
--------------------------------
Index : GUI Pair Distribution Function (PDF)

**Purpose:** The Pair Distribution Function (PDF) analysis is used to calculate
the probability density of finding one atom at a certain distance from another
atom within a material or system. It provides insights into the atomic radial
packing, helping researchers understand the spatial distribution of atoms.



2. **Load Atomic Data:**
   - Click on the "File" menu.
   - Select "Load Atomic Data" and choose your data file.

3. **Access the "Pair Distribution Function (PDF)" Analysis:**
   - In the MDANSE interface, navigate to the "Analysis" section.
   - Locate and select "Pair Distribution Function (PDF)" from the available
     analysis options.

4. **Configure Settings:**
   - Frames: Specify the frames or time points for PDF calculation (Default:
     First: 0, Last: All, Step: 1).
   - r Values: Define the range of radial distances (r values) for PDF analysis.
     (Default: from 0 to 10 by step of 1, r based on loaded data Atomic structure).
   - Atom Selection: Choose the atoms or particles to include.

5. **Output Files (Optional):**
   - Configure output file settings if necessary.

6. **Run the Calculation:**
   - Click on the "Run" button to initiate the PDF calculation.

7. **Review Results:**
   - After the calculation, access and interpret the Pair Distribution Function
     (PDF) results.
   - Suggested Plots:
     - *Pair Distribution Function (PDF) Plot:* Visualize the PDF as a function
       of radial distance, providing insights into atomic radial packing.


Static Structure Factor
-----------------------
Index : GUI Static Structure Factor (General)

**Purpose:** The Static Coherent Structure Factor analysis aims to calculate the
structure factor, which characterizes the atomic arrangements in reciprocal
space. It is particularly useful for understanding the scattering of X-rays or
neutrons from a material, providing information about its crystalline structure.

2. **Load Atomic Data:**
   - Click on the "File" menu.
   - Select "Load Atomic Data" and choose your data file.

3. **Access the "Static Structure Factor" Analysis:**
   - In the MDANSE interface, navigate to the "Analysis" section.
   - Locate and select "Static Structure Factor" from the available analysis options.

4. **Configure Settings:**
   - *Frames:* Specify the frames or time points for Static Structure Factor
     calculation (Default: First: 0, Last: All, Step: 1).
   - *r Values:* Define the range of radial distances (r values) and q values for
     the analysis (Default: (r) based on loaded data Atomic structure, (q) loaded
     data reciprocal lattice).
   - *Reference Frame:* Specify the number of the frame to be used as a reference
     for the calculation (Default: 0). The deviation will be calculated as how it
     deviates from the values in this frame.
   - *Atom Selection:* Choose the atoms or particles to include.
   - *Atom Transmutation (Optional):* Configure atom transmutation settings if needed.
   - *Weights (Optional):* Set up weights for the analysis (Default: Equal).
   - *Output Files (Optional):* Configure output file settings as required.

5. **Run the Calculation:**
   - Click on the "Run" button to initiate the Static Structure Factor calculation.

6. **Review Results:**
   - After the calculation, access and interpret the Static Structure Factor
     results.
   - Suggested Plots:
     - *Static Structure Factor Plot:* Visualize the Static Structure Factor,
       providing information about the atomic arrangements in reciprocal space.

Root Mean Square Deviation (RMSD)
----------------------------------
Index : GUI Root Mean Square Deviation (RMSD)

**Purpose:** The Root Mean Square Deviation (RMSD) analysis is employed for
measuring the structural similarity or deviation between different frames or
configurations of a molecular system. It helps track how a molecular structure
changes over time.


2. **Load Atomic Data:**
   - Click on the "File" menu.
   - Select "Load Atomic Data" and choose your data file.

3. **Access the "Root Mean Square Deviation (RMSD)" Analysis:**
   - In the MDANSE interface, navigate to the "Analysis" section.
   - Locate and select "Root Mean Square Deviation (RMSD)" from the available
     analysis options.

4. **Configure Settings:**
   - *Reference Frames:* Set reference frames for RMSD calculation (Default:
     First: 0, Last: All, Step: 1).
   - *Atom Selection:* Choose the atoms or particles to include in the analysis.
   - *Output Files (Optional):* Configure any specific output file settings.

5. **Run the Calculation:**
   - Click on the "Run" or "Calculate" button to initiate the RMSD calculation.

6. **Review Results:**
   - After the calculation, access and interpret the RMSD results.
   - Suggested Plots:
     - *RMSD Plot:* Visualize RMSD values over time, indicating structural changes.



Radius Of Gyration (ROG)
--------------------------
Index : GUI Radius Of Gyration (ROG)

**Purpose:** The Radius of Gyration can be used, for example, to
determine the compactness of a molecule. It is calculated as a root
(mass weighted) mean square distance of the atoms of a molecule relative to
its centre of mass. *ROG* can be used to follow the size and spread
of a molecule during the molecular dynamics simulation.

2. **Load Atomic Data:**
   - Click on the "File" menu.
   - Select "Load Atomic Data" and choose your data file.

3. **Access the "Radius Of Gyration (ROG)" Analysis:**
   - In the MDANSE interface, navigate to the "Analysis" section.
   - Locate and select "Radius Of Gyration (ROG)" from the available analysis
     options.

4. **Configure Settings:**
   - *Frames:* Specify the frames or time points for ROG calculation.
   - *Atom Selection:* Choose the atoms or particles to include.
   - *Output Files (Optional):* Configure output file settings as required.
   - *Weights (Optional):* Configure weights for the analysis if applicable
     (Default: Equal).
   - *Output Files (Optional):* Set up output file settings as needed.

5. **Run the Calculation:**
   - Click on the "Run" button to initiate the ROG calculation.

6. **Review Results:**
   - After the calculation, access and interpret the ROG results.
   - Suggested Plots:
     - *ROG Plot:* Visualize ROG values over time, indicating molecular
       compactness changes.


Solvent Accessible Surface
--------------------------
Index : GUI Solvent Accessible Surface

**Purpose:** The Solvent Accessible Surface analysis calculates the surface area
accessible to a solvent molecule within a molecular system. This analysis provides
valuable information about the surface properties of molecules and their
interactions with solvent molecules.

2. **Load Molecular Data**:
   - Access the "File" menu.
   - Select "Load Molecular Data" to load your data file.

3. **Access the "Solvent Accessible Surface" Analysis**:
   - Within the MDANSE interface, navigate to the "Analysis" section.
   - Choose "Solvent Accessible Surface" from the list of available analysis options.

4. **Configure Analysis Settings**:
   - *Frames*: Specify the frames or time points for the Solvent Accessible Surface
     calculation.
   - *Atom Selection*: Choose the atoms or molecules for which the analysis will be
     performed.
   - *n Sphere Points*: Define the number of points to create in the mesh around
     each atom or molecule (Default: 1000). This determines the density of points
     used in the calculation.
   - *Probe Radius*: Set the probe radius (in nanometers, Default: 0.14) that
     affects the observed surface area. A smaller probe radius detects more detail
     and reports a larger surface area. The default value is approximately equal to
     the radius of a water molecule.

5. **Run the Calculation**:
   - Initiate the Solvent Accessible Surface calculation by clicking the "Run" button.

6. **Review Results**:
   - After the calculation, access and interpret the Solvent Accessible Surface
     results.

7. **Suggested Plots**:
   - *Solvent Accessible Surface Plot*: Visualize the surface area accessible to
     solvent molecules within the system.


Static Structure Factor
-----------------------
Index : GUI Static Structure Factor (General)

**Purpose:** The Static Structure Factor calculation is used to calculate the
scattering of waves (like X-rays) off a material, revealing the arrangement and
interaction of atoms or molecules. This is crucial for understanding the
internal structure of both ordered and disordered materials, from crystals to
glasses and liquids, at the atomic level.


2. **Load Atomic Data:**
   - Click on the "File" menu.
   - Select "Load Atomic Data" and choose your data file.

3. **Access the "Static Structure Factor" Analysis:**
   - In the MDANSE interface, navigate to the "Analysis" section.
   - Locate and select "Static Structure Factor" from the available analysis
     options.

4. **Configure Settings:**
   - *Frames:* Specify the frames or time points for Static Structure Factor
     calculation (Default: First: 0, Last: All, Step: 1).
   - *r Values:* Define the range of radial distances (r values) and q values for
     the analysis (Default: From 0 to 10 nanometers, Step of 1).
   - *q Values:* Define the range of wavevector values (q values) for the analysis
     (Default: From 0 to 10).
   - *Atom Selection:* Choose the atoms or particles to include.
   - *Atom Transmutation (Optional):* Configure atom transmutation settings if
     needed.
   - *Weights (Optional):* Set up weights for the analysis (Default: Equal).
   - *Output Files (Optional):* Configure output file settings as required.

5. **Run the Calculation:**
   - Click on the "Run" button to initiate the Static Structure Factor calculation.

6. **Review Results:**
   - After the calculation, access and interpret the Static Structure Factor
     results.

7. **Suggested Plots:**
   - *Radial Distribution Function (RDF) Plot:* Show the radial distribution of
     particle pairs, which can help visualize the static structure factor.
   - *Structure Factor Plot:* Display the calculated Static Structure Factor as a
     function of wavevector q.
   - *Atom Pair Correlation Plot:* Show the correlation between specific atom pairs
     as a function of distance.

Voronoi Analysis
-----------------

**Purpose:** Voronoi analysis is used to calculate Voronoi tessellation, which
partitions space into cells around each atom or molecule in a system. This
provides valuable insights into the spatial arrangement of particles.


2. **Load Atomic or Molecular Data:**
   - Click on the "File" menu.
   - Select "Load Atomic/Molecular Data" and choose your data file.

3. **Access the Voronoï Analysis:**
   - In the MDANSE interface, navigate to the "Analysis" section.
   - Locate and select "Voronoï" from the available analysis options.

4. **Configure Settings:**
   - *Frames:* Specify the frames or time points for Voronoï analysis.
   - *Apply Periodic Boundary Condition:* Choose whether to apply periodic
     boundary conditions to the Voronoi cells (Default: True).
   - *PBC Border Size:* Define the size of the border for applying periodic
     boundary conditions (Default: 0.0).
   - *Output Files (Optional):* Configure output file settings as required.
   - *Running Mode:* Select the appropriate running mode for the analysis.

5. **Run the Calculation:**
   - Click on the "Run" button to initiate the Voronoï analysis.

6. **Review Results:**
   - After the calculation, access and interpret the Voronoï analysis results.

7. **Suggested Plots:**
   - *Voronoï Cell Visualization:* Visualize the Voronoï cells around each atom
     or molecule in the system to understand their spatial distribution.

X-ray Static Structure Factor
-----------------------------
Index 13: GUI Static Structure Factor (X-ray)

**Purpose:** Calculate the X-ray Static Structure Factor. This analysis provides
detailed insights into the arrangement of atoms or molecules within the material,
helping to understand its crystalline or amorphous structure.

2. **Load Atomic Data:**
   - Click on the "File" menu.
   - Select "Load Atomic Data" and choose your data file.

3. **Access the "X-ray Static Structure Factor" Analysis:**
   - In the MDANSE interface, navigate to the "Analysis" section.
   - Locate and select "X-ray Static Structure Factor" from the available analysis options.

4. **Configure Settings:**
   - *Frames:* Specify the frames or time points for X-ray Static Structure Factor
     calculation (Default: First: 0, Last: All, Step: 1).
   - *r Values:* Define the range of radial distances (r values) and q values for the
     analysis (Default: From 0 to 10 nanometers, Step of 1).
   - *Atom Selection:* Choose the atoms or particles to include.
   - *Atom Transmutation (Optional):* Configure atom transmutation settings if needed.
   - *Weights (Optional):* Set up weights for the analysis (Default: Equal).
   - *Output Files (Optional):* Configure output file settings as required.

5. **Run the Calculation:**
   - Click on the "Run" button to initiate the X-ray Static Structure Factor calculation.

6. **Review Results:**
   - After the calculation, access and interpret the X-ray Static Structure Factor
     results.

7. **Suggested Plots:**
   - *X-ray Scattering Pattern:* Display the X-ray scattering pattern, which is
     related to the X-ray Static Structure Factor.
   - *Pair Distribution Function (PDF) Plot:* Show the PDF as a function of radial
     distance, which is related to the X-ray structure factor.
   - *Atomic Form Factor Plot:* Visualize the atomic form factor as a function of
     scattering angle.
