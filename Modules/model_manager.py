import os
from typing import Dict, Optional
import itertools
import pathlib
import numpy as np
import tensorflow as tf

# Set TensorFlow logging before importing
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


class ModelManager:
    """Manages model loading and prediction"""

    def __init__(self, models_dir: str):
        # Convert string path to pathlib.Path and resolve it
        self.models_dir = pathlib.Path(models_dir).resolve()
        self.model_paths: Dict[str, pathlib.Path] = {}
        self.current_model = None
        self.current_model_name = "--"
        self._load_model_files()

    def _load_model_files(self):
        if not self.models_dir.exists():
            print(f"Models directory does not exist: {self.models_dir}")
            return

        model_files = itertools.chain(
            self.models_dir.glob("*.keras"),
            self.models_dir.glob("*.h5"),
            self.models_dir.glob("*.KERAS"),
            self.models_dir.glob("*.H5"),
        )

        for model_file in model_files:
            model_key = model_file.stem.lower()
            if model_key not in self.model_paths:
                self.model_paths[model_key] = model_file

    def get_available_models(self) -> list[str]:
        """Get list of available model names"""
        return list(self.model_paths.keys())

    def load_model(self, model_name: str) -> bool:
        model_key = model_name.lower()
        if model_key not in self.model_paths:
            return False

        try:
            model_path = self.model_paths[model_key]
            if not model_path.exists():
                print(f"Model file no longer exists: {model_path}")
                return False

            self.current_model = tf.keras.models.load_model(str(model_path))
            self.current_model_name = model_name
            return True
        except Exception as e:
            print(f"Failed to load model {model_name}: {e}")
            return False

    def predict(self, data: np.ndarray) -> Optional[int]:
        if self.current_model is None:
            return None

        try:
            normalized_data = self._min_max_normalize(data)
            input_data = np.expand_dims(normalized_data, axis=0)
            prediction = self.current_model.predict(input_data, verbose=0)
            return int(np.argmax(prediction))
        except Exception:
            return None

    @staticmethod
    def _min_max_normalize(data: np.ndarray) -> np.ndarray:
        min_val, max_val = np.min(data), np.max(data)
        if max_val - min_val == 0:
            return np.zeros_like(data, dtype=np.float32)
        return ((data - min_val) / (max_val - min_val)).astype(np.float32)
