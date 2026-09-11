from pathlib import Path

import httplib2

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# --------------------------------------------------
# Google Drive permissions
# --------------------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/drive.file"
]


# --------------------------------------------------
# Project paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]


CREDENTIALS_FILE = (
    BASE_DIR / "credentials.json"
)


TOKEN_FILE = (
    BASE_DIR / "token.json"
)


# --------------------------------------------------
# HTTP configuration
# --------------------------------------------------

# Google Drive downloads can occasionally take
# longer than the default HTTP timeout.
HTTP_TIMEOUT = 300


# --------------------------------------------------
# Authentication
# --------------------------------------------------

def get_drive_credentials():
    """
    Authenticate the user and return
    Google Drive OAuth credentials.
    """

    credentials = None

    # --------------------------------------------------
    # Reuse existing OAuth token
    # --------------------------------------------------

    if TOKEN_FILE.exists():

        credentials = (
            Credentials.from_authorized_user_file(
                str(TOKEN_FILE),
                SCOPES
            )
        )

    # --------------------------------------------------
    # Refresh expired credentials
    # --------------------------------------------------

    if credentials and credentials.expired:

        if credentials.refresh_token:

            credentials.refresh(
                Request()
            )

    # --------------------------------------------------
    # Start OAuth flow if required
    # --------------------------------------------------

    if not credentials or not credentials.valid:

        if not CREDENTIALS_FILE.exists():

            raise FileNotFoundError(
                "credentials.json was not found "
                "in the project root."
            )

        flow = (
            InstalledAppFlow
            .from_client_secrets_file(
                str(CREDENTIALS_FILE),
                SCOPES
            )
        )

        credentials = (
            flow.run_local_server(
                port=0
            )
        )

        # Save token for future runs.
        TOKEN_FILE.write_text(
            credentials.to_json(),
            encoding="utf-8"
        )

    return credentials


# --------------------------------------------------
# Google Drive service
# --------------------------------------------------

def get_drive_service():
    """
    Authenticate the user and create
    a Google Drive API service with
    an extended HTTP timeout.
    """

    credentials = get_drive_credentials()

    # Create an HTTP client with a longer timeout.
    http = httplib2.Http(
        timeout=HTTP_TIMEOUT
    )

    # Authorize the HTTP client.
    authorized_http = AuthorizedHttp(
        credentials,
        http=http
    )

    # Create the Google Drive service.
    service = build(
        "drive",
        "v3",
        http=authorized_http,
        cache_discovery=False
    )

    return service


# --------------------------------------------------
# Upload file
# --------------------------------------------------

def upload_file(
    local_file_path: str,
    file_name: str,
    folder_id: str
) -> str:
    """
    Upload a local file to Google Drive.

    Returns the Google Drive file ID.
    """

    from googleapiclient.http import (
        MediaFileUpload
    )

    service = get_drive_service()

    file_metadata = {
        "name": file_name,
        "parents": [folder_id]
    }

    media = MediaFileUpload(
        local_file_path,
        resumable=True
    )

    uploaded_file = (
        service.files()
        .create(
            body=file_metadata,
            media_body=media,
            fields="id,name"
        )
        .execute()
    )

    return uploaded_file["id"]


# --------------------------------------------------
# List files
# --------------------------------------------------

def list_files(
    folder_id: str
) -> list[dict]:
    """
    List files inside a Google Drive folder.
    """

    service = get_drive_service()

    query = (
        f"'{folder_id}' in parents "
        "and trashed = false"
    )

    response = (
        service.files()
        .list(
            q=query,
            spaces="drive",
            fields="files(id,name)",
            pageSize=100
        )
        .execute()
    )

    return response.get(
        "files",
        []
    )


# --------------------------------------------------
# Download file
# --------------------------------------------------

def download_file(
    file_id: str,
    local_file_path: str
) -> str:
    """
    Download a Google Drive file with
    retry support and an extended timeout.
    """

    from googleapiclient.http import (
        MediaIoBaseDownload
    )

    service = get_drive_service()

    request = (
        service.files()
        .get_media(
            fileId=file_id
        )
    )

    destination = Path(
        local_file_path
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Write the file from the beginning.
    with destination.open(
        "wb"
    ) as file_handle:

        downloader = (
            MediaIoBaseDownload(
                file_handle,
                request,
                chunksize=1024 * 1024
            )
        )

        done = False

        while not done:

            status, done = (
                downloader.next_chunk(
                    num_retries=5
                )
            )

            if status:

                progress = int(
                    status.progress() * 100
                )

                print(
                    f"    Download progress: "
                    f"{progress}%"
                )

    return str(destination)