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
    def __init__(self, job, parameters=None, job_id='job'):
        """
        Builds test for a given job
        :Parameters:
        # job
        # parameters (dict): optional. If not None, the parameters which the job file will be built with.
        # job_id (str): optional. The ID of the job being tested. Used to recognise jobs that require special treatment.
        """
        # Save job
        self.job = job
        self.job.get_default_parameters()

        # Check if reference data is present
        self.reference_data_path = os.path.join(os.path.pardir, os.path.pardir, os.path.pardir, "Data",
                                                "Jobs_reference_data", job._type)
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

        self.__generate_test_file(parameters, job_id)

    @staticmethod
    def __create_dependencies():
        """
        Gather the dependecies that the test file will require.

        :Parameters:
        # array_of_python_dependancies_string (array of string) Example:[numpy, "os", "sys"]
        # array_of_mdanse_dependancies_string (array of string) Example:["from foo import bar", "import spam"]

        :return: list of external modules and MDANSE modules required for the test to run
        :rtype: (list, list)-tuple
        """
        array_of_python_dependencies_string = ['unittest', 'numpy', 'os']
        array_of_mdanse_dependencies_string = ['from MDANSE import REGISTRY']

        # Write dependencies
        # Add unittest, shutils and os if needed
        if not "unittest" in array_of_python_dependencies_string:
            array_of_python_dependencies_string.append("unittest")
        if not "os" in array_of_python_dependencies_string:
            array_of_python_dependencies_string.append("os")
        if not "shutil" in array_of_python_dependencies_string:
            array_of_python_dependencies_string.append("shutil")
        if not "time" in array_of_python_dependencies_string:
            array_of_python_dependencies_string.append("time")

        # Add NetCDF
        array_of_mdanse_dependencies_string.append('from Scientific.IO.NetCDF import NetCDFFile')
        array_of_mdanse_dependencies_string.append('import Comparator')

        # Sort arrays to write imports in the alphabetical order
        array_of_python_dependencies_string.sort()
        array_of_mdanse_dependencies_string.sort()

        return array_of_mdanse_dependencies_string, array_of_python_dependencies_string

    def __create_compare_function(self):
        """
        Creates a string with python code of a function that will compare the file generated in the test to
        a reference file.

        :return: String of python code of the compare function.
        :rtype: str
        """
        compare = 'def compare(file1, file2):\n' \
                  '    ret = True\n'

        if self.job._type in ['dftb', 'forcite']:
            compare = ''.join([compare, '    ignored_vars = ["temperature", "kinetic_energy", "velocities"]\n\n'])
        else:
            compare = ''.join([compare, '    ignored_vars = ["temperature", "kinetic_energy"]\n\n'])

        compare = ''.join([compare,
                           '    f = NetCDFFile(file1,"r")\n'
                           '    try:\n'
                           '        res1 = {}\n'
                           '        for k, v in f.variables.items():\n'
                           '            if k not in ignored_vars:\n'
                           '                res1[k] = v.getValue()\n'
                           '    finally:\n'
                           '        f.close()\n\n'
                           '    f = NetCDFFile(file2,"r")\n'
                           '    try:\n'
                           '        res2 = {}\n'
                           '        for k,v in f.variables.items():\n'
                           '            if k not in ignored_vars:\n'
                           '                res2[k] = v.getValue()\n'
                           '    finally:\n'
                           '        f.close()\n\n'
                           '    return Comparator.Comparator().compare(res1, res2)\n\n\n'
                           ])

        return compare

    def __create_test(self, parameters, test_name):
        """
        Creates a single test in a test case.

        :Parameters:
        # parameters (dict): optional. If not None, the parameters which the job file will be built with.
        # test_name (str): A name for the test.
        """
        # Name each test after the file it is testing
        test_string = '    def test_{}(self):\n'.format(test_name)

        # Writes the line that will initialize the |parameters| dictionary and create the job
        if parameters is None:
            parameters = self.job.get_default_parameters()
        test_string += '        parameters = {}\n'
        for k, v in sorted(parameters.items()):
            temp = 'parameters[%r] = %r\n' % (k, v)
            test_string = test_string + '        ' + temp.replace('\\\\', '/')
        test_string += '        job = REGISTRY[%r][%r]()\n' % ('job', self.job._type)
        test_string += '        output_path = parameters["output_files"][0]\n'
        test_string += '        reference_data_path = "' + self.reference_data_path.replace('\\', '/') + '"\n'

        # Launch the job in monoprocessor mode and copy output file
        test_string += '        print "Launching job in monoprocessor mode"\n' \
                       '        parameters["running_mode"] = ("monoprocessor",1)\n' \
                       '        job.run(parameters, status=False)\n' \
                       '        shutil.copy(output_path + ".nc", reference_data_path + "_mono" + ".nc")\n' \
                       '        print "Monoprocessor execution completed"\n\n'

        # Launch the job in multiprocessor mode if avalaible
        if self.multiprocessor:
            test_string += '        print "Launching job in multiprocessor mode"\n' \
                           '        parameters["running_mode"] = ("multiprocessor",2)\n' \
                           '        job.run(parameters,False)\n' \
                           '        shutil.copy(output_path + ".nc", reference_data_path + "_multi" + ".nc")\n' \
                           '        print "Multiprocessor execution completed"\n\n'

        # Compare reference data with monoprocessor if reference data exists
        if self.reference_data_file:
            test_string += '        print "Comparing monoprocessor output with reference output"\n' \
                           '        self.assertTrue(compare("' + self.reference_data_file.replace('\\', '/') + \
                           '", reference_data_path + "_mono" + ".nc"))\n\n'
        # Compare reference data with multiprocessor if reference data exists
        if self.reference_data_file and self.multiprocessor:
            test_string += '        print "Comparing multiprocessor output with reference output"\n' \
                           '        self.assertTrue(compare("' + self.reference_data_file.replace('\\', '/') + \
                           '", reference_data_path + "_multi" + ".nc"))\n\n'
        # If no reference data but multiprocessor, compare mono and multiprocessor
        elif self.multiprocessor:
            test_string += '        print "Comparing monoprocessor output with multiprocessor output"\n' \
                           '        self.assertTrue(compare(reference_data_path + "_mono" + ".nc", ' \
                           'reference_data_path + "_multi" + ".nc"))\n\n'
        test_string += '        try:\n' \
                       '            os.remove(reference_data_path + "_mono" + ".nc")\n'
        if self.multiprocessor:
            test_string += '            os.remove(reference_data_path + "_multi" + ".nc")\n'
        test_string += '        except OSError:\n' \
                       '            pass\n\n'

        # If test is GMTF, restore old_universe_name
        if self.job._type == "gmft":
            test_string += '        job.configuration["trajectory"]["instance"].universe.__class__.__name__ = ' \
                           'job.old_universe_name\n'

        return test_string

    def __create_test_suite(self):
        """
        Creates the string of python code defining a suite function that creates a test suite.
        :return: Python code defining suite function.
        :rtype: str
        """
        test_string = '\ndef suite():\n' \
                      '    loader = unittest.TestLoader()\n' \
                      '    s = unittest.TestSuite()\n' \
                      '    s.addTest(loader.loadTestsFromTestCase(Test%s))\n' % self.job._type.upper()
        test_string += '    return s'
        return test_string

    def __generate_test_file(self, parameters, job_id):
        """
        Generates a .py file and writes into it all the code defined in the previous methods.

        :param parameters: The parameters which the job file will be built with.
        :type parameters: dict or None

        :param job_id: The id of the job class for which the tests are being generated.
        :type job_id: str
        """
        f = open(self.job_file_name, 'w')

        # The first line contains the call to the python executable. This is necessary for the file to
        # be autostartable.
        f.write('#!%s\n\n' % sys.executable)

        # Write dependecies
        array_of_mdanse_dependancies_string, array_of_python_dependancies_string = self.__create_dependencies()
        for dependancy_string in array_of_python_dependancies_string:
            f.write("import " + dependancy_string + "\n")
        f.write("\n")
        for dependancy_string in array_of_mdanse_dependancies_string:
            f.write(dependancy_string + "\n")
        f.write("\n")

        # Write the compare function, a test case, and the suite function
        file_body = self.__create_compare_function() + 'class Test%s(unittest.TestCase):\n\n' % self.job._type.upper() \
                    + self.__create_test(parameters, test_name=job_id)
        # If the job is CASTEP converter, create an additional test that uses a different input file.
        if job_id == 'castep':
            self.job.settings['castep_file'] = ('input_file', {'default': os.path.join('..', '..', '..', 'Data',
                                                                                       'Trajectories', 'CASTEP',
                                                                                       'PBAnew_short.md')})
            file_body += self.__create_test(parameters=None, test_name='short_header')
        f.write(file_body)
        f.write(self.__create_test_suite())

        # Write file ending
        f.write("\n\n")
        f.write("if __name__ == '__main__':\n")
        f.write('    unittest.main(verbosity=2)\n')
        f.close()
        os.chmod(self.job_file_name, stat.S_IRWXU)


if __name__ == '__main__':
    # Main script, automatically creates source files for testing jobs
    for job_id, job in REGISTRY['job'].items():
        # Skip the mcstas test because mcstas executable is not available on all platform
        if job_id == 'mvi' or job_id == 'pdf':
            pass
        else:
            job_file_generator = JobFileGenerator(job, job_id=job_id)
