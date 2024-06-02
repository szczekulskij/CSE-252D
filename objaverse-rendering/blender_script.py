import math
import os 

OBJAVERSE_PATH = os.path.expanduser("~/.objaverse/hf-objaverse-v1/glbs/") # default path for where the objaverse objects will be stored
IMAGE_PATH = os.path.expanduser('''~/masters-work/spring '24/CSE-252D/objaverse-rendering/objaverse_data''') # default path for where the rendered objaverse images will be stored
# if IMAGE_PATH or OBJAVERSE_PATH is not found, it will be created
if not os.path.exists(IMAGE_PATH): os.makedirs(IMAGE_PATH)
if not os.path.exists(OBJAVERSE_PATH): os.makedirs(OBJAVERSE_PATH)


# LIGHT_TYPE = "Point" # type of light to be used in the scene
LIGHT_TYPE = "Sun" # type of light to be used in the scene

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
    parser.add_argument('--nr_images', type=int, default=8, help='Number of processes to use') # number of images to render per object
    parser.add_argument("--engine", type=str, default="CYCLES", choices=["CYCLES", "BLENDER_EEVEE"])
    parser.add_argument("--scale", type=float, default=0.8)
    parser.add_argument("--camera_dist", type=float, default=1.2)
    parser.add_argument("--img_resolution", type=int, default=512)
    parser.add_argument("--filename", type=str, default=10)
    argv = sys.argv[sys.argv.index("--") + 1 :]
    args = parser.parse_args(argv)

    print('===================', args.engine, '===================')

    # Copy paste from zero123/objaverse-rendering/blender_script.py
    context = bpy.context
    scene = context.scene
    render = scene.render

    # new addition - completely reset the scene
    """Resets the scene to a clean state only not camera."""
    # delete everything that isn't part of a camera or a light
    for obj in bpy.data.objects:
        if obj.type not in {"CAMERA"}:
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


    # setup lightning (new part)
    # string to upper LIGHT_TYPE
    bpy.ops.object.light_add(type=LIGHT_TYPE.upper(), radius=1, align="WORLD", location=(0, 0, 0))
    print("before")
    light = bpy.data.lights[LIGHT_TYPE]
    print("after")

    # Defuault light params, we'll be changing them later
    # light.energy = 3000
    # light.energy = 1000
    light.energy = 200
    # bpy.data.objects[LIGHT_TYPE].location[2] = 0.5
    # bpy.data.objects[LIGHT_TYPE].scale[0] = 100
    # bpy.data.objects[LIGHT_TYPE].scale[1] = 100
    # bpy.data.objects[LIGHT_TYPE].scale[2] = 100
    # light.location = 0, 0, 0.5
    # light.scale = 100, 100, 100


    # Copy paste from zero123/objaverse-rendering/blender_script.py
    render.engine = args.engine
    render.image_settings.file_format = "PNG"
    render.image_settings.color_mode = "RGBA"
    render.resolution_x = args.img_resolution
    render.resolution_y = args.img_resolution
    render.resolution_percentage = 100

    # Copy paste from zero123/objaverse-rendering/blender_script.py
    scene.cycles.device = "GPU"
    # scene.cycles.samples = 128
    scene.cycles.samples = 1 # pat attention - light bouncing
    scene.cycles.diffuse_bounces = 1
    scene.cycles.glossy_bounces = 1
    scene.cycles.transparent_max_bounces = 3
    scene.cycles.transmission_bounces = 3
    scene.cycles.filter_width = 0.01
    scene.cycles.use_denoising = True
    scene.render.film_transparent = True


    # Might require change for devices other than M2
    bpy.context.preferences.addons["cycles"].preferences.get_devices()
    # Set the device_type
    bpy.context.preferences.addons[
        "cycles"
    ].preferences.compute_device_type = "METAL" # or "CUDA" or "OPENCL"
    # multhi-threading
    processes = multiprocessing.cpu_count() - 2 # 2 is the number of threads that are always running



    #######################################################
    '''Below you can find functions specific to blender'''
    #######################################################
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
    def load_object(object_path: str) -> None:
        """Loads a glb model into the scene."""
        if not os.path.isfile(object_path):
            raise RuntimeError(f"File {object_path} does not exist")
        if object_path.endswith(".glb"):
            bpy.ops.import_scene.gltf(filepath=object_path, merge_vertices=True)
        elif object_path.endswith(".fbx"):
            bpy.ops.import_scene.fbx(filepath=object_path)
        else:
            raise ValueError(f"Unsupported file type: {object_path}")


    def randomize_lighting():
        # def sample_spherical(radius_min=1.5, radius_max=2.0, maxz=1.6, minz=-0.75):
        def sample_spherical(radius_min=1.5, radius_max=1.5, maxz=1.6, minz=-0.75):
            correct = False
            while not correct:
                vec = np.random.uniform(-1, 1, 3)
        #         vec[2] = np.abs(vec[2])
                radius = np.random.uniform(radius_min, radius_max, 1)
                vec = vec / np.linalg.norm(vec, axis=0) * radius[0]
                if maxz > vec[2] > minz:
                    correct = True
            return vec

        # def sample_spherical():
        #     # new implementation by Jan, where we limit to only quarter of the sphere
        #     # camera is set at (0,1.2,0) 
        #     # the object is normalized to fit within box that goe from [-0.5,0.5] for each dimension
        #     y = np.random.uniform(0.1,1.5) # light from in front of the camera, never behind
        #     x = np.random.uniform(-1, 1) # light can be on either side of the object
        #     z = np.random.uniform(-0.3, 0.8) # light can be only at the level of the object or above

        #     vec = np.array([x,y,z])
        #     # vec = vec / np.linalg.norm(vec, axis=0) 
        #     return vec
            
        
        x,y,z = sample_spherical()
        # light.energy = 3000
        # light.energy = 1000
        light.energy = 200
        # light.location = x,y,z
        bpy.data.objects[LIGHT_TYPE].location[0] = x
        bpy.data.objects[LIGHT_TYPE].location[1] = y
        bpy.data.objects[LIGHT_TYPE].location[2] = z

        # set angles to point towards origin based on the coordinates x,y,z


        direction = - Vector((x, y, z)) # watch out here
        rot_quat = direction.to_track_quat('-Z', 'Y')
        bpy.data.objects[LIGHT_TYPE].rotation_euler = rot_quat.to_euler()
        return x,y,z


    #######################################################
    '''Main Functions'''
    #######################################################
    def render_and_save_images_for_a_single_object(filepath, object_uid, nr_images):
        '''
        renders and save images for a single object
        in IMAGE_PATH we'll be saving in a following format:
        images - IMAGE_PATH/{uid}/{object_uid}/{iter}.png
        lightning params - IMAGE_PATH/{uid}/{object_uid}/{iter}.txt

        params:
            bpy: blender context (has to be passed from the main script)
            object_uid: str
            nr_images: int
        '''
        # 0. Create folder for images
        os.makedirs(f"{IMAGE_PATH}/{object_uid}", exist_ok=True)
        # 1. reset scene after previous object renderings
        reset_scene() # doesn't reset camera and light
        # 2. load new object
        load_object(filepath)
        # 3. normalize scene so that the object is always in the center
        normalize_scene()

        # 4. Set camera location 
        cam = scene.objects["Camera"]
        cam.location = (0, 1.2, 0) # should that be different ?
        # cam.direction = - (0, 1.2, 0)
        # copy rest of the code from before


        
        cam.data.lens = 35
        cam.data.sensor_width = 32
        cam_constraint = cam.constraints.new(type="TRACK_TO")
        cam_constraint.track_axis = "TRACK_NEGATIVE_Z"
        cam_constraint.up_axis = "UP_Y"
        # cam = scene.objects["Camera"]
        # cam.location = (0, 1.2, 0) # should that be different ? How does it tie together with the transformation matrx of light that we output as our data label?

        
        # 4. Create an empty object to track (helpful for camera and light setup)
        empty = bpy.data.objects.new("Empty", None)
        scene.collection.objects.link(empty)
        cam_constraint.target = empty

        for i in range(nr_images):
            # 5. randomize lightning
            x,y,z = randomize_lighting()

            # 6. Render the image
            render_path = f"{IMAGE_PATH}/{object_uid}/{i:03d}.png"
            scene.render.filepath = render_path
            bpy.ops.render.render(write_still=True)

            # 7. Save the lightning params in a txt file
            coordinates = f"{x},{y},{z}"
            # RT = get_3x4_RT_matrix_from_blender(bpy.data.lights["Point"])
            # with open(f"{IMAGE_PATH}/{object_uid}/{i:03d}.txt", "w") as f:
            #     f.write(coordinates + "\n")
            #     # f.write(str(RT))
            #     f.close()
            # save coordinates to .npy
            np.save(f"{IMAGE_PATH}/{object_uid}/{i:03d}.npy", np.array([x,y,z]))


    object_uid = args.filename.split("/")[-1].split(".")[0]
    print("Rendering images for object with uid:", object_uid)
    render_and_save_images_for_a_single_object(args.filename, object_uid, args.nr_images)