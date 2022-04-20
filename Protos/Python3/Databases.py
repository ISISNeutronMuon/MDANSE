import yaml

with open('atoms.yml','r') as fin:
    ATOMS = yaml.safe_load(fin)

with open('molecules.yml','r') as fin:
    MOLECULES = yaml.safe_load(fin)

with open('residues.yml','r') as fin:
    RESIDUES = yaml.safe_load(fin)

with open('nucleotides.yml','r') as fin:
    NUCLEOTIDES = yaml.safe_load(fin)
