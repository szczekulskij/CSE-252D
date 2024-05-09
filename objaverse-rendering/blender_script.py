import os 

OBJAVERSE_PATH = "~/.objaverse/hf-objaverse-v1/glbs/" # default path for where the objaverse objects will be stored
IMAGE_PATH = '''~/masters-work/spring '24/CSE-252D/objaverse-rendering/objaverse_data''' # default path for where the rendered objaverse images will be stored
# if IMAGE_PATH or OBJAVERSE_PATH is not found, it will be created
if not os.path.exists(IMAGE_PATH): os.makedirs(IMAGE_PATH)
if not os.path.exists(OBJAVERSE_PATH): os.makedirs(OBJAVERSE_PATH)










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


def randomize_lighting(bpy, light):
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
    light.energy = 3000
    light.location = x,y,z

    direction = - light.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    light.rotation_euler = rot_quat.to_euler()
    return x,y,z


def get_3x4_RT_matrix_from_blender(light):
    # bcam stands for blender camera
    # R_bcam2cv = Matrix(
    #     ((1, 0,  0),
    #     (0, 1, 0),
    #     (0, 0, 1)))

    # Transpose since the rotation is object rotation, 
    # and we want coordinate rotation
    # R_world2bcam = cam.rotation_euler.to_matrix().transposed()
    # T_world2bcam = -1*R_world2bcam @ location
    #
    # Use matrix_world instead to account for all constraints
    location, rotation = light.matrix_world.decompose()[0:2]
    R_world2bcam = rotation.to_matrix().transposed()

    # Convert camera location to translation vector used in coordinate changes
    # T_world2bcam = -1*R_world2bcam @ cam.location
    # Use location from matrix_world to account for constraints:     
    T_world2bcam = -1*R_world2bcam @ location

    # # Build the coordinate transform matrix from world to computer vision camera
    # R_world2cv = R_bcam2cv@R_world2bcam
    # T_world2cv = R_bcam2cv@T_world2bcam

    # put into 3x4 matrix
    RT = Matrix((
        R_world2bcam[0][:] + (T_world2bcam[0],),
        R_world2bcam[1][:] + (T_world2bcam[1],),
        R_world2bcam[2][:] + (T_world2bcam[2],)
        ))
    return RT





#######################################################
'''Main Functions'''
#######################################################
def render_and_save_images_for_a_single_object(bpy, scene, cam_constraint, object_uid, nr_images):
    '''
    renders and save images for a single object
    in IMAGE_PATH we'll be saving in a following format:
    images - IMAGE_PATH/{uid}/{hash_light_params}.png
    lightning params - IMAGE_PATH/{uid}/{hash_light_params}.txt

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

    # 4. Set camera location 
    cam = scene.objects["Camera"]
    cam.location = (0, 1.2, 0) # should that be different ? How does it tie together with the transformation matrx of light that we output as our data label?

    
    # 4. Create an empty object to track (helpful for camera and light setup)
    empty = bpy.data.objects.new("Empty", None)
    scene.collection.objects.link(empty)
    cam_constraint.target = empty

    for i in range(nr_images):
        # 5. randomize lightning
        x,y,z = randomize_lighting(bpy, bpy.data.lights["Point"])

        # 6. Render the image
        render_path = f"{IMAGE_PATH}/{object_uid}/{i:03d}.png"
        scene.render.filepath = render_path
        bpy.ops.render.render(write_still=True)

        # 7. Save the lightning params in a txt file
        coordinates = f"{x},{y},{z}"
        RT = get_3x4_RT_matrix_from_blender(bpy.data.lights["Point"])
        with open(f"{IMAGE_PATH}/{object_uid}/{i:03d}.txt", "w") as f:
            f.write(coordinates + "\n")
            f.write(str(RT))
            f.close()


def main(nr_objects, nr_images, nr_processes, bpy, scene, cam_constraint):
    # 1. Download objects and save them in the default path
    # objects in form dict{uid: obj}
    objects_uids = list(objects.keys())
    # 2. For each object render and save images and then delete
    for object_uid in objects_uids:
        # render and save images for a single object
        render_and_save_images_for_a_single_object(bpy, scene, cam_constraint, object_uid, nr_images)




if __name__ == "__main__":
    import multiprocessing
    import argparse
    import sys
    from mathutils import Vector, Matrix
    import numpy as np

    import bpy
    from mathutils import Vector
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
    # multhi-threading
    processes = multiprocessing.cpu_count() - 2 # 2 is the number of threads that are always running
    main(nr_objects=args.nr_objects, 
         nr_images=args.nr_images, 
         nr_processes=processes, 
         bpy = bpy,
         scene = scene,
         cam_constraint=cam_constraint,
         )