# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/DataViewModel/JobHolder.py
# @brief     Subclass of QStandardItemModel for MDANSE jobs
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************

from icecream import ic

from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtCore import QObject, Slot, Signal, QProcess, QThread, QMutex


class JobThread(QThread):
    job_failure = Signal(str)

    def __init__(self, *args, command=None, parameters={}):
        super().__init__(*args)
        ic("JobThread starts init")
        self._command = command
        self._parameters = parameters
        ic("JobThread finished init")

    def run(self):
        ic("JobThread.run is starting")
        job = self._command()
        job.build_configuration()
        ic(f"JobThread._parameters: {self._parameters}")
        try:
            job.run(self._parameters)
        except Exception as inst:
            ic("JobThread has entered exception handling!")
            error_message = ""
            error_message += str(type(inst))
            error_message += str(inst.args)  # arguments stored in .args
            error_message += str(inst)  # __str__ allows args to be printed directly,
            ic("JobThread is about to emit the failure message")
            self.job_failure.emit(error_message)
        else:
            ic("JobThread.run did not raise an exception. JobThread.run will exit now")
        self.exec()  # this starts event handling - will it help?


class JobItem(QStandardItem):
    def __init__(self, *args, command=None):
        super().__init__(*args)
        self._command = command
        self._parameters = {}
        self.has_started = False
        self.has_finished = False
        self.percent_complete = 0
        self._output = None
        self.reference = None

    @property
    def parameters(self):
        return self._parameters

    @parameters.setter
    def set_parameters(self, input: dict):
        self._parameters = input


class JobHolder(QStandardItemModel):
    def __init__(self, parent: QObject = None, python: str = ""):
        super().__init__(parent=parent)
        self.python_interpreter = python
        self.lock = QMutex()
        self.existing_threads = []

    @Slot(str)
    def reportError(self, err: str):
        ic(err)

    @Slot(object)
    def addItem(self, new_entry: QProcess):
        traj = JobItem(new_entry.basename, trajectory=new_entry)
        self.appendRow([traj])

    @Slot(int)
    def startJob(self, job_id: int = -1):
        handle = QProcess(parent=self)

    @Slot(list)
    def startThread(self, job_vars: list):
        th_ref = JobThread(command=job_vars[0], parameters=job_vars[1])
        th_ref.job_failure.connect(self.reportError)
        ic("Thread ready to start!")
        th_ref.start()
        self.existing_threads.append(th_ref)

    # def on_run(self, event=None):

    #     if not self._parametersPanel.validate():
    #         return

    #     parameters = self._parametersPanel.get_value()

    #     name = self._job.define_unique_name()

    #     handle,filename = tempfile.mkstemp(prefix="MDANSE_%s.py" % name, text=True)
    #     os.close(handle)

    #     self._job.save(filename, parameters)

    #     if PLATFORM.name == "windows":
    #         startupinfo = subprocess.STARTUPINFO()
    #         startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    #         startupinfo.wShowWindow = subprocess.SW_HIDE
    #     else:
    #         startupinfo = None

    #     try:
    #         p = subprocess.Popen([sys.executable, filename], startupinfo=startupinfo, stdin=subprocess.PIPE,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #     except subprocess.CalledProcessError as e:
    #         message = e.output
    #     else:
    #         message = None

    #     PUBLISHER.sendMessage("msg_start_job",message=message)

    #     if message is None and not self._standlone:
    #         d = wx.MessageDialog(None, 'Your analysis is performing. Do you want to close ?', 'Question', wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
    #         if d.ShowModal() == wx.ID_YES:
    #             self.on_close(None)

    #     if self._standlone:
    #         p.wait()
