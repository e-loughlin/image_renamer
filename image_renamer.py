import argparse
import os
import sys
import glob
import logging
from PIL import Image
from PIL.ExifTags import TAGS
from pathlib import Path

img_formats = ['.png', '.jpg', '.jpeg']

def is_image_file(filepath):
    return os.path.splitext(filepath)[-1].lower() in img_formats

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-directory', '-i', dest="input_directory", type=str, required=True,
                        help='Directory in which to search for images and rename them.')
    parser.add_argument('--output-dir', '-o', dest="output_directory", type=str, required=True,
                        help='Directory in which to save the new files.')
    parser.add_argument('--recursive', '-r', dest='recursive', action='store_true',
                        help='Search for images recursively in directories.')
    parser.add_argument('--overwrite', '-f', dest='force_overwrite', action='store_true',
                        help='Force overwrite of existing image files.')
    parser.add_argument('--skip', '-s', dest='skip_overwrite_prompt', action='store_true',
                        help='If a duplicate file is found, do not overwrite and do not ask user.')
    parser.add_argument('--delete-original', '-D', dest='delete_original_file', action='store_true',
                        help='Delete original image file after successfully renaming it.')

    return parser.parse_args()

def main():
    args = parse_args()
    logging.basicConfig(handlers=[logging.FileHandler("debug.log"),
                                  logging.StreamHandler()],
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.INFO)

    logger = logging.getLogger(__name__)

    image_dir = os.path.abspath(args.input_directory)
    args.input_directory = image_dir
    args.output_directory = os.path.abspath(args.output_directory)

    logger.info(f"Initiating new run with args: {args}")
    if not os.path.isdir(image_dir):
        logger.critical(f"Specified directory was not found: {image_dir}")
        sys.exit()
    if not os.path.isdir(args.output_directory):
        logger.critical(f"Specified directory was not found: {args.output_directory}")
        sys.exit()

    logger.info(f"Searching for images in {image_dir}...")

    if args.recursive:
        files = list(Path(image_dir).rglob("*"))
    else:
        files = list(Path(image_dir).glob("*"))

    image_files = list(filter(is_image_file, files))
    num_files = len(image_files)

    logger.info(f"Found {num_files} files. Processing...")

    # image_files = [os.path.join(image_dir, f) for f in image_files]

    converted_count = 0 
    for f in image_files:
        logger.info(f"Opening image: {f}...")
        image = Image.open(f)
        exifdata = image.getexif()

        decoded_exif_data = {}

        for tag_id in exifdata:
            # Get the tag name, instead of human unreadable tag id
            tag = TAGS.get(tag_id, tag_id)
            data = exifdata.get(tag_id)
            # Decode bytes 
            # if isinstance(data, bytes):
                # data = data.decode()
            decoded_exif_data[tag] = data

        try:
            orig_ext = os.path.splitext(f)[-1]
            new_filename = decoded_exif_data["DateTimeOriginal"].replace(":", "-").replace(" ", "_") + orig_ext
            new_filepath = os.path.join(args.output_directory, new_filename)
        except:
            logger.warning(f"Failed to find suitable EXIF data to rename. EXIF Data =  {decoded_exif_data}")
            continue

        if os.path.isfile(new_filepath) and not args.force_overwrite:
            if args.skip_overwrite_prompt:
                continue
            print(f"File {new_filepath} already exists! Overwrite it? [Y/N]")
            response = input().lower()
            if "n" in response:
                continue

        image.save(new_filepath)
        logger.info(f"Copied and renamed {f} to {new_filepath}.")
        converted_count += 1

        if args.delete_original_file:
            os.remove(f)
            logger.info(f"Deleted {f}")

    logger.info(f"Jobs completed. Renamed {converted_count} of {num_files} files")

if __name__ == "__main__":
    main()