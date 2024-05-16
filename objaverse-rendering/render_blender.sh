#!/bin/bash

: '
add comments here
Robust - itll only download 3d objects that havent been rendered yet
To specify path for images/3d objects download look into blender_script.py

Had to be setup this way in a shell script, since any script run from blender HAS to use blenders python 
(and therefore cant have any dependencies installed)
'

alias blender=/Applications/Blender.app/Contents/MacOS/Blender 
# 1. Set up variables
num_objects=5
num_images=4 # per object
img_resolution=512

# 2. Download 3d objects
# python3 -m pip install -r requirements_blender.txt # can be commented out if already installed
python3 objaverse_download.py --num_objects $num_objects # this will download blender files and save filenames in filenames.txt file (it'll delete the file if it existed before running this script)
filenames=$(cat filenames.txt)

# 2.1 Some robustness
# 2.1.1 Check if filenames.txt is empty
if [ ! -s filenames.txt ]
then
    echo "Error: filenames.txt is empty. Please ensure it contains filenames."
    exit 1
fi

# 2.1.2 Check if filenames variable is set
if [ -z "$filenames" ]
then
    echo "Error: No filenames found. Please check filenames.txt."
    exit 1
fi

#3. Run blender script for each object
for filename in $filenames; 
do
    echo "Processing file for object: $filename"
    blender -b -P blender_script.py -- \
        --nr_images $num_images \
        --engine CYCLES \
        --scale 0.8 \
        --camera_dist 1.2  \
        --img_resolution $img_resolution \
        --filename $filename 
done

# #4. Delete 3d objects (so they dont take up space
python3 objaverse_delete.py --filenames $filenames