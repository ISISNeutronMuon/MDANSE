import os

if __name__ == "__main__":

    target_dirs = ["Extensions","Src","Tests"]

    header = """# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      %s
# @brief     Implements module/class/test %s
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

"""

    mdanse_root = os.path.dirname(os.path.abspath(__file__))

    for target_dir in target_dirs:
        for subdir,_,filenames in os.walk(os.path.join(mdanse_root,target_dir)):
            for filename in filenames:
                basename,file_ext = os.path.splitext(filename)
                if file_ext not in [".py",".pyx"]:
                    continue

                full_path = os.path.join(subdir,filename)

                with open(full_path,"r") as fin:
                    contents = header % (os.path.relpath(full_path,mdanse_root),basename) + fin.read()

                with open(full_path,"w") as fout:
                    fout.write(contents)
    


