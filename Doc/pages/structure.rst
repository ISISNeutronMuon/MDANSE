
This section is dealing with specific types of analysis performed by
MDANSE. If you are not sure where these fit into the general workflow
of data analysis, please read :ref:`workflow-of-analysis`.

Analysis: Structure
===================

Area Per Molecule
'''''''''''''''''
The Area Per Molecule (APM) analysis in Molecular Dynamics (MD) assesses the surface
area occupied by each molecule within a given system. This tool plays a crucial role
in comprehending molecular arrangement and interactions. Users can specify the
molecule they wish to analyze, such as the default DMPC (a common phospholipid),
ensuring that the molecule's name matches the one in the data file, typically in HDF
format. The APM analysis provides valuable insights into how molecules are
distributed and interact with one another. This analysis is particularly vital in the
study of complex structures like cell membranes. It aids in understanding membrane
functionality and its response to various conditions, shedding light on essential
biological processes. By utilizing APM analysis in MDANSE, researchers can gain a
deeper understanding of molecular systems and their behavior, ultimately contributing
to advancements in fields like biophysics and structural biology.


Coordination Number
'''''''''''''''''''
In chemistry, the Coordination Number (CN) is the total number of neighbors
of a central atom in a molecule or ion. CN plays a vital role in the analysis
of complex molecular systems in simulations, serving several key purposes:

- Packing Effects: CN reveals how atoms are densely packed around central
  groups. This helps identify stable configurations, phase transitions, and
  aggregation patterns.
- Molecular Interactions: It quantifies atom coordination, indicating
  attractive or repulsive forces. High CN values suggest strong interactions
  like bonds, while lower CN values imply weaker or repulsive forces.
- Tracking Structural Changes: CN analysis tracks how atomic coordination
  evolves over time. This is essential for studying dynamic processes and
  structural transformations in simulations.
- Detailed Molecular Organization: CN provides quantitative measures of atom
  arrangements, aiding in the identification of specific patterns like
  solvation shells or coordination spheres.

In the context of MDANSE, CN is defined differently from the traditional
concept. In MDANSE, CN is calculated not only around a single central atom but
around the centers of gravity of a group of atoms. Importantly, when the
selected group comprises only one atom, the MDANSE CN definition is
effectively equivalent to the traditional CN definition based on a central
atom. This extended definition allows for the analysis of coordination within
groups of atoms rather than being limited to individual central atoms.
In this context, the *CN* is defined as:

.. math::
   :label: pfx118

   {n{\left( {r,{r + \mathit{dr}}} \right) = \frac{1}{N_{G}}}{\sum\limits_{g = 1}^{N_{G}}{\sum\limits_{I = 1}^{N_{\mathit{species}}}{n_{\mathit{gI}}\left( {r,{r + \mathit{dr}}} \right)}}}}

where NG is the number of groups of atoms, N\ :sub:`species` is the
number of species found in the system and n\ :sub:`gI`\ (r) is the *CN*
defined for species *I* defined as the number of atoms of species *I*
found in a shell of width *dr* at a distance *r* of the center of
gravity of the group of atom *g*.

*MDANSE* allows one to compute the *CN* on a set of equidistantly spaced
distances at different times

.. math::
   :label: pfx119

   {\mathit{CN}\left( r_{m} \right)\doteq\frac{1}{N_{\mathit{frames}}}\frac{1}{N_{G}}{\sum\limits_{f = 1}^{N_{\mathit{frames}}}{\sum\limits_{g = 1}^{N_{G}}{\sum\limits_{I = 1}^{N_{\mathit{species}}}{CN_{\mathit{gI}}\left( {r_{m},t_{f}} \right)}}}},\\
   {m = 0}\ldots{N_{r} - 1},{n = 0}\ldots{N_{\mathit{frames}} - 1.}}

where N\ :sub:`r` and N\ :sub:`frames` are respectively the number of
distances and times at which the *CN* is evaluated and

.. math::
   :label: pfx120

   {CN_{\mathit{gI}}{\left( {r_{m},t_{f}} \right) = n_{\mathit{gI}}}\left( {r_{m},t_{f}} \right),}

is the number of atoms of species *I* found within [rm, rm + dr] at frame
*f* from the centre of gravity of group *g*.

From these expressions, several remarks can be done. Firstly, the Eqs.
:math:numref:`pfx119` and :math:numref:`pfx120` can be restricted
to intramolecular and intermolecular distances only. Secondly, these
equations can be averaged over the selected frames providing a time
averaged intra and intermolecular *CN*. Finally, the same equations
(time-dependent and time-averaged) can be integrated over r to provide a
cumulative *CN*. *MDANSE* computes all these variations.




Density Profile
'''''''''''''''

-  available for trajectories only

The Density Profile analysis in MDANSE calculates the spatial
distribution of particles or molecules along a specified axis within a
simulation box. This analysis provides valuable insights into how the density of
particles or molecules varies across the system along the chosen axis. By
dividing the axis into segments or bins and specifying the size of each bin
using the parameter **dr**, the Density Profile reveals how particles are
distributed within the system. It is a useful tool for understanding the spatial
arrangement and concentration of particles, making it valuable for identifying
regions of interest and tracking changes over time in molecular simulations.


Eccentricity
''''''''''''

-  available for trajectories only


*Description:* Eccentricity analysis in MDANSE quantifies how elongated or
flattened molecules are, revealing valuable insights into their shape and
structure. Researchers use it to understand molecular geometry and
conformation, aiding the differentiation of molecules by shape. This analysis is
vital for studying structural properties in complex molecular systems and
characterizing molecular shape and morphology.


Molecular Trace
'''''''''''''''

*Description:* Molecular Trace in MDANSE pertains to a calculation or property
related to the analysis of molecular structures within the context of neutron
scattering experiments or molecular dynamics simulations. The "resolution"
parameter in this context determines the level of detail with which molecular
structures are represented or analyzed. A higher resolution results in a more
detailed representation of molecular behavior, allowing for the tracking of
specific molecular entities within simulations. Conversely, a lower resolution
simplifies the analysis for computational efficiency, providing a broader
overview of molecular behavior. The Molecular Trace calculation is a valuable
tool for investigating the movement and behavior of molecular components in
complex systems.

In the context of Molecular Trace analysis, molecular structures are often
represented and analyzed in terms of grid points, where each point corresponds
to a specific location within the molecular system. The resolution parameter
controls the spacing and granularity of these grid points, influencing the
detail of the analysis.


Pair Distribution Function
''''''''''''''''''''''''''

.. _theory-and-implementation-11:

Theory and implementation
                         

The Pair Distribution Function (*PDF*) is an example of a pair
correlation function, which describes how, on average, the atoms in a
system are radially packed around each other. This proves to be a
particularly effective way of describing the average structure of
disordered molecular systems such as liquids. Also in systems like
liquids, where there is continual movement of the atoms and a single
snapshot of the system shows only the instantaneous disorder, it is
extremely useful to be able to deal with the average structure.

The *PDF* is useful in other ways. For example, it is something that can
be deduced experimentally from x-ray or neutron diffraction studies,
thus providing a direct comparison between experiment and simulation. It
can also be used in conjunction with the interatomic pair potential
function to calculate the internal energy of the system, usually quite
accurately.

Mathematically, the *PDF* can be computed using the following formula:

.. math::
   :label: pfx121

   {\mathit{PDF}{(r) = {\sum\limits_{{I = 1},J\geq I}^{N_{\mathit{species}}}n_{I}}}n_{J}\omega_{I}\omega_{J}g_{\mathit{IJ}}(r)}

where N\ :sub:`species` is the number of selected species, n\ :sub:`I`
and n\ :sub:`J` are respectively the numbers of atoms of species *I* and
*J*, :math:`\omega`\ :sub:`I` and :math:`\omega`\ :sub:`J` respectively the weights for species
*I* and *J* (see Section `Coordination Number`_ for more details) and

.. math::
   :label: pfx122
   
   {\mathit{PD}F_{\mathit{\alpha\beta}}(r)}

\ is the partial *PDF* for I and J species that can be defined as:

.. math::
   :label: pfx123

   {\mathit{PD}F_{\mathit{IJ}}{(r) = \frac{\left\langle {\sum\limits_{\alpha = 1}^{n_{I}}{n_{\alpha J}(r)}} \right\rangle}{n_{I}\rho_{J}4\pi r^{2}\mathit{dr}}}}

where :math:`\rho`\ :sub:`J` is the density of atom of species *J* and

.. math::
   :label: pfx124
   
   {n_{\alpha J}(r)}

\ is the mean number of atoms of species *J* in a shell of width *dr* at
distance *r* of the atom :math:`\alpha` of species *I*.

From the computation of PDF, two related quantities are also calculated;
the Radial Distribution Function (RDF), defined as

.. math::
   :label: pfx125

   {\mathit{RDF}{(r) = 4}\pi r^{2}\rho_{0}\mathit{PDF}(r),}

and the Total Correlation Function (TCF), defined as

.. math::
   :label: pfx126

   {\mathit{TCF}{(r) = 4}\pi r\rho_{0}\left( {\mathit{PDF}{(r) - 1}} \right),}

where :math:`\rho`\ :sub:`0` is the average atomic density, which is defined as

.. math::
   :label: pfx127

   {{\rho_{0} = \frac{N}{V}},}

where N is the total number of atoms in the system and V the volume of
the simulation.

All these quantities are initially calculated as intramolecular and
intermolecular parts for each pair of atoms, which are then added to
create the total PDF/RDF/TCF for each pair of atoms, as well as the
total intramolecular and total intermolecular values. Lastly, the total
functions are computed. Please note, however, that in the case of TCF,
the below set of equations has been chosen, which will return results
that differ from those of nMOLDYN.

.. math::
   :label: pfx128

   {\mathit{TCF}_{\mathit{intramolecular}}{(r) = 4}\pi r\rho_{0}\mathit{PDF}_{\mathit{intramolecular}}(r),}

.. math::
   :label: pfx129

   {\mathit{TCF}_{\mathit{intermolecular}}{(r) = 4}\pi r\rho_{0}\left( {\mathit{PDF}_{\mathit{intermolecular}}{(r) - 1}} \right),}

.. math::
   :label: pfx130

   {\mathit{TCF}_{\mathit{total}}{(r) = 4}\pi r\rho_{0}\left( {\mathit{PDF}_{\mathit{total}}{(r) - 1}} \right),}


Root Mean Square Deviation
''''''''''''''''''''''''''
                         
The Root Mean-Square Deviation (*RMSD*) is perhaps the most popular estimator
of structural similarity. It quantifies differences between two structures by
measuring the root mean-square of atomic position differences, revealing
insights into their structural dissimilarities. It is a numerical measure of
the difference between two structures. It can be defined as:


.. math::
   :label: pfx131

   {\mathit{RMSD}{(t) = \sqrt{\frac{\sum\limits_{\alpha = 1}^{N_{\alpha}}\left( {r_{\alpha}{(t) - r_{\alpha}}\left( t_{\mathit{ref}} \right)} \right)}{N_{\alpha}}}}}

where N\_ is the number of atoms of the system, and r_(t) and r_(tref )
are respectively the position of atom :math:`\alpha` at time t and tref where tref is
a reference time usually chosen as the first step of the simulation.
Typically, *RMSD* is used to quantify the structural evolution of the
system during the simulation. It can provide precious information about
the system especially if it reached equilibrium or conversely if major
structural changes occurred during the simulation.

In Molecular Dynamics Analysis for Neutron Scattering Experiments
(*MDANSE*), *RMSD* is computed using the discretized version of equation
:math:numref:`pfx130`:

.. math::
   :label: pfx132

   {\mathit{RMSD}{\left( {n\cdot\Delta t} \right) = \sqrt{\frac{\sum\limits_{\alpha = 1}^{N_{\alpha}}\left( {r_{\alpha}{(t) - r_{\mathit{ref}}}(t)} \right)}{N_{\alpha}}}},{n = 0}\ldots{N_{t} - 1}.}

where Nt is the number of frames and

.. math::
   :label: pfx133
   
   {\mathrm{\Delta}t}

\ is the time step.

.

Root Mean Square Fluctuation
''''''''''''''''''''''''''''

-  available for trajectories only

Root Mean Square Fluctuation (RMSF) assesses how the positions of atoms or
molecules within a system fluctuate over time. Specifically, RMSF measures the
average magnitude of deviations or fluctuations in atomic positions from their
mean positions during a simulation.

RMSF analysis is valuable for understanding the flexibility and stability of
molecules within a simulation, providing insights into regions where atoms or
groups of atoms exhibit significant fluctuations. This information can be crucial
for studying the dynamic behavior of biomolecules, protein-ligand interactions,
or any molecular system subject to temporal variations.

Radius Of Gyration
''''''''''''''''''

.. _theory-and-implementation-13:

Theory and implementation
                         

Radius Of Gyration (*ROG*) is the name of several related measures of
the size of an object, a surface, or an ensemble of points. It is
calculated as the Root Mean Square Distance between the system and a
reference that can be either the centre of gravity of the system either
a given axis. 

The *ROG* serves as a quantitative measure that characterizes the spatial distribution
and compactness of molecular or ensemble structures. ROG is instrumental in size determination,
providing precise insights into the dimensions of objects or systems. Moreover, it
plays a crucial role in shape analysis, elucidating how molecular components
are arranged concerning the center of gravity. Its ability to track
structural fluctuations over time is essential for studying dynamic processes
in molecular systems.

In *MDANSE*, the reference is chosen to be the centre of
gravity of the system under study. Mathematically, it can be defined as:

.. math::
   :label: pfx134

   {\mathit{ROG}{(t) = \sqrt{\frac{\sum\limits_{\alpha = 1}^{N_{\alpha}}\left( {r_{\alpha}{(t) - r_{\mathit{cms}}}(t)} \right)}{N_{\alpha}}}}}

where :math:`N_{\alpha}`
is the number of atoms of the system, and :math:`r_{\alpha}(t)` and
:math:`r_{cms}(t)` are respectively the position of atom :math:`\alpha` and the
centre of mass of the system at time t.

*ROG* describes the overall spread of the molecule and as such is a good
measure for the molecule compactness. For example, it can be useful when
monitoring folding process.

In *MDANSE*, *ROG* is computed using the discretized version of equation
:math:numref:`pfx131`:

.. math::
   :label: pfx135

   {\mathit{ROG}{\left( {n\cdot\Delta t} \right) = \sqrt{\frac{\sum\limits_{\alpha = 1}^{N_{\alpha}}\left( {r_{\alpha}{(t) - r_{\mathit{cms}}}(t)} \right)}{N_{\alpha}}}},{n = 0}\ldots{N_{t} - 1.}}

where N\ :sub:`t` is the number of frames and Δt is the time step.



Solvent Accessible Surface
''''''''''''''''''''''''''

-  available for trajectories only


The Solvent Accessible Surface calculation involves defining the surface
accessibility of molecules or atoms by creating a mesh of points. The
number of points is determined by the field discussed, influencing the
level of detail in the surface representation. Essentially, a higher
density of points leads to a finer-grained representation, capturing
smaller surface features and intricacies.

- **Probe Radius**: Measured in nanometers, the probe radius is a crucial
  parameter influencing the precision of the calculation. Smaller probe
  radii provide a more detailed and comprehensive assessment of the
  molecular surface area, often resulting in a larger reported surface
  area due to increased sensitivity to surface features.

Spatial Density
'''''''''''''''

.. _theory-and-implementation-14:

Theory and implementation
                         

The Spatial Density (*SD*) can be seen as a generalization of the pair
distribution function. Indeed, pair distribution functions are defined
as orientationally averaged distribution functions. Although these
correlation functions reflect many key features of the short-range order
in molecular systems, it should be realized that an average spatial
assembly of non-spherical particles cannot be uniquely characterized
from these one-dimensional functions. So, structural models postulated
for the molecular ordering in non-simple systems based only on
one-dimensional *PDF* will always be somewhat ambiguous. The goal of
*SD* analysis is to provide greater clarity in the structural analysis
of molecular systems by utilizing distribution function which span both
the radial and angular coordinates of the separation vector. This can
provide useful information about the average local structure in a
complex system.

*MDANSE* allows one to compute the *SD* in spherical coordinates on a
set of concentric shells surrounding the centres of mass of selected
triplets of atoms using the formula:

.. math::
   :label: pfx136
   
   {\mathit{SD}\left( {r_{l},\theta_{m},\phi_{n}} \right)\doteq\frac{1}{N_{\mathit{triplets}N_{\mathit{groups}}}}{\sum\limits_{t = 1}^{N_{\mathit{triplets}}}{\sum\limits_{g = 1}^{N_{\mathit{groups}}}\left\langle {n_{\mathit{tg}}\left( {r_{l},\theta_{m},\phi_{n}} \right)} \right\rangle}},}

.. math::
   :label: pfx137

   {l = 0}\ldots{N_{r} - 1},{m = 0}\ldots{N_{\theta} - 1},{n = 0}\ldots{N_{\phi} - 1.}

where N\ :sub:`triplets` and N\ :sub:`groups` are respectively the
number of triplets and groups, r\ :sub:`l`, θ\ :sub:`m` and φ\ :sub:`n`
are the spherical coordinates at which the *SD* is evaluated,
N\ :sub:`r`, :math:`N_{\theta}` and :math:`N_{\phi}`
are respectively the number of discrete *r*, θ and φ values and
n\ :sub:`tg`\ (r\ :sub:`l`, θ\ :sub:`m`, φ\ :sub:`n`) is the number of
group of atoms of type *g* whose centres of mass is found to be in the
volume element defined by [r, r + dr], [θ, θ + dθ] and [φ, φ + dφ] in
the spherical coordinates basis cantered on the centre of mass of
triplet *t*. So technically, *MDANSE* proceeds more or less in the
following way:

-  defines the centre of mass

   .. math::
     :label: pfx138
   
     {c_{i}^{t}{i = 1},2\ldots N_{\mathit{triplets}}}

   \ for each triplet of atoms,

-  defines the centre of mass

   .. math::
     :label: pfx139
     
     {c_{i}^{g}{i = 1},2\ldots N_{\mathit{groups}}}

   \ for each group of atoms,

-  constructs an oriented orthonormal basis

   .. math::
     :label: pfx140
     
     {R_{i}^{t}{i = 1},2\ldots N_{\mathit{triplets}}}

   \ cantered on each c\ :sup:`t`, this basis is defined from the three
   vectors **v1**, **v2**, **v3**,

   -  

      .. math::
        :label: pfx141 
        
        {v_{1} = \frac{n_{1} + n_{2}}{\left| \left| {n_{1} + n_{2}} \right| \right|}}

      \ where **n1** and **n2** are respectively the normalized vectors
      in (**a1**,\ **a2**) and (**a1**,\ **a3**) directions where
      (**a1**,\ **a2**,\ **a3**) are the three atoms of the triplet *t*,
   -  v\ :sub:`2` is defined as the clockwise normal vector orthogonal
      to v1 that belongs to the plane defined by **a1**, **a2** and
      **a3** atoms,
   -  

      .. math::
        :label: pfx142
        
        {{\overrightarrow{v_{3}} = \overrightarrow{v_{1}}}\times\overrightarrow{v_{2}}}

-  expresses the cartesian coordinates of each c\ :sup:`g` in each
   R\ :sup:`t`,

-  transforms these coordinates in spherical coordinates,

-  discretizes the spherical coordinates in r\ :sub:`l`, θ\ :sub:`m` and
   φ\ :sub:`n`,

-  does

   .. math::
     :label: pfx143
     
     {n_{\mathit{tg}}{\left( {r_{l},\theta_{m},\phi_{n}} \right) = n_{\mathit{tg}}}{\left( {r_{l},\theta_{m},\phi_{n}} \right) + 1}}


`

Static Structure Factor
'''''''''''''''''''''''


The **Static Structure Factor** analysis offers a convenient method to
calculate the static coherent structure factor, represented as S(q), where
S(q) = F\ :sub:`coh`\ (q, t = 0). This factor is fundamental for gaining
insights into the ordered arrangements of particles within a material.

This analysis serves as a valuable tool, especially in trajectory-based
simulations, for assessing the ordered structures of particles in a material.
It provides the flexibility to control both distance and q-value ranges,
facilitating a comprehensive exploration of the material's structural
properties.


Voronoi
''''''''

In MDANSE, Voronoi analysis plays a pivotal role in characterizing the
spatial distribution and organization of particles or atoms within a
molecular dynamics simulation. This analysis entails the division of the
simulation box into Voronoi cells, with each cell centered around a
particle. Voronoi cells provide essential insights into the local
environment and packing of particles, allowing researchers to understand
the arrangement and interactions of molecules in detail. Within MDANSE,
the "apply periodic_boundary_condition" parameter is available to ensure
accurate analysis, particularly for systems extending beyond the simulation
box. This capability enables users to uncover valuable details about
molecular structures and dynamics.


Xray Static Structure Factor
''''''''''''''''''''''''''''

MDANSE's Xray Static Structure Factor analysis is tailored for neutron
and X-ray scattering experiments in material science. It systematically
investigates material structural properties by analyzing particle
distribution and ordering. Researchers gain precise insights into
fundamental aspects like atomic spacing and ordered patterns. MDANSE
provides fine-grained control over "r values" and "q values," enabling
customization for probing specific material structural characteristics.
This tool is invaluable for advancing scientific and industrial research,
especially in neutron scattering experiments.
