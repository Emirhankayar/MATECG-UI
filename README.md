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

gdown https://drive.google.com/uc?id=14wejH07V4TiktA6WkpqACbwng66IVcgt
gdown https://drive.google.com/uc?id=1h8L52fI3sTAhSSUkBu0Ku5VdsEwPhIYS

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
--TO BE ADDED--
- Preparing the Application (plugging the data, model)

@software{Pe_SignalGrad_CAM_2025,
  author = {Pe, Samuele and Buonocore, Tommaso Mario and Giovanna, Nicora and Enea, Parimbelli},
  title = {{SignalGrad-CAM}},
  url = {https://github.com/bmi-labmedinfo/signal_grad_cam},
  version = {0.0.1},
  year = {2025}
}
This code uses SignalGrad-CAM.
Pe, S., Buonocore, T. M., Nicora, G., & Parimbelli, E. (2025). SignalGrad-CAM (Version 0.0.1) 
https://github.com/bmi-labmedinfo/signal_grad_cam

