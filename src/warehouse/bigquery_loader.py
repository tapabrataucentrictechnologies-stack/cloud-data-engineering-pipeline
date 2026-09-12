import csv
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import bigquery
from google.api_core.exceptions import NotFound


# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("BIGQUERY_DATASET")

if not PROJECT_ID:
    raise ValueError("GCP_PROJECT_ID is missing from .env")

if not DATASET_ID:
    raise ValueError("BIGQUERY_DATASET is missing from .env")


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIRECTORY = (
    BASE_DIR
    / "data"
    / "processed"
)


# ============================================================
# BIGQUERY CLIENT
# ============================================================

def get_bigquery_client():
    """
    Create and return a BigQuery client.
    """

    return bigquery.Client(
        project=PROJECT_ID
    )


# ============================================================
# DATASET
# ============================================================

def create_dataset():
    """
    Create the BigQuery dataset if it does not already exist.
    """

    client = get_bigquery_client()

    dataset_id = (
        f"{PROJECT_ID}.{DATASET_ID}"
    )

    dataset = bigquery.Dataset(
        dataset_id
    )

    dataset.location = "US"

    dataset = client.create_dataset(
        dataset,
        exists_ok=True
    )

    print(
        f"BigQuery dataset ready: "
        f"{dataset.full_dataset_id}"
    )

    return dataset


# ============================================================
# TABLE NAME NORMALIZATION
# ============================================================

def normalize_table_name(file_name: str):
    """
    Convert a processed file name into a safe BigQuery
    table name.

    Examples:

        customers_processed.csv
            -> customers

        Sample - Superstore_processed.csv
            -> sample_superstore

        Churn_Modelling_processed.csv
            -> churn_modelling
    """

    table_name = Path(
        file_name
    ).stem

    if table_name.endswith(
        "_processed"
    ):

        table_name = table_name[
            :-len("_processed")
        ]

    table_name = table_name.lower()

    table_name = re.sub(
        r"[^a-zA-Z0-9_]+",
        "_",
        table_name
    )

    table_name = re.sub(
        r"_+",
        "_",
        table_name
    )

    table_name = table_name.strip(
        "_"
    )

    if not table_name:
        table_name = "dataset"

    if table_name[0].isdigit():

        table_name = (
            f"table_{table_name}"
        )

    return table_name


# ============================================================
# COLUMN NAME NORMALIZATION
# ============================================================

def normalize_column_name(
    column_name: str
):
    """
    Convert a CSV column name into a BigQuery-compatible
    column name.
    """

    column_name = str(
        column_name
    ).strip().lower()

    column_name = re.sub(
        r"[^a-zA-Z0-9_]+",
        "_",
        column_name
    )

    column_name = re.sub(
        r"_+",
        "_",
        column_name
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


# ============================================================
# READ CSV HEADER
# ============================================================

def read_csv_header(
    file_path: Path
):
    """
    Read and normalize the CSV header.
    """

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file_handle:

        reader = csv.reader(
            file_handle
        )

        header = next(
            reader,
            None
        )

    if not header:

        raise ValueError(
            f"CSV file contains no header: "
            f"{file_path}"
        )

    normalized_columns = []

    used_names = set()

    for column in header:

        base_name = normalize_column_name(
            column
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

        normalized_columns.append(
            new_name
        )

    return normalized_columns


# ============================================================
# PREPARE NORMALIZED CSV
# ============================================================

def prepare_csv_for_bigquery(
    file_path: Path
):
    """
    Create a temporary CSV with normalized column names.

    The original processed CSV is not modified.
    """

    normalized_columns = read_csv_header(
        file_path
    )

    temporary_file = (
        file_path.parent
        / f".bq_{file_path.stem}.csv"
    )

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as source_file:

        reader = csv.reader(
            source_file
        )

        original_header = next(
            reader,
            None
        )

        if original_header is None:

            raise ValueError(
                f"CSV file is empty: "
                f"{file_path}"
            )

        with temporary_file.open(
            "w",
            encoding="utf-8",
            newline=""
        ) as target_file:

            writer = csv.writer(
                target_file
            )

            writer.writerow(
                normalized_columns
            )

            for row in reader:

                writer.writerow(
                    row
                )

    return (
        temporary_file,
        normalized_columns
    )


# ============================================================
# DISCOVER PROCESSED FILES
# ============================================================

def discover_processed_files():
    """
    Find every processed CSV generated by the pipeline.
    """

    PROCESSED_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    return sorted(
        PROCESSED_DIRECTORY.glob(
            "*_processed.csv"
        ),
        key=lambda path: path.name.lower()
    )


# ============================================================
# INFER CLUSTERING COLUMNS
# ============================================================

def choose_clustering_columns(
    schema
):
    """
    Automatically select useful clustering columns.

    Maximum of two columns are selected.
    """

    preferred_names = [
        "customer_id",
        "product_id",
        "order_id",
        "region",
        "category",
        "country",
        "city",
        "state",
        "segment",
    ]

    schema_names = {
        field.name
        for field in schema
    }

    selected = []

    for column_name in preferred_names:

        if column_name in schema_names:

            selected.append(
                column_name
            )

        if len(selected) == 2:
            break

    return selected


# ============================================================
# CHECK WHETHER TABLE EXISTS
# ============================================================

def get_existing_table(
    client,
    table_id
):
    """
    Return the existing BigQuery table.

    Returns None when the table does not exist.
    """

    try:

        return client.get_table(
            table_id
        )

    except NotFound:

        return None


# ============================================================
# BUILD LOAD CONFIGURATION
# ============================================================

def build_load_config(
    existing_table=None,
    clustering_columns=None
):
    """
    Build BigQuery load configuration.

    If the table already exists, its partitioning and
    clustering configuration is preserved.

    If the table does not exist, a new ingestion-time
    partitioned table is created and clustering is added
    when suitable columns are available.
    """

    job_config = (
        bigquery.LoadJobConfig()
    )

    job_config.source_format = (
        bigquery.SourceFormat.CSV
    )

    job_config.skip_leading_rows = 1

    job_config.autodetect = True

    job_config.write_disposition = (
        bigquery.WriteDisposition.WRITE_TRUNCATE
    )

    job_config.allow_quoted_newlines = True

    job_config.ignore_unknown_values = False

    job_config.max_bad_records = 0


    # --------------------------------------------------------
    # Existing table
    # --------------------------------------------------------

    if existing_table is not None:

        print(
            "\n  Existing BigQuery table detected."
        )

        if existing_table.time_partitioning:

            print(
                "  Preserving existing partitioning."
            )

            job_config.time_partitioning = (
                existing_table.time_partitioning
            )

        if existing_table.clustering_fields:

            print(
                "  Preserving existing clustering: "
                f"{existing_table.clustering_fields}"
            )

            job_config.clustering_fields = (
                existing_table.clustering_fields
            )

        return job_config


    # --------------------------------------------------------
    # New table
    # --------------------------------------------------------

    print(
        "\n  New BigQuery table detected."
    )

    print(
        "  Creating ingestion-time partitioning."
    )

    job_config.time_partitioning = (
        bigquery.TimePartitioning(
            type_=(
                bigquery.TimePartitioningType.DAY
            )
        )
    )

    if clustering_columns:

        print(
            "  Creating clustering: "
            f"{clustering_columns}"
        )

        job_config.clustering_fields = (
            clustering_columns
        )

    return job_config


# ============================================================
# LOAD ONE DATASET
# ============================================================

def load_dataset(
    file_path: Path
):
    """
    Dynamically load one processed CSV into BigQuery.
    """

    print("\n" + "=" * 60)

    print(
        f"Loading dataset: "
        f"{file_path.name}"
    )

    print("=" * 60)

    client = get_bigquery_client()


    # --------------------------------------------------------
    # Table name
    # --------------------------------------------------------

    table_name = normalize_table_name(
        file_path.name
    )

    table_id = (
        f"{PROJECT_ID}."
        f"{DATASET_ID}."
        f"{table_name}"
    )

    print(
        f"  BigQuery table: "
        f"{table_id}"
    )


    # --------------------------------------------------------
    # Prepare CSV
    # --------------------------------------------------------

    temporary_file = None

    try:

        (
            temporary_file,
            normalized_columns
        ) = prepare_csv_for_bigquery(
            file_path
        )

        print(
            "  Normalized columns:"
        )

        for column in normalized_columns:

            print(
                f"    - {column}"
            )


        # ----------------------------------------------------
        # Check existing table
        # ----------------------------------------------------

        existing_table = get_existing_table(
            client,
            table_id
        )


        # ----------------------------------------------------
        # Determine clustering for new table
        # ----------------------------------------------------

        clustering_columns = (
            choose_clustering_columns(
                [
                    bigquery.SchemaField(
                        name,
                        "STRING"
                    )
                    for name in normalized_columns
                ]
            )
        )


        # ----------------------------------------------------
        # Build configuration
        # ----------------------------------------------------

        job_config = build_load_config(
            existing_table=existing_table,
            clustering_columns=clustering_columns
        )


        # ----------------------------------------------------
        # Start load job
        # ----------------------------------------------------

        print(
            "\n  Starting BigQuery load..."
        )

        with temporary_file.open(
            "rb"
        ) as file_handle:

            load_job = (
                client.load_table_from_file(
                    file_handle,
                    table_id,
                    job_config=job_config
                )
            )

        print(
            f"  Load job ID: "
            f"{load_job.job_id}"
        )


        # ----------------------------------------------------
        # Wait for job
        # ----------------------------------------------------

        load_job.result()


        # ----------------------------------------------------
        # Check errors
        # ----------------------------------------------------

        if load_job.errors:

            print(
                "\n  BigQuery load errors:"
            )

            for error in load_job.errors:

                print(
                    f"    {error}"
                )

            raise RuntimeError(
                f"BigQuery load failed for "
                f"{file_path.name}"
            )


        # ----------------------------------------------------
        # Get resulting table
        # ----------------------------------------------------

        table = client.get_table(
            table_id
        )


        print(
            "\n  Dataset loaded successfully."
        )

        print(
            f"  Rows loaded: "
            f"{table.num_rows}"
        )

        print(
            f"  Columns: "
            f"{len(table.schema)}"
        )


        # ----------------------------------------------------
        # Show schema
        # ----------------------------------------------------

        print(
            "\n  BigQuery schema:"
        )

        for field in table.schema:

            print(
                f"    - "
                f"{field.name}: "
                f"{field.field_type}"
            )


        # ----------------------------------------------------
        # Partition information
        # ----------------------------------------------------

        if table.time_partitioning:

            if table.time_partitioning.field:

                print(
                    "  Partitioned by column: "
                    f"{table.time_partitioning.field}"
                )

            else:

                print(
                    "  Partitioned by: "
                    "ingestion time"
                )


        # ----------------------------------------------------
        # Clustering information
        # ----------------------------------------------------

        if table.clustering_fields:

            print(
                "  Clustered by: "
                f"{table.clustering_fields}"
            )

        else:

            print(
                "  Clustering: none"
            )


        return table


    finally:

        # ----------------------------------------------------
        # Remove temporary file
        # ----------------------------------------------------

        if (
            temporary_file
            and temporary_file.exists()
        ):

            temporary_file.unlink()


# ============================================================
# VERIFY TABLE
# ============================================================

def verify_table(
    table_name: str
):
    """
    Verify a BigQuery table using SQL COUNT(*).
    """

    client = get_bigquery_client()

    table_id = (
        f"{PROJECT_ID}."
        f"{DATASET_ID}."
        f"{table_name}"
    )

    query = f"""
        SELECT COUNT(*) AS total_rows
        FROM `{table_id}`
    """

    result = client.query(
        query
    ).result()

    row = next(
        iter(result)
    )

    return int(
        row["total_rows"]
    )


# ============================================================
# LOAD ALL PROCESSED DATASETS
# ============================================================

def load_all_tables():
    """
    Dynamically discover and load every processed dataset
    into BigQuery.
    """

    print("\n" + "=" * 60)

    print(
        "BIGQUERY WAREHOUSE LOAD"
    )

    print("=" * 60)


    # --------------------------------------------------------
    # Make sure dataset exists
    # --------------------------------------------------------

    create_dataset()


    # --------------------------------------------------------
    # Discover files
    # --------------------------------------------------------

    processed_files = (
        discover_processed_files()
    )

    if not processed_files:

        print(
            "\nNo processed datasets found."
        )

        print(
            f"Expected files inside: "
            f"{PROCESSED_DIRECTORY}"
        )

        return {}


    print(
        "\nProcessed datasets discovered:"
    )

    for file_path in processed_files:

        print(
            f"  - {file_path.name}"
        )


    # --------------------------------------------------------
    # Load datasets
    # --------------------------------------------------------

    results = {}

    for file_path in processed_files:

        table = load_dataset(
            file_path
        )

        table_name = (
            normalize_table_name(
                file_path.name
            )
        )

        results[
            table_name
        ] = table


    # --------------------------------------------------------
    # Final verification
    # --------------------------------------------------------

    print("\n" + "=" * 60)

    print(
        "BIGQUERY LOAD COMPLETED"
    )

    print("=" * 60)

    print(
        "\nFinal BigQuery tables:"
    )

    for table_name in results:

        row_count = verify_table(
            table_name
        )

        print(
            f"  {table_name}: "
            f"{row_count} rows"
        )

    return results


# ============================================================
# CONNECTION TEST
# ============================================================

def test_bigquery_connection():
    """
    Test the BigQuery connection.
    """

    client = get_bigquery_client()

    query = """
        SELECT 1 AS test_value
    """

    rows = client.query(
        query
    ).result()

    for row in rows:

        print(
            "BigQuery test result:",
            row["test_value"]
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    test_bigquery_connection()

    load_all_tables()