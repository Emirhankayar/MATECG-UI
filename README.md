# Installation
## Linux & OSX
```sh
git clone https://github.com/Emirhankayar/MATECG-UI.git
cd MATECG-UI

# Use python 3.11
python3.11 -m venv venv
source venv/bin/activate

chmod +x install.sh
./install.sh
```

# ECG Classification Based Medical Device Prototype
This is the repository for the Medical Device Software Prototype being devoleped by Alessandro Longato, Emirhan Kayar, Lodovico Cabrini, and Libero Biagi, for the Laboratory of Medical Devices and Systems, third year of the Bachelor of Science in Artificial Intelligence (a.y. 2024/2025).

## Our Idea
Our idea is to develop a machine learning software able to detect diffrent kinds of arrhythmia starting from raw ECG data and basic patient information, like age and gender. To complete the medical device, this software should be embedded in a portable ECG scanner, but this is beyond the scope of the laboratory. However, this project still delivers an industrial level application, and the model training software.

## Data
The data used for training is from this paper: [A 12-lead electrocardiogram database for arrhythmia research covering more than 10,000 patients](https://www.nature.com/articles/s41597-020-0386-x)

## Model Architecture
Resnet
--Add image here--

## Final Pipeline
--TO BE ADDED--
- Obtaining the data
- Preprocessing
- Choosing the model architecture
- Training the model, customization
- Preparing the Application (plugging the data, model)
- Testing


