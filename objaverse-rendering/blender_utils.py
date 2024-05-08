import os 
import random
import objaverse
import multiprocessing

MAX_PROCESSES = multiprocessing.cpu_count()
def get_ids_of_already_downloaded_objects(objaverse_path, image_path):
    ''' 
    Objects from objaverse are stored in form PATH/{gibberish}/{uid}.glb
    Rendering (2d images) are stored in form PATH/{uid}/{light_params_camera_params}.png
    '''
    downloaded_objects = set()
    for root, dirs, files in os.walk(objaverse_path):
        for file in files:
            if file.endswith(".glb"):
                uid = file.split(".")[0]
                downloaded_objects.add(uid)

    for root, dirs, files in os.walk(image_path):
        for file in files:
            if file.endswith(".png"):
                uid = file.split("/")[0]
                downloaded_objects.add(uid)

    return downloaded_objects
    

def download_3d_objects_from_objectverse(nr_objects, nr_processes):
    '''
    saves to "~/.objaverse/hf-objaverse-v1/glbs/" path by default
    '''
    assert nr_processes <= MAX_PROCESSES, f"nr_processes should be less than {MAX_PROCESSES}"
    allUids = objaverse.load_uids()
    downloaded_uids = get_ids_of_already_downloaded_objects()
    uids = [uid for uid in allUids if uid not in downloaded_uids] # remove already downloaded objects (quick operation, dw)
    uids = random.sample(uids, nr_objects) # get random objects
    objects = objaverse.load_objects(
        uids=uids,
        download_processes=nr_processes
    )
    return objects


