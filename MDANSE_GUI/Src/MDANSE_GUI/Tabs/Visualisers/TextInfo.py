from qtpy.QtCore import QObject, Slot, Signal
from qtpy.QtWidgets import QPushButton, QTextBrowser, QWidget, QFileDialog


class TextInfo(QTextBrowser):
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

    @Slot(str)
    def append_text(self, new_text: str):
        self.append(new_text)

    def filter(self, some_text: str, line_break="<br />"):
        new_text = ""
        if self._header:
            new_text += self._header + line_break
        if some_text is not None:
            new_text += line_break.join([x.strip() for x in some_text.split("\n")])
        if self._footer:
            new_text += line_break + self._footer
        return new_text
