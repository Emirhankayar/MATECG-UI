import os
import sys
import Modules.gui as gui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL)
    app = QApplication(sys.argv)
    window = gui.App()
    # window.showFullScreen()
    window.show()
    sys.exit(app.exec_())
