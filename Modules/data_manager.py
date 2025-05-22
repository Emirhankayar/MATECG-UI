import pathlib
import numpy as np
import pandas as pd
from signal_grad_cam import TfCamBuilder
from typing import Dict, List, Optional


class DataManager:
    """Manages patient data, labels, and diagnostics"""

    def __init__(self):
        self.all_patients: List[str] = []
        self.patient_dir_map: Dict[str, pathlib.Path] = {}
        self.label_map_dfs: Dict[pathlib.Path, pd.DataFrame] = {}
        self.diagnostics_map: Dict[pathlib.Path, pd.DataFrame] = {}
        self.diagnostics_file_map: Dict[pathlib.Path, pathlib.Path] = {}
        self.mounted_dirs: List[pathlib.Path] = []
        self.label_map = {
            0: "Atrial Fibrillation (AFIB)",
            1: "Generic Supraventricular Tachycardia (GSVT)",
            2: "Sinus Bradycardia (SB)",
            3: "Sinus Rhythm (SR)",
        }
        self.grad_target_layer_name = ["res_4_conv_2"]
        self.grad_target_classes = [0, 1, 2, 3]
        self.grad_class_labels = [
            "Atrial Fibrillation",
            "Supraventricular Tachycardia",
            "Sinus Bradycardia",
            "Sinus Rhythm",
        ]

    def add_directory(self, dir_path: pathlib.Path) -> tuple[bool, str]:
        if dir_path in self.mounted_dirs:
            return False, f"Directory '{dir_path}' already added"

        label_success, label_msg = self._load_label_map(dir_path)
        if not label_success:
            return False, label_msg

        self._load_diagnostics(dir_path)

        patient_files = list(dir_path.glob("*.csv"))
        if not patient_files:
            return False, "No .csv files found in directory"

        new_patients = []
        for file in patient_files:
            patient_name = file.stem
            if patient_name not in self.patient_dir_map:
                new_patients.append(patient_name)
                self.patient_dir_map[patient_name] = dir_path

        self.all_patients.extend(new_patients)
        self.all_patients = sorted(set(self.all_patients))
        self.mounted_dirs.append(dir_path)

        return True, f"Added {len(new_patients)} patients"

    def _load_label_map(self, dir_path: pathlib.Path) -> tuple[bool, str]:
        label_path = dir_path / "Label_Map.xlsx"
        if not label_path.exists():
            return False, f"Label map not found at {label_path}"

        try:
            label_df = pd.read_excel(label_path)
            self.label_map_dfs[dir_path] = label_df
            return True, "Label map loaded successfully"
        except Exception as e:
            return False, f"Failed to load label map: {e}"

    def _load_diagnostics(self, dir_path: pathlib.Path):
        diag_path = dir_path / "Diagnostics.xlsx"
        if diag_path.exists():
            try:
                diag_df = pd.read_excel(diag_path)
                self.diagnostics_map[dir_path] = diag_df
                self.diagnostics_file_map[dir_path] = diag_path
            except Exception as e:
                print(f"Failed to load diagnostics from {diag_path}: {e}")

    def get_patient_data(self, patient_id: str) -> Optional[np.ndarray]:
        if patient_id not in self.patient_dir_map:
            return None

        data_path = self.patient_dir_map[patient_id] / f"{patient_id}.csv"
        if not data_path.exists():
            return None

        try:
            df = pd.read_csv(data_path, header=None)
            return df.to_numpy()
        except Exception:
            return None

    def get_patient_label(self, patient_id: str) -> Optional[int]:
        if patient_id not in self.patient_dir_map:
            return None

        dir_path = self.patient_dir_map[patient_id]
        label_df = self.label_map_dfs.get(dir_path)

        if label_df is None or label_df.empty:
            return None

        patient_row = label_df[label_df["FileName"] == patient_id]
        if patient_row.empty:
            return None

        return int(patient_row["Rhythm"].iloc[0])

    def get_patient_diagnostics(self, patient_id: str) -> Optional[Dict]:
        if patient_id not in self.patient_dir_map:
            return None

        dir_path = self.patient_dir_map[patient_id]
        diag_df = self.diagnostics_map.get(dir_path)

        if diag_df is None or diag_df.empty:
            return None

        patient_row = diag_df[diag_df["FileName"] == patient_id]
        if patient_row.empty:
            return None

        return patient_row.drop(columns=["FileName"]).iloc[0].to_dict()

    def update_patient_rhythm(self, patient_id: str, predicted_rhythm: str) -> bool:
        if patient_id not in self.patient_dir_map:
            return False

        dir_path = self.patient_dir_map[patient_id]
        diag_df = self.diagnostics_map.get(dir_path)
        diag_path = self.diagnostics_file_map.get(dir_path)

        if diag_df is None or diag_path is None:
            return False

        idx = diag_df.index[diag_df["FileName"] == patient_id]
        if idx.empty:
            return False

        try:
            diag_df.loc[idx, "Rhythm"] = predicted_rhythm
            diag_df.to_excel(diag_path, index=False)
            return True
        except Exception:
            return False

    def get_patient_grad_cam(
        self,
        model,
        patient_id: str,
        patient_data: np.float32,
        patient_label: np.int32,
        dir_path: pathlib.Path,
    ):

        cam_builder = TfCamBuilder(
            model, class_names=self.grad_class_labels, time_axs=0
        )
        cams, predicted_probs_dict, bar_ranges = cam_builder.get_cam(
            patient_data,
            data_labels=[patient_label],
            target_classes=self.grad_target_classes,
            explainer_types="Grad-CAM",
            target_layers=self.grad_target_layer_name,
            softmax_final=False,
            data_names=patient_id,
            data_sampling_freq=50,
            dt=1,
            results_dir_path=dir_path,
        )

        # Explain different input channels
        comparison_algorithm = "Grad-CAM"
        for i in range(12):
            selected_channels_indices = [i]
            results_dir_path = dir_path / f"channel_{i}"
            results_dir_path.mkdir(parents=True, exist_ok=True)

            cam_builder.single_channel_output_display(
                data_list=patient_data,
                data_labels=[patient_label],
                predicted_probs_dict=predicted_probs_dict,
                cams_dict=cams,
                explainer_types=comparison_algorithm,
                target_classes=self.grad_target_classes,
                target_layers=self.grad_target_layer_name,
                desired_channels=selected_channels_indices,
                data_names=patient_id,
                fig_size=(20, 10),
                grid_instructions=(1, len(selected_channels_indices)),
                bar_ranges_dict=bar_ranges,
                results_dir_path=results_dir_path,
                data_sampling_freq=50,
                dt=1,
                line_width=0.5,
                marker_width=30,
                axes_names=(None, None),
            )

    def clear(self):
        self.all_patients.clear()
        self.patient_dir_map.clear()
        self.label_map_dfs.clear()
        self.diagnostics_map.clear()
        self.diagnostics_file_map.clear()
        self.mounted_dirs.clear()
