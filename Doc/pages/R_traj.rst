Trajectory Converters Information
==================================

All converters output the trajectories as .MDT files, which are binary HDF5 files.

+-------------------+--------------------------------------+-------------------+------------------------------------------+----------------------------------------------+
| Type              | File Format                          | Default Extension | Description                              | Improved Other Information                   |
+===================+======================================+===================+==========================================+==============================================+
| CASTEP Converter  | CASTEP trajectory format             | .md               | Converts CASTEP trajectory files to HDF  | Supports all CASTEP file versions with       |
|                   |                                      |                   | format, including velocities and forces. |  metadata integration.                       |
+-------------------+--------------------------------------+-------------------+------------------------------------------+----------------------------------------------+
| CHARMM Converter  | CHARMM trajectory format             |  .pdb (PDB file), | Converts CHARMM trajectory files to HDF  | Integration with PDB file formats for        |
|                   |                                      | other             | format. Integration with PDB file        | enhanced CHARMM trajectory processing.       |
|                   |                                      |                   | formats for enhanced CHARMM trajectory   |                                              |
|                   |                                      |                   | processing.                              |                                              |
+-------------------+--------------------------------------+-------------------+------------------------------------------+----------------------------------------------+
| CP2K Converter    | CP2K trajectory format               |  .xyz (position), | Converts CP2K trajectory files to HDF    | Velocity approximation from positions        |
|                   |                                      | .xyz (velocity),  | format, including positions, velocities, | available; optimal for incomplete            |
|                   |                                      |  .cell (cell)     | and cell dimensions. Velocity            | datasets.                                    |
|                   |                                      |                   | approximation from positions available;  |                                              |
|                   |                                      |                   | optimal for incomplete datasets.         |                                              |
+-------------------+--------------------------------------+-------------------+------------------------------------------+----------------------------------------------+
| DFTB Converter    | DFTB trajectory format               |  .xtd (XTD file), | Converts DFTB trajectory files to HDF    | Requires system's XTD file for accurate      |
|                   |                                      |  .trj (TRJ file)  |  format. Requires system's XTD file for  | trajectory conversion of DFTB files.         |
|                   |                                      |                   | accurate trajectory conversion of DFTB   |                                              |
|                   |                                      |                   | files.                                   |                                              |
+-------------------+--------------------------------------+-------------------+------------------------------------------+----------------------------------------------+
| Discover Converter| Discover module trajectory files     |  .xtd, .his       | Converts Discover module trajectory to   | Converts velocities but not forces.          |
|                   |                                      |                   | HDF format. Enhanced support for         | Enhanced support for variable header         |
|                   |                                      |                   | variable header lengths in CASTEP files. | lengths in CASTEP files.                     |
+-------------------+--------------------------------------+-------------------+------------------------------------------+----------------------------------------------+
| DL_POLY Converter | DL POLY trajectory files             | .field, .history  | Converts DL POLY trajectory to HDF       | Version-selective conversion with            |
|                   |                                      |                   | format. Converts both velocities and     | advanced support for atom aliasing in        |
|                   |                                      |                   | forces. Version-selective conversion     | DL POLY files.                               |
|                   |                                      |                   | with advanced support for atom aliasing  |                                              |
|                   |                                      |                   | in DL POLY files.                        |                                              |
+-------------------+--------------------------------------+-------------------+------------------------------------------+----------------------------------------------+
| DMol Converter    | DMol module trajectory files         | .xtd, .his        | Converts DMol module trajectory to HDF   | Does not convert velocities. Optimized       |
|                   |                                      |                   | format. Does not convert velocities.     | for DMol files from Materials Studio,        |
|                   |                                      |                   | Optimized for DMol files from Materials  | ensuring high fidelity data transfer.        |
|                   |                                      |                   | Studio, ensuring high fidelity data      |                                              |
|                   |                                      |                   | transfer.                                |                                              |
+-------------------+--------------------------------------+-------------------+------------------------------------------+----------------------------------------------+
| Forcite Converter | Forcite module trajectory files      | .xtd, .trj        | Converts Forcite module trajectory to    | Accommodates both XTD and TRJ files          |
|                   |                                      |                   | HDF format. Accommodates both XTD and    | from the Forcite module for                  |
|                   |                                      |                   | TRJ files from the Forcite module for    |  conversions.                                |
|                   |                                      |                   |  conversions.                            |                                              |
+-------------------+--------------------------------------+-------------------+------------------------------------------+----------------------------------------------+
| Generic Converter | ASCII trajectory files               | .gt               | Converts an ASCII trajectory to HDF      | Ideal for converting non-standard or         |
|                   |                                      |                   | format. Ideal for converting non-standard| unsupported trajectory file formats.         |
|                   |                                      |                   | or unsupported trajectory file formats.  |                                              |
+-------------------+--------------------------------------+-------------------+------------------------------------------+----------------------------------------------+
| Gromacs Converter | Gromacs trajectory files             | .pdb, .xtc, .trr  | Converts Gromacs trajectory to HDF       | Requires a PDB file and XTC/TRR              |
|                   |                                      |                   | format. Requires a PDB file and XTC/TRR  | trajectory file. Focused on seamless         |
|                   |                                      |                   | trajectory file. Focused on seamless     | conversion of Gromacs trajectories,          |
|                   |                                      |                   | conversion of Gromacs trajectories,      | including all essential file types.          |
|                   |                                      |                   | including all essential file types.      |                                              |
+-------------------+--------------------------------------+-------------------+------------------------------------------+----------------------------------------------+
| LAMMPS Converter  | LAMMPS trajectory files              | .config, .        | Converts LAMMPS trajectory to HDF        | Requires LAMMPS configuration and            |
|                   |                                      | trajectory        | format. Requires LAMMPS configuration and| trajectory files. Advanced features          |
|                   |                                      |                   | trajectory files. Advanced features      | include mass tolerance and intelligent       |
|                   |                                      |                   | include mass tolerance and intelligent   | mass association for complex simulations.    |
|                   |                                      |                   | mass association for complex simulations.|                                              |
+-------------------+--------------------------------------+-------------------+------------------------------------------+----------------------------------------------+
| NAMD Converter    | NAMD trajectory files                | .pdb, .dcd        | Converts NAMD trajectory to HDF format.  | Requires a PDB file and DCD trajectory       |
|                   |                                      |                   | Requires a PDB file and DCD trajectory   | file. Tailored for NAMD trajectories,        |
|                   |                                      |                   | file. Tailored for NAMD trajectories,    | ensuring accurate data representation        |
|                   |                                      |                   | ensuring accurate data representation in | in conversions.                              |
|                   |                                      |                   | conversions.                             |                                              |
+-------------------+--------------------------------------+-------------------+------------------------------------------+----------------------------------------------+
| PDB Converter     | PDB files                            | .pdb              | Converts standalone PDB files to HDF     | Specialized in PDB file transformations,     |
|                   |                                      |                   | format. Specialized in PDB file          | excluding velocity data for clarity.         |
|                   |                                      |                   | transformations, excluding velocity data |                                              |
|                   |                                      |                   | for clarity.                             |                                              |
+-------------------+--------------------------------------+-------------------+------------------------------------------+----------------------------------------------+
| VASP Converter    | VASP trajectory files (XDATCAR)      | .xdatcar          | Converts VASP trajectory to HDF format.  | Exclusively handles VASP trajectories,       |
|                   |                                      |                   | Exclusively handles VASP trajectories,   | focusing on precision and data integrity.    |
|                   |                                      |                   | focusing on precision and data integrity.|                                              |
+-------------------+--------------------------------------+-------------------+------------------------------------------+----------------------------------------------+
| XPLOR Converter   | X-PLOR trajectory files (PDB and DCD)| .pdb, .dcd        | Converts X-PLOR trajectory to HDF format.| Dedicated to X-PLOR format conversions,      |
|                   |                                      |                   | Dedicated to X-PLOR format conversions,  | ensuring accurate trajectory                 |
|                   |                                      |                   | ensuring accurate trajectory             | representation.                              |
|                   |                                      |                   | representation.                          |                                              |
+-------------------+--------------------------------------+-------------------+------------------------------------------+----------------------------------------------+
