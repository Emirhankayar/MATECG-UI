#!/bin/bash

set -e

pip install -U pip setuptools wheel
pip install signal-grad-cam tensorflow openpyxl pandas PyQt5 pyqtgraph pyqt-svg-button absresgetter scikit-learn matplotlib fextract
pip uninstall opencv-python
pip cache purge
pip install opencv-python-headless

mkdir -p src/Data
cd src/Data/

pip install gdown fextract

gdown https://drive.google.com/uc?id=1LEl74mH2-VUf7sh7SnTqnR3ZThxzJxSr
gdown https://drive.google.com/uc?id=1z51W9MPZOZB1cIj75OfbM057fTrOHw-2

fextract -x -v External_Dataset.zip
fextract -x -v Internal_Dataset.zip

cd ../..

python3 main.py

