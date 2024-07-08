import os
from PyQt5.QtCore import QProcess, pyqtSignal, QObject
from gui.progressdialog import ProgressDialog
from app.processthread import ProcessThread
from app.exportthread import ExportThread


class ProcessHandler(QObject):
    messageSignal = pyqtSignal(tuple)
    successSignal = pyqtSignal(bool)

    def __init__(self, main_window=None):
        super(ProcessHandler, self).__init__()

        self.main_window = main_window
        self.progress_dialog = None
        self.process_thread = None
        self.selected_files = None
        self.files_to_export = None

    def execute(self, cmd_template, files_list, operation):
        parent_dialog = self.main_window
        if len(files_list) > 1:
            self.selected_files = self.main_window.fetch_selected_files()
            if not self.selected_files:
                self.messageSignal.emit(("Error: No files selected, no operation preformed", 'red'))
                self.reset_variables()
                return

        # Create and show the progress dialog
        self.progress_dialog = ProgressDialog(parent_dialog)
        self.progress_dialog.show()

        # Start the processing in a separate thread
        self.process_thread = ProcessThread(cmd_template, files_list, operation,
                                            self.progress_dialog, self.selected_files)
        self.process_thread.progress_signal.connect(self.handle_thread_message)
        self.process_thread.finished_signal.connect(self.handle_thread_finished)
        self.process_thread.start()

    def export_files(self, input_files, output_path, pdf=False):
        files = input_files.copy()
        if not files:
            print("No files to export.")
            return
        if pdf or len(files) == 1:
            # batch to single pdf or single file export
            if pdf:
                files = self.pick_selected_files(input_files)
                if files is None:
                    return
            files.sort()
            files.append(output_path)
            print(files)
            cmd = ["convert", files]
            print(f"Exporting {os.path.basename(output_path)}")
            self.run_export(cmd)
        else:
            files = self.pick_selected_files(input_files)
            if files is None:
                return
            self.progress_dialog = ProgressDialog(self.main_window)
            self.progress_dialog.show()

            # Start the batch export processing in a separate thread
            self.process_thread = ExportThread(files, output_path, self.progress_dialog)
            self.process_thread.progress_signal.connect(self.handle_thread_message)
            self.process_thread.finished_signal.connect(self.handle_export_thread)
            self.process_thread.start()

    def pick_selected_files(self, files):
        self.files_to_export = []
        self.selected_files = self.main_window.fetch_selected_files()
        if not self.selected_files:
            self.messageSignal.emit(("Error: No files selected, no operation preformed", 'red'))
            self.reset_variables()
            return None
        for file in files:
            parts = file.split('-', 1)
            if len(parts) > 1:
                if parts[1] in self.selected_files:
                    self.files_to_export.append(file)
            else:
                self.messageSignal.emit((f"Internal error (file \'{file}\'). File omitted from export.", "red"))
        return self.files_to_export

    def run_export(self, cmd):
        process = QProcess()
        process.start(*cmd)
        finished = process.waitForFinished()

        if not finished or process.exitStatus() != QProcess.NormalExit or process.exitCode() != 0:
            error_message = process.readAllStandardError().data().decode().strip()
            self.messageSignal.emit((f"Export failed: {error_message}", "red"))
        else:
            self.messageSignal.emit(("Export completed successfully.", 'green'))
        self.reset_variables()

    def handle_thread_message(self, styled_message):
        self.messageSignal.emit(styled_message)

    def handle_thread_finished(self, success):
        if success:
            self.messageSignal.emit(("Operation completed successfully. Loading new version.", 'green'))
            self.successSignal.emit(True)
        else:
            self.messageSignal.emit(("Operation terminated. Reverting to previous version.", 'red'))
            self.successSignal.emit(False)

        self.progress_dialog.close_dialog()
        self.reset_variables()

    def handle_export_thread(self, success):
        if success:
            self.messageSignal.emit(("Export completed successfully.", 'green'))
        else:
            self.messageSignal.emit(("Export completed with errors.", 'red'))

        self.progress_dialog.close_dialog()
        self.reset_variables()

    def reset_variables(self):
        self.progress_dialog = None
        self.process_thread = None
        self.selected_files = None
        self.files_to_export = None

