
Plotting Options
================

Plots
-----

In this section, we'll explore various plotting options tailored to MDANSE
(Molecular Dynamics Analysis for Neutron Scattering Experiments) data, helping
you effectively analyze and visualize your scientific findings.

To learn more about how to use these plots and make the most out of MDANSE's
visualization tools, refer to the technical references and user guides available
in the MDANSE documentation. These resources provide in-depth instructions,
examples, and tips on utilizing the plotting capabilities. 

Understanding Plotting Options
-------------------------------

**Line Plotter:**
    Visualize dynamic trends in MDANSE data, e.g., temperature fluctuations,
    energy profiles, or scattering intensities over time. Customize line styles,
    colors, and axes settings.

**Image Plotter:**
    Display MDANSE data as heatmaps or spatial distributions. Adjust aspect
    ratios, colormaps, and settings for neutron scattering patterns, electron
    density maps, or spatial correlations.

**Elevation Plotter:**
    Explore 3D MDANSE structures and landscapes. Zoom in on molecular
    structures and adjust contrast for detailed examination of complex systems,
    like biomolecules or nanomaterials.

**2D Slice Plotter:**
    Visualize specific 3D MDANSE data slices, focusing on dimensions and regions
    of interest. Simplify density profiles, radial distribution functions, or
    cross-sectional views of molecular assemblies.

**Iso Surface Plotter:**
    Create 3D surface visualizations with various rendering modes. Adjust opacity,
    contours, and slice orientations to highlight features in volumetric data,
    such as solvent density distributions or macromolecular structures.

Choosing the Right Plotting Option
----------------------------------

Selecting the appropriate plotting option is crucial for meaningful insights:

**Line Plotter:**
    For tracking temporal changes like temperature and energy during simulations.

**Image Plotter:**
    To display spatial information, such as scattering patterns, electron
    densities, or diffusion maps.

**Elevation Plotter:**
    Useful for gaining a 3D perspective on complex molecular structures,
    nanomaterials, or biomolecules.

**2D Slice Plotter:**
    When focusing on specific 3D data sections, aiding local property analysis.

**Iso Surface Plotter:**
    Great for rendering 3D volumetric data, highlighting complex structures like
    solvent-solute interfaces or protein conformations.



Line Plotter
-------------

Figure 1 shows a Line Plot of temperature vs. time. In this Line Plotter,
the x-axis represents time (in picoseconds), while the y-axis represents
temperature (in Kelvin). The graph shows how the temperature of a molecular
system evolves during a 1000 ps molecular dynamics simulation. This plot
allows for tracking variations and trends in the system's temperature,
revealing valuable insights into its thermal behavior over time.

MDANSE's Line Plotter is an essential tool for visualizing dynamic data trends.
It's particularly valuable for tracking changes in critical parameters, such as
temperature fluctuations, energy profiles, or scattering intensities, as they
evolve over time during simulations. Users can adjust line styles, colors, and
axes settings to enhance data clarity. This tool is useful for analyzing
temporal behavior. For instance, it can identify temperature shifts that may
indicate phase transitions, fluctuations in energy levels signifying critical
events, or scattering intensity variations revealing structural changes.

Image Plotter
-------------

Figure 2 shows an Image Plot of a neutron scattering pattern from a
crystalline material. It employs scattering angles (in degrees) on both
the x and y-axes, while the colormap represents neutron scattering
intensity. This visualization aids in the identification of
crystallographic peaks and provides structural insights.

The Image Plotter in MDANSE simplifies spatial data visualization,
making it suitable for systems with complex data structures, including
neutron scattering patterns or electron density maps. Its user-friendly
interface allows you to customize aspect ratios and select colormaps
that best highlight essential data features. This tool aids in pattern
recognition and structural analysis. It is particularly beneficial for
understanding structural insights within diverse systems.

Elevation Plotter
-----------------

Figure 3 shows a three-dimensional elevation plot of a biomolecule. The
x and y-axes denote spatial coordinates (in angstroms), while the z-axis
represents elevation, offering a three-dimensional view of a protein's
structure. It provides a view of its spatial arrangement, including bond
angles and structural features.

MDANSE's Elevation Plotter is for exploring complex three-dimensional
structures like biomolecules and nanomaterials. Researchers can zoom in
on molecular structures, adjust contrast settings, and navigate 3D
topography. This tool reveals subtle spatial details often concealed in
2D representations, aiding in visualizing surface characteristics or
deconstructing the structure of biomolecules.

2D Slice Plotter
----------------

Figure 4 shows a Density Profile Slice. The 2D Slice Plotter reveals the
density profile of solvent molecules within a specific plane of a
nanomaterial. Spatial coordinates (in nanometers) are depicted on the x
and y-axes, while the color map indicates particle density. This plot is
instrumental in understanding spatial variations in solvent distribution.

The 2D Slice Plotter simplifies the visualization of cross-sectional
views within 3D datasets. It streamlines the examination of localized
properties, enabling in-depth analysis of factors like density profiles
or composition within specific sections of a system. Researchers employ
it to study particle distribution in nanomaterials or conduct
compositional analyses of specific molecular layers.

Iso Surface Plotter
-------------------

Figure 5 shows an Electron Density Iso Surface. This provides a detailed
visualization of the electron density distribution around a molecule. It
utilizes spatial coordinates (in angstroms) on the x, y, and z-axes,
while the isosurface illustrates specific electron density levels.
Researchers can manipulate parameters to emphasize molecular shapes and
binding sites within the electron density data.

MDANSE's Iso Surface Plotter effectively visualizes volumetric data.
Researchers can customize parameters like opacity and contour levels to
emphasize features within 3D datasets, such as solvent density
distributions or protein conformations. This tool aids in visualizing and
analyzing complex structures and interfaces within molecular or material
systems, facilitating tasks like visualizing molecular binding sites or
solvent molecule arrangements around nanoparticles. Researchers gain a
comprehensive understanding of intricate structures and their scientific
significance.


