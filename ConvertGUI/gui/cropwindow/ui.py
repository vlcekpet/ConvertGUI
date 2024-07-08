from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QRect, QSize, QSignalBlocker, pyqtSlot, pyqtSignal

from gui import cropwindow
from gui.cropwindow.qcrop_ui import Ui_QCrop

MARGIN_H = 48
MARGIN_V = 120


class QCrop(QDialog):
    commandSignal = pyqtSignal(list, list, str)

    def __init__(self, files_list=None):
        super().__init__()

        self._ui = Ui_QCrop()
        self._ui.setupUi(self)

        self.setWindowTitle('Crop')

        self.files = files_list
        self.base_dir = "temp"

        self.image = QPixmap(self.files[0])
        self._original = QRect(0, 0, self.image.width(), self.image.height())
        self._ui.selector.crop = QRect(0, 0, self.image.width(), self.image.height())
        self._ui.selector.setPixmap(self.image)

        self._ui.spinBoxX.setMaximum(self._original.width()-1)
        self._ui.spinBoxY.setMaximum(self._original.height()-1)
        self._ui.spinBoxW.setMaximum(self._original.width())
        self._ui.spinBoxH.setMaximum(self._original.height())
        self.update_crop_values()

        self.resize(self._original.width() + MARGIN_H, self._original.height() + MARGIN_V)

    def update_crop_area(self):
        values = self.crop_values()
        if self._ui.selector.crop != values:
            self._ui.selector.crop = values
            self._ui.selector.update()

    def crop_values(self):
        return QRect(
            self._ui.spinBoxX.value(),
            self._ui.spinBoxY.value(),
            self._ui.spinBoxW.value(),
            self._ui.spinBoxH.value()
        )

    def update_crop_values(self):
        self._ui.spinBoxX.blockSignals(True)
        self._ui.spinBoxX.setValue(self._ui.selector.crop.x())
        self._ui.spinBoxX.blockSignals(False)
        self._ui.spinBoxY.blockSignals(True)
        self._ui.spinBoxY.setValue(self._ui.selector.crop.y())
        self._ui.spinBoxY.blockSignals(False)
        self._ui.spinBoxW.blockSignals(True)
        self._ui.spinBoxW.setValue(self._ui.selector.crop.width())
        self._ui.spinBoxW.blockSignals(False)
        self._ui.spinBoxH.blockSignals(True)
        self._ui.spinBoxH.setValue(self._ui.selector.crop.height())
        self._ui.spinBoxH.blockSignals(False)

    @pyqtSlot()
    def reset_crop_values(self):
        self._ui.spinBoxX.setValue(0)
        self._ui.spinBoxY.setValue(0)
        self._ui.spinBoxW.setValue(self._original.width())
        self._ui.spinBoxH.setValue(self._original.height())

    def accept(self):
        x = self._ui.spinBoxX.value()
        y = self._ui.spinBoxY.value()
        width = self._ui.spinBoxW.value()
        height = self._ui.spinBoxH.value()

        cmd_template = ["-crop", f"{width}x{height}+{x}+{y}"]
        print("Crop parameters sent to Process Handler")
        self.commandSignal.emit(cmd_template, self.files, "Crop")
        super().accept()

    def reject(self):
        print("Cropping canceled.")
        super().reject()
