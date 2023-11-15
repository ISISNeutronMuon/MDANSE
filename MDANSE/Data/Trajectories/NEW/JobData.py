import sys
import json
from pydantic import BaseModel
from pathlib import Path

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
        for key, value in self.parameters.items():
            if isinstance(value, str) and Path(value).is_file():
                self.parameters[key] = str(Path(value).relative_to(Path.cwd()))

        with open(filename, 'w') as f:
            json.dump(self.dict(), f, indent=4)

    @staticmethod
    def load_from_file(parameters_file):
        try:
            with open(parameters_file, 'r') as f:
                data = json.load(f)
                return JobData(**data)
        except FileNotFoundError:
            print(f"Error: File '{parameters_file}' not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON file '{parameters_file}'.")
            sys.exit(1)

    @classmethod
    def main(cls):
        if len(sys.argv) < 2:
            print("Usage: python script.py [parameters_file.json]")
            sys.exit(1)

        parameters_file = sys.argv[1]
        job_data = cls.load_from_file(parameters_file)
        job_data.parameters.setdefault('mdanse_category', 'default_category')
        job_data.parameters.setdefault('mdanse_type', 'default_type')
        job_data.save_to_file('job_data.json')

if __name__ == "__main__":
    JobData.main()
