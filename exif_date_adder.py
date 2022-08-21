import argparse
import os
import sys
import logging
from exif import Image
from pathlib import Path
import re

img_formats = ['.png', '.jpg', '.jpeg']

def is_image_file(filepath):
    return os.path.splitext(filepath)[-1].lower() in img_formats

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-directory', '-i', dest="input_directory", type=str, required=True,
                        help='Directory in which to search for images and rename them.')
    parser.add_argument('--recursive', '-r', dest='recursive', action='store_true',
                        help='Search for images recursively in directories.')
    parser.add_argument('--overwrite', '-o', dest='overwrite', action='store_true',
                        help='Force overwrite of existing datetime string.')
    parser.add_argument('--date', '-d', dest='date', type=str, required=True,
                        help='Date to add. Note that timestamps will be incremented. Format: YYYY:MM:DD')
                        
    return parser.parse_args()

def main():
    args = parse_args()
    logging.basicConfig(handlers=[logging.FileHandler("debug.log"),
                                  logging.StreamHandler()],
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.INFO)

    logger = logging.getLogger(__name__)

    if not re.match('\d{4}:\d{2}:\d{2}', args.date):
        logger.critical(f"Date format incorrect. See --help options.")
        sys.exit()        

    image_dir = os.path.abspath(args.input_directory)
    args.input_directory = image_dir

    logger.info(f"Initiating new run with args: {args}")
    if not os.path.isdir(image_dir):
        logger.critical(f"Specified directory was not found: {image_dir}")
        sys.exit()

    logger.info(f"Searching for images in {image_dir}...")

    if args.recursive:
        files = list(Path(image_dir).rglob("*"))
    else:
        files = list(Path(image_dir).glob("*"))

    image_files = list(filter(is_image_file, files))
    num_files = len(image_files)

    logger.info(f"Found {num_files} files. Processing...")

    converted_count = 0 
    for f in image_files:
        logger.info(f"Opening image: {f}...")
        try:
            with open(f, 'rb') as img_file:
                image = Image(img_file)
        except Exception as e:
            logger.warning(f"Failed to open file {f}")
            logger.debug(e)
            continue

        hours = converted_count // 3600
        minutes = (converted_count % 3600) // 60
        seconds  = (converted_count % 3600) % 60

        try:
            image.get("datetime_original")
            if not args.overwrite:
                logger.info("File already has EXIF date time stamp. Skipping.")
                continue
        except:
            pass

        image.datetime_original = f"{args.date} {hours:02d}:{minutes:02d}:{seconds:02d}"

        with open(f, 'wb') as img_file:
            img_file.write(image.get_file())

        converted_count += 1
        if converted_count == (3600 * 24):
            logger.warning("Maximum number of images reached for this day.")
            break

    logger.info(f"Jobs completed. Updated EXIF date {converted_count} of {num_files} files")

if __name__ == "__main__":
    main()
