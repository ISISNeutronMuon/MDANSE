import sys
import json
from pydantic import BaseModel


class JobData(BaseModel):
    """
    Stores all the information needed to run an MDANSE job.
    """
    mdanse_category: str
    mdanse_type: str
    parameters: dict

    def save_to_file(self, filename):
        """
        Save the JobData instance to a file in JSON format.
        Parameters:
        filename (str): The name of the file to save the data to.
        """
        with open(filename, 'w') as f:
            json.dump(self.dict(), f, indent=4)

    def main(self):
        """
        Handles the processing of command-line arguments and JSON data for the MDANSE job.
        It parses command-line arguments and loads parameters from JSON file.
        Gets 'mdanse_category' and 'mdanse_type' retrieves them from the JSON file.
        In case of any issues with file access or JSON decoding, prints error message.
        Creates an instance of the JobData class with the collected values and
        saves it to 'job_data.json'.
        """
        if len(sys.argv) < 2:
            print("Usage: python script.py [parameters_file.json]")
            sys.exit(1)

        parameters_file = sys.argv[1]

        try:
            with open(parameters_file, 'r') as f:
                data = json.load(f)
                job_data = JobData(**data)
        except FileNotFoundError:
            print(f"Error: File '{parameters_file}' not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON file '{parameters_file}'.")
            sys.exit(1)

        if 'mdanse_category' not in job_data.parameters:
            print("Warning: 'mdanse_category' not found in JSON file. Using default value.")
            job_data.parameters['mdanse_category'] = "default_category"

        if 'mdanse_type' not in job_data.parameters:
            print("Warning: 'mdanse_type' not found in JSON file. Using default value.")
            job_data.parameters['mdanse_type'] = "default_type"

        job_data.save_to_file('job_data.json')


if __name__ == "__main__":
    job_data_instance = JobData()
    job_data_instance.main()