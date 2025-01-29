# Reference implementation for zero1-2-3 paper:
# https://github.com/cvlab-columbia/zero123/blob/main/objaverse-rendering/scripts/blender_script.py

import math
import os
import random 


# LIGHT_TYPE = "Point" # type of light to be used in the scene
LIGHT_TYPE = "Sun" # type of light to be used in the scene


import multiprocessing
import argparse
import sys
from mathutils import Vector, Matrix
import numpy as np

import bpy
from mathutils import Vector
import multiprocessing
parser = argparse.ArgumentParser(description='Render 3D objects from objaverse')
parser.add_argument('--nr_images', type=int, default=8, help='Number of images to render per object') # number of images to render per object
parser.add_argument("--engine", type=str, default="CYCLES", choices=["CYCLES", "BLENDER_EEVEE"])
parser.add_argument("--scale", type=float, default=0.8)
parser.add_argument("--camera_dist", type=float, default=1.2)
parser.add_argument("--img_resolution", type=int, default=512)
parser.add_argument("--filename", type=str, default=10)
parser.add_argument("--image_path", type=str, default="~/Desktop/blender_output")

argv = sys.argv[sys.argv.index("--") + 1 :]
args = parser.parse_args(argv)

print('===================', args.engine, '===================')


# ======================================================= START (Probably) Unncessary code ===========================================================================
# Shouldn't be needed anymore
# # new addition - completely reset the scene
# """Resets the scene to a clean state only not camera."""
# # delete everything that isn't part of a camera or a light
# for obj in bpy.data.objects:
#     if obj.type not in {"CAMERA"}:
#         bpy.data.objects.remove(obj, do_unlink=True)
# # delete all the materials
# for material in bpy.data.materials:
#     bpy.data.materials.remove(material, do_unlink=True)
# # delete all the textures
# for texture in bpy.data.textures:
#     bpy.data.textures.remove(texture, do_unlink=True)
# # delete all the images
# for image in bpy.data.images:
#     bpy.data.images.remove(image, do_unlink=True)

# setup lightning (new part)
# string to upper LIGHT_TYPE
# bpy.ops.object.light_add(type=LIGHT_TYPE.upper(), radius=1, align="WORLD", location=(0, 0, 0))
# print("before")
# light = bpy.data.lights[LIGHT_TYPE]
# print("after")

# Defuault light params, we'll be changing them later
# light.energy = 3000
# light.energy = 1000
# light.energy = 200
# bpy.data.objects[LIGHT_TYPE].location[2] = 0.5
# bpy.data.objects[LIGHT_TYPE].scale[0] = 100
# bpy.data.objects[LIGHT_TYPE].scale[1] = 100
# bpy.data.objects[LIGHT_TYPE].scale[2] = 100
# light.location = 0, 0, 0.5
# light.scale = 100, 100, 100
# ======================================================= END (Probably) Unncessary code ===========================================================================

context = bpy.context
scene = context.scene
render = scene.render

cam = scene.objects["Camera"]
cam.location = (0, 1.2, 0)
cam.data.lens = 35
cam.data.sensor_width = 32

cam_constraint = cam.constraints.new(type="TRACK_TO")
cam_constraint.track_axis = "TRACK_NEGATIVE_Z"
cam_constraint.up_axis = "UP_Y"

# setup lighting
bpy.ops.object.light_add(type="AREA", location=(0, 0, 3))
light = bpy.data.lights["Area"]
light.energy = 500  # Adjust brightness
light.color = (1, 1, 1)  # Neutral white light


light2 = bpy.data.lights["Area"]
light2.energy = 3000

bpy.ops.object.light_add(type="SUN", location=(5, 5, 5))
sun = bpy.data.lights["Sun"]
sun.energy = 2  # Sunlight is less intense

bpy.data.objects["Area"].location[2] = 0.5
bpy.data.objects["Area"].scale[0] = 100
bpy.data.objects["Area"].scale[1] = 100
bpy.data.objects["Area"].scale[2] = 100

render.engine = args.engine
render.image_settings.file_format = "PNG"
render.image_settings.color_mode = "RGBA"
render.resolution_x = 512
render.resolution_y = 512
render.resolution_percentage = 100

scene.cycles.device = "GPU"
scene.cycles.samples = 128
scene.cycles.diffuse_bounces = 1
scene.cycles.glossy_bounces = 1
scene.cycles.transparent_max_bounces = 3
scene.cycles.transmission_bounces = 3
scene.cycles.filter_width = 0.01
scene.cycles.use_denoising = True
scene.render.film_transparent = True

bpy.context.preferences.addons["cycles"].preferences.get_devices()
# Set the device_type
bpy.context.preferences.addons[
    "cycles"
].preferences.compute_device_type = "METAL" # or "OPENCL" or "CUDA"

# multhi-threading (for our 252D purposes of faster rendering)
processes = multiprocessing.cpu_count() - 2 # 2 is the number of threads that are always running


# New changes to enable more color
bpy.context.scene.view_settings.view_transform = 'Standard'



#######################################################
'''Below you can find helper functions specific to blender'''
#######################################################

def enable_colors_in_the_scene():
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            for mat in obj.data.materials:
                if not mat.node_tree:  # No shader nodes
                    print(f"Material {mat.name} is missing nodes. Adding default shader.")
                    mat.use_nodes = True
                    bsdf = mat.node_tree.nodes.get('Principled BSDF')
                    if bsdf:
                        bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)  # White



def reset_scene() -> None:
    """Resets the scene to a clean state."""
    # delete everything that isn't part of a camera or a light
    for obj in bpy.data.objects:
        if obj.type not in {"CAMERA", "LIGHT"}:
        # if obj.type not in {"CAMERA"}:
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
def normalize_scene():
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
        print(obj)
        obj.scale = obj.scale * scale
    # Apply scale to matrix_world.
    bpy.context.view_layer.update()
    bbox_min, bbox_max = scene_bbox()
    offset = -(bbox_min + bbox_max) / 2
    for obj in scene_root_objects():
        obj.matrix_world.translation += offset
    bpy.ops.object.select_all(action="DESELECT")


# load the glb model
def load_object(filepath: str) -> None:
    """Loads a glb model into the scene."""
    if not os.path.isfile(filepath):
        raise RuntimeError(f"File {filepath} does not exist")
    if filepath.endswith(".glb"):
        bpy.ops.import_scene.gltf(filepath=filepath, merge_vertices=True)
    elif filepath.endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=filepath)
    elif filepath.endswith(".obj"):
        bpy.ops.wm.obj_import(filepath=filepath)
    else:
        raise ValueError(f"Unsupported file type: {filepath}")


def randomize_lighting() -> None:
    light2.energy = random.uniform(300, 600)
    bpy.data.objects["Area"].location[0] = random.uniform(-1., 1.)
    bpy.data.objects["Area"].location[1] = random.uniform(-1., 1.)
    bpy.data.objects["Area"].location[2] = random.uniform(0.5, 1.5)


def reset_lighting() -> None:
    light2.energy = 1000
    bpy.data.objects["Area"].location[0] = 0
    bpy.data.objects["Area"].location[1] = 0
    bpy.data.objects["Area"].location[2] = 0.5


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

def set_camera_location():
    # from https://blender.stackexchange.com/questions/18530/
    x, y, z = sample_spherical(radius_min=1.5, radius_max=2.2, maxz=2.2, minz=-2.2)
    camera = bpy.data.objects["Camera"]
    camera.location = x, y, z

    direction = - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    return camera

def randomize_camera():
    # elevation = random.uniform(0., 90.)
    # azimuth = random.uniform(0., 360)
    # distance = random.uniform(0.8, 1.6)
    # return set_camera_location(elevation, azimuth, distance)
    return set_camera_location()


#######################################################
'''Main Function'''
#######################################################
def render_and_save_images_for_a_single_object(filepath, nr_images):
    '''
    '''
    # 1. reset scene after previous object renderings
    reset_scene() # doesn't reset camera and light
    # 2. load new object
    load_object(filepath)
    # 3. normalize scene so that the object is always in the center
    normalize_scene()

    # 4. create an empty object to track
    empty = bpy.data.objects.new("Empty", None)
    scene.collection.objects.link(empty)
    cam_constraint.target = empty

    # randomize_lighting()

    enable_colors_in_the_scene()

    
    # Unncessary code, keeping for tracking
    # cam.data.lens = 35
    # cam.data.sensor_width = 32
    # cam_constraint = cam.constraints.new(type="TRACK_TO")
    # cam_constraint.track_axis = "TRACK_NEGATIVE_Z"
    # cam_constraint.up_axis = "UP_Y"
    # cam = scene.objects["Camera"]
    # cam.location = (0, 1.2, 0) # should that be different ? How does it tie together with the transformation matrx of light that we output as our data label?

    
    # 4. Create an empty object to track (helpful for camera and light setup)
    empty = bpy.data.objects.new("Empty", None)
    scene.collection.objects.link(empty)
    cam_constraint.target = empty

    for i in range(nr_images):
        # 5. randomize lightning
        randomize_camera()

        # 6. Render the image
        render_path = f"{args.image_path}/{i:03d}.png"
        scene.render.filepath = render_path
        bpy.ops.render.render(write_still=True)

        # 7. Save the camera angle coordinates in a file (TODO CRI: Add this functionality)
        # coordinates = f"{x},{y},{z}"
        # RT = get_3x4_RT_matrix_from_blender(bpy.data.lights["Point"])
        # with open(f"{IMAGE_PATH}/{object_uid}/{i:03d}.txt", "w") as f:
        #     f.write(coordinates + "\n")
        #     # f.write(str(RT))
        #     f.close()
        # # save coordinates to .npy
        # np.save(f"{IMAGE_PATH}/{object_uid}/{i:03d}.npy", np.array([x,y,z]))

if __name__ == "__main__":
    render_and_save_images_for_a_single_object(args.filename, args.nr_images)