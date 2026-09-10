from pyspark.sql import DataFrame
from pyspark.sql.functions import col, to_date


def clean_orders(df: DataFrame) -> DataFrame:
    """
    Clean and standardize order data.
    """

    cleaned_df = (
        df
        # Convert order date to a proper date
        .withColumn("order_date", to_date(col("order_date")))

        # Remove invalid quantities
        .filter(col("quantity") > 0)

        # Remove invalid prices
        .filter(col("price") > 0)

        # Remove duplicate orders
        .dropDuplicates(["order_id"])
    )

    return cleaned_df