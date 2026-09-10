from pyspark.sql import DataFrame
from pyspark.sql.functions import col


def check_positive_values(
    df: DataFrame,
    columns: list[str]
) -> dict:
    """
    Check that specified numeric columns contain
    only positive values.
    """

    invalid_counts = {}

    for column_name in columns:
        invalid_count = (
            df.filter(col(column_name) <= 0)
            .count()
        )

        invalid_counts[column_name] = invalid_count

    return {
        "passed": all(
            count == 0
            for count in invalid_counts.values()
        ),
        "invalid_counts": invalid_counts
    }