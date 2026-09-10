from pyspark.sql import DataFrame, SparkSession


def load_csv(
    spark: SparkSession,
    file_path: str
) -> DataFrame:
    """
    Load a CSV file into a Spark DataFrame.
    """

    return (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(file_path)
    )