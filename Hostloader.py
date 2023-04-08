#!/usr/bin/env python3
#
import sys
import glob
import serial
import logging

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QFileDialog, QStatusBar
)
from PyQt5.uic import loadUi
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot, QRegExp
from PyQt5.QtGui import QRegExpValidator
from main_window_ui import Ui_MainWindow

import pyMicroloader as ml
class Window(QMainWindow, Ui_MainWindow):
    work_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.connectSignalsSlots()
        self.ldr = None         # The class to use as loader
        self.file_name = ""
        self.port_names = self.serial_port_names()
        self.populate_serial_ports()
        self.loader_names = ['Altos USB', 'AMSAT Serial', 'RT-IHU (TMS570)']
        self.populate_loaders()
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.refresh_status()
        self.show_status_line()
        self.threadpool = QThreadPool()
        self.serial_number.setValidator(QRegExpValidator(QRegExp("[0-9]*")))
        self.serial_number_ui_enabled(False)


    def serial_number_ui_enabled(self, enabled):
        self.serial_number.setEnabled(enabled)
        self.force_serial_checkbox.setEnabled(enabled)
        self.serial_number_label.setEnabled(enabled)


    def connectSignalsSlots(self):
        self.action_Exit.triggered.connect(self.close)
        self.action_About_AMSAT_Hostloader.triggered.connect(self.about)
        self.action_Open.triggered.connect(self.open_file)
        self.serial_ports.activated.connect(self.refresh_status)
        self.loaders.activated.connect(self.refresh_status)
        self.test_button.clicked.connect(self.test_button_action)
        self.flash_button.clicked.connect(self.flash_button_action)

    def set_loader(self):
        loader_number = self.loaders.currentIndex()
        if loader_number == 1:
            import pyAltosFlash as ldr
        elif loader_number == 2:
            import pySerialFlash as ldr
        elif loader_number == 3:
            import pyTISerialFlash as ldr
        else:
            return
        self.ldr = ldr

    def test_button_action(self):
        self.set_loader()
        self.logger_text.clear()
        self.disable_buttons()
        worker = BackgroundWorker(
            'Test',
            self.ldr,
            self.serial_ports.currentText()
        )
        self.execute_worker(worker)


    def flash_button_action(self):
        self.set_loader()
        self.logger_text.clear()
        self.disable_buttons()
        if self.loaders.currentIndex() == 3:    # This is the TI loader
            worker = BackgroundWorker(
                'Flash',
                self.ldr,
                self.serial_ports.currentText(),
                file_name = self.file_name
            )
        else:
            serial_number = None
            if len(self.serial_number) > 0:
                serial_number = int(self.serial_number.text())
            else:
                serial_number
            worker = BackgroundWorker(
                'FlashLegacy',
                self.ldr,
                self.serial_ports.currentText(),
                file_name = self.file_name,
                force_serial = self.force_serial.isChecked()
            )
        self.execute_worker(worker)

    def disable_buttons(self):
        self.test_button.setEnabled(False)
        self.flash_button.setEnabled(False)

    def execute_worker(self, worker):
        worker.signals.progress.connect(self.update_progress)
        worker.signals.finished.connect(self.restore_buttons)
        self.threadpool.start(worker)


    def update_progress(self, message):
        msg = message.split(' ', 1)
        if msg[0] == 'ERROR':
            self.logger_text.appendHtml(f'<p style="color: red;">{msg[1]}</p>')
        else:
            self.logger_text.appendPlainText(msg[1])


    def restore_buttons(self):
        self.refresh_status()


    def refresh_status(self):
        self.test_button.setEnabled(False)
        self.flash_button.setEnabled(False)
        if self.serial_ports.currentIndex() > 0 and self.loaders.currentIndex() > 0:
            self.test_button.setEnabled(True)
            if len(self.file_name) > 0:
                self.flash_button.setEnabled(True)
        if self.loaders.currentIndex() in (0, 3):
            self.serial_number_ui_enabled(False)
        else:
            self.serial_number_ui_enabled(True)
        self.show_status_line()

    def open_file(self):
        options = QFileDialog.Options()
        self.file_name, _ = QFileDialog.getOpenFileName(
            self,
            "QFileDialog.getOpenFileName()",
            "",
            "All Files (*)",
            options=options
        )
        self.filename_label.setText(f"Flash file: {self.file_name}")
        self.refresh_status()
        self.show_status_line()


    def show_status_line(self):
        if self.loaders.currentText() == "None":
            self.statusBar.showMessage("Please select a loader", 0)
        elif self.serial_ports.currentText() == "None":
            self.statusBar.showMessage("Please select a serial port", 0)
        elif len(self.file_name) == 0:
            self.statusBar.showMessage("Please select a file to flash", 0)
        else:
            self.statusBar.showMessage("", 0)


    def about(self):
        QMessageBox.about(
            self,
            "About AMSAT Host loader",
            "<p>Flash a new image to an IHU or RT-IHU</p>"
            "<p>Heimir Þór Sverrisson, 2023</p>"
            "<p>W1ANT / TF3ANT</p>"
        )


    def populate_loaders(self):
        self.loaders.addItem("None")
        self.loaders.addItems(self.loader_names)


    def populate_serial_ports(self):
        self.serial_ports.addItem("None")
        self.serial_ports.addItems(self.port_names)


    def serial_port_names(self):
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            ports = glob.glob('/dev/ttyUSB[0-9]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')
        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result

class WorkerSignals(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(str)

class BackgroundWorker(QRunnable):

    def __init__(self, task_name, ldr, port, file_name=None, force_serial=False, serial_number=None):
        super(BackgroundWorker, self).__init__()
        self.ldr = ldr
        self.port = port
        self.log_handler = None
        self.setup_logger()
        self.task_name = task_name
        self.file_name = file_name
        self.force_serial = force_serial
        self.serial_number = serial_number
        self.signals = WorkerSignals()

    # Alternative format string:
    #    '%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s'
    #
    def setup_logger(self):
        logging.getLogger().handlers.clear()    # Remove the default logger
        self.log_handler = StringListLogger(self.update_progress)
        self.log_handler.setFormatter(
            logging.Formatter(
                    '%(levelname)s %(message)s'
                )
        )
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.DEBUG)

    @pyqtSlot()
    def run(self):
        try:
            if self.task_name == 'Test':
                self.ldr.FlashLdr(device=self.port, debug=True)
            elif self.task_name == 'Flash':
                loader = self.ldr.FlashLdr(device=self.port, debug=True)
                loader.download_application(self.file_name)
                loader.StartExecution()
            elif self.task_name == 'FlashLegacy':
                loader = self.ldr.FlashLdr(device=self.port, debug=True)
                ml.flash_and_run(self.file, loader, self.force_serial, self.serial_number)
        except Exception as e:
            logging.error(f'Error connecting: {e}')
        logging.getLogger().removeHandler(self.log_handler)
        self.signals.finished.emit()

    def update_progress(self, message):
        self.signals.progress.emit(message)

class StringListLogger(logging.Handler):
    def __init__(self, update_progress):
        super(StringListLogger, self).__init__()
        self.update_progress = update_progress

    def emit(self, record):
        msg = self.format(record)
        self.update_progress(msg)

    def write(self, m):
        pass

class QPlainTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super(QPlainTextEditLogger, self).__init__()

        self.logger_text = parent.logger_text
        self.logger_text.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.logger_text.appendPlainText(msg)

    def write(self, m):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())