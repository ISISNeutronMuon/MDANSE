"""
MDANSE Analysis Script
This script facilitates the execution of MDANSE analysis tasks by setting up the necessary components, including the selector and QVectors, and passing these objects directly to the analysis runner. It is designed to enable standalone runs, making it easy to execute the analysis from a script, with the goal of ensuring the transferability of jobs between different computers and clusters.
Usage:
    python mdanse_analysis_script.py [job] [trajectory]
    - job: Code for the MDANSE job to be run (e.g., 'msd' for Mean Square Displacement).
    - trajectory: Trajectory file path (required for analysis jobs, not needed for trajectory conversion jobs).
Example:
    python mdanse_analysis_script.py msd path/to/trajectory.dcd
"""
import sys
import argparse
import h5py
from MDANSE import REGISTRY
from MDANSE.Framework.QVectors import IQvectors
from MDANSE.Framework.Selectors.ISelector import ISelector
import json
from pathlib import Path

class JobData:
    def __init__(self, job_file):
        with open(job_file, 'r') as f:
            data = json.load(f)
            self.mdanse_type = data['mdanse_type']
            self.trajectory = str(Path(data['trajectory']).resolve())

def read_trajectory(file_path):
    with h5py.File(file_path, 'r') as file:
        trajectory_data = file['trajectory'][:]  # Modify to HDF5 structure
    return trajectory_data

class MDANSEAnalysisRunner:
    def __init__(self, job_data):
        self.job_data = job_data
        self.selector = None
        self.qvectors = None
        self.requires_qvectors = False

    def set_selector(self, selector):
        if not isinstance(selector, ISelector):
            raise ValueError("Selector must be an instance of ISelector.")
        self.selector = selector

    def set_qvectors(self, qvectors):
        if not isinstance(qvectors, IQvectors):
            raise ValueError("QVectors must be an instance of IQvectors.")
        self.qvectors = qvectors

    def run_analysis(self):
        trajectory_data = read_trajectory(self.job_data.trajectory)
        job_class = REGISTRY['job'][self.job_data.mdanse_type]
        
        job_requirements = get_job_requirements(job_class)  # Implement this function based on MDANSE framework

        if 'selector' in job_requirements:
            self.set_selector(GeneralSelector(trajectory_data))  # Implement GeneralSelector or use a specific selector
        if 'qvectors' in job_requirements:
            self.requires_qvectors = True
            self.set_qvectors(GeneralQVectors(trajectory_data))  # Implement GeneralQVectors or use a specific QVectors class

        if 'selector' in job_requirements and self.selector is None:
            raise ValueError("Selector component is required but not set.")
        if 'qvectors' in job_requirements and (self.requires_qvectors and self.qvectors is None):
            raise ValueError("QVectors component is required but not set.")

        job_instance = job_class(self.job_data.parameters)

        if self.selector:
            job_instance.set_selector(self.selector)
        if self.qvectors and self.requires_qvectors:
            job_instance.set_qvectors(self.qvectors)

        job_instance.run()

def parse_args():
    parser = argparse.ArgumentParser(description="MDANSE Analysis Script")
    parser.add_argument('job_file', help='Path to the JSON job file')
    args = parser.parse_args()
    return args



if __name__ == "__main__":
    args = parse_args()
    trajectory = args.trajectory
    job = args.job[0]
    if not REGISTRY['job'].get(job):
        print('Unknown job: %s' % job)
        sys.exit(1)
    for v in REGISTRY['job'][job].settings.values():
        if v[0] == 'trajectory' and not trajectory:
            print('A trajectory is needed')
            sys.exit(1)
    trajectory = trajectory[0] if trajectory else None

    # Adding MDANSEAnalysisRunner
    analysis_runner = MDANSEAnalysisRunner()
    try:
        analysis_runner.run_analysis()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)