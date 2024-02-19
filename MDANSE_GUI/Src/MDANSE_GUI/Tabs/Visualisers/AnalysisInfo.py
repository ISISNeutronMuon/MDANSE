from collections import defaultdict

from qtpy.QtCore import QObject, Slot, Signal
from qtpy.QtWidgets import QPushButton, QTextBrowser, QWidget, QFileDialog

from MDANSE.Framework.Jobs.IJob import IJob


class AnalysisInfo(QTextBrowser):
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        self._header = kwargs.pop("header", "")
        self._footer = kwargs.pop("footer", "")
        super().__init__(*args, **kwargs)
        self.setOpenExternalLinks(True)

    @Slot(object)
    def update_panel(self, incoming: object):
        filtered = self.filter(incoming)
        self.setHtml(filtered)

    def filter(self, some_text: str, line_break="<br />"):
        new_text = ""
        if self._header:
            new_text += self._header + line_break
        if some_text is not None:
            new_text += line_break.join([x.strip() for x in some_text.split("\n")])
        if self._footer:
            new_text += line_break + self._footer
        return new_text

    def summarise_chemical_system(self, job_name):
        try:
            temp_instance = IJob.create(job_name)
        except:
            return ""
        text = "\n ==== Input Parameter summary ==== \n"
        params = temp_instance.get_default_parameters()
        for key, value in params.items():
            try:
                text += f"parameters['{key}'] = {value[0]} # {value[1]} \n"
            except:
                continue
        text += " ===== \n"
        return text
