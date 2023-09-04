import os
import yaml


def load_database(database_path):
    """Load in memory the database YAML file"""

    # Load the chemical elements database
    with open(database_path, "r") as fin:
        try:
            database = yaml.safe_load(fin)
        except yaml.YAMLError as exc:
            print(exc)

    return database


_homedir = os.path.expanduser("~")
CHEMICAL_ELEMENTS = load_database(
    os.path.join(_homedir, ".waterstay", "chemical_elements.yml")
)
STANDARD_RESIDUES = load_database(os.path.join(_homedir, ".waterstay", "residues.yml"))
