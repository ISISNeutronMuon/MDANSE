import os
import h5py
import unittest
from unittest.mock import patch
from MDANSE import REGISTRY
from MDANSE.IO.IOUtils import _IFileVariable
from MDANSE.Framework.Formats.IFormat import IFormat
from MDANSE.Framework.Formats.HDFFormat import HDFFormat


class TestHDFFormat(unittest.TestCase):
    def setUp(self):
        self.data = {}


    @patch('h5py.File')
    def test_write(self, mock_file):
        filename = 'test.h5'
        header = "Test Header"
        HDFFormat.write(filename, self.data, header)
        mock_file.assert_called_with('trajectory_test.hdf', 'w')
        mock_file_instance = mock_file.return_value
        self.assertTrue(mock_file_instance.create_dataset.called)
        self.assertTrue(mock_file_instance.close.called)


    def test_find_numeric_variables(self):
        var_dict = {}
        group = h5py.File('test_file.hdf5', 'w')
        dset = group.create_dataset('numeric_data', data=[1, 2, 3, 4, 5], dtype='int')
        subgroup = group.create_group('subgroup')
        subgroup.create_dataset('string_data', data='hello', dtype='S5')

        find_numeric_variables(var_dict, group)

        self.assertEqual(len(var_dict), 1)  # Only one numeric variable in the test case
        self.assertIn('numeric_data', var_dict)
        self.assertIsInstance(var_dict['numeric_data'], tuple)
        
    unittest.main()