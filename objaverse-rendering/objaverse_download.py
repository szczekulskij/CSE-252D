'''
Few notes and design choices:
1. I'm putting camera in a single place, and not moving it around.
2. Lightning is randomized for each render (rather than hardcoing ~8 different lightnings positions). This way ANN can generalize better. (similar like og paper)
3. 

'''

import itertools
import math
import os 
import random
import time

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
    

GOOD_CATEGORIES = ["car", "vehicle", "automobile", "robot", "machine", "weapon",
                   "food", 
                   ]



def download_3d_objects_from_objectverse(
        nr_objects, 
        nr_processes = MAX_PROCESSES - 2, 
        categories = ["car", "vehicle", "automobile", "robot", 
                      "car", "wood", "robot", "tree", "skull", "lamp", "animegirl", "cat", "dog", "ship", "human",
                      "man", "woman", "plane", "airplane", "aircraft", "computer", "apple", "batman", "spiderman",
                      ],
        # categories = [],
        ):
    '''
    saves to "~/.objaverse/hf-objaverse-v1/glbs/" path by default
    '''
    allUids = objaverse.load_uids()
    annotations = objaverse.load_annotations(allUids)
    def get_categories_given_uids(uids):
        return {uid: [item['name'] for item in annotations[uid]['tags']] for uid in uids}

    assert type(categories) == list, "categories should be a list of strings"
    downloaded_uids = get_ids_of_already_downloaded_objects()
    allUids = [uid for uid in allUids if uid not in downloaded_uids]

    if not categories: # don't limit to any categories
        uids_to_download = random.sample(allUids, nr_objects)
        if len(uids_to_download) == 0:
            raise Exception("Couldn't find any objects that haven't been downloaded and processed yet.")
    else: # download only from specific categories
        uids_to_download = set()
        categories = set(categories)

        uid_categories = get_categories_given_uids(allUids)
        uids = (uid for uid in allUids if any(category in uid_categories[uid] for category in categories))
        uids = [uid for uid in uids if uid not in uids_to_download]
        print("found uids: ", len(uids))
        uids_to_download.update(uids)

        if len(uids_to_download) > nr_objects:
            # take a random subset of the uids
            uids_to_download = random.sample(uids_to_download, len(uids_to_download))
            uids_to_download = set(itertools.islice(uids_to_download, nr_objects))

        if len(uids_to_download) == 0:
            raise Exception("Couldn't find any objects in the given categories that haven't been downloaded yet. Try again with different categories.")

    objects = objaverse.load_objects(
        uids=uids_to_download,
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
    print(objects)
    # remove filenames.txt 
    if os.path.exists('filenames.txt'):
        os.remove('filenames.txt')

    # print filepaths
    with open('filenames.txt', 'w') as f:
        for _, filepath in objects.items():
            f.write(filepath + '\n')