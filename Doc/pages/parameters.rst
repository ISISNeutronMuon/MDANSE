
.. _parameters:

Glossary of Parameters
=======================

Frames
~~~~~~

+--------------+---------+------------------+---------------------------------------------------------+
| Parameter    | Format  | Default Value    | Description                                             |
+==============+=========+==================+=========================================================+
| First frame  | int     | 0                | The frame from which the analysis will begin, the       |
|              |         |                  | first frame taken into account.                         |
+--------------+---------+------------------+---------------------------------------------------------+
| Last frame   | int     | Last frame       | The frame until which the analysis proceeds. The last   |
|              |         |                  | frame taken into account.                               |
+--------------+---------+------------------+---------------------------------------------------------+
| Frame step   | int     | 1                | Determines the periodicity of which steps are used      |
|              |         |                  | and which are skipped. 1 means that all frames are      |
|              |         |                  | read, 2 means every other is read, etc.                 |
+--------------+---------+------------------+---------------------------------------------------------+

.. _param-qshells:

Q shells
~~~~~~~~

+--------------+---------+---------+--------------------------------------------------------+
| Input        | Format  | Default | Description                                            |
+==============+=========+=========+========================================================+
| from         | float   | 0       | The lowest value of :math:`|Q|` to be used in Q-vector |
|              |         |         | generation.                                            |
+--------------+---------+---------+--------------------------------------------------------+
| to           | float   | 10      | The highest value of :math:`|Q|` to be used in Q-vector|
|              |         |         | generation.                                            |
+--------------+---------+---------+--------------------------------------------------------+
| by step of   | float   | 1       | The step by which :math:`|Q|` is incremented when      |
|              |         |         | changing from one Q-shell to the next one. Please      |
|              |         |         | adjust the *width* input parameter accordingly when    |
|              |         |         | changing the step.                                     |
+--------------+---------+---------+--------------------------------------------------------+

The *unit* of the Q-vector length in MDANSE is :math:`\text{nm}^{-1}`.

.. _param-output-files:

Output files
~~~~~~~~~~~~

This is one of the two parameters that are present in each analysis, the
other being :ref:`param-frames`. It usually appears at the bottom of
an analysis window (:ref:`analysis`), right above the
buttons. 

-  **output files**

+---------------+---------------------------------------------------------------+
| Output Files  |                                                               |
+===============+===============================================================+
|   Format:     | `str`                                                         |
+---------------+---------------------------------------------------------------+
|   Default:    | `trajectory_directory_path\<trajectory_filename>_             |
|               | <analysis_acronym>`                                           |
+---------------+---------------------------------------------------------------+
|   Browse:     | The **Browse** button opens a system file browser window,     |
|               | allowing the navigation of the filesystem.                    |
+---------------+---------------------------------------------------------------+

**Description:** Specifies the location where analysis results will be stored.
It's typically composed of a directory path, the name of the HDF file being
analyzed, and a shortened analysis acronym (e.g., "disf" for dynamic incoherent
structure factor). If a file with the same name already exists, a unique number
(n) is appended to avoid overwriting.

-  **output formats**

+-------------------+------------------------------------------------------+
| Output Formats    |                                                      |
+-------------------+------------------------------------------------------+
| Format            | Drop-down                                            |
| Default           | HDF5 (for analysis), HDF (for trajectory conversion) |
+-------------------+------------------------------------------------------+

*Description:* specifies the :ref:`file_formats` in
which the analysis results are saved. :ref:`hdf5`,
:ref:`text_output`, or cominbations of those can be selected.
The name of these files is given in the 'Basename' string.

Creating selections
~~~~~~~~~~~~~~~~~~~

There are the following Selections in MDANSE, each of which provides a
variety of ways to alter the analysis:

-  :ref:`param-axis-selection`
-  :ref:`param-atom-selection`
-  :ref:`param-atom-transmutation`
-  :ref:`param-atom-charges`
-  Q Vectors (explored separately in the `next
   section <#_A3.4._Q_vectors>`__)

The ones relevant to the analysis are present in its window, but some
can also be performed from :ref:`molecular-viewer`. By
default, there are no Selections saved in MDANSE; they all have to be
created manually. Each selection is unique to a trajectory HDF
file, but all selections are stored in the same folder, $APPDATA/mdanse.
Therefore, if a selection is to be reuse, it is important to give
selections unique names even when creating the same selection for
multiple trajectories. To help with that, all existing saved selection
can be viewed in the User Definition Viewer which can be accessed from
the `toolbar <#_Toolbar>`__. To save a selection, type a name in the
field next to the **Save** button, and then click on the button. This
will save the selection without closing the window.

.. _param-axis-selection:

Axis Selection/Reference Basis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Inside an analysis window, Axis Selection looks like this:

The drop-down menu is used to choose one of the existing definitions.
Only the definitions with the format matching the analysis, i.e. those
with the same number of selected atoms as the analysis expects, will
appear. New ones can be created by clicking on the **New definition**
button, which will open the window below. The details of the currently
selected definition can be viewed in the User Definition Viewer by
clicking on the **View selected definition**.

When this window is opened from an analysis window, the 'Number of
atoms' field at the top will be set to the number of atoms that must be
selected for the selection to work in the analysis from whose window it
was opened. The field will also not be editable. Thus, when the New
definition button is clicked in :ref:`analysis-angular-correlation`
analysis, the field will be set
to 2, because that is how many it requires.

The number of atoms indicates how many atoms from one molecule must be
selected. To select an atom, click on the + button in the 'Molecules'
list to show which atoms that molecule contains, and then double-click
the atom. That will cause the chosen atom to appear in the 'Selected
atoms' list, and its details in the box below. An atom can be removed
from selection by clicking on it in the 'Selected atoms' list and
hitting the Delete key on the keyboard.

Axis selection is available for :ref:`analysis-angular-correlation`
and :ref:`analysis-op` analyses.



Atom Selection
^^^^^^^^^^^^^^

Atom Selection allows you to select any set of atoms and/or other
particles. These selected particles are then the ones that are made the
target of the analysis. There is no limit to which particles can be
included in a selection, or to how many selections can be used
simultaneously. There can even be none; Atom Selection is entirely
optional.

Inside an analysis window, Atom Selection appears thusly:

The green button adds a line for another selection, allowing you to
choose one more selection to apply to that analysis:

The line can be removed by clicking on the red button. The drop-down
menu and the **View selected definition** button work the way they do in
Axis Selection <link>. The **Set new selection** button opens the
following window:

The **Filter by** field contains different ways to access the various
particles in the loaded trajectory. Clicking on a filter will make all
the relevant particles appear in the top right box:

Clicking on the particles/groups in that window will highlight them and
make them appear in the **Selection** box. Together with the buttons for
logical operations, it is possible to make complex selections, like so:

The large box below the **Selection** box should show information about
your selection, but it is broken for complex selections. The box at the
very bottom, next to the **Save** button, is used for naming the
selection. Each selection must be named with a unique name. The **Save**
button saves the selection for the loaded trajectory, but it will not
close the Atom Selection window. Once selection has been saved, it
should appear in the drop-down menu in the analysis window.

Atom selection is available for all the analyses for which
:ref:`param-atom-transmutation` is available, as well as all
:ref:`analysis-trajectory` analyses, :ref:`analysis-gacf`, `Molecular
Trace <#_Molecular_Trace>`__, `Root Mean Square
Fluctuation, <#_Root_Mean_Square_1>`__ `Radius of
Gyration <#_Radius_Of_Gyration>`__, `Solvent Accessible
Surface <#_Solvent_Accessible_Surface>`__.

.. _param-atom-transmutation:

Atom Transmutation
^^^^^^^^^^^^^^^^^^

To use Atom Transmutation, simply select an Atom Selection in the grey
drop-down menu on the left, and then choose the element into which the
atoms in that Atom Selection will be transmuted from the white drop-down
menu next to the red button. For example, the below Atom Transmutation
will transmute all sodium ions into potassium ions:

This parameter is available for the following analyses: `Coordination
Number <#_Coordination_Number>`__, `Current Correlation
Function <#_Current_Correlation_Function>`__, `Density Of
States <#_Density_Of_States>`__, `Density
Profile <#_Density_Profile>`__, `Dynamic Coherent Structure
Factor <#_Dynamic_Coherent_Structure>`__, `Dynamic Incoherent Structure
Factor <#_Dynamic_Incoherent_Structure>`__,
`Eccentricity <#_Eccentricity>`__, `Elastic Incoherent Structure
Factor <#_Elastic_Incoherent_Structure>`__, `Gaussian Dynamic Incoherent
Structure Factor <#_Gaussian_Dynamic_Incoherent>`__, `General Auto
Correlation Function <#_General_AutoCorrelation_Function>`__, `Mean
Square Displacement <#_Mean_Square_Displacement>`__, `Neutron Dynamic
Total Structure Factor <#_Neutron_Dynamic_Total>`__, `Order
Parameter <#_Order_Parameter>`__, `Pair Distribution
Function <#_Pair_Distribution_Function>`__, `Position Auto Correlation
Function <#_Position_AutoCorrelation_Function>`__, `Root Mean Square
Deviation <#_Root_Mean_Square>`__, `Static Structure
Factor <#_Static_Structure_Factor>`__, `Velocity Auto Correlation
Function <#_Velocity_AutoCorrelation_Function>`__, `X-Ray Static
Structure Factor <#_Xray_Static_Structure>`__.

.. _param-atom-charges:

Atom Charges
^^^^^^^^^^^^

This selection works inside an analysis window exactly the same as
:ref:`param-axis-selection`. The only difference is the window that
opens when **Set new selection** button is clicked. The Partial Charges
window appears as below, and allows you to edit the charges at each atom
inside the system. To do that, simply click on a field in the **charge**
column and type in a number. The change will be confirmed once you hit
enter or click outside the field. Once all changes have been made, name
the selection using the box at the bottom, then click the **Save**
button, and finally close the window.

This parameter is only available for the
:ref:`analysis-dacf` analysis.

.. _param-q-vectors:

Q vectors
~~~~~~~~~

Similar to the selections above but specific to `Scattering
Plugin <#_Scattering>`__\ s, Q vectors give the opportunity to change
how the analysis is performed. Each window has a part like this:

This section must be filled for analysis to be able to run. Like for
other selections, there are no definitions by default. Therefore, one
has to be created by clicking on the **New definition** button. This
will open a window like in one of the following subsections, which show
how Q Vectors are defined for each type of Q Vector. There are many
types, and it is up to you to choose which is the best for a given
experiment.

Once a definition of choice exists, it can be selected from the
drop-down menu. The **View selected definition** opens the User
Definition viewer <link> at the currently selected definition.

Spherical Lattice Vectors
^^^^^^^^^^^^^^^^^^^^^^^^^

+------------------+-----------+---------+------------------------------------------------------------+
| Parameter        | Format    | Default | Description                                                |
+==================+===========+=========+============================================================+
| seed             | int       | 0       | RNG seed used to generate the vectors. Setting the same    |
|                  |           |         | seed ensures reproducibility of random numbers.            |
+------------------+-----------+---------+------------------------------------------------------------+
| n vectors        | int       | 50      | Number of hkl vectors in each shell. Higher values result  |
| (Number of hkl   |           |         | in higher accuracy but longer computation time.            |
| vectors)         |           |         |                                                            |
+------------------+-----------+---------+------------------------------------------------------------+
| width            | float     | 1.0     | Accepted tolerance of each shell. Often identical to the   |
|                  |           |         | "by step of" parameter.                                    |
+------------------+-----------+---------+------------------------------------------------------------+
| Generate button  |           |         | Generates hkl vectors based on the specified parameters    |
|                  |           |         | (seed, n vectors, width). Must be clicked before saving.   |
+------------------+-----------+---------+------------------------------------------------------------+
| Name             | str       | None    | Allows you to name the generated vectors. Name must be     |
|                  |           |         | set before saving the vectors.                             |
+------------------+-----------+---------+------------------------------------------------------------+
| Save button      |           |         | Saves the generated vectors. It doesn't close the Q        |
|                  |           |         | Vectors window. Saved vectors may be in a specific format. |    
+------------------+-----------+---------+------------------------------------------------------------+


Circular Lattice Vectors
^^^^^^^^^^^^^^^^^^^^^^^^

+------------------+-----------+---------+------------------------------------------------------------+
| Parameter        | Format    | Default | Description                                                |
+==================+===========+=========+============================================================+
| seed             | int       | 0       | The RNG seed used to generate the vectors. Setting the same|
|                  |           |         | seed ensures reproducibility of random numbers.            |
+------------------+-----------+---------+------------------------------------------------------------+
| n vectors        | int       | 50      | Number of hkl vectors in each shell. Higher values result  |
|                  |           |         | in higher accuracy but at the cost of longer computational |
|                  |           |         | time.                                                      |
+------------------+-----------+---------+------------------------------------------------------------+
| width            | float     | 1.0     | Accepted tolerance of each shell. Often identical to the   |
|                  |           |         | "by step of" parameter.                                    |
+------------------+-----------+---------+------------------------------------------------------------+
| Generate button  |           |         | Generates hkl vectors based on the specified parameters    |
|                  |           |         | (seed, n vectors, width). Must be clicked before saving.   |
+------------------+-----------+---------+------------------------------------------------------------+
| Name             | str       | None    | Allows you to name the generated vectors. Name must be     |
|                  |           |         | set before saving the vectors.                             |
+------------------+-----------+---------+------------------------------------------------------------+
| Save button      |           |         | Saves the generated vectors. It doesn't close the Q        |
|                  |           |         | Vectors window. Saved vectors may be in a specific format. |    
+------------------+-----------+---------+------------------------------------------------------------+

-  axis 1

   +--------------+-----------+---------+-----------------------+
   | Component    | Format    | Default | Description           |
   +==============+===========+=========+=======================+
   | x-component  | int       | 1       | X-component for plane |
   +--------------+-----------+---------+-----------------------+
   | y-component  | int       | 0       | Y-component for plane |
   +--------------+-----------+---------+-----------------------+
   | z-component  | int       | 0       | Z-component for plane |
   +--------------+-----------+---------+-----------------------+

-  axis 2

   +--------------+-----------+---------+-----------------------+
   | Component    | Format    | Default | Description           |
   +==============+===========+=========+=======================+
   | x-component  | int       | 0       | X-component for plane |
   +--------------+-----------+---------+-----------------------+
   | y-component  | int       | 1       | Y-component for plane |
   +--------------+-----------+---------+-----------------------+
   | z-component  | int       | 0       | Z-component for plane |
   +--------------+-----------+---------+-----------------------+



Linear Lattice Vectors
^^^^^^^^^^^^^^^^^^^^^^

+------------------+-----------+---------+------------------------------------------------------------+
| Parameter        | Format    | Default | Description                                                |
+==================+===========+=========+============================================================+
| seed             | int       | 0       | The RNG seed used to generate the vectors. Setting the same|
|                  |           |         | seed ensures reproducibility of random numbers.            |
+------------------+-----------+---------+------------------------------------------------------------+
| n vectors        | int       | 50      | Number of hkl vectors in each shell. Higher values result  |
|                  |           |         | in higher accuracy but at the cost of longer computational |
|                  |           |         | time.                                                      |
+------------------+-----------+---------+------------------------------------------------------------+
| width            | float     | 1.0     | Accepted tolerance of each shell. Often identical to the   |
|                  |           |         | "by step of" parameter.                                    |
+------------------+-----------+---------+------------------------------------------------------------+
| axis             |           |         |                                                            |
+------------------+-----------+---------+------------------------------------------------------------+
|   x-component   | int       | 1       | The x-components of the specified axis.                     |
+------------------+-----------+---------+------------------------------------------------------------+
|   y-component   | int       | 0       | The y-components of the specified axis.                     |
+------------------+-----------+---------+------------------------------------------------------------+
|   z-component   | int       | 0       | The z-components of the specified axis.                     |
+------------------+-----------+---------+------------------------------------------------------------+
| Generate button  |           |         | Generates hkl vectors based on the specified parameters    |
|                  |           |         | (seed, n vectors, width). Must be clicked before saving.   |
+------------------+-----------+---------+------------------------------------------------------------+
| Name             | str       | None    | This is the empty box at the bottom of the window. It      |
|                  |           |         | allows you to name the generated vectors. This must be     |
|                  |           |         | set before saving the vectors.                             |
+------------------+-----------+---------+------------------------------------------------------------+
| Save button      |           |         | Saves the generated vectors. It doesn't close the Q        |
|                  |           |         | Vectors window. Saved vectors may be in a specific format. |    
+------------------+-----------+---------+------------------------------------------------------------+


Miller Indices Lattice Vectors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+-----------------+-----------+---------+------------------------------------------------------------+
| Parameter       | Format    | Default | Description                                                |
+=================+===========+=========+============================================================+
| seed            | int       | 0       | The RNG seed used to generate the vectors. Setting the same|
|                 |           |         | seed ensures reproducibility of random numbers.            |
+-----------------+-----------+---------+------------------------------------------------------------+
| width           | float     | 1.0     | Accepted tolerance of each shell. Often identical to the   |
|                 |           |         | "by step of" parameter.                                    |
+-----------------+-----------+---------+------------------------------------------------------------+


-  h (and the same goes for k and l fields)

+-----------------+-----------+---------+------------------------------------------------------------+
| Parameter       | Format    | Default | Description                                                |
+=================+===========+=========+============================================================+
|   from          | int       | 0       | Minimum value used to construct the range of h vectors.    |
+-----------------+-----------+---------+------------------------------------------------------------+
|   to            | int       | 0       | Maximum value used to construct the range of h vectors.    |
+-----------------+-----------+---------+------------------------------------------------------------+
|   by step of    | int       | 1       | Step used to construct the range of h vectors. If it is    |
|                 |           |         | 1, every integer between **from** and **to** is placed     |
|                 |           |         | into the range; if it is 2, every other, etc.              |
+-----------------+-----------+---------+------------------------------------------------------------+
| Generate button |           |         | Generates hkl vectors based on the specified parameters    |
|                 |           |         | (h ranges). Must be clicked before saving.                 |
+-----------------+-----------+---------+------------------------------------------------------------+
| Name            | str       | None    | This is the empty box at the bottom of the window. It      |
|                 |           |         | allows you to name the generated vectors. This must be     |
|                 |           |         | set before saving the vectors.                             |
+-----------------+-----------+---------+------------------------------------------------------------+
| Save button     |           |         | Saves the generated vectors. It doesn't close the Q      |
|                 |           |         | Vectors window. Saved vectors may be in a specific format.|    
+-----------------+-----------+---------+------------------------------------------------------------+


Spherical Vectors
^^^^^^^^^^^^^^^^^
+-----------------+-----------+---------+------------------------------------------------------------+
| Parameter       | Format    | Default | Description                                                |
+=================+===========+=========+============================================================+
| seed            | int       | 0       | The RNG seed used to generate the vectors. Setting the same|
|                 |           |         | seed ensures reproducibility of random numbers.            |
+-----------------+-----------+---------+------------------------------------------------------------+
| n vectors       | int       | 50      | The number of hkl vectors in each shell. Higher values     |
|                 |           |         | result in higher accuracy but longer computational time.   |
+-----------------+-----------+---------+------------------------------------------------------------+
| width           | float     | 1.0     | The accepted tolerance of each shell. Often identical to   |
|                 |           |         | the "by step of" parameter.                                |
+-----------------+-----------+---------+------------------------------------------------------------+
| Generate button |           |         | Generates hkl vectors based on the specified parameters    |
|                 |           |         | (seed, n vectors, width). Must be clicked before saving.   |
+-----------------+-----------+---------+------------------------------------------------------------+
| Name            | str       | None    | This is the empty box at the bottom of the window. It      |
|                 |           |         | allows you to name the generated vectors before saving.    |
+-----------------+-----------+---------+------------------------------------------------------------+
| Save button     |           |         | Saves the generated vectors. It doesn't close the Q        |
|                 |           |         | Vectors window.                                            |
+-----------------+-----------+---------+------------------------------------------------------------+


Circular Vectors
^^^^^^^^^^^^^^^^

+-----------------+-----------+---------+--------------------------------------------------------+
| Parameter       | Format    | Default | Description                                            |
+=================+===========+=========+========================================================+
| seed            | int       | 0       | The RNG seed used to generate the vectors. Setting the |
|                 |           |         | same seed ensures that the same random numbers are     |
|                 |           |         | generated, making the calculation reproducible.        |
+-----------------+-----------+---------+--------------------------------------------------------+
| n vectors       | int       | 50      | The number of hkl vectors in each shell. Increasing    |
|                 |           |         | this value improves accuracy but also increases        |
|                 |           |         | computational time.                                    |
+-----------------+-----------+---------+--------------------------------------------------------+
| width           | float     | 1.0     | The accepted tolerance of each shell. It often matches |
|                 |           |         | the "by step of" parameter.                            |
+-----------------+-----------+---------+--------------------------------------------------------+
| axis 1          |           |         | Axis 1 parameters:                                     |
|                 |           |         |   - x-component: int, default 1                        |
|                 |           |         |     The x-component of the first axis used to specify  |
|                 |           |         |     the plane.                                         |
|                 |           |         |   - y-component: int, default 0                        |
|                 |           |         |     The y-component of the first axis used to specify  |
|                 |           |         |     the plane.                                         |
|                 |           |         |   - z-component: int, default 0                        |
|                 |           |         |     The z-component of the first axis used to specify  |
|                 |           |         |     the plane.                                         |
+-----------------+-----------+---------+--------------------------------------------------------+
| axis 2          |           |         | Axis 2 parameters:                                     |
|                 |           |         |   - x-component: int, default 0*                       |
|                 |           |         |     The x-component of the second axis used to         |
|                 |           |         |     specify the plane.                                 |
|                 |           |         |   - y-component: int, default 1                        |
|                 |           |         |     The y-component of the second axis used to         |
|                 |           |         |     specify the plane.                                 |
|                 |           |         |   - z-component: int, default 0                        |
|                 |           |         |     The z-component of the second axis used to         |
|                 |           |         |     specify the plane.                                 |
+-----------------+-----------+---------+--------------------------------------------------------+
| Generate button |           |         | Generates hkl vectors based on the specified           |
|                 |           |         | parameters (seed, n vectors, width, axis components).  |
|                 |           |         | Must be clicked before saving.                         |
+-----------------+-----------+---------+--------------------------------------------------------+
| Name            | str       | None    | This is the empty box at the bottom of the window.     |
|                 |           |         | It allows you to name the generated vectors before     |
|                 |           |         | saving. Must be set before saving.                     |
+-----------------+-----------+---------+--------------------------------------------------------+
| Save button     |           |         | Saves the generated vectors. It does not close the Q   |
|                 |           |         | Vectors window. The saved vectors may be in a          |
|                 |           |         | specific format, such as a table format.               |
+-----------------+-----------+---------+--------------------------------------------------------+


Linear Vectors
^^^^^^^^^^^^^^

+-----------------+-----------+---------+-------------------------------------------------------+
| Parameter       | Format    | Default | Description                                           |
+=================+===========+=========+=======================================================+
| seed            | int       | 0       | The RNG seed used to generate the vectors. Setting    |
|                 |           |         | the same seed ensures that the same random numbers    |
|                 |           |         | are generated, making the calculation more            |
|                 |           |         | reproducible.                                         |
+-----------------+-----------+---------+-------------------------------------------------------+
| n vectors       | int       | 50      | The number of hkl vectors in each shell. Higher       |
|                 |           |         | values result in higher accuracy but longer           |
|                 |           |         | computational time.                                   |
+-----------------+-----------+---------+-------------------------------------------------------+
| width           | float     | 1.0     | The accepted tolerance of each shell. It is often     |
|                 |           |         | identical to the "by step of" parameter.              |
+-----------------+-----------+---------+-------------------------------------------------------+
| axis            |           |         | Axis parameters:                                      |
|                 |           |         |   - x-component: int, default 1                       |
|                 |           |         |     The x-component of the specified axis.            |
|                 |           |         |   - y-component: int, default 0                       |
|                 |           |         |     The y-component of the specified axis.            |
|                 |           |         |   - z-component: int, default 0                       |
|                 |           |         |     The z-component of the specified axis.            |
+-----------------+-----------+---------+-------------------------------------------------------+
| Generate button |           |         | Generates hkl vectors based on the specified          |
|                 |           |         | parameters (seed, n vectors, width, axis              |
|                 |           |         | components). Must be clicked before saving.           |
+-----------------+-----------+---------+-------------------------------------------------------+
| Name            | str       | None    | This is the empty box at the bottom of the window.    |
|                 |           |         | It allows you to name the generated vectors before    |
|                 |           |         | saving. Must be set before saving.                    |
+-----------------+-----------+---------+-------------------------------------------------------+
| Save button     |           |         | Saves the generated vectors. It does not close the    |
|                 |           |         | Q Vectors window.                                     |
+-----------------+-----------+---------+-------------------------------------------------------+


Grid Vectors
^^^^^^^^^^^^

+-----------------+-----------+---------+---------------------------------------------------------------+
| Parameter       | Format    | Default | Description                                                   |
+=================+===========+=========+===============================================================+
| seed            | int       | 0       | The RNG seed used to generate the vectors. Setting the same   |
|                 |           |         | seed ensures that the same random numbers are generated,      |
|                 |           |         | making the calculation more reproducible.                     |
+-----------------+-----------+---------+---------------------------------------------------------------+
| hrange (krange  |           |         | Range parameters for h, k, and l vectors:                     |
| , lrange fields)|           |         |   - from: int, default 0                                      |
|                 |           |         |     The minimum value used to construct the range of h        |
|                 |           |         |     vectors.                                                  |
|                 |           |         |   - to: int, default 0                                        |
|                 |           |         |     The maximum value used to construct the range of h        |
|                 |           |         |     vectors.                                                  |
|                 |           |         |   - by step of: int, default 1                                |
|                 |           |         |     The step used to construct the range of h vectors. If it  |
|                 |           |         |     is 1, every integer between **from** and **to** is        |
|                 |           |         |     placed into the range; if it is 2, every other, etc.      |
+-----------------+-----------+---------+---------------------------------------------------------------+
| qstep           | float     | 0.01    | Determines how the hkl vectors are grouped.                   |
+-----------------+-----------+---------+---------------------------------------------------------------+
| Generate button |           |         | Generates hkl vectors based on the specified parameters       |
|                 |           |         | (seed, hrange, krange, lrange, qstep). Must be clicked        |
|                 |           |         | before saving.                                                |
+-----------------+-----------+---------+---------------------------------------------------------------+
| Name            | str       | None    | This is the empty box at the bottom of the window. It         |
|                 |           |         | allows you to name the generated vectors before saving.       |
|                 |           |         | Must be set before saving.                                    |
+-----------------+-----------+---------+---------------------------------------------------------------+
| Save button     |           |         | Saves the generated vectors. It does not close the Q          |
|                 |           |         | Vectors window. Saved vectors may be in a specific format.    |
+-----------------+-----------+---------+---------------------------------------------------------------+


Approximated Dispersion Vectors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+-----------------+-----------+----------------------+------------------------------------------------------------+
| Parameter       | Format    | Default              | Description                                                |
+=================+===========+======================+============================================================+
| generator       | drop-down | circular_lattice     | The selection of which type of Q Vectors is being          |
|                 |           |                      | defined.                                                   |
+-----------------+-----------+----------------------+------------------------------------------------------------+
| Q start (nm^-1) |           |                      | Q start parameters for the first and second Q points:      |
|                 |           |                      |   - x-component: int, default 1                            |
|                 |           |                      |     The x-component of this Q point.                       |
|                 |           |                      |   - y-component: int, default 0                            |
|                 |           |                      |     The y-component of this Q point.                       |
|                 |           |                      |   - z-component: int, default 0                            |
|                 |           |                      |     The z-component of this Q point.                       |
+-----------------+-----------+----------------------+------------------------------------------------------------+
| Q step (nm^-1)  | float     | 0.1                  | The increment by which Q is increased when tracing the     |
|                 |           |                      | line between the two points.                               |
+-----------------+-----------+----------------------+------------------------------------------------------------+
| Generate button |           |                      | Generates hkl vectors based on the specified parameters    |
|                 |           |                      | (generator, Q start, Q step). Must be clicked before       |
|                 |           |                      | saving.                                                    |
+-----------------+-----------+----------------------+------------------------------------------------------------+
| Name            | str       | None                 | This is the empty box at the bottom of the window. It      |
|                 |           |                      | allows you to name the generated vectors before saving.    |
|                 |           |                      | Must be set before saving.                                 |
+-----------------+-----------+----------------------+------------------------------------------------------------+
| Save button     |           |                      | Saves the generated vectors. It does not close the Q       |
|                 |           |                      | Vectors window. Saved vectors may be in a specific format. |    
+-----------------+-----------+----------------------+------------------------------------------------------------+


.. _param-group-coordinates:

Group coordinates
~~~~~~~~~~~~~~~~~

This parameter is available in the following analyses: 
:ref:`trajectory-comt`,
:ref:`analysis-dos`, :ref:`analysis-disf`,
:ref:`analysis-eisf`, :ref:`analysis-gdisf`, 
:ref:`analysis-gacf`, :ref:`analysis-msd`, 
:ref:`analysis-op`, `Rigid Body
Trajectory <#_Rigid_Body_Trajectory>`__, `Root Mean Square
Deviation <#_Root_Mean_Square>`__, `Root Mean Square
Fluctuation <#_Root_Mean_Square_1>`__, `Velocity Auto Correlation
Function <#_Velocity_AutoCorrelation_Function>`__.

.. _param-instrument-resolution:

Instrument resolution
~~~~~~~~~~~~~~~~~~~~~

This option is available in all the analyses performing a time Fourier
Transform, e.g. for the calculation of the density of states or the
dynamic structure factor. The following resolution shapes are supported
in MDANSE at the moment:

- Gaussian

  :code:`('gaussian', {'mu': 0.0, 'sigma': 1.0})`

- Lorentzian

  :code:`('lorentzian', {'mu': 0.0, 'sigma': 1.0})`

- Pseudo-Voigt

  The corresponding MDANSE input is:

  :code:`('pseudo-voigt', {'eta': 0.5, 'mu_lorentzian': 0.0, 'sigma_lorentzian': 1.0, 'mu_gaussian': 0.0, 'sigma_gaussian': 1.0})`

- square

  The corresponding MDANSE input is:

  :code:`('square', {'mu': 0.0, 'sigma': 1.0})`

- triangular

  The corresponding MDANSE input is:

  :code:`('triangular', {'mu': 0.0, 'sigma': 1.0})`

- ideal
  The corresponding MDANSE input is:

  :code:`('ideal', {})`


This parameter is available for the following analyses: `Current
Correlation Function <#_Current_Correlation_Function>`__, `Density of
States <#_Density_Of_States>`__, `Dynamic Coherent Structure
Factor <#_Dynamic_Coherent_Structure>`__, `Dynamic Incoherent Structure
Factor <#_Dynamic_Incoherent_Structure>`__, `Gaussian Dynamic Incoherent
Structure Factor <#_Gaussian_Dynamic_Incoherent>`__, `Neutron Dynamic
Total Structure Factor <#_Neutron_Dynamic_Total>`__, `Structure Factor
From Scattering Function <#_Structure_Factor_From>`__.

.. _params-interpolation-order:

Interpolation order
~~~~~~~~~~~~~~~~~~~

Analyses that require atomic velocity data have an option to interpolate
this data from atomic positions. By default, no interpolation is
performed and instead MDANSE attempts to use the velocities stored int
the HDF trajectory. Of course, depending on the way your simulation
was set up, it is possible that the atoms velocities were not even stored
in the output. It is still possible to derive the velocities of atoms
from their positions at known time intervals, which is the subject of this
section.


Interpolation order is available for the following analyses: `Current
Correlation Function <#_Current_Correlation_Function>`__, `Density of
States <#_Density_Of_States>`__, `Temperature <#_Temperature>`__,
`Velocity Auto Correlation
Function <#_Velocity_AutoCorrelation_Function>`__. However, please note
that due to the nature of the `Current Correlation
Function <#_Current_Correlation_Function>`__ analysis, the interpolation
there is more complicated, the details of which can be found in its
`section <#_GUI>`__.

.. _param-normalize:

Normalize
~~~~~~~~~

Normalisation is available for the following analyses: `Current
Correlation Function <#_Current_Correlation_Function>`__, `General Auto
Correlation Function <#_General_AutoCorrelation_Function>`__, `Position
Auto Correlation Function <#_Position_AutoCorrelation_Function>`__,
`Velocity Auto Correlation
Function <#_Velocity_AutoCorrelation_Function>`__.

.. _param-project-coordinates:

Project coordinates 
~~~~~~~~~~~~~~~~~~~~

This parameter is available for the following analyses: `Density of
States <#_Density_Of_States>`__, `Dynamic Incoherent Structure
Factor <#_Dynamic_Incoherent_Structure>`__, `Elastic Incoherent
Structure Factor <#_Elastic_Incoherent_Structure>`__, `Gaussian Dynamic
Incoherent Structure Factor <#_Gaussian_Dynamic_Incoherent>`__, `Mean
Square Displacement <#_Mean_Square_Displacement>`__, `Position Auto
Correlation Function <#_Position_AutoCorrelation_Function>`__, `Velocity
Auto Correlation Function <#_Velocity_AutoCorrelation_Function>`__.

.. _param-weights:

Weights
~~~~~~~

This parameter is available in the following analyses: `Current
Correlation Function <#_Current_Correlation_Function>`__, `Density of
States <#_Density_Of_States>`__, `Density
Profile <#_Density_Profile>`__, `Dynamic Coherent Structure
Factor <#_Dynamic_Coherent_Structure>`__, `Dynamic Incoherent Structure
Factor <#_Dynamic_Incoherent_Structure>`__,
`Eccentricity <#_Eccentricity>`__, `Elastic Incoherent Structure
Factor <#_Elastic_Incoherent_Structure>`__, `Gaussian Dynamic Incoherent
Structure Factor <#_Gaussian_Dynamic_Incoherent>`__, `General Auto
Correlation Function <#_General_AutoCorrelation_Function>`__, `Mean
Square Displacement <#_Mean_Square_Displacement>`__, `Pair Distribution
Function <#_Pair_Distribution_Function>`__, `Radius of
Gyration <#_Radius_Of_Gyration>`__, `Rigid Body
Trajectory <#_Rigid_Body_Trajectory>`__, `Root Mean Square
Deviation <#_Root_Mean_Square>`__, `Static Structure
Factor <#_Static_Structure_Factor>`__, `Velocity Auto Correlation
Function <#_Velocity_AutoCorrelation_Function>`__.

.. _param-running-mode:

Running mode
~~~~~~~~~~~~

Running mode is available for most analyses: all
`Dynamics <#_Dynamics>`__ analyses, all `Trajectory <#_Trajectory>`__
analyses, all `Thermodynamics <#_Thermodynamics>`__ analyses, `Area Per
Molecule <#_Area_Per_Molecule>`__, `Coordination
Number <#_Coordination_Number>`__, `Current Correlation
Function <#_Current_Correlation_Function>`__, `Density
Profile <#_Density_Profile>`__, `Dipole Auto Correlation
Function <#_Dipole_AutoCorrelation_Function>`__, `Dynamic Coherent
Structure Factor <#_Dynamic_Coherent_Structure>`__, `Dynamic Incoherent
Structure Factor <#_Dynamic_Incoherent_Structure>`__,
`Eccentricity <#_Eccentricity>`__, `Elastic Incoherent Structure
Factor <#_Elastic_Incoherent_Structure>`__, `Gaussian Dynamic Incoherent
Structure Factor <#_Gaussian_Dynamic_Incoherent>`__, `McStas Virtual
Instrument <#_McStas_Virtual_Instrument>`__, `Molecular
Trace <#_Molecular_Trace>`__, `Neutron Dynamic Total Structure
Factor <#_Neutron_Dynamic_Total>`__, `Order
Parameter <#_Order_Parameter>`__, `Pair Distribution
Function <#_Pair_Distribution_Function>`__, `Radius of
Gyration <#_Radius_Of_Gyration>`__, `Rigid Body
Trajectory <#_Rigid_Body_Trajectory>`__, `Root Mean Square
Deviation <#_Root_Mean_Square>`__, `Root Mean Square
Fluctuation <#_Root_Mean_Square_1>`__, `Static Structure
Factor <#_Static_Structure_Factor>`__, `Voronoi <#_Voronoi>`__, `X-Ray
Static Structure Factor <#_Xray_Static_Structure>`__.
