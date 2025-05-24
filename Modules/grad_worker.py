import time
from signal_grad_cam import TfCamBuilder
from PyQt5.QtCore import QRunnable, pyqtSignal, QObject


class GradCamWorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)
    log = pyqtSignal(str)


class GradCamWorker(QRunnable):
    """Worker class for the gradcam, to prevent main loop blocking"""

    def __init__(self, model, patient_id, patient_data, patient_label, dir_path):
        super().__init__()
        self.model = model
        self.patient_id = patient_id
        self.patient_data = patient_data
        self.patient_label = patient_label
        self.dir_path = dir_path
        self.signals = GradCamWorkerSignals()
        self.grad_target_layer_name = ["res_4_conv_2"]
        self.grad_target_classes = [0, 1, 2, 3]
        self.grad_class_labels = [
            "Atrial Fibrillation",
            "Supraventricular Tachycardia",
            "Sinus Bradycardia",
            "Sinus Rhythm",
        ]

    def run(self):
        # This project uses SignalGrad-CAM (Pe et al., 2025)
        # Source: https://github.com/bmi-labmedinfo/signal_grad_cam
        self.signals.log.emit("Starting Grad-CAM generation...")
        start_time = time.time()
        try:

            cam_builder = TfCamBuilder(
                self.model, class_names=self.grad_class_labels, time_axs=0
            )
            cams, predicted_probs_dict, bar_ranges = cam_builder.get_cam(
                self.patient_data,
                data_labels=[self.patient_label],
                target_classes=self.grad_target_classes,
                explainer_types="Grad-CAM",
                target_layers=self.grad_target_layer_name,
                softmax_final=False,
                data_names=self.patient_id,
                data_sampling_freq=50,
                dt=1,
                results_dir_path=self.dir_path,
            )

            comparison_algorithm = "Grad-CAM"
            for i in range(12):
                step_time = time.time()
                self.signals.log.emit(f"Processing Grad-CAM for channel {i + 1}/12...")
                selected_channels_indices = [i]
                results_dir_path = self.dir_path / f"channel_{i}"
                results_dir_path.mkdir(parents=True, exist_ok=True)

                cam_builder.single_channel_output_display(
                    data_list=self.patient_data,
                    data_labels=[self.patient_label],
                    predicted_probs_dict=predicted_probs_dict,
                    cams_dict=cams,
                    explainer_types=comparison_algorithm,
                    target_classes=self.grad_target_classes,
                    target_layers=self.grad_target_layer_name,
                    desired_channels=selected_channels_indices,
                    data_names=self.patient_id,
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
                self.signals.log.emit(
                    f"Step {i + 1} took {time.time() - step_time:.2f} seconds."
                )

            self.signals.log.emit(
                f"Grad-CAM generation completed in {time.time() - start_time:.2f} seconds."
            )
            time.sleep(2)
            self.signals.finished.emit()

        except Exception as e:
            self.signals.error.emit(str(e))
