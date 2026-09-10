from src.ingestion.drive_ingestion import (
    upload_raw_files,
    download_raw_files
)


def main():
    """
    Run the Google Drive ingestion stage.
    """

    print(
        "Starting Google Drive ingestion..."
    )

    print(
        "\nUploading raw files..."
    )

    uploaded_files = upload_raw_files()

    for file_info in uploaded_files:
        print(
            f" - Uploaded: {file_info['name']}"
        )

    print(
        "\nDownloading files from Google Drive..."
    )

    downloaded_files = download_raw_files()

    for file_path in downloaded_files:
        print(
            f" - Downloaded: {file_path}"
        )

    print(
        "\nGoogle Drive ingestion completed successfully."
    )


if __name__ == "__main__":
    main()