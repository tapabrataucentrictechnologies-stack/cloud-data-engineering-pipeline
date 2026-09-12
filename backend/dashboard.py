from fastapi import APIRouter, HTTPException
from google.cloud import bigquery
import os
from dotenv import load_dotenv


load_dotenv()


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)


PROJECT_ID = os.getenv(
    "GCP_PROJECT_ID",
    "cloud-data-engineering-508208"
)

DATASET = os.getenv(
    "BIGQUERY_DATASET",
    "cloud_pipeline_dataset"
)


def get_bigquery_client():
    """
    Create a BigQuery client using Google Application Default Credentials.
    """

    return bigquery.Client(
        project=PROJECT_ID
    )


@router.get("/summary")
def get_dashboard_summary():

    try:

        client = get_bigquery_client()

        query = f"""
        SELECT
            total_customers,
            total_orders,
            total_units_sold,
            total_revenue,
            average_order_value
        FROM
            `{PROJECT_ID}.{DATASET}.business_summary`
        LIMIT 1
        """

        result = list(
            client.query(query).result()
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Business summary contains no data."
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

    except Exception as error:

        print(
            "Dashboard summary error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )