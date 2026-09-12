from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.cloud.google_drive import list_files
from src.config.settings import (
    GOOGLE_DRIVE_FOLDER_ID,
    SUPPORTED_EXTENSIONS,
    validate_drive_settings,
)

from src.run_pipeline import run_pipeline


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/pipeline",
    tags=["Pipeline"]
)


# ============================================================
# PIPELINE STATE
# ============================================================

pipeline_state = {
    "status": "idle",
    "selected_file": None,
    "result": None,
    "error": None,
}


# ============================================================
# REQUEST MODEL
# ============================================================

class PipelineRequest(BaseModel):
    """
    Request body used when the user selects
    a dataset and clicks Run Pipeline.
    """

    selected_file: str


# ============================================================
# GET AVAILABLE DRIVE FILES
# ============================================================

@router.get("/files")
def get_available_files():
    """
    Return supported files currently available
    inside the configured Google Drive raw folder.
    """

    try:

        validate_drive_settings()

        drive_files = list_files(
            GOOGLE_DRIVE_FOLDER_ID
        )

        supported_files = []

        for file in drive_files:

            file_name = (
                file.get("name", "")
            )

            extension = (
                Path(file_name)
                .suffix
                .lower()
            )

            # Ignore unsupported files.
            if extension not in SUPPORTED_EXTENSIONS:
                continue

            # Ignore temporary Excel files.
            if file_name.startswith("~$"):
                continue

            supported_files.append(
                {
                    "id": file.get("id"),
                    "name": file_name,
                    "extension": extension,
                    "type": extension.replace(
                        ".",
                        ""
                    ).upper(),
                    "mime_type": file.get(
                        "mimeType"
                    ),
                    "size": file.get(
                        "size"
                    ),
                }
            )

        return {
            "success": True,
            "count": len(
                supported_files
            ),
            "files": supported_files,
        }

    except Exception as error:

        print(
            "Drive file listing error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# GET PIPELINE STATUS
# ============================================================

@router.get("/status")
def get_pipeline_status():
    """
    Return the current pipeline status.
    """

    return {
        "success": True,
        "status": pipeline_state["status"],
        "selected_file": (
            pipeline_state["selected_file"]
        ),
        "result": (
            pipeline_state["result"]
        ),
        "error": (
            pipeline_state["error"]
        ),
    }


# ============================================================
# RUN PIPELINE
# ============================================================

@router.post("/run")
def execute_pipeline(
    request: PipelineRequest
):
    """
    Run the existing end-to-end pipeline
    for the selected Google Drive file.

    The existing run_pipeline() function is reused.
    """

    selected_file = (
        request.selected_file.strip()
    )

    if not selected_file:

        raise HTTPException(
            status_code=400,
            detail="A dataset file must be selected."
        )

    # --------------------------------------------------------
    # Update state
    # --------------------------------------------------------

    pipeline_state["status"] = "running"

    pipeline_state["selected_file"] = (
        selected_file
    )

    pipeline_state["result"] = None

    pipeline_state["error"] = None

    print(
        "\n"
        + "=" * 60
    )

    print(
        "FASTAPI PIPELINE REQUEST"
    )

    print(
        "=" * 60
    )

    print(
        f"Selected file: {selected_file}"
    )

    try:

        # ----------------------------------------------------
        # Call the existing working pipeline
        # ----------------------------------------------------

        result = run_pipeline(
            selected_file
        )

        # ----------------------------------------------------
        # Update successful state
        # ----------------------------------------------------

        pipeline_state["status"] = (
            "completed"
        )

        pipeline_state["result"] = (
            result
        )

        return {
            "success": True,
            "message": (
                "Pipeline completed successfully."
            ),
            "data": result,
        }

    except FileNotFoundError as error:

        pipeline_state["status"] = (
            "failed"
        )

        pipeline_state["error"] = str(
            error
        )

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:

        pipeline_state["status"] = (
            "failed"
        )

        pipeline_state["error"] = str(
            error
        )

        print(
            "Pipeline execution error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# RESET PIPELINE STATUS
# ============================================================

@router.post("/reset")
def reset_pipeline_status():
    """
    Reset the in-memory pipeline status.
    """

    pipeline_state["status"] = "idle"

    pipeline_state["selected_file"] = None

    pipeline_state["result"] = None

    pipeline_state["error"] = None

    return {
        "success": True,
        "message": "Pipeline status reset.",
    }