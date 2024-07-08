Trajectory Converters Information
==================================



+-------------------+--------------------------------------+-------------------+--------------------------------------+------------------------------------------+----------------------------------------------+
| Type              | File Format                          | Default Extension | Output                               | Description                              | Improved Other Information                   |
+===================+======================================+===================+======================================+==========================================+==============================================+
| CASTEP Converter  | CASTEP trajectory format             | .md               | HDF format file containing trajectory| Converts CASTEP trajectory files to HDF  | Supports all CASTEP file versions with       |
|                   |                                      |                   | data                                 | format, including velocities and forces. |  metadata integration.          |
+-------------------+--------------------------------------+-------------------+--------------------------------------+------------------------------------------+----------------------------------------------+
| CHARMM Converter  | CHARMM trajectory format             |  .pdb (PDB file), | HDF format file containing trajectory| Converts CHARMM trajectory files to HDF  | Integration with PDB file formats for        |
|                   |                                      | other             | data                                 | format. Integration with PDB file        | enhanced CHARMM trajectory processing.       |
|                   |                                      |                   |                                      | formats for enhanced CHARMM trajectory   |                                              |
|                   |                                      |                   |                                      | processing.                              |                                              |
+-------------------+--------------------------------------+-------------------+--------------------------------------+------------------------------------------+----------------------------------------------+
| CP2K Converter    | CP2K trajectory format               |  .xyz (position), | HDF format file containing trajectory| Converts CP2K trajectory files to HDF    | Velocity approximation from positions        |
|                   |                                      | .xyz (velocity),  | data                                 | format, including positions, velocities, | available; optimal for incomplete            |
|                   |                                      |  .cell (cell)     |                                      | and cell dimensions. Velocity            | datasets.                                    |
|                   |                                      |                   |                                      | approximation from positions available;  |                                              |
|                   |                                      |                   |                                      | optimal for incomplete datasets.         |                                              |
+-------------------+--------------------------------------+-------------------+--------------------------------------+------------------------------------------+----------------------------------------------+
| DFTB Converter    | DFTB trajectory format               |  .xtd (XTD file), | HDF format file containing trajectory| Converts DFTB trajectory files to HDF    | Requires system's XTD file for accurate      |
|                   |                                      |  .trj (TRJ file)  | data                                 |  format. Requires system's XTD file for  | trajectory conversion of DFTB files.         |
|                   |                                      |                   |                                      | accurate trajectory conversion of DFTB   |                                              |
|                   |                                      |                   |                                      | files.                                   |                                              |
+-------------------+--------------------------------------+-------------------+--------------------------------------+------------------------------------------+----------------------------------------------+
| Discover Converter| Discover module trajectory files     |  .xtd, .his       | HDF format file containing trajectory| Converts Discover module trajectory to   | Converts velocities but not forces.          |
|                   |                                      |                   | data                                 | HDF format. Enhanced support for         | Enhanced support for variable header         |
|                   |                                      |                   |                                      | variable header lengths in CASTEP files. | lengths in CASTEP files.                     |
+-------------------+--------------------------------------+-------------------+--------------------------------------+------------------------------------------+----------------------------------------------+
| DL_POLY Converter | DL POLY trajectory files             | .field, .history  | HDF format file containing trajectory| Converts DL POLY trajectory to HDF       | Version-selective conversion with            |
|                   |                                      |                   | data                                 | format. Converts both velocities and     | advanced support for atom aliasing in        |
|                   |                                      |                   |                                      | forces. Version-selective conversion     | DL POLY files.                               |
|                   |                                      |                   |                                      | with advanced support for atom aliasing  |                                              |
|                   |                                      |                   |                                      | in DL POLY files.                        |                                              |
+-------------------+--------------------------------------+-------------------+--------------------------------------+------------------------------------------+----------------------------------------------+
| DMol Converter    | DMol module trajectory files         | .xtd, .his        | HDF format file containing trajectory| Converts DMol module trajectory to HDF   | Does not convert velocities. Optimized       |
|                   |                                      |                   | data                                 | format. Does not convert velocities.     | for DMol files from Materials Studio,        |
|                   |                                      |                   |                                      | Optimized for DMol files from Materials  | ensuring high fidelity data transfer.        |
|                   |                                      |                   |                                      | Studio, ensuring high fidelity data      |                                              |
|                   |                                      |                   |                                      | transfer.                                |                                              |
+-------------------+--------------------------------------+-------------------+--------------------------------------+------------------------------------------+----------------------------------------------+
| Forcite Converter | Forcite module trajectory files      | .xtd, .trj        | HDF format file containing trajectory| Converts Forcite module trajectory to    | Accommodates both XTD and TRJ files          |
|                   |                                      |                   | data                                 | HDF format. Accommodates both XTD and    | from the Forcite module for                  |
|                   |                                      |                   |                                      | TRJ files from the Forcite module for    |  conversions.                   |
|                   |                                      |                   |                                      |  conversions.               |                                              |
+-------------------+--------------------------------------+-------------------+--------------------------------------+------------------------------------------+----------------------------------------------+
| Generic Converter | ASCII trajectory files               | .gt               | HDF format file containing trajectory| Converts an ASCII trajectory to HDF      | Ideal for converting non-standard or         |
|                   |                                      |                   | data                                 | format. Ideal for converting non-standard| unsupported trajectory file formats.         |
|                   |                                      |                   |                                      | or unsupported trajectory file formats.  |                                              |
+-------------------+--------------------------------------+-------------------+--------------------------------------+------------------------------------------+----------------------------------------------+
| Gromacs Converter | Gromacs trajectory files             | .pdb, .xtc, .trr  | HDF format file containing trajectory| Converts Gromacs trajectory to HDF       | Requires a PDB file and XTC/TRR              |
|                   |                                      |                   | data                                 | format. Requires a PDB file and XTC/TRR  | trajectory file. Focused on seamless         |
|                   |                                      |                   |                                      | trajectory file. Focused on seamless     | conversion of Gromacs trajectories,          |
|                   |                                      |                   |                                      | conversion of Gromacs trajectories,      | including all essential file types.          |
|                   |                                      |                   |                                      | including all essential file types.      |                                              |
+-------------------+--------------------------------------+-------------------+--------------------------------------+------------------------------------------+----------------------------------------------+
| LAMMPS Converter  | LAMMPS trajectory files              | .config, .        | HDF format file containing trajectory| Converts LAMMPS trajectory to HDF        | Requires LAMMPS configuration and            |
|                   |                                      | trajectory        | data                                 | format. Requires LAMMPS configuration and| trajectory files. Advanced features          |
|                   |                                      |                   |                                      | trajectory files. Advanced features      | include mass tolerance and intelligent       |
|                   |                                      |                   |                                      | include mass tolerance and intelligent   | mass association for complex simulations.    |
|                   |                                      |                   |                                      | mass association for complex simulations.|                                              |
+-------------------+--------------------------------------+-------------------+--------------------------------------+------------------------------------------+----------------------------------------------+
| NAMD Converter    | NAMD trajectory files                | .pdb, .dcd        | HDF format file containing trajectory| Converts NAMD trajectory to HDF format.  | Requires a PDB file and DCD trajectory       |
|                   |                                      |                   | data                                 | Requires a PDB file and DCD trajectory   | file. Tailored for NAMD trajectories,        |
|                   |                                      |                   |                                      | file. Tailored for NAMD trajectories,    | ensuring accurate data representation        |
|                   |                                      |                   |                                      | ensuring accurate data representation in | in conversions.                              |
|                   |                                      |                   |                                      | conversions.                             |                                              |
+-------------------+--------------------------------------+-------------------+--------------------------------------+------------------------------------------+----------------------------------------------+
| PDB Converter     | PDB files                            | .pdb              | HDF format file containing trajectory| Converts standalone PDB files to HDF     | Specialized in PDB file transformations,     |
|                   |                                      |                   | data                                 | format. Specialized in PDB file          | excluding velocity data for clarity.         |
|                   |                                      |                   |                                      | transformations, excluding velocity data |                                              |
|                   |                                      |                   |                                      | for clarity.                             |                                              |
+-------------------+--------------------------------------+-------------------+--------------------------------------+------------------------------------------+----------------------------------------------+
| VASP Converter    | VASP trajectory files (XDATCAR)      | .xdatcar          | HDF format file containing trajectory| Converts VASP trajectory to HDF format.  | Exclusively handles VASP trajectories,       |
|                   |                                      |                   | data                                 | Exclusively handles VASP trajectories,   | focusing on precision and data integrity.    |
|                   |                                      |                   |                                      | focusing on precision and data integrity.|                                              |
+-------------------+--------------------------------------+-------------------+--------------------------------------+------------------------------------------+----------------------------------------------+
| XPLOR Converter   | X-PLOR trajectory files (PDB and DCD)| .pdb, .dcd        | HDF format file containing trajectory| Converts X-PLOR trajectory to HDF format.| Dedicated to X-PLOR format conversions,      |
|                   |                                      |                   | data                                 | Dedicated to X-PLOR format conversions,  | ensuring accurate trajectory                 |
|                   |                                      |                   |                                      | ensuring accurate trajectory             | representation.                              |
|                   |                                      |                   |                                      | representation.                          |                                              |
+-------------------+--------------------------------------+-------------------+--------------------------------------+------------------------------------------+----------------------------------------------+
