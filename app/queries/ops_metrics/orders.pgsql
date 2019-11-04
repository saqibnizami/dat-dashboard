WITH omv AS (
    SELECT
        order_id,
        string_agg(value, ', ') AS order_meta_values
    FROM orders.order_metadata
    GROUP BY order_id
    )
SELECT
    orders.id AS order_id,
    created_at AS order_created_at,
    order_type.code,
    CASE
        WHEN orders.prescription_id IS NULL THEN 'singlekit'
        ELSE 'multikit'
    END AS kit_type,
    CASE
        WHEN lower(omv.order_meta_values) LIKE '%upgraded from%' THEN 'upgrade'
        WHEN lower(omv.order_meta_values) LIKE '%explorer upgrade%' THEN 'upgrade'
        ELSE 'nonupgrade'
    END AS upgrade_type,
    orders.version,
    state,
    sample_id,
    delivery_id
FROM orders.orders
LEFT JOIN omv ON omv.order_id = orders.id
INNER JOIN orders.order_type ON orders.order_type_id=order_type.id
WHERE state NOT IN ('DRAFT') AND created_at > '2017-12-31'
