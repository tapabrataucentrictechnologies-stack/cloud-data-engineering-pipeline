CREATE OR REPLACE VIEW
`cloud-data-engineering-508208.cloud_pipeline_dataset.business_summary`
AS

SELECT
    (SELECT COUNT(*)
     FROM `cloud-data-engineering-508208.cloud_pipeline_dataset.customers`
    ) AS total_customers,

    (SELECT COUNT(*)
     FROM `cloud-data-engineering-508208.cloud_pipeline_dataset.orders`
    ) AS total_orders,

    (SELECT SUM(quantity)
     FROM `cloud-data-engineering-508208.cloud_pipeline_dataset.orders`
    ) AS total_units_sold,

    ROUND(
        (SELECT SUM(quantity * price)
         FROM `cloud-data-engineering-508208.cloud_pipeline_dataset.orders`
        ),
        2
    ) AS total_revenue,

    ROUND(
        (SELECT AVG(quantity * price)
         FROM `cloud-data-engineering-508208.cloud_pipeline_dataset.orders`
        ),
        2
    ) AS average_order_value;