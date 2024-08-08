import argparse
import logging
import os
import shutil
import sys
from pathlib import Path

from exif import Image

img_formats = [".png", ".jpg", ".jpeg"]


def is_image_file(filepath):
    return os.path.splitext(filepath)[-1].lower() in img_formats


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-directory",
        "-i",
        dest="input_directory",
        type=str,
        required=True,
        help="Directory in which to search for images and rename them.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        dest="output_directory",
        type=str,
        required=True,
        help="Root directory in which to save the renamed files by year.",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        dest="recursive",
        action="store_true",
        help="Search for images recursively in directories.",
    )
    parser.add_argument(
        "--overwrite",
        "-f",
        dest="force_overwrite",
        action="store_true",
        help="Force overwrite of existing image files. Otherwise, a D is appended to the filename.",
    )
    parser.add_argument(
        "--skip",
        "-s",
        dest="skip_overwrite_prompt",
        action="store_true",
        help="If a duplicate file is found, do not overwrite and do not ask user.",
    )
    parser.add_argument(
        "--delete-orig",
        "-D",
        dest="delete_originals",
        action="store_true",
        help="Moves the originals with new names. Without this option, a copy is made instead with a new name.",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        handlers=[logging.FileHandler("debug.log"), logging.StreamHandler()],
        format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.INFO,
    )

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

        try:
            date_time = image.get("datetime_original")
            if date_time is None:
                raise ValueError("No datetime_original found in EXIF data.")
            year = date_time.split(":")[0]  # Extract the year from datetime_original
        except Exception as e:
            logger.warning(
                f"Failed to find suitable EXIF data to rename for {f}. Error: {e}"
            )
            # If EXIF data is not found, move/copy the image to the "Other" directory
            year = "Other"

        # Create the year directory if it doesn't exist
        year_directory = os.path.join(args.output_directory, year)
        if not os.path.exists(year_directory):
            os.makedirs(year_directory)
            logger.info(f"Created directory: {year_directory}")

        try:
            orig_ext = os.path.splitext(f)[-1]
            new_filename = (
                date_time.replace(":", "-").replace(" ", "_") + orig_ext
                if date_time
                else os.path.basename(f)
            )
            new_filepath = os.path.join(year_directory, new_filename)
        except Exception as e:
            logger.warning(f"Failed to construct new filepath for {f}. Error: {e}")
            continue

        duplicate_exists = os.path.isfile(new_filepath)
        if duplicate_exists and args.skip_overwrite_prompt:
            continue
        if not args.force_overwrite:
            while duplicate_exists:
                new_filepath = (
                    os.path.splitext(new_filepath)[0]
                    + "D"
                    + os.path.splitext(new_filepath)[1]
                )
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
