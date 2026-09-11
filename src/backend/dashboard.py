from fastapi import APIRouter, HTTPException

from google.cloud import bigquery

import os
from dotenv import load_dotenv


# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# Router configuration
# ---------------------------------------------------------

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)


# ---------------------------------------------------------
# BigQuery configuration
# ---------------------------------------------------------

PROJECT_ID = os.getenv(
    "GCP_PROJECT_ID",
    "cloud-data-engineering-508208"
)

DATASET = os.getenv(
    "BIGQUERY_DATASET",
    "cloud_pipeline_dataset"
)


# ---------------------------------------------------------
# BigQuery client
# ---------------------------------------------------------

def get_bigquery_client():
    return bigquery.Client(
        project=PROJECT_ID
    )


# ---------------------------------------------------------
# Dashboard summary API
# ---------------------------------------------------------

@router.get("/summary")
def get_dashboard_summary():

    try:

        client = get_bigquery_client()

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
            client.query(query).result()
        )


        # -------------------------------------------------
        # Check whether BigQuery returned data
        # -------------------------------------------------

        if not result:

            raise HTTPException(
                status_code=404,
                detail="No dashboard data found."
            )


        row = result[0]


        # -------------------------------------------------
        # Return JSON response
        # -------------------------------------------------

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
                )
            }
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