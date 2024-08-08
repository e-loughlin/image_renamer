import argparse
import os
import subprocess
import sys


def run_script(script_name, args):
    """Helper function to run a script with arguments."""
    command = [sys.executable, script_name] + args
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {script_name}: {result.stderr}")
    else:
        print(result.stdout)


def main():
    parser = argparse.ArgumentParser(description="Backup and manage your photos.")
    parser.add_argument(
        "--start-date",
        "-s",
        required=True,
        help="Start date for downloading photos from Google Photos (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end-date",
        "-e",
        required=True,
        help="End date for downloading photos from Google Photos (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--external-hd",
        "-x",
        required=True,
        help="Path to the external hard drive where photos will be stored.",
    )
    parser.add_argument(
        "--phone-device",
        "-p",
        required=True,
        help="Path to the device (phone) where photos will be copied from.",
    )
    parser.add_argument(
        "--local-backup",
        "-l",
        required=True,
        help="Path to the local storage on your Mac for resizing and backup.",
    )
    args = parser.parse_args()

    # 1. Download photos from Google Photos between specified dates
    print("Downloading photos from Google Photos...")
    google_downloader_args = [
        args.start_date,
        args.end_date,
        os.path.join(args.external_hd, "Google_Photos"),
    ]
    run_script("google_downloader.py", google_downloader_args)

    # 2. Copy photos from phone/device to external hard drive
    print("Copying photos from phone/device to external hard drive...")
    image_renamer_args = [
        "--input-directory",
        args.phone_device,
        "--output-dir",
        os.path.join(args.external_hd),
        "--recursive",
    ]
    run_script("image_renamer.py", image_renamer_args)

    # 3. Copy/rename all photos to a single location and overwrite duplicates
    print("Renaming and consolidating all photos to a single location...")
    image_renamer_args = [
        "--input-directory",
        os.path.join(args.external_hd, "Google_Photos"),
        "--output-dir",
        args.external_hd,
        "--overwrite",
        "--delete-orig",
        "--recursive",
    ]
    run_script("image_renamer.py", image_renamer_args)

    # Run renamer again for phone photos
    image_renamer_args = [
        "--input-directory",
        os.path.join(args.external_hd, "Phone_Photos"),
        "--output-dir",
        args.external_hd,
        "--overwrite",
        "--recursive",
    ]
    run_script("image_renamer.py", image_renamer_args)

    # 4. Resize photos and back them up to local storage
    print("Resizing photos and backing them up to local storage...")
    image_resizer_args = [
        "--input-directory",
        args.external_hd,
        "--output-dir",
        args.local_backup,
        "--resize_max_dim_pix",
        "1200",
        "--overwrite",
        "--recursive",
    ]
    run_script("image_resizer.py", image_resizer_args)

    # 5. MANUAL: Confirm before deleting photos from Google Photos
    confirm = input(
        f"Do you want to delete photos from Google Photos between {args.start_date} and {args.end_date}? (yes/no): "
    )
    if confirm.lower() == "yes":
        google_deleter_args = [args.start_date, args.end_date]
        run_script("google_deleter.py", google_deleter_args)
    else:
        print("Skipping deletion of photos from Google Photos.")

    # 6. Upload resized photos back to Google Photos
    print("Uploading resized photos to Google Photos...")
    google_uploader_args = [args.local_backup]
    run_script("google_uploader.py", google_uploader_args)

    print("Backup process completed.")


if __name__ == "__main__":
    main()
