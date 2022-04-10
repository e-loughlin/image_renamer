# image_renamer
A Python utility for bulk renaming images based on their EXIF metadata.

Why?

I became extraordinarily frustrated by how horribly disorganized my photos were. 
I had photos from my old blackberry, my android, my multitude of old cameras, my friend's cameras,
photos downloaded from Facebook, from Google drive, etc etc etc... I wanted them in a nice, neat format, which was easy to read. I wanted them to simply be named by their timestamp, and nothing else.

I needed a way to organize them. So I built this tool. It can recursively search through all the folders of the destination input folder, determine their EXIF timestamp, and re-save the file in a different directory as specified. If two files with the exact same timestamp (same exact second) are found, it's considered a duplicate. You can choose to --skip or --overwrite in these cases. You can select the -D option to delete existing files after they've been re-saved under the new name. 

USE AT YOUR OWN RISK. This script CAN DELETE FILES.

## Installing 

`pip install -r requirements.txt`

## Running

Copy an entire directory of image files, saving them in the output directory.:
`python image_renamer.py -i <directory> -o <output_dir>`

Rename an entire directory of image files (recursively):
`python image_renamer.py -d <directory> -o <output_dir> -r`

`-D` : Also delete the original source image, only after it's been successfully saved under a different name elsewhere.
`--skip`: If a duplicate destination file is found, skips that image altogether. Will not delete the file in this case.
`--overwrite`: If a duplicate destination file is found, overwrites that image altogether.

If neither `--skip` or `--overwrite` flags are selected, the user will be prompted for their input on each file. 