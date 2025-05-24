import os
from typing import Dict, Optional
import itertools
import pathlib
import numpy as np
import tensorflow as tf
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

class ModelManager:
    """Manages model loading and prediction"""

    def __init__(self, models_dir: str):
        import tensorflow as tf
        self.models_dir = pathlib.Path(models_dir)
        self.model_paths: Dict[str, pathlib.Path] = {}
        self.current_model = None
        self.current_model_name = "--"
        self._load_model_files()

    def _load_model_files(self):
        if not self.models_dir.exists():
            return

        model_files = itertools.chain(
            self.models_dir.glob("*.keras"), self.models_dir.glob("*.h5")
        )

        for model_file in model_files:
            self.model_paths[model_file.stem] = model_file

    def load_model(self, model_name: str) -> bool:
        if model_name not in self.model_paths:
            return False

        try:
            model_path = self.model_paths[model_name]
            self.current_model = tf.keras.models.load_model(model_path)
            self.current_model_name = model_name
            return True
        except Exception:
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
