#!/bin/bash

targetDir=$1
destDir=$2

for folder in $targetDir/*; do
    if [ -d "$folder" ]; then
        folderName=$(basename "$folder")
        mkdir "$destDir/$folderName"
        python image_resizer.py -i "$targetDir/$folderName" -o "$destDir/$folderName" -r -s --resize_max_dim_pix 1000
    fi
done
