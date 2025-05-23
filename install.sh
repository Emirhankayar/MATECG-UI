#!/bin/bash

set -e

pip install -U pip setuptools wheel
pip install signal-grad-cam tensorflow openpyxl pandas PyQt5 pyqtgraph pyqt-svg-button absresgetter scikit-learn matplotlib
pip uninstall opencv-python
pip cache purge
pip install opencv-python-headless

mkdir -p src/Data
cd src/Data/

pip install gdown

gdown https://drive.google.com/uc?id=14wejH07V4TiktA6WkpqACbwng66IVcgt
gdown https://drive.google.com/uc?id=1h8L52fI3sTAhSSUkBu0Ku5VdsEwPhIYS

unzip Internal_Dataset.zip
unzip External_Dataset.zip


cd ../..

python3 main.py

