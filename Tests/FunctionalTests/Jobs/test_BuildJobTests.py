import unittest
import os
from BuildJobTests import JobFileGenerator

class JobForTest():
    settings = {}
    configuration = {"output_files":{"files":["./File.nc"]}}
    _type = 'Test'
    
    def set_multi_processor(self):
        self.settings = {'running_mode':True}
    
    def set_mono_processor(self):
        self.settings = {}
        
    def get_default_parameters(self):
        return {}

class TestBuildJobTests(unittest.TestCase):
    def test(self):
        temp = os.path.join(os.path.split(__file__)[0], "Test_Test.py")
        self.job = JobForTest()
        self.object = JobFileGenerator(self.job)
        self.assertTrue(os.path.isfile(temp))
        os.remove(temp)
        self.job.set_multi_processor()
        self.object = JobFileGenerator(self.job)
        self.assertTrue(os.path.isfile(temp))
        os.remove(temp)
        
if __name__ == '__main__':
    unittest.main(verbosity=2)