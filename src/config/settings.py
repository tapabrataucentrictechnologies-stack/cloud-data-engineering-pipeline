import os

from dotenv import load_dotenv


# Load variables from the .env file.
load_dotenv()


GCP_PROJECT_ID = os.getenv(
    "GCP_PROJECT_ID"
)

GOOGLE_DRIVE_FOLDER_ID = os.getenv(
    "GOOGLE_DRIVE_FOLDER_ID"
)

BIGQUERY_DATASET = os.getenv(
    "BIGQUERY_DATASET"
)

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development"
)


def validate_drive_settings():
    """
    Validate the configuration required
    for Google Drive.
    """

    missing = []

    if not GCP_PROJECT_ID:
        missing.append("GCP_PROJECT_ID")

    if not GOOGLE_DRIVE_FOLDER_ID:
        missing.append(
            "GOOGLE_DRIVE_FOLDER_ID"
        )

    if missing:
        raise ValueError(
            "Missing required environment variables: "
            + ", ".join(missing)
        )