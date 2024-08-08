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


# Google File Uploader / Downloader

Store a credentials.json Google authentication file in the home directory. Then run `python google_uploader.py /path/to/photo/dir`.

Instructions on how to get that credentials JSON can be found here: https://developers.google.com/photos/library/guides/get-started


# All-In-One Tool

1. Figure out dates you want to transfer photos from.
2. Run script to download all photos between those dates from Google API and save them to the external Hard Drive.
3. Plug in your phone / device. Copy photos from there to some drive on the external Hard Drive.
4. Copy / rename all photos from both locations to the same place, and delete duplicates.
5. Files being transfered in this way should detect which subfolder they belong to. If they're not proper EXIF photos, they should be organized as such.
6. Run the image_resizer from the external drive to back them up in local storage in the Mac.
7. Delete all files from Google between those dates.
8. Run the google_uploader.py script 
