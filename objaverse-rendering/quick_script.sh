#!/bin/bash
# Script used to loop throguh render_blender.sh
# It's useful, since render_blender deleted .glsb objects ONLY at the end of the script

# for i in 10 iters run "sh render_blender.sh"

for i in {1..10}
do
    echo "Iteration of blender download is $i"
    sh render_blender.sh
done