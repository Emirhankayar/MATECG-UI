import sys
import Modules.gui as gui
from PyQt5.QtWidgets import QApplication

# import os

# os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = "/usr/lib64/qt5/plugins/platforms"
# os.environ["QT_QPA_PLATFORM"] = "xcb"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = gui.App()

    # window.showFullScreen()
    window.show()  # if you want not fullscreen
    sys.exit(app.exec_())
