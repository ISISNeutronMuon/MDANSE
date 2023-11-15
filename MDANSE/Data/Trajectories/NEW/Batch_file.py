import os
import glob
import threading
import json

def run_single_job(job_parameters):
    """
    Run a single MDANSE job with the given parameters.

    Parameters:
    job_parameters (dict): The parameters for the MDANSE job.
    """
    print(f"Running job with parameters: {job_parameters}")

def load_parameters(filename):
    """
    Load and manipulate job parameters from a JSON file.

    Parameters:
    filename (str): The path to the JSON file containing job parameters.

    Returns:
    dict: The manipulated job parameters.
    """
    with open(filename, 'r') as file:
        job_parameters = json.load(file)

    job_parameters['parameter_name'] = new_value  # Manipulate parameters here if needed

    return job_parameters

job_directory = 'job_parameters/'

job_files = glob.glob(os.path.join(job_directory, '*.json'))

if not job_files:
    print(f"No JSON files found in the directory: {job_directory}")
else:
    print(f"Found the following JSON files for batch job execution:")
    for job_file in job_files:
        print(job_file)

    threads = []

    for job_file in job_files:
        job_parameters = load_parameters(job_file)
        thread = threading.Thread(target=run_single_job, args=(job_parameters,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print("All jobs completed.")