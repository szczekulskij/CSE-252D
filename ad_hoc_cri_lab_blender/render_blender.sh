#!/bin/bash

alias blender=/Applications/Blender.app/Contents/MacOS/Blender # pointer to blender executable

# 1. Set following variables
filename=""  # path to 3d object file
num_images=10
img_resolution=256
image_path= "~/Desktop/blender_output"

# 2. If image path does not exist, create it
if [ ! -d "$image_path" ]; then
    mkdir -p $image_path
fi

# 3. Check all params have been set and throw error if not
if [ -z "$filename" ]; then
    echo "Error: Please set the filename variable to the path of the 3d object file"
    exit 1
fi

echo "Processing file for object: $filename"
blender -b -P blender_script.py -- \
    --nr_images $num_images \
    --engine CYCLES \
    --scale 0.8 \
    --camera_dist 1.2  \
    --img_resolution $img_resolution \
    --filename $filename 

echo "Done rendering images for object: $filename"