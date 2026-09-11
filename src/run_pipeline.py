import csv
import os
import sys
from pathlib import Path


# --------------------------------------------------
# Project paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_DIRECTORY = BASE_DIR / "data" / "from_drive"

PROCESSED_DIRECTORY = BASE_DIR / "data" / "processed"


# --------------------------------------------------
# Spark Python configuration
# --------------------------------------------------

# Always use the Python interpreter from the active
# virtual environment.
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable


from pyspark.sql import SparkSession


from src.ingestion.drive_ingestion import download_raw_files

from src.ingestion.csv_loader import load_csv

from src.ingestion.json_loader import load_json

from src.ingestion.xml_loader import load_xml


from src.transformation.customers import clean_customers

from src.transformation.orders import clean_orders

from src.transformation.products import clean_products


from src.validation.quality_report import (
    generate_customer_quality_report,
    generate_order_quality_report,
    generate_product_quality_report,
)


# --------------------------------------------------
# Spark session
# --------------------------------------------------

def create_spark_session():
    """Create the Spark session used by the pipeline."""

    return (
        SparkSession.builder
        .appName("CloudDataEngineeringPipeline")
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


# --------------------------------------------------
# Quality report
# --------------------------------------------------

def print_quality_report(report: dict):
    """Print a readable data quality report."""

    print(f"\nData Quality Report: {report['dataset']}")

    print(f"Rows: {report['row_count']}")

    print(
        f"Schema passed: "
        f"{report['schema']['passed']}"
    )

    print(
        f"Null checks passed: "
        f"{report['nulls']['passed']}"
    )

    print(
        f"Duplicate checks passed: "
        f"{report['duplicates']['passed']}"
    )

    if "positive_values" in report:

        print(
            f"Positive value checks passed: "
            f"{report['positive_values']['passed']}"
        )


# --------------------------------------------------
# Save DataFrame
# --------------------------------------------------

def save_dataframe_as_csv(
    dataframe,
    output_directory: Path,
    file_name: str,
):
    """
    Save a small Spark DataFrame as one CSV file.

    Python's CSV writer is used instead of Spark's
    distributed CSV writer to avoid Windows Hadoop
    filesystem issues.
    """

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = output_directory / file_name

    rows = [
        row.asDict()
        for row in dataframe.collect()
    ]

    columns = dataframe.columns

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file_handle:

        writer = csv.DictWriter(
            file_handle,
            fieldnames=columns,
        )

        writer.writeheader()

        writer.writerows(rows)

    return output_file


# --------------------------------------------------
# Main pipeline
# --------------------------------------------------

def main():
    """Run the complete batch ETL pipeline."""

    print("=" * 60)

    print(
        "END-TO-END CLOUD DATA ENGINEERING PIPELINE"
    )

    print("=" * 60)


    # --------------------------------------------------
    # 1. Download raw files
    # --------------------------------------------------

    print(
        "\n[1/5] Downloading raw files "
        "from Google Drive..."
    )

    downloaded_files = download_raw_files(
        str(RAW_DIRECTORY)
    )

    for file_path in downloaded_files:

        print(
            f"  Downloaded: {file_path}"
        )


    # --------------------------------------------------
    # 2. Start Spark
    # --------------------------------------------------

    print(
        "\n[2/5] Starting PySpark..."
    )

    spark = create_spark_session()


    try:

        # --------------------------------------------------
        # Load raw datasets
        # --------------------------------------------------

        print(
            "\nLoading raw datasets..."
        )

        customers_raw = load_csv(
            spark,
            str(
                RAW_DIRECTORY / "customers.csv"
            ),
        )

        orders_raw = load_json(
            spark,
            str(
                RAW_DIRECTORY / "orders.json"
            ),
        )

        products_raw = load_xml(
            spark,
            str(
                RAW_DIRECTORY / "products.xml"
            ),
        )


        print(
            f"  Customers: "
            f"{customers_raw.count()} rows"
        )

        print(
            f"  Orders: "
            f"{orders_raw.count()} rows"
        )

        print(
            f"  Products: "
            f"{products_raw.count()} rows"
        )


        # --------------------------------------------------
        # 3. Raw quality checks
        # --------------------------------------------------

        print(
            "\n[3/5] Running raw data "
            "quality checks..."
        )

        customer_raw_report = (
            generate_customer_quality_report(
                customers_raw
            )
        )

        order_raw_report = (
            generate_order_quality_report(
                orders_raw
            )
        )

        product_raw_report = (
            generate_product_quality_report(
                products_raw
            )
        )


        print_quality_report(
            customer_raw_report
        )

        print_quality_report(
            order_raw_report
        )

        print_quality_report(
            product_raw_report
        )


        # --------------------------------------------------
        # 4. Transform datasets
        # --------------------------------------------------

        print(
            "\n[4/5] Transforming datasets..."
        )

        customers_clean = clean_customers(
            customers_raw
        )

        orders_clean = clean_orders(
            orders_raw
        )

        products_clean = clean_products(
            products_raw
        )


        print(
            f"  Customers after cleaning: "
            f"{customers_clean.count()} rows"
        )

        print(
            f"  Orders after cleaning: "
            f"{orders_clean.count()} rows"
        )

        print(
            f"  Products after cleaning: "
            f"{products_clean.count()} rows"
        )


        # --------------------------------------------------
        # Processed quality checks
        # --------------------------------------------------

        print(
            "\nRunning processed data "
            "quality checks..."
        )

        customer_clean_report = (
            generate_customer_quality_report(
                customers_clean
            )
        )

        order_clean_report = (
            generate_order_quality_report(
                orders_clean
            )
        )

        product_clean_report = (
            generate_product_quality_report(
                products_clean
            )
        )


        print_quality_report(
            customer_clean_report
        )

        print_quality_report(
            order_clean_report
        )

        print_quality_report(
            product_clean_report
        )


        # --------------------------------------------------
        # 5. Save processed datasets
        # --------------------------------------------------

        print(
            "\n[5/5] Saving processed datasets..."
        )

        PROCESSED_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )


        # Customers
        customers_output = (
            save_dataframe_as_csv(
                customers_clean,
                PROCESSED_DIRECTORY,
                "customers.csv",
            )
        )


        # Orders
        # Explicit order is important because BigQuery
        # expects this exact schema order.
        orders_clean = orders_clean.select(
            "order_id",
            "customer_id",
            "product_id",
            "order_date",
            "quantity",
            "price",
        )

        orders_output = save_dataframe_as_csv(
            orders_clean,
            PROCESSED_DIRECTORY,
            "orders.csv",
        )


        # Products
        products_clean = products_clean.select(
            "product_id",
            "product_name",
            "category",
        )

        products_output = save_dataframe_as_csv(
            products_clean,
            PROCESSED_DIRECTORY,
            "products.csv",
        )


        print(
            "\nProcessed datasets saved:"
        )

        print(
            f"  - {customers_output}"
        )

        print(
            f"  - {orders_output}"
        )

        print(
            f"  - {products_output}"
        )


        # --------------------------------------------------
        # Pipeline completed
        # --------------------------------------------------

        print(
            "\n" + "=" * 60
        )

        print(
            "PIPELINE COMPLETED SUCCESSFULLY"
        )

        print(
            "=" * 60
        )


    finally:

        spark.stop()


# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":
    main()