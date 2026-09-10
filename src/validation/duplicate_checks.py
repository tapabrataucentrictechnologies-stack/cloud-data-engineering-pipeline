from pyspark.sql import DataFrame


def check_duplicates(
    df: DataFrame,
    key_columns: list[str]
) -> dict:
    """
    Check for duplicate records based on key columns.
    """

    total_rows = df.count()

    unique_rows = (
        df.select(*key_columns)
        .distinct()
        .count()
    )

    duplicate_count = total_rows - unique_rows

    return {
        "passed": duplicate_count == 0,
        "total_rows": total_rows,
        "unique_rows": unique_rows,
        "duplicate_count": duplicate_count
    }