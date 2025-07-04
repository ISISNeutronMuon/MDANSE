from pathlib import Path

from MDANSE.Framework.Converters.ASE import ASE
from MDANSE.Framework.Converters.CASTEP import CASTEP

from MDANSE.Framework.Parsers.FortranUnformat import binary_file_reader


X = CASTEP()

X.fold = False
X.trajectory_file = "~/MDANSE/MDANSE/Tests/UnitTests/Data/PBAnew.md"
X.output_files.path = "./doom_file.mdt"
X.time_unit = "ps"
X.time_step = 10.

X.run()

Y = ASE()

X.fold = False
X.trajectory_file = "~/MDANSE/MDANSE/Tests/UnitTests/Data/Cu_5steps_ASEformat.traj"
X.output_files.path = "./final_doom_file.mdt"
X.time_unit = "ps"
X.time_step = 10.

X.run()
