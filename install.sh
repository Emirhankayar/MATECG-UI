#!/bin/bash

set -e

git clone https://github.com/Emirhankayar/MATECG-UI.git
cd MATECG-UI

python3.11 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cd src/Data/

pip install gdown

gdown https://drive.google.com/uc?id=FILE_ID_1
gdown https://drive.google.com/uc?id=FILE_ID_2

unzip *.zip

cd ../..

python3 main.py

