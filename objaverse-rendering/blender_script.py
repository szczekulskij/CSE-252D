import random
import objaverse
import os
import multiprocessing
import argparse
import json
import math
import os
import random
import sys
import time
import urllib.request
import uuid
from typing import Tuple
from mathutils import Vector, Matrix
import numpy as np

import bpy
from mathutils import Vector
from blender_utils import main
import multiprocessing


parser = argparse.ArgumentParser(description='Render 3D objects from objaverse')
parser.add_argument('--nr_objects', type=int, default=10, help='Number of objects to render') # number of objects to render
parser.add_argument('--nr_images', type=int, default=8, help='Number of processes to use') # number of images to render per object
parser.add_argument("--engine", type=str, default="CYCLES", choices=["CYCLES", "BLENDER_EEVEE"])
parser.add_argument("--scale", type=float, default=0.8)
parser.add_argument("--camera_dist", type=int, default=1.2)
parser.add_argument("--img_resolution", type=int, default=512)




argv = sys.argv[sys.argv.index("--") + 1 :]
args = parser.parse_args(argv)

print('===================', args.engine, '===================')

# Copy paste from zero123/objaverse-rendering/blender_script.py
context = bpy.context
scene = context.scene
render = scene.render
cam = scene.objects["Camera"]
cam.location = (0, 1.2, 0) # should that be different ?
cam.data.lens = 35
cam.data.sensor_width = 32
cam_constraint = cam.constraints.new(type="TRACK_TO")
cam_constraint.track_axis = "TRACK_NEGATIVE_Z"
cam_constraint.up_axis = "UP_Y"


# setup lightning (new part)
bpy.ops.object.light_add(type="POINT", radius=1, align="WORLD", location=(0, 0, 0))
light = bpy.data.lights["Point"]

# Defuault light params, we'll be changing them later
light.energy = 3000
# bpy.data.objects["Point"].location[2] = 0.5
# bpy.data.objects["Point"].scale[0] = 100
# bpy.data.objects["Point"].scale[1] = 100
# bpy.data.objects["Point"].scale[2] = 100
light.location = 0, 0, 0.5
light.scale = 100, 100, 100


# Copy paste from zero123/objaverse-rendering/blender_script.py
render.engine = args.engine
render.image_settings.file_format = "PNG"
render.image_settings.color_mode = "RGBA"
render.resolution_x = args.img_resolution
render.resolution_y = args.img_resolution
render.resolution_percentage = 100

# Copy paste from zero123/objaverse-rendering/blender_script.py
scene.cycles.device = "GPU"
scene.cycles.samples = 128
scene.cycles.diffuse_bounces = 1
scene.cycles.glossy_bounces = 1
scene.cycles.transparent_max_bounces = 3
scene.cycles.transmission_bounces = 3
scene.cycles.filter_width = 0.01
scene.cycles.use_denoising = True
scene.render.film_transparent = True


# Might require change for M2
bpy.context.preferences.addons["cycles"].preferences.get_devices()
# Set the device_type
bpy.context.preferences.addons[
    "cycles"
].preferences.compute_device_type = "CUDA" # or "OPENCL"


if __name__ == "__main__":
    # multhi-threading
    processes = multiprocessing.cpu_count() - 2 # 2 is the number of threads that are always running
    main(nr_objects=args.nr_objects, 
         nr_images=args.nr_images, 
         nr_processes=processes, 
         bpy = bpy,
         scene = scene,
         cam_constraint=cam_constraint,
         )