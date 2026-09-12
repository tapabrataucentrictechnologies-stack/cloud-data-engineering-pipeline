from pathlib import Path

import httplib2

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# ============================================================
# GOOGLE DRIVE PERMISSIONS
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/drive"
]


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
)


CREDENTIALS_FILE = (
    BASE_DIR
    / "credentials.json"
)


TOKEN_FILE = (
    BASE_DIR
    / "token.json"
)


# ============================================================
# HTTP CONFIGURATION
# ============================================================

HTTP_TIMEOUT = 300


# ============================================================
# AUTHENTICATION
# ============================================================

def get_drive_credentials():
    """
    Authenticate with Google Drive.

    Existing OAuth credentials are reused whenever
    possible. Expired credentials are refreshed.
    """

    credentials = None

    # --------------------------------------------------------
    # Load existing token
    # --------------------------------------------------------

    if TOKEN_FILE.exists():

        credentials = (
            Credentials.from_authorized_user_file(
                str(TOKEN_FILE),
                SCOPES
            )
        )

    # --------------------------------------------------------
    # Refresh expired token
    # --------------------------------------------------------

    if (
        credentials
        and credentials.expired
        and credentials.refresh_token
    ):

        credentials.refresh(
            Request()
        )

    # --------------------------------------------------------
    # Start OAuth flow when necessary
    # --------------------------------------------------------

    if (
        not credentials
        or not credentials.valid
    ):

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

        # Save credentials for future requests.
        TOKEN_FILE.write_text(
            credentials.to_json(),
            encoding="utf-8"
        )

    return credentials


# ============================================================
# GOOGLE DRIVE SERVICE
# ============================================================

def get_drive_service():
    """
    Create an authenticated Google Drive API service.
    """

    credentials = (
        get_drive_credentials()
    )

    http = httplib2.Http(
        timeout=HTTP_TIMEOUT
    )

    authorized_http = AuthorizedHttp(
        credentials,
        http=http
    )

    service = build(
        "drive",
        "v3",
        http=authorized_http,
        cache_discovery=False
    )

    return service


# ============================================================
# UPLOAD FILE
# ============================================================

def upload_file(
    local_file_path: str,
    file_name: str,
    folder_id: str
) -> str:
    """
    Upload a local file to Google Drive.

    Returns:
        Google Drive file ID.
    """

    from googleapiclient.http import (
        MediaFileUpload
    )

    service = (
        get_drive_service()
    )

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


# ============================================================
# LIST FILES
# ============================================================

def list_files(
    folder_id: str
) -> list[dict]:
    """
    List files inside a Google Drive folder.

    Returns a list containing:
        id
        name
    """

    if not folder_id:
        raise ValueError(
            "Google Drive folder ID is required."
        )

    service = (
        get_drive_service()
    )

    query = (
        f"'{folder_id}' in parents "
        "and trashed = false"
    )

    response = (
        service.files()
        .list(
            q=query,
            spaces="drive",
            fields="files(id,name,mimeType,size)",
            pageSize=100,
            orderBy="name"
        )
        .execute()
    )

    return response.get(
        "files",
        []
    )


# ============================================================
# DOWNLOAD FILE
# ============================================================

def download_file(
    file_id: str,
    local_file_path: str
) -> str:
    """
    Download a Google Drive file.

    Returns:
        Local downloaded file path.
    """

    from googleapiclient.http import (
        MediaIoBaseDownload
    )

    if not file_id:
        raise ValueError(
            "Google Drive file ID is required."
        )

    service = (
        get_drive_service()
    )

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