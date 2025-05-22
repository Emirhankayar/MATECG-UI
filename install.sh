#!/bin/bash

set -e


pip install tensorflow
pip install pandas
pip install PyQt5
pip install pyqtgraph
pip install scikit-learn
pip install matplotlib

cd src/Data/

pip install gdown

gdown https://drive.google.com/uc?id=1SKLSjpmsnGic0xtidMs_R_BnKdTwTcUK
gdown https://drive.google.com/uc?id=1APwdgLVZLtK5mKE__uRTWupU_8veZCLZ

unzip *.zip

cd ../..

python3 main.py

