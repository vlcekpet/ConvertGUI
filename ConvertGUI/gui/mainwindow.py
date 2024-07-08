import os
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QListWidgetItem, QShortcut
from PyQt5.QtGui import QPixmap, QKeySequence

from gui.cropwindow.ui import QCrop
from gui.resizewindow import ResizeWindow
from gui.rotatewindow import RotateWindow
from gui.addtextwindow import AddTextWindow
from gui.filterwindow import FilterWindow
from gui.blurwindow import BlurWindow
from app.processhandler import ProcessHandler
from app.filemanager import FileManager


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('ui/mainwindow.ui', self)

        # Initialize FileManager
        self.file_manager = FileManager(self)
        self.file_manager.messageSignal.connect(self.log_message_from_signal)
        # Initialize ProcessHandler
        self.process_handler = ProcessHandler(self)
        self.process_handler.messageSignal.connect(self.log_message_from_signal)
        self.process_handler.successSignal.connect(self.check_success)

        # Connect UI elements to their functionality
        self.pushSelect.clicked.connect(self.select_files)
        # Dialog elements for convert
        self.pushExport.clicked.connect(self.export_file)
        self.pushResize.clicked.connect(self.open_resize_window)
        self.pushRotate.clicked.connect(self.open_rotate_window)
        self.pushCrop.clicked.connect(self.open_crop_window)
        self.pushFilter.clicked.connect(self.open_filter_window)
        self.pushText.clicked.connect(self.open_text_window)
        self.pushBlur.clicked.connect(self.open_blur_window)
        # Multiple files selection buttons
        self.selectAll.clicked.connect(self.select_all_files)
        self.unselectAll.clicked.connect(self.unselect_all_files)

        # Tickbox for PDF selection with batch  ...maybe also add connect to file change?
        self.singlePDFcheck.setVisible(False)
        self.comboFormat.currentIndexChanged.connect(self.update_pdfcheck_visibility)

        # Menu actions
        self.actionOpen.triggered.connect(self.select_files)
        self.actionExport.triggered.connect(self.export_file)
        self.actionQuit.triggered.connect(self.close)
        self.actionUndo.triggered.connect(self.undo_action)
        self.actionRedo.triggered.connect(self.redo_action)

        # Keyboard shortcuts
        self.shortcutSave = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcutSave.activated.connect(self.export_file)
        self.shortcutOpen = QShortcut(QKeySequence("Ctrl+O"), self)
        self.shortcutOpen.activated.connect(self.select_files)
        self.shortcutClose = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.shortcutClose.activated.connect(self.close)
        self.shortcutUndo = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.shortcutUndo.activated.connect(self.undo_action)
        self.shortcutRedo = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        self.shortcutRedo.activated.connect(self.redo_action)

        # Disabled buttons on init with no files loaded
        self.update_button_states()

    def update_button_states(self):
        """ Enable or disable buttons based on whether files are loaded """
        buttons = [self.pushResize, self.pushRotate, self.pushCrop,
                   self.pushFilter, self.pushText, self.pushBlur]
        if self.file_manager.current_files:
            # Check if any of the files is a PDF
            pdf = any(file.lower().endswith('.pdf') for file in self.file_manager.current_files)
            for button in buttons:
                button.setEnabled(not pdf)
            self.pushExport.setEnabled(True)
            self.actionExport.setEnabled(True)
            self.comboFormat.setEnabled(True)
        else:
            for button in buttons:
                button.setEnabled(False)
            self.pushExport.setEnabled(False)
            self.actionExport.setEnabled(False)
            self.comboFormat.setEnabled(False)

    def update_pdfcheck_visibility(self):
        """ Checks if the export format is set to PDF and if in the multiple files mode """
        if len(self.file_manager.current_files) > 1 and self.comboFormat.currentText() == 'PDF':
            self.singlePDFcheck.setVisible(True)
        else:
            self.singlePDFcheck.setVisible(False)

    def update_preview(self, files):
        """ Handles preview of file(s) with respect to the mode of the selection. """
        if len(files) == 1:
            self.previewStackedWg.setCurrentWidget(self.pageSingleFile)
            base, ext = os.path.splitext(files[0])
            if ext == ".pdf":
                pixmap = QPixmap("resources/blankpreview.jpg")
            else:
                pixmap = QPixmap(files[0])
            self.labelPicture.setPixmap(pixmap.scaled(self.labelPicture.size(), Qt.KeepAspectRatio))
        elif len(files) > 1:
            self.previewStackedWg.setCurrentWidget(self.pageMultiple)
            self.listOfFiles.clear()
            for file in files:
                parts = file.split('-', 1)
                if len(parts) > 1:
                    file = parts[1]  # Display file without path and version
                item = QListWidgetItem(file)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                self.listOfFiles.addItem(item)
        else:
            self.previewStackedWg.setCurrentWidget(self.pageNoFile)

    def select_all_files(self):
        """ Selects all files in list of files in multiple files mode """
        for index in range(self.listOfFiles.count()):
            item = self.listOfFiles.item(index)
            item.setCheckState(Qt.Checked)

    def unselect_all_files(self):
        """ Unselects all files in list of files in multiple files mode """
        for index in range(self.listOfFiles.count()):
            item = self.listOfFiles.item(index)
            item.setCheckState(Qt.Unchecked)

    def fetch_selected_files(self):
        """Returns the list of checked items in the list of files"""
        selected_files = []
        for index in range(self.listOfFiles.count()):
            item = self.listOfFiles.item(index)
            if item.checkState() == Qt.Checked:
                selected_files.append(item.text())
        return selected_files

    def update_export_format(self, files):
        """ Sets export format choice with respect to the opened file """
        if files:
            file_extension = files[0].split('.')[-1].upper()
            if file_extension == "JPEG":
                file_extension = "JPG"
            index = self.comboFormat.findText(file_extension)
            if index >= 0:
                self.comboFormat.setCurrentIndex(index)
            else:
                self.comboFormat.setCurrentIndex(2)  # Default to the JPG format if not found
        else:
            self.comboFormat.setCurrentIndex(2)  # No file selected

    def select_files(self):
        self.file_manager.select_files()
        self.update_button_states()

    def export_file(self):
        """ File export handler, triggers process handler with respect to file mode """
        format_extension = self.comboFormat.currentText().lower()  # selected format as file extension
        default_filename = f"converted_output.{format_extension}"

        file_path, _ = QFileDialog.getSaveFileName(self, "Save File",
                                                   os.path.join(os.path.expanduser("~"), default_filename),
                                                   f"All files (*)")
        if file_path:
            # handle case of user writing name without extension
            if not file_path.endswith(f".{format_extension}"):
                file_path += f".{format_extension}"
            # check batch to single pdf
            if (len(self.file_manager.current_files) > 1 and format_extension == "pdf"
                    and self.singlePDFcheck.isChecked()):
                pdf = True
            else:
                pdf = False

            self.process_handler.export_files(self.file_manager.current_files, file_path, pdf)
        else:
            print("Export aborted.")

    def open_resize_window(self):
        """ Resize operation dialog execution """
        print("Opening Resize Window...")
        files_list = self.file_manager.current_files
        dialog = ResizeWindow(files_list)
        dialog.commandSignal.connect(self.run_process)
        dialog.exec_()

    def open_rotate_window(self):
        """ Rotate operation dialog execution """
        print("Opening Rotate Window...")
        files_list = self.file_manager.current_files
        dialog = RotateWindow(files_list)
        dialog.commandSignal.connect(self.run_process)
        dialog.exec_()

    def open_crop_window(self):
        """ Crop operation dialog execution """
        print("Opening Crop Window...")
        files_list = self.file_manager.current_files
        dialog = QCrop(files_list)
        dialog.commandSignal.connect(self.run_process)
        dialog.exec()

    def open_filter_window(self):
        """ Color filter operation dialog execution """
        print("Opening Filter Window...")
        files_list = self.file_manager.current_files
        dialog = FilterWindow(files_list)
        dialog.commandSignal.connect(self.run_process)
        dialog.exec_()

    def open_text_window(self):
        """ Text Add operation dialog execution """
        print("Opening Add Text Window...")
        files_list = self.file_manager.current_files
        dialog = AddTextWindow(files_list)
        dialog.commandSignal.connect(self.run_process)
        dialog.exec_()

    def open_blur_window(self):
        """ Blur operation dialog execution """
        print("Opening Blur Window...")
        files_list = self.file_manager.current_files
        dialog = BlurWindow(files_list)
        dialog.commandSignal.connect(self.run_process)
        dialog.exec_()

    def run_process(self, parameters, files, operation):
        """ Triggers process handler to preform operation """
        self.process_handler.execute(parameters, files, operation)

    def check_success(self, success):
        """ Checks success after ProcessHandler action, triggers file manager """
        if success:
            self.file_manager.update_current_files()
        else:
            self.file_manager.remove_processed_files()

    def log_message_from_signal(self, data):
        """ Sends message from signal to log_message method to display in the log """
        message, color = data
        if color is None:
            self.log_message(message)
        else:
            self.log_message(message, color)

    def log_message(self, message, color=None):
        """ Shows information in the log about preformed operations and technical matters. """
        if color:
            message = f'<span style="color:{color};">{message}</span>'
        self.textEditLog.append(message)

    def undo_action(self):
        print("Undo last action...")
        self.file_manager.undo()

    def redo_action(self):
        print("Redo last action...")
        self.file_manager.redo()

    def closeEvent(self, event):
        """ Manages exiting the app """
        reply = QtWidgets.QMessageBox.question(self, 'Message',
                                               "Are you sure you want to quit?", QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.file_manager.clear_temp_folder()  # clear temporary files on exit
            event.accept()
        else:
            event.ignore()

