import argparse
import logging
import os
import shutil
import sys
from pathlib import Path

from PIL import Image
from PIL.ExifTags import TAGS

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
        help="Root directory in which to save the resized files by year.",
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
        help="Force overwrite of existing image files. Otherwise, the word RESIZED is appended to the filename.",
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
        help="Deletes the original photos.",
    )
    parser.add_argument(
        "--resize_max_dim_pix",
        "--resize",
        dest="resize_max_dim_pix",
        required=True,
        type=int,
        help="Resize the resulting image such that the greatest dimension is equal to the value. Image will scale proportionally.",
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
            image = Image.open(f)
        except Exception as e:
            logger.warning(f"Failed to open file {f}")
            logger.debug(e)
            continue

        try:
            # Extract EXIF data for datetime
            exif_data = image._getexif()
            if exif_data:
                for tag, value in exif_data.items():
                    tag_name = TAGS.get(tag, tag)
                    if tag_name == "DateTimeOriginal":
                        date_time = value
                        break
                else:
                    date_time = None
            else:
                date_time = None

            if date_time is None:
                raise ValueError("No DateTimeOriginal found in EXIF data.")
            year = date_time.split(":")[0]  # Extract the year from DateTimeOriginal
        except Exception as e:
            logger.warning(
                f"Failed to find suitable EXIF data to organize for {f}. Error: {e}"
            )
            year = "Other"

        # Create the year directory or "Other" directory if it doesn't exist
        year_directory = os.path.join(args.output_directory, year)
        if not os.path.exists(year_directory):
            os.makedirs(year_directory)
            logger.info(f"Created directory: {year_directory}")

        file_name = os.path.basename(f)
        new_filepath = os.path.join(year_directory, file_name)

        duplicate_exists = os.path.isfile(new_filepath)
        if duplicate_exists and args.skip_overwrite_prompt:
            continue
        if not args.force_overwrite:
            while duplicate_exists:
                new_filepath = (
                    os.path.splitext(new_filepath)[0]
                    + "_RESIZED"
                    + os.path.splitext(new_filepath)[1]
                )
                duplicate_exists = os.path.isfile(new_filepath)

        max_dim = args.resize_max_dim_pix
        x, y = image.size

        biggest_dim = x if x > y else y

        if max_dim > biggest_dim:
            logger.warning(
                f"Images can only be reduced in size. Max dimension {max_dim} is greater than image size = {image.size}"
            )
            shutil.copyfile(f, new_filepath)
            continue

        if x > y:
            ratio = max_dim / float(x)
        else:
            ratio = max_dim / float(y)

        new_x = ratio * x
        new_y = ratio * y

        resized_image = image.resize((int(new_x), int(new_y)))

        try:
            exif = image.info.get("exif")
            resized_image.save(new_filepath, exif=exif)
        except:
            logger.warning(f"No EXIF data found.")
            resized_image.save(new_filepath)

        if args.delete_originals:
            os.remove(f)
            logger.info(f"Deleted original image: {f}")

        logger.info(f"Resized {f} to {new_filepath}.")

        converted_count += 1

    logger.info(f"Jobs completed. Resized {converted_count} of {num_files} files")


if __name__ == "__main__":
    main()
