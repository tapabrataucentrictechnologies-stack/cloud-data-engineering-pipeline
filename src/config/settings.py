import os

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# GOOGLE CLOUD CONFIGURATION
# ============================================================

GCP_PROJECT_ID = os.getenv(
    "GCP_PROJECT_ID"
)

BIGQUERY_DATASET = os.getenv(
    "BIGQUERY_DATASET"
)


# ============================================================
# GOOGLE DRIVE CONFIGURATION
# ============================================================

GOOGLE_DRIVE_FOLDER_ID = os.getenv(
    "GOOGLE_DRIVE_FOLDER_ID"
)


# ============================================================
# APPLICATION ENVIRONMENT
# ============================================================

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development"
)


# ============================================================
# SUPPORTED INPUT FILE TYPES
# ============================================================

SUPPORTED_EXTENSIONS = {
    ".csv",
    ".json",
    ".xml",
    ".xlsx",
}


# ============================================================
# VALIDATE GOOGLE DRIVE SETTINGS
# ============================================================

def validate_drive_settings():
    """
    Validate the configuration required
    for Google Drive access.
    """

    missing = []

    if not GCP_PROJECT_ID:
        missing.append(
            "GCP_PROJECT_ID"
        )

    if not GOOGLE_DRIVE_FOLDER_ID:
        missing.append(
            "GOOGLE_DRIVE_FOLDER_ID"
        )

    if missing:

        raise ValueError(
            "Missing required environment variables: "
            + ", ".join(missing)
        )


# ============================================================
# VALIDATE BIGQUERY SETTINGS
# ============================================================

def validate_bigquery_settings():
    """
    Validate the configuration required
    for BigQuery access.
    """

    missing = []

    if not GCP_PROJECT_ID:
        missing.append(
            "GCP_PROJECT_ID"
        )

    if not BIGQUERY_DATASET:
        missing.append(
            "BIGQUERY_DATASET"
        )

    if missing:

        raise ValueError(
            "Missing required environment variables: "
            + ", ".join(missing)
        )