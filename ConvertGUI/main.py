import sys
from PyQt5.QtWidgets import QApplication
from gui.mainwindow import MainWindow
from resources import icons_rc


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
