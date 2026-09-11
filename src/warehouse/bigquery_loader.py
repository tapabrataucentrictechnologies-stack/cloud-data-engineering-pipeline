import csv
import os
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

    Authentication is obtained through
    Google Application Default Credentials.
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

    dataset_id = f"{PROJECT_ID}.{DATASET_ID}"

    dataset = bigquery.Dataset(dataset_id)

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
# SCHEMAS
# ============================================================

CUSTOMER_SCHEMA = [
    bigquery.SchemaField(
        "customer_id",
        "INTEGER",
        mode="REQUIRED"
    ),
    bigquery.SchemaField(
        "name",
        "STRING",
        mode="REQUIRED"
    ),
    bigquery.SchemaField(
        "email",
        "STRING",
        mode="NULLABLE"
    ),
    bigquery.SchemaField(
        "city",
        "STRING",
        mode="REQUIRED"
    ),
    bigquery.SchemaField(
        "country",
        "STRING",
        mode="REQUIRED"
    ),
    bigquery.SchemaField(
        "signup_date",
        "DATE",
        mode="REQUIRED"
    ),
]


ORDER_SCHEMA = [
    bigquery.SchemaField(
        "order_id",
        "INTEGER",
        mode="REQUIRED"
    ),
    bigquery.SchemaField(
        "customer_id",
        "INTEGER",
        mode="REQUIRED"
    ),
    bigquery.SchemaField(
        "product_id",
        "INTEGER",
        mode="REQUIRED"
    ),
    bigquery.SchemaField(
        "order_date",
        "DATE",
        mode="REQUIRED"
    ),
    bigquery.SchemaField(
        "quantity",
        "INTEGER",
        mode="REQUIRED"
    ),
    bigquery.SchemaField(
        "price",
        "FLOAT",
        mode="REQUIRED"
    ),
]


PRODUCT_SCHEMA = [
    bigquery.SchemaField(
        "product_id",
        "INTEGER",
        mode="REQUIRED"
    ),
    bigquery.SchemaField(
        "product_name",
        "STRING",
        mode="REQUIRED"
    ),
    bigquery.SchemaField(
        "category",
        "STRING",
        mode="REQUIRED"
    ),
]


# ============================================================
# HELPER: DELETE AND CREATE TABLE
# ============================================================

def recreate_table(
    client,
    table_id,
    schema,
    partition_field=None,
    clustering_fields=None
):
    """
    Delete an existing table and recreate it.

    For orders, ingestion-time partitioning is used
    so historical order_date values do not determine
    the BigQuery partition.
    """

    print(
        f"\nRecreating table: {table_id}"
    )

    client.delete_table(
        table_id,
        not_found_ok=True
    )

    table = bigquery.Table(
        table_id,
        schema=schema
    )

    # --------------------------------------------------------
    # Partitioning
    # --------------------------------------------------------
    #
    # If partition_field is supplied, use column-based
    # partitioning.
    #
    # If partition_field is None, create an
    # ingestion-time partitioned table.
    #

    if partition_field:
        table.time_partitioning = (
            bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field=partition_field
            )
        )

    else:
        table.time_partitioning = (
            bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY
            )
        )

    # --------------------------------------------------------
    # Clustering
    # --------------------------------------------------------

    if clustering_fields:
        table.clustering_fields = (
            clustering_fields
        )

    created_table = client.create_table(
        table
    )

    print("  Table created")

    if created_table.time_partitioning:

        partition_field_name = (
            created_table.time_partitioning.field
        )

        if partition_field_name:
            print(
                "  Partitioned by column:",
                partition_field_name
            )

        else:
            print(
                "  Partitioned by: ingestion time"
            )

    if created_table.clustering_fields:

        print(
            "  Clustered by:",
            created_table.clustering_fields
        )

    return created_table


# ============================================================
# CUSTOMERS
# ============================================================

def load_customers():
    """
    Load processed customers.csv into BigQuery.
    """

    print("\n" + "=" * 60)
    print("Loading customers...")
    print("=" * 60)

    client = get_bigquery_client()

    file_path = (
        PROCESSED_DIRECTORY
        / "customers.csv"
    )

    if not file_path.exists():
        raise FileNotFoundError(
            f"Customers file not found: {file_path}"
        )

    table_id = (
        f"{PROJECT_ID}."
        f"{DATASET_ID}."
        f"customers"
    )

    job_config = bigquery.LoadJobConfig(
        schema=CUSTOMER_SCHEMA,
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        write_disposition=(
            bigquery.WriteDisposition.WRITE_TRUNCATE
        ),
        allow_quoted_newlines=True
    )

    print(
        f"  Source file: {file_path}"
    )

    with file_path.open(
        "rb"
    ) as file_handle:

        load_job = client.load_table_from_file(
            file_handle,
            table_id,
            job_config=job_config
        )

    print(
        f"  Load job ID: {load_job.job_id}"
    )

    load_job.result()

    if load_job.errors:
        print("\nBigQuery customer load errors:")

        for error in load_job.errors:
            print(error)

        raise RuntimeError(
            "Customers could not be loaded."
        )

    table = client.get_table(
        table_id
    )

    print(
        f"  Customers loaded: "
        f"{table.num_rows} rows"
    )

    return table


# ============================================================
# READ AND VALIDATE ORDERS CSV
# ============================================================

def read_orders_csv():
    """
    Read orders.csv using Python's CSV module.

    The values are explicitly converted to the types
    expected by BigQuery.
    """

    file_path = (
        PROCESSED_DIRECTORY
        / "orders.csv"
    )

    if not file_path.exists():
        raise FileNotFoundError(
            f"Orders file not found: {file_path}"
        )

    expected_columns = [
        "order_id",
        "customer_id",
        "product_id",
        "order_date",
        "quantity",
        "price"
    ]

    orders = []

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file_handle:

        reader = csv.DictReader(
            file_handle,
            skipinitialspace=True
        )

        if reader.fieldnames is None:
            raise ValueError(
                "orders.csv does not contain a header."
            )

        actual_columns = [
            column.strip()
            for column in reader.fieldnames
        ]

        if actual_columns != expected_columns:
            raise ValueError(
                "\nOrders CSV columns are incorrect.\n"
                f"Expected: {expected_columns}\n"
                f"Found: {actual_columns}"
            )

        for row_number, row in enumerate(
            reader,
            start=2
        ):

            # Ignore completely blank rows.
            if not any(
                value and value.strip()
                for value in row.values()
            ):
                continue

            try:
                order = {
                    "order_id": int(
                        row["order_id"].strip()
                    ),
                    "customer_id": int(
                        row["customer_id"].strip()
                    ),
                    "product_id": int(
                        row["product_id"].strip()
                    ),
                    "order_date": (
                        row["order_date"].strip()
                    ),
                    "quantity": int(
                        row["quantity"].strip()
                    ),
                    "price": float(
                        row["price"].strip()
                    )
                }

            except Exception as error:
                raise ValueError(
                    f"Invalid order at CSV row "
                    f"{row_number}: {row}\n"
                    f"Error: {error}"
                ) from error

            # Basic validation.
            if order["quantity"] <= 0:
                raise ValueError(
                    f"Invalid quantity in order "
                    f"{order['order_id']}"
                )

            if order["price"] <= 0:
                raise ValueError(
                    f"Invalid price in order "
                    f"{order['order_id']}"
                )

            orders.append(order)

    if not orders:
        raise ValueError(
            "orders.csv contains no valid records."
        )

    print(
        f"  Validated local orders: "
        f"{len(orders)} rows"
    )

    return orders


# ============================================================
# VERIFY ORDERS USING SQL
# ============================================================

def get_sql_row_count(
    client,
    table_id
):
    """
    Get the actual row count from BigQuery
    using SQL COUNT(*).
    """

    query = f"""
        SELECT COUNT(*) AS total_rows
        FROM `{table_id}`
    """

    query_job = client.query(
        query
    )

    result = query_job.result()

    row = next(iter(result))

    return int(
        row["total_rows"]
    )


# ============================================================
# ORDERS - PRIMARY BATCH LOAD
# ============================================================

def load_orders():
    """
    Load processed orders into BigQuery.

    Orders are stored in an ingestion-time partitioned
    table. The business order_date remains a normal DATE
    column.

    Data is loaded using a BigQuery batch load job.
    """

    print("\n" + "=" * 60)
    print("Loading orders...")
    print("=" * 60)

    client = get_bigquery_client()

    # --------------------------------------------------------
    # Read and validate local orders
    # --------------------------------------------------------

    orders = read_orders_csv()

    table_id = (
        f"{PROJECT_ID}."
        f"{DATASET_ID}."
        f"orders"
    )

    # --------------------------------------------------------
    # Recreate table
    # --------------------------------------------------------

    recreate_table(
        client=client,
        table_id=table_id,
        schema=ORDER_SCHEMA,
        partition_field=None,
        clustering_fields=[
            "customer_id",
            "product_id"
        ]
    )

    # --------------------------------------------------------
    # BigQuery batch load
    # --------------------------------------------------------

    print(
        "\n  Loading records into BigQuery..."
    )

    job_config = bigquery.LoadJobConfig(
        schema=ORDER_SCHEMA,
        source_format=(
            bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
        ),
        write_disposition=(
            bigquery.WriteDisposition.WRITE_APPEND
        ),
        ignore_unknown_values=False,
        max_bad_records=0
    )

    load_job = client.load_table_from_json(
        orders,
        table_id,
        job_config=job_config
    )

    print(
        f"  Load job ID: "
        f"{load_job.job_id}"
    )

    # Wait for BigQuery to finish.
    load_job.result()

    # --------------------------------------------------------
    # Check load errors
    # --------------------------------------------------------

    if load_job.errors:

        print(
            "\n  BigQuery load errors:"
        )

        for error in load_job.errors:
            print(
                f"    {error}"
            )

        raise RuntimeError(
            "BigQuery orders load job failed."
        )

    # --------------------------------------------------------
    # Check output rows
    # --------------------------------------------------------

    output_rows = (
        load_job.output_rows
        if load_job.output_rows is not None
        else 0
    )

    print(
        f"  Load job output rows: "
        f"{output_rows}"
    )

    # --------------------------------------------------------
    # Verify with SQL
    # --------------------------------------------------------

    sql_count = get_sql_row_count(
        client,
        table_id
    )

    print(
        f"  BigQuery SQL row count: "
        f"{sql_count}"
    )

    # --------------------------------------------------------
    # Validate final count
    # --------------------------------------------------------

    if sql_count != len(orders):

        raise RuntimeError(
            "BigQuery orders table contains "
            f"{sql_count} rows, but "
            f"{len(orders)} rows were expected."
        )

    # --------------------------------------------------------
    # Final table information
    # --------------------------------------------------------

    table = client.get_table(
        table_id
    )

    print(
        "\n  Orders loaded successfully."
    )

    if table.time_partitioning:

        if table.time_partitioning.field:

            print(
                "  Partitioned by column:",
                table.time_partitioning.field
            )

        else:

            print(
                "  Partitioned by: ingestion time"
            )

    if table.clustering_fields:

        print(
            "  Clustered by:",
            table.clustering_fields
        )

    return table

    # --------------------------------------------------------
    # BigQuery JSON load
    # --------------------------------------------------------

    print(
        "\n  Loading records into BigQuery..."
    )

    job_config = bigquery.LoadJobConfig(
        schema=ORDER_SCHEMA,
        source_format=(
            bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
        ),
        write_disposition=(
            bigquery.WriteDisposition.WRITE_APPEND
        ),
        ignore_unknown_values=False,
        max_bad_records=0
    )

    load_job = client.load_table_from_json(
        orders,
        table_id,
        job_config=job_config
    )

    print(
        f"  Load job ID: "
        f"{load_job.job_id}"
    )

    load_job.result()

    # --------------------------------------------------------
    # Check load job errors
    # --------------------------------------------------------

    if load_job.errors:
        print(
            "\n  BigQuery load job errors:"
        )

        for error in load_job.errors:
            print(
                f"    {error}"
            )

        raise RuntimeError(
            "BigQuery orders load job failed."
        )

    # --------------------------------------------------------
    # Check output rows
    # --------------------------------------------------------

    output_rows = (
        load_job.output_rows
        if load_job.output_rows is not None
        else 0
    )

    print(
        f"  Load job output rows: "
        f"{output_rows}"
    )

    sql_count = get_sql_row_count(
        client,
        table_id
    )

    print(
        f"  BigQuery SQL row count: "
        f"{sql_count}"
    )

    # --------------------------------------------------------
    # If successful, finish
    # --------------------------------------------------------

    if sql_count == len(orders):

        print(
            f"  Orders loaded successfully: "
            f"{sql_count} rows"
        )

        table = client.get_table(
            table_id
        )

        print(
            "  Partitioned by:",
            table.time_partitioning.field
        )

        print(
            "  Clustered by:",
            table.clustering_fields
        )

        return table

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    print(
        "\n  WARNING: BigQuery load job "
        "did not insert the expected rows."
    )

    print(
        "  Using row-level BigQuery fallback..."
    )

    # Recreate the table again so we know
    # the fallback starts from an empty table.
    recreate_table(
    client=client,
    table_id=table_id,
    schema=ORDER_SCHEMA,
    partition_field=None,
    clustering_fields=[
        "customer_id",
        "product_id"
    ]
)

    # --------------------------------------------------------
    # Insert JSON rows
    # --------------------------------------------------------

    # errors = client.insert_rows_json(
    #     table_id,
    #     orders,
    #     skip_invalid_rows=False,
    #     ignore_unknown_values=False
    # )

    # --------------------------------------------------------
    # Check insertion errors
    # --------------------------------------------------------

    if errors:

        print(
            "\n  BigQuery row insertion errors:"
        )

        for error in errors:
            print(
                f"    {error}"
            )

        raise RuntimeError(
            "BigQuery fallback insertion failed."
        )

    # --------------------------------------------------------
    # Final SQL verification
    # --------------------------------------------------------

    final_count = get_sql_row_count(
        client,
        table_id
    )

    print(
        f"  Fallback inserted: "
        f"{final_count} rows"
    )

    if final_count != len(orders):

        raise RuntimeError(
            "BigQuery orders table still contains "
            f"{final_count} rows, but "
            f"{len(orders)} rows were expected."
        )

    table = client.get_table(
        table_id
    )

    print(
        "\n  Orders loaded successfully."
    )

    print(
        "  Partitioned by:",
        table.time_partitioning.field
    )

    print(
        "  Clustered by:",
        table.clustering_fields
    )

    return table


# ============================================================
# PRODUCTS
# ============================================================

def load_products():
    """
    Load processed products.csv into BigQuery.
    """

    print("\n" + "=" * 60)
    print("Loading products...")
    print("=" * 60)

    client = get_bigquery_client()

    file_path = (
        PROCESSED_DIRECTORY
        / "products.csv"
    )

    if not file_path.exists():
        raise FileNotFoundError(
            f"Products file not found: {file_path}"
        )

    table_id = (
        f"{PROJECT_ID}."
        f"{DATASET_ID}."
        f"products"
    )

    job_config = bigquery.LoadJobConfig(
        schema=PRODUCT_SCHEMA,
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        write_disposition=(
            bigquery.WriteDisposition.WRITE_TRUNCATE
        ),
        allow_quoted_newlines=True
    )

    print(
        f"  Source file: {file_path}"
    )

    with file_path.open(
        "rb"
    ) as file_handle:

        load_job = client.load_table_from_file(
            file_handle,
            table_id,
            job_config=job_config
        )

    print(
        f"  Load job ID: {load_job.job_id}"
    )

    load_job.result()

    if load_job.errors:

        print(
            "\nBigQuery product load errors:"
        )

        for error in load_job.errors:
            print(error)

        raise RuntimeError(
            "Products could not be loaded."
        )

    table = client.get_table(
        table_id
    )

    print(
        f"  Products loaded: "
        f"{table.num_rows} rows"
    )

    return table


# ============================================================
# LOAD ALL TABLES
# ============================================================

def load_all_tables():
    """
    Load all processed datasets into BigQuery.
    """

    print("\n" + "=" * 60)
    print("BIGQUERY WAREHOUSE LOAD")
    print("=" * 60)

    # Make sure dataset exists.
    create_dataset()

    results = {}

    # Customers
    results["customers"] = (
        load_customers()
    )

    # Orders
    results["orders"] = (
        load_orders()
    )

    # Products
    results["products"] = (
        load_products()
    )

    # --------------------------------------------------------
    # Final verification
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("BIGQUERY LOAD COMPLETED")
    print("=" * 60)

    client = get_bigquery_client()

    for table_name in [
        "customers",
        "orders",
        "products"
    ]:

        table_id = (
            f"{PROJECT_ID}."
            f"{DATASET_ID}."
            f"{table_name}"
        )

        row_count = get_sql_row_count(
            client,
            table_id
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
    Simple BigQuery connection test.
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