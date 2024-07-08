from PyQt5 import QtWidgets, uic


class ProgressDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(ProgressDialog, self).__init__(parent)
        uic.loadUi('ui/processwindow.ui', self)

        self.stop_button.clicked.connect(self.stop_processing)
        self.stopped = False

    def stop_processing(self):
        self.stopped = True
        self.label.setText("Stopping...")

    def closeEvent(self, event):
        # if attempted to close, behaves like clicking stop
        self.stop_processing()

    def close_dialog(self):
        self.accept()


