from pyspark.sql import DataFrame

def check_required_columns(df: DataFrame, 
                           required_columns: list[str]
                           ) -> dict:
    """
    Check if the DataFrame contains all required columns.
    """

    actual_columns = set(df.columns)
    required_columns_set = set(required_columns)

    missing_columns = sorted(
        required_columns_set - actual_columns
    )

    unexpected_columns = sorted(
        actual_columns - required_columns_set
    )

    return {
        "passed": len(missing_columns) == 0,
        "missing_columns": missing_columns,
        "unexpected_columns": unexpected_columns
    }