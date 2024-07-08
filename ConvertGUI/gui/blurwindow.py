from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal


class BlurWindow(QtWidgets.QDialog):
    commandSignal = pyqtSignal(list, list, str)

    def __init__(self, files_list=None):
        super(BlurWindow, self).__init__()
        uic.loadUi('ui/blurwindow.ui', self)

        self.files = files_list
        self.base_dir = "temp"

        self.label_2.setText(str(self.sliderDeviation.value()))

        # Connect slider and label signal
        self.sliderDeviation.valueChanged.connect(self.update_label)

    def update_label(self, value):
        """ Display of the blur sigma value from the slider scale """
        self.label_2.setText(str(value))

    def accept(self):
        """ Parameters collection and send to process handler on accept """
        sigma = self.sliderDeviation.value()
        cmd_template = ["-blur", f"0x{sigma}"]
        print("Blur parameters sent to Process Handler")
        self.commandSignal.emit(cmd_template, self.files, "Blur")
        super().accept()

    def reject(self):
        print("Blur operation canceled.")
        super().reject()
