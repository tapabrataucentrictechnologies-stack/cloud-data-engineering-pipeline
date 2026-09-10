import os
import sys

# Make Spark use the Python interpreter from the active virtual environment.
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession

from src.ingestion.csv_loader import load_csv
from src.ingestion.json_loader import load_json
from src.ingestion.xml_loader import load_xml

from src.validation.schema_checks import check_required_columns
from src.validation.null_checks import check_nulls
from src.validation.duplicate_checks import check_duplicates
from src.validation.value_checks import check_positive_values

from src.validation.quality_report import (
    generate_customer_quality_report,
    generate_order_quality_report,
    generate_product_quality_report
)


def create_spark_session():
    """
    Create a local Spark session for validation tests.
    """

    return (
        SparkSession.builder
        .appName("ValidationTest")
        .master("local[*]")
        .getOrCreate()
    )


def test_customer_schema():
    spark = create_spark_session()

    df = load_csv(
        spark,
        "data/raw/customers.csv"
    )

    result = check_required_columns(
        df,
        [
            "customer_id",
            "name",
            "email",
            "city",
            "country",
            "signup_date"
        ]
    )

    assert result["passed"] is True
    assert result["missing_columns"] == []

    spark.stop()


def test_customer_nulls():
    spark = create_spark_session()

    df = load_csv(
        spark,
        "data/raw/customers.csv"
    )

    result = check_nulls(
        df,
        [
            "customer_id",
            "name",
            "email",
            "city",
            "country",
            "signup_date"
        ]
    )

    # Customer 1011 intentionally has no email.
    assert result["null_counts"]["email"] == 1
    assert result["passed"] is False

    spark.stop()


def test_customer_duplicates():
    spark = create_spark_session()

    df = load_csv(
        spark,
        "data/raw/customers.csv"
    )

    result = check_duplicates(
        df,
        ["customer_id"]
    )

    # Customer 1005 is intentionally duplicated.
    assert result["duplicate_count"] == 1
    assert result["passed"] is False

    spark.stop()


def test_order_values():
    spark = create_spark_session()

    df = load_json(
        spark,
        "data/raw/orders.json"
    )

    result = check_positive_values(
        df,
        [
            "quantity",
            "price"
        ]
    )

    # One negative quantity and one negative price
    # are intentionally present in the raw data.
    assert result["invalid_counts"]["quantity"] == 1
    assert result["invalid_counts"]["price"] == 1
    assert result["passed"] is False

    spark.stop()


def test_customer_quality_report():
    spark = create_spark_session()

    df = load_csv(
        spark,
        "data/raw/customers.csv"
    )

    report = generate_customer_quality_report(df)

    assert report["dataset"] == "customers"
    assert report["row_count"] == 15
    assert report["duplicates"]["duplicate_count"] == 1
    assert report["nulls"]["null_counts"]["email"] == 1

    spark.stop()


def test_order_quality_report():
    spark = create_spark_session()

    df = load_json(
        spark,
        "data/raw/orders.json"
    )

    report = generate_order_quality_report(df)

    assert report["dataset"] == "orders"
    assert report["row_count"] == 12
    assert report["positive_values"]["invalid_counts"]["quantity"] == 1
    assert report["positive_values"]["invalid_counts"]["price"] == 1

    spark.stop()


def test_product_quality_report():
    spark = create_spark_session()

    df = load_xml(
        spark,
        "data/raw/products.xml"
    )

    report = generate_product_quality_report(df)

    assert report["dataset"] == "products"
    assert report["row_count"] == 5
    assert report["duplicates"]["duplicate_count"] == 0
    assert report["nulls"]["passed"] is True

    spark.stop()