from pyspark.sql import DataFrame
from pyspark.sql.functions import col, sum


def check_nulls(df: DataFrame,
                columns: list[str]
                ) -> dict:
    """
    Count null values in the specified columns.
    """

    null_counts = {}

    for column_name in columns:
        null_count = (
            df.select(
                sum(
                    col(column_name).isNull().cast("int")
                ).alias("null_count")
            )
            .collect()[0]["null_count"]
        )

        null_counts[column_name] = int(null_count or 0)

    return {
        "passed": all(
            count == 0
            for count in null_counts.values()
        ),
        "null_counts": null_counts
    }