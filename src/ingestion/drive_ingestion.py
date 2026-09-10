from pathlib import Path

from src.cloud.google_drive import (
    upload_file,
    list_files,
    download_file
)

from src.config.settings import (
    GOOGLE_DRIVE_FOLDER_ID,
    validate_drive_settings
)


# File types supported by the pipeline.
SUPPORTED_EXTENSIONS = {
    ".csv",
    ".json",
    ".xml"
}


def upload_raw_files(
    raw_directory: str = "data/raw"
) -> list[dict]:
    """
    Upload supported raw data files
    to Google Drive.
    """

    validate_drive_settings()

    raw_path = Path(
        raw_directory
    )

    if not raw_path.exists():
        raise FileNotFoundError(
            f"Raw data directory not found: "
            f"{raw_directory}"
        )

    uploaded_files = []

    for file_path in raw_path.iterdir():

        # Ignore directories.
        if not file_path.is_file():
            continue

        # Ignore unsupported file types.
        if (
            file_path.suffix.lower()
            not in SUPPORTED_EXTENSIONS
        ):
            continue

        file_id = upload_file(
            local_file_path=str(file_path),
            file_name=file_path.name,
            folder_id=GOOGLE_DRIVE_FOLDER_ID
        )

        uploaded_files.append(
            {
                "name": file_path.name,
                "file_id": file_id
            }
        )

    return uploaded_files


def download_raw_files(
    output_directory: str = "data/from_drive"
) -> list[str]:
    """
    Download supported raw files from
    Google Drive into a local staging directory.
    """

    validate_drive_settings()

    output_path = Path(
        output_directory
    )

    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    drive_files = list_files(
        GOOGLE_DRIVE_FOLDER_ID
    )

    downloaded_files = []

    for drive_file in drive_files:

        file_name = drive_file["name"]

        # Ignore unsupported files.
        if (
            Path(file_name).suffix.lower()
            not in SUPPORTED_EXTENSIONS
        ):
            continue

        local_path = (
            output_path / file_name
        )

        download_file(
            file_id=drive_file["id"],
            local_file_path=str(local_path)
        )

        downloaded_files.append(
            str(local_path)
        )

    return downloaded_files