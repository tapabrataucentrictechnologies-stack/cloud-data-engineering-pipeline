import os
import sys
from pathlib import Path

import pytest

# Make Spark use the Python interpreter
# from the active virtual environment.
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession

from src.ingestion.drive_ingestion import (
    download_raw_files
)

from src.ingestion.csv_loader import load_csv
from src.ingestion.json_loader import load_json
from src.ingestion.xml_loader import load_xml


@pytest.mark.skipif(
    not os.getenv("GOOGLE_DRIVE_FOLDER_ID"),
    reason="Google Drive is not configured"
)
def test_drive_download_and_ingestion():

    download_raw_files(
        "data/from_drive"
    )

    csv_path = Path(
        "data/from_drive/customers.csv"
    )

    json_path = Path(
        "data/from_drive/orders.json"
    )

    xml_path = Path(
        "data/from_drive/products.xml"
    )

    assert csv_path.exists()
    assert json_path.exists()
    assert xml_path.exists()

    spark = (
        SparkSession.builder
        .appName("DriveIngestionTest")
        .master("local[*]")
        .getOrCreate()
    )

    customers = load_csv(
        spark,
        str(csv_path)
    )

    orders = load_json(
        spark,
        str(json_path)
    )

    products = load_xml(
        spark,
        str(xml_path)
    )

    assert customers.count() == 15
    assert orders.count() == 12
    assert products.count() == 5

    spark.stop()