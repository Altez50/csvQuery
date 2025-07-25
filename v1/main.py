import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ui_mainwindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('icons/main.png'))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())