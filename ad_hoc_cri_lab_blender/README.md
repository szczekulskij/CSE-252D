In this directory we store the tools used to:
1. Download objaverse data
2. Render and save objaverse data into 2d images with different lighting conditions
3. Deleting downloaded glb objects to save space

Furthermore, we store the rendered 2D images in the `objaverse-rendering/objaverse_data` directory.


## Setup to run the rendering script:
1. Download & install the blender software from the official website: https://www.blender.org/download/
2. Set up blender in terminal by adding the path to the blender executable to the PATH variable. For example, in the bash shell, you can add the following line to the `.bashrc` file:
```bash
export PATH=$PATH:/path/to/blender/executable
```
3. Install python dependencies via `python3 -m pip install -r requirements_blender.txt`


# Requirements for running script
* Look into `ad_hoc_cri_lab_blender/render_blender.sh`
* Set the variables within the shell script above and run it
* (Optional) Change `METAL` to `CUDA` in `blender_script.py` (eg. line of code `.preferences.compute_device_type = "METAL" # or "CUDA" or "OPENCL"`)