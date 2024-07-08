from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QProcess, pyqtSignal
from PyQt5.QtGui import QIntValidator


class ResizeWindow(QtWidgets.QDialog):
    commandSignal = pyqtSignal(list, list, str)

    def __init__(self, files_list=None):
        super(ResizeWindow, self).__init__()
        uic.loadUi('ui/resizewindow.ui', self)

        self.files = files_list

        self.sliderScale.valueChanged.connect(self.update_scale_display)
        self.textScale.textChanged.connect(self.update_slider_value)

        self.radioCustom.toggled.connect(self.toggle_custom_size)
        self.radioScale.toggled.connect(self.toggle_scale)

        self.setup_validators()

        self.update_scale_display()
        self.fetch_and_display_size()
        self.radioCustom.setChecked(True)
        self.toggle_custom_size(True)

    def fetch_and_display_size(self):
        if len(self.files) == 1:
            self.get_image_size(self.files[0])
        else:
            self.printOrigSize.setText("Unavailable for batch")

    def get_image_size(self, image_path):
        process = QProcess()
        if image_path.lower().endswith('.gif'):
            process.start("convert", [f"{image_path}[0]", "-format", "%wx%h", "info:"])
        else:
            process.start("convert", [image_path, "-format", "%wx%h", "info:"])
        process.waitForFinished()  # Synchronously wait for the process to finish
        output = process.readAllStandardOutput().data().decode().strip()

        if 'x' in output:
            width, height = map(int, output.split('x'))
            if width is not None and height is not None:
                self.printOrigSize.setText(f"{width} x {height}")
                self.set_dimensions(width, height)
            else:
                self.printOrigSize.setText("No size info")
        else:
            self.printOrigSize.setText("No size info")

    def set_dimensions(self, width, height):
        self.lineEdit.setText(str(width))
        self.lineEdit_2.setText(str(height))

    def update_scale_display(self):
        scale_value = self.sliderScale.value()
        self.textScale.setText(str(scale_value))

    def update_slider_value(self):
        scale_value = self.textScale.text()
        if scale_value.isdigit():
            self.sliderScale.setValue(int(scale_value))

    def setup_validators(self):
        validator = QIntValidator(1, 10000, self)  # Max dimensions reasonable
        self.lineEdit.setValidator(validator)
        self.lineEdit_2.setValidator(validator)
        self.textScale.setValidator(QIntValidator(1, 200, self))

    def toggle_custom_size(self, checked):
        self.lineEdit.setEnabled(checked)
        self.lineEdit_2.setEnabled(checked)
        self.pushLock.setEnabled(checked)
        if checked:
            self.sliderScale.setEnabled(False)
            self.textScale.setEnabled(False)
            self.scalePercentLabel.setEnabled(False)

    def toggle_scale(self, checked):
        self.sliderScale.setEnabled(checked)
        self.textScale.setEnabled(checked)
        self.scalePercentLabel.setEnabled(checked)
        if checked:
            self.lineEdit.setEnabled(False)
            self.lineEdit_2.setEnabled(False)
            self.pushLock.setEnabled(False)

    def display_message_box(self, message):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setWindowTitle("Input Error")
        msg.setText(f"{message}")
        msg.exec_()

    def accept(self):
        width = self.lineEdit.text()
        height = self.lineEdit_2.text()
        scale = self.sliderScale.value()

        if self.radioCustom.isChecked():
            if not width and not height:
                self.display_message_box("The dimension values are empty")
                return  # nothing if both fields are empty
            elif not self.pushLock.isChecked():
                if width and height:
                    cmd_template = ["-resize", f"{width}x{height}!"]
                else:
                    self.display_message_box("Only one dimension filled.\nToggle the \"lock aspect ratio\" "
                                             "button, if you wish to\nlet the convert calculate "
                                             "the other dimension. ")
                    return
            else:
                if width and height:
                    cmd_template = ["-resize", f"{width}x{height}"]
                elif width:
                    cmd_template = ["-resize", f"{width}x"]
                else:
                    cmd_template = ["-resize", f"x{height}"]
        else:
            cmd_template = ["-resize", f"{scale}%"]

        print("Resize parameters sent to Process Handler")
        self.commandSignal.emit(cmd_template, self.files, "Resize")
        super().accept()

    def reject(self):
        print("Resize canceled.")
        super().reject()

