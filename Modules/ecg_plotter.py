import numpy as np
import pyqtgraph as pg
import sklearn.preprocessing as preprocessing


class ECGPlotter:
    def __init__(self, plot_widget: pg.PlotWidget):
        self.plot_widget = plot_widget
        self.scaler = preprocessing.MinMaxScaler(feature_range=(-1, 1))

    def plot_signal(self, data: np.ndarray):
        self.plot_widget.clear()

        # Normalize x and y values for better appearence
        x_values = np.arange(data.shape[0]).reshape(-1, 1)
        x_normalized = self.scaler.fit_transform(x_values).flatten()

        y_values = data[:, 0].reshape(-1, 1)
        y_normalized = self.scaler.fit_transform(y_values).flatten()

        self.plot_widget.setYRange(-1.5, 1.5)
        self.plot_widget.plot(
            x_normalized, y_normalized, pen="g", width=1.5, name="ECG Signal"
        )
