from pyspark.sql import DataFrame, SparkSession


def load_json(
    spark: SparkSession,
    file_path: str
) -> DataFrame:
    """
    Load a multi-line JSON file into a Spark DataFrame.
    """

    return (
        spark.read
        .option("multiLine", True)
        .json(file_path)
    )