import argparse
import os
import sys
import glob
import logging
from pathlib import Path
import shutil
from exif import Image

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
                        help='Force overwrite of existing image files. Otherwise, a D is appended to the filename.')
    parser.add_argument('--skip', '-s', dest='skip_overwrite_prompt', action='store_true',
                        help='If a duplicate file is found, do not overwrite and do not ask user.')
    parser.add_argument('--delete-orig', '-D', dest='delete_originals', action='store_true',
                        help='Moves the originals with new names. Without this option, a copy is made instead with a new name.')

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
        try:
            with open(f, "rb") as img_file:
                image = Image(img_file)
        except Exception as e:
            logger.warning(f"Failed to open file {f}")
            logger.debug(e)
            continue

        date_time = image.get("datetime_original")

        try:
            orig_ext = os.path.splitext(f)[-1]
            new_filename = date_time.replace(":", "-").replace(" ", "_") + orig_ext
            new_filepath = os.path.join(args.output_directory, new_filename)
        except:
            logger.warning(f"Failed to find suitable EXIF data to rename. EXIF Data =  {image.list_all()}")
            continue
        
        duplicate_exists = os.path.isfile(new_filepath)
        if duplicate_exists and args.skip_overwrite_prompt:
            continue
        if not args.force_overwrite:
            while(duplicate_exists):
                new_filepath = os.path.splitext(new_filepath)[0] + "D" + os.path.splitext(new_filepath)[1]
                duplicate_exists = os.path.isfile(new_filepath)


        if args.delete_originals:
            os.rename(f, new_filepath)
            logger.info(f"Moved {f} to {new_filepath}.")
        else:
            shutil.copyfile(f, new_filepath)
            logger.info(f"Copied {f} to {new_filepath}.")
            
        converted_count += 1

    logger.info(f"Jobs completed. Renamed {converted_count} of {num_files} files")

if __name__ == "__main__":
    main()
