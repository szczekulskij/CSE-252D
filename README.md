# CSE-252D

## Requirements
- Python 3.10.8


## M2 mac book
For M2 mac book make sure to install pytorch via miniforge (conda) to enable GPU (macbook metal) support. 
Seperate requirements.txt is provided for M2 mac book (`requirements_m2.txt`)

# Rendering images (eg creating dataset in form (image.png, label.txt) for each objet in blender)
* *Running: `cd objaverse-rendering && sh render_blender.sh` - this by default will create dir `objaverse-rendering/objaverse_data` and save images & labels there (look into objaverse_download.py for path details)
* Currentely hard-coded only to download objects from specific categories (eg. chair, table, sofa, etc) - can be changed in `objaverse_download.py`
* The script will (1) download glp objects from given categories; (2) render images for each object; (3) save images & labels in `objaverse-rendering/objaverse_data`; (4) delete downloaded glb objects (to save space)
* Instructions for setting up the script to run can be found in README.md in `objaverse-rendering` directory. Code should be straight forward to understand and modify as needed.