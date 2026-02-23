import argparse
import logging
import os
import shutil
import sys
from pathlib import Path

from exif import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

img_formats = [".png", ".jpg", ".jpeg"]
vid_formats = [".mp4", ".mov", ".avi", ".mkv"]


def is_media_file(filepath):
    return os.path.splitext(filepath)[-1].lower() in img_formats + vid_formats


def is_image_file(filepath):
    return os.path.splitext(filepath)[-1].lower() in img_formats


def is_video_file(filepath):
    return os.path.splitext(filepath)[-1].lower() in vid_formats


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-directory",
        "-i",
        dest="input_directory",
        type=str,
        required=True,
        help="Directory in which to search for images and videos to rename.",
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
        help="Search for files recursively in directories.",
    )
    parser.add_argument(
        "--overwrite",
        "-f",
        dest="force_overwrite",
        action="store_true",
        help="Force overwrite of existing files. Otherwise, a 'D' is appended to the filename.",
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
    other_directory = os.path.join(args.output_directory, "Other")

    logger.info(f"Initiating new run with args: {args}")
    if not os.path.isdir(image_dir):
        logger.critical(f"Specified directory was not found: {image_dir}")
        sys.exit()
    if not os.path.isdir(args.output_directory):
        logger.critical(f"Specified directory was not found: {args.output_directory}")
        sys.exit()

    if not os.path.exists(other_directory):
        os.makedirs(other_directory)

    logger.info(f"Searching for media files in {image_dir}...")

    if args.recursive:
        files = list(Path(image_dir).rglob("*"))
    else:
        files = list(Path(image_dir).glob("*"))

    media_files = list(filter(is_media_file, files))
    num_files = len(media_files)

    logger.info(f"Found {num_files} files. Processing...")

    converted_count = 0
    moved_to_other_count = 0

    for f in media_files:
        logger.info(f"Opening file: {f}...")
        year = None
        date_time = None

        if is_image_file(f):
            try:
                with open(f, "rb") as img_file:
                    image = Image(img_file)
                date_time = image.get("datetime_original")
                if date_time is None:
                    raise ValueError("No datetime_original found in EXIF data.")
                year = date_time.split(":")[0]
            except Exception as e:
                logger.warning(
                    f"No suitable metadata found for {f} ({e}). Using file modification time."
                )
                mtime = os.path.getmtime(f)
                import datetime
                dt = datetime.datetime.fromtimestamp(mtime)
                date_time = dt.strftime("%Y:%m:%d %H:%M:%S")
                year = str(dt.year)
        elif is_video_file(f):
            try:
                parser = createParser(str(f))  # Convert Path object to string
                metadata = extractMetadata(parser)
                if metadata and metadata.has("creation_date"):
                    creation_date = metadata.get("creation_date")
                    date_time = creation_date.strftime("%Y:%m:%d %H:%M:%S")
                    year = str(creation_date.year)
                else:
                    raise ValueError("No creation date found in metadata.")
            except Exception as e:
                logger.warning(
                    f"No suitable metadata found for {f} ({e}). Using file modification time."
                )
                mtime = os.path.getmtime(f)
                import datetime
                dt = datetime.datetime.fromtimestamp(mtime)
                date_time = dt.strftime("%Y:%m:%d %H:%M:%S")
                year = str(dt.year)

        year_directory = os.path.join(args.output_directory, year)
        if not os.path.exists(year_directory):
            os.makedirs(year_directory)
            logger.info(f"Created directory: {year_directory}")

        orig_ext = os.path.splitext(f)[-1]
        new_filename = (
            date_time.replace(":", "-").replace(" ", "_") + orig_ext
            if year != "Other"
            else os.path.basename(f)
        )
        new_filepath = os.path.join(year_directory, new_filename)

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

    logger.info(
        f"Jobs completed. Renamed {converted_count} of {num_files} files. Moved {moved_to_other_count} files to 'Other' directory."
    )


if __name__ == "__main__":
    main()
