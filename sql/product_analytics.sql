CREATE OR REPLACE VIEW
`cloud-data-engineering-508208.cloud_pipeline_dataset.product_analytics`
AS

SELECT
    p.product_id,
    p.product_name,
    p.category,

    COUNT(o.order_id) AS total_orders,

    COALESCE(SUM(o.quantity), 0) AS total_units_sold,

    COALESCE(
        SUM(o.quantity * o.price),
        0
    ) AS total_revenue,

    COALESCE(
        AVG(o.quantity * o.price),
        0
    ) AS average_order_value

FROM
    `cloud-data-engineering-508208.cloud_pipeline_dataset.products` p

LEFT JOIN
    `cloud-data-engineering-508208.cloud_pipeline_dataset.orders` o

ON
    p.product_id = o.product_id

GROUP BY
    p.product_id,
    p.product_name,
    p.category;