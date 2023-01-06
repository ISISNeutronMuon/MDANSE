"""
A tool for batch re-linking of MDANSE libraries.
So far it was necessary to run in twice:
once in the Frameworks directory of the bundle
with get_file_list('libvtk')
and again in Contents/Resources/lib/python2.7/site-packages/vtk
with get_file_list('.so')
"""

import os
import subprocess

def get_file_list(search_string):
    """
    Find all the file names in the working directory
    that contain the input 'search_string'.
    """
    output = subprocess.run([f"ls | grep {search_string}"], shell=True, capture_output=True)
    if len(output.stderr) > 1:
        print(search_string)
        raise Exception(str(output.stderr))
    return list(x.decode('ascii') for x in output.stdout.split(b'\n'))

def get_libraries(fname):
    """
    Get the names of all the libraries that are linked to the
    input file.
    """
    if len(fname) > 1:
        output = subprocess.run([f"otool -L {fname}"], shell=True, capture_output=True)
    else:
        return []
    if len(output.stderr) > 1:
        print(fname)
        raise Exception(str(output.stderr))
    result = []
    for x in output.stdout.split(b'\n'):
        temp = x.decode('ascii')
        if ':' in temp:
            continue
        try:
            result.append(temp.split()[0])
        except IndexError:
            continue
    return result

def replace_libline(fname, line, to_remove=None, to_insert='@executable_path/../Frameworks/'):
    """
    Prepare the command that will re-link a single library in the specified file.
    """
    _, libname = os.path.split(line)
    if to_remove is None:
        result = to_insert + libname
    else:
        result = line.replace(to_remove, to_insert)
    return f"install_name_tool -change {line} {result} {fname}"

if __name__ == '__main__':
    try:
        os.chdir(r'/Users/runner/work/MDANSE/MDANSE/temp/dist/MDANSE.app/Contents/Resources/lib/python2.7/site-packages/vtkmodules')
        flist = get_file_list('.so')  # in site-packages vtk
        os.chdir(r'/Users/runner/work/MDANSE/MDANSE/temp/dist/MDANSE.app/Contents/Framework')
        flist.extend(get_file_list('libvtk'))  # in Framework

        for fname in flist:
            liblist = get_libraries(fname)
            for libname in liblist:
                if 'vtk' in libname:
                    subprocess.run(replace_libline(fname, libname), shell = True)
                elif 'python' in libname:
                    subprocess.run(replace_libline(fname, libname), shell = True)
    except:
        pass
    
