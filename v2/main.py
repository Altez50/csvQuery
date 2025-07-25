import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from vscode_main_window import VSCodeMainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('../icons/main.png'))
    window = VSCodeMainWindow()
    window.show()
    sys.exit(app.exec_())