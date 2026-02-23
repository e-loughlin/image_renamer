import os
from pathlib import Path

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

# Supported video formats
vid_formats = [".mp4", ".mov", ".avi"]


def is_video_file(filepath):
    return os.path.splitext(filepath)[-1].lower() in vid_formats


# Function to rename video files based on metadata
def rename_video_file(file_path, output_directory):
    parser = createParser(str(file_path))  # Convert Path object to string
    metadata = extractMetadata(parser)
    date_time = metadata.get("creation_date")  # Extract creation date from metadata
    year = date_time.year  # Extract the year from creation_date

    orig_ext = os.path.splitext(file_path)[-1]
    new_filename = date_time.strftime("%Y-%m-%d_%H-%M-%S") + orig_ext
    new_filepath = os.path.join(output_directory, str(year), new_filename)

    os.makedirs(os.path.dirname(new_filepath), exist_ok=True)
    os.rename(file_path, new_filepath)


# Example usage
input_directory = "/Volumes/Evan Extern/05_Photos/Other/"
output_directory = "/Volumes/Evan Extern/Other/"

for file in Path(input_directory).rglob("*"):
    if is_video_file(file):
        rename_video_file(file, output_directory)
