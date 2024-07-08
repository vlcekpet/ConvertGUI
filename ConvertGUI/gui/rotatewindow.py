from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QColorDialog


class RotateWindow(QtWidgets.QDialog):
    commandSignal = pyqtSignal(list, list, str)

    def __init__(self, files_list=None):
        super(RotateWindow, self).__init__()
        uic.loadUi('ui/rotatewindow.ui', self)

        self.files = files_list

        # Validators and UI settings
        self.lineAngle.setValidator(QIntValidator(-360, 360, self))
        self.lineAngle.setEnabled(False)
        self.displayColor.setEnabled(False)
        self.transparentCheck.setEnabled(False)

        # Init values
        self.flip_command = ""
        self.rotation_angle = 0
        self.backgroundColor = "#FFFFFF"  # Default background color to white
        self.displayColor.setStyleSheet(f"background-color: {self.backgroundColor}")

        # Radio buttons for rotation
        self.radioButton.toggled.connect(lambda: self.set_rotation(0))
        self.radioButton_2.toggled.connect(lambda: self.set_rotation(90))
        self.radioButton_3.toggled.connect(lambda: self.set_rotation(180))
        self.radioButton_4.toggled.connect(lambda: self.set_rotation(270))
        self.radioButton_8.toggled.connect(self.custom_rotation_enabled)

        # Radio buttons for flipping
        self.radioButton_7.toggled.connect(lambda: self.set_flip('none'))
        self.radioButton_5.toggled.connect(lambda: self.set_flip('horizontal'))
        self.radioButton_6.toggled.connect(lambda: self.set_flip('vertical'))

        # Button to display color dialog
        self.displayColor.clicked.connect(self.open_color_dialog)

    def custom_rotation_enabled(self, checked):
        if checked:
            self.lineAngle.setEnabled(checked)
            self.displayColor.setEnabled(checked)
            self.transparentCheck.setEnabled(checked)
        else:
            self.lineAngle.setEnabled(False)
            self.displayColor.setEnabled(False)
            self.transparentCheck.setEnabled(False)

    def set_rotation(self, rotation):
        self.rotation_angle = rotation

    def set_flip(self, mode):
        if mode == 'horizontal':
            self.flip_command = '-flop'
        elif mode == 'vertical':
            self.flip_command = '-flip'
        else:
            self.flip_command = ""

    def open_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            print(f"Color selected: {color.name()}")
            self.backgroundColor = color.name()
            self.displayColor.setStyleSheet(f"background-color: {self.backgroundColor}")

    def accept(self):
        flip_command = self.flip_command
        rotation_angle = self.rotation_angle
        color = self.backgroundColor
        if self.radioButton_8.isChecked():
            rotation_angle = self.lineAngle.text()
            if not rotation_angle.isdigit():
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setWindowTitle("Input Error")
                msg.setText("Invalid rotation angle")
                msg.exec_()
                return
        if self.transparentCheck.isChecked():
            color = "none"

        cmd_template = ["-background", f"{color}", "-rotate", f"{rotation_angle}"]
        if flip_command != "":
            cmd_template.append(f"{flip_command}")

        print("Rotate/Flip parameters sent to Process Handler")
        self.commandSignal.emit(cmd_template, self.files, "Rotate/Flip")
        super().accept()

    def reject(self):
        print("Rotate/Flip canceled.")
        super().reject()
