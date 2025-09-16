
import numpy as np

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.MolecularDynamics.UnitCell import UnitCell


configurators = sorted(IConfigurator.indirect_subclasses())
converters = sorted(Converter.indirect_subclasses())
jobs = sorted(IJob.indirect_subclasses())
generators = sorted(set(IQVectors.indirect_subclasses()) - {"IQVectors", "LatticeQVectors"})

job_inputs = {}
converter_inputs = {}
qvector_inputs = {}
job_page = []
converter_page = []
input_page = []
qvector_page = []

def make_configurator_doc(conf: str, parent: str) -> str:
    result = ""
    try:
        temp = IConfigurator.create(conf, 'dummy')
    except TypeError:
        temp = IConfigurator.create(conf, 'dummy', parser=None)
    result += f"\n.. _configurator-{parent}-{conf}:\n\n"
    result += f"{conf}\n"
    result += "".join(len(conf)*['-'])+'\n'
    result += f"\ndefault={temp._default}\n\n"
    if temp.__doc__:
        result += '\n'.join(str(x).strip() for x in temp.__doc__.split('\n'))
    else:
        print(f"bad docstring in {conf}")
    return result



for job in jobs:
    if job in converters:
        continue
    result = ""
    temp: IJob = IJob.create(job)
    if not temp.enabled:
        continue
    result += f"\n.. _analysis-reference-{job}:\n\n"
    result += f"{job}\n"
    result += "".join(len(job)*['~'])+'\n\n'
    if temp.__doc__:
        result += '\n'.join(str(x).lstrip() for x in temp.__doc__.split('\n'))
    else:
        print(f"bad docstring in {conf}")
    if not result.endswith('\n'):
        result += '\n'
    result += "\nInputs:\n\n"
    for iname, itype in temp.settings.items():
        conf = itype[0]
        defval = itype[1].get("default", "N/A")
        job_inputs[conf] = make_configurator_doc(conf, "analysis")
        result += f"- {iname}: :ref:`configurator-analysis-{conf}` default={defval}\n"
    job_page.append(result)
        

for job in converters:
    result = ""
    temp: Converter = Converter.create(job)
    if not temp.enabled:
        continue
    result += f"\n.. _converter-reference-{job}:\n\n"
    result += f"{job}\n"
    result += "".join(len(job)*['~'])+'\n\n'
    if temp.__doc__:
        result += '\n'.join(str(x).lstrip() for x in temp.__doc__.split('\n'))
    else:
        print(f"bad docstring in {conf}")
    if not result.endswith('\n'):
        result += '\n'
    result += "\nInputs:\n\n"
    for iname, itype in temp.settings.items():
        conf = itype[0]
        defval = itype[1].get("default", "N/A")
        converter_inputs[conf] = make_configurator_doc(conf, "converter")
        result += f"- {iname}: :ref:`configurator-converter-{conf}` default={defval}\n"
    converter_page.append(result)


for qvecs in generators:
    result = ""
    temp: IQVectors = IQVectors.create(qvecs, unit_cell=UnitCell(np.eye(3)))
    if not temp.enabled:
        continue
    result += f"\n.. _qvectors-reference-{qvecs}:\n\n"
    result += f"{qvecs}\n"
    result += "~" * len(qvecs) + "\n\n"
    if temp.__doc__:
        result += "\n".join(map(str.lstrip, temp.__doc__.splitlines()))
    else:
        print(f"bad docstring in {conf}")
    if not result.endswith('\n'):
        result += '\n'
    result += "\nInputs:\n\n"
    for iname, (conf, params) in temp.settings.items():
        defval = params.get("default", "N/A")
        job_inputs[conf] = make_configurator_doc(conf, "analysis")
        result += f"- {iname}: :ref:`configurator-analysis-{conf}` default={defval}\n"
    qvector_page.append(result)


with open("pages/vector_generators.rst", "w") as target:
    target.write("""\
.. _vector-generator-list:

List of q-vector generators
===========================
""")
    target.write("\n".join(qvector_page) + "\n")

with open("pages/converters.rst", "w") as target:
    target.write(".. _converter-list:\n\n")
    target.write("List of trajectory converters\n")
    target.write("=============================\n\n")
    for entry in converter_page:
        target.write(entry + "\n")

with open("pages/analysis_jobs.rst", 'w') as target:
    target.write(".. _analysis-list:\n")
    target.write("\n")
    target.write("List of analysis types\n")
    target.write("======================\n\n")
    for entry in job_page:
        target.write(entry + "\n")

with open("pages/parameters.rst", 'w') as target:
    target.write('\n')
    target.write('Converter Inputs\n')
    target.write('~~~~~~~~~~~~~~~~\n')
    order = sorted(converter_inputs.keys())
    for name in order:
        entry = converter_inputs[name]
        target.write(entry + "\n")
    target.write('\n')
    target.write('Analysis Inputs\n')
    target.write('~~~~~~~~~~~~~~~\n')
    order = sorted(job_inputs.keys())
    for name in order:
        entry = job_inputs[name]
        target.write(entry + "\n")
