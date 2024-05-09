'''
Few notes and design choices:
1. I'm putting camera in a single place, and not moving it around.
2. Lightning is randomized for each render (rather than hardcoing ~8 different lightnings positions). This way ANN can generalize better. (similar like og paper)
3. 

'''

import math
import os 
import random

import numpy as np
import objaverse
import multiprocessing
from mathutils import Vector, Matrix
from blender_script import OBJAVERSE_PATH, IMAGE_PATH

MAX_PROCESSES = multiprocessing.cpu_count()


#######################################################
'''Functions specific to objaverse download'''
#######################################################
def get_ids_of_already_downloaded_objects():
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
    

def download_3d_objects_from_objectverse(nr_objects, nr_processes = MAX_PROCESSES - 2):
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




if __name__ == "__main__":
    # parse args from terminal
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_objects", type=int, default=10)
    args = parser.parse_args()
    objects = download_3d_objects_from_objectverse(args.num_objects) # objects in form dict{uid: filepath}

    # print filepaths
    for _, filepath in objects.items():
        print(filepath)
    