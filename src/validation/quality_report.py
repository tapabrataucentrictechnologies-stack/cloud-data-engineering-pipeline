from pyspark.sql import DataFrame

from src.validation.schema_checks import check_required_columns
from src.validation.null_checks import check_nulls
from src.validation.duplicate_checks import check_duplicates
from src.validation.value_checks import check_positive_values


def generate_customer_quality_report(
    df: DataFrame
) -> dict:
    """
    Generate a complete quality report for customers.
    """

    schema_result = check_required_columns(
        df,
        [
            "customer_id",
            "name",
            "email",
            "city",
            "country",
            "signup_date"
        ]
    )

    null_result = check_nulls(
        df,
        [
            "customer_id",
            "name",
            "email",
            "city",
            "country",
            "signup_date"
        ]
    )

    duplicate_result = check_duplicates(
        df,
        ["customer_id"]
    )

    return {
        "dataset": "customers",
        "row_count": df.count(),
        "schema": schema_result,
        "nulls": null_result,
        "duplicates": duplicate_result
    }


def generate_order_quality_report(
    df: DataFrame
) -> dict:
    """
    Generate a complete quality report for orders.
    """

    schema_result = check_required_columns(
        df,
        [
            "order_id",
            "customer_id",
            "product_id",
            "order_date",
            "quantity",
            "price"
        ]
    )

    null_result = check_nulls(
        df,
        [
            "order_id",
            "customer_id",
            "product_id",
            "order_date",
            "quantity",
            "price"
        ]
    )

    duplicate_result = check_duplicates(
        df,
        ["order_id"]
    )

    value_result = check_positive_values(
        df,
        [
            "quantity",
            "price"
        ]
    )

    return {
        "dataset": "orders",
        "row_count": df.count(),
        "schema": schema_result,
        "nulls": null_result,
        "duplicates": duplicate_result,
        "positive_values": value_result
    }


def generate_product_quality_report(
    df: DataFrame
) -> dict:
    """
    Generate a complete quality report for products.
    """

    schema_result = check_required_columns(
        df,
        [
            "product_id",
            "product_name",
            "category"
        ]
    )

    null_result = check_nulls(
        df,
        [
            "product_id",
            "product_name",
            "category"
        ]
    )

    duplicate_result = check_duplicates(
        df,
        ["product_id"]
    )

    return {
        "dataset": "products",
        "row_count": df.count(),
        "schema": schema_result,
        "nulls": null_result,
        "duplicates": duplicate_result
    }