import logging as log

from PyQt5.QtWidgets import QWidget, QLabel, QRubberBand
from PyQt5.QtGui import QPainter, QBrush, QColor, QPalette, QPen
from PyQt5.QtCore import QRect, QSize, QPoint, QMargins, pyqtSignal, Qt


def exclude(outer, inner):
    """
    :param outer: the external rectangle as a QRect object
    :param inner: the inner rectangle as a QRect object
    :return: a tuple of four QRect objecs, representing the frame of the inner rect
        +----+--------------+--------+
        | 11 | 222222222222 | 444444 |
        | 11 +--------------+ 444444 |
        | 11 |              | 444444 |
        | 11 |              | 444444 |
        | 11 |              | 444444 |
        | 11 +--------------+ 444444 |
        | 11 | 333333333333 | 444444 |
        | 11 | 333333333333 | 444444 |
        +----+--------------+--------+
    """
    # just in case the inner rect goes beyond the outer limits
    log.debug('OUTER:')
    log.debug(outer)
    log.debug('INNER:')
    log.debug(inner)
    inner = outer.intersected(inner)
    areas = (
        QRect(outer.left(),     outer.top(),        inner.left(),                   outer.height()),
        QRect(inner.left(),     outer.top(),        inner.width(),                  inner.top()),
        QRect(inner.left(),     inner.bottom()+1,   inner.width(),                  outer.height()-inner.bottom()-1),
        QRect(inner.right()+1,  outer.top(),        outer.width()-inner.right()+1,  outer.height())
    )
    log.debug('AREAS:')
    log.debug(areas)
    return areas


class AreaSelector(QLabel):
    area_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.crop = QRect(0, 0, 0, 0)
        # parent is the QFrame, its parent is the Workspace
        parent.parent().selector = self

    def paintEvent(self, event):
        super().paintEvent(event)

        qp = QPainter(self)
        qp.setBrush(QBrush(QColor(0, 0, 0, 200)))
        qp.setPen(Qt.NoPen)

        for r in exclude(self.geometry().translated(-1, -1), self.crop):
            qp.drawRect(r)


class Workspace(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._rubberband = None
        self._origin = None
        self.selector = None

        p = QPalette()
        p.setColor(QPalette.Background, Qt.black)
        self.setPalette(p)

    def mousePressEvent(self, event):
        if not self._rubberband:
            self._rubberband = QRubberBand(QRubberBand.Rectangle, self)
        self._origin = event.pos()
        self.selector.crop = QRect(QPoint(0, 0), self.selector.geometry().size())
        self.repaint()
        self._rubberband.setGeometry(QRect(self._origin, QSize()))
        self._rubberband.show()

    def mouseMoveEvent(self, event):
        selection = QRect(self._origin, event.pos()).normalized()
        self._rubberband.setGeometry(selection)

    def mouseReleaseEvent(self, event):
        selection = QRect(self._origin, event.pos()).normalized()
        fullimage = self.selector.parent().geometry() - QMargins(1, 1, 1, 1)
        self.selector.crop = selection.intersected(fullimage).translated(-fullimage.topLeft())
        self._rubberband.setGeometry(selection)
        self._rubberband.hide()
        self.repaint()
        self.selector.area_changed.emit()
