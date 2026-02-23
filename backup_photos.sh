#!/bin/bash

# Environment Variables (set these as needed)
START_DATE="2024-01-28"
END_DATE="2024-08-15"
EXTERNAL_HD="/Volumes/Evan Extern/05_Photos/"
PHONE_BACKUP="/Volumes/Evan Extern/Phone_Photos/"
GOOGLE_BACKUP="/Volumes/Evan Extern/Google_Photos"
LOCAL_BACKUP="/Users/eloughlin/data/05_Photos/"

source ./env/bin/activate

# Path to your Python scripts
SCRIPT_DIR="."

# Get start and end year from the specified dates
START_YEAR=$(echo $START_DATE | cut -d'-' -f1)
END_YEAR=$(echo $END_DATE | cut -d'-' -f1)

# 1. Download photos from Google Photos between specified dates
command="python3 \"$SCRIPT_DIR/google_downloader.py\" \"$START_DATE\" \"$END_DATE\" \"$GOOGLE_BACKUP\""
echo "Command: $command"
read -p "Do you want to download photos from Google Photos between $START_DATE and $END_DATE? (yes/no): " confirm
if [ "$confirm" = "yes" ]; then
    echo "Downloading photos from Google Photos..."
    eval $command
    if [ $? -ne 0 ]; then
        echo "Error downloading photos from Google Photos."
        exit 1
    fi
else
    echo "Skipping download of photos from Google Photos."
fi

# 2. Copy photos from phone/device to external hard drive
command="python3 \"$SCRIPT_DIR/image_renamer.py\" --input-directory \"$PHONE_BACKUP\" --output-dir \"$EXTERNAL_HD\" --recursive --overwrite --delete-orig"
echo "Command: $command"
read -p "Do you want to copy photos from phone/device to external hard drive? (yes/no): " confirm
if [ "$confirm" = "yes" ]; then
    echo "Copying photos from phone/device to external hard drive..."
    eval $command
    if [ $? -ne 0 ]; then
        echo "Error copying photos from phone/device."
        exit 1
    fi
else
    echo "Skipping copy of photos from phone/device."
fi

# 3. Copy/rename all photos to a single location and overwrite duplicates
command="python3 \"$SCRIPT_DIR/image_renamer.py\" --input-directory \"$GOOGLE_BACKUP\" --output-dir \"$EXTERNAL_HD\" --skip --delete-orig --recursive"
echo "Command: $command"
read -p "Do you want to copy photos from Google Backup to External Storage? (yes/no): " confirm
if [ "$confirm" = "yes" ]; then
    echo "Renaming and consolidating all photos to a single location..."
    eval $command
    if [ $? -ne 0 ]; then
        echo "Error renaming photos from Google Photos."
        exit 1
    fi

    command="python3 \"$SCRIPT_DIR/image_renamer.py\" --input-directory \"$PHONE_BACKUP\" --output-dir \"$EXTERNAL_HD\" --overwrite --recursive"
    echo "Command: $command"
    eval $command
    if [ $? -ne 0 ]; then
        echo "Error renaming photos from phone."
        exit 1
    fi
else
    echo "Skipping renaming and consolidation of photos."
fi

# 4. Resize photos for each year in the specified range and back them up to local storage
for ((year=START_YEAR; year<=END_YEAR; year++)); do
    command="python3 \"$SCRIPT_DIR/image_resizer.py\" --input-directory \"$EXTERNAL_HD/$year\" --output-dir \"$LOCAL_BACKUP\" --resize_max_dim_pix 1200 --overwrite --recursive"
    echo "Command: $command"
    read -p "Do you want to resize photos in the year $year and back them up to local storage? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        echo "Resizing photos for the year $year and backing them up to local storage..."
        eval $command
        if [ $? -ne 0 ]; then
            echo "Error resizing and backing up photos for the year $year."
            exit 1
        fi
    else
        echo "Skipping resizing and backup of photos for the year $year."
    fi
done

# 5. MANUAL: Confirm before deleting photos from Google Photos
command="python3 \"$SCRIPT_DIR/google_deleter.py\" \"$START_DATE\" \"$END_DATE\""
echo "Command: $command"
read -p "Do you want to delete photos from Google Photos between $START_DATE and $END_DATE? (yes/no): " confirm
if [ "$confirm" = "yes" ]; then
    eval $command
    if [ $? -ne 0 ]; then
        echo "Error deleting photos from Google Photos."
        exit 1
    fi
else
    echo "Skipping deletion of photos from Google Photos."
fi

# 6. Upload resized photos back to Google Photos
command="python3 \"$SCRIPT_DIR/google_uploader.py\" \"$LOCAL_BACKUP\""
echo "Command: $command"
read -p "Do you want to upload resized photos to Google Photos? (yes/no): " confirm
if [ "$confirm" = "yes" ]; then
    echo "Uploading resized photos to Google Photos..."
    eval $command
    if [ $? -ne 0 ]; then
        echo "Error uploading resized photos to Google Photos."
        exit 1
    fi
else
    echo "Skipping upload of resized photos to Google Photos."
fi

echo "Backup process completed."

