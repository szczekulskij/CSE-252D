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
num_objects=1
num_images=4 # per object
img_resolution=512

# 2. Download 3d objects
python3 -m pip install bpy
filenames=$(python3 objaverse_download.py --num_objects $num_objects)

for filename in $filenames;
do
    echo $filename
done

: '
#3. Run blender script for each object
# for filename in $filenames; 
# do
#     blender --python-use-system-env -b -P blender_script.py -- \
#         --nr_objects $num_objects \
#         --nr_images $num_images \
#         --engine CYCLES \
#         --scale 0.8 \
#         --camera_dist 1.2  \
#         --img_resolution $img_resolution \
#         --filename $filename
# done

# #4. Delete 3d objects (so they dont take up space
# python3 objaverse_delete.py --filenames $filenames
'