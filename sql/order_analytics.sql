CREATE OR REPLACE VIEW
`cloud-data-engineering-508208.cloud_pipeline_dataset.sales_analytics`
AS

SELECT
    order_date,

    COUNT(order_id) AS total_orders,

    SUM(quantity) AS total_units_sold,

    ROUND(
        SUM(quantity * price),
        2
    ) AS total_revenue,

    ROUND(
        AVG(quantity * price),
        2
    ) AS average_order_value

FROM
    `cloud-data-engineering-508208.cloud_pipeline_dataset.orders`

GROUP BY
    order_date

ORDER BY
    order_date;