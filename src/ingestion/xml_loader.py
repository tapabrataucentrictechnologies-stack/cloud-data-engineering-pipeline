import xml.etree.ElementTree as ET

from pyspark.sql import DataFrame, SparkSession


def load_xml(
    spark: SparkSession,
    file_path: str
) -> DataFrame:
    """
    Load a simple products XML file into a Spark DataFrame.
    """

    tree = ET.parse(file_path)
    root = tree.getroot()

    records = []

    for product in root.findall("product"):
        record = {}

        for element in product:
            record[element.tag] = element.text

        records.append(record)

    return spark.createDataFrame(records)