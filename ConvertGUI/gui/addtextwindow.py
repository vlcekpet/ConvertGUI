from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QColorDialog, QFileDialog


class AddTextWindow(QtWidgets.QDialog):
    commandSignal = pyqtSignal(list, list, str)

    def __init__(self, files_list=None):
        super(AddTextWindow, self).__init__()
        uic.loadUi('ui/addtextwindow.ui', self)

        self.files = files_list
        self.base_dir = "temp"

        self.comboFont.currentTextChanged.connect(self.select_font_file)
        self.comboSize.currentTextChanged.connect(self.check_custom_size)

        self.pushColor.clicked.connect(self.select_color)

        self.font_file = None
        self.color = "#000000"
        self.pushColor.setStyleSheet("background-color: black")
        self.customSize.setValidator(QIntValidator(1, 9999, self))
        self.customSize.setVisible(False)

        # Font dictionary
        self.font_dict = {
            "Work Sans": "resources/textfonts/WorkSans-",
            "Lora": "resources/textfonts/Lora-",
            "Roboto Mono": "resources/textfonts/RobotoMono-"
        }

    def check_custom_size(self):
        """ Enables custom text size dialog """
        if self.comboSize.currentText() == "Custom":
            self.customSize.setVisible(True)
        else:
            self.customSize.setVisible(False)

    def select_font_file(self, text):
        """ Handles font selection or a user-selected custom text font """
        if text == "Custom":
            options = QFileDialog.Options()
            fileName, _ = QFileDialog.getOpenFileName(
                self,
                "Select a font file",
                "",
                "Font Files (*.ttf *.otf)",
                options=options
            )
            if fileName:
                self.font_file = fileName
                self.pushBold.setVisible(False)
                self.pushItalic.setVisible(False)
            else:
                self.font_file = self.font_dict.get("Work Sans", "")
                self.comboFont.setCurrentIndex(0)  # Reset to first predefined option if no file selected
                self.pushBold.setVisible(True)
                self.pushItalic.setVisible(True)
        else:
            self.pushBold.setVisible(True)
            self.pushItalic.setVisible(True)
            self.font_file = self.font_dict.get(text, "")

    def select_color(self):
        """ Handles text color """
        color = QColorDialog.getColor()
        if color.isValid():
            self.color = color.name()
            self.pushColor.setStyleSheet(f"background-color: {self.color}")

    def get_position(self):
        """ Handles position of the text in the picture """
        if self.radioTL.isChecked():
            return "NorthWest"
        elif self.radioTC.isChecked():
            return "North"
        elif self.radioTR.isChecked():
            return "NorthEast"
        elif self.radioML.isChecked():
            return "West"
        elif self.radioMC.isChecked():
            return "Center"
        elif self.radioMR.isChecked():
            return "East"
        elif self.radioBL.isChecked():
            return "SouthWest"
        elif self.radioBC.isChecked():
            return "South"
        elif self.radioBR.isChecked():
            return "SouthEast"

    def display_message_box(self, message):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setWindowTitle("Input Error")
        msg.setText(f"{message}")
        msg.exec_()

    def accept(self):
        """ Parameters collection and send to process handler on accept """
        text = self.textEdit.toPlainText()
        if text == "":
            self.display_message_box("No text to add")
            return

        position = self.get_position()

        size = self.comboSize.currentText()
        if size == "Custom":
            size = self.customSize.text()
            if size == "":
                self.display_message_box("No text size info")
                return

        if self.comboFont.currentText() != "Custom":
            font_style = "Regular"
            if self.pushBold.isChecked() and self.pushItalic.isChecked():
                font_style = "BoldItalic"
            elif self.pushBold.isChecked():
                font_style = "Bold"
            elif self.pushItalic.isChecked():
                font_style = "Italic"
            self.font_file = f"{self.font_file}{font_style}.ttf"

        cmd_template = ["-gravity", position, "-pointsize", size, "-fill", self.color,
                        "-font", self.font_file, "-annotate", "+0+0", text]
        print("Text Add parameters sent to Process Handler")
        self.commandSignal.emit(cmd_template, self.files, "Text Add")
        super().accept()

    def reject(self):
        print("Text Addition canceled.")
        super().reject()
