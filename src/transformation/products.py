from pyspark.sql import DataFrame
from pyspark.sql.functions import col, trim


def clean_products(df: DataFrame) -> DataFrame:
    """
    Clean and standardize product data.
    """

    cleaned_df = (
        df
        # Clean text columns
        .withColumn("product_name", trim(col("product_name")))
        .withColumn("category", trim(col("category")))

        # Remove duplicate products
        .dropDuplicates(["product_id"])
    )

    return cleaned_df