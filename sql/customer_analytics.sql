CREATE OR REPLACE VIEW
`cloud-data-engineering-508208.cloud_pipeline_dataset.customer_analytics`
AS

SELECT
    c.customer_id,
    c.name,
    c.email,
    c.city,
    c.country,
    c.signup_date,

    COUNT(o.order_id) AS total_orders,

    COALESCE(SUM(o.quantity), 0) AS total_items_purchased,

    COALESCE(
        SUM(o.quantity * o.price),
        0
    ) AS total_spend,

    COALESCE(
        AVG(o.quantity * o.price),
        0
    ) AS average_order_value

FROM
    `cloud-data-engineering-508208.cloud_pipeline_dataset.customers` c

LEFT JOIN
    `cloud-data-engineering-508208.cloud_pipeline_dataset.orders` o

ON
    c.customer_id = o.customer_id

GROUP BY
    c.customer_id,
    c.name,
    c.email,
    c.city,
    c.country,
    c.signup_date;