from fastapi import APIRouter, HTTPException

from google.cloud import bigquery

import os

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# ROUTER CONFIGURATION
# ============================================================

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)


# ============================================================
# BIGQUERY CONFIGURATION
# ============================================================

PROJECT_ID = os.getenv(
    "GCP_PROJECT_ID",
    "cloud-data-engineering-508208"
)

DATASET = os.getenv(
    "BIGQUERY_DATASET",
    "cloud_pipeline_dataset"
)


# ============================================================
# BIGQUERY CLIENT
# ============================================================

def get_bigquery_client():

    return bigquery.Client(
        project=PROJECT_ID
    )


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

@router.get("/summary")
def get_dashboard_summary():

    try:

        client = (
            get_bigquery_client()
        )

        query = f"""
        SELECT

            (
                SELECT COUNT(*)
                FROM `{PROJECT_ID}.{DATASET}.customers`
            ) AS total_customers,

            (
                SELECT COUNT(*)
                FROM `{PROJECT_ID}.{DATASET}.orders`
            ) AS total_orders,

            (
                SELECT COUNT(*)
                FROM `{PROJECT_ID}.{DATASET}.products`
            ) AS total_products,

            (
                SELECT COALESCE(
                    SUM(quantity),
                    0
                )
                FROM `{PROJECT_ID}.{DATASET}.orders`
            ) AS total_units_sold,

            (
                SELECT COALESCE(
                    ROUND(
                        SUM(quantity * price),
                        2
                    ),
                    0
                )
                FROM `{PROJECT_ID}.{DATASET}.orders`
            ) AS total_revenue,

            (
                SELECT COALESCE(
                    ROUND(
                        AVG(quantity * price),
                        2
                    ),
                    0
                )
                FROM `{PROJECT_ID}.{DATASET}.orders`
            ) AS average_order_value
        """

        result = list(
            client.query(
                query
            ).result()
        )

        if not result:

            raise HTTPException(
                status_code=404,
                detail="No dashboard data found."
            )

        row = result[0]

        return {
            "success": True,
            "data": {

                "total_customers": int(
                    row.total_customers or 0
                ),

                "total_orders": int(
                    row.total_orders or 0
                ),

                "total_products": int(
                    row.total_products or 0
                ),

                "total_units_sold": int(
                    row.total_units_sold or 0
                ),

                "total_revenue": float(
                    row.total_revenue or 0
                ),

                "average_order_value": float(
                    row.average_order_value or 0
                ),
            },
        }

    except HTTPException:
        raise

    except Exception as error:

        print(
            "Dashboard summary error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# REVENUE OVER TIME
# ============================================================

@router.get("/revenue-over-time")
def get_revenue_over_time():

    try:

        client = (
            get_bigquery_client()
        )

        query = f"""
            SELECT
                order_date,
                ROUND(
                    SUM(quantity * price),
                    2
                ) AS total_revenue

            FROM `{PROJECT_ID}.{DATASET}.orders`

            GROUP BY order_date

            ORDER BY order_date
        """

        rows = list(
            client.query(
                query
            ).result()
        )

        return {
            "success": True,

            "data": [
                {
                    "order_date": str(
                        row.order_date
                    ),

                    "total_revenue": float(
                        row.total_revenue or 0
                    ),
                }

                for row in rows
            ],
        }

    except Exception as error:

        print(
            "Revenue over time error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# REVENUE BY PRODUCT
# ============================================================

@router.get("/revenue-by-product")
def get_revenue_by_product():

    try:

        client = (
            get_bigquery_client()
        )

        query = f"""
            SELECT

                p.product_name,

                ROUND(
                    COALESCE(
                        SUM(
                            o.quantity * o.price
                        ),
                        0
                    ),
                    2
                ) AS total_revenue

            FROM `{PROJECT_ID}.{DATASET}.products` p

            LEFT JOIN
                `{PROJECT_ID}.{DATASET}.orders` o

            ON
                p.product_id = o.product_id

            GROUP BY
                p.product_name

            ORDER BY
                total_revenue DESC
        """

        rows = list(
            client.query(
                query
            ).result()
        )

        return {
            "success": True,

            "data": [
                {
                    "product_name": (
                        row.product_name
                    ),

                    "total_revenue": float(
                        row.total_revenue or 0
                    ),
                }

                for row in rows
            ],
        }

    except Exception as error:

        print(
            "Revenue by product error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# REVENUE BY CUSTOMER
# ============================================================

@router.get("/revenue-by-customer")
def get_revenue_by_customer():

    try:

        client = (
            get_bigquery_client()
        )

        query = f"""
            SELECT

                c.customer_id,

                c.name AS customer_name,

                ROUND(
                    COALESCE(
                        SUM(
                            o.quantity * o.price
                        ),
                        0
                    ),
                    2
                ) AS total_revenue

            FROM
                `{PROJECT_ID}.{DATASET}.customers` c

            LEFT JOIN
                `{PROJECT_ID}.{DATASET}.orders` o

            ON
                c.customer_id = o.customer_id

            GROUP BY
                c.customer_id,
                c.name

            ORDER BY
                total_revenue DESC
        """

        rows = list(
            client.query(
                query
            ).result()
        )

        return {
            "success": True,

            "data": [
                {
                    "customer_id": (
                        row.customer_id
                    ),

                    "customer_name": (
                        row.customer_name
                    ),

                    "total_revenue": float(
                        row.total_revenue or 0
                    ),
                }

                for row in rows
            ],
        }

    except Exception as error:

        print(
            "Revenue by customer error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )