import os
import sys

from pyspark.sql import SparkSession

from src.ingestion.csv_loader import load_csv
from src.ingestion.json_loader import load_json
from src.ingestion.xml_loader import load_xml


def create_spark_session():
    # Make sure Spark Python workers use the active virtual environment.
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    return (
        SparkSession.builder
        .appName("IngestionTest")
        .master("local[*]")
        .getOrCreate()
    )


def test_csv_ingestion():
    spark = create_spark_session()

    df = load_csv(
        spark,
        "data/raw/customers.csv"
    )

    assert df.count() == 15
    assert "customer_id" in df.columns
    assert "email" in df.columns

    spark.stop()


def test_json_ingestion():
    spark = create_spark_session()

    df = load_json(
        spark,
        "data/raw/orders.json"
    )

    assert df.count() == 12
    assert "order_id" in df.columns
    assert "customer_id" in df.columns

    spark.stop()


def test_xml_ingestion():
    spark = create_spark_session()

    df = load_xml(
        spark,
        "data/raw/products.xml"
    )

    assert df.count() == 5
    assert "product_id" in df.columns
    assert "product_name" in df.columns

    spark.stop()