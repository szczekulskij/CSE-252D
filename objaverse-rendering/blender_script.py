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


PROCESSES = multiprocessing.cpu_count() - 2 # leave some cpus for other stuff to not kill the PC
OBJAVERSE_PATH = "~/.objaverse/hf-objaverse-v1/glbs/" # default path for where the objaverse objects will be stored
IMAGE_PATH = '''~/masters-work/spring '24/CSE-252D/objaverse-rendering/objaverse_data''' # default path for where the rendered objaverse images will be stored
# if IMAGE_PATH or OBJAVERSE_PATH is not found, it will be created
if not os.path.exists(IMAGE_PATH): os.makedirs(IMAGE_PATH)
if not os.path.exists(OBJAVERSE_PATH): os.makedirs(OBJAVERSE_PATH)

parser = argparse.ArgumentParser(description='Render 3D objects from objaverse')
parser.add_argument('--nr_objects', type=int, default=10, help='Number of objects to render') # number of objects to render
parser.add_argument('--nr_images', type=int, default=8, help='Number of processes to use') # number of images to render per object
parser.add_argument("--engine", type=str, default="CYCLES", choices=["CYCLES", "BLENDER_EEVEE"])
parser.add_argument("--scale", type=float, default=0.8)
parser.add_argument("--camera_dist", type=int, default=1.2)



argv = sys.argv[sys.argv.index("--") + 1 :]
args = parser.parse_args(argv)

print('===================', args.engine, '===================')





def get_ids_of_already_downloaded_objects(objaverse_path = OBJAVERSE_PATH, image_path = IMAGE_PATH):
    ''' 
    Objects from objaverse are stored in form PATH/{gibberish}/{uid}.glb
    Rendering (2d images) are stored in form PATH/{uid}/{light_params_camera_params}.png
    '''
    downloaded_objects = set()
    for root, dirs, files in os.walk(OBJAVERSE_PATH):
        for file in files:
            if file.endswith(".glb"):
                uid = file.split(".")[0]
                downloaded_objects.add(uid)

    for root, dirs, files in os.walk(IMAGE_PATH):
        for file in files:
            if file.endswith(".png"):
                uid = file.split("/")[0]
                downloaded_objects.add(uid)

    return downloaded_objects
    


def download_3d_objects_from_objectverse(nr_objects, nr_processes = PROCESSES):
    '''
    saves to "~/.objaverse/hf-objaverse-v1/glbs/" path by default
    '''
    allUids = objaverse.load_uids()
    downloaded_uids = get_ids_of_already_downloaded_objects()
    uids = [uid for uid in allUids if uid not in downloaded_uids] # remove already downloaded objects (quick operation, dw)
    uids = random.sample(uids, nr_objects) # get random objects
    objects = objaverse.load_objects(
        uids=uids,
        download_processes=nr_processes
    )
    return objects