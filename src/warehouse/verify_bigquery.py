import os

from dotenv import load_dotenv
from google.cloud import bigquery


# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================

load_dotenv()

PROJECT_ID = os.getenv(
    "GCP_PROJECT_ID"
)

DATASET_ID = os.getenv(
    "BIGQUERY_DATASET"
)


if not PROJECT_ID:

    raise ValueError(
        "GCP_PROJECT_ID is missing from .env"
    )


if not DATASET_ID:

    raise ValueError(
        "BIGQUERY_DATASET is missing from .env"
    )


# ============================================================
# EXPECTED ROW COUNTS
# ============================================================

EXPECTED_ROWS = {
    "customers": 14,
    "orders": 10,
    "products": 5
}


# ============================================================
# BIGQUERY CLIENT
# ============================================================

def get_bigquery_client():
    """
    Create a BigQuery client.
    """

    return bigquery.Client(
        project=PROJECT_ID
    )


# ============================================================
# SQL ROW COUNT
# ============================================================

def get_sql_row_count(
    client,
    table_id
):
    """
    Get the actual number of rows in a table
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

    row = next(
        iter(result)
    )

    return int(
        row["total_rows"]
    )


# ============================================================
# VERIFY TABLE
# ============================================================

def verify_table(
    client,
    table_name
):
    """
    Verify one BigQuery table.
    """

    table_id = (
        f"{PROJECT_ID}."
        f"{DATASET_ID}."
        f"{table_name}"
    )

    # --------------------------------------------------------
    # Get table metadata
    # --------------------------------------------------------

    table = client.get_table(
        table_id
    )

    # --------------------------------------------------------
    # Get actual SQL count
    # --------------------------------------------------------

    sql_row_count = get_sql_row_count(
        client,
        table_id
    )

    print(
        f"\nTable: {table_name}"
    )

    print(
        f"Metadata rows: "
        f"{table.num_rows}"
    )

    print(
        f"SQL COUNT(*): "
        f"{sql_row_count}"
    )

    # --------------------------------------------------------
    # Columns
    # --------------------------------------------------------

    print(
        "Columns:"
    )

    for field in table.schema:

        print(
            f"  - {field.name}: "
            f"{field.field_type}"
        )

    # --------------------------------------------------------
    # Partitioning
    # --------------------------------------------------------

    if table.time_partitioning:

        if table.time_partitioning.field:

            print(
                "Partitioned by column:",
                table.time_partitioning.field
            )

        else:

            print(
                "Partitioned by: ingestion time"
            )

    # --------------------------------------------------------
    # Clustering
    # --------------------------------------------------------

    if table.clustering_fields:

        print(
            "Clustered by:",
            table.clustering_fields
        )

    # --------------------------------------------------------
    # Expected row count
    # --------------------------------------------------------

    expected_rows = EXPECTED_ROWS[
        table_name
    ]

    if sql_row_count != expected_rows:

        raise RuntimeError(
            f"{table_name} contains "
            f"{sql_row_count} rows, but "
            f"{expected_rows} rows were expected."
        )

    print(
        f"  Row count verified: "
        f"{expected_rows}"
    )


# ============================================================
# VERIFY ORDERS CONTENT
# ============================================================

def verify_orders_content(
    client
):
    """
    Display a few records from the orders table.

    This provides an additional check that the data
    itself is present, not just the row count.
    """

    table_id = (
        f"{PROJECT_ID}."
        f"{DATASET_ID}."
        f"orders"
    )

    query = f"""
        SELECT
            order_id,
            customer_id,
            product_id,
            order_date,
            quantity,
            price
        FROM `{table_id}`
        ORDER BY order_date
        LIMIT 5
    """

    print(
        "\nSample orders:"
    )

    results = client.query(
        query
    ).result()

    for row in results:

        print(
            f"  Order {row.order_id}: "
            f"customer={row.customer_id}, "
            f"product={row.product_id}, "
            f"date={row.order_date}, "
            f"quantity={row.quantity}, "
            f"price={row.price}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("BIGQUERY WAREHOUSE VERIFICATION")
    print("=" * 60)

    client = get_bigquery_client()

    # --------------------------------------------------------
    # Verify all tables
    # --------------------------------------------------------

    for table_name in [
        "customers",
        "orders",
        "products"
    ]:

        verify_table(
            client,
            table_name
        )

    # --------------------------------------------------------
    # Verify sample orders
    # --------------------------------------------------------

    verify_orders_content(
        client
    )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print(
        "ALL BIGQUERY TABLES VERIFIED SUCCESSFULLY"
    )
    print("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()