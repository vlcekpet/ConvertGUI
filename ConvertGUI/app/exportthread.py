import os
from PyQt5.QtCore import QProcess, pyqtSignal, QThread


class ExportThread(QThread):
    progress_signal = pyqtSignal(tuple)
    finished_signal = pyqtSignal(bool)

    def __init__(self, input_files, output_path, progress_dialog):
        super(ExportThread, self).__init__()
        self.input_files = input_files
        self.output_path = output_path
        self.progress_dialog = progress_dialog

    def run(self):
        fail = False
        base, ext = os.path.splitext(self.output_path)
        for i, file in enumerate(self.input_files, start=1):
            if self.progress_dialog.stopped:
                fail = True
                self.progress_signal.emit(("Export canceled by user. Some of the files might have been already "
                                           "exported.\nPlease check the selected export directory.", "red"))
                break
            # output file path with enumeration
            numbered_output_path = f"{base}{i}{ext}"
            cmd = ["convert", [file, numbered_output_path]]
            process = QProcess()
            process.start(*cmd)
            finished = process.waitForFinished()
            if not finished or process.exitStatus() != QProcess.NormalExit or process.exitCode() != 0:
                error_message = process.readAllStandardError().data().decode().strip()
                self.progress_signal.emit((f"Export failed {file}: {error_message}", "red"))
                fail = True

        self.finished_signal.emit(not fail)
