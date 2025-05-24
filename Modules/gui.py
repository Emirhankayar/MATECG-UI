import sys
import pathlib
import subprocess
import webbrowser
import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt5.QtCore import Qt
from functools import partial
from PyQt5.QtGui import QColor, QIcon
from typing import Dict, List, Optional

from PyQt5.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QGridLayout,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import QThreadPool

from pyqt_svg_button.svgButton import SvgButton

from Modules.data_manager import DataManager
from Modules.ecg_plotter import ECGPlotter
from Modules.model_manager import ModelManager
from Modules.grad_worker import GradCamWorker
from Modules.loading_dial import LoadingDialog


class App(QMainWindow):
    """Main application class"""

    def __init__(self):
        super().__init__()
        self.threadpool = QThreadPool()
        self.data_manager = DataManager()
        self.model_manager = ModelManager(
            str(pathlib.Path.cwd() / pathlib.Path("src/Models").resolve())
        )

        self.selected_patient: Optional[str] = None
        self.current_prediction: Optional[int] = None
        self.current_prediction_text: Optional[str] = None

        self.diag_labels: Dict[str, QLabel] = {}
        self.diag_grid_widget: Optional[QWidget] = None

        self._setup_ui()
        self._connect_signals()
        self._load_initial_model()

    def _setup_ui(self):
        icon = str(pathlib.Path.cwd() / "src" / "icons" / "appicon.png")

        self.setWindowIcon(QIcon(icon))

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

        buttons_config = [
            ("btn_add", "add.svg", "Add directory."),
            ("btn_remove", "remove.svg", "Remove current directory."),
            ("btn_save", "save.svg", "Save patient rhythm data."),
            ("btn_grad", "grad.svg", "Generate patient GRAD-CAM data"),
            ("btn_view", "view.svg", "View generated patient Grad-CAM data as PDF"),
            ("btn_eval", "eval.svg", "Predict patient rhythm data."),
        ]

        for attr_name, icon_filename, tooltip in buttons_config:
            icon_path = str(pathlib.Path.cwd() / "src" / "icons" / icon_filename)

            btn = SvgButton(self)
            btn.setIcon(icon_path)
            btn.setToolTip(tooltip)
            btn.setFixedSize(40, 40)
            setattr(self, attr_name, btn)
            layout.addWidget(btn)

        # Initial states
        self.btn_grad.setEnabled(False)
        self.btn_save.setEnabled(False)
        self.btn_eval.setEnabled(False)
        self.btn_view.setEnabled(False)
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
        bottom_layout.addLayout(left_controls, 1)

        # Right controls (diagnostics)
        right_controls = QVBoxLayout()
        bottom_layout.addLayout(right_controls, 3)

        return layout

    def _create_model_controls(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        # Left side - model selection
        left_side = QVBoxLayout()

        self.model_options = QComboBox()
        available_models = self.model_manager.get_available_models()
        self.model_options.addItems(available_models)

        self.dropdown_label = QLabel(
            f"<b>Model Information</b><br>" f"Name: --, --<br>" f"Dir: --, --"
        )

        left_side.addWidget(self.model_options)
        left_side.addWidget(self.dropdown_label)

        self.prediction_label = QLabel(
            f"<b>Prediction Information</b><br>" f"Class: --, --<br>" f"Name: --, --"
        )
        self.true_label = QLabel(
            f"<b>Label Information</b><br>" f"Class: --, --<br>" f"Name: --, --"
        )
        left_side.addWidget(self.prediction_label)
        left_side.addWidget(self.true_label)
        layout.addLayout(left_side)

        return layout

    def _connect_signals(self):
        self.search_bar.textChanged.connect(self._filter_patients)
        self.patient_list.currentItemChanged.connect(self._on_patient_selected)

        # Buttons
        self.btn_add.clicked.connect(self._add_directory)
        self.btn_remove.clicked.connect(self._remove_directories)
        self.btn_save.clicked.connect(self._save_prediction)
        self.btn_eval.clicked.connect(self._evaluate_patient)
        self.btn_grad.clicked.connect(self._load_patient_grad_cam)
        self.btn_view.clicked.connect(self._open_cam_pdf_external)

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
                    item.setForeground(QColor(0, 128, 0))
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
        self._update_patient_labels()
        self._update_patient_diagnostics()

    def _update_patient_labels(self):
        true_label = self.data_manager.get_patient_label(self.selected_patient)
        self.btn_eval.setEnabled(True)
        if true_label is not None:
            label_text = self.data_manager.label_map.get(true_label, "Unknown")
            self.true_label.setText(
                f"<b>Label Information</b><br>"
                f"Class: {true_label}<br>"
                f"Name: {label_text}"
            )
        else:
            self.true_label.setText(
                f"<b>Label Information</b><br>" f"Class: --, --<br>" f"Name: --, --"
            )

    def _update_patient_diagnostics(self):
        diagnostics = self.data_manager.get_patient_diagnostics(self.selected_patient)

        if diagnostics is None:
            return

        if not self.diag_grid_widget:
            self._create_diagnostics_grid(list(diagnostics.keys()))

        for col_name, value in diagnostics.items():
            if col_name in self.diag_labels:
                display_value = "--" if pd.isna(value) else str(value)
                self.diag_labels[col_name].setText(
                    f"<b>{col_name}</b>: {display_value}"
                )

        # Enable evaluation if rhythm is missing
        # Enable grad if grad value is missing
        rhythm_missing = pd.isna(diagnostics.get("Rhythm"))
        self.btn_eval.setEnabled(rhythm_missing)
        grad_value = diagnostics.get("Grad")
        grad_ready = grad_value == 1
        grad_missing = grad_value == 0 or pd.isna(grad_value)
        self.btn_grad.setEnabled(grad_missing)
        self.btn_view.setEnabled(grad_ready)
        self.btn_view.setToolTip(
            "Grad-CAM ready to print for this patient."
            if grad_ready
            else "Grad-CAM not available."
        )

    def _create_diagnostics_grid(self, columns: List[str]):
        if self.diag_grid_widget:
            self.diag_grid_widget.deleteLater()

        self.diag_grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(5, 40, 0, 0)
        grid_layout.setSpacing(15)
        grid_layout.setVerticalSpacing(30)
        reordered_columns = []
        if "Rhythm" in columns:
            reordered_columns.append("Rhythm")
        reordered_columns.extend(
            [col for col in columns if col not in ("Rhythm", "FileName")]
        )

        self.diag_labels = {}
        cols = 6
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
        right_panel = self.central_widget.layout().itemAt(1).layout()
        bottom_layout = right_panel.itemAt(1).layout()
        right_controls = bottom_layout.itemAt(1).layout()
        right_controls.addWidget(self.diag_grid_widget)

    def _evaluate_patient(self):
        if not self.selected_patient:
            self._show_warning("No patient selected!")
            return

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
            f"<b>Prediction Information</b><br>"
            f"Class: {predicted_class}<br>"
            f"Name: {self.current_prediction_text}"
        )

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

        dir_path = pathlib.Path("src") / "Data" / "Cams" / self.selected_patient

        dir_path.mkdir(parents=True, exist_ok=True)

        patient_data = self.data_manager.get_patient_data(self.selected_patient)
        if patient_data is None:
            self._show_warning("No patient data loaded!")
            return

        patient_data = self.model_manager._min_max_normalize(patient_data)

        if patient_data.ndim == 3 and patient_data.shape[1] == 1:
            patient_data = np.squeeze(patient_data, axis=1)

        patient_data = np.expand_dims(patient_data, axis=0)

        worker = GradCamWorker(
            model=self.model_manager.current_model,
            patient_id=self.selected_patient,
            patient_data=patient_data,
            patient_label=patient_label,
            dir_path=dir_path,
        )
        worker.signals.finished.connect(partial(self._on_grad_cam_finished, worker))
        worker.signals.error.connect(partial(self._on_grad_cam_error, worker))

        self.patient_list.setEnabled(False)
        self.btn_grad.setEnabled(False)
        self.btn_view.setEnabled(False)
        self.loading_dialog = LoadingDialog(parent=self)
        worker.signals.log.connect(self.loading_dialog.append_log)
        worker.signals.finished.connect(self.loading_dialog.accept)
        worker.signals.error.connect(
            lambda msg: self.loading_dialog.append_log(f"ERROR: {msg}")
        )

        self.loading_dialog.show()
        self.threadpool.start(worker)

    def _on_grad_cam_finished(self, worker):
        patient_id = worker.patient_id
        patient_label = worker.patient_label
        dir_path = worker.dir_path
        self._update_patient_color(patient_id, "green")
        self.data_manager.update_patient_grad(patient_id)
        self._update_patient_diagnostics()

        self.data_manager.get_patient_cam_imgs(dir_path, patient_id, patient_label)
        self.btn_grad.setToolTip("Grad-CAM already available for this patient.")
        self.btn_view.setToolTip("Grad-CAM ready to print for this patient.")

        self.patient_list.setEnabled(True)
        self.btn_grad.setEnabled(False)
        self.btn_view.setEnabled(True)

    def _on_grad_cam_error(self, error_msg):
        self._show_error(f"Grad-CAM generation failed: {error_msg}")
        self.patient_list.setEnabled(True)
        self.btn_grad.setEnabled(True)

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
        default_dir = str(pathlib.Path("src") / "Data")
        directory = QFileDialog.getExistingDirectory(
            self, "Select Patient Directory", default_dir
        )
        if not directory:
            return

        dir_path = pathlib.Path(directory).resolve()
        success = self.data_manager.add_directory(dir_path)

        if success:
            self.search_bar.setEnabled(True)
            self._update_patient_list(self.data_manager.all_patients)
            self.btn_add.setEnabled(False)
            self.btn_remove.setEnabled(True)
        else:
            self._show_error("Failed to add directory.")

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
            model_path = self.model_manager.model_paths.get(model_name.lower())
            model_path = model_path.relative_to(pathlib.Path.cwd())
            self.dropdown_label.setText(
                f"<b>Model Information</b><br>"
                f"Name: {model_name}<br>"
                f"Dir: {model_path}"
            )
        else:
            self._show_error(f"Failed to load model: {model_name}")

    def _reset_prediction_ui(self):
        self.prediction_label.setText(
            f"<b>Prediction Information</b><br>" f"Class: --, --<br>" f"Name: --, --"
        )
        self.btn_save.setEnabled(False)
        self.current_prediction = None
        self.current_prediction_text = None

    def _reset_ui(self):
        self.patient_list.clear()
        self.search_bar.clear()
        self.plot_graph.clear()
        self.true_label.setText(
            f"<b>Label Information</b><br>" f"Class: --, --<br>" f"Name: --, --"
        )
        self.selected_patient = None

        # Clear diagnostics grid
        if self.diag_grid_widget:
            self.diag_grid_widget.deleteLater()
            self.diag_grid_widget = None
            self.diag_labels.clear()

        self._reset_prediction_ui()

    def get_native_os(self, pdf_path: pathlib.Path):
        """use native OS app to view the pdf"""
        """
            placed a fallback, if the OS does not have native app
            it runs the pdf in the browser NOT SURE IF GONNA WORK
        """
        pdf_path = str(pdf_path.resolve())

        try:
            if sys.platform.startswith == "win":
                import os

                os.startfile(pdf_path)
                return True
            elif sys.platform.startswith == "darwin":
                subprocess.run(["open", str(pdf_path)], check=True)
                return True

            elif sys.platform.startswith("linux"):
                subprocess.run(["xdg-open", str(pdf_path)], check=True)
                return True

            else:
                webbrowser.open(pdf_path.as_uri())
        except Exception as e:
            print(f"Failed to open file with system app")
            return False

    def _open_cam_pdf_external(self):
        patient_id = self.selected_patient
        if not patient_id:
            self._show_warning("No patient selected!")
            return

        pdf_path = (
            pathlib.Path("src") / "Data" / "Cams" / patient_id / f"{patient_id}.pdf"
        )

        if not pdf_path.exists():
            self._show_error("Grad-CAM PDF not found!")
            return

        try:
            self.get_native_os(pdf_path)
        except Exception as e:
            self._show_error(f"Failed to open PDF: {e}")

    def _show_error(self, message: str):
        """Show error message"""
        QMessageBox.critical(self, "Error", message)

    def _show_warning(self, message: str):
        """Show warning message"""
        QMessageBox.warning(self, "Warning", message)

    def _show_info(self, message: str):
        """Show info message"""
        QMessageBox.information(self, "Info", message)
