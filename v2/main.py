import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from vscode_main_window import VSCodeMainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('/icons/main.png'))
    
    # Check for file argument
    file_to_open = None
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path) and file_path.lower().endswith(('.xlsx', '.xls', '.csv')):
            file_to_open = file_path
    
    window = VSCodeMainWindow(file_to_open=file_to_open)
    window.show()
    sys.exit(app.exec_())