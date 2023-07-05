#!/bin/bash

pip uninstall -y MDANSE_GUI
python setup.py bdist_wheel
pip install dist/MDANSE_GUI-0.0.1-py3-none-any.whl
