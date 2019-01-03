# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Tests/FunctionalTests/Jobs/BuildJobTests.py
# @brief     Implements module/class/test BuildJobTests
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os
import stat
import sys

from MDANSE import REGISTRY

class JobFileGenerator():
    def __init__(self, job, parameters=None):
        """
        Builds test for a given job
        :Parameters:
        # job
        # parameters (dict): optional. If not None, the parameters which the job file will be built with.
        """
        # Save job
        self.job = job
        self.job.get_default_parameters()
        # Check if reference data is present
        self.reference_data_path = os.path.join(os.path.pardir, os.path.pardir, os.path.pardir, "Data", "Jobs_reference_data", job._type)
        self.reference_data_file = self.reference_data_path + "_reference" + ".nc"
        if not os.path.isfile(self.reference_data_file):
            print "/!\ Reference data file is not present for job " + str(job)
            self.reference_data_file = None
        # Check if job can be launched on multiprocessor
        if job.settings.has_key('running_mode'):
            self.multiprocessor = True
        else:
            print "/!\ Job " + str(job) + " cannot be launched on multiprocessor"
            self.multiprocessor = False
        # Create the job file
        self.job_file_name = "Test_%s.py" % job._type
        self.__build_job_file(parameters)

    def __build_job_file(self, parameters):
        """
        Builds job file for a given job
        :Parameters:
        # parameters (dict): optional. If not None, the parameters which the job file will be built with.
        """
        array_of_python_dependancies_string = ['unittest', 'numpy', 'os']
        array_of_mdanse_dependancies_string = ['from MDANSE import REGISTRY']
        test_string = ''
        test_string = test_string +     'class Test%s(unittest.TestCase):\n\n' % self.job._type.upper()
        test_string = test_string +     '    def test(self):\n'
        # Writes the line that will initialize the |parameters| dictionary and create the job
        if parameters is None:
            parameters = self.job.get_default_parameters()
        test_string = test_string +     '        parameters = {}\n'
        for k, v in sorted(parameters.items()):
            temp = 'parameters[%r] = %r\n' % (k, v)
            test_string = test_string + '        ' + temp.replace('\\\\', '/')
        test_string = test_string +     '        job = REGISTRY[%r][%r]()\n' % ('job',self.job._type)
        test_string = test_string +     '        output_path = parameters["output_files"][0]\n'
        test_string = test_string +     '        reference_data_path = "' + self.reference_data_path.replace('\\', '/') + '"\n'
        # Launch the job in monoprocessor mode and copy output file
        test_string = test_string +     '        print "Launching job in monoprocessor mode"\n'
        test_string = test_string +     '        parameters["running_mode"] = ("monoprocessor",1)\n'
        test_string = test_string +     '        job.run(parameters, status=False)\n'
        test_string = test_string +     '        shutil.copy(output_path + ".nc", reference_data_path + "_mono" + ".nc")\n'
        test_string = test_string +     '        print "Monoprocessor execution completed"\n\n'
        # Launch the job in multiprocessor mode if avalaible
        if self.multiprocessor:
            test_string = test_string + '        print "Launching job in multiprocessor mode"\n'
            test_string = test_string + '        parameters["running_mode"] = ("multiprocessor",2)\n'
            test_string = test_string + '        job.run(parameters,False)\n'
            test_string = test_string + '        shutil.copy(output_path + ".nc", reference_data_path + "_multi" + ".nc")\n'
            test_string = test_string + '        print "Multiprocessor execution completed"\n\n'
        # Compare reference data with monoprocessor if reference data exists
        if self.reference_data_file:
            test_string = test_string + '        print "Comparing monoprocessor output with reference output"\n'
            test_string = test_string + '        self.assertTrue(compare("' +  self.reference_data_file.replace('\\', '/') + '", reference_data_path + "_mono" + ".nc"))\n\n'
        # Compare reference data with multiprocessor if reference data exists
        if self.reference_data_file and self.multiprocessor:
            test_string = test_string + '        print "Comparing multiprocessor output with reference output"\n'
            test_string = test_string + '        self.assertTrue(compare("' +  self.reference_data_file.replace('\\', '/') + '", reference_data_path + "_multi" + ".nc"))\n\n'
        # If no reference data but multiprocessor, compare mono and multiprocessor
        elif self.multiprocessor:
            test_string = test_string + '        print "Comparing monoprocessor output with multiprocessor output"\n'
            test_string = test_string + '        self.assertTrue(compare(reference_data_path + "_mono" + ".nc", reference_data_path + "_multi" + ".nc"))\n\n'
        test_string = test_string +     '        try:\n'
        test_string = test_string +     '            os.remove(reference_data_path + "_mono" + ".nc")\n'
        if self.multiprocessor:
            test_string = test_string + '            os.remove(reference_data_path + "_multi" + ".nc")\n'
        test_string = test_string +     '        except:\n'
        test_string = test_string +     '            pass\n'
        # If test is GMTF, restore old_universe_name
        if self.job._type == "gmft":
            test_string = test_string + '        job.configuration["trajectory"]["instance"].universe.__class__.__name__ = job.old_universe_name\n'
        # Finally write the suite method that will be called by test script
        test_string = test_string +     '\n\ndef suite():\n'
        test_string = test_string +     '    loader = unittest.TestLoader()\n'
        test_string = test_string +     '    s = unittest.TestSuite()\n'
        test_string = test_string +     '    s.addTest(loader.loadTestsFromTestCase(Test%s))\n' % self.job._type.upper()
        test_string = test_string +     '    return s'
        
        self.__generate_test_file(test_string, array_of_python_dependancies_string, array_of_mdanse_dependancies_string)

    def __generate_test_file(self, test_string, array_of_python_dependancies_string, array_of_mdanse_dependancies_string):
        """
        Produce a file for the given informations
        :Parameters:
        # test_string (string): the content
        # array_of_python_dependancies_string (array of string) Example:[numpy, "os", "sys"]
        # array_of_mdanse_dependancies_string (array of string) Example:["from foo import bar", "import spam"]
        """
        f = open(self.job_file_name, 'w')
        
        # The first line contains the call to the python executable. This is necessary for the file to
        # be autostartable.
        f.write('#!%s\n\n' % sys.executable)
        
        # Write dependancies
        # Add unittest, shutils and os if needed
        if not "unittest" in array_of_python_dependancies_string:
            array_of_python_dependancies_string.append("unittest")
        if not "os" in array_of_python_dependancies_string:
            array_of_python_dependancies_string.append("os")
        if not "shutil" in array_of_python_dependancies_string:
            array_of_python_dependancies_string.append("shutil")
        if not "time" in array_of_python_dependancies_string:
            array_of_python_dependancies_string.append("time")
        # Add NetCDF
        array_of_mdanse_dependancies_string.append('from Scientific.IO.NetCDF import NetCDFFile')
        array_of_mdanse_dependancies_string.append('import Comparator')
    
        # Sort arrays to write imports in the alphabetical order
        array_of_python_dependancies_string.sort()
        array_of_mdanse_dependancies_string.sort()
        # Write in file
        for dependancy_string in array_of_python_dependancies_string:
            f.write("import " + dependancy_string + "\n")
        f.write("\n")
        for dependancy_string in array_of_mdanse_dependancies_string:
            f.write(dependancy_string + "\n")
        f.write("\n")
        
        # Create the compare function
        test_string2 =                'def compare(file1, file2):\n'
        test_string2 = test_string2 + '    ret = True\n'
        test_string2 = test_string2 + '    f = NetCDFFile(file1,"r")\n'
        test_string2 = test_string2 + '    res1 = {}\n'
        test_string2 = test_string2 + '    for k,v in f.variables.items():\n'
        test_string2 = test_string2 + '        res1[k] = v.getValue()\n'
        test_string2 = test_string2 + '    f.close()\n'
        test_string2 = test_string2 + '    f = NetCDFFile(file2,"r")\n'
        test_string2 = test_string2 + '    res2 = {}\n'
        test_string2 = test_string2 + '    for k,v in f.variables.items():\n'
        test_string2 = test_string2 + '        res2[k] = v.getValue()\n'
        test_string2 = test_string2 + '    f.close()\n'
        test_string2 = test_string2 + '    return Comparator.Comparator().compare(res1, res2)\n\n'
        
        # Write test string
        f.write(test_string2 + test_string)
        f.write("\n\n")
        
        # Write file ending
        f.write("if __name__ == '__main__':\n")
        f.write('    unittest.main(verbosity=2)\n')
        f.close()
        os.chmod(self.job_file_name,stat.S_IRWXU)
        
if __name__ == '__main__':
    # Main script, automatically creates source files for testing jobs
    for job_id,job in REGISTRY['job'].items():
        # Skip the mcstas test because mcstas executable is not available on all platform
        if job_id=='mvi':
            pass
        else:
            job_file_generator = JobFileGenerator(job)

