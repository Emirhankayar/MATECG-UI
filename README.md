# MATECG-UI
<p align="center">
  <img src="src/icons/appicon.png" alt="App Icon" width="600"/>
</p>

## Installation
### Linux & OSX
```sh
git clone https://github.com/Emirhankayar/MATECG-UI.git
cd MATECG-UI

python3.12 -m venv venv
source venv/bin/activate

chmod +x install.sh
./install.sh
```
### Windows
```sh
git clone https://github.com/Emirhankayar/MATECG-UI.git
cd MATECG-UI

python3.12 -m venv venv

.\venv\Scripts\Activate.ps1

pip install -U pip setuptools wheel
pip install signal-grad-cam tensorflow openpyxl pandas PyQt5 pyqtgraph pyqt-svg-button absresgetter scikit-learn matplotlib
pip uninstall opencv-python
pip cache purge
pip install opencv-python-headless

mkdir src\Data -Force
cd src\Data

pip install gdown

gdown https://drive.google.com/uc?id=1LEl74mH2-VUf7sh7SnTqnR3ZThxzJxSr
gdown https://drive.google.com/uc?id=1z51W9MPZOZB1cIj75OfbM057fTrOHw-2

Expand-Archive -Path "External_Dataset.zip" -DestinationPath ".\External_Dataset"
Expand-Archive -Path "Internal_Dataset.zip" -DestinationPath ".\Internal_Dataset"

cd ../..
python3 main.py

```
## ECG Classification Based Medical Device Prototype
This is the repository for the Medical Device Software Prototype being devoleped by Alessandro Longato, Emirhan Kayar, Lodovico Cabrini, and Libero Biagi, for the Laboratory of Medical Devices and Systems, third year of the Bachelor of Science in Artificial Intelligence (a.y. 2024/2025).

## Our Idea
Our idea is to develop a machine learning software able to detect diffrent kinds of arrhythmia starting from raw ECG data and basic patient information, like age and gender. To complete the medical device, this software should be embedded in a portable ECG scanner, but this is beyond the scope of the laboratory. However, this project still delivers an industrial level application, and the model training software.

## Data
Two distinct datasets are used to evaluate the model's generalization capability. The internal dataset, used for training and internal-testing, is sourced from this paper: [A 12-lead electrocardiogram database for arrhythmia research covering more than 10,000 patients](https://www.nature.com/articles/s41597-020-0386-x). The external dataset (link to be added) is used only for independent validation.

## Preprocessing
Preprocessing involves denoising the signals, time-binning them to a fixed length of 500, casting arrays to float32 and labels to int32, organizing directories, applying min-max scaling, and mapping the labels.

## Model Architecture  
<p align="center">
  <img src="src/Models/architecture.svg" alt="Model Architecture" width="600"/>
</p>

## Final Pipeline
The final prototype integrates the machine learning model into a cross-platform desktop application developed using PyQt5. The application offers a user-friendly graphical interface compatible with Linux, OSX, and Windows. 

### Key functionalities:

#### Data Visualization: 
Display of raw 12-lead ECG signals for each patient.

#### Patient Metadata Display: 
Presentation of basic patient information (e.g., age, gender) and extracted signal features such as heart rate variability metrics.

#### Automated Analysis: 
ECG signals are analyzed using the trained AI model to classify potential arrhythmias.

#### Explainability with Grad-CAM: 
The application provides explainable AI outputs by generating Grad-CAM visualizations over ECG leads, helping to interpret the model’s decision.

#### Results Exporting: 
Classification results and visual explanations can be saved for future review or clinical reporting.

## Citations
### SignalGrad-CAM.
Pe, S., Buonocore, T. M., Nicora, G., & Parimbelli, E. (2025). SignalGrad-CAM (Version 0.0.1) 
https://github.com/bmi-labmedinfo/signal_grad_cam

