import sys
import Modules.gui as gui
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = gui.App()
    window.showFullScreen()
    # window.show()
    sys.exit(app.exec_())
