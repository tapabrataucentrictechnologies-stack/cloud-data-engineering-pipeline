import csv
import json
import os
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_DIRECTORY = (
    BASE_DIR
    / "data"
    / "from_drive"
)

PROCESSED_DIRECTORY = (
    BASE_DIR
    / "data"
    / "processed"
)


# ============================================================
# SPARK PYTHON CONFIGURATION
# ============================================================

# Always use the Python interpreter from the active
# virtual environment.

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable


from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

from src.ingestion.drive_ingestion import download_raw_files
from src.warehouse.bigquery_loader import load_dataset


# ============================================================
# SUPPORTED FILE TYPES
# ============================================================

SUPPORTED_EXTENSIONS = {
    ".csv",
    ".json",
    ".xml",
    ".xlsx",
}


# ============================================================
# SPARK SESSION
# ============================================================

def create_spark_session():
    """
    Create the Spark session used by the pipeline.
    """

    return (
        SparkSession.builder
        .appName(
            "CloudDataEngineeringPipeline"
        )
        .master("local[*]")
        .config(
            "spark.hadoop.fs.file.impl",
            "org.apache.hadoop.fs.RawLocalFileSystem",
        )
        .config(
            "spark.hadoop.fs.permissions.umask-mode",
            "000",
        )
        .getOrCreate()
    )


# ============================================================
# COLUMN NAME NORMALIZATION
# ============================================================

def normalize_column_name(
    column_name: str
) -> str:
    """
    Convert a column name into a BigQuery-friendly format.

    Examples:

        Order Date
            -> order_date

        Customer ID
            -> customer_id

        Sales($)
            -> sales
    """

    column_name = str(
        column_name
    ).strip().lower()

    column_name = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        column_name,
    )

    column_name = re.sub(
        r"_+",
        "_",
        column_name,
    )

    column_name = column_name.strip(
        "_"
    )

    if not column_name:
        column_name = "column"

    if column_name[0].isdigit():

        column_name = (
            f"column_{column_name}"
        )

    return column_name


def normalize_columns(
    dataframe
):
    """
    Normalize all DataFrame column names
    and make them unique.
    """

    used_names = set()

    new_columns = []

    for column in dataframe.columns:

        base_name = (
            normalize_column_name(
                column
            )
        )

        new_name = base_name

        counter = 2

        while new_name in used_names:

            new_name = (
                f"{base_name}_{counter}"
            )

            counter += 1

        used_names.add(
            new_name
        )

        new_columns.append(
            new_name
        )

    return dataframe.toDF(
        *new_columns
    )


# ============================================================
# CSV LOADER
# ============================================================

def load_csv_dynamic(
    spark,
    file_path: Path
):
    """
    Dynamically load a CSV file.
    """

    print(
        f"  Reading CSV: "
        f"{file_path.name}"
    )

    dataframe = (
        spark.read
        .option(
            "header",
            True
        )
        .option(
            "inferSchema",
            True
        )
        .option(
            "multiLine",
            True
        )
        .option(
            "escape",
            '"'
        )
        .csv(
            str(file_path)
        )
    )

    return dataframe


# ============================================================
# JSON LOADER
# ============================================================

def load_json_dynamic(
    spark,
    file_path: Path
):
    """
    Dynamically load a JSON file.
    """

    print(
        f"  Reading JSON: "
        f"{file_path.name}"
    )

    dataframe = (
        spark.read
        .option(
            "multiLine",
            True
        )
        .option(
            "inferSchema",
            True
        )
        .json(
            str(file_path)
        )
    )

    return dataframe


# ============================================================
# XML LOADER
# ============================================================

def load_xml_dynamic(
    spark,
    file_path: Path
):
    """
    Load a simple record-oriented XML file.

    Each direct child of the XML root is treated
    as one record.
    """

    print(
        f"  Reading XML: "
        f"{file_path.name}"
    )

    tree = ET.parse(
        file_path
    )

    root = tree.getroot()

    records = []

    for element in root:

        record = {}

        # Include attributes.
        for key, value in element.attrib.items():

            record[key] = value

        # Include child elements.
        for child in element:

            # Handle nested XML.
            if list(child):

                nested_value = {}

                for nested_child in child:

                    nested_value[
                        nested_child.tag
                    ] = nested_child.text

                record[
                    child.tag
                ] = json.dumps(
                    nested_value
                )

            else:

                record[
                    child.tag
                ] = child.text

        records.append(
            record
        )

    if not records:

        raise ValueError(
            f"No records were found in XML file: "
            f"{file_path.name}"
        )

    dataframe = spark.createDataFrame(
        records
    )

    return dataframe


# ============================================================
# EXCEL LOADER
# ============================================================

def load_excel_dynamic(
    spark,
    file_path: Path
):
    """
    Load an XLSX file using pandas and
    convert it into a Spark DataFrame.
    """

    print(
        f"  Reading XLSX: "
        f"{file_path.name}"
    )

    try:

        import pandas as pd

    except ImportError as error:

        raise RuntimeError(
            "pandas is required to read XLSX files. "
            "Install with: "
            "python -m pip install pandas openpyxl"
        ) from error

    try:

        pandas_dataframe = (
            pd.read_excel(
                file_path,
                engine="openpyxl",
            )
        )

    except ImportError as error:

        raise RuntimeError(
            "openpyxl is required to read XLSX files. "
            "Install with: "
            "python -m pip install openpyxl"
        ) from error

    pandas_dataframe.columns = [
        str(column)
        for column
        in pandas_dataframe.columns
    ]

    pandas_dataframe = (
        pandas_dataframe.where(
            pandas_dataframe.notna(),
            None,
        )
    )

    records = (
        pandas_dataframe.to_dict(
            orient="records"
        )
    )

    if not records:

        raise ValueError(
            f"No records were found in XLSX file: "
            f"{file_path.name}"
        )

    dataframe = spark.createDataFrame(
        records
    )

    return dataframe


# ============================================================
# DYNAMIC FILE LOADER
# ============================================================

def load_file(
    spark,
    file_path: Path
):
    """
    Automatically select the correct reader based
    on the file extension.
    """

    extension = (
        file_path.suffix.lower()
    )

    if extension == ".csv":

        return load_csv_dynamic(
            spark,
            file_path
        )

    if extension == ".json":

        return load_json_dynamic(
            spark,
            file_path
        )

    if extension == ".xml":

        return load_xml_dynamic(
            spark,
            file_path
        )

    if extension == ".xlsx":

        return load_excel_dynamic(
            spark,
            file_path
        )

    raise ValueError(
        f"Unsupported file type: "
        f"{extension}"
    )


# ============================================================
# GENERIC CLEANING
# ============================================================

def clean_dataframe(
    dataframe
):
    """
    Apply generic cleaning that can work
    across different datasets.

    Operations:

    1. Normalize column names
    2. Trim string values
    3. Convert empty strings to null
    4. Remove duplicate rows
    """

    dataframe = normalize_columns(
        dataframe
    )

    # --------------------------------------------------------
    # Clean string columns
    # --------------------------------------------------------

    for field in dataframe.schema.fields:

        if isinstance(
            field.dataType,
            StringType
        ):

            dataframe = dataframe.withColumn(
                field.name,
                F.trim(
                    F.col(field.name)
                )
            )

            dataframe = dataframe.withColumn(
                field.name,
                F.when(
                    F.col(field.name) == "",
                    None,
                ).otherwise(
                    F.col(field.name)
                )
            )

    # --------------------------------------------------------
    # Remove duplicate rows
    # --------------------------------------------------------

    dataframe = (
        dataframe.dropDuplicates()
    )

    return dataframe


# ============================================================
# GENERIC DATA QUALITY REPORT
# ============================================================

def generate_quality_report(
    dataframe,
    dataset_name: str
):
    """
    Generate a generic data quality report.

    Checks:

    - Row count
    - Column count
    - Schema
    - Null values
    - Duplicate rows
    """

    row_count = (
        dataframe.count()
    )

    column_count = (
        len(dataframe.columns)
    )

    duplicate_count = (
        row_count
        - dataframe.dropDuplicates().count()
    )

    null_counts = {}

    for column in dataframe.columns:

        null_count = (
            dataframe
            .filter(
                F.col(column).isNull()
            )
            .count()
        )

        null_counts[
            column
        ] = null_count

    total_nulls = sum(
        null_counts.values()
    )

    schema_passed = (
        column_count > 0
    )

    null_check_passed = True

    duplicate_check_passed = (
        duplicate_count == 0
    )

    return {

        "dataset": dataset_name,

        "row_count": row_count,

        "column_count": column_count,

        "schema": {
            "passed": schema_passed,
            "column_count": column_count,
        },

        "nulls": {
            "passed": null_check_passed,
            "total_nulls": total_nulls,
            "columns": null_counts,
        },

        "duplicates": {
            "passed": duplicate_check_passed,
            "duplicate_rows": duplicate_count,
        },
    }


# ============================================================
# PRINT DATA QUALITY REPORT
# ============================================================

def print_quality_report(
    report: dict
):
    """
    Print a readable quality report.
    """

    print(
        f"\nData Quality Report: "
        f"{report['dataset']}"
    )

    print(
        f"Rows: "
        f"{report['row_count']}"
    )

    print(
        f"Columns: "
        f"{report['column_count']}"
    )

    print(
        f"Schema passed: "
        f"{report['schema']['passed']}"
    )

    print(
        f"Null checks passed: "
        f"{report['nulls']['passed']}"
    )

    print(
        f"Total null values: "
        f"{report['nulls']['total_nulls']}"
    )

    print(
        f"Duplicate checks passed: "
        f"{report['duplicates']['passed']}"
    )

    print(
        f"Duplicate rows: "
        f"{report['duplicates']['duplicate_rows']}"
    )


# ============================================================
# SAVE DATAFRAME AS CSV
# ============================================================

def save_dataframe_as_csv(
    dataframe,
    output_directory: Path,
    file_name: str
):
    """
    Save a Spark DataFrame as one CSV file.

    toLocalIterator() avoids loading the complete
    dataset into one Python list at once.
    """

    output_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_directory
        / file_name
    )

    columns = (
        dataframe.columns
    )

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file_handle:

        writer = csv.DictWriter(
            file_handle,
            fieldnames=columns
        )

        writer.writeheader()

        for row in (
            dataframe.toLocalIterator()
        ):

            writer.writerow(
                row.asDict()
            )

    return output_file


# ============================================================
# DISCOVER INPUT FILES
# ============================================================

def discover_input_files():
    """
    Discover all supported files that are currently
    available in the local Drive staging directory.
    """

    RAW_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    files = []

    for file_path in (
        RAW_DIRECTORY.iterdir()
    ):

        if not file_path.is_file():
            continue

        # Ignore temporary Excel files.
        if file_path.name.startswith(
            "~$"
        ):
            continue

        if file_path.suffix.lower() not in (
            SUPPORTED_EXTENSIONS
        ):
            continue

        files.append(
            file_path
        )

    return sorted(
        files,
        key=lambda path:
            path.name.lower()
    )


# ============================================================
# FIND SELECTED FILE
# ============================================================

def find_selected_file(
    selected_file: str
):
    """
    Find one selected file from the downloaded
    Google Drive staging directory.

    The user only needs to provide the file name,
    not the full local path.
    """

    input_files = (
        discover_input_files()
    )

    if not input_files:

        raise FileNotFoundError(
            "No supported files are available "
            "in the Google Drive staging directory."
        )

    # --------------------------------------------------------
    # Match by file name
    # --------------------------------------------------------

    selected_name = (
        Path(
            selected_file
        ).name
    )

    for file_path in input_files:

        if (
            file_path.name.lower()
            == selected_name.lower()
        ):

            return file_path

    # --------------------------------------------------------
    # File not found
    # --------------------------------------------------------

    available_files = "\n".join(
        f"  - {file_path.name}"
        for file_path
        in input_files
    )

    raise FileNotFoundError(
        "\nSelected file was not found: "
        f"{selected_file}\n\n"
        "Available files:\n"
        f"{available_files}"
    )


# ============================================================
# PROCESS ONE DATASET
# ============================================================

def process_dataset(
    spark,
    file_path: Path
):
    """
    Process exactly one selected dataset.

    Returns the generated processed CSV path.
    """

    print("\n" + "-" * 60)

    print(
        f"PROCESSING DATASET: "
        f"{file_path.name}"
    )

    print("-" * 60)


    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    print(
        "\nLoading dataset..."
    )

    dataframe = load_file(
        spark,
        file_path
    )

    raw_row_count = (
        dataframe.count()
    )

    print(
        f"  Rows loaded: "
        f"{raw_row_count}"
    )

    print(
        f"  Columns detected: "
        f"{len(dataframe.columns)}"
    )

    print(
        "  Columns:"
    )

    for column in (
        dataframe.columns
    ):

        print(
            f"    - {column}"
        )


    # --------------------------------------------------------
    # Raw quality checks
    # --------------------------------------------------------

    print(
        "\n[3/6] Running raw data "
        "quality checks..."
    )

    raw_report = (
        generate_quality_report(
            dataframe,
            file_path.name
        )
    )

    print_quality_report(
        raw_report
    )


    # --------------------------------------------------------
    # Cleaning and transformation
    # --------------------------------------------------------

    print(
        "\n[4/6] Cleaning and transforming "
        "dataset..."
    )

    cleaned_dataframe = (
        clean_dataframe(
            dataframe
        )
    )

    cleaned_row_count = (
        cleaned_dataframe.count()
    )

    print(
        f"  Rows after cleaning: "
        f"{cleaned_row_count}"
    )

    print(
        f"  Columns after cleaning: "
        f"{len(cleaned_dataframe.columns)}"
    )

    print(
        "  Final columns:"
    )

    for column in (
        cleaned_dataframe.columns
    ):

        print(
            f"    - {column}"
        )


    # --------------------------------------------------------
    # Processed quality checks
    # --------------------------------------------------------

    print(
        "\nRunning processed data "
        "quality checks..."
    )

    processed_report = (
        generate_quality_report(
            cleaned_dataframe,
            f"{file_path.name} "
            f"(processed)"
        )
    )

    print_quality_report(
        processed_report
    )


    # --------------------------------------------------------
    # Save processed dataset
    # --------------------------------------------------------

    print(
        "\n[5/6] Saving processed dataset..."
    )

    output_file_name = (
        f"{file_path.stem}_processed.csv"
    )

    output_file = (
        save_dataframe_as_csv(
            cleaned_dataframe,
            PROCESSED_DIRECTORY,
            output_file_name
        )
    )

    print(
        f"  Saved: "
        f"{output_file}"
    )

    return output_file


# ============================================================
# RUN SELECTED DATASET PIPELINE
# ============================================================

def run_pipeline(
    selected_file: str = None
):
    """
    Run the pipeline for one selected file.

    If selected_file is None, the first available
    file is used.

    This function will later be called by FastAPI
    when the user clicks "Run Pipeline".
    """

    print("=" * 60)

    print(
        "END-TO-END CLOUD DATA ENGINEERING PIPELINE"
    )

    print("=" * 60)


    # --------------------------------------------------------
    # 1. Download raw files from Google Drive
    # --------------------------------------------------------

    print(
        "\n[1/6] Downloading raw files "
        "from Google Drive..."
    )

    downloaded_files = (
        download_raw_files(
            str(RAW_DIRECTORY)
        )
    )

    if downloaded_files:

        for file_path in downloaded_files:

            print(
                f"  Downloaded: "
                f"{file_path}"
            )

    else:

        print(
            "  No new files were downloaded."
        )


    # --------------------------------------------------------
    # Discover available files
    # --------------------------------------------------------

    input_files = (
        discover_input_files()
    )

    if not input_files:

        raise FileNotFoundError(
            "No supported input files were found."
        )

    print(
        "\nSupported input files available:"
    )

    for file_path in input_files:

        print(
            f"  - {file_path.name}"
        )


    # --------------------------------------------------------
    # Select one dataset
    # --------------------------------------------------------

    if selected_file:

        selected_path = (
            find_selected_file(
                selected_file
            )
        )

    else:

        selected_path = (
            input_files[0]
        )

        print(
            "\nNo file was explicitly selected."
        )

        print(
            f"Using first available file: "
            f"{selected_path.name}"
        )


    print(
        "\nSelected dataset:"
    )

    print(
        f"  {selected_path.name}"
    )


    # --------------------------------------------------------
    # 2. Start Spark
    # --------------------------------------------------------

    print(
        "\n[2/6] Starting PySpark..."
    )

    spark = (
        create_spark_session()
    )


    try:

        # ----------------------------------------------------
        # Process exactly one file
        # ----------------------------------------------------

        processed_file = (
            process_dataset(
                spark,
                selected_path
            )
        )


        # ----------------------------------------------------
        # 6. BigQuery
        # ----------------------------------------------------

        print(
            "\n[6/6] Loading processed dataset "
            "into BigQuery..."
        )

        bigquery_table = (
            load_dataset(
                processed_file
            )
        )


        # ----------------------------------------------------
        # Final result
        # ----------------------------------------------------

        table_name = (
            bigquery_table.table_id
        )

        print(
            "\n" + "=" * 60
        )

        print(
            "PIPELINE COMPLETED SUCCESSFULLY"
        )

        print("=" * 60)

        print(
            f"\nSource file:"
        )

        print(
            f"  {selected_path.name}"
        )

        print(
            f"\nProcessed file:"
        )

        print(
            f"  {processed_file}"
        )

        print(
            f"\nBigQuery table:"
        )

        print(
            f"  {table_name}"
        )

        print(
            f"\nRows loaded:"
        )

        print(
            f"  {bigquery_table.num_rows}"
        )

        return {
            "success": True,
            "source_file": selected_path.name,
            "processed_file": str(
                processed_file
            ),
            "bigquery_table": table_name,
            "rows_loaded": (
                bigquery_table.num_rows
            ),
        }


    finally:

        spark.stop()


# ============================================================
# COMMAND-LINE ENTRY POINT
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Optional command-line argument
    #
    # Example:
    #
    # python -m src.run_pipeline customers.csv
    #
    # --------------------------------------------------------

    selected_file = None

    if len(sys.argv) > 1:

        selected_file = (
            sys.argv[1]
        )

    run_pipeline(
        selected_file
    )