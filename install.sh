#!/bin/bash

set -e


pip install tensorflow
pip install signal-grad-cam
pip install openpyxl
pip install pandas
pip install PyQt5
pip install pyqtgraph
pip install pyqt-svg-button
pip install absresgetter
pip install scikit-learn
pip install matplotlib

mkdir -p src/Data
cd src/Data/

pip install gdown

gdown https://drive.google.com/uc?id=14wejH07V4TiktA6WkpqACbwng66IVcgt
gdown https://drive.google.com/uc?id=1h8L52fI3sTAhSSUkBu0Ku5VdsEwPhIYS

unzip Internal_Dataset.zip
unzip External_Dataset.zip


cd ../..

python3 main.py

