import pathlib
import numpy as np
import pandas as pd
from PIL import Image
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

        row = patient_row.iloc[0]

        return row.to_dict()

    def update_patient_diagnostic_field(
        self, patient_id: str, field: str, value
    ) -> bool:
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
            diag_df.loc[idx, field] = value
            diag_df.to_excel(diag_path, index=False)
            return True
        except Exception:
            return False

    def update_patient_rhythm(self, patient_id: str, predicted_rhythm: str) -> bool:
        return self.update_patient_diagnostic_field(
            patient_id, "Rhythm", predicted_rhythm
        )

    def update_patient_grad(self, patient_id: str, value: int = 1) -> bool:
        return self.update_patient_diagnostic_field(patient_id, "Grad", value)

    def get_patient_grad_status(self, patient_id: str) -> Optional[int]:
        if patient_id not in self.patient_dir_map:
            return None

        dir_path = self.patient_dir_map[patient_id]
        diag_df = self.diagnostics_map.get(dir_path)

        if diag_df is None or diag_df.empty:
            return None

        patient_row = diag_df[diag_df["FileName"] == patient_id]
        if patient_row.empty:
            return None

        if "Grad" not in diag_df.columns:
            return None

        grad_value = patient_row["Grad"].iloc[0]

        if grad_value == 1:
            return 1
        elif grad_value == 0:
            return 0
        else:
            return None

    def get_patient_cam_imgs(
        self, dir_path: pathlib.Path, patient_id: str, target_class: int
    ) -> Optional[List[pathlib.Path]]:
        cam_path = dir_path

        channels = {
            p.name
            for p in cam_path.iterdir()
            if p.is_dir() and p.name.startswith("channel_")
        }
        if channels != {f"channel_{i}" for i in range(12)}:
            print("Missing some channel directories.")
            return None

        images = []
        for i in range(12):
            channel_dir = cam_path / f"channel_{i}"
            imgs = list(channel_dir.rglob(f"*class{target_class}.png"))
            if not imgs:
                print(f"Missing image in {channel_dir} for class {target_class}")
                return None
            images.append(imgs[0])

        self.save_cam_imgs_as_pdf(images, patient_id, dir_path.parent)
        return images

    def save_cam_imgs_as_pdf(
        self, image_paths: List[pathlib.Path], patient_id: str, output_dir: pathlib.Path
    ):
        pil_images = [Image.open(str(path)).convert("RGB") for path in image_paths]
        pdf_path = output_dir / patient_id / f"{patient_id}.pdf"
        pil_images[0].save(
            pdf_path,
            save_all=True,
            append_images=pil_images[1:],
            resolution=300,
            quality=95,
        )
        print(f"Saved PDF to: {pdf_path}")

    def clear(self):
        self.all_patients.clear()
        self.patient_dir_map.clear()
        self.label_map_dfs.clear()
        self.diagnostics_map.clear()
        self.diagnostics_file_map.clear()
        self.mounted_dirs.clear()
