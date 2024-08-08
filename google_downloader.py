import json
import os
import sys
from datetime import datetime

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these SCOPES, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/photoslibrary.readonly"]


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


def list_media_items(session, start_date, end_date):
    """List all media items between two dates."""
    url = "https://photoslibrary.googleapis.com/v1/mediaItems:search"
    headers = {
        "Authorization": f"Bearer {session.credentials.token}",
        "Content-type": "application/json",
    }
    payload = json.dumps(
        {
            "filters": {
                "dateFilter": {
                    "ranges": [
                        {
                            "startDate": {
                                "year": start_date.year,
                                "month": start_date.month,
                                "day": start_date.day,
                            },
                            "endDate": {
                                "year": end_date.year,
                                "month": end_date.month,
                                "day": end_date.day,
                            },
                        }
                    ]
                }
            },
            "pageSize": 100,
        }
    )

    media_items = []
    next_page_token = None

    while True:
        if next_page_token:
            payload_dict = json.loads(payload)
            payload_dict["pageToken"] = next_page_token
            payload = json.dumps(payload_dict)

        response = requests.post(url, headers=headers, data=payload)
        if response.status_code != 200:
            print(f"Failed to list media items: {response.content}")
            break

        data = response.json()
        media_items.extend(data.get("mediaItems", []))
        next_page_token = data.get("nextPageToken", None)
        if not next_page_token:
            break

    return media_items


def download_photo(session, media_item, download_dir):
    """Download a photo."""
    base_url = media_item["baseUrl"]
    filename = os.path.join(download_dir, f"{media_item['id']}.jpg")
    response = requests.get(f"{base_url}=d")
    if response.status_code == 200:
        with open(filename, "wb") as file:
            file.write(response.content)
        print(f"Downloaded {filename}")
    else:
        print(f"Failed to download {filename}: {response.content}")


def main(start_date_str, end_date_str, download_dir):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    creds = authenticate()
    session = requests.Session()
    session.credentials = creds

    media_items = list_media_items(session, start_date, end_date)
    print(
        f"Found {len(media_items)} media items between {start_date_str} and {end_date_str}"
    )

    for media_item in media_items:
        download_photo(session, media_item, download_dir)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python download_photos.py <start_date> <end_date> <download_dir>")
        print("Dates should be in YYYY-MM-DD format")
    else:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
