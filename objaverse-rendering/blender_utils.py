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

PROCESSES = multiprocessing.cpu_count() - 2 # leave some cpus for other stuff to not kill the PC
OBJAVERSE_PATH = "~/.objaverse/hf-objaverse-v1/glbs/" # default path for where the objaverse objects will be stored
IMAGE_PATH = '''~/masters-work/spring '24/CSE-252D/objaverse-rendering/objaverse_data''' # default path for where the rendered objaverse images will be stored
# if IMAGE_PATH or OBJAVERSE_PATH is not found, it will be created
if not os.path.exists(IMAGE_PATH): os.makedirs(IMAGE_PATH)
if not os.path.exists(OBJAVERSE_PATH): os.makedirs(OBJAVERSE_PATH)

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





#######################################################
'''Below you can find functions specific to blender'''
#######################################################
def reset_scene(bpy) -> None:
    """Resets the scene to a clean state."""
    # delete everything that isn't part of a camera or a light
    for obj in bpy.data.objects:
        if obj.type not in {"CAMERA", "LIGHT"}:
            bpy.data.objects.remove(obj, do_unlink=True)
    # delete all the materials
    for material in bpy.data.materials:
        bpy.data.materials.remove(material, do_unlink=True)
    # delete all the textures
    for texture in bpy.data.textures:
        bpy.data.textures.remove(texture, do_unlink=True)
    # delete all the images
    for image in bpy.data.images:
        bpy.data.images.remove(image, do_unlink=True)



# normalzie each scene so it's in the same scale and coordinate system
def normalize_scene(bpy):
    def scene_root_objects():
        for obj in bpy.context.scene.objects.values():
            if not obj.parent:
                yield obj
    def scene_meshes():
        for obj in bpy.context.scene.objects.values():
            if isinstance(obj.data, (bpy.types.Mesh)):
                yield obj
                
    def scene_bbox(single_obj=None, ignore_matrix=False):
        bbox_min = (math.inf,) * 3
        bbox_max = (-math.inf,) * 3
        found = False
        for obj in scene_meshes() if single_obj is None else [single_obj]:
            found = True
            for coord in obj.bound_box:
                coord = Vector(coord)
                if not ignore_matrix:
                    coord = obj.matrix_world @ coord
                bbox_min = tuple(min(x, y) for x, y in zip(bbox_min, coord))
                bbox_max = tuple(max(x, y) for x, y in zip(bbox_max, coord))
        if not found:
            raise RuntimeError("no objects in scene to compute bounding box for")
        return Vector(bbox_min), Vector(bbox_max)

    bbox_min, bbox_max = scene_bbox()
    scale = 1 / max(bbox_max - bbox_min)
    for obj in scene_root_objects():
        obj.scale = obj.scale * scale
    # Apply scale to matrix_world.
    bpy.context.view_layer.update()
    bbox_min, bbox_max = scene_bbox()
    offset = -(bbox_min + bbox_max) / 2
    for obj in scene_root_objects():
        obj.matrix_world.translation += offset
    bpy.ops.object.select_all(action="DESELECT")


# load the glb model
def load_object(bpy, object_path: str) -> None:
    """Loads a glb model into the scene."""
    if object_path.endswith(".glb"):
        bpy.ops.import_scene.gltf(filepath=object_path, merge_vertices=True)
    elif object_path.endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=object_path)
    else:
        raise ValueError(f"Unsupported file type: {object_path}")




# similar sample as for the camera position in the original paper's code


# def randomize_lighting(bpy, light2):
#     x,y,z = random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(0.5, 1.5)
#     light2.energy = 3000
#     bpy.data.objects["Point"].location[0] = x
#     bpy.data.objects["Point"].location[1] = y
#     bpy.data.objects["Point"].location[2] = z
#     return x,y,z


def randomize_lighting(bpy, light2):
    def sample_spherical(radius_min=1.5, radius_max=2.0, maxz=1.6, minz=-0.75):
        correct = False
        while not correct:
            vec = np.random.uniform(-1, 1, 3)
    #         vec[2] = np.abs(vec[2])
            radius = np.random.uniform(radius_min, radius_max, 1)
            vec = vec / np.linalg.norm(vec, axis=0) * radius[0]
            if maxz > vec[2] > minz:
                correct = True
        return vec
    
    x,y,z = sample_spherical()
    light2.energy = 3000
    light2.location = x,y,z

    direction = - light2.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    light2.rotation_euler = rot_quat.to_euler()
    return x,y,z


#######################################################
'''Main Function'''
#######################################################
def render_and_save_images_for_a_single_object(bpy, scene, cam_constraint, object_uid, nr_images):
    '''
    renders and save images for a single object
    in IMAGE_PATH we'll be saving in a following format:
    images - IMAGE_PATH/{uid}/{hash_light_params}.png
    lightning params - IMAGE_PATH/{uid}/{hash_light_params}.json

    params:
        bpy: blender context (has to be passed from the main script)
        object_uid: str
        nr_images: int
    '''
    os.makedirs(f"{IMAGE_PATH}/{object_uid}", exist_ok=True)
    # 1. reset scene after previous object renderings
    reset_scene(bpy) # doesn't reset camera and light
    # 2. load new object
    load_object(bpy, f"{OBJAVERSE_PATH}/{object_uid}.glb")
    # 3. normalize scene so that the object is always in the center
    normalize_scene(bpy)
    
    # 4. Create an empty object to track (helpful for camera and light setup)
    empty = bpy.data.objects.new("Empty", None)
    scene.collection.objects.link(empty)
    cam_constraint.target = empty
