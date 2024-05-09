#!/bin/bash

: '
Just copy paste the command below and place it into your terminal, or call `sh render_blender.sh` from the terminal while modifying the parameters as needed.

If you run this script following will happen:
# 1. 3d images will get downloaded to your PC
# 2. The images will be rendered into 2 images under different lighting conditions

Params:
-- nr_objects - how many 3d objects to download
-- nr_images - nr of images to render for each 3d object
'
alias blender=/Applications/Blender.app/Contents/MacOS/Blender 

blender --python-use-system-env -b -P blender_script.py -- \
        --nr_objects 100 \
        --nr_images 8 \
        --engine CYCLES \
        --scale 0.8 \
        --camera_dist 1.2  \
        --img_resolution 512