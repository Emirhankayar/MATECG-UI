from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QTextEdit,
    QApplication,
)


class LoadingDialog(QDialog):
    """Minimalistic loading dialog"""

    def __init__(self, title="Processing...", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout()
        self.label = QLabel("Grad-CAM images are being generated...")
        layout.addWidget(self.label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        layout.addWidget(self.progress)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def append_log(self, text: str):
        self.log_output.append(text)
        QApplication.processEvents()
