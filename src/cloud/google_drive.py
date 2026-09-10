from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# Permissions required by this application.
SCOPES = [
    "https://www.googleapis.com/auth/drive.file"
]


# Project root directory.
BASE_DIR = Path(__file__).resolve().parents[2]


# OAuth credential files.
CREDENTIALS_FILE = (
    BASE_DIR / "credentials.json"
)

TOKEN_FILE = (
    BASE_DIR / "token.json"
)


def get_drive_service():
    """
    Authenticate the user and create
    a Google Drive API service.
    """

    credentials = None

    # Reuse previously generated OAuth token.
    if TOKEN_FILE.exists():

        credentials = (
            Credentials.from_authorized_user_file(
                str(TOKEN_FILE),
                SCOPES
            )
        )

    # Refresh expired credentials.
    if credentials and credentials.expired:

        if credentials.refresh_token:

            credentials.refresh(
                Request()
            )

    # Start OAuth flow if authentication
    # is missing or invalid.
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

        # Save the authentication token
        # for future runs.
        TOKEN_FILE.write_text(
            credentials.to_json()
        )

    # Create Google Drive API client.
    service = build(
        "drive",
        "v3",
        credentials=credentials
    )

    return service


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
            fields="files(id,name)"
        )
        .execute()
    )

    return response.get(
        "files",
        []
    )


def download_file(
    file_id: str,
    local_file_path: str
) -> str:
    """
    Download a Google Drive file.
    """

    import io

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

    with destination.open(
        "wb"
    ) as file_handle:

        downloader = (
            MediaIoBaseDownload(
                file_handle,
                request
            )
        )

        done = False

        while not done:

            _, done = (
                downloader.next_chunk()
            )

    return str(destination)