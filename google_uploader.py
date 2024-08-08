import json
import os
import sys

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these SCOPES, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/photoslibrary.appendonly"]


def authenticate():
    """Authenticate the user and return the credentials."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def sanitize_filename(filename):
    """Sanitize filename to ensure it contains only ASCII characters."""
    return filename.encode("ascii", errors="ignore").decode("ascii")


def upload_photo(session, file_path):
    """Upload a photo to Google Photos."""
    upload_url = "https://photoslibrary.googleapis.com/v1/uploads"
    sanitized_filename = sanitize_filename(os.path.basename(file_path))
    headers = {
        "Authorization": f"Bearer {session.credentials.token}",
        "Content-type": "application/octet-stream",
        "X-Goog-Upload-File-Name": sanitized_filename,
        "X-Goog-Upload-Protocol": "raw",
    }

    with open(file_path, "rb") as file:
        response = requests.post(upload_url, headers=headers, data=file)

    if response.status_code == 200:
        return response.content.decode("utf-8")
    else:
        print(f"Failed to upload {file_path}: {response.content}")
        return None


def create_media_item(session, upload_token, description="Uploaded by script"):
    """Create a media item in Google Photos."""
    url = "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate"
    headers = {
        "Authorization": f"Bearer {session.credentials.token}",
        "Content-type": "application/json",
    }
    payload = json.dumps(
        {
            "newMediaItems": [
                {
                    "description": description,
                    "simpleMediaItem": {"uploadToken": upload_token},
                }
            ]
        }
    )
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        print("Media item created successfully.")
    else:
        print(f"Failed to create media item: {response.content}")


def main(directory):
    creds = authenticate()
    session = requests.Session()
    session.credentials = creds

    successful_uploads = 0
    failed_uploads = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(("png", "jpg", "jpeg")):
                file_path = os.path.join(root, file)
                try:
                    print(f"Uploading {file_path}...")
                    upload_token = upload_photo(session, file_path)
                    if upload_token:
                        create_media_item(session, upload_token)
                        successful_uploads += 1
                    else:
                        failed_uploads.append(file_path)
                except Exception as e:
                    print(f"Error uploading {file_path}: {e}")
                    failed_uploads.append(file_path)

    print(
        f"Upload completed: {successful_uploads} files successfully uploaded, {len(failed_uploads)} files failed."
    )

    if len(failed_uploads) > 0:
        with open("failed_uploads.txt", "w") as f:
            for failed_file in failed_uploads:
                f.write(f"{failed_file}\n")

        print("Failed uploads written to failed_uploads.txt.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python upload_photos.py <directory>")
    else:
        main(sys.argv[1])
