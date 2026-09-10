from pyspark.sql import DataFrame
from pyspark.sql.functions import col, lower, trim, to_date


def clean_customers(df: DataFrame) -> DataFrame:
    """
    Clean and standardize customer data.
    """

    cleaned_df = (
        df
        # Remove duplicate customers
        .dropDuplicates(["customer_id"])

        # Clean text columns
        .withColumn("name", trim(col("name")))
        .withColumn("email", lower(trim(col("email"))))
        .withColumn("city", trim(col("city")))
        .withColumn("country", trim(col("country")))

        # Convert signup date to a proper date
        .withColumn("signup_date", to_date(col("signup_date")))
    )

    return cleaned_df