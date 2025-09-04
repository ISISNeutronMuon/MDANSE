
This section is dealing with specific types of analysis performed by
MDANSE. If you are not sure where these fit into the general workflow
of data analysis, please read :ref:`workflow-of-analysis`.

Analysis: Structure
===================

This section contains the following plugins:

-  :ref:`area-per-molecule`
-  :ref:`coordination-number`
-  :ref:`eccentricity`
-  :ref:`molecular-trace`
-  :ref:`pair-distribution-function`
-  :ref:`radius-of-gyration`
-  :ref:`solvent-accessible-surface`
-  :ref:`voronoi`

.. _area-per-molecule:

Area Per Molecule
'''''''''''''''''

The area per molecule (APM) analysis in molecular dynamics (MD) assesses the surface
area occupied by each molecule within a given system. This tool plays a crucial role
in comprehending molecular arrangement and interactions. Users can specify the
molecule they wish to analyze. The APM analysis provides valuable insights into how molecules are
distributed and interact with one another. This analysis is particularly vital in the
study of complex structures like cell membranes. It aids in understanding membrane
functionality and its response to various conditions, shedding light on essential
biological processes. By utilizing APM analysis in MDANSE, researchers can gain a
deeper understanding of molecular systems and their behavior, ultimately contributing
to advancements in fields like biophysics and structural biology.

.. _coordination-number:

Coordination Number
'''''''''''''''''''

In chemistry, the coordination number (CN) is the total number of neighbors
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

In MDANSE the CN is defined as

.. math::
   :label: cn1

    \mathrm{CN}_{\alpha\beta}(r) =  c_{\beta} \int\limits_{0}^{\infty}\mathrm{d}r \, 4 \pi r^2  \rho g_{\alpha\beta}(r)

where :math:`g_{\alpha\beta}(r)` is the partial pair distribution function,
see Section :ref:`pair-distribution-function` for details.

.. _eccentricity:

Eccentricity
''''''''''''

Eccentricity analysis in MDANSE quantifies how spherical a system is and
can be used to observe how the geometry of the system changes over time.
The eccentricity of a selection of atom is calculated using the equation

.. math::
   :label: ecc1

    \mathrm{ecc} = \frac{\sqrt{\lambda_{3}^2 - \lambda_{1}^2}}{\lambda_{3}}

where :math:`\lambda_{1}` and :math:`\lambda_{3}` are its smallest and
largest principal moments of inertia. A spherically symmetric
selection of atoms will have an eccentricity approaching 0 and an
aspherical selection of atoms will have a eccentricity approaching 1.

.. _molecular-trace:

Molecular Trace
'''''''''''''''

Molecular trace in MDANSE pertains to a calculation or property
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

In the context of molecular trace analysis, molecular structures are often
represented and analyzed in terms of grid points, where each point corresponds
to a specific location within the molecular system. The resolution parameter
controls the spacing and granularity of these grid points, influencing the
detail of the analysis.


.. _pair-distribution-function:

Pair Distribution Function
''''''''''''''''''''''''''

The pair distribution function (PDF) is an example of a pair
correlation function, which describes how, on average, the atoms in a
system are packed around each other. This proves to be a
particularly effective way of describing the average structure of
disordered molecular systems such as liquids. Also in systems like
liquids, where there is continual movement of the atoms and a single
snapshot of the system shows only the instantaneous disorder, it is
extremely useful to be able to deal with the average structure.

The PDF is useful in other ways. For example, it is something that can
be deduced experimentally from x-ray or neutron diffraction studies,
thus providing a direct comparison between experiment and simulation. It
can also be used in conjunction with the interatomic pair potential
function to calculate the internal energy of the system, usually quite
accurately.

Mathematically, the PDF can be computed using the following formula:

.. math::
   :label: pdf1

   g(\mathbf{r}) = \sum_{\alpha}\sum_{\beta \geq \alpha}  W_{\alpha\beta} g_{\alpha\beta}(\mathbf{r}), \qquad g_{\alpha\beta}(\mathbf{r}) = \frac{1}{Nc_{\alpha}c_{\beta}}\frac{1}{\rho} \frac{\mathrm{d} N_{\alpha\beta}(\mathbf{r})}{ \mathrm{d} \mathbf{r}}

where :math:`g_{\alpha\beta}(\mathbf{r})` is the partial PDF for :math:`\alpha`
and :math:`\beta` atom-types, :math:`N(\mathbf{r})`
is the average number of particles in the volume :math:`\mathrm{d} \mathbf{r}`
at the position :math:`\mathbf{r}` between the atom-types :math:`\alpha`
and :math:`\beta` and :math:`\rho` is the density of the system.

For isotropic system we can define the PDF as a function of distance

.. math::
   :label: pdf2

   g(r) = \sum_{\alpha}\sum_{\beta \geq \alpha}  W_{\alpha\beta} g_{\alpha\beta}(r), \qquad g_{\alpha\beta}(r) = \frac{1}{Nc_{\alpha}c_{\beta}} \frac{1}{\rho} \frac{1}{4 \pi r^2}  \frac{\mathrm{d} N(r)}{ \mathrm{d} r}

where :math:`N(r)` is the average number of particles in the
volume :math:`4 \pi r^2 \mathrm{d} r` at a distance :math:`r`
between the atom-types :math:`\alpha` and :math:`\beta`.

From the computation of PDF, two related quantities are also calculated;
the radial distribution function (RDF) and the total correlation function (TCF)

.. math::
   :label: pdf3

   \mathrm{RDF}{(r) = 4}\pi r^{2}\rho g(r), \qquad \mathrm{TCF}{(r) = 4}\pi r\rho\left[ {g{(r) - 1}} \right].

All these quantities are initially calculated as intramolecular and
intermolecular parts for each pair of atoms, which are then added to
create the total PDF/RDF/TCF for each pair of atoms, as well as the
total intramolecular and total intermolecular values.
Please note, however, that in the case of TCF, the below set of equations
have been chosen, which will return results that differ from those
of nMOLDYN

.. math::
   :label: pdf4

   {\mathrm{TCF}_{\mathrm{intra}}{(r) = 4}\pi r\rho g_{\mathrm{intra}}(r),}

.. math::
   :label: pdf5

   {\mathrm{TCF}_{\mathrm{inter}}{(r) = 4}\pi r\rho\left[ {g_{\mathrm{inter}}{(r) - 1}} \right],}

.. math::
   :label: pdf6

   {\mathrm{TCF}_{\mathrm{tot}}{(r) = 4}\pi r\rho\left[ {g_{\mathrm{tot}}{(r) - 1}} \right].}


.. _radius-of-gyration:

Radius of Gyration
''''''''''''''''''

Radius of gyration (ROG) is calculated as a root (atomic mass weighted) mean
square distance of the components of a system relative to either its centre of
mass or a given axis of rotation. The ROG serves as a quantitative
measure which can be used to characterize the spatial distribution of
a system such as a molecule or a cluster of atoms. In MDANSE, ROG is
calculated relative to the systems centre of mass. It can be defined as

.. math::
   :label: rog1

    \mathrm{ROG}(t) = \sqrt{ \frac{\sum_{j}m_{j} \vert \mathbf{r}_{j}(t) - \mathbf{r}_{\mathrm{COM}}(t) \vert^{2}}{\sum_{j} m_{j}} }

where :math:`m_j` is the mass and :math:`\mathbf{r}_{j}(t)` are the positions
of the atom :math:`j`, :math:`\mathbf{r}_{\mathrm{COM}}(t)` is the centre of mass of
the system and :math:`t` is the time of the simulation. ROG can be used to
describe the overall spread of the molecule and as such is a good measure
for the molecule compactness. For example, it can be useful when monitoring
folding process of a protein.


.. _solvent-accessible-surface:

Solvent Accessible Surface
''''''''''''''''''''''''''

The solvent accessible surface calculation involves defining the surface
accessibility of molecules or atoms by creating a mesh of points. The
number of points is determined by the field discussed, influencing the
level of detail in the surface representation. Essentially, a higher
density of points leads to a finer-grained representation, capturing
smaller surface features and intricacies.

**Probe Radius**: Measured in nanometers, the probe radius is a crucial
parameter influencing the precision of the calculation. Smaller probe
radii provide a more detailed and  assessment of the
molecular surface area, often resulting in a larger reported surface
area due to increased sensitivity to surface features.


.. _voronoi:

Voronoi
'''''''

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
