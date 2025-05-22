import pathlib

"""
FINAL_SIZE = 5000 // DYNAMIC WINDOW SIZE (will be decided according to provided final size.)
(FINAL_SIZE, 12)
"""

FINAL_SIZE = 500

PROJECT_DIR = pathlib.Path("./")

ZIP_PATH = PROJECT_DIR / "Data.zip"
ZIP_CONTENT = PROJECT_DIR / "Data/ECGDataDenoised.zip"
XLSX_PATH = PROJECT_DIR / "Data/Diagnostics.xlsx"
CSV_PATH = PROJECT_DIR / "Data/ECGDataDenoised"
LABEL = PROJECT_DIR / "Data/Label_Map.xlsx"
ZIP_CONTENT_OUTPUT = PROJECT_DIR / "Data/"

"""
 MODELS DIR TO LOAD FOR GUI
"""
MODELS_DIR = PROJECT_DIR / "src/Models"
"""
 DO NOT MODIFY !
 This dict is for our target class
"""
RHY_DICT = {
    "AF": 0,
    "AFIB": 0,
    "SVT": 1,
    "AT": 1,
    "SAAWR": 1,
    "ST": 1,
    "AVNRT": 1,
    "AVRT": 1,
    "SB": 2,
    "SA": 3,
    "SR": 3,
}
