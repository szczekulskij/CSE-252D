#!/bin/bash

# for i in 10 iters run "sh render_blender.sh"

for i in {1..10}
do
    echo "Iteration of blender download is $i"
    sh render_blender.sh
done