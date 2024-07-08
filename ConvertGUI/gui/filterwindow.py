from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QColorDialog
from PyQt5.QtGui import QIntValidator


class FilterWindow(QtWidgets.QDialog):
    commandSignal = pyqtSignal(list, list, str)

    def __init__(self, files_list=None):
        super(FilterWindow, self).__init__()
        uic.loadUi('ui/filterwindow.ui', self)

        self.files = files_list

        self.lineEdit.setValidator(QIntValidator(1, 99, self))

        self.pushButton.clicked.connect(self.select_color)

        self.radioButton.toggled.connect(self.update_ui_state)
        self.radioButton_2.toggled.connect(self.update_ui_state)
        self.radioButton_3.toggled.connect(self.update_ui_state)

        # Connect slider to line edit
        self.horizontalSlider.valueChanged.connect(self.update_intensity)
        self.lineEdit.textChanged.connect(self.update_slider)

        # Initialize filter color - white
        self.color = "#FFFFFF"
        self.pushButton.setStyleSheet(f"background-color: {self.color}")

        # Initial UI state
        self.update_ui_state()

    def update_ui_state(self):
        """ Disables buttons with respect to filter selection """
        color_filter_selected = self.radioButton_2.isChecked()
        self.pushButton.setEnabled(color_filter_selected)
        self.horizontalSlider.setEnabled(color_filter_selected)
        self.lineEdit.setEnabled(color_filter_selected)
        self.label.setEnabled(color_filter_selected)

    def select_color(self):
        """ Sets color filter color """
        color = QColorDialog.getColor()
        if color.isValid():
            self.color = color.name()
            self.pushButton.setStyleSheet(f"background-color: {self.color}")
            print(f"Color for filter set to: {self.color}")

    def update_intensity(self, value):
        """ Displays intensity from slider in line edit """
        self.lineEdit.setText(str(value))

    def update_slider(self):
        """ Sets slider to intensity from line edit """
        value = self.lineEdit.text()
        if value.isdigit():
            self.horizontalSlider.setValue(int(value))

    def accept(self):
        """ Parameters collection and send to process handler on accept """
        intensity = self.horizontalSlider.value()

        # Parameters selection
        if self.radioButton_3.isChecked():
            # Grayscale filter
            cmd_template = ["-colorspace", "Gray"]
        elif self.radioButton_2.isChecked() and self.color:
            # Color filter
            cmd_template = ["-fill", f"{self.color}", "-colorize", f"{intensity}%"]
        else:
            # Black and white filter
            cmd_template = ["-monochrome"]

        print("Color Filter parameters sent to Process Handler")
        self.commandSignal.emit(cmd_template, self.files, "Color Filter")
        super().accept()

    def reject(self):
        # Logic to handle the Cancel action
        print("Color Filter operation canceled.")
        super().reject()
