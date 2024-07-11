Trajectory Converters Information
==================================

All converters output the trajectories as .MDT files, which are binary HDF5 files.

+-------------------+--------------------------------------+-------------------+------------------------------------------+
| Type              | File Format                          | Default Extension | Description                              |
+===================+======================================+===================+==========================================+
| ASE Converter     | Various (.extxyz, .traj, .log, ...)  | N/A               | Tries to read the trajectory using       |
|                   |                                      |                   | ASE and the ase.io module. Useful for MD |
|                   |                                      |                   | software without a dedicated converter.  |
+-------------------+--------------------------------------+-------------------+------------------------------------------+
| CASTEP Converter  | CASTEP trajectory format             | .md               | Converts CASTEP trajectory files to HDF  |
|                   |                                      |                   | format, including velocities and forces. |
+-------------------+--------------------------------------+-------------------+------------------------------------------+
| CHARMM Converter  | CHARMM trajectory format             | .pdb (PDB file),  | Converts CHARMM trajectory files to HDF  |
|                   |                                      | other             | format. Integration with PDB file        |
|                   |                                      |                   | formats for enhanced CHARMM trajectory   |
|                   |                                      |                   | processing.                              |
+-------------------+--------------------------------------+-------------------+------------------------------------------+
| CP2K Converter    | CP2K trajectory format               | .xyz (position),  | Converts CP2K trajectory files to HDF    |
|                   |                                      | .xyz (velocity),  | format, including positions, velocities, |
|                   |                                      | .cell (cell)      | and cell dimensions. Velocity            |
|                   |                                      |                   | approximation from positions available;  |
|                   |                                      |                   | optimal for incomplete datasets.         |
+-------------------+--------------------------------------+-------------------+------------------------------------------+
| DFTB Converter    | DFTB trajectory format               | .xtd (XTD file),  | Converts DFTB trajectory files to HDF    |
|                   |                                      | .trj (TRJ file)   | format. Requires system's XTD file for   |
|                   |                                      |                   | accurate trajectory conversion of DFTB   |
|                   |                                      |                   | files.                                   |
+-------------------+--------------------------------------+-------------------+------------------------------------------+
| Discover Converter| Discover module trajectory files     |  .xtd, .his       | Converts Discover module trajectory to   |
|                   |                                      |                   | HDF format. Enhanced support for         |
|                   |                                      |                   | variable header lengths in CASTEP files. |
+-------------------+--------------------------------------+-------------------+------------------------------------------+
| DL_POLY Converter | DL POLY trajectory files             | .field, .history  | Converts DL POLY trajectory to HDF       |
|                   |                                      |                   | format. Converts both velocities and     |
|                   |                                      |                   | forces. Version-selective conversion     |
|                   |                                      |                   | with advanced support for atom aliasing  |
|                   |                                      |                   | in DL POLY files.                        |
+-------------------+--------------------------------------+-------------------+------------------------------------------+
| DMol Converter    | DMol module trajectory files         | .xtd, .his        | Converts DMol module trajectory to HDF   |
|                   |                                      |                   | format. Does not convert velocities.     |
|                   |                                      |                   | Optimized for DMol files from Materials  |
|                   |                                      |                   | Studio, ensuring high fidelity data      |
|                   |                                      |                   | transfer.                                |
+-------------------+--------------------------------------+-------------------+------------------------------------------+
| Forcite Converter | Forcite module trajectory files      | .xtd, .trj        | Converts Forcite module trajectory to    |
|                   |                                      |                   | HDF format. Accommodates both XTD and    |
|                   |                                      |                   | TRJ files from the Forcite module for    |
|                   |                                      |                   | conversions.                             |
+-------------------+--------------------------------------+-------------------+------------------------------------------+
| Gromacs Converter | Gromacs trajectory files             | .pdb, .xtc, .trr  | Converts Gromacs trajectory to HDF       |
|                   |                                      |                   | format. Requires a PDB file and XTC/TRR  |
|                   |                                      |                   | trajectory file. Focused on seamless     |
|                   |                                      |                   | conversion of Gromacs trajectories,      |
|                   |                                      |                   | including all essential file types.      |
+-------------------+--------------------------------------+-------------------+------------------------------------------+
| LAMMPS Converter  | LAMMPS trajectory files              | .config, .        | Converts LAMMPS trajectory to HDF        |
|                   |                                      | trajectory        | format. Requires LAMMPS configuration and|
|                   |                                      |                   | trajectory files. Advanced features      |
|                   |                                      |                   | include mass tolerance and intelligent   |
|                   |                                      |                   | mass association for complex simulations.|
+-------------------+--------------------------------------+-------------------+------------------------------------------+
| NAMD Converter    | NAMD trajectory files                | .pdb, .dcd        | Converts NAMD trajectory to HDF format.  |
|                   |                                      |                   | Requires a PDB file and DCD trajectory   |
|                   |                                      |                   | file. Tailored for NAMD trajectories,    |
|                   |                                      |                   | ensuring accurate data representation in |
|                   |                                      |                   | conversions.                             |
+-------------------+--------------------------------------+-------------------+------------------------------------------+
| PDB Converter     | PDB files                            | .pdb              | Converts standalone PDB files to HDF     |
|                   |                                      |                   | format. Specialized in PDB file          |
|                   |                                      |                   | transformations, excluding velocity data |
|                   |                                      |                   | for clarity.                             |
+-------------------+--------------------------------------+-------------------+------------------------------------------+
| VASP Converter    | VASP trajectory files (XDATCAR)      | .xdatcar          | Converts VASP trajectory to HDF format.  |
|                   |                                      |                   | Exclusively handles VASP trajectories,   |
|                   |                                      |                   | focusing on precision and data integrity.|
+-------------------+--------------------------------------+-------------------+------------------------------------------+
| XPLOR Converter   | X-PLOR trajectory files (PDB and DCD)| .pdb, .dcd        | Converts X-PLOR trajectory to HDF format.|
|                   |                                      |                   | Dedicated to X-PLOR format conversions,  |
|                   |                                      |                   | ensuring accurate trajectory             |
|                   |                                      |                   | representation.                          |
+-------------------+--------------------------------------+-------------------+------------------------------------------+
