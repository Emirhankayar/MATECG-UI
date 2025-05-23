import pathlib
import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPainter, QImage
import fitz  # pip install PyMuPDF
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from typing import Dict, List, Optional
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QGridLayout,
    QVBoxLayout,
    QWidget,
)
import Modules.constants as constants
from Modules.data_manager import DataManager
from Modules.ecg_plotter import ECGPlotter
from Modules.model_manager import ModelManager


class App(QMainWindow):
    """Main application class"""

    def __init__(self):
        super().__init__()

        # Initialize
        self.data_manager = DataManager()
        self.model_manager = ModelManager(constants.MODELS_DIR)

        self.selected_patient: Optional[str] = None
        self.current_prediction: Optional[int] = None
        self.current_prediction_text: Optional[str] = None

        self.diag_labels: Dict[str, QLabel] = {}
        self.diag_grid_widget: Optional[QWidget] = None

        self._setup_ui()
        self._connect_signals()
        self._load_initial_model()

    def _setup_ui(self):
        self.setWindowTitle("MATE-GUI")
        self.resize(900, 600)

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QHBoxLayout()
        self.central_widget.setLayout(main_layout)

        # Left panel
        left_panel = self._create_left_panel()
        main_layout.addLayout(left_panel, 1)

        # Right panel
        right_panel = self._create_right_panel()
        main_layout.addLayout(right_panel, 3)

    def _create_left_panel(self) -> QVBoxLayout:
        layout = QVBoxLayout()

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search patient id...")
        layout.addWidget(self.search_bar)
        self.search_bar.setEnabled(False)

        # Patient list
        self.patient_list = QListWidget()
        self.patient_list.setAlternatingRowColors(True)
        layout.addWidget(self.patient_list)

        # Control buttons
        controls = self._create_control_buttons()
        layout.addLayout(controls)

        return layout

    def _create_control_buttons(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        font = QFont("FontAwesome", 20)

        buttons_config = [
            ("btn_add", "", "Add Patient"),
            ("btn_remove", "", "Remove Patient"),
            ("btn_save", "", "Save Patient"),
            ("btn_grad", "", "Load GRAD-CAM"),
            ("btn_print", "", "Print/Save as PDF GRAD-CAM"),
        ]

        for attr_name, text, tooltip in buttons_config:
            btn = QPushButton(text)
            btn.setFont(font)
            btn.setToolTip(tooltip)
            setattr(self, attr_name, btn)
            layout.addWidget(btn)

        # Initial states
        self.btn_grad.setEnabled(False)
        self.btn_save.setEnabled(False)
        self.btn_print.setEnabled(False)
        self.btn_remove.setEnabled(False)

        return layout

    def _create_right_panel(self) -> QVBoxLayout:
        layout = QVBoxLayout()

        # Plot widget
        self.plot_graph = pg.PlotWidget()
        self.plotter = ECGPlotter(self.plot_graph)
        layout.addWidget(self.plot_graph)

        # Bottom controls
        bottom_layout = QHBoxLayout()
        layout.addLayout(bottom_layout)

        # Left controls (model selection)
        left_controls = self._create_model_controls()
        bottom_layout.addLayout(left_controls, 2)

        # Right controls (diagnostics)
        right_controls = QVBoxLayout()
        bottom_layout.addLayout(right_controls, 1)

        return layout

    def _create_model_controls(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        # Left side - model selection
        left_side = QVBoxLayout()

        self.model_options = QComboBox()
        self.model_options.addItems(list(self.model_manager.model_paths.keys()))

        self.dropdown_label = QLabel("Loaded Model: --")
        self.model_dir = QLabel("Model Directory: --, --")

        left_side.addWidget(self.model_options)
        left_side.addWidget(self.dropdown_label)
        left_side.addWidget(self.model_dir)

        # Right side - evaluation
        right_side = QVBoxLayout()

        self.btn_eval = QPushButton("Evaluate Patient Data")
        self.prediction_label = QLabel("Prediction: --, --")
        self.true_label = QLabel("True Label Class: --, --\nTrue Label: --, --")

        right_side.addWidget(self.btn_eval)
        right_side.addWidget(self.prediction_label)
        right_side.addWidget(self.true_label)

        layout.addLayout(left_side)
        layout.addLayout(right_side)

        return layout

    def _connect_signals(self):
        # Search and selection
        self.search_bar.textChanged.connect(self._filter_patients)
        self.patient_list.currentItemChanged.connect(self._on_patient_selected)

        # Buttons
        self.btn_add.clicked.connect(self._add_directory)
        self.btn_remove.clicked.connect(self._remove_directories)
        self.btn_save.clicked.connect(self._save_prediction)
        self.btn_eval.clicked.connect(self._evaluate_patient)
        self.btn_grad.clicked.connect(self._load_patient_grad_cam)
        self.btn_print.clicked.connect(self._print_cam_imgs)

        # Model selection
        self.model_options.currentTextChanged.connect(self._on_model_changed)

    def _load_initial_model(self):
        if self.model_options.count() > 0:
            first_model = self.model_options.itemText(0)
            self._load_model(first_model)

    def _filter_patients(self):
        search_text = self.search_bar.text().lower()
        filtered_patients = [
            p for p in self.data_manager.all_patients if search_text in p.lower()
        ]
        self._update_patient_list(filtered_patients)

    def _update_patient_list(self, patients: List[str]):
        self.patient_list.clear()
        for patient in patients:
            self.patient_list.addItem(patient)

    def _update_patient_color(self, patient_name: str, status: str):
        for i in range(self.patient_list.count()):
            item = self.patient_list.item(i)
            if item.text() == patient_name:
                if status == "green":
                    item.setForeground(QColor(0, 128, 0))  # Green
                else:
                    item.setData(Qt.ForegroundRole, None)
                break

    def _on_patient_selected(self):
        selected_item = self.patient_list.currentItem()
        if not selected_item:
            return

        self.selected_patient = selected_item.text()
        self._load_patient_data()
        self._reset_prediction_ui()

    def _load_patient_data(self):
        if not self.selected_patient:
            return

        # Load ECG data
        ecg_data = self.data_manager.get_patient_data(self.selected_patient)
        if ecg_data is None:
            self._show_error(f"Could not load data for patient {self.selected_patient}")
            return

        # Plot ECG signal
        self.plotter.plot_signal(ecg_data)

        # Update labels and diagnostics
        self._update_patient_labels()
        self._update_patient_diagnostics()

    def _update_patient_labels(self):
        true_label = self.data_manager.get_patient_label(self.selected_patient)

        if true_label is not None:
            label_text = self.data_manager.label_map.get(true_label, "Unknown")
            self.true_label.setText(
                f"True Label Class: {true_label}\nTrue Label: {label_text}"
            )
        else:
            self.true_label.setText("True Label Class: --\nTrue Label: --")

    def _update_patient_diagnostics(self):
        diagnostics = self.data_manager.get_patient_diagnostics(self.selected_patient)

        if diagnostics is None:
            return

        # Create/update diagnostics grid if needed
        if not self.diag_grid_widget:
            self._create_diagnostics_grid(list(diagnostics.keys()))

        # Update diagnostic labels
        for col_name, value in diagnostics.items():
            if col_name in self.diag_labels:
                display_value = "--" if pd.isna(value) else str(value)
                self.diag_labels[col_name].setText(
                    f"<b>{col_name}</b>: {display_value}"
                )

        # Enable evaluation if rhythm is missing
        rhythm_missing = pd.isna(diagnostics.get("Rhythm"))
        self.btn_eval.setEnabled(rhythm_missing)
        # Enable grad if grad value is missing
        grad_value = diagnostics.get("Grad")
        grad_ready = grad_value == 1
        grad_missing = grad_value == 0 or pd.isna(grad_value)

        self.btn_grad.setEnabled(grad_missing)

        # Enable print only if grad is ready
        self.btn_print.setEnabled(grad_ready)
        self.btn_print.setToolTip(
            "Grad-CAM ready to print for this patient."
            if grad_ready
            else "Grad-CAM not available."
        )

    def _create_diagnostics_grid(self, columns: List[str]):
        if self.diag_grid_widget:
            self.diag_grid_widget.deleteLater()

        self.diag_grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(15)
        reordered_columns = []
        if "Rhythm" in columns:
            reordered_columns.append("Rhythm")
        reordered_columns.extend(
            [col for col in columns if col not in ("Rhythm", "FileName")]
        )

        self.diag_labels = {}
        cols = 3
        label_index = 0
        for col_name in reordered_columns:
            if col_name == "FileName":
                continue

            label = QLabel(f"<b>{col_name}</b>: --")
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignLeft)

            row, col = label_index // cols, label_index % cols
            grid_layout.addWidget(label, row, col)
            self.diag_labels[col_name] = label

            label_index += 1
        self.diag_grid_widget.setLayout(grid_layout)

        # Add to right panel (find the right controls layout)
        right_panel = self.central_widget.layout().itemAt(1).layout()
        bottom_layout = right_panel.itemAt(1).layout()
        right_controls = bottom_layout.itemAt(1).layout()
        right_controls.addWidget(self.diag_grid_widget)

    def _evaluate_patient(self):
        if not self.selected_patient:
            self._show_warning("No patient selected!")
            return

        # Get patient data
        ecg_data = self.data_manager.get_patient_data(self.selected_patient)
        if ecg_data is None:
            self._show_warning("No patient data loaded!")
            return

        predicted_class = self.model_manager.predict(ecg_data)
        if predicted_class is None:
            self._show_error("Prediction failed!")
            return

        self.current_prediction = predicted_class
        self.current_prediction_text = self.data_manager.label_map.get(
            predicted_class, "Unknown"
        )

        self.prediction_label.setText(
            f"Prediction: {self.current_prediction_text},\n"
            f"Prediction Class: {predicted_class}"
        )

        true_label = self.data_manager.get_patient_label(self.selected_patient)
        color = "green" if predicted_class == true_label else "red"
        self.prediction_label.setStyleSheet(f"color:{color}; font-weight:regular;")

        self.btn_save.setEnabled(True)

    def _load_patient_grad_cam(self):
        if not self.selected_patient:
            self._show_warning("Select the patient first!")
            return

        diagnostics = self.data_manager.get_patient_diagnostics(self.selected_patient)
        rhythm = diagnostics.get("Rhythm") if diagnostics else None

        if pd.isna(rhythm):
            self._show_warning(
                "Rhythm label in diagnostics file is missing.\nPlease evaluate the patient and save the result\nbefore generating Grad-CAM."
            )
            return

        if isinstance(rhythm, int):
            patient_label = rhythm
        else:
            label_map_rev = {v: k for k, v in self.data_manager.label_map.items()}
            patient_label = label_map_rev.get(rhythm)
            if patient_label is None:
                self._show_warning(f"Could not convert Rhythm '{rhythm}' to label.")
                return

        dir_path = pathlib.Path("src/Data/Cams") / self.selected_patient
        dir_path.mkdir(parents=True, exist_ok=True)

        patient_data = self.data_manager.get_patient_data(self.selected_patient)
        if patient_data is None:
            self._show_warning("No patient data loaded!")
            return

        patient_data = self.model_manager._min_max_normalize(patient_data)

        if patient_data.ndim == 3 and patient_data.shape[1] == 1:
            patient_data = np.squeeze(patient_data, axis=1)

        patient_data = np.expand_dims(patient_data, axis=0)

        model = self.model_manager.current_model

        self.patient_list.setEnabled(False)
        self.btn_grad.setEnabled(False)
        self.btn_print.setEnabled(True)
        self.btn_grad.setToolTip("Generating Grad-CAM...")

        self.data_manager.get_patient_grad_cam(
            model, self.selected_patient, patient_data, patient_label, dir_path
        )

        success = self.data_manager.update_patient_grad(self.selected_patient)
        self.patient_list.setEnabled(True)
        self._update_patient_color(self.selected_patient, "green")
        self._update_patient_diagnostics()
        if success:
            self._update_patient_diagnostics()
            self.data_manager.get_patient_cam_imgs(
                dir_path, self.selected_patient, patient_label
            )
            self._show_info("Grad-CAM was successfully generated and Saved as PDF.")
            self.btn_grad.setToolTip("Grad-CAM already available for this patient.")
            self.btn_grad.setEnabled(False)
            self.btn_print.setEnabled(True)
            self.btn_print.setToolTip("Grad-CAM ready to print for this patient.")
        else:
            self._show_error("Failed to generate Grad-CAM!")
            self.btn_grad.setEnabled(True)
            self.btn_print.setEnabled(False)
            self.btn_print.setToolTip(
                "Grad-CAM is not ready to print for this patient."
            )
            self.btn_grad.setToolTip("Grad-CAM generation failed. Click to retry.")

    def _print_cam_imgs(self):
        patient_id = self.selected_patient
        if not patient_id:
            self._show_warning("No patient selected!")
            return

        pdf_path = pathlib.Path("src/Data/Cams") / patient_id / f"{patient_id}.pdf"
        if not pdf_path.exists():
            print(f"PDF not found: {pdf_path}")
            return

        doc = fitz.open(str(pdf_path))

        printer = QPrinter()
        printer.setPageSize(QPrinter.A4)
        printer.setFullPage(True)
        printer.setOutputFormat(QPrinter.NativeFormat)

        dialog = QPrintDialog(printer)
        if dialog.exec_() != QPrintDialog.Accepted:
            print("Print cancelled.")
            return

        painter = QPainter(printer)
        for page_num in range(len(doc)):
            if page_num > 0:
                printer.newPage()

            pix = doc.load_page(page_num).get_pixmap(dpi=300)
            img = QImage(
                pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888
            )
            rect = painter.viewport()
            size = img.size()
            size.scale(rect.size(), aspectMode=1)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(img.rect())
            painter.drawImage(0, 0, img)

        painter.end()
        print(f"Printed PDF: {pdf_path}")

    def _save_prediction(self):
        if not self.selected_patient or not self.current_prediction_text:
            self._show_warning("No prediction to save!")
            return

        success = self.data_manager.update_patient_rhythm(
            self.selected_patient, self.current_prediction_text
        )

        if success:
            self._show_info("Prediction saved successfully!")
            self.btn_save.setEnabled(False)
            self._update_patient_diagnostics()
        else:
            self._show_error("Failed to save prediction!")

    def _add_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Patient Directory", "src/Data/"
        )
        if not directory:
            return

        dir_path = pathlib.Path(directory)
        success, message = self.data_manager.add_directory(dir_path)

        if success:
            self.search_bar.setEnabled(True)
            self._update_patient_list(self.data_manager.all_patients)
            self.btn_add.setEnabled(False)
            self.btn_remove.setEnabled(True)
            self._show_info(message)
        else:
            self._show_error(message)

    def _remove_directories(self):
        if not self.data_manager.mounted_dirs:
            self._show_info("No directories to remove.")
            return

        self.data_manager.clear()
        self._reset_ui()

        self.btn_add.setEnabled(True)
        self.btn_remove.setEnabled(False)
        self.search_bar.setEnabled(False)

        self._show_info(f"Removed the directory.")

    def _on_model_changed(self):
        selected_model = self.model_options.currentText()
        self._load_model(selected_model)
        self._reset_prediction_ui()

    def _load_model(self, model_name: str):
        success = self.model_manager.load_model(model_name)

        if success:
            model_path = self.model_manager.model_paths[model_name]
            self.dropdown_label.setText(f"Loaded Model: {model_name}")
            self.model_dir.setText(f"Model Directory: {model_path}")
        else:
            self._show_error(f"Failed to load model: {model_name}")

    def _reset_prediction_ui(self):
        self.prediction_label.setText("Prediction: --, --")
        self.prediction_label.setStyleSheet("color:black; font-weight:regular;")
        self.btn_save.setEnabled(False)
        self.current_prediction = None
        self.current_prediction_text = None

    def _reset_ui(self):
        self.patient_list.clear()
        self.search_bar.clear()
        self.plot_graph.clear()
        self.true_label.setText("True Label Class: --, --\nTrue Label: --, --")
        self.selected_patient = None

        # Clear diagnostics grid
        if self.diag_grid_widget:
            self.diag_grid_widget.deleteLater()
            self.diag_grid_widget = None
            self.diag_labels.clear()

        self._reset_prediction_ui()

    def _show_error(self, message: str):
        """Show error message"""
        QMessageBox.critical(self, "Error", message)

    def _show_warning(self, message: str):
        """Show warning message"""
        QMessageBox.warning(self, "Warning", message)

    def _show_info(self, message: str):
        """Show info message"""
        QMessageBox.information(self, "Info", message)
