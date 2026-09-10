import os
import sys

# Make Spark use the Python interpreter from the active virtual environment.
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession

from src.ingestion.csv_loader import load_csv
from src.ingestion.json_loader import load_json
from src.ingestion.xml_loader import load_xml

from src.transformation.customers import clean_customers
from src.transformation.orders import clean_orders
from src.transformation.products import clean_products


def create_spark_session():
    """
    Create a local Spark session for testing.
    """

    return (
        SparkSession.builder
        .appName("TransformationTest")
        .master("local[*]")
        .getOrCreate()
    )


def test_customer_transformation():
    """
    Test customer cleaning and deduplication.
    """

    spark = create_spark_session()

    df = load_csv(
        spark,
        "data/raw/customers.csv"
    )

    cleaned_df = clean_customers(df)

    # Original file contains 15 rows.
    # One duplicate customer is removed.
    assert cleaned_df.count() == 14

    # Customer IDs must be unique.
    assert cleaned_df.select("customer_id").distinct().count() == 14

    spark.stop()


def test_order_transformation():
    """
    Test order cleaning and validation.
    """

    spark = create_spark_session()

    df = load_json(
        spark,
        "data/raw/orders.json"
    )

    cleaned_df = clean_orders(df)

    # Original file contains 12 orders.
    # Two invalid orders are removed.
    assert cleaned_df.count() == 10

    # No invalid quantities should remain.
    assert cleaned_df.filter("quantity <= 0").count() == 0

    # No invalid prices should remain.
    assert cleaned_df.filter("price <= 0").count() == 0

    spark.stop()


def test_product_transformation():
    """
    Test product cleaning and deduplication.
    """

    spark = create_spark_session()

    df = load_xml(
        spark,
        "data/raw/products.xml"
    )

    cleaned_df = clean_products(df)

    # XML contains five products.
    assert cleaned_df.count() == 5

    # Product IDs must be unique.
    assert cleaned_df.select("product_id").distinct().count() == 5

    spark.stop()