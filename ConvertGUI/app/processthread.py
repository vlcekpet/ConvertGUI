import os
import shutil
from PyQt5.QtCore import QProcess, pyqtSignal, QThread


class ProcessThread(QThread):
    progress_signal = pyqtSignal(tuple)
    finished_signal = pyqtSignal(bool)

    def __init__(self, cmd_template, files_list, operation, progress_dialog, selected_files=None):
        super(ProcessThread, self).__init__()
        self.cmd_template = cmd_template
        self.files_list = files_list
        self.operation = operation
        self.progress_dialog = progress_dialog
        self.selected_files = selected_files

    def run(self):
        fail = False
        base_dir = "temp"
        for file in self.files_list:
            if self.progress_dialog.stopped:
                fail = True
                self.progress_signal.emit(("Processing canceled by user.", "red"))
                break

            original_path = file
            base_name = os.path.basename(file)
            parts = base_name.split('-', 1)
            rest_of_name = ""
            if len(parts) == 2:
                prefix, rest_of_name = parts
                output_file_name = f"NEW-{rest_of_name}"
            else:
                output_file_name = f"ERR-{base_name}"

            output_path = os.path.join(base_dir, output_file_name)

            # Handle file not in selected files
            if (self.selected_files is not None) and (rest_of_name not in self.selected_files):
                shutil.copy(original_path, output_path)
                continue

            parameters = self.cmd_template.copy()
            parameters.insert(0, original_path)
            parameters.append(output_path)

            process = QProcess()
            process.start("convert", parameters)
            finished = process.waitForFinished()

            if not finished or process.exitStatus() != QProcess.NormalExit or process.exitCode() != 0:
                error_message = process.readAllStandardError().data().decode().strip()
                self.progress_signal.emit((f"{self.operation} failed ({base_name}): {error_message}", "red"))
                fail = True
                break

        self.finished_signal.emit(not fail)
