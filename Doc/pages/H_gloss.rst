Configuring Parameters
======================

**Purpose:**
This  guide provides detailed instructions for configuring parameters
and running analyses within an MDANSE Analysis window. It covers the common
structure of MDANSE Analysis windows and guides you through the process of
customizing parameters for specific analyses.

1. **Access an Analysis Tool:**
   - Access the desired analysis tool tailored to your specific research needs by
     navigating to the "Analysis" section in MDANSE.

2. **Load Trajectory Data in HDF Format:**
   - In the trajectory box, specify the path to the trajectory data file in HDF
     (Hierarchical Data Format) format. This format is commonly used for efficient
     storage and retrieval of trajectory data. It serves as the data source for
     your analysis.

     .. note::
        Trajectory data in HDF format is preferred due to its advantages in terms
        of data organization and access speed.

3. **Configure Analysis Parameters:**
   - Explore and configure the parameters that are specific to the chosen analysis
     tool. These parameters may vary between analyses and are crucial for
     customizing your analysis.

   - **Frames Configuration:**
     - Adjust the "Frames" parameters to define the range of frames to be
       considered for the analysis:
       - *First Frame (Default: 0):* Determine the starting frame for your
         analysis. It indicates the initial point of data consideration.
       - *Last Frame (Default: Last frame in the trajectory):* Set the endpoint
         for your analysis. This frame marks the conclusion of data inclusion.
       - *Frame Step (Default: 1):* Control the frequency of frame selection.
         Higher values skip frames at defined intervals, optimizing the analysis
         duration.

4. **Customize Parameters for Your Analysis:**
   - Tailor the parameters to match the specifics of your analysis:
     - Explore and adjust analysis-specific parameters, such as axis selection,
       output settings, and configuration options. These parameters are essential
       for fine-tuning your analysis based on your research objectives.

5. **Utilize the Buttons:**
   - At the bottom of the Analysis window, you'll find several buttons:
     - **Save:** Use the "Save" button to preserve the current analysis, including
       your configured options, into a Python script. This script can be executed
       from the command line, promoting reproducibility and automation.
     - **Run:** Start the analysis process by clicking the "Run" button. Upon
       completion, you'll be prompted to decide whether you want to close the
       window. Note that the status of the analysis can be monitored in the Jobs
       panel. Keep in mind that there is a known bug where successful analyses may
       not always display in the Jobs panel.




Q Shells
-------

**Purpose:**
Q Shells in MDANSE are fundamental for scattering experiments and related analyses.
They play a crucial role in defining the distribution of Q vectors in reciprocal space,
which directly impacts the accuracy and scope of your analysis.

Define Q Shell Parameters
'''''''''''''''''''''''''

To effectively configure Q Shells in your MDANSE analysis, follow these steps:

   - Open your MDANSE analysis and locate the "Q Shells" configuration.

   - Configure the following parameters:

     - **From (Default: 0):** This parameter sets the lowest value of |Q| to be used
       in Q-vector generation. It defines the starting point for your Q vectors.

     - **To (Default: 10):** Define the highest value of |Q| to be used in your
       analysis. This parameter sets the upper limit for Q vectors.

     - **By Step of (Default: 1):** Specify the increment value for |Q| when
       transitioning from one Q-shell to the next. This parameter determines the
       spacing between Q vectors. Adjust the "Width" parameter accordingly when
       changing the step.


Adjust for Specific Analysis
''''''''''''''''''''''''''''

Customize the Q shell parameters based on the specific requirements of your analysis:

   - Depending on your analysis objectives and the characteristics of your molecular
     system, you may need to tailor the Q shell parameters to align with scattering
     experiment data effectively.

   - Consider the range and density of Q vectors required to capture the relevant
     structural and dynamical information in your system.

   - Collaborate with domain experts or refer to relevant literature to ensure that
     your Q shell configuration is suitable for your research goals.

The accuracy and relevance of your MDANSE analysis results depend significantly on
how well you configure the Q Shells. Properly adjusted Q shell parameters enable you
to extract valuable insights from scattering experiments and advance your understanding
of molecular systems.


Creating Selections
-------------------

**Purpose:**
In MDANSE, creating selections is a powerful way to fine-tune your analysis,
enabling you to precisely target specific data subsets or criteria. These
selections offer various methods to modify your analysis, enhancing the precision
and relevance of your results.

Understand Selection Types
''''''''''''''''''''''''''

MDANSE provides several types of selections, each designed for specific purposes:

   - Axis Selection/Reference Basis (Default: None): Allows you to choose
     reference axes for your analysis.
   - Atom Selection (Default: None): Enables you to select specific atoms or
     groups of atoms in your molecular system.
   - Atom Transmutation (Default: None): Provides the capability to change atom
     types during analysis.
   - Atom Charges (Default: None): Allows you to manipulate atom charges for
     advanced analysis.
   - Q Vectors (explored separately in the next section): Defines the distribution
     of Q vectors in reciprocal space for scattering experiments.

Access Selection Configuration
''''''''''''''''''''''''''''''

   - Depending on your analysis needs, you can access selection configurations from
     within the MDANSE analysis window or the Molecular Viewer.

Creating Selections Manually
''''''''''''''''''''''''''''

   - By default, MDANSE does not save any selections, requiring you to create them
     manually. These selections are specific to a trajectory HDF file.

Ensure Unique Naming
''''''''''''''''''''

   - To prevent conflicts, assign each selection a unique name, even if you're
     creating the same selection for multiple trajectories. This practice ensures
     proper organization and prevents the overwriting of selections.

Utilize User Definition Viewer
''''''''''''''''''''''''''''''

   - The User Definition Viewer, accessible from the toolbar, simplifies
     selection management. It provides an overview of all saved selections,
     streamlining the selection process.

**Step 6: Save Your Selections**

   - To save a selection, follow these steps:
     1. Enter a distinctive name for your selection in the provided field next to
        the Save button.
     2. Click the Save button to store the selection. This action saves the
        selection without closing the selection window.


Axis Selection/Reference Basis
-------------------------------

**Purpose:** In MDANSE, Axis Selection/Reference Basis allows you to choose
reference axes for your analysis. This selection is vital for specific analyses
such as Angular Correlation and Order Parameter.

**Step 1: Access Axis Selection** Inside an analysis window, find the Axis
Selection/Reference Basis configuration. This section enables you to select
reference axes for your analysis.

**Step 2: Create Definitions**

- From the drop-down menu, select one of the existing axis definitions. These
  definitions are based on the number of selected atoms required for the
  analysis. Only definitions matching the analysis's requirements will appear.
- To create a new definition, click the "New definition" button, opening the
  configuration window.

**Step 3: Define Axis Selection**

The "Number of atoms" field will be automatically set to the number of atoms
required for the analysis. To select atoms, click the "+" button in the
"Molecules" list, displaying the atoms within a molecule. Double-click on an
atom to add it to the "Selected atoms" list, along with its details. To remove
an atom from the selection, click on it in the "Selected atoms" list and press
the Delete key.

**Step 4: Utilize User Definition Viewer**

Access the User Definition Viewer from the toolbar to manage and view all saved
axis selections.

**Step 5: Save Your Axis Selection**

To save your selection, provide it with a unique name in the field next to the
"Save" button. Click the "Save" button to store the selection. This action saves
the selection without closing the selection window.

Axis Selection/Reference Basis is essential for fine-tuning your analysis by
specifying reference axes, contributing to the accuracy and relevance of your
results.

Atom Selection
--------------

**Purpose:** Atom Selection in MDANSE enables you to select specific atoms or
groups of atoms in your molecular system for analysis customization.

**Step 1: Access Atom Selection**

Inside an analysis window, find the Atom Selection configuration. Atom Selection
allows you to choose which atoms or particles to include in your analysis.

**Step 2: Add Selections**

The green button adds a line for another selection, allowing you to choose
additional selections for your analysis. You can include multiple selections to
focus on different sets of particles. You can remove a line by clicking the red
button. Use the drop-down menu and the "View selected definition" button to
manage selections.

**Step 3: Create Atom Selections**

Click the "Set new selection" button to open the configuration window. Here, you
can define the criteria for selecting atoms.

**Step 4: Define Selection Criteria**

Utilize the "Filter by" field to access particles in the trajectory. Selecting a
filter will display relevant particles in the top right box. Click
particles/groups to highlight them and add them to the selection list. Perform
complex selections by combining logical operations.

**Step 5: Name and Save Your Selection**

Name each selection uniquely in the field next to the "Save" button. Click
"Save" to store the selection. This action saves the selection without closing
the Atom Selection window.

Atom Selection provides flexibility to tailor your analysis by selecting specific
particles, enhancing the precision and relevance of your results.

Atom Transmutation
------------------

**Purpose:** Atom Transmutation in MDANSE simulates isotopic substitution,
allowing you to define the atomic makeup of selected particles.

**Step 1: Access Atom Transmutation**

Inside an analysis window, find the Atom Transmutation configuration. Atom
Transmutation allows you to change the chemical element of selected atoms in
your analysis.

**Step 2: Select an Atom Selection**

Choose an Atom Selection from the left drop-down menu. Atom Transmutation is
applied to the selected particles in this selection.

**Step 3: Define Transmutation Element**

Use the white drop-down menu next to the red button to choose the element to
which the selected atoms will be transmuted.

Atom Transmutation allows you to customize the atomic composition of selected
particles, particularly useful for simulating isotopic substitutions in your
analysis.

Creating Spherical Lattice Vectors
------------------------------------

**Purpose:**

Spherical Lattice Vectors in MDANSE are used to generate a set of hkl vectors
compatible with the simulation box. This guide will walk you through the
process of creating spherical lattice vectors for your analysis.

**Step 1: Access Spherical Lattice Vectors**

Open the MDANSE analysis window. Look for the "Spherical Lattice Vectors"
section within the Q Vectors configuration.

**Step 2: Define Vector Parameters**

When configuring Spherical Lattice Vectors in MDANSE, it's essential to specify
the following parameters:

**Seed:**
- (Default: 0)
- The "Seed" parameter is an integer used to initialize the random number
  generation process, ensuring reproducibility. Modify it for different vector
  sets.

**Q Shells:**
- (Default: 50)
- The "Q Shells" parameter, an integer, determines the number of hkl vectors in
  each shell. More vectors increase accuracy but extend computation time.

**Width:**
- (Default: 1.0)
- The "Width" parameter, a float, sets the tolerance for each shell. Usually, it
  matches the step value. A smaller width improves Q resolution. Adjust it as
  needed for your analysis.

**Step 3: Generate Vectors**

Click the "Generate" button to create the hkl vectors based on the specified
parameters. These vectors will be used for your analysis, so ensure the settings
are appropriate.

**Step 4: Name Your Vectors**

In the empty box at the bottom of the window, provide a name for the generated
vectors. A descriptive name helps you identify the vectors for future reference.

**Step 5: Save the Vectors**

Click the "Save" button to save the generated spherical lattice vectors. Your
vectors are now ready to be used in your analysis.

**Step 6: Additional Notes**

- The "Generate" button must be clicked before saving the vectors.
- These vectors are useful for computations like the dynamical coherent
  structure factor on an isotropic sample, such as a liquid or crystalline
  powder.
- Saving your vectors is essential to use them in subsequent analyses.
- The window does not close automatically after saving, allowing further
  adjustments if needed.


Circular Lattice vectors 
--------------------------

**Purpose**

The purpose of this guide is to help users generate Q vectors within the
software interface. Q vectors are generated based on specified axis components to
define a plane. These Q vectors are crucial for various scientific and
computational applications, particularly in materials science and
crystallography.

**Step 1: Access the Q Vectors Window**

Open the Q Vectors window within the software interface. It appears to have
fields and buttons for specifying and generating Q vectors.

**Step 2: Configure Axis 1**

- **x-component:** [Default: 1] This component specifies the x-coordinate of the
  vector that defines the first axis used to specify the plane.
- **y-component:** [Default: 0] This component specifies the y-coordinate of the
  vector that defines the first axis used to specify the plane.
- **z-component:** [Default: 0] This component specifies the z-coordinate of the
  vector that defines the first axis used to specify the plane.

**Step 3: Configure Axis 2**

- **x-component:** [Default: 0] This component specifies the x-coordinate of the
  vector that defines the second axis used to specify the plane.
- **y-component:** [Default: 1] This component specifies the y-coordinate of the
  vector that defines the second axis used to specify the plane.
- **z-component:** [Default: 0] This component specifies the z-coordinate of the
  vector that defines the second axis used to specify the plane.

**Step 4: Generate Q Vectors**
Click the **"Generate"** button to create the Q vectors based on the default
specifications for Axis 1 and Axis 2. These vectors will be generated and
displayed.

**Step 5: Name the Generated Vectors**
- In the **"Name"** field, enter a descriptive name for the generated vectors.
  This name will help you identify and reference these vectors in the future.

**Step 6: Set the Number of hkl Vectors**
- **Number of hkl vectors:** [Format: int Default: 50] This parameter specifies
  the number of hkl vectors in each shell. Higher values result in higher
  accuracy but at the cost of longer computational time.

**Step 7: Save the Generated Vectors**
Click the **"Save"** button to save the generated Q vectors with the specified
name and the desired number of hkl vectors. The vectors will be saved, and you
can access them for further analysis or use.

Note: Make sure to set a name before saving the vectors, as the name is required
for identification. The **"Save"** button does not close the Q Vectors window,
allowing you to continue working with the generated vectors or make additional
configurations.


Generate Linear Vectors
------------------------

Linear Vectors in the software allow you to generate vectors along a specific
direction determined by an axis. Here's how to use this feature:

1. **Access Linear Vectors Feature:**
   - Open the software and locate the Linear Vectors tool. This tool is essential
     for generating linear vectors in a specified direction.

2. **Set the Seed for Random Number Generation:**
   - Look for the "Seed" parameter.
   - *Format*: int [Default: 0]
   - The RNG seed used to generate the vectors. Using the same seed ensures
     reproducibility, which is crucial for consistent results.

3. **Specify the Number of hkl Vectors:**
   - Configure the "n vectors" parameter.
   - *Format*: int [Default: 50]
   - This parameter defines the number of hkl vectors in each shell. Higher values
     result in higher accuracy but may require more computational time.

4. **Set the Width Tolerance for Shells:**
   - Adjust the "width" parameter.
   - *Format*: float [Default: 1.0]
   - The "width" parameter specifies the accepted tolerance for each shell, often
     identical to the step. It influences the distribution of vectors.

5. **Define the Axis:**
   - Configure the axis using the following parameters:
     - x-component: *Format*: int [Default: 1]
     - y-component: *Format*: int [Default: 0]
     - z-component: *Format*: int [Default: 0]
     - Specify the components of the desired axis that defines the vector
       direction.

6. **Generate Linear Vectors:**
   - Click the "Generate" button to create the hkl vectors based on the specified
     settings. This step initiates vector generation.

7. **Name the Generated Vectors:**
   - Enter a name for the generated vectors in the "Name" field. A descriptive
     name helps you identify them later when working with the vectors.

8. **Save the Generated Vectors:**
   - Click the "Save" button to save the vectors. The window won't close,
     allowing you to continue working with the vectors or make additional
     configurations.



Generate Grid Vectors
---------------------

Grid Vectors in the software allow you to generate hkl vectors within a specified
range and group them according to a qstep. Follow these steps:

1. **Access Grid Vectors Feature:**
   - Open the software and locate the Grid Vectors tool. This tool is essential
     for generating grid vectors within a specified range.

2. **Set the Seed for Random Number Generation:**
   - Configure the "seed" parameter.
   - *Format*: int [Default: 0]
   - The "seed" parameter ensures reproducible random number generation for
     consistent results.

3. **Define h-range, k-range, and l-range:**
   - Set the following parameters for each range:
     - from: *Format*: int [Default: 0]
     - to: *Format*: int [Default: 0]
     - by step of: *Format*: int [Default: 1]
     - Specify the range and step for h, k, and l vectors, which determine the
       grid's dimensions.

4. **Set the qstep:**
   - Adjust the "qstep" parameter.
   - *Format*: float [Default: 0.01]
   - The "qstep" parameter determines how the hkl vectors are grouped within the
     grid.

5. **Generate Grid Vectors:**
   - Click the "Generate" button to create the hkl vectors based on the specified
     settings. This step initiates grid vector generation.

6. **Name the Generated Vectors:**
   - Provide a name for the generated vectors in the "Name" field. A descriptive
     name helps you identify the grid vectors.

7. **Save the Generated Vectors:**
   - Click the "Save" button to save the vectors. The tool won't close, allowing
     further work or configurations with the generated grid vectors.



Generate Approximated Dispersion Vectors
-----------------------------------------

The Approximated Dispersion Vectors feature allows you to generate Q vectors along
a line connecting two input Q points. Follow these steps:

1. **Access Approximated Dispersion Vectors Feature:**
   - Open the software and find the Approximated Dispersion Vectors tool. This
     feature is useful for creating Q vectors along a defined line.

2. **Select the Generator Type:**
   - Use the drop-down menu to choose the generator type, such as
     "circular_lattice."
     - This selection determines the type of Q Vectors you want to define.

3. **Specify the First Q Point:**
   - Configure the following components:
     - x-component: *Format*: int [Default: 1]
     - y-component: *Format*: int [Default: 0]
     - z-component: *Format*: int [Default: 0]
     - Define the components of the first Q point along the line.

4. **Specify the Second Q Point:**
   - Set the components (x, y, z) for the second Q point similarly to the first
     one.
     - Define the components of the second Q point along the line.

5. **Set the Q Step:**
   - Adjust the "Q step (nm^-1)" parameter.
   - *Format*: float [Default: 0.1]
     - The "Q step" parameter determines the increment by which Q is increased when
       tracing the line between the two points.

6. **Generate Approximated Dispersion Vectors:**
   - Click the "Generate" button to create the Q vectors based on the specified
     settings. This step initiates vector generation along the defined line.

7. **Name the Generated Vectors:**
   - Provide a name for the generated vectors in the "Name" field. A descriptive
     name helps you identify the dispersion vectors.

8. **Save the Generated Vectors:**
   - Click the "Save" button to save the vectors. The tool will not close

Group Coordinates 
------------------

1. **Accessing Group Coordinates:**

   To make use of group coordinates within MDANSE, you must access this feature
   during the setup of your analysis. Group coordinates allow you to group atoms
   based on specific criteria for customized calculations.

2. **Default Setting (atom):**

   By default, MDANSE uses the "atom" setting for group coordinates. In this
   default configuration:

   - Calculations are performed using the atomic positions of all the selected
     atoms in your system.
   - All individual atoms are considered independently in the analysis.

3. **Changing the Group Setting:**

   If you find it necessary to modify the group setting according to your
   research requirements, you can do so by selecting an alternative option from
   the available choices. The common options include:

   - "group": This setting groups atoms based on specific group assignments.
   - "residue": Group atoms based on residue identifiers.
   - "chain": Group atoms according to chain designations.
   - "molecule": Group atoms by their molecular assignments.

   Your choice among these options depends on the nature of your system and how
   MDANSE interpreted it during the conversion process from your input data.

4. **Application of Group Coordinates:**

   The primary objective of employing group coordinates is to amalgamate all
   atoms belonging to a particular group into a single representative position.
   This amalgamation effectively combines the selected atoms within the chosen
   group into a single point.

   This grouping operation is advantageous for various calculations, such as:

   - Computing the mean square displacement of molecular centers.
   - Analyzing the collective behavior of atoms within a specific group.
   - Simplifying complex systems for more focused analysis.

5. **Analysis Availability:**

   The "Group coordinates" parameter is available in numerous analyses offered
   by MDANSE. These analyses include:

   - Center Of Masses Trajectory.
   - Density Of States.
   - Mean Square Displacement.
   - Order Parameter.
   - And more.

   Depending on your specific analysis goals, you can enable the "Group
   coordinates" feature to tailor calculations based on the grouped atomic
   positions.

6. **Default Settings for Group Coordinates:**

   - The default setting for group coordinates in MDANSE is "atom," where
     individual atoms are considered independently for analysis.
   - The default grouping options ("group," "residue," "chain," "molecule") may
     vary depending on the system's nature and input data interpretation.

Instrument Resolution 
----------------------
**Purpose**

   The instrument resolution serves the crucial purpose of smoothing the data in the
   time domain before performing a Fourier Transform into the frequency domain. This
   smoothing helps avoid numerical artifacts and ensures more accurate and reliable
   results in your analysis.

1. **Accessing Instrument Resolution:**

   To control the instrument resolution in MDANSE, navigate to the relevant section
   of the software interface that allows you to adjust this parameter.

2. **Available Resolution Shapes:**

   MDANSE supports various resolution shapes, each with specific mathematical
   characteristics. The default resolution shape is Gaussian, but you have the
   flexibility to choose from a range of options, including Lorentzian, Pseudo-
   Voigt, Square, Triangular, and Ideal.

3. **Selecting a Resolution Shape:**

   Depending on your analysis requirements, you can select the most suitable
   resolution shape. For instance:

   - 'gaussian': Provides a standard Gaussian-shaped resolution function.
     Example: ('gaussian', {'mu': 0.0, 'sigma': 1.0})

   - 'lorentzian': Offers a Lorentzian-shaped function.
     Example: ('lorentzian', {'mu': 0.0, 'sigma': 1.0})

   - 'pseudo-voigt': Combines Lorentzian and Gaussian components.
     Example: ('pseudo-voigt', {'eta': 0.5, 'mu_lorentzian': 0.0,
              'sigma_lorentzian': 1.0, 'mu_gaussian': 0.0, 'sigma_gaussian': 1.0})

   - 'square': Represents a square-shaped resolution profile.
     Example: ('square', {'mu': 0.0, 'sigma': 1.0})

   - 'triangular': Utilizes a triangular-shaped resolution function.
     Example: ('triangular', {'mu': 0.0, 'sigma': 1.0})

   - 'ideal': Expresses an ideal resolution as a Dirac function.
     Example: ('ideal', {})

4. **Setting Parameters (μ and σ):**

   Each resolution shape may have specific parameters that can be adjusted.
   Commonly, you can set the center position (μ) and width (σ) of the resolution
   function. These parameters define the behavior of the resolution shape and can be
   tailored to your analysis needs.

5. **Resolution in Frequency Units:**

   MDANSE operates in frequency units, so it may be necessary to convert resolution
   values into energy units (e.g., meV) for practical use. A typical conversion
   factor for Gaussian resolution is σ ≈ 0.65 ps⁻¹, corresponding to a 1 meV
   resolution.


Setting Interpolation Order 
---------------------------
**Purpose:**

The interpolation order in MDANSE allows you to control the precision and
accuracy of velocity data interpolation. This feature is essential for
analyses that require atomic velocity data, ensuring reliable results.

**Step 1: Access the Interpolation Order Setting**
- Open MDANSE on your computer.

**Step 2: Default Behavior**
- By default, MDANSE attempts to use velocities stored in the HDF trajectory for
  analysis. Check if your simulation has stored velocity data in this format.

**Step 3: Choosing an Interpolation Order**
- If your simulation has velocity data, you can set the interpolation order.
- Click on the "Interpolation Order" setting.
- Choose an interpolation order ranging from 1st to 5th order.
  - Default: 1st Order

**Step 4: Understanding Order 1 Interpolation**
- If you select "Order 1" interpolation, MDANSE calculates the first
  time-derivative of each point using neighboring positions and the time step
  (∆t).
  - Formula: (ṙ(t_i)) = (r(t_i+1) - r(t_i)) / ∆t

**Step 5: Higher-Order Interpolation (N > 1)**
- For interpolation orders higher than 1 (2nd, 3rd, 4th, or 5th order),
  MDANSE employs an Nth-order polynomial interpolation technique.
- This technique involves interpolating multiple points within a given range to
  calculate the first time-derivative.
  - Supported Orders: {2, 3, 4, 5}

**Step 6: Analysis Compatibility**
- The "Interpolation Order" parameter is available in several MDANSE analyses,

- Note that the implementation of interpolation in the Current Correlation
  Function analysis may involve additional complexities, which are explained in
  the respective section of the MDANSE documentation.

By following these steps, you can effectively set the interpolation order in
MDANSE for your specific analysis needs, ensuring precise velocity data handling.




 Weights
---------

**Purpose:** Adjust how atoms or elements contribute to property
calculations.

**Step 2: Load Molecular Data**

   - Import your molecular data using the "File" menu.

**Step 3: Access Analysis with Weights Option**

   - Identify the analysis that includes the "Weights" option.
   - *Note:* Most analyses offer the "Weights" option to customize property
     computations.

**Step 4: Customize Weights**

   - Access "Weights" within the analysis settings.
   
   - *Default Weighting:*
   
     - In many cases, the default weight is set to 'equal,' treating all
       atoms or elements equally.
     - *Scattering Analyses:*
       - Default weights differ for coherent (bcoh) and incoherent (b2inc)
         analyses.
       
   - *Customization:*
   
     - You have the flexibility to select any numerical property from the
       MDANSE database as a weighting factor.
     - Adjust weights based on your research requirements.

**Step 5: Understand Weighted Property Calculations**

   - Weights allow you to control how atoms or elements contribute to
     property calculations.
   - The total property is calculated based on the weighted contributions of
     individual elements or atom pairs.
   - *For single-particle analyses* (e.g., mean square displacement, velocity
     autocorrelation function), properties are computed for all different
     elements identified in the system.
   - *For collective analyses* (e.g., partial distribution function, dynamic
     coherent structure factor), properties are calculated for all possible
     pairs of different elements.
