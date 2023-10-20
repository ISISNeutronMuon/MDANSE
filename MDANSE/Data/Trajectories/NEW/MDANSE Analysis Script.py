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
from MDANSE import REGISTRY
from MDANSE.Framework.QVectors import IQvectors
from MDANSE.Framework.Selectors.ISelector import ISelector

class MDANSEAnalysisRunner:
    def __init__(self):
        self.selector = None
        self.qvectors = None
    def set_selector(self, selector):
        if not isinstance(selector, ISelector):
            raise ValueError("Selector must be an instance of ISelector.")
        self.selector = selector
    def set_qvectors(self, qvectors):
        if not isinstance(qvectors, IQvectors):
            raise ValueError("QVectors must be an instance of IQvectors.")
        self.qvectors = qvectors
    def run_analysis(self):
        if self.selector is None or self.qvectors is None:
            raise ValueError("Both selector and qvectors must be set before running analysis.")
        # Example:
        # result = mdanse_analysis_function(self.selector, self.qvectors)
        # return result

class ExampleSelector(ISelector):
    def __init__(self, universe):
        super().__init__(universe)
        self.selected_atoms = []  
    def select(self):
        print("Selecting atoms from the trajectory.")
        selected_atoms = self.universe.atomList()[:10]  # Selecting first 10 atoms as an example
        return selected_atoms
    def get_selected_atoms(self):
        print("Retrieving selected atoms.")
        if not self.selected_atoms:
            print("No atoms have been selected yet.")
            return None
        else:
            return self.selected_atoms
    def apply_filter(self, filter_criteria):
        print(f"Applying filter based on criteria: {filter_criteria}.")
        filtered_atoms = []
        for atom in self.selected_atoms:
            # Example filtering based on criteria
            if atom['property'] == filter_criteria:
                filtered_atoms.append(atom)
        return filtered_atoms


class ExampleQVectors(IQvectors):
    def __init__(self, universe, status=None):
        super().__init__(universe, status)
    def _generate(self):
        generated_qvectors = []
        for frame in self.universe:
            qvector = calculate_qvector(frame)  
            generated_qvectors.append(qvector)
        return generated_qvectors
    def apply_cutoff(self, cutoff_value):
        filtered_qvectors = [qv for qv in qvectors_data if qv < cutoff_value]  
        return filtered_qvectors

def parse_args():
    parser = argparse.ArgumentParser(description='''This is mdanse_job: a shortcut for running MDANSE job. It opens a GUI dialog 
    from where an analysis or a trajectory converter will be setup and eventually run.''')
    parser.add_argument('job', nargs=1, help='Code for the job to be run. E.g. msd for Mean Square Displacement. For a complete list of available jobs please run "mdanse -r job"')
    parser.add_argument('trajectory', nargs='*', help='Trajectory file. This is needed only for analysis job. Not required for trajectory conversion jobs.')
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
    pdb_file = None  
    pdb_reader = None  # Replace with the appropriate reader

    selector = ExampleSelector(pdb_reader)  
    qvectors = ExampleQVectors(pdb_reader.universe)  
    analysis_runner.set_selector(selector)
    analysis_runner.set_qvectors(qvectors)

    try:
        analysis_runner.run_analysis()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)